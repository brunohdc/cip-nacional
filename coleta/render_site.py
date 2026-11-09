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

from cobranca import brl, esta_desatualizado, fmt_data, fmt_faixa, fmt_valor, tipo_label, validate_record

BASE = os.environ.get("CIP_BASE", os.path.expanduser("~/workspace/cip_collected"))
OUT = os.environ.get("CIP_SITE", os.path.expanduser("~/workspace/cip_site"))
ONLY_MUNICIPAL = os.environ.get("CIP_ONLY", "1" if os.environ.get("CIP_DATA") else "0") == "1"
DATA_ENV = os.environ.get("CIP_DATA")
DATASET_PATH = DATA_ENV or (f"{BASE}/cip_top500.json" if os.path.exists(f"{BASE}/cip_top500.json") else f"{BASE}/cip_top100.json")
regs = json.load(open(DATASET_PATH, encoding="utf-8"))
for _reg in regs:
    validate_record(_reg)
DATA_BR = fmt_data(max((r.get("atualizado_em") for r in regs if r.get("atualizado_em")), default="2026-10-01"))

def slugify(s):
    s = unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9\s-]", "", s).strip().lower()
    return re.sub(r"[\s]+", "-", s)

def esc(s):
    return html.escape(str(s), quote=True)

MEC = {
    "percentual_base": "percentual sobre uma base municipal documentada",
    "percentual_modulo_tip": "percentual sobre o módulo de referência TIP",
    "percentual_teip": "percentual sobre o TEIP (Tarifa de Energia na Estrada de Entrega — módulo B4a)",
    "formula_teip": "fórmula com componentes fixo e variável sobre o TEIP",
    "valor_fixo": "valor fixo por faixa de consumo (R$ por mês)",
    "outro": "percentual sobre a base de cálculo/rateio definida em lei",
    "desconhecido": "ainda não confirmado (tabela oficial não localizada)",
}
MEC_CURTO = {
    "percentual_base": "Percentual sobre base municipal",
    "percentual_modulo_tip": "Percentual sobre TIP",
    "percentual_teip": "Percentual sobre TEIP",
    "formula_teip": "Fórmula sobre TEIP",
    "valor_fixo": "Valor fixo",
    "outro": "Percentual sobre base municipal",
    "desconhecido": "Não informado",
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

CLASSE_TXT = {"residencial": "Residencial", "nao_residencial": "Não residencial", "nao_edificado": "Não edificado"}

def tabela_html(r):
    if not r.get("tabelas"): return ""
    out = []
    for classe, linhas in r["tabelas"].items():
        nome_classe = CLASSE_TXT.get(classe, classe.replace("_", " ").capitalize())
        out.append(f'<h3>{esc(nome_classe)}</h3>')
        out.append('<table class="tab"><thead><tr><th>Faixa de consumo</th><th>Cobrança</th></tr></thead><tbody>')
        for f in linhas:
            nota = f'<span class="nota"> — {esc(f["nota"])}</span>' if f.get("nota") and "isento" not in str(f.get("valor", "")).lower() else ""
            out.append(f'<tr><td>{esc(fmt_faixa(f, r))}</td><td><strong>{esc(fmt_valor(f, r))}</strong>{nota}</td></tr>')
        out.append("</tbody></table>")
    if r.get("tipo") == "percentual":
        base = r.get("base_calculo") or {}
        out.append(f'<p class="unidade"><strong>Base:</strong> {esc(base.get("descricao", "base municipal"))} — '
                   f'{brl(base.get("valor"))} em {esc(str(base.get("exercicio", "exercício não informado")))}.</p>')
    elif r.get("tipo") == "fixa":
        out.append('<p class="unidade">Valores em R$/mês.</p>')
    else:
        un = next((f.get("unidade", "BRL") for ls in r["tabelas"].values() for f in ls), "BRL")
        out.append(f'<p class="unidade">Unidade: {esc(UNIT_TXT.get(un, un))}.</p>')
    return "\n".join(out)

def page(r, uf_hub, hub, ufs_siblings):
    nome, uf = r["municipio"], r["uf"]
    tipo = r.get("tipo")
    if tipo:
        tipo_txt = tipo_label(tipo)
    elif r.get("mecanismo") in MEC_CURTO and r["mecanismo"] != "desconhecido":
        tipo_txt = MEC_CURTO[r["mecanismo"]]
    elif r["status"] == "parcial":
        tipo_txt = "Informação parcial"
    else:
        tipo_txt = "Não informado"
    exercicio = r.get("exercicio")
    ex = f" {exercicio}" if exercicio else ""
    title = f"CIP em {nome} ({uf}) — {tipo_txt}{ex}"
    data = fmt_data(r["atualizado_em"]) if r.get("atualizado_em") else DATA_BR
    desc = f"CIP em {nome}/{uf}: {tipo_txt}{ex}, base legal e fontes verificadas em {data}."
    stale = esta_desatualizado(r)
    if r["status"] == "completo" and not stale:
        badge = f'<div class="badge ok">✔ Tabela oficial verificada — checado em {data}</div>'
    elif r["status"] == "completo":
        badge = f'<div class="badge warn">◐ Valores de {exercicio} — confira a atualização · checado em {data}</div>'
    elif r["status"] == "parcial":
        badge = f'<div class="badge warn">◐ Informação parcial — checado em {data}</div>'
    else:
        badge = f'<div class="badge none">○ Não informado — sem lei local encontrada ({data})</div>'

    tem_tabela = bool(r.get("tabelas"))
    if not tem_tabela and r["status"] != "completo":
        resumo = ("Informação parcial; a tabela completa não foi localizada."
                  if r["status"] == "parcial" else "Não informado; nenhuma lei local foi encontrada.")
    else:
        resumo = f"<strong>{esc(tipo_txt)}</strong> por faixa de consumo."
        if tipo == "percentual" and r.get("base_calculo"):
            b = r["base_calculo"]
            resumo += f" Incide sobre {esc(b.get('descricao', 'a base municipal'))} de {brl(b.get('valor'))}."
    dist = ", ".join(esc(d) for d in r.get("distribuidoras", [])) or "não informada"
    resumo += f" Repassada por: {dist}."

    body = [f'<div class="resumo">{badge}<p>{resumo}</p></div>']
    tabela = tabela_html(r)
    if tabela:
        body.append("<h2>Cobrança</h2>" + tabela)
    else:
        body.append('<p class="aviso">Tabela de cobrança não localizada na fonte oficial.</p>')

    if not tem_tabela and r["status"] != "completo":
        calc = "<p>A forma de cálculo ainda não foi confirmada na fonte oficial.</p>"
    elif tipo == "percentual" and r.get("base_calculo"):
        b = r["base_calculo"]
        calc = (f"<p>Valor mensal = percentual ÷ 100 × {esc(b.get('descricao', 'base'))} "
                f"({brl(b.get('valor'))}). O valor estimado em reais aparece ao lado de cada faixa.</p>")
    elif tipo == "fixa":
        calc = "<p>O valor da tabela é cobrado por mês, conforme a faixa de consumo.</p>"
    elif r["mecanismo"] == "formula_teip":
        calc = "<p>A cobrança usa a fórmula publicada na fonte. Ela não é convertida em percentual nem calculada sem a tarifa de referência.</p>"
    else:
        calc = f"<p>{esc(MEC.get(r['mecanismo'], 'A forma de cálculo ainda não foi confirmada.'))}</p>"
    body.append(f"<details><summary>Como calculamos</summary>{calc}</details>")

    legal = []
    if r.get("base_legal"):
        legal.append("<h3>Base legal</h3><ul>" + "".join(
            f'<li>{esc(b["norma"])}' + (f' — vigência {esc(b["vigencia"])}' if b.get("vigencia") else "") +
            (f' — <a href="{esc(b["fonte_url"])}" rel="noopener" target="_blank">ver fonte</a>' if b.get("fonte_url") else "") + "</li>"
            for b in r["base_legal"]) + "</ul>")
    if r.get("isencoes"):
        legal.append("<h3>Isenções</h3><ul>" + "".join(
            f'<li>{esc(i.get("descricao", "n/d"))} — base: {esc(i.get("base_legal", "n/d"))}</li>' for i in r["isencoes"]) + "</ul>")
    if r.get("observacoes"):
        legal.append(f"<h3>Observações</h3><p>{esc(r['observacoes'])}</p>")
    if r.get("ressalvas"):
        legal.append("<h3>Ressalvas de verificação</h3><ul>" +
                     "".join(f"<li>{esc(x)}</li>" for x in r["ressalvas"]) + "</ul>")
    if r.get("pendencias"):
        legal.append("<h3>O que ainda falta</h3><ul>" +
                     "".join(f"<li>{esc(x)}</li>" for x in r["pendencias"]) + "</ul>")
    if legal:
        body.append("<details><summary>Base legal, isenções e ressalvas</summary>" + "".join(legal) + "</details>")

    if r.get("fontes"):
        body.append("<details><summary>Fontes verificadas</summary><ul>" + "".join(
            f'<li><a href="{esc(f["url"])}" rel="noopener" target="_blank">{esc(f["titulo"])}</a> '
            f'({esc(f["tipo"])}, checado em {esc(f["data_coleta"])})</li>' for f in r["fontes"]) + "</ul></details>")

    irmaos = [s for s in ufs_siblings if s["slug"] != r["slug"]][:8]
    if irmaos:
        lis = "".join(f'<li><a href="/cip/{uf.lower()}/{s["slug"]}/">{esc(s["municipio"])}</a></li>' for s in irmaos)
        body.append(f'<details><summary>Outros municípios de {uf}</summary>'
                    f'<p><a href="{uf_hub}">Ver todos os municípios de {uf}</a></p>'
                    f'<ul class="links">{lis}</ul></details>')

    crumbs = [("CIP", "/cip/"), (uf.upper(), f"/cip/{uf.lower()}/"), (nome, None)]
    bc = "".join(f'<li><a href="{p}">{esc(n)}</a></li>' if p else f"<li>{esc(n)}</li>" for n, p in crumbs)
    ld = {"@context": "https://schema.org", "@type": "WebPage", "name": title, "description": desc}
    if r.get("atualizado_em"):
        ld["dateModified"] = r["atualizado_em"]
    return f"""<!DOCTYPE html>
<html lang="pt-BR"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}">
<link rel="stylesheet" href="/assets/style.css">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
</head><body>
<header><a class="logo" href="/">CIP Nacional</a> <nav><a href="/cip/">Municípios</a> · <a href="https://brunohdc.github.io/cip-arrecadada-por-municipio/">Arrecadação</a></nav></header>
<main>
<ul class="crumbs">{bc}</ul>
<h1>{esc(title)}</h1>
{"".join(body)}
</main>
<footer><p>Registro checado em {data} · próxima revisão {esc(r["proxima_revisao"])} · nenhum valor estimado.</p></footer>
</body></html>"""

def hub_page(titulo, intro, itens, back=None):
    lis = "".join(f'<li><a href="{p}">{esc(t)}</a> <span class="st st-{s}">{s.replace("_"," ")}</span></li>'
                  for t, p, s in itens)
    bc = f'<ul class="crumbs"><li><a href="/cip/">CIP</a></li>' if back else '<ul class="crumbs">'
    return f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(titulo)}</title><meta name="description" content="{esc(intro[:150])}">
