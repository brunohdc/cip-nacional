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

FONTS = """<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Epilogue:wght@400;500;600&display=swap" rel="stylesheet">"""

def topbar():
    return """<header class="shell topbar">
<a class="brand" href="/"><span class="brand-mark">C</span>CIP Nacional</a>
<div class="top-meta"><span class="status"><span class="status-dot"></span>Consulta pública</span><span>Brasil</span></div>
<nav><a href="/cip/">Municípios</a><a href="https://brunohdc.github.io/cip-arrecadada-por-municipio/">Arrecadação</a></nav>
</header>"""

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
STATUS_SHORT = {"completo": "verificado", "parcial": "parcial", "nao_encontrado": "não informado"}
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
    n_faixas = sum(len(linhas) for linhas in (r.get("tabelas") or {}).values())
    dist = ", ".join(esc(d) for d in r.get("distribuidoras", [])) or "não informada"
    if not tem_tabela and r["status"] != "completo":
        resumo_texto = ("Informação parcial; a tabela completa não foi localizada."
                        if r["status"] == "parcial" else "Não informado; nenhuma lei local foi encontrada.")
    else:
        resumo_texto = f"{tipo_txt} por faixa de consumo."
        if tipo == "percentual" and r.get("base_calculo"):
            b = r["base_calculo"]
            resumo_texto += f" Incide sobre {b.get('descricao', 'a base municipal')} de {brl(b.get('valor'))}."
        resumo_texto += f" Repassada por {dist}."
    hero_copy = (
        "Valores pagos por faixa de consumo, com base legal, exercício e fonte verificada. "
        "O que não está na fonte oficial aparece como não informado — nenhum valor é estimado."
        if tem_tabela else
        "A tabela de cobrança ainda não foi localizada. Veja a base legal, as ressalvas e as pendências desta apuração."
    )
    art_footer = "por faixa de consumo" if tem_tabela else "tabela não localizada"
    base = r.get("base_calculo") or {}
    base_row = ""
    if tipo == "percentual" and base:
        base_row = (
            f'<div class="meta-row"><dt>Base</dt><dd>{esc(base.get("descricao", "base municipal"))}'
            f'<br>{brl(base.get("valor"))} em {esc(str(base.get("exercicio", "n/d")))}</dd></div>'
        )

    tabela = tabela_html(r)
    tabela_final = (
        f'<div class="table-wrap">{tabela}</div>' if tabela else
        '<div class="empty"><strong>Tabela não localizada</strong>'
        'A base legal e as pendências estão nos detalhes abaixo.</div>'
    )

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

    detalhes = [f"<details><summary>Como calculamos</summary>{calc}</details>"]
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
        detalhes.append("<details><summary>Base legal, isenções e ressalvas</summary>" + "".join(legal) + "</details>")

    if r.get("fontes"):
        detalhes.append("<details><summary>Fontes verificadas</summary><ul>" + "".join(
            f'<li><a href="{esc(f["url"])}" rel="noopener" target="_blank">{esc(f["titulo"])}</a> '
            f'({esc(f["tipo"])}, checado em {esc(f["data_coleta"])})</li>' for f in r["fontes"]) + "</ul></details>")

    irmaos = [s for s in ufs_siblings if s["slug"] != r["slug"]][:8]
    if irmaos:
        lis = "".join(f'<li><a href="/cip/{uf.lower()}/{s["slug"]}/">{esc(s["municipio"])}</a></li>' for s in irmaos)
        detalhes.append(f'<details><summary>Outros municípios de {uf}</summary>'
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
{FONTS}
<link rel="stylesheet" href="/assets/style.css">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
</head><body>
{topbar()}
<main class="shell">
<section class="hero" aria-labelledby="page-title">
<div>
<div class="eyebrow">Consulta municipal · {uf}</div>
<h1 id="page-title">CIP em <em>{esc(nome)}</em></h1>
<p class="hero-copy">{hero_copy}</p>
</div>
<div class="hero-art" aria-hidden="true">
<div class="art-coin">R$</div>
<div class="art-copy">
<strong>{esc(tipo_txt)}</strong>
<span>{exercicio or 'exercício não informado'} · {uf}</span>
<div class="art-rule"></div>
<span>{art_footer}</span>
</div>
</div>
</section>
<ul class="crumbs">{bc}</ul>
<section class="workspace" aria-label="Cobrança da CIP">
<div class="panel">
<div class="section-head">
<div><div class="section-kicker">Tabela de cobrança</div><h2>Faixas e valores</h2></div>
<div class="result-count">{n_faixas} faixas</div>
</div>
{tabela_final}
</div>
<aside class="focus" aria-label="Resumo da cobrança">
<div class="focus-top">
<div class="focus-label"><span>Resumo</span><span class="focus-index">{uf}</span></div>
<h2 class="focus-title">{esc(tipo_txt)}</h2>
<p class="focus-kind">{esc(STATUS_TXT[r['status']])}</p>
<p class="focus-description">{esc(resumo_texto)}</p>
</div>
<div class="focus-bottom">
{badge}
<dl class="meta-list">
<div class="meta-row"><dt>Exercício</dt><dd>{exercicio or 'n/d'}</dd></div>
{base_row}
<div class="meta-row"><dt>Distribuidora</dt><dd>{dist}</dd></div>
<div class="meta-row"><dt>Checado</dt><dd>{data}</dd></div>
</dl>
</div>
</aside>
</section>
<section class="faq" aria-labelledby="detalhes-title">
<div class="faq-head"><div class="section-kicker">Detalhes</div><h2 id="detalhes-title">Cálculo, base legal e fontes</h2></div>
<div class="faq-grid">{"".join(detalhes)}</div>
</section>
</main>
<footer class="footer shell"><span>Registro checado em {data} · próxima revisão {esc(r["proxima_revisao"])}.</span><span>Nenhum valor estimado.</span></footer>
</body></html>"""

def hub_page(titulo, intro, itens, back=None):
    lis = "".join(
        f'<li><a href="{p}">{esc(t)}</a><span class="st st-{s}">{esc(STATUS_SHORT.get(s, s))}</span></li>'
        for t, p, s in itens
    )
    crumbs = ('<ul class="crumbs"><li><a href="/cip/">CIP</a></li>'
              f'<li>{esc(titulo)}</li></ul>' if back else '<ul class="crumbs"><li>CIP</li></ul>')
    return f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(titulo)}</title><meta name="description" content="{esc(intro[:150])}">
{FONTS}
<link rel="stylesheet" href="/assets/style.css"></head><body>
{topbar()}
<main class="shell">
{crumbs}
<section class="hero" aria-labelledby="page-title">
<div>
<div class="eyebrow">Consulta pública · {len(itens)} municípios</div>
<h1 id="page-title">{esc(titulo)}</h1>
<p class="hero-copy">{esc(intro)}</p>
</div>
<div class="hero-art" aria-hidden="true">
<div class="art-coin">CIP</div>
<div class="art-copy">
<strong>{len(itens)}</strong>
<span>municípios</span>
<div class="art-rule"></div>
<span>lista atualizada</span>
</div>
</div>
</section>
<section class="panel" aria-label="Lista de municípios">
<div class="section-head">
<div><div class="section-kicker">Lista</div><h2>Municípios</h2></div>
<div class="result-count">{len(itens)} registros</div>
</div>
<div class="toolbar">
<label class="search"><span class="sr-only">Buscar município</span><svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true"><circle cx="10.8" cy="10.8" r="6.8" stroke="currentColor" stroke-width="1.5"/><path d="m16 16 4.5 4.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg><input id="busca" type="search" placeholder="Buscar município…" autocomplete="off"></label>
</div>
<ul class="links dois">{lis}</ul>
</section>
</main>
<footer class="footer shell"><span>Consulta gratuita · checado em {DATA_BR} · nenhum valor estimado.</span><span>CIP Nacional</span></footer>
<script>
(function(){{
 const q=document.getElementById('busca'); if(!q)return;
 const items=[...document.querySelectorAll('.links li')];
 q.addEventListener('input',()=>{{const s=q.value.toLowerCase(); items.forEach(li=>{{li.hidden=!li.textContent.toLowerCase().includes(s);}});}});
}})();
</script>
</body></html>"""

# ---------- gerar ----------
CSS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "style.css")
os.makedirs(f"{OUT}/assets", exist_ok=True)
with open(CSS_PATH, encoding="utf-8") as f:
    css = f.read()
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
root = f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CIP Nacional — alíquotas de iluminação pública por município</title>
<meta name="description" content="Consulte a Contribuição de Iluminação Pública (CIP) do seu município: valores por faixa, base legal e data da verificação.">
{FONTS}
<link rel="stylesheet" href="/assets/style.css"></head><body>
{topbar()}
<main class="shell">
<section class="hero" aria-labelledby="page-title">
<div>
<div class="eyebrow">Consulta pública · Brasil</div>
<h1 id="page-title">CIP no Brasil.<br><em>Valor claro.</em></h1>
<p class="hero-copy">Consulte os valores da <strong>Contribuição de Iluminação Pública (CIP)</strong> por município: faixas, base legal, isenções e a data exata da verificação. O que não está na fonte oficial aparece como não informado — nenhum valor é estimado.</p>
<a class="cta" href="/cip/">Consultar municípios</a>
</div>
<div class="hero-art" aria-hidden="true">
<div class="art-coin">R$</div>
<div class="art-copy">
<strong>{len(regs)}</strong>
<span>municípios</span>
<div class="art-rule"></div>
<span>consulta gratuita</span>
</div>
</div>
</section>
<section class="workspace" aria-label="Formas de consulta">
<div class="panel">
<div class="section-head">
<div><div class="section-kicker">Consulta</div><h2>Escolha o caminho</h2></div>
<div class="result-count">{len(by_uf)} UFs</div>
</div>
<ul class="links tres">
<li><a href="/cip/">Por município</a><span class="st st-completo">{len(regs)} páginas</span></li>
<li><a href="/distribuidora/">Por distribuidora</a><span class="st st-completo">{len(by_dist)}</span></li>
<li><a href="https://brunohdc.github.io/cip-arrecadada-por-municipio/">Arrecadação</a><span class="st st-completo">SICONFI</span></li>
</ul>
</div>
<aside class="focus" aria-label="Resumo da base">
<div class="focus-top">
<div class="focus-label"><span>Base</span><span class="focus-index">BR</span></div>
<h2 class="focus-title">Dados oficiais</h2>
<p class="focus-kind">Sem estimativas</p>
<p class="focus-description">Cada página mostra a faixa, o valor, a base legal e a data da checagem. O que não está na fonte oficial aparece como não informado.</p>
</div>
<div class="focus-bottom">
<dl class="meta-list">
<div class="meta-row"><dt>Municípios</dt><dd>{len(regs)}</dd></div>
<div class="meta-row"><dt>Estados</dt><dd>{len(by_uf)}</dd></div>
<div class="meta-row"><dt>Distribuidoras</dt><dd>{len(by_dist)}</dd></div>
<div class="meta-row"><dt>Checado</dt><dd>{DATA_BR}</dd></div>
</dl>
</div>
</aside>
</section>
</main>
<footer class="footer shell"><span>Registro checado em {DATA_BR} · nenhum valor estimado.</span><span>CIP Nacional</span></footer>
</body></html>"""
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
