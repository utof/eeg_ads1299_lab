"""Bounded native R24 authoring and diagnostics; no remote engineering writes."""
from pathlib import Path
import atexit
import contextlib
import os
import subprocess
import traceback

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
change("(54.5,64,34.8,38.5),'GPIO1/inner'", "(54.5,67,29.5,43),'GPIO1/inner'")
change("shutil.copytree(BASE/'hardware/rev_a/footprints',OUT/'footprints')", "# The complete CAD directory retains its project-local libraries.")
change("'dbf10413-cc72-52d0-a0d7-6b1aa55e77ab'}", "'dbf10413-cc72-52d0-a0d7-6b1aa55e77ab','bf44cb01-4974-5b9c-b9b9-f12a3026051e'}")
assert source.count('(54.95,36.6)') == 3
source = source.replace('(54.95,36.6)', '(54.95,36.5)')
assert source.count('(65.8,35.9)') == 2
source = source.replace('(65.8,35.9)', '(64.825,36.9)')
# A new fixed DNP/open requirement is independently exercised before authoring.
change("'5 failed, 1 passed' in red.stdout", "'6 failed, 1 passed' in red.stdout")
change("'4 failed, 2 passed' in focused.stdout", "'4 failed, 3 passed' in focused.stdout")

OUT.mkdir(exist_ok=True)
(OUT/'corrected-author.py').write_text(source)
def retain_partial():
    patch=subprocess.check_output(['git','diff','--binary','ff953c03c452f1572602b52aa62f42e80bfa9588'],cwd=ROOT)
    (OUT/'partial-source.patch').write_bytes(patch)
atexit.register(retain_partial)
checks = Path(os.environ['GITHUB_WORKSPACE'])/'workbench/l5_r24_checks.py'
logpath = OUT/'author-console.log'
try:
    with logpath.open('w') as log:
        before=subprocess.run(['/usr/bin/python3',str(checks),'before'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=120)
        assert before.returncode==0, 'new R24 fail-first requirements did not produce the expected failures'
        with contextlib.redirect_stdout(log):
            exec(compile(source,str(OUT/'corrected-author.py'),'exec'), {'__name__':'__main__'})
        after=subprocess.run(['/usr/bin/python3',str(checks),'after'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=780)
        assert after.returncode==0, 'R24 diagnostics are not all resolved'
finally:
    text=logpath.read_text()[-14000:] if logpath.exists() else 'author did not start'
    print(text)
    print('::notice title=R24 diagnostic tail::'+text.replace('%','%25').replace('\r','%0D').replace('\n','%0A'))
