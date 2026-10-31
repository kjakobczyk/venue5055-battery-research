#!/usr/bin/env python3
"""Offline AMI-UAF extraction from the two checksum-pinned Dell packages.
Never execute the input. Vendor payloads remain local to the chosen output path.
"""
import argparse,hashlib,json,struct
from pathlib import Path
KNOWN={'45cd5b0ca4356a13cb78bc0f0855bc45ac05e56b0d10f70179ba8cb0713caaf6':'A04','6626d695b48705a43f63d05ba3f577cdfb14ad99e9118a397b0d029a0001cd6d':'A07'}
EC_SHA='21e4efa3f1608539e47e5a8e1511c8f9cd0e3ac4703185555c85363135ab3bd8'
def chk(b):
 if len(b)%2:raise ValueError('Odd module length')
 return sum(x[0] for x in struct.iter_unpack('<H',b))&65535

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('package',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 data=a.package.read_bytes();digest=hashlib.sha256(data).hexdigest()
 if digest not in KNOWN:raise SystemExit('Input is not either study-pinned Dell package; refuse extraction')
 candidates=[];pos=0
 while (pos:=data.find(b'@UAF',pos))!=-1:
  off=pos;pos+=4
  if off+16>len(data):continue
  size=struct.unpack_from('<I',data,off+4)[0]
  if size>=1024 and off+size<=len(data):
   b=data[off:off+size]
   if size%2==0 and chk(b)==0 and b[16:20]==b'@UII':candidates.append((off,b))
 if not candidates:raise SystemExit('No valid UAF root')
 offset,b=max(candidates,key=lambda x:len(x[1]));records=[];out=a.output;out.mkdir(parents=True,exist_ok=True);pos=16
 from uefi_firmware import efi_compressor
 while pos<len(b):
  if pos+24>len(b):raise ValueError('Truncated module')
  tag,size=struct.unpack_from('<4sI',b,pos);assert tag.startswith(b'@') and size>=24 and pos+size<=len(b)
  mod=b[pos:pos+size];assert chk(mod)==0
  compressed,original=struct.unpack_from('<II',mod,16);assert 0<original<=32*1024*1024
  if compressed==original:decoded=mod[24:24+original]
  else:
   encoded=mod[16:]+bytes(max(0,compressed+8-len(mod[16:])))
   decoded=efi_compressor.EfiDecompress(encoded,len(encoded))
  assert len(decoded)==original
  name=tag.decode('ascii')[1:]+'.bin';dest=out/name
  if dest.exists() and dest.read_bytes()!=decoded:raise FileExistsError('Refuse to replace different '+str(dest))
  dest.write_bytes(decoded);h=hashlib.sha256(decoded).hexdigest()
  if tag==b'@EC0':assert h==EC_SHA
  records.append(dict(tag=tag.decode(),container_offset=pos,module_bytes=size,compressed_bytes=compressed,decoded_bytes=original,sha256=h,file=name))
  pos+=size
 assert pos==len(b)
 (out/'manifest.json').write_text(json.dumps(dict(package_version=KNOWN[digest],package_sha256=digest,uaf_executable_offset=offset,components=records),indent=2)+'\n')
 print(json.dumps(records,indent=2))
if __name__=='__main__':main()
