#!/usr/bin/python3
"""Authorized one-field Qmax test: 7720 -> own Def0 8794 mAh.
Fixed scope; fresh backup, staged verification, checksum commit, readback, RESET.
No cycle counter, Ra, chemistry, calibration, security or ROM changes.
"""
from pathlib import Path
import datetime,hashlib,json,os,sys,time,shutil
from read_bq_via_ec import Bridge,crc,root

class TestBridge(Bridge):
 def __init__(self,r,out):super().__init__(r);self.out=out;self.allowed_writes={};self.rollback=False
 def save(self):
  p=self.out/'report.json';tmp=self.out/'report.json.tmp'
  with tmp.open('w') as f:json.dump(self.report,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
  tmp.replace(p)
 def setreg(self,reg,value):
  assert reg in (0x17,0x18,0x19,0x1a,0x1b,0x1c,0x1d)
  if reg==0x18:assert value in (6,7,8,9)
  p=bytes([0x65,16,reg,value])+bytes(14);p+=bytes([crc(bytes([32])+p)])
  self.report['events'].append(dict(op='ec_request_register',reg=hex(reg),value=value))
  self.xfer([(0,p)]);time.sleep(.04)
 def request(self,reg,proto=9,value=None):
  if value is None:
   assert (proto==9 and (reg in (0,6,8,10,18,28,30,32,46,0x3e) or reg in range(0x40,0x60,2))) or (proto==7 and reg in (0x60,0x61,0x6a))
  else:
   assert (proto==8 and reg==0 and value in (0,1,2,8,31,0x41)) or (proto==8 and reg==0x3e and 0<=value<=65535) or (proto==6 and reg==0x61 and value in (0,1)) or (proto==6 and reg in self.allowed_writes and value==self.allowed_writes[reg])
  time.sleep(max(0,.6-(time.monotonic()-self.last)))
  if self.readblock(0xf1)[8]:raise RuntimeError('EC request busy')
  self.changed=True
  for r,v in ((0x17,0),(0x1a,0xaa),(0x1b,reg)):self.setreg(r,v)
  if value is not None:
   self.setreg(0x1c,value&255)
   if proto==8:self.setreg(0x1d,value>>8)
  for _ in range(15):
   s=self.readblock(0xf1)
   if s[7]&3 or s[8] or s[10]!=0xaa or s[11]!=reg:raise RuntimeError('EC selector mismatch '+s.hex())
   if not s[7]&0x10:break
   time.sleep(.08)
  else:raise RuntimeError('Internal I2C bus busy')
  if value is not None:
   actual=int.from_bytes(s[12:14],'little') if proto==8 else s[12]
   if actual!=value:raise RuntimeError('EC outgoing data mismatch')
  event=dict(op='bq_transaction',register=hex(reg),protocol=proto,value=value,rollback=self.rollback)
  self.report['events'].append(event)
  if value is not None and (reg in range(0x40,0x61) or (reg==0 and value==0x41)):self.save()
  self.last=time.monotonic();self.setreg(0x18,proto)
  end=time.monotonic()+3
  while True:
   s=self.readblock(0xf1)
   if not s[8]:break
   if time.monotonic()>end:raise RuntimeError('EC completion timeout')
   time.sleep(.1)
  event['status']=s[9]
  if s[9]!=128:raise RuntimeError('BQ transaction failed '+hex(s[9]))
  return s[12] if proto in (6,7) else int.from_bytes(s[12:14],'little')
 def control(self,selector):self.request(0,8,selector);return self.request(0)
 def select(self,cls):
  self.request(0x3e,8,cls)
  if self.request(0x3e)!=cls:raise RuntimeError('Class/block mismatch')
 def window(self):return b''.join(self.request(reg).to_bytes(2,'little') for reg in range(0x40,0x60,2))
 def block(self,cls):
  self.select(cls);b=self.window();c=self.request(0x60,7)
  if c!=(255-sum(b))&255:raise RuntimeError('DataFlash checksum mismatch')
  return b
 def snapshot(self):
  a={name:self.request(reg) for reg,name in [(8,'voltage_mV'),(6,'temperature_0p1K'),(10,'flags'),(18,'fcc_mAh'),(28,'soh_raw'),(30,'cycles'),(32,'soc_pct'),(46,'design_mAh')]}
  a['control_status']=self.control(0);a['application_status']=self.request(0x6a,7)
  return a
 def persistent(self,original,candidate):
  assert len(original)==len(candidate)==32
  self.select(82);current=self.window()
  if current!=original:raise RuntimeError('State changed before staging; no commit')
  self.allowed_writes={0x40+i:candidate[i] for i in range(32) if original[i]!=candidate[i]}
  for reg,val in self.allowed_writes.copy().items():self.request(reg,6,val)
  staged=self.window()
  if staged!=candidate:raise RuntimeError('Staging mismatch; no checksum commit')
  checksum=(255-sum(candidate))&255;self.allowed_writes={0x60:checksum}
  self.report['commit_attempted']=True;self.save();self.request(0x60,6,checksum);time.sleep(.3)
  self.allowed_writes={}
  self.select(0);readback=self.block(82)
  if readback!=candidate:raise RuntimeError('Persistent full-block readback mismatch')
  self.report['commit_verified']=True;self.save()


def main():
 if sys.argv[1:]!=['--apply-reviewed-qmax-test']:raise SystemExit('Requires --apply-reviewed-qmax-test; fixed authorized Qmax-only experiment')
 stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S');out=root/('qmax-test-'+stamp);out.mkdir()
 report=dict(timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='Qmax0 7720 -> 8794 only; one BQ RESET; preserve cycles/Ra/calibration',events=[])
 bridge=TestBridge(report,out);old_select=old_control=None;original=None;candidate=None;changed_select=False;secondary=None
 try:
  bridge.open();report['before_gauge']=bridge.snapshot()
  identity={name:bridge.control(sel) for sel,name in [(1,'device'),(2,'firmware'),(8,'chemistry'),(31,'dfversion')]};report['identity']=identity
  assert identity==dict(device=0x510,firmware=0x400,chemistry=0x3353,dfversion=0x2202),'Unexpected gauge identity'
  before=report['before_gauge'];assert before['application_status']&3==0,'Unexpected active/unsupported profile'
  assert not before['control_status']&0x6000,'Gauge sealed'
  assert before['voltage_mV']>=3800 and 2832<=before['temperature_0p1K']<=3132,'Voltage/temperature precondition'
  old_select=bridge.request(0x3e);old_control=bridge.request(0x61,7);assert old_control in (0,1)
  report['original_selectors']=[old_select,old_control];changed_select=True;bridge.request(0x61,6,0)
  backups={cls:bridge.block(cls) for cls in (82,83,91,93)}
  original=backups[82];assert int.from_bytes(original[2:4],'big')==7720,'Qmax changed since authorized plan'
  assert original[6]==2 and original[1]&3==0,'Unexpected learning/profile state'
  ref=backups[83];assert ref[:2]==b'\x33\x53' and int.from_bytes(ref[2:4],'big')==8794,'Reference profile differs'
  candidate=bytearray(original);candidate[2:4]=ref[2:4];candidate=bytes(candidate)
  for cls,b in backups.items():
   p=out/f'before-class-{cls}.bin'
   with p.open('wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
  secondary=Path('/var/backups')/('venue5055-qmax-'+stamp);secondary.mkdir()
  for p in out.glob('before-class-*.bin'):shutil.copy2(p,secondary/p.name)
  report['secondary_backup']=str(secondary)
  report['before_state']=original.hex();report['candidate_state']=candidate.hex();report['changed_offsets']=[i for i in range(32) if original[i]!=candidate[i]]
  assert report['changed_offsets']==[2,3]
  bridge.save();print('Preflight passed. Fresh backups:',out,secondary,flush=True)
  bridge.persistent(original,candidate);print('Qmax persistent write verified: only offsets 2 and 3 changed.',flush=True)
  report['reset_attempted']=True;bridge.save();bridge.request(0,8,0x41);time.sleep(2)
  report['after_gauge']=bridge.snapshot()
  afterstate=bridge.block(82);(out/'after-class-82.bin').write_bytes(afterstate)
  report['after_state']=afterstate.hex()
  assert report['after_gauge']['control_status']&0x80,'Gauge initialization incomplete'
  assert report['after_gauge']['control_status']&1,'Qmax updates disabled after RESET'
  assert report['after_gauge']['application_status']&3==0,'Gauge selected another profile'
  assert int.from_bytes(afterstate[2:4],'big')==8794,'Qmax did not survive RESET'
  assert afterstate[4:12]==original[4:12],'Cycles/UpdateStatus/second Qmax changed'
  report['resistance_unchanged']={}
  for cls in (91,93):
   b=bridge.block(cls);(out/f'after-class-{cls}.bin').write_bytes(b);report['resistance_unchanged'][str(cls)]=b==backups[cls]
  assert all(report['resistance_unchanged'].values()),'Resistance table changed'
  report['success']=True;print('Post-RESET results:',json.dumps(report['after_gauge']),flush=True)
 except Exception as e:
  report.update(success=False,error=str(e));print('Stopped:',e,flush=True)
  if report.get('commit_attempted') and original is not None:
   try:
    bridge.rollback=True;current=bridge.block(82)
    if current!=original:bridge.persistent(current,original)
    report['rollback_verified']=bridge.block(82)==original
    if report.get('reset_attempted') or report['rollback_verified']:
     bridge.request(0,8,0x41);time.sleep(2)
    report['rollback_gauge']=bridge.snapshot()
    print('Rollback:',report['rollback_verified'],flush=True)
   except Exception as re:report['rollback_error']=str(re);print('Rollback error:',re,flush=True)
 finally:
  if changed_select:
   try:
    bridge.request(0x3e,8,old_select);bridge.request(0x61,6,old_control)
    report['gauge_selectors_restored']=bridge.request(0x3e)==old_select and bridge.request(0x61,7)==old_control
   except Exception as e:report['selector_restore_error']=str(e)
  try:bridge.close()
  except Exception as e:report['ec_restore_error']=str(e)
  bridge.save()
  if secondary:
   shutil.copy2(out/'report.json',secondary/'report.json')
  print('Report:',out/'report.json',flush=True)
if __name__=='__main__':main()
