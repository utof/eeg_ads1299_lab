"""Reconstruct original hash-bound Git objects in a disposable worktree only."""
import base64, hashlib, json, lzma, pathlib, subprocess, sys
payload, root = map(pathlib.Path, sys.argv[1:3])
data=payload.read_bytes()
assert len(data)==47012
assert hashlib.sha256(data).hexdigest()=='6514e28931f164c977eae0963dadeee28b77a7dc1ef61841ab245d85989c4373'
envelope=json.loads(lzma.decompress(data))
def git(*args, data=None):
    return subprocess.check_output(['git',*args],cwd=root,input=data)
def oid(kind,data):
    return hashlib.sha1(kind.encode()+b' '+str(len(data)).encode()+b'\0'+data).hexdigest()
assert git('rev-parse','HEAD').decode().strip()=='98362c6b6445ddb402ddf942b1c81af738eebe56'
assert not git('status','--porcelain')
helper=root.parent/'original_auxiliary_author.py'
helper.write_text(envelope['author_auxiliary_py'])
for step in envelope['steps']:
    before=git('rev-parse','HEAD').decode().strip()
    raw=step['raw_commit'].encode()
    assert oid('commit',raw)==step['commit']
    assert raw.decode().splitlines()[1]=='parent '+before
    for entry in step['files']+step['generated']:
        path=pathlib.PurePosixPath(entry['path'])
        assert not path.is_absolute() and '..' not in path.parts
        assert path.parts[0] in ('hardware','tests','docs','tools','tach.toml')
        assert entry['mode']=='100644'
        existing=git('ls-files','-s','--',str(path)).decode().split()
        assert (existing[1] if existing else '0'*40)==entry['old'],str(path)
    if step['generated']:
        assert not (root/'hardware/rev_a/auxiliary').exists()
        subprocess.run([sys.executable,str(helper),str(root)],check=True,cwd=root)
    for entry in step['files']:
        if 'base64' in entry:
            content=base64.b64decode(entry['base64'],validate=True)
        else:
            lines=[] if entry['old']=='0'*40 else git('cat-file','blob',entry['old']).decode().splitlines(keepends=True)
            parts=[]
            for part in entry['lines']:
                if isinstance(part,str):parts.append(part)
                else:
                    assert len(part)==2 and 0<=part[0]<=part[1]<=len(lines)
                    parts.extend(lines[part[0]:part[1]])
            content=''.join(parts).encode()
        assert oid('blob',content)==entry['new'],entry['path']
        file=root/entry['path'];file.parent.mkdir(parents=True,exist_ok=True);file.write_bytes(content)
    for entry in step['files']+step['generated']:
        content=(root/entry['path']).read_bytes()
        assert oid('blob',content)==entry['new'],entry['path']
        assert git('hash-object','-w','--stdin',data=content).decode().strip()==entry['new']
        git('update-index','--add','--cacheinfo',entry['mode']+','+entry['new']+','+entry['path'])
    tree=git('write-tree').decode().strip()
    assert raw.decode().splitlines()[0]=='tree '+tree,tree
    assert git('hash-object','-t','commit','-w','--stdin',data=raw).decode().strip()==step['commit']
    git('reset','--hard',step['commit'])
    assert not git('status','--porcelain')
    print(step['commit'],tree,flush=True)
assert git('rev-parse','HEAD').decode().strip()=='d0a9e3acf6ec96f966adcd4258a1ffe48bc3f586'
assert git('rev-parse','HEAD^{tree}').decode().strip()=='49a8cc8b90f41ee7405e948a951975bbc6221d99'
