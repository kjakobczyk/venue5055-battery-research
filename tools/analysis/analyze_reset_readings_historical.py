#!/usr/bin/python3
"""Offline decode of checksum-verified diagnostic files; no device access."""
from pathlib import Path
import json,hashlib
root=Path(__file__).resolve().parent
blocks={};sources={}
for folder in sorted(root.glob('dataflash-*')):
 if not folder.is_dir():continue
 for p in folder.glob('class-*-block-*.bin'):
  _,cls,_,blk=p.stem.split('-');key=(int(cls),int(blk));d=p.read_bytes()
  report=folder/'report.json'
  if not report.exists():report=folder/'progress.json'
  if not report.exists():continue
  meta=json.loads(report.read_text());m=next((x for x in meta.get('blocks',[]) if (x['subclass'],x['block'])==key),None)
  if m and m['checksum_valid'] and m['hex']==d.hex() and len(d)==32:
   blocks[key]=d;sources[key]=str(p)
def get(cls,offset,n=1,signed=False):
 try:b=b''.join(blocks[(cls,k)] for k in range((offset+n-1)//32+1))
 except KeyError:return None
 return int.from_bytes(b[offset:offset+n],'big',signed=signed)
fields={
 'design_capacity_mAh':(48,10,2,False),'soh_load_mA':(48,13,2,True),'cc_threshold_mAh':(48,7,2,False),
 'charging_voltage_mV':(34,2,2,False),'taper_current_mA':(36,2,2,False),'taper_voltage_mV':(36,6,2,False),
 'sysdown_set_voltage_mV':(49,5,2,False),'sysdown_clear_voltage_mV':(49,8,2,False),
 'default_average_current_mA':(49,14,2,True),'default_average_power_mW':(49,16,2,True),
 'load_select':(80,0,1,False),'load_mode':(80,1,1,False),'terminate_voltage_mV':(80,46,2,True),
 'reserve_capacity_mAh':(80,59,2,False),'reserve_energy':(80,61,2,False),
 'user_rate_mA':(80,55,2,True),'user_rate_power':(80,57,2,True),
 'min_passed_charge_for_qmax_pct':(80,40,1,False),'qmax_filter':(80,44,1,False),'max_default_qmax_pct':(80,45,1,False),
 'qmax_max_delta_pct':(80,72,1,False),'ra_max_delta':(80,70,2,False),
 'discharge_threshold_mA':(81,0,2,False),'charge_threshold_mA':(81,2,2,False),'quit_current_mA':(81,4,2,False),
 'discharge_relax_time_s':(81,6,2,False),'charge_relax_time_s':(81,8,1,False),
 'it_enable':(82,0,1,False),'application_status':(82,1,1,False),
 'qmax0_mAh':(82,2,2,False),'cycle_count0':(82,4,2,False),'update_status0':(82,6,1,False),
 'qmax1_mAh':(82,7,2,False),'cycle_count1':(82,9,2,False),'update_status1':(82,11,1,False),
 'average_current_last_run_mA':(82,12,2,True),'average_power_last_run':(82,14,2,True),
 'default0_chem_id':(83,0,2,False),'default0_qmax_mAh':(83,2,2,False),'default0_update_status':(83,4,1,False),
 'default1_chem_id':(84,0,2,False),'default1_qmax_mAh':(84,2,2,False),'default1_update_status':(84,4,1,False),
 'opconfig':(64,0,2,False),'opconfig_b':(64,11,1,False),'opconfig_c':(64,12,1,False),'opconfig_d':(64,13,1,False),'opconfig_e':(64,14,1,False),
}
out={'fields':{k:get(*v) for k,v in fields.items()},'resistance_tables':{},'sources':{f'{k[0]}:{k[1]}':v for k,v in sources.items()}}
for cls in (87,88,91,92,93,94):
 if (cls,0) not in blocks:continue
 b=blocks[cls,0];base=int.from_bytes(b[2:4],'big',signed=True);gain=b[4]
 deltas=[int.from_bytes(bytes([x]),'big',signed=True) for x in b[5:19]]
 vals=[base]
 if gain<=15:
  for d in deltas:vals.append(vals[-1]+d*2**gain)
 else:vals=[]
 out['resistance_tables'][str(cls)]={'status':hex(b[0]),'flag':hex(b[1]),'base_r':base,'gain':gain,'deltas':deltas,'decompressed_native_units':vals,'encoding_note':'SLUA450 cumulative BaseR+sum(delta)*2**Gain; native scale not independently calibrated','raw':b.hex()}
f=out['fields']
if f['application_status'] is not None:out['last_used_profile']=f['application_status']&1
(root/'reset-readings-decoded.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
