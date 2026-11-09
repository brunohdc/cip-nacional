#!/usr/bin/env python3
"""Coleta arrecadação oficial de CIP (SICONFI/DCA, conta 1.2.4.0.00.0.0).

Saída: coleta/arrecadacao_cip.json (gravação incremental)
Fonte: https://apidatalake.tesouro.gov.br/ords/siconfi/tt/dca (Anexo I-C, Receitas Brutas Realizadas)
Anti-fabricação: valor ausente = null + status; nada é estimado.
Use CIP_REFRESH=1 para reconsultar todos os municípios, não apenas os que faltam.
"""
import json, os, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date

BASE = os.environ.get("CIP_BASE", os.path.expanduser("~/workspace/cip_collected"))
OUT = f"{BASE}/arrecadacao_cip.json"
YEARS = list(range(date.today().year - 4, date.today().year))
REFRESH = os.environ.get("CIP_REFRESH") == "1"
API = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt/dca"
CONTA = "RO1.2.4.0.00.0.0"      # receita bruta realizada (Anexo I-C)
CONTA_ALT = "P4.2.3.0.0.00.00"  # passivo/controle (Anexo I-HI)

regs = json.load(open(f"{BASE}/cip_top500.json" if os.path.exists(f"{BASE}/cip_top500.json") else f"{BASE}/cip_top100.json", encoding="utf-8"))
res = {}
if os.path.exists(OUT):
    res = {r["cod_ibge"]: r for r in json.load(open(OUT, encoding="utf-8"))}


def fetch(cod, ano):
    q = urllib.parse.urlencode({"an_exercicio": ano, "id_ente": cod})
    req = urllib.request.Request(f"{API}?{q}", headers={"User-Agent": "cip-collector/1.0"})
    for tent in range(3):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read().decode("utf-8", "replace"))
        except Exception as e:
            if tent == 2:
                return {"_erro": str(e)}
            time.sleep(2 + 3 * tent)


def colher(reg):
    cod = reg["cod_ibge"]
    anterior = res.get(cod, {})
    antigo = anterior.get("por_ano", {})
    item = {"cod_ibge": cod, "municipio": reg["municipio"], "uf": reg["uf"],
            "slug": reg["slug"], "por_ano": {}, "populacao": anterior.get("populacao"),
            "fonte": dict(anterior.get("fonte", {})),
            "coletado_em": anterior.get("coletado_em") or time.strftime("%Y-%m-%d")}
    sucesso = False
    for ano in YEARS:
        d = fetch(cod, ano)
        if "_erro" in d:
            item["por_ano"][str(ano)] = antigo.get(str(ano))
            if item["por_ano"][str(ano)] is None:
                item[f"erro_{ano}"] = d["_erro"][:120]
            continue
        sucesso = True
        its = d.get("items", [])
        alvo = None
        for i in its:
            if i.get("cod_conta") == CONTA:
                alvo = i
                break
        if alvo is None:
            for i in its:
                if i.get("cod_conta") == CONTA_ALT:
                    alvo = i
                    break
        if alvo:
            item["por_ano"][str(ano)] = alvo["valor"]
            item["populacao"] = item["populacao"] or alvo.get("populacao")
            item["fonte"][str(ano)] = f"{API}?an_exercicio={ano}&id_ente={cod} ({alvo['cod_conta']})"
        else:
            item["por_ano"][str(ano)] = None
    if sucesso:
        item["coletado_em"] = time.strftime("%Y-%m-%d")
    vals = [v for v in item["por_ano"].values() if isinstance(v, (int, float))]
    item["total_acumulado"] = round(sum(vals), 2) if vals else None
    item["anos_com_dado"] = sorted(int(k) for k, v in item["por_ano"].items()
                                   if isinstance(v, (int, float)))
    item["status"] = "ok" if len(item["anos_com_dado"]) == len(YEARS) else (
        "parcial" if item["anos_com_dado"] else "sem_dado")
    return item


def salvar(res):
    lst = sorted(res.values(), key=lambda r: r["cod_ibge"])
    json.dump(lst, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


alvos = regs if REFRESH else [r for r in regs if r["cod_ibge"] not in res]
print(f"total {len(regs)} | já coletados {len(res)} | a coletar {len(alvos)} | exercícios {YEARS}", flush=True)

with ThreadPoolExecutor(max_workers=4) as ex:
    for i, item in enumerate(ex.map(colher, alvos), 1):
        res[item["cod_ibge"]] = item
        if i % 5 == 0 or i == len(alvos):
            salvar(res)
            done = item["total_acumulado"]
            print(f"[{i}/{len(alvos)}] {item['municipio']}-{item['uf']} "
                  f"total={done} status={item['status']}", flush=True)
salvar(res)
ok = sum(1 for r in res.values() if r["status"] == "ok")
print(f"FIM: {len(res)} municípios | ok={ok} | parcial="
      f"{sum(1 for r in res.values() if r['status']=='parcial')} | "
      f"sem_dado={sum(1 for r in res.values() if r['status']=='sem_dado')}", flush=True)
