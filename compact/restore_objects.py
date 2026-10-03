"""One-use, hash-gated transport repair. Never a product dependency or layout generator."""
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import sys
import tempfile
import zlib

ROOT = Path(sys.argv[1]).resolve()
INPUT = Path(sys.argv[2]).resolve()
BASE = '3926fa02816b6812bcacd6113db180278186c258'
HEAD = '87c0d7e93d4dd0c4be4a410732c3a84d34151693'
TREE = 'c9d71ca4a31b3bca65b9c5a64cbb7f20eb9860c1'
BOARD = '7c02996c61e9ea4b4c854ad9424d11a121e1a7eb'
sha = lambda b: hashlib.sha256(b).hexdigest()

def git(*args, data=None):
    return subprocess.check_output(['git', *args], cwd=ROOT, input=data)

assert git('rev-parse', 'HEAD').decode().strip() == BASE
assert not git('status', '--porcelain')
parts = ['000', '001', '002', '003', '006', '009', '012', '015', '018', '021']
prefix = b''.join((INPUT/'old'/'parts'/f'{n}.txt').read_bytes().strip() for n in parts)[:21000]
assert sha(prefix) == 'b894f52924ff7d14e81aae46c525380f8ebc950fa326cf973227417cc21ac4d3'
extra = (INPUT/'prefix.txt').read_bytes().strip()
assert len(extra) == 1000 and sha(extra) == '61b7b12b8eccbf247fed43ad0fb0a3a130593ac80f36b26fa05a5d4b72f2ecad'
raw = base64.b64decode(prefix+extra, validate=True)
assert raw.index(b'PACK') == 178
pack = raw[178:]
assert struct.unpack('>4sII', pack[:12]) == (b'PACK', 2, 48)
objects = {}
names = {1:'commit', 2:'tree', 3:'blob', 4:'tag'}

def varint(data, i):
    value = shift = 0
    while True:
        b = data[i]; i += 1; value |= (b & 127) << shift
        if not b & 128: return value, i
        shift += 7
        assert shift < 64

def apply_delta(base, delta, partial=False):
    length, i = varint(delta, 0)
    expected, i = varint(delta, i)
    assert length == len(base)
    output = []
    while i < len(delta):
        opcode = delta[i]; i += 1
        try:
            if opcode & 128:
                offset = size = 0
                for j in range(4):
                    if opcode & (1 << j): offset |= delta[i] << (8*j); i += 1
                for j in range(3):
                    if opcode & (16 << j): size |= delta[i] << (8*j); i += 1
                size = size or 65536
                assert offset+size <= len(base)
                output.append(base[offset:offset+size])
            else:
                assert opcode
                if i+opcode > len(delta):
                    assert partial
                    break
                output.append(delta[i:i+opcode]); i += opcode
        except IndexError:
            assert partial
            break
    result = b''.join(output)
    assert partial or len(result) == expected
    return result

def read_object(data, position, origin=0, partial=False):
    start = position
    b = data[position]; position += 1
    kind = (b >> 4) & 7
    size = b & 15; shift = 4
    while b & 128:
        b = data[position]; position += 1
        size |= (b & 127) << shift; shift += 7
    source = None
    if kind == 6:
        b = data[position]; position += 1; distance = b & 127
        while b & 128:
            b = data[position]; position += 1
            distance = ((distance+1) << 7) + (b & 127)
        source = objects[origin+start-distance]
    elif kind == 7:
        oid = data[position:position+20].hex(); position += 20
        source = (git('cat-file', '-t', oid).decode().strip(), git('cat-file', '-p', oid))
        # Trees need raw binary, not the human-readable -p representation.
        source = (source[0], git('cat-file', source[0], oid))
    decoder = zlib.decompressobj()
    decoded = decoder.decompress(data[position:])
    end = len(data)-len(decoder.unused_data)
    if not partial: assert decoder.eof and len(decoded) == size
    else: assert not decoder.eof
    if source:
        name, base = source
        content = apply_delta(base, decoded, partial=partial)
    else:
        name, content = names[kind], decoded
    return name, content, end

def store(offset, name, content):
    oid = hashlib.sha1(f'{name} {len(content)}\0'.encode()+content).hexdigest()
    actual = git('hash-object', '-w', '-t', name, '--stdin', data=content).decode().strip()
    assert actual == oid
    objects[offset] = (name, content)
    return oid

pos = 12
while pos < 11744:
    begin = pos
    name, data, pos = read_object(pack, pos)
    store(begin, name, data)
