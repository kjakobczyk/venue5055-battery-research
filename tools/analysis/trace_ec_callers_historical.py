# Reproducible offline evidence for A07 EC call chain. Never opens device files.
from pathlib import Path
import hashlib,json,re
import pypcode
r=Path(__file__).resolve().parent; b=(r/'A07-images/EC0.bin').read_bytes()
assert hashlib.sha256(b).hexdigest()=='21e4efa3f1608539e47e5a8e1511c8f9cd0e3ac4703185555c85363135ab3bd8'
c=pypcode.Context('CR16C:LE:16:default')
ranges=[(0x3e54,0x3e9a),(0x71bc,0x737e),(0x7e40,0x83b6),(0x83b6,0x84aa),(0x84aa,0x8688),(0xc058,0xc164)]
lines=[]; ins={}
for start,end in ranges:
 lines.append(f'\n; Range {start:06x}..{end:06x}; FILE OFFSETS; linear decode from function boundary')
 for i in c.disassemble(b[start:end+8],start).instructions:
  off=i.addr.offset
  if off>=end:break
  assert off+i.length<=end
  ins[off]=i
  lines.append(f'{off:06x}: {b[off:off+i.length].hex():12} {i.mnem:8} {i.body}')
expect={0x3e80:('BAL','0x71bc'),0x72d8:('BAL','0x7e6a'),0x7e9c:('BAL','0x83b6'),0x8410:('MOVD','0x2f6a6'),0x842e:('MOVD','0x3110a'),0x8434:('BAL','0x81d4'),0x827a:('BAL','0xc058')}
for off,(m,v) in expect.items():assert ins[off].mnem==m and v in ins[off].body
assert len(b[0xf6a6:0xf6a6+0x1a63])==6755
assert b[0xf6a6:0xf6a8]==b'W:' and b[0x1110a:0x1110c]==b'W:'
(r/'A07-images/EC0-call-chain.asm').write_text('\n'.join(lines)+'\n')
print('Verified EC SHA-256, linear instruction boundaries, 7 call/pointer landmarks, script locations and lengths.')
