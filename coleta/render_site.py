#!/usr/bin/env python3
"""Gera o site estático de CIP a partir de cip_top100.json.

Saída: ~/workspace/cip_site/
  /index.html
  /cip/index.html                  (hub nacional)
  /cip/<uf>/index.html             (hub por UF)
  /cip/<uf>/<slug>/index.html      (página do município — 1 URL = 1 município)
  /distribuidora/<slug>/index.html (hub da distribuidora)
  /assets/style.css
"""
import json, unicodedata, html, re, os, sys
from collections import defaultdict

BASE = os.environ.get("CIP_BASE", os.path.expanduser("~/workspace/cip_collected"))
OUT = os.environ.get("CIP_SITE", os.path.expanduser("~/workspace/cip_site"))
DATA_BR = "01/10/2026"
DATASET_PATH = f"{BASE}/cip_top500.json" if os.path.exists(f"{BASE}/cip_top500.json") else f"{BASE}/cip_top100.json"
regs = json.load(open(DATASET_PATH))
ARRQ = {}
_arr = f"{BASE}/arrecadacao_cip.json"
if os.path.exists(_arr):
    ARRQ = {str(r["cod_ibge"]): r for r in json.load(open(_arr))}
YEARS_ARR = [2022, 2023, 2024, 2025]

def brl(v):
    if not isinstance(v, (int, float)):
        return "n/d"
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def slugify(s):
    s = unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9\s-]", "", s).strip().lower()
    return re.sub(r"[\s]+", "-", s)

def esc(s):
    return html.escape(str(s), quote=True)

MEC = {
    "percentual_modulo_tip": "percentual sobre o módulo de referência TIP",
    "percentual_teip": "percentual sobre o TEIP (Tarifa de Energia na Estrada de Entrega — módulo B4a)",
    "formula_teip": "fórmula com componentes fixo e variável sobre o TEIP",
    "valor_fixo": "valor fixo por faixa de consumo (R$ por mês)",
    "outro": "percentual sobre a base de cálculo/rateio definida em lei",
    "desconhecido": "ainda não confirmado (tabela oficial não localizada)",
}
STATUS_TXT = {
    "completo": "tabela oficial verificada",
    "parcial": "informação parcial — tabela completa ainda não localizada",
    "nao_encontrado": "não informado — sem lei local encontrada",
}
UNIT_TXT = {
    "BRL": "R$/mês", "PERCENTUAL_MODULO_TIP": "% do módulo TIP",
    "PERCENTUAL_TEIP": "% do TEIP", "FORMULA_TEIP": "fórmula (TEIP)",
    "PERCENTUAL_BASE": "% da base de cálculo",
}
UNI = ("sp","mg","rj","rs","ba","pr","ce","pe","sc","go","ma","pb","pa","es","rn","mt","ms","al","se","pi","am","ro","to","ac","rr","ap","df")

def fmt_faixa(f):
    lo, hi = f["faixa_kwh"]["min"], f["faixa_kwh"]["max"]
    if lo is None and hi is None: return "todas as faixas"
    if lo is None: return f"até {hi} kWh"
    if hi is None: return f"acima de {lo} kWh"
    return f"{lo+1}–{hi} kWh" if lo != 0 else f"0–{hi} kWh"

def fmt_valor(f):
    v = f["valor"]
    if isinstance(v, str): return v.capitalize()
    u = f["unidade"]
    if u == "BRL": return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{v:g}%".replace(".", ",")

def tabela_html(r):
    if not r.get("tabelas"): return ""
    out = []
    for classe, linhas in r["tabelas"].items():
        nome_classe = classe.replace("_", " ").capitalize()
        out.append(f'<h3>{esc(nome_classe)}</h3>')
        out.append('<table class="tab"><thead><tr><th>Faixa de consumo</th><th>Alíquota/valor</th></tr></thead><tbody>')
        for f in linhas:
            nota = f'<span class="nota"> — {esc(f["nota"])}</span>' if f.get("nota") and len(f["faixa_kwh"]) and f["nota"] and "isento" not in str(f["valor"]) else ""
            out.append(f'<tr><td>{esc(fmt_faixa(f))}</td><td><strong>{esc(fmt_valor(f))}</strong>{nota}</td></tr>')
        out.append("</tbody></table>")
    un = next((f["unidade"] for ls in r["tabelas"].values() for f in ls), "BRL")
    out.append(f'<p class="unidade">Unidade: {esc(UNIT_TXT.get(un, un))}.</p>')
    return "\n".join(out)

