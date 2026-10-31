#!/usr/bin/python3
"""Statically extract GenCAD components, pins and battery communication routes."""
from pathlib import Path
import hashlib,json,shlex
root=Path(__file__).resolve().parent
source=next(root.glob('*.cad'))
components={};nets={};pins={};section='';component=None;signal=None
for line in source.read_text().splitlines():
 if line.startswith('$'):section=line;continue
 t=shlex.split(line)
 if not t:continue
 if section=='$COMPONENTS':
  if t[0]=='COMPONENT':component=t[1];components[component]={}
  elif t[0] in ('PLACE','LAYER','ROTATION','SHAPE','DEVICE'):components[component][t[0]]=t[1:]
  elif t[0]=='ATTRIBUTE' and len(t)>3 and t[2]=='VALUE':components[component]['value']=t[3]
 if section=='$SIGNALS':
  if t[0]=='SIGNAL':signal=t[1];nets[signal]=[]
  elif t[0]=='NODE':nets[signal].append(t[1:3]);pins.setdefault(t[1],{})[t[2]]=signal
assert 'BQ27510' in components['PU4401']['value']
assert 'NPCE948' in components['U4101']['value']
expected={
 'PU4401':{'11':'FG_I2C_SCL','10':'FG_I2C_SDA'},
 'PR4406':{'1':'FG_I2C_SCL','2':'I2C_0_SCL_EC'},
 'PR4405':{'1':'FG_I2C_SDA','2':'I2C_0_SDA_EC'},
 'R4106':{'1':'I2C_0_SCL_EC','2':'I2C_0_SCL_EC_1'},
 'R4107':{'1':'I2C_0_SDA_EC','2':'I2C_0_SDA_EC_1'},
 'R4111':{'1':'I2C_0_SCL','2':'I2C_0_SCL_EC_2'},
 'R4112':{'1':'I2C_0_SDA','2':'I2C_0_SDA_EC_2'},
 'R4122':{'1':'I2C_0_SCL','2':'I2C_0_SCL_EC'},
 'R4123':{'1':'I2C_0_SDA','2':'I2C_0_SDA_EC'},
 'U4101':{'B8':'I2C_0_SCL_EC_1','C8':'I2C_0_SDA_EC_1','E2':'I2C_0_SCL_EC_2','F2':'I2C_0_SDA_EC_2'},
 'CPU1':{'AD12':'I2C_0_SCL','AE12':'I2C_0_SDA'}}
for c,required in expected.items():
 for pin,net in required.items():assert pins[c][pin]==net,(c,pin)
(root/'netlist.json').write_text(json.dumps({'components':components,'nets':nets,'pins':pins},indent=2))
report={'source':source.name,'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
 'verified_routes':expected,'components':{c:components[c] for c in expected},
 'limitation':'CAD connectivity does not establish actual population of optional links in the physical tablet.'}
(root/'battery-routing.json').write_text(json.dumps(report,indent=2))
print('PASS: BQ27510 -> EC port 1; CPU -> EC port 2; optional R4122/R4123 bridge routes verified in CAD')
