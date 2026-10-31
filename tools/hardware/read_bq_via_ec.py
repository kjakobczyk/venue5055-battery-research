#!/usr/bin/python3
"""Fixed diagnostic reads through Venue 5055 EC. No arbitrary commands.
Volatile EC writes set up SMBus reads. Gauge Control writes only select documented
read-only responses: status, device type, firmware, chemistry and DF version.
No unseal, reset, ROM entry, DataFlash configuration or persistent writes.
"""
from pathlib import Path
import ctypes,fcntl,os,time,json,hashlib,datetime
root=Path(__file__).resolve().parent
class Msg(ctypes.Structure):_fields_=[('addr',ctypes.c_uint16),('flags',ctypes.c_uint16),('len',ctypes.c_uint16),('buf',ctypes.POINTER(ctypes.c_uint8))]
class Transfer(ctypes.Structure):_fields_=[('msgs',ctypes.POINTER(Msg)),('nmsgs',ctypes.c_uint32)]
libc=ctypes.CDLL(None,use_errno=True);libc.ioctl.argtypes=[ctypes.c_int,ctypes.c_ulong,ctypes.c_void_p]
def crc(b):
 c=0
 for v in b:
  c^=v
  for _ in range(8):c=((c<<1)^7 if c&128 else c<<1)&255
 return c
class Bridge:
 def __init__(self,report):self.report=report;self.fd=None;self.old=None;self.changed=False;self.last=0
 def xfer(self,parts):
  bufs=[(ctypes.c_uint8*len(b))(*b) for _,b in parts]
  msgs=(Msg*len(parts))(*(Msg(16,f,len(buf),buf) for (f,_),buf in zip(parts,bufs)))
  tx=Transfer(msgs,len(parts));n=libc.ioctl(self.fd,0x707,ctypes.byref(tx))
  if n!=len(parts):raise OSError(ctypes.get_errno(),'I2C_RDWR')
  return [bytes(b) for b in bufs]
 def readblock(self,cmd):
  assert cmd in (0xf1,0xf2,0xf3,0xa2,0xa3)
  b=self.xfer([(0,bytes([cmd])),(1,bytes(18))])[1]
  self.report['events'].append(dict(op='read_ec',command=hex(cmd),raw=b.hex()))
  if b[0]!=16 or crc(bytes([32,cmd,33])+b[:-1])!=b[-1]:raise RuntimeError('EC CRC/length mismatch')
  return b[1:17]
 def setreg(self,reg,value):
  assert reg in (0x17,0x18,0x19,0x1a,0x1b,0x1c,0x1d)
  if reg==0x18:assert value in (8,9)
  p=bytes([0x65,16,reg,value])+bytes(14);p+=bytes([crc(bytes([32])+p)])
  self.report['events'].append(dict(op='volatile_ec_write',register=hex(reg),value=hex(value),packet=p.hex()))
  self.xfer([(0,p)]);time.sleep(.04)
 def transaction(self,reg,selector=None):
  assert (selector is None and reg in (0,6,8,10,12,14,16,18,20,28,30,32,40,46)) or (reg==0 and selector in (0,1,2,8,31))
  time.sleep(max(0,.6-(time.monotonic()-self.last)))
  state=self.readblock(0xf1)
  if state[8]:raise RuntimeError('EC host interface busy')
  self.changed=True
  for r,v in ((0x17,0),(0x1a,0xaa),(0x1b,reg)):self.setreg(r,v)
  if selector is not None:
   self.setreg(0x1c,selector);self.setreg(0x1d,0)
  state=self.readblock(0xf1)
  if not(state[7]==0 and state[8]==0 and state[10]==0xaa and state[11]==reg):raise RuntimeError('EC selector readback mismatch')
  if selector is not None and state[12:14]!=selector.to_bytes(2,'little'):raise RuntimeError('Control selector readback mismatch')
  self.last=time.monotonic();self.setreg(0x18,8 if selector is not None else 9)
  end=time.monotonic()+2
  while True:
   state=self.readblock(0xf1)
   if state[8]==0:break
   if time.monotonic()>end:raise RuntimeError('EC transaction timeout')
   time.sleep(.1)
  if state[9]!=128:raise RuntimeError('EC downstream status '+hex(state[9]))
  return int.from_bytes(state[12:14],'little')
 def open(self):
  for k,v in [('product_name','Venue 10 Pro 5055'),('board_name','084N67'),('bios_version','A04')]:assert Path('/sys/class/dmi/id/'+k).read_text().strip()==v
  assert 'I2C1' in Path('/sys/bus/i2c/devices/i2c-0/firmware_node/path').read_text()
  for ver in ('A04','A07'):assert hashlib.sha256((root/(ver+'-images')/'EC0.bin').read_bytes()).hexdigest()=='21e4efa3f1608539e47e5a8e1511c8f9cd0e3ac4703185555c85363135ab3bd8'
  self.lock=open(root/'ec-host-access.lock','a');fcntl.flock(self.lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  self.fd=os.open('/dev/i2c-0',os.O_RDWR|os.O_CLOEXEC);fcntl.ioctl(self.fd,0x703,16)
  self.old=self.readblock(0xf1)
  if self.old[8]:raise RuntimeError('EC busy before diagnostics')
  self.report['before']={hex(k):self.readblock(k).hex() for k in (0xf1,0xf2,0xf3,0xa2,0xa3)}
 def close(self):
  if self.fd is None:return
  try:
   if self.changed:
    state=self.readblock(0xf1)
    if state[8]:raise RuntimeError('EC still busy; no restore writes')
    for reg in (0x17,0x19,0x1a,0x1b,0x1c,0x1d):self.setreg(reg,self.old[reg-16])
    state=self.readblock(0xf1)
    self.report['after']={hex(k):self.readblock(k).hex() for k in (0xf1,0xa2,0xa3)}
    self.report['volatile_registers_restored']=all(state[x]==self.old[x] for x in (7,8,9,10,11,12,13))
  finally:os.close(self.fd);self.fd=None

def main():
 report={'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),'events':[],'standard':{},'control':{}}
 bridge=Bridge(report)
 try:
  bridge.open()
  for reg,name in [(8,'voltage_mV'),(6,'temperature_0p1K'),(10,'flags'),(12,'nominal_available_mAh'),(14,'full_available_mAh'),(16,'remaining_mAh'),(18,'full_charge_mAh'),(20,'average_current_raw'),(28,'state_of_health_raw'),(30,'cycle_count'),(32,'state_of_charge_pct'),(40,'internal_temperature_0p1K'),(46,'design_capacity_mAh')]:
   v=bridge.transaction(reg);report['standard'][name]=v;print(name,v,flush=True)
   if reg==8 and not 2500<=v<=5000:raise RuntimeError('Invalid voltage; stop')
  for selector,name in [(0,'control_status'),(1,'device_type'),(2,'firmware_version'),(8,'chemistry_id'),(31,'dataflash_version')]:
   bridge.transaction(0,selector=selector);v=bridge.transaction(0)
   report['control'][name]={'value':v,'hex':f'0x{v:04x}'};print(name,f'0x{v:04x}',flush=True)
  report['success']=True
 except Exception as e:report.update(success=False,error=str(e));print('Stopped:',e,flush=True)
 finally:
  try:bridge.close()
  except Exception as e:report['restore_error']=str(e)
  out=root/('bq-readonly-via-ec-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'.json')
  out.write_text(json.dumps(report,indent=2)+'\n');print('Saved',out,flush=True)
if __name__=='__main__':main()