def faq(r):
    nome, uf = r["municipio"], r["uf"]
    base = "; ".join(b["norma"] for b in r["base_legal"]) or "não informado"
    qs = []
    if r["status"] == "completo":
        ex = f" (exercício {r['exercicio']})" if r.get("exercicio") else ""
        first = next(iter(r["tabelas"].values()))[0] if r["tabelas"] else None
        qs.append((f"Quanto é a CIP em {nome}?",
                   f"A alíquota de CIP em {nome}/{uf}{ex} varia por faixa de consumo — veja a tabela acima, extraída da legislação oficial. "
                   + (f"Na primeira faixa da tabela: {fmt_valor(first)}." if first and isinstance(first.get("valor"), (int, float)) else "")))
    elif r["status"] == "parcial":
        qs.append((f"Quanto é a CIP em {nome}?",
                   f"A tabela completa de alíquotas de {nome}/{uf} ainda não foi localizada em fonte oficial acessível "
                   f"(status: informação parcial). A base legal é {base}. O registro é re-checado mensalmente — "
                   f"se você é do município e conhece a fonte, ela entra na próxima revisão."))
    else:
        qs.append((f"Quanto é a CIP em {nome}?",
                   f"Não informado: sem lei local de CIP encontrada para {nome}/{uf} na checagem de {DATA_BR}. "
                   "Nada é estimado aqui — quando a fonte oficial for localizada, o valor entra no registro."))
    qs.append(("Como a CIP de {0} é calculada?".format(nome),
               f"Em {nome} a cobrança segue o mecanismo: {MEC[r['mecanismo']]}"
               + (f", definido em {base}." if r["base_legal"] else ".")))
    quem = ", ".join(r["distribuidoras"]) if r["distribuidoras"] else "não informado"
    qs.append((f"Quem cobra a CIP em {nome}?",
               f"A cobrança é feita pela concessionária de energia — em {nome}/{uf}: {quem} "
               "(a alíquota em si é definida pelo município, e a distribuidora repassa na fatura de energia)."))
    if r["isencoes"]:
        ie = r["isencoes"][0]
        qs.append((f"Quem é isento da CIP em {nome}?",
                   esc(ie.get("descricao", "n/d")) + f" (base: {ie.get('base_legal', 'n/d')}). "
                   + ("Demais condições na legislação local." if len(r["isencoes"]) > 1 else "")))
    else:
        qs.append((f"Quem é isento da CIP em {nome}?",
                   "Isenções não foram localizadas na checagem de " + DATA_BR + " — conferir a legislação municipal citada na base legal."))
    qs.append(("O que é a CIP (Contribuição de Iluminação Pública)?",
               "É a contribuição prevista no art. 149-A da Constituição Federal, cobrada por municípios para custear a iluminação pública; "
               "ela aparece na fatura de energia elétrica ou no IPTU, dependendo do município."))
    if r.get("pendencias"):
        qs.append((f"O que falta para a página de {nome} estar completa?",
                   "Pendências de verificação: " + esc("; ".join(r["pendencias"])) + "."))
    return qs

