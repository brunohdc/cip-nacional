import json,os,re,io,html,unicodedata
from pypdf import PdfReader
BASE=os.environ.get('CIP_BASE',os.path.expanduser('~/workspace/cip_collected'))
R=json.load(open(BASE+'/recheck_2026-11/fetch_result.json'))
d=json.load(open(BASE+'/cip_top100.json'))
def text_of(rec):
    raw=open(os.path.join(BASE+'/recheck_2026-11/cache',rec['key']+'.bin'),'rb').read()
    if raw[:4]==b'%PDF':
        try: return '\n'.join((p.extract_text() or '') for p in PdfReader(io.BytesIO(raw)).pages)
        except Exception: return ''
    t=raw.decode('utf-8','ignore')
    t=re.sub(r'(?is)<(script|style).*?</\1>',' ',t); t=re.sub(r'(?s)<[^>]+>',' ',t)
    return html.unescape(t)
def norm(s):
    s=unicodedata.normalize('NFKD',s); s=''.join(c for c in s if not unicodedata.combining(c))
    return re.sub(r'[\s\u00a0]+',' ',s).lower()
texts={r['url']:norm(text_of(r)) for r in R if r['status']==200}
def variants(v):
    out=set()
    for nd in (1,2,3,4):
        s=f'{v:.{nd}f}'
        out.add(s); out.add(s.replace('.',','))
        out.add(s.rstrip('0').rstrip('.') if '.' in s else s)
    out.add(str(int(v)) if float(v).is_integer() else '')
    return [x for x in out if x]
out=[]
for r in d:
    vals=[]
    for cls,rows in (r.get('tabelas') or {}).items():
        for row in rows:
            v=row.get('valor')
            if isinstance(v,(int,float)) and v: vals.append(float(v))
    vals=sorted(set(vals))
    ok=[f['url'] for f in (r.get('fontes') or []) if f['url'] in texts and len(texts[f['url']])>300]
    txt=' '.join(texts[u] for u in ok)
    miss=[v for v in vals if not any(re.search(r'(?<![\d.,])'+re.escape(s)+r'(?![\d])',txt) for s in variants(v))]
    out.append({'municipio':r['municipio'],'uf':r['uf'],'status':r['status'],'exercicio':r.get('exercicio'),
      'n_val':len(vals),'miss':miss,'fontes_ok':len(ok),'n_fontes':len(r.get('fontes') or [])})
json.dump(out,open(BASE+'/recheck_2026-11/verify2.json','w'),ensure_ascii=False,indent=1)
ok=[o for o in out if o['status']=='completo' and o['fontes_ok']>0]
print('completos c/ fonte lida:',len(ok))
for o in ok:
    flag='' if not o['miss'] else 'MISS'
    print(f"{o['municipio'][:20]:21}{o['uf']:3}{str(o['exercicio']):5}{o['n_val']:4} faltam {len(o['miss']):3} {flag} {o['miss'][:6]}")