<link rel="stylesheet" href="/assets/style.css"></head><body>
<header><a class="logo" href="/">CIP Nacional</a> <nav><a href="/cip/">Municípios</a> · <a href="https://brunohdc.github.io/cip-arrecadada-por-municipio/">Arrecadação</a></nav></header>
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
.resumo{display:flex;gap:.75rem;align-items:center;flex-wrap:wrap;margin:.5rem 0 1rem}
.resumo p{margin:0}
.aviso{background:#fff8e6;border-left:3px solid #d39e00;padding:.5rem .7rem;font-size:.9rem}
details{margin:.6rem 0;border-bottom:1px solid #eee;padding:.25rem 0}
summary{cursor:pointer;font-weight:600;padding:.25rem 0}
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
open(f"{OUT}/assets/style.css", "w", encoding="utf-8").write(css)

PREFIX = "/cip-nacional"

def prefix_links():
    for dp, _, fs in os.walk(OUT):
        for f in fs:
            if not f.endswith(".html"):
                continue
            fp = os.path.join(dp, f)
            txt = open(fp, encoding="utf-8").read()
            txt2 = re.sub(r'href="(/(?!cip-nacional/)[^"]*)"', lambda m: f'href="{PREFIX}{m.group(1)}"', txt)
            if txt2 != txt:
                open(fp, "w", encoding="utf-8").write(txt2)

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

if ONLY_MUNICIPAL:
    prefix_links()
    print(f"modo piloto: {n} páginas municipais geradas em {OUT}")
    sys.exit(0)

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
# raiz
root = f"""<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CIP Nacional — alíquotas de iluminação pública por município</title>
<meta name="description" content="Consulte a Contribuição de Iluminação Pública (CIP) do seu município: alíquotas oficiais, base legal e data da verificação.">
<link rel="stylesheet" href="/assets/style.css"></head><body>
<header><a class="logo" href="/">CIP Nacional</a> <nav><a href="/cip/">Municípios</a> · <a href="https://brunohdc.github.io/cip-arrecadada-por-municipio/">Arrecadação</a></nav></header>
<main><h1>CIP Nacional — alíquotas de iluminação pública por município</h1>
<p>Consulta gratuita das alíquotas da <strong>Contribuição de Iluminação Pública (CIP)</strong> em municípios brasileiros: tabela de faixas, base legal, isenções e a <strong>data exata da verificação</strong>. Regra desta base: o que não está na fonte oficial aparece como <em>não informado</em> — nenhum valor é estimado.</p>
<p>Cada município tem uma página ({len(regs)} páginas), organizada por estado e por distribuidora.</p>
<p><a href="/cip/">→ Consultar municípios</a></p></main>
<footer><p>Registro checado em {DATA_BR} · nenhum valor estimado.</p></footer></body></html>"""
open(f"{OUT}/index.html", "w", encoding="utf-8").write(root)

# ---------- prefixar links internos (base do site: /cip-nacional) ----------
prefix_links()

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
