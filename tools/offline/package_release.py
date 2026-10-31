#!/usr/bin/env python3
"""Create local review/GitHub and arXiv source bundles. No network/hardware."""
from pathlib import Path
import hashlib,json,subprocess,sys,tarfile,zipfile
ROOT=Path(__file__).resolve().parents[2]
def main():
 subprocess.run([sys.executable,str(ROOT/'tools/offline/verify_evidence.py')],check=True)
 dist=ROOT/'dist';dist.mkdir(exist_ok=True)
 required=[ROOT/'paper/main.tex',ROOT/'paper/references.bib',ROOT/'paper/main.bbl',ROOT/'paper/main.pdf']+list((ROOT/'paper/figures').glob('*.pdf'))
 assert all(p.is_file() for p in required) and len(required)>=7,'Build figures and paper first'
 source=[ROOT/'paper/main.tex',ROOT/'paper/references.bib',ROOT/'paper/main.bbl']+sorted((ROOT/'paper/figures').glob('*.pdf'))
 with tarfile.open(dist/'venue5055-arxiv-source.tar.gz','w:gz') as t:
  for p in source:t.add(p,arcname=str(p.relative_to(ROOT/'paper')))
 excluded={'.git','.venv','work','dist','__pycache__'};suffixes={'.aux','.log','.out','.toc','.blg','.pyc','.fls','.fdb_latexmk'}
 files=[p for p in ROOT.rglob('*') if p.is_file() and not (set(p.relative_to(ROOT).parts)&excluded) and p.suffix not in suffixes]
 with zipfile.ZipFile(dist/'venue5055-github-review.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in sorted(files):z.write(p,'venue5055-battery-research/'+str(p.relative_to(ROOT)))
 artifacts=[dict(file=p.name,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(dist.iterdir()) if p.suffix in ('.zip','.gz')]
 (dist/'SHA256SUMS').write_text(''.join(x['sha256']+'  '+x['file']+'\n' for x in artifacts))
 print(json.dumps(artifacts,indent=2))
if __name__=='__main__':main()
