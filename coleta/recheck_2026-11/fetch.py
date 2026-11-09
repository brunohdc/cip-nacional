import json, os, hashlib, concurrent.futures, requests, urllib3
urllib3.disable_warnings()
BASE=os.environ.get('CIP_BASE',os.path.expanduser('~/workspace/cip_collected'))
d=json.load(open(BASE+'/cip_top100.json'))
urls={}
for r in d:
    for f in (r.get('fontes') or []):
        urls.setdefault(f['url'],[]).append(r['municipio']+'/'+r['uf'])
OUT=BASE+'/recheck_2026-11/cache'
os.makedirs(OUT,exist_ok=True)
H={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36','Accept-Language':'pt-BR,pt;q=0.9'}
def go(u):
    key=hashlib.md5(u.encode()).hexdigest()[:12]
    try:
        r=requests.get(u,headers=H,timeout=40,verify=False,allow_redirects=True)
        ct=r.headers.get('content-type','')
        open(os.path.join(OUT,key+'.bin'),'wb').write(r.content)
        return {'url':u,'key':key,'status':r.status_code,'ct':ct[:60],'len':len(r.content),'final':r.url,'muns':urls[u]}
    except Exception as e:
        return {'url':u,'key':key,'status':'ERR','ct':'','len':0,'final':str(e)[:120],'muns':urls[u]}
res=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
    for r in ex.map(go,urls):
        res.append(r)
json.dump(res,open(BASE+'/recheck_2026-11/fetch_result.json','w'),ensure_ascii=False,indent=1)
from collections import Counter
print(Counter(str(r['status']) for r in res))
print('ok',sum(1 for r in res if r['status']==200))
for r in res:
    if r['status']!=200: print(r['status'],r['url'][:110],'|',','.join(r['muns'])[:60])