def page(r, uf_hub, hub, ufs_siblings):
    nome, uf = r["municipio"], r["uf"]
    ex = f" — alíquotas {r['exercicio']}" if r.get("exercicio") else ""
    title = f"Contribuição de Iluminação Pública em {nome} ({uf}){ex}"
    desc = r.get("descricao") or (
        f"CIP (Contribuição de Iluminação Pública) em {nome}-{uf}: {STATUS_TXT[r['status']]}. "
        f"Base legal, alíquotas, distribuidora e data da verificação.")
    faq_html, faq_json = [], []
    for q, a in faq(r):
        faq_html.append(f"<h3>{esc(q)}</h3><p>{a}</p>")
        faq_json.append({"@type": "Question", "name": q,
                         "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", a)}})
    status_note = {
        "completo": f'<div class="badge ok">✔ Tabela oficial verificada — checado em {DATA_BR}</div>',
        "parcial": f'<div class="badge warn">◐ Informação parcial — checado em {DATA_BR}</div>',
        "nao_encontrado": f'<div class="badge none">○ Não informado — sem lei local encontrada ({DATA_BR})</div>',
    }[r["status"]]
    body = [f"<p>Esta página reúne o que foi verificado sobre a <strong>Contribuição de Iluminação Pública (CIP)</strong> "
            f"em <strong>{esc(nome)}/{uf}</strong>: {STATUS_TXT[r['status']]}. "
            f"A consulta é gratuita e a checagem mais recente foi em <strong>{DATA_BR}</strong>.</p>"]
    body.append(status_note)
    if r.get("tabelas"):
        body.append("<h2>Alíquotas da CIP</h2>" + tabela_html(r))
    if r.get("observacoes"):
        body.append(f'<h2>Observações</h2><p>{esc(r["observacoes"])}</p>')
    if r["ressalvas"]:
        body.append("<h2>Ressalvas de verificação</h2><ul>" +
                    "".join(f"<li>{esc(x)}</li>" for x in r["ressalvas"]) + "</ul>")
    if r["pendencias"]:
        body.append("<h2>O que ainda falta</h2><ul>" +
                    "".join(f"<li>{esc(x)}</li>" for x in r["pendencias"]) + "</ul>")
    body.append("<h2>Como é calculada em {0}</h2><p>A CIP em {0} segue o mecanismo: <strong>{1}</strong>. "
                "O município define a alíquota por lei e a concessionária repassa o valor na fatura de energia elétrica. "
                "A competência é municipal (art. 149-A da CF), por isso a alíquota muda de um município para outro "
                "— inclusive dentro da mesma distribuidora.</p>".format(esc(nome), esc(MEC[r["mecanismo"]])))
    if r["base_legal"]:
        body.append("<h2>Base legal</h2><ul>" + "".join(
            f'<li>{esc(b["norma"])}' + (f' — vigência {esc(b["vigencia"])}' if b.get("vigencia") else "") +
            (f' — <a href="{esc(b["fonte_url"])}" rel="noopener" target="_blank">ver fonte</a>' if b.get("fonte_url") else "") + "</li>"
            for b in r["base_legal"]) + "</ul>")
    if r["isencoes"]:
        body.append("<h2>Isenções</h2><ul>" + "".join(
            f'<li>{esc(i.get("descricao","n/d"))} — base: {esc(i.get("base_legal","n/d"))}</li>' for i in r["isencoes"]) + "</ul>")
    quem = ", ".join(esc(d) for d in r["distribuidoras"])
    body.append(f"<h2>Concessionária responsável</h2><p>Em {esc(nome)}/{uf} a distribuidora de energia é "
                f"<strong>{quem}</strong> — é ela que repassa o valor da CIP na fatura.</p>")
    a = ARRQ.get(str(r["cod_ibge"]))
    if a and a.get("total_acumulado"):
        linhas = "".join(
            f'<tr><td>{y}</td><td>{brl(a["por_ano"].get(str(y)))}</td></tr>' for y in YEARS_ARR)
        pc = ""
        if a.get("populacao"):
            pc = f'<p>Equivale a <strong>{brl(a["total_acumulado"] / a["populacao"])}</strong> por habitante ' \
                 f'(população {a["populacao"]:,} ).</p>'.replace(",", ".")
        body.append(
            "<h2>Arrecadação oficial da CIP</h2>"
            "<p>Quanto o município efetivamente arrecadou com a contribuição, segundo a "
            "Declaração de Contas Anuais (DCA) publicada no SICONFI/Tesouro Nacional — conta "
            "<code>1.2.4.0.00.0.0</code> (Contribuição para o Custeio do Serviço de Iluminação Pública).</p>"
            '<table class="tab"><thead><tr><th>Exercício</th><th>Arrecadado</th></tr></thead><tbody>'
            + linhas + "</tbody></table>"
            f'<p><strong>Total acumulado {a["anos_com_dado"][0]}–{a["anos_com_dado"][-1]}: '
            f'{brl(a["total_acumulado"])}</strong>.</p>' + pc +
            '<p><a href="/arrecadacao/">Ver o ranking completo de arrecadação</a></p>')

    body.append("<h2>Perguntas frequentes</h2>" + "\n".join(faq_html))
    if r["fontes"]:
        body.append("<h2>Fontes verificadas</h2><ul>" + "".join(
            f'<li><a href="{esc(f["url"])}" rel="noopener" target="_blank">{esc(f["titulo"])}</a> '
            f'({esc(f["tipo"])}, checado em {esc(f["data_coleta"])})</li>' for f in r["fontes"]) + "</ul>")
    # links internos
    irmaos = "".join(f'<li><a href="/cip/{uf.lower()}/{s["slug"]}/">{esc(s["municipio"])}</a></li>'
                     for s in ufs_siblings if s["slug"] != r["slug"])
    body.append(f'<h2>Consulte outros municípios de {uf}</h2><ul class="links">{irmaos}</ul>')
    crumbs = [("CIP", "/cip/"), (uf.upper(), f"/cip/{uf.lower()}/"), (nome, None)]
    bc = "".join(f'<li><a href="{p}">{esc(n)}</a></li>' if p else f"<li>{esc(n)}</li>" for n, p in crumbs)
    ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": faq_json}
    return f"""<!DOCTYPE html>
<html lang="pt-BR"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}">
<link rel="stylesheet" href="/assets/style.css">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
</head><body>
<header><a class="logo" href="/">CIP Nacional</a> <nav><a href="/cip/">Municípios</a> · <a href="/arrecadacao/">Arrecadação</a></nav></header>
<main>
<ul class="crumbs">{bc}</ul>
<h1>{esc(title)}</h1>
{"".join(body)}
</main>
<footer><p>Registro checado em {DATA_BR} · próxima revisão {esc(r["proxima_revisao"])} · dados de fontes oficiais — nenhum valor estimado.</p></footer>
</body></html>"""

