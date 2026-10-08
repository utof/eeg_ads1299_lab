"""Bounded corrections to the immutable R24 attempt; no remote engineering writes."""
from pathlib import Path
import atexit
import subprocess

BASE = 'd66523fb52aa6d5e0a7be115b6bd13d9ebafaa36'
ROOT = Path('/tmp/l5-edit')
OUT = Path('/tmp/l5-out')
source = subprocess.check_output(['git', 'show', BASE+':workbench/l5_author.py'], text=True)

def change(old, new):
    global source
    assert source.count(old) == 1, (old, source.count(old))
    source = source.replace(old, new)

change("text = text.rstrip()[:-1]+f'\\n(net {new_code} \"MISO_DRV\")\\n'+newfp+'\\n)\\n'", "text = text.rstrip()[:-1]+'\\n'+newfp+'\\n)\\n'\nfirst = next(a for a,z,f in topforms(text) if f.startswith('(footprint'))\ntext = text[:first]+f'(net {new_code} \"MISO_DRV\")\\n'+text[first:]")
change("b = p.LoadBoard(str(boardpath))\nchanged_ids", "b = p.LoadBoard(str(boardpath))\nassert len(list(b.GetFootprints())) == sum(f.startswith('(footprint') for a,z,f in topforms(original))+1\nuuid_map = {}\nchanged_ids")
change("t.m_Uuid=p.KIID(identity or uid(name)); b.Add(t); changed_ids.add(t.m_Uuid.AsString())", "wanted=identity or uid(name); uuid_map[t.m_Uuid.AsString()]=wanted; b.Add(t); changed_ids.add(wanted)")
change("v.m_Uuid=p.KIID(uid(name)); b.Add(v); changed_ids.add(v.m_Uuid.AsString())", "wanted=uid(name); uuid_map[v.m_Uuid.AsString()]=wanted; b.Add(v); changed_ids.add(wanted)")
change("v.SetWidth(p.FromMM(.6))", "v.SetWidth(p.F_Cu,p.FromMM(.6))")
change("native=(OUT/'native-r24.kicad_pcb').read_text()", "native=(OUT/'native-r24.kicad_pcb').read_text()\nfor observed,wanted in uuid_map.items():\n    assert native.count(observed) == 1\n    native=native.replace(observed,wanted)")
change("result=result.rstrip()[:-1]+f'\\n(net {new_code} \"MISO_DRV\")\\n'+'\\n'.join(extras)+'\\n)\\n'", "result=result.rstrip()[:-1]+'\\n'+'\\n'.join(extras)+'\\n)\\n'\nfirst = next(a for a,z,f in topforms(result) if f.startswith('(footprint'))\nresult = result[:first]+f'(net {new_code} \"MISO_DRV\")\\n'+result[first:]")
# Only the relocated unused GPIO1 shunt needs this wider disposable search.
# The MISO 10mm/two-via and full-reference requirements are not relaxed.
change("(54.5,64,34.8,38.5),'GPIO1/inner'", "(54.5,67,29.5,43),'GPIO1/inner'")
change("assert miso_length <= 10", "assert miso_length <= 10\np.SaveBoard(str(OUT/'before-gpio-route.kicad_pcb'),b)")
change("shutil.copytree(BASE/'hardware/rev_a/footprints',OUT/'footprints')", "# The complete CAD directory already retains its project-local libraries.")

OUT.mkdir(exist_ok=True)
(OUT/'corrected-author.py').write_text(source)
def retain_partial():
    patch=subprocess.check_output(['git','diff','--binary','ff953c03c452f1572602b52aa62f42e80bfa9588'],cwd=ROOT)
    (OUT/'partial-source.patch').write_bytes(patch)
atexit.register(retain_partial)
exec(compile(source,str(OUT/'corrected-author.py'),'exec'), {'__name__':'__main__'})
