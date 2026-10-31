#!/usr/bin/env python3
"""Regenerate publication figures from recorded evidence; never access hardware."""
from pathlib import Path
import json,datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'paper/figures';OUT.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.size':10,'font.family':'DejaVu Sans','pdf.fonttype':42,'ps.fonttype':42,'svg.hashsalt':'venue5055-study-20261031','axes.spines.top':False,'axes.spines.right':False})
def save(fig,name):
 for ext in ('pdf','svg','png'):
  meta={'Creator':'venue5055-battery-research'}
  if ext=='pdf':meta['CreationDate']=datetime.datetime(2026,10,31,tzinfo=datetime.timezone.utc)
  if ext=='svg':meta['Date']='2026-10-31'
  fig.savefig(OUT/f'{name}.{ext}',bbox_inches='tight',dpi=180,metadata=meta)
 plt.close(fig)
d=json.loads((ROOT/'evidence/intervention/report.json').read_text());a=d['before_gauge'];b=d['after_gauge'];design=a['design_mAh']
fig,axes=plt.subplots(1,2,figsize=(10.2,3.9),gridspec_kw={'width_ratios':[1.15,1]})
colors=['#365f8c','#bd662b'];labels=['Before','After edit + reset'];x=[0,1,2]
for off,vals,col,lab in [(-.18,[7720,a['fcc_mAh'],design],colors[0],labels[0]),(.18,[8794,b['fcc_mAh'],design],colors[1],labels[1])]:
 bars=axes[0].bar([i+off for i in x],vals,.34,label=lab,color=col)
 for bar,v in zip(bars,vals):axes[0].text(bar.get_x()+bar.get_width()/2,v+100,f'{v:,}',ha='center',va='bottom',fontsize=8)
axes[0].set_xticks(x,['Stored Qmax0','Reported FCC','Design reference']);axes[0].set_ylabel('Charge / model parameter (mAh)');axes[0].set_ylim(0,10100);axes[0].legend(frameon=False,fontsize=8,loc='upper center',ncol=2);axes[0].set_title('A. Parameter and reported capacity')
for off,vals,col in [(-.18,[a['fcc_mAh']/design*100,a['soh_raw']&255],colors[0]),(.18,[b['fcc_mAh']/design*100,b['soh_raw']&255],colors[1])]:
 bars=axes[1].bar([i+off for i in [0,1]],vals,.34,color=col)
 for bar,v in zip(bars,vals):axes[1].text(bar.get_x()+bar.get_width()/2,v+1,f'{v:.2f}%' if v not in (78,95) else f'{v:.0f}%',ha='center',va='bottom',fontsize=8)
axes[1].set_xticks([0,1],['FCC / design','Gauge SOH']);axes[1].set_ylim(0,108);axes[1].set_ylabel('Reported metric (%)');axes[1].set_title('B. Distinct health-reporting metrics')
fig.suptitle('One device, one Qmax edit followed by one gauge reset',fontsize=12)
fig.text(.5,-.015,'Single observations; no reset-only control and no independent physical-capacity measurement.',ha='center',fontsize=8)
fig.tight_layout();save(fig,'reporting-change')
model=json.loads((ROOT/'evidence/dataflash/decoded-readings.json').read_text());tab=model['resistance_tables']
fig,ax=plt.subplots(figsize=(8.3,3.9))
for key,label,col,style in [('87','Reference Def0 / Def1','#243e57','-'),('91','Profile 0: Ra','#bd662b','--'),('93','Profile 0: Rax (flag 0x55)','#a9372d','-'),('92','Profile 1: Ra / Rax','#4d845e',':')]:
 ax.plot(range(15),tab[key]['decompressed_native_units'],label=label,color=col,linestyle=style,marker='o',markersize=3,linewidth=1.6)
ax.set_xlabel('Resistance-table grid index (nonuniform DOD spacing)');ax.set_ylabel('Decompressed native model units');ax.set_ylim(0,65);ax.set_xticks(range(15));ax.grid(axis='y',alpha=.2);ax.legend(frameon=False,fontsize=8,ncol=2);ax.set_title('Acquired resistance profiles before the Qmax intervention')
fig.text(.5,-.02,'Temperature-normalized model entries; not an independent impedance measurement.',ha='center',fontsize=8);fig.tight_layout();save(fig,'resistance')
fig,ax=plt.subplots(figsize=(10,4.2));ax.set_xlim(0,10);ax.set_ylim(0,4.2);ax.axis('off')
def box(x,y,w,h,text,color):
 ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.06',facecolor=color,edgecolor='#34495e',linewidth=1));ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=10)
def arrow(a,b,text=None,dashed=False):
 ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=13,color='#34495e',linewidth=1.3,linestyle='--' if dashed else '-'))
 if text:ax.text((a[0]+b[0])/2,(a[1]+b[1])/2+.15,text,ha='center',va='bottom',fontsize=8)
box(.1,1.8,2.1,1,'Linux / CPU\nhost I2C','#e5edf6');box(3.7,1.8,2.3,1,'Nuvoton EC\nNPCE948','#e6efe6');box(7.5,1.8,2.2,1,'TI fuel gauge\nBQ27510-G3','#f9ecdf')
arrow((2.2,2.3),(3.65,2.3),'EC 7-bit 0x10');arrow((6,2.3),(7.45,2.3),'channel 0; 0x55')
ax.text(2.95,1.35,'CPU AD12 / AE12\nto EC E2 / F2',ha='center',fontsize=8);ax.text(6.75,1.35,'EC B8 / C8 to\nPU4401 SCL / SDA',ha='center',fontsize=8)
ax.plot([1.15,1.15,8.6,8.6],[2.85,3.65,3.65,2.85],'--',color='#8d7770',linewidth=1.2);ax.text(4.9,3.8,'R4122 / R4123 optional links: actual population unverified',ha='center',fontsize=8)
ax.text(4.9,.65,'Validated software path: block 0x65 request registers + block 0xF1 result readback',ha='center',fontsize=9)
ax.text(4.9,.2,'Boardview rail labels: CPU-side 1.8 V; gauge-side 3.3 V. No physical bridge was installed.',ha='center',fontsize=8)
save(fig,'topology')
print('Generated 3 figures in PDF, SVG and PNG.')
