"""Offline epoch analysis and session-held-out toy machine learning."""
import numpy as np
from scipy.signal import butter, sosfiltfilt, welch
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, confusion_matrix
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from .adc import ADCConfig, to_volts

BANDS={'theta':(4,8),'alpha':(8,13),'beta':(13,30)}


def psd(x,fs):
    x=np.asarray(x,float)
    if x.ndim not in (1,2) or len(x)<fs or not np.all(np.isfinite(x)):
        raise ValueError('PSD requires at least 1 s of finite time-first samples')
    nperseg=min(len(x),int(4*fs))
    return welch(x,fs=fs,window='hann',nperseg=nperseg,
                 noverlap=nperseg//2,detrend='constant',axis=0,scaling='density')


def bandpower(x,fs,low,high):
    if not 0<=low<high<fs/2:
        raise ValueError('Invalid frequency band')
    f,p=psd(x,fs)
    select=(f>=low)&(f<=high)
    return np.trapezoid(p[select],f[select],axis=0)


def quality_flags(x,invalid=None,threshold_uV=150):
    """Heuristic peak-to-peak screen, not comprehensive artifact removal.

    Operates on raw differential voltages before bandpass. Unknown artifacts
    can pass. Constant electrode offset alone is not an artifact.
    """
    x=np.asarray(x,float)
    if x.ndim!=2 or not np.all(np.isfinite(x)):
        return {'nonfinite_or_shape':True,'overrange':True,'large_excursion':True,'flat':True}
    centered=x-np.median(x,axis=0)
    return {'nonfinite_or_shape':False,
            'overrange':bool(np.any(invalid)) if invalid is not None else False,
            'large_excursion':bool(np.max(np.ptp(centered,axis=0))>threshold_uV*1e-6),
            'flat':bool(np.any(np.std(centered,axis=0)<.01e-6))}


def epoch_features(data):
    """4-s nonoverlapping windows, discard 2 s at each block boundary.

    Each candidate is locally demeaned/filtered; no filter bridges train/test
    sessions. Quality rules are fixed before labels are read. Condition and
    session IDs are NEVER features. Split by session, not window.
    """
    cfg=data['metadata']; fs=cfg['fs_hz']
    adc=ADCConfig(gain=cfg['gain'],fs_hz=fs)
    x=to_volts(data['codes'],adc)
    features=[]; labels=[]; groups=[]; rows=[]
    sos=butter(4,[1,40],fs=fs,btype='bandpass',output='sos')
    window=4*fs
    for block in np.unique(data['block']):
        indices=np.flatnonzero(data['block']==block)
        # Dataset uses contiguous blocks; refusing otherwise prevents bridging.
        if not np.all(np.diff(indices)==1): raise ValueError('Noncontiguous block')
        for offset in range(2*fs,len(indices)-2*fs-window+1,window):
            idx=indices[offset:offset+window]
            raw=x[idx]
            flags=quality_flags(raw,data['invalid'][idx])
            accepted=not any(flags.values())
            row={'block':int(block),'session':int(data['session'][idx[0]]),
                 'start_s':float(data['time_s'][idx[0]]),
                 'condition':int(data['condition'][idx[0]]),'accepted':accepted,**flags}
            if accepted:
                filtered=sosfiltfilt(sos,raw-np.mean(raw,axis=0),axis=0)
                powers=[bandpower(filtered,fs,*band) for band in BANDS.values()]
                feat=np.log10(np.maximum(np.concatenate(powers),1e-24))
                features.append(feat); labels.append(row['condition']);groups.append(row['session'])
                row['alpha_uV2']=float(np.mean(powers[1])*1e12)
            rows.append(row)
    if not features:
        raise ValueError('All epochs rejected; inspect raw data and range/quality flags')
    return np.asarray(features),np.asarray(labels),np.asarray(groups),rows


def _cross_validate(X,y,groups):
    if len(np.unique(groups))<3 or len(np.unique(y))!=2:
        raise ValueError('Need >=3 groups and both conditions')
    predictions=np.empty_like(y); baseline=np.empty_like(y); folds=[]
    for train,test in LeaveOneGroupOut().split(X,y,groups):
        if len(np.unique(y[train]))!=2 or len(np.unique(y[test]))!=2:
            raise ValueError('Each held-out session and training set must contain both conditions')
        if set(groups[train])&set(groups[test]): raise AssertionError('Session leakage')
        model=make_pipeline(StandardScaler(),LogisticRegression(max_iter=2000,random_state=0))
        model.fit(X[train],y[train])
        predictions[test]=model.predict(X[test])
        dummy=DummyClassifier(strategy='most_frequent').fit(X[train],y[train])
        baseline[test]=dummy.predict(X[test])
        folds.append({'held_out_session':int(groups[test][0]),
                      'train_sessions':sorted(int(z) for z in np.unique(groups[train])),
                      'train_epochs':len(train),'test_epochs':len(test),
                      'balanced_accuracy':float(balanced_accuracy_score(y[test],predictions[test]))})
    return {'balanced_accuracy':float(balanced_accuracy_score(y,predictions)),
            'baseline_balanced_accuracy':float(balanced_accuracy_score(y,baseline)),
            'confusion_matrix':confusion_matrix(y,predictions,labels=[0,1]).tolist(),
            'folds':folds}


def analyze(data,permutations=20):
    X,y,g,rows=epoch_features(data)
    result=_cross_validate(X,y,g)
    accepted=[r for r in rows if r['accepted']]
    block_ids=np.array([r['block'] for r in accepted])
    rng=np.random.default_rng(data['metadata']['seed']+17)
    null=[]
    for _ in range(permutations):
        # Exchange labels by whole block WITHIN each session, never by sample.
        yp=y.copy()
        for session in np.unique(g):
            blocks=np.unique(block_ids[g==session])
            values=np.array([y[block_ids==b][0] for b in blocks])
            rng.shuffle(values)
            for b,label in zip(blocks,values): yp[block_ids==b]=label
        null.append(_cross_validate(X,yp,g)['balanced_accuracy'])
    by_condition={str(k):float(np.median([r['alpha_uV2'] for r in accepted if r['condition']==k])) for k in (0,1)}
    result.update({'kind':'synthetic_pipeline_test_not_neuroscience_evidence',
                   'candidate_epochs':len(rows),'accepted_epochs':len(accepted),
                   'rejected_epochs':len(rows)-len(accepted),
                   'alpha_median_uV2':by_condition,
                   'closed_open_alpha_ratio':by_condition['1']/by_condition['0'],
                   'block_permutation_scores':null,
                   'block_permutation_mean':float(np.mean(null)) if null else None,
                   'block_permutation_p':float((1+sum(s>=result['balanced_accuracy'] for s in null))/(1+len(null))) if null else None,
                   'feature_names':[f'log10_{band}_V2_ch{c+1}' for band in BANDS for c in range(data['metadata']['channels'])]})
    return result,rows