assert pos == 11744 and len(objects) == 18
name, partial_board, _ = read_object(pack, pos, partial=True)
assert name == 'blob'
# Entire authored track/via/rule-area prefix is already present. Supply only the
# two explicit zone outlines, then refill their derived caches in a temporary copy.
marker = b'(zone\n\t\t(net 24)\n\t\t(net_name "HOST_GND")'
assert partial_board.count(marker) == 1
unfilled = partial_board[:partial_board.index(marker)].decode()
for net, label, ident, left, right in [
    (24, 'HOST_GND', '1da15d33-7608-547a-9365-c93c6c77efb1', '0.5', '20.25'),
    (40, 'TARGET_GND', '81952ffc-dd7f-5880-a07c-cb7c615be34b', '23.75', '89.5')]:
    unfilled += f'''(zone
        (net {net}) (net_name "{label}") (layer "In1.Cu") (uuid "{ident}")
        (name "P2_{label}_REFERENCE") (hatch edge 0.5)
        (connect_pads thru_hole_only (clearance 0.25)) (min_thickness 0.2)
        (filled_areas_thickness no)
        (fill yes (thermal_gap 0.25) (thermal_bridge_width 0.3))
        (polygon (pts (xy {left} 0.5) (xy {right} 0.5) (xy {right} 74.5) (xy {left} 74.5)))
)
'''
unfilled += ')\n'

def forms(text):
    depth = 0; start = 0; quoted = escape = False
    for i, c in enumerate(text):
        if quoted:
            if escape: escape = False
            elif c == '\\': escape = True
            elif c == '"': quoted = False
        elif c == '"': quoted = True
        elif c == '(':
            if depth == 1: start = i
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 1: yield start, i+1, text[start:i+1]
    assert depth == 0 and not quoted

with tempfile.TemporaryDirectory(prefix='p2-cache-recovery-') as temp:
    temp = Path(temp)
    src = temp/'input.kicad_pcb'; dst = temp/'filled.kicad_pcb'
    src.write_text(unfilled)
    subprocess.run([os.environ.get('KICAD_PYTHON', '/usr/bin/python3'), '-c',
        'import pcbnew as p,sys;assert p.Version()=="9.0.2";'
        'b=p.LoadBoard(sys.argv[1]);p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(sys.argv[2],b)',
        str(src), str(dst)], check=True, timeout=45)
    filled = {re.search(r'\(uuid "([^"]+)"', z).group(1):z
              for _, _, z in forms(dst.read_text()) if z.startswith('(zone') and '(filled_polygon' in z}
    assert len(filled) == 2
    restored = unfilled
    for a, b, z in reversed(list(forms(unfilled))):
        if z.startswith('(zone') and 'P2_' in z:
            ident = re.search(r'\(uuid "([^"]+)"', z).group(1)
            restored = restored[:a]+filled[ident]+restored[b:]
    restored = restored.encode()
    assert sha(restored) == '57e54660e1cb99f74091f4d7e43ce4a942171a477320cf630a8343d72cf86d1c'
    assert store(11744, 'blob', restored) == BOARD
recipes = []
for index in range(4):
    recipes.extend(json.loads(line) for line in (INPUT/'readable'/f'recipe{index:02d}.jsonl').read_text().splitlines())
assert len(recipes) == 29
for index, spec in enumerate(recipes):
    if 'file' in spec:
        data = (INPUT/'readable'/spec['file']).read_bytes()
    elif 'hex' in spec:
        data = bytes.fromhex(spec['hex'])
    else:
        base = git('cat-file', spec['type'], spec['base'])
        chunks = []
        for operation in spec['ops']:
            if operation[0] == 'copy':
                _, offset, size = operation
                assert 0 <= offset and offset+size <= len(base)
                chunks.append(base[offset:offset+size])
            elif operation[0] == 'text':
                chunks.append(operation[1].encode())
            else:
                assert operation[0] == 'hex'
                chunks.append(bytes.fromhex(operation[1]))
        data = b''.join(chunks)
        assert len(data) == spec['size']
    actual = store(35561+index, spec['type'], data)
    assert actual == spec['oid'], (spec['oid'], actual)
assert len(objects) == 48
assert git('rev-parse', HEAD+'^{tree}').decode().strip() == TREE
assert git('rev-list', '--count', BASE+'..'+HEAD).decode().strip() == '8'
subprocess.run(['git', 'fsck', '--full', '--no-dangling', HEAD], cwd=ROOT, check=True)
print('RESTORED exact original eight commits, board bytes, and tree', HEAD, TREE)
