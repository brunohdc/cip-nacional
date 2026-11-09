import json,os,re,unicodedata
from pypdf import PdfReader
import io
BASE=os.environ.get('CIP_BASE',os.path.expanduser('~/workspace/cip_collected'))
R=json.load(open(BASE+'/recheck_2026-11/fetch_result.json'))
d=json.load(open(BASE+'/cip_top100.json'))
by={ (r['url']):r for r in R }
def text_of(rec):
    p=os.path.join(BASE+'/recheck_2026-11/cache',rec['key']+'.bin')
    raw=open(p,'rb').read()
    if raw[:4]==b'%PDF':
        try:
            rd=PdfReader(io.BytesIO(raw))
            return '\n'.join((pg.extract_text() or '') for pg in rd.pages)
        except Exception as e:
            return ''
    t=raw.decode('utf-8','ignore')
    t=re.sub(r'(?is)<(script|style).*?</\1>',' ',t)
    t=re.sub(r'(?s)<[^>]+>',' ',t)
    import html
    return html.unescape(t)
def norm(s):
    s=unicodedata.normalize('NFKD',s)
    s=''.join(c for c in s if not unicodedata.combining(c))
    return re.sub(r'\s+',' ',s).lower()
texts={}
for rec in R:
    if rec['status']==200:
        texts[rec['url']]=norm(text_of(rec))
out=[]
for r in d:
    vals=[]
    for cls,rows in (r.get('tabelas') or {}).items():
        for row in rows:
            v=row.get('valor')
            if isinstance(v,(int,float)) and v not in (0,0.0):
                vals.append(v)
    vals=sorted(set(vals))
    src=[f['url'] for f in (r.get('fontes') or [])]
    ok=[u for u in src if u in texts and len(texts[u])>500]
    txt=' '.join(texts[u] for u in ok)
    found=[]
    for v in vals:
        a=f'{v:.2f}'.replace('.',',')
        b=f'{v:.2f}'
        if a in txt or b in txt: found.append(v)
    # year mentions in text
    years=sorted(set(int(y) for y in re.findall(r'\b(20[12]\d)\b',txt)))
    out.append({'municipio':r['municipio'],'uf':r['uf'],'status':r['status'],'exercicio':r.get('exercicio'),
      'n_val':len(vals),'n_found':len(found),'fontes':len(src),'fontes_ok':len(ok),
      'ok_ratio':round(len(found)/len(vals),2) if vals else None,'years':years[-4:] if years else []})
json.dump(out,open(BASE+'/recheck_2026-11/verify.json','w'),ensure_ascii=False,indent=1)
print(f"{'municipio':22}{'uf':3}{'st':6}{'ex':6}{'val':>5}{'fnd':>5}{'ok':>4}{'fok':>4}  anos")
for o in sorted(out,key=lambda x:(x['ok_ratio'] is not None, x['ok_ratio'] or 0)):
    print(f"{o['municipio'][:21]:22}{o['uf']:3}{o['status'][:5]:6}{str(o['exercicio'] or '-'):6}{o['n_val']:5}{o['n_found']:5}{o['fontes']:4}{o['fontes_ok']:4}  {o['years']}")
