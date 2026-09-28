# Experiments: building evidence rather than collecting attractive traces

Your interest in consciousness and meditation can motivate this project without requiring the first experiment to answer a philosophical question. The useful first questions are smaller: can you recover a known signal, distinguish it from interference, and repeat a controlled observation?

**The body-connected experiments below are future protocols, conditional on the hardware review in HARDWARE_GUIDE.md. They are not instructions to attach the current unreviewed circuit.** The supplied data and classifier are synthetic only.

## Experiment 0: a signal whose answer you know

Run `python run_lab.py demo`. The generator builds six sessions with randomized, balanced condition blocks. One label receives a larger 10-Hz component. It also adds other rhythms, colored noise, residual 50/60-Hz interference, offsets and occasional artifacts.

Before looking at the result, predict which condition should have more 8–13-Hz power. Open the spectrum and the JSON report. The measured increase confirms that this limited software path can recover a deliberately planted effect. It does not confirm that the synthetic signal is a realistic model of meditation.

Then run `--null-effect`, change the random seed, change channel count, and increase artifact size. Keep each result in a distinct output folder. A notebook that records settings, predictions and outcomes is more useful than a folder of unlabeled screenshots.

## Experiment 1: deliberately damage the measurement

Set the differential offset beyond the gain-dependent range. The correct outcome is rejected/overrange data. A smooth filtered waveform is not the goal.

Run `python tools/run_loopback.py`. Confirm both deliberate packet losses are reported. Try a manual replay with frequent drops: the inspector may have no uninterrupted four-second interval and therefore no spectrum. Treat that as an informative failure.

Change the electrode impedance model. Observe how common-mode interference turns into a differential error. Keep the distinction between this passive circuit result and the synthetic recording generator: they are separate exercises in this release.

## Experiment 2: hardware, but still no head

With a reviewed assembled board and target-compiled firmware, record the internal test source, then internal short. Save raw binary, decoded CSV, metadata JSON, firmware revision, clock/reference assumptions and a note of the physical setup.

Move digital wiring or change the radio setting one factor at a time, while remaining on the bench. Check packet continuity and spectra. Do not assume a noisy radio setup can be corrected later with a classifier.

A future external-dummy calibration requires board-specific input/common-mode and protection review. Passing internal test and short establishes only part of the signal chain.

## Experiment 3: a future posterior-alpha observation

After the body-interface gate is satisfied, a modest first physiological target is a repeated comparison of eyes open and eyes closed using a posterior recording channel. OpenBCI's EEG guide uses this kind of alpha observation as an accessible demonstration [S12]. It is a better initial target than inventing a direct measure of consciousness.

A proposed learning protocol is twelve 30-second blocks, six in each eye condition, in a balanced randomized order. This block count is a practical starting design, not a statistical power calculation. Stay comfortably seated, keep the head and jaw relaxed, and use a stable setup. Record condition onsets, uncertainty in timing, electrode montage and contact preparation. Mark transitions and exclude a predefined settling interval before analysis.

Choose the exact montage/reference/bias connections from the reviewed board documentation, not from this generic description. O1/O2 are standardized posterior location names, not arbitrary labels for “somewhere at the back.” Proper placement and reference details matter.

Specify the analysis before inspecting the results: an 8–13-Hz band-power comparison across clean blocks, a quality rule, and how transitions and artifacts are excluded. Keep all blocks, including those that fail quality checks, in the record. Report the number rejected in each condition. Inspect raw voltage, spectral content and quality information together.

An increase after eye closure may be a useful repeatable physiological observation. Its absence in one attempt does not establish that your brain is abnormal, nor does its presence establish that every channel is good. Eye movement and muscle signals can dominate recordings; MNE documents these artifact families [S7].

## Experiment 4: meditation versus quiet rest, with the eyes held constant

Do not compare eyes-open ordinary activity with eyes-closed meditation and call the difference a meditation effect. That design changes too many things at once.

A proposed within-person pilot is six two-minute blocks per session: three meditation blocks and three quiet-rest blocks, with the **same eye condition** in both. Balance order across sessions and use ordinary comfortable breathing rather than deliberately changing respiration. Keep posture, instructions, room and recording setup as constant as practical. Run on at least three separate days as an exploratory start; this is not a claim of sufficient statistical power.

Write down one primary outcome beforehand, for example the difference in median log posterior alpha power between conditions. Other bands can be exploratory rather than retrospectively promoted to the original hypothesis. Record subjective ratings after blocks: perceived stability of attention, drowsiness, effort, discomfort and perceived depth. These are separate observations, not ground truth derived from the EEG itself.

The first result should be an effect estimate and the spread across blocks/days, with quality exclusions visible. A classifier is optional. A non-significant, unstable, or artifact-dependent result is still useful information about the measurement and protocol.

## Experiment 5: a classifier that faces a meaningful test

Start with a simple model, not a deep network. Keep all windows from a day together, fit scaling only on training days, and hold out a complete day. Do not randomly mix nearby or overlapping windows between training and test sets. The supplied synthetic example implements the same basic group-separation principle [S6, S8].

Check a majority-class baseline, shuffled whole-block labels, and whether predictions correlate with artifacts, time in the session, electrode quality or recorded movement. A model that learns a jaw-tension habit can predict your labels while answering the wrong scientific question.

The existing `demo` classifier is **not** automatically applicable to a real capture CSV. It expects a validated labeled synthetic dataset with session/block information. Real data need a separate import/annotation path, accurate events, montage/reference metadata, artifact review and appropriate validation. The bench `inspect` command computes unlabeled signal-quality summaries; it does not infer meditation.

## What would justify a stronger claim?

A credible next claim is specific: “Under this montage, protocol and quality rule, this participant showed a repeatable difference in a prespecified measurement across these sessions.” That is much narrower than “this device measures consciousness.”

Keep alternative explanations visible. A small scalp-recording system and a label classifier alone do not identify a unique mechanism of consciousness. The project can nevertheless teach the practical science needed to ask increasingly precise questions about perception, attention and subjective experience.

## Minimal experiment record

Use a text file beside every recording with: session/date; device and firmware revision; gain/reference/sample rate; montage; condition schedule; timing method; electrode preparation; battery/wireless arrangement; raw-data filename; packet-quality summary; exclusions; and subjective notes. Avoid uploading identifiable raw recordings or private notes to public services without considering the privacy consequences.

Use `experiment_record_template.md` as a starting point. A future assistant should receive the protocol and quality record, not only the most attractive plot.

References marked `[S#]` are linked in [SOURCES.md](SOURCES.md).
