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
    t=raw.decode('utf-8','ignore'); t=re.sub(r'(?is)<(script|style).*?</\1>',' ',t); t=re.sub(r'(?s)<[^>]+>',' ',t)
    return html.unescape(t)
def norm(s):
    s=unicodedata.normalize('NFKD',s); s=''.join(c for c in s if not unicodedata.combining(c))
    return re.sub(r'[\s\u00a0]+',' ',s).lower()
texts={r['url']:norm(text_of(r)) for r in R if r['status']==200}
def variants(v):
    out=set()
    for nd in (0,1,2,3,4):
        s=f'{v:,.{nd}f}'
        for x in (s, s.replace(',','X').replace('.',',').replace('X','.'), s.replace(',','.'), s.replace(',','')):
            out.add(x)
    return [x for x in out if x]
res=[]
for r in d:
    vals=[]
    for cls,rows in (r.get('tabelas') or {}).items():
        for row in rows:
            x=row.get('valor')
            if isinstance(x,(int,float)) and x: vals.append(float(x))
    vals=sorted(set(vals))
    ok=[f['url'] for f in (r.get('fontes') or []) if f['url'] in texts and len(texts[f['url']])>300]
    txt=' '.join(texts[u] for u in ok)
    miss=[v for v in vals if not any(re.search(r'(?<![\d.,])'+re.escape(s)+r'(?![\d])',txt) for s in variants(v))]
    if r['status']=='completo':
        res.append((r['municipio'],r['uf'],r.get('exercicio'),len(vals),len(miss),miss,len(ok)))
tot=sum(1 for x in res if not x[4]); print('completos 100% conferidos:',tot,'/',len(res))
for x in res:
    if x[4]: print(x)
