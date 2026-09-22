"""Machine-readable verification scope, including explicitly unavailable tools."""
from pathlib import Path
import datetime
import importlib.metadata
import json
import platform
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

def validate(root,require_ngspice=False):
    root=Path(root);out=root/'results/validation';out.mkdir(parents=True,exist_ok=True)
    proc=subprocess.run([sys.executable,'-m','pytest','-q','--junitxml='+str(out/'pytest.xml')],
                        cwd=root,capture_output=True,text=True,timeout=240)
    print(proc.stdout,end='');print(proc.stderr,end='',file=sys.stderr)
    (out/'pytest.log').write_text(proc.stdout+'\n'+proc.stderr)
    suites=ET.parse(out/'pytest.xml').getroot()
    count={key:sum(int(s.get(key,0)) for s in suites.iter('testsuite')) for key in ['tests','failures','errors','skipped']}
    from lab.analog import circuit_report
    spice_error=None
    try:circuit_report(out/'circuits',require_ngspice=require_ngspice)
    except (RuntimeError,AssertionError) as e:spice_error=str(e)
    versions={name:importlib.metadata.version(name) for name in ['numpy','scipy','matplotlib','scikit-learn','pytest']}
    report={
      'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
      'platform':platform.platform(),'python':sys.version,'versions':versions,
      'test_counts':count,'python_tests_passed':proc.returncode==0,
      'native_cpp_core':{'compiler':shutil.which('g++') or shutil.which('clang++'),
                        'scope':'CRC, signed 24-bit conversion, transport encoder only; test result in pytest.xml'},
      'ngspice':{'available':bool(shutil.which('ngspice')),'required':require_ngspice,'error':spice_error,
                 'executed':bool(shutil.which('ngspice')) and spice_error is None},
      'esp32_target_compile':{'status':'not_run','reason':'ESP32 Arduino toolchain unavailable in this environment'},
      'visual_guide':{'node_available':bool(shutil.which('node')),
                       'arithmetic_scope':'Node regression tests in pytest; not full browser behavior',
                       'browser_render':'not_run',
                       'reason':'Playwright package present but Chromium executable unavailable'},
      'physical_hardware_test':{'status':'not_run','reason':'No actual ADS1299/ESP32 board connected'},
      'body_connection_authorized':False,
      'overall_scope':'Software/numerical-model verification only; NOT full hardware validation'
    }
    (root/'VALIDATION.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
    if proc.returncode or spice_error:return 1
    return 0