def hub_page(titulo, intro, itens, back=None):
    lis = "".join(f'<li><a href="{p}">{esc(t)}</a> <span class="st st-{s}">{s.replace("_"," ")}</span></li>'
                  for t, p, s in itens)
    bc = f'<ul class="crumbs"><li><a href="/cip/">CIP</a></li>' if back else '<ul class="crumbs">'
    return f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(titulo)}</title><meta name="description" content="{esc(intro[:150])}">
<link rel="stylesheet" href="/assets/style.css"></head><body>
<header><a class="logo" href="/">CIP Nacional</a> <nav><a href="/cip/">Municípios</a> · <a href="/arrecadacao/">Arrecadação</a></nav></header>
<main>{bc}<li>{esc(titulo)}</li></ul>
<h1>{esc(titulo)}</h1><p>{esc(intro)}</p><ul class="links dois">{lis}</ul></main>
<footer><p>Consulta gratuita · checado em {DATA_BR} · nenhum valor estimado.</p></footer></body></html>"""

# ---------- gerar ----------
css = """body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;color:#1a1a1a;line-height:1.6}
header{background:#0d2b45;color:#fff;padding:.7rem 1rem;display:flex;gap:1rem;align-items:baseline}
header a{color:#ffd166;text-decoration:none}header nav a{color:#fff}
main{max-width:820px;margin:0 auto;padding:1rem}
h1{font-size:1.5rem;margin:.4rem 0 1rem}h2{font-size:1.15rem;margin-top:1.8rem;border-bottom:1px solid #e5e5e5;padding-bottom:.2rem}
h3{font-size:1rem;margin:1.1rem 0 .3rem}
table.tab{border-collapse:collapse;width:100%;font-size:.95rem;margin:.4rem 0}
table.tab th{background:#0d2b45;color:#fff;text-align:left;padding:.4rem .6rem}
table.tab th.sortable{cursor:pointer;user-select:none}table.tab th.sortable:hover{background:#174c73}
table.tab td{border-bottom:1px solid #e8e8e8;padding:.35rem .6rem}
table.tab tr:nth-child(even){background:#f7f9fb}
.nota{color:#666;font-size:.85em}.unidade{color:#555;font-size:.85rem}
.badge{display:inline-block;padding:.3rem .7rem;border-radius:999px;font-size:.85rem;margin:.3rem 0}
.badge.ok{background:#e3f6e8;color:#14602c}.badge.warn{background:#fff3d6;color:#7a5200}.badge.none{background:#f1f1f1;color:#555}
.crumbs{list-style:none;padding:0;display:flex;gap:.4rem;font-size:.85rem;color:#666}
.crumbs li:after{content:"›";margin-left:.4rem}.crumbs li:last-child:after{content:""}
ul.links{columns:2;list-style:none;padding:0}ul.links.dois{columns:3}
ul.links li{margin:.25rem 0;break-inside:avoid}
.st{font-size:.72rem;text-transform:uppercase;color:#888;margin-left:.4rem}
.st-completo{color:#14602c}.st-parcial{color:#7a5200}.st-nao_encontrado{color:#888}
a{color:#0b5ed7}footer{max-width:820px;margin:2rem auto 1rem;padding:0 1rem;color:#777;font-size:.8rem;border-top:1px solid #eee}
@media(max-width:640px){ul.links,ul.links.dois{columns:1}}
"""
os.makedirs(f"{OUT}/assets", exist_ok=True)
open(f"{OUT}/assets/style.css", "w").write(css)

by_uf = defaultdict(list)
by_dist = defaultdict(list)
for r in regs:
    by_uf[r["uf"]].append(r)
    for d in r["distribuidoras"]:
        by_dist[d].append(r)

# páginas de município
n = 0
for r in regs:
    uf = r["uf"]
    d = f"{OUT}/cip/{uf.lower()}/{r['slug']}"
    os.makedirs(d, exist_ok=True)
    sibs = sorted(by_uf[uf], key=lambda x: x["municipio"])
    open(f"{d}/index.html", "w", encoding="utf-8").write(page(r, f"/cip/{uf.lower()}/", "/cip/", sibs))
    n += 1

# hub nacional
itens = []
for uf in sorted(by_uf):
    for r in sorted(by_uf[uf], key=lambda x: x["municipio"]):
        itens.append((f'{r["municipio"]}/{uf}', f"/cip/{uf.lower()}/{r['slug']}/", r["status"]))
open(f"{OUT}/cip/index.html", "w", encoding="utf-8").write(hub_page(
    "CIP por município — Brasil",
    f"Contribuição de Iluminação Pública em {len(regs)} dos maiores municípios do Brasil, com alíquotas, "
    "base legal e data de verificação. Nenhum valor estimado: se não está na fonte oficial, está marcado como não informado.",
    itens))
# hubs por UF
for uf, rs in by_uf.items():
    d = f"{OUT}/cip/{uf.lower()}"
    os.makedirs(d, exist_ok=True)
    its = [(r["municipio"], f"/cip/{uf.lower()}/{r['slug']}/", r["status"]) for r in sorted(rs, key=lambda x: x["municipio"])]
    open(f"{d}/index.html", "w", encoding="utf-8").write(hub_page(
        f"CIP em {uf.upper()} — alíquotas por município",
        f"Alíquotas da Contribuição de Iluminação Pública (CIP) em {len(its)} municípios de {uf}, "
        "com base legal, ressalvas e data da checagem.", its, back=True))
# hubs por distribuidora
for dist, rs in by_dist.items():
    s = slugify(dist)
    d = f"{OUT}/distribuidora/{s}"
    os.makedirs(d, exist_ok=True)
    its = [(f'{r["municipio"]}/{r["uf"]}', f'/cip/{r["uf"].lower()}/{r["slug"]}/', r["status"]) for r in rs]
    open(f"{d}/index.html", "w", encoding="utf-8").write(hub_page(
        f"CIP na distribuidora {dist} — municípios atendidos",
        f"Municípios atendidos pela {dist} com registro de alíquota de CIP conferido. "
        "A alíquota é definida por cada município — por isso varia dentro da mesma distribuidora.",
        its, back=True))
# ---------- página de arrecadação ----------
arr = [a for a in ARRQ.values() if a.get("total_acumulado")]
arr.sort(key=lambda a: -a["total_acumulado"])
sem_dado = sorted([a for a in ARRQ.values() if not a.get("total_acumulado")],
                  key=lambda a: a["municipio"])
Y0, Y1 = YEARS_ARR[0], YEARS_ARR[-1]
soma = sum(a["total_acumulado"] for a in arr)
pop_tot = sum(a.get("populacao") or 0 for a in arr)
pc_geral = soma / pop_tot if pop_tot else 0
linhas = []
for i, a in enumerate(arr, 1):
    reg = next((x for x in regs if x["cod_ibge"] == a["cod_ibge"]), None)
    link = f'/cip/{a["uf"].lower()}/{a["slug"]}/'
    pc = (a["total_acumulado"] / a["populacao"]) if a.get("populacao") else None
    cels = "".join(f'<td data-sort="{a["por_ano"].get(str(y)) if isinstance(a["por_ano"].get(str(y)), (int, float)) else "-1"}">{brl(a["por_ano"].get(str(y)))}</td>' for y in YEARS_ARR)
    total_sort = a["total_acumulado"] if isinstance(a.get("total_acumulado"), (int, float)) else -1
    pop_sort = a.get("populacao") if isinstance(a.get("populacao"), (int, float)) else -1
    pc_sort = pc if isinstance(pc, (int, float)) else -1
    linhas.append(
        f'<tr data-uf="{a["uf"]}"><td data-sort="{i}">{i}</td><td data-sort="{esc(a["municipio"])}"><a href="{link}">{esc(a["municipio"])}</a></td><td data-sort="{a["uf"]}">{a["uf"]}</td>'
        f'<td data-sort="{pop_sort}">{a.get("populacao", "n/d")}</td>{cels}'
        f'<td data-sort="{total_sort}"><strong>{brl(a["total_acumulado"])}</strong></td>'
        f'<td data-sort="{pc_sort}">{brl(pc) if pc else "n/d"}</td>'
        f'<td data-sort="{1 if reg and reg["status"] == "completo" else 0}">{"✔" if reg and reg["status"] == "completo" else "◐"}</td></tr>')
header = ('<th class="sortable" data-col="0"># ↕</th><th class="sortable" data-col="1">Município ↕</th>'
          '<th class="sortable" data-col="2">UF ↕</th><th class="sortable" data-col="3">População ↕</th>'
          + "".join(f'<th class="sortable" data-col="{4+i}">{y} ↕</th>' for i, y in enumerate(YEARS_ARR))
          + f'<th class="sortable" data-col="{4+len(YEARS_ARR)}">Total {Y0}–{Y1} ↕</th>'
          + f'<th class="sortable" data-col="{5+len(YEARS_ARR)}">R$/hab ↕</th>'
          + f'<th class="sortable" data-col="{6+len(YEARS_ARR)}">Tabela de alíquota ↕</th>')
tabela = ("<table class=\"tab sortable-table\"><thead><tr>" + header + "</tr></thead><tbody>"
          + "".join(linhas) + "</tbody></table>")
faq_arr = [
    ("O que é o total acumulado da CIP nesta página?",
     f"É a soma do valor que a prefeitura registrou como arrecadado com a Contribuição de Iluminação Pública "
     f"nos exercícios {Y0} a {Y1}, segundo as Declarações de Contas Anuais (DCA) publicadas no SICONFI, do "
     "Tesouro Nacional. Não é estimativa: cada célula vem do relatório oficial do próprio município."),
    ("De onde vêm exatamente esses números?",
     "Da conta contábil <code>1.2.4.0.00.0.0 — Contribuição para o Custeio do Serviço de Iluminação Pública</code> "
     "(linha 'Receitas Brutas Realizadas' do Anexo I-C da DCA). A API é pública: "
     "apidatalake.tesouro.gov.br/ords/siconfi/tt/dca."),
    ("Por que alguns municípios aparecem como n/d?",
     "Porque o município não entregou a DCA daquele exercício ou a conta não foi localizada no relatório. "
     "Nesta base, ausência de dado é publicada como n/d — nunca substituída por estimativa, média da região "
     "ou valor de município vizinho."),
    ("O valor arrecadado é o que eu pago de CIP?",
     "Não diretamente. A arrecadação é o total municipal (somando todas as unidades consumidoras). O que você paga "
     "depende da sua faixa de consumo e da regra do seu município — veja a página do município para a tabela de alíquotas."),
    ("Posso comparar municípios pela arrecadação?",
     "Só com cuidado. O total depende do tamanho da cidade (população e número de unidades consumidoras), do preço "
     "da energia e do mecanismo de cobrança local. A coluna R$/habitante ajuda, mas municípios industriais ou com "
     "muita iluminação pública tendem a arrecadar mais por habitante sem que o morador pague mais."),
    ("Com que frequência a arrecadação é atualizada?",
     "As DCAs são anuais. Esta página foi montada com dados coletados em " + DATA_BR + " e passa por revisão "
     "automática mensal, junto com as tabelas de alíquotas."),
]
faq_arr_html = "".join(f"<h3>{esc(q)}</h3><p>{a}</p>" for q, a in faq_arr)
faq_arr_json = [{"@type": "Question", "name": q,
                 "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", a)}} for q, a in faq_arr]
ld_arr = {"@context": "https://schema.org", "@context_url": "https://schema.org",
          "@graph": [
              {"@type": "Dataset",
               "name": f"Arrecadação da CIP por município no Brasil ({Y0}–{Y1})",
               "description": "Valores de arrecadação da Contribuição para o Custeio do Serviço de Iluminação "
                              "Pública registrados nas Declarações de Contas Anuais (DCA/SICONFI) de municípios brasileiros.",
               "temporalCoverage": f"{Y0}/{Y1}",
               "isAccessibleForFree": True,
               "creator": {"@type": "Organization", "name": "CIP Nacional"},
               "variableMeasured": "Arrecadação anual da CIP (R$)"},
              {"@type": "FAQPage", "mainEntity": faq_arr_json}]}
opts_uf = "".join(f'<option value="{uf}">{uf}</option>' for uf in sorted({a["uf"] for a in arr}))
filter_js = """<script>
(function(){
 const table=document.querySelector('table.sortable-table'), tbody=table.querySelector('tbody'), sel=document.getElementById('filtro-uf'), c=document.getElementById('contador-filtro');
 let rows=[...tbody.querySelectorAll('tr')], direction={};
 function atualizar(){const uf=sel.value; let n=0; rows.forEach(r=>{const show=!uf||r.dataset.uf===uf; r.hidden=!show; if(show)n++;}); c.textContent=uf?('Mostrando '+n+' município(s) de '+uf+'.'):'Mostrando todos os municípios com dado.';}
 function ordenar(col){
   direction[col]=direction[col]==='asc'?'desc':'asc';
   const asc=direction[col]==='asc';
   rows.sort((a,b)=>{let x=a.children[col].dataset.sort||'', y=b.children[col].dataset.sort||''; const nx=Number(x), ny=Number(y); if(!Number.isNaN(nx)&&!Number.isNaN(ny)){x=nx;y=ny;} else {x=x.toString().localeCompare(y.toString(),'pt-BR');y=0;} return (x<y?-1:x>y?1:0)*(asc?1:-1);});
   rows.forEach((r,i)=>{tbody.appendChild(r); r.children[0].textContent=i+1;}); atualizar();
 }
 table.querySelectorAll('th.sortable').forEach(th=>th.addEventListener('click',()=>ordenar(Number(th.dataset.col))));
 sel.addEventListener('change',atualizar); atualizar();
})();
</script>"""
arr_html = f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Arrecadação da CIP por município — total acumulado {Y0}–{Y1}</title>
<meta name="description" content="Quanto cada município brasileiro arrecadou com a Contribuição de Iluminação Pública (CIP) de {Y0} a {Y1}, segundo o SICONFI/Tesouro Nacional. Ranking, total acumulado e valor por habitante.">
<link rel="stylesheet" href="/assets/style.css">
<script type="application/ld+json">{json.dumps(ld_arr, ensure_ascii=False)}</script>
</head><body>
<header><a class="logo" href="/">CIP Nacional</a> <nav><a href="/cip/">Municípios</a> · <a href="/arrecadacao/">Arrecadação</a></nav></header>
<main>
<ul class="crumbs"><li><a href="/cip/">CIP</a></li><li>Arrecadação</li></ul>
<h1>Arrecadação da CIP pelos municípios — total acumulado {Y0}–{Y1}</h1>
<p>Esta página mostra <strong>quanto cada município efetivamente arrecadou</strong> com a
<strong>Contribuição de Iluminação Pública (CIP)</strong> em cada exercício, e o <strong>total acumulado</strong> dos
quatro anos somados. A fonte é a Declaração de Contas Anuais (DCA) de cada prefeitura, publicada no
<strong>SICONFI</strong>, do Tesouro Nacional — a mesma base que os órgãos de controle usam.</p>
<div class="badge ok">✔ {len(arr)} municípios com dado oficial · soma {brl(soma)} · {Y0}–{Y1} · checado em {DATA_BR}</div>
<h2>Resumo</h2>
<ul>
<li><strong>{len(arr)}</strong> dos {len(ARRQ) or len(regs)} municípios desta base têm arrecadação publicada em pelo menos um exercício.</li>
<li><strong>Soma dos totais acumulados:</strong> {brl(soma)}.</li>
<li><strong>Maior arrecadação acumulada:</strong> {esc(arr[0]["municipio"])}/{arr[0]["uf"]} —
{brl(arr[0]["total_acumulado"])} em {Y0}–{Y1}.</li>
<li><strong>Média por habitante</strong> (nos municípios com dado e população informada): {brl(pc_geral)} por habitante no período.</li>
</ul>
<h2>Ranking por arrecadação acumulada</h2>
<label for="filtro-uf"><strong>Filtrar por estado:</strong></label>
<select id="filtro-uf" aria-label="Filtrar por estado"><option value="">Todos os estados</option>{opts_uf}</select>
<p id="contador-filtro" class="unidade">Mostrando todos os municípios com dado.</p>
{tabela}
{filter_js}
<p class="unidade">Valores nominais, em reais, como declarados pelo município — não corrigidos pela inflação.
Última coluna: ✔ quando a tabela de alíquotas do município também foi verificada nesta base.</p>
<h2>Como ler esta tabela</h2>
<p>A CIP é uma contribuição municipal criada pelo art. 149-A da Constituição: quem paga é o consumidor de energia,
na fatura ou no IPTU, e o dinheiro é vinculado ao custeio, manutenção, ampliação e melhoria da iluminação pública.
Como a competência é de cada município, o desenho da cobrança varia muito: há cidades que cobram percentual sobre
a tarifa, outras com valor fixo por faixa de consumo e outras com fórmula própria. Por isso, comparar
<em>alíquotas</em> entre municípios exige olhar o mecanismo de cada um — e comparar <em>arrecadação</em> exige olhar
o tamanho da cidade.</p>
<p>O total acumulado serve para três leituras práticas: dimensionar o mercado de iluminação pública de um município
(quanto recurso circula por ano), verificar se o valor arrecadado é compatível com o parque de iluminação instalado
e acompanhar a evolução ano a ano — um salto atípico costuma indicar mudança de lei ou de base de cálculo.</p>
<p>Duas ressalvas importantes. Primeiro, arrecadação não é despesa: o município pode arrecadar um valor e aplicar
outro, já que a CIP pode ser usada também para amortizar investimentos na rede. Segundo, nem todo município
entrega a DCA no prazo — quando o dado não está publicado, esta página mostra <em>n/d</em> em vez de estimar.</p>
<h2>Perguntas frequentes</h2>
{faq_arr_html}
<h2>Fontes</h2>
<ul>
<li><a href="https://apidatalake.tesouro.gov.br/ords/siconfi/tt/dca" rel="noopener" target="_blank">API SICONFI / DCA — Tesouro Nacional</a> (conta 1.2.4.0.00.0.0, coleta em {DATA_BR})</li>
<li><a href="https://siconfi.tesouro.gov.br/" rel="noopener" target="_blank">SICONFI — portal público</a></li>
</ul>
{"<h2>Municípios sem dado publicado</h2><p>Sem DCA com a conta da CIP localizada nos exercícios " + str(Y0) + "–" + str(Y1) + ":</p><ul>" + "".join(f'<li>{esc(a["municipio"])}/{a["uf"]}</li>' for a in sem_dado) + "</ul>" if sem_dado else ""}
<p><a href="/cip/">← Ver alíquotas por município</a></p>
</main>
<footer><p>Dados oficiais do SICONFI/Tesouro Nacional · coletado em {DATA_BR} · nenhum valor estimado.</p></footer>
</body></html>"""
os.makedirs(f"{OUT}/arrecadacao", exist_ok=True)
open(f"{OUT}/arrecadacao/index.html", "w", encoding="utf-8").write(arr_html)

# raiz
root = f"""<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CIP Nacional — alíquotas de iluminação pública por município</title>
<meta name="description" content="Consulte a Contribuição de Iluminação Pública (CIP) do seu município: alíquotas oficiais, base legal e data da verificação.">
<link rel="stylesheet" href="/assets/style.css"></head><body>
<header><a class="logo" href="/">CIP Nacional</a> <nav><a href="/cip/">Municípios</a> · <a href="/arrecadacao/">Arrecadação</a></nav></header>
<main><h1>CIP Nacional — alíquotas de iluminação pública por município</h1>
<p>Consulta gratuita das alíquotas da <strong>Contribuição de Iluminação Pública (CIP)</strong> em municípios brasileiros: tabela de faixas, base legal, isenções e a <strong>data exata da verificação</strong>. Regra desta base: o que não está na fonte oficial aparece como <em>não informado</em> — nenhum valor é estimado.</p>
<p>Cada município tem uma página ({len(regs)} páginas), organizada por estado e por distribuidora.</p>
<p><a href="/cip/">→ Consultar municípios</a></p></main>
<footer><p>Registro checado em {DATA_BR} · nenhum valor estimado.</p></footer></body></html>"""
open(f"{OUT}/index.html", "w", encoding="utf-8").write(root)

# ---------- prefixar links internos (base do site: /cip-nacional) ----------
PREFIX = "/cip-nacional"
for dp, _, fs in os.walk(OUT):
    for f in fs:
        if not f.endswith(".html"): continue
        fp = os.path.join(dp, f)
        txt = open(fp, encoding="utf-8").read()
        txt2 = re.sub(r'href="(/(?!cip-nacional/)[^"]*)"',
                      lambda m: f'href="{PREFIX}{m.group(1)}"', txt)
        if txt2 != txt:
            open(fp, "w", encoding="utf-8").write(txt2)

# ---------- verificar ----------
arqs = []
for dp, _, fs in os.walk(OUT):
    for f in fs:
        arqs.append(os.path.join(dp, f))
paginas = [a for a in arqs if a.endswith(".html")]
# vazamento de template no HTML (ignora atributos HTML legitimos e conteudo de tags <script>)
vazamentos = []
for p in paginas:
    txt = open(p, encoding="utf-8").read()
    # remove conteudo de tags script (possui JSON com chaves e aspas)
    txt_sem_script = re.sub(r'<script.*?</script>', '', txt, flags=re.S)
    # remove tags HTML para ficar so texto visivel
    txt_só_texto = re.sub(r'<[^>]+>', ' ', txt_sem_script)
    # detecta "nan" como palavra solta (nao dentro de "nao encontrado")
    texto_normalizado = ' ' + txt_só_texto.lower().replace('\n', ' ') + ' '
    if ' nan ' in texto_normalizado:
        vazamentos.append((p.replace(OUT, ""), 'nan'))
    for frag in ['"', '{', '}', 'None']:
        if frag in txt_só_texto:
            vazamentos.append((p.replace(OUT, ""), frag))
if vazamentos:
    print("Vazamentos de template detectados:")
    for v in vazamentos[:20]: print("  ", v)
# links internos resolvem?
quebrados = set()
for p in paginas:
    txt = open(p, encoding="utf-8").read()
    for href in re.findall(r'href="(/[^"]+)"', txt):
        href = href[len(PREFIX):] if href.startswith(PREFIX) else href
        alvo = os.path.join(OUT, href.lstrip("/"))
        ok = os.path.exists(alvo) or os.path.exists(os.path.join(alvo, "index.html")) or os.path.exists(alvo.rstrip("/"))
        if not ok: quebrados.add((p.replace(OUT, ""), href))
print(f"arquivos: {len(arqs)} | páginas html: {len(paginas)} | municípios: {n}")
print(f"links internos quebrados: {len(quebrados)}")
for q in sorted(quebrados)[:10]: print("  ", q)
# word count de uma página completa e uma parcial
for alvo in [r for r in regs if r["status"] == "completo"][0], [r for r in regs if r["status"] == "parcial"][0]:
    txt = open(f"{OUT}/cip/{alvo['uf'].lower()}/{alvo['slug']}/index.html", encoding="utf-8").read()
    corpo = re.sub(r"<script.*?</script>|<[^>]+>", " ", txt, flags=re.S)
    print(f"palavras {alvo['municipio']} ({alvo['status']}): {len(corpo.split())}")
sys.exit(1 if (quebrados or vazamentos) else 0)
