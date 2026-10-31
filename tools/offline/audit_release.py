#!/usr/bin/env python3
"""Check the publication tree for stale claims, broken links, and excluded inputs."""
import ast,hashlib,importlib.util,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def main():
 spec=importlib.util.spec_from_file_location('verify',ROOT/'tools/offline/verify_evidence.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);result=v.main()
 # Negative checks are meaningful for a release-verification tool.
 raw=bytes.fromhex(json.loads((ROOT/'evidence/transport/host-register-probe.json').read_text())['results'][0]['response'])
 assert v.crc8(bytes([32,0xf1,33])+raw[:-1])==raw[-1]
 bad=bytearray(raw);bad[4]^=1
 assert v.crc8(bytes([32,0xf1,33])+bad[:-1])!=bad[-1]
 for p in (ROOT/'tools').rglob('*.py'):ast.parse(p.read_text(),filename=str(p))
 broken=[]
 for p in [ROOT/'README.md',*sorted((ROOT/'docs').glob('*.md'))]:
  for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
   if '://' in target or target.startswith('#'):continue
   dest=(p.parent/target.split('#')[0])
   if not dest.exists():broken.append((str(p.relative_to(ROOT)),target))
 assert not broken,broken
 tex=(ROOT/'paper/main.tex').read_text();bib=(ROOT/'paper/references.bib').read_text();keys=set(re.findall(r'@\w+\{([^,]+),',bib))
 cited={k.strip() for group in re.findall(r'\\cite\{([^}]+)\}',tex) for k in group.split(',')}
 assert cited<=keys,sorted(cited-keys)
 assert 'Krzysztof Jakóbczyk' in tex and 'reset-only control' in tex and 'not evidence of electrochemical capacity recovery' in tex
 assert '8794' in tex and '6827' in tex and '49' in tex
 assert 'PLACEHOLDER' not in tex and 'TODO' not in tex
 # Check packet examples copied into the documentation.
 for line in (ROOT/'docs/PROTOCOL.md').read_text().splitlines():
  if '65 10 ' in line and re.search(r': 65 10 ',line):
   b=bytes.fromhex(line.split(': ',1)[1]);assert len(b)==19 and v.crc8(bytes([32])+b[:-1])==b[-1]
 # Exclusion audit applies to release inputs, not ignored local work/.
 for p in ROOT.rglob('*'):
  rel=p.relative_to(ROOT)
  if set(rel.parts)&{'work','dist','.venv','.git','__pycache__'}:continue
  if p.is_file():assert p.suffix.lower() not in ('.exe','.rar','.cad','.aml','.efi'),str(rel)
 print(json.dumps(dict(audit='passed',python_sources_parsed=len(list((ROOT/'tools').rglob('*.py'))),bibliography_keys=len(keys),cited_keys=len(cited),broken_links=len(broken)),indent=2))
if __name__=='__main__':main()
