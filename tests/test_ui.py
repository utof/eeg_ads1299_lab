from pathlib import Path
import shutil
import subprocess
import pytest
ROOT=Path(__file__).resolve().parents[1]


def test_interactive_headroom_calculator_matches_expected_boundaries():
    node=shutil.which('node')
    if not node:pytest.skip('Node unavailable; UI arithmetic not rerun')
    script="""
const assert=require('node:assert/strict');
const {headroom}=require('./ui/explorer.js');
let h=headroom(24,30,2.5);
assert.equal(h.valid,true);assert.equal(h.fullScaleMv,187.5);
assert.ok(Math.abs(h.lsbUv-0.022351741790771484)<1e-14);
assert.equal(headroom(24,300,2.5).valid,false);
assert.equal(headroom(12,300,2.5).valid,true);
assert.equal(headroom(24,30,0.1).commonOK,false);
assert.throws(()=>headroom(3,0,2.5));
"""
    result=subprocess.run([node,'-e',script],cwd=ROOT,capture_output=True,text=True)
    assert result.returncode==0,result.stderr


def test_html_has_no_remote_dependencies_and_keeps_wiring_boundary():
    text=(ROOT/'START_HERE.html').read_text()
    assert '<script src="http' not in text
    assert 'Power' in text and 'board schematic' in text
    assert 'not a complete circuit' in text
    assert 'ui/explorer.js' in text
