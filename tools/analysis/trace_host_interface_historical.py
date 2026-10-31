from pathlib import Path
import pypcode,hashlib,struct,json
r=Path(__file__).resolve().parent;b=(r/'A04-images/EC0.bin').read_bytes()
assert b==(r/'A07-images/EC0.bin').read_bytes()
c=pypcode.Context('CR16C:LE:16:default');lines=[]
for start,end in [(0x43de,0x48fa),(0x48fa,0x4df2),(0x737e,0x7d16),(0x3412,0x3474),(0x32b0,0x33fa),(0xc058,0xc178)]:
 lines.append(f'\n; FILE OFFSETS {start:06x}..{end:06x}')
 for i in c.disassemble(b[start:end+8],start).instructions:
  if i.addr.offset>=end:break
  lines.append(f'{i.addr.offset:06x}: {i.mnem:8} {i.body}')
(r/'EC-host-interface.asm').write_text('\n'.join(lines)+'\n')
maps={}
for name,offset,base in [('write',0xf11e,0x124ea),('read',0xf08c,0x12265)]:
 maps[name]={hex(0x10+i):hex(2*(base+struct.unpack_from('<h',b,offset+i*2)[0])-0x20000) for i in range(12)}
assert maps['write']['0x18']=='0x4a04' and maps['read']['0x18']=='0x456a'
(r/'EC-host-register-dispatch.json').write_text(json.dumps(maps,indent=2)+'\n');print(maps)
