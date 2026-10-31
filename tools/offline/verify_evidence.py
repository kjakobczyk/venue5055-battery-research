#!/usr/bin/env python3
"""Verify the released evidence without device access or third-party packages."""
import hashlib,json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def load(p):return json.loads((ROOT/p).read_text())
def crc8(data):
 c=0
 for v in data:
  c^=v
  for _ in range(8):c=((c<<1)^7 if c&128 else c<<1)&255
 return c
def main():
 manifest=load('evidence/manifest.json')
 for record in manifest['records']:
  p=ROOT/record['release_relative'];b=p.read_bytes()
  assert len(b)==record['bytes'] and hashlib.sha256(b).hexdigest()==record['release_sha256'],p
 d=load('evidence/intervention/report.json');base=ROOT/'evidence/intervention'
 old=(base/'before-class-82.bin').read_bytes();new=(base/'after-class-82.bin').read_bytes()
 assert old.hex()==d['before_state'] and new.hex()==d['after_state']==d['candidate_state']
 assert [i for i in range(32) if old[i]!=new[i]]==[2,3]
 assert int.from_bytes(old[2:4],'big')==7720 and int.from_bytes(new[2:4],'big')==8794
 assert (255-sum(old))&255==0xe2 and (255-sum(new))&255==0xac
 assert old[:2]==new[:2] and old[4:]==new[4:]
 for cls in (91,93):assert (base/f'before-class-{cls}.bin').read_bytes()==(base/f'after-class-{cls}.bin').read_bytes()
 assert d['success'] and d['gauge_selectors_restored'] and d['volatile_registers_restored']
 tr=[e for e in d['events'] if e.get('op')=='bq_transaction']
 writes=[e for e in tr if e['protocol']==6 and 0x40<=int(e['register'],16)<=0x60]
 assert [(int(e['register'],16),e['value']) for e in writes]==[(0x42,0x22),(0x43,0x5a),(0x60,0xac)]
 assert sum(e['protocol']==8 and e['register']=='0x0' and e['value']==0x41 for e in tr)==1
 assert d['before_gauge']['fcc_mAh']==5973 and d['after_gauge']['fcc_mAh']==6827
 assert d['before_gauge']['cycles']==d['after_gauge']['cycles']==49
 # Read all recorded EC block replies; reject malformed CRCs, not just bad values.
 packet_count=0
 for p in (ROOT/'evidence').rglob('*.json'):
  o=json.loads(p.read_text())
  for e in o.get('events',[]) if isinstance(o,dict) else []:
   if e.get('op')=='read_ec' or e.get('operation')=='read_ec_block':
    cmd=int(e['command'],16);b=bytes.fromhex(e.get('raw',e.get('response','')))
    assert len(b)==18 and b[0]==16 and crc8(bytes([0x20,cmd,0x21])+b[:-1])==b[-1],(p,e)
    packet_count+=1
 # Verify the 25 measured blocks against acquisition-session checksums.
 sessions=[load('evidence/dataflash/first-session.json'),load('evidence/dataflash/completed-session.json')]
 expected={}
 for session in sessions:
  assert session['gauge_selectors_restored'] and session['volatile_registers_restored']
  for item in session['blocks']:
   assert item['checksum_valid'];expected[item['subclass'],item['block']]=item
 files=list((ROOT/'evidence/dataflash/blocks').glob('*.bin'));assert len(files)==25
 for p in files:
  _,cls,_,blk=p.stem.split('-');b=p.read_bytes();e=expected[int(cls),int(blk)]
  assert b.hex()==e['hex'] and (255-sum(b))&255==e['checksum_received']
 initial=load('evidence/acpi/initial-reading.json');post=load('evidence/acpi/post-boot-verification.json')
 assert initial['sysfs']['POWER_SUPPLY_CHARGE_FULL']=='3459000'
 assert initial['ec']['full_mAh']==5973 and initial['sysfs']['POWER_SUPPLY_CAPACITY']=='173'
 assert post['override_active'] and post['dsdt_checksum_valid'] and post['voltage_matches_within_100mV'] and post['full_capacity_matches_ec']
 assert len(load('evidence/acpi/patch-proof.json')['changed_offsets'])==6
 probe=load('evidence/transport/direct-gauge-probes.json');assert len(probe['results'])==5 and all(x['errno']==121 for x in probe['results'])
 comp=load('evidence/firmware/EC-comparison.json');assert comp['byte_identical'] and comp['a04_sha256']==comp['a07_sha256']
 result={'artifacts_verified':len(manifest['records']),'ec_reply_frames_verified':packet_count,'dataflash_blocks_verified':len(files),'subject_count':1,'intervention':'Qmax0 change followed by one RESET','changed_state_offsets':[2,3],'qmax_before_mAh':7720,'qmax_after_mAh':8794,'fcc_before_mAh':5973,'fcc_after_mAh':6827,'fcc_change_mAh':854,'fcc_relative_change_pct':(6827/5973-1)*100,'fcc_design_before_pct':5973/8680*100,'fcc_design_after_pct':6827/8680*100,'soh_before_pct':78,'soh_after_pct':95,'cycle_count_unchanged':49,'runtime_capacity_measurement_performed':False,'reset_only_control_performed':False}
 print(json.dumps(result,indent=2))
 return result
if __name__=='__main__':main()
