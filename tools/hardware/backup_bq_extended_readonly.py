#!/usr/bin/python3
"""Extended backup of documented BQ DF blocks. Only selector writes; NEVER window/checksum writes.
Uses audited EC bridge, no unseal/reset/ROM commands, no arbitrary CLI.
"""
from pathlib import Path
import time,json,datetime
from read_bq_via_ec import Bridge,crc,root
class BackupBridge(Bridge):
 def setreg(self,reg,value):
  assert reg in (0x17,0x18,0x19,0x1a,0x1b,0x1c,0x1d)
  if reg==0x18:assert value in (6,7,8,9)
  p=bytes([0x65,16,reg,value])+bytes(14);p+=bytes([crc(bytes([32])+p)])
  self.report['events'].append(dict(op='volatile_ec_write',register=hex(reg),value=hex(value),packet=p.hex()))
  self.xfer([(0,p)]);time.sleep(.04)
 def select_or_read(self,reg,protocol=9,value=None,restoring=False):
  if value is None:
   assert (protocol==9 and (reg==0x3e or reg in range(0x40,0x60,2))) or (protocol==7 and reg in (0x60,0x61))
  else:
   assert (protocol==6 and reg==0x61 and value in (0,1)) or (protocol==8 and reg==0x3e and (restoring or value in (2, 32, 34, 36, 48, 49, 64, 68, 81, 82, 83, 84, 87, 88, 91, 92, 93, 94, 104, 107, 80, 336, 592, 106, 362)))
  time.sleep(max(0,.6-(time.monotonic()-self.last)))
  s=self.readblock(0xf1)
  if s[8]:raise RuntimeError('EC request busy')
  self.changed=True
  for r,v in ((0x17,0),(0x1a,0xaa),(0x1b,reg)):self.setreg(r,v)
  if value is not None:
   self.setreg(0x1c,value&255)
   if protocol==8:self.setreg(0x1d,value>>8)
  # Register 0x17 includes read-only live bus-status bits in addition to
  # low two channel-select bits (EC read dispatcher 0x4516).
  for attempt in range(12):
   s=self.readblock(0xf1)
   if s[7]&3 or s[8] or s[10]!=0xaa or s[11]!=reg:raise RuntimeError('Request selector mismatch: '+s.hex())
   if not (s[7]&0x10):break
   time.sleep(.08)
  else:raise RuntimeError('EC internal bus remains busy')
  if value is not None:
   actual=int.from_bytes(s[12:14],'little') if protocol==8 else s[12]
   if actual!=value:raise RuntimeError('Write-selector data readback mismatch')
  self.last=time.monotonic();self.setreg(0x18,protocol)
  deadline=time.monotonic()+2
  while True:
   s=self.readblock(0xf1)
   if s[8]==0:break
   if time.monotonic()>deadline:raise RuntimeError('EC request timeout')
   time.sleep(.1)
  if s[9]!=128:raise RuntimeError('Downstream failure '+hex(s[9]))
  v=int.from_bytes(s[12:14],'little')
  return v&255 if protocol in (6,7) else v

def main():
 stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S');out=root/('dataflash-extended-'+stamp);out.mkdir()
 report={'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'extended documented configuration backup; see block list; not a complete firmware or reserved-memory dump','events':[],'blocks':[]};bridge=BackupBridge(report);old_select=None;old_control=None;touched=False
 try:
  bridge.open()
  bridge.transaction(0,selector=0);status=bridge.transaction(0);report['control_status_before']=hex(status)
  if status&0x6000:raise RuntimeError('SEALED or full-access-sealed; no selector writes')
  old_select=bridge.select_or_read(0x3e);old_control=bridge.select_or_read(0x61,7)
  report['original_gauge_selectors']={'class_block_word':hex(old_select),'block_data_control':old_control}
  (out/'before.json').write_text(json.dumps({k:v for k,v in report.items() if k!='events'},indent=2)+'\n')
  if old_control not in (0,1):raise RuntimeError('Unexpected BlockDataControl value; stop')
  touched=True;bridge.select_or_read(0x61,6,0)
  for cls,block in [(36, 0), (48, 0), (49, 0), (64, 0), (68, 0), (81, 0), (82, 0), (83, 0), (84, 0), (87, 0), (88, 0), (91, 0), (92, 0), (93, 0), (94, 0), (104, 0), (107, 0), (80, 0), (80, 1), (80, 2), (106, 0), (106, 1)]:
   bridge.select_or_read(0x3e,8,cls+256*block)
   selected=bridge.select_or_read(0x3e)
   if selected!=cls+256*block:raise RuntimeError('DataFlash class/block readback mismatch')
   data=b''.join(bridge.select_or_read(reg).to_bytes(2,'little') for reg in range(0x40,0x60,2))
   received=bridge.select_or_read(0x60,7);expected=(255-sum(data))&255
   item=dict(subclass=cls,block=block,hex=data.hex(),checksum_received=received,checksum_expected=expected,checksum_valid=received==expected)
   report['blocks'].append(item);(out/f'class-{cls}-block-{block}.bin').write_bytes(data)
   (out/'progress.json').write_text(json.dumps(report,indent=2)+'\n')
   print(json.dumps(item),flush=True)
   if received!=expected:raise RuntimeError('DataFlash checksum mismatch; no interpretation')
  report['success']=True
 except Exception as e:report.update(success=False,error=str(e));print('Stopped:',e,flush=True)
 finally:
  if touched:
   try:
    bridge.select_or_read(0x3e,8,old_select,restoring=True)
    bridge.select_or_read(0x61,6,old_control)
    report['gauge_selectors_restored']=bridge.select_or_read(0x3e)==old_select and bridge.select_or_read(0x61,7)==old_control
   except Exception as e:report['gauge_restore_error']=str(e)
  try:bridge.close()
  except Exception as e:report['ec_restore_error']=str(e)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print('Saved',out,flush=True)
if __name__=='__main__':main()
