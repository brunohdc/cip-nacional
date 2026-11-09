#!/usr/bin/env python3
"""Monta batches/saida_lote2.json (30 registros) a partir dos dados coletados."""
import json, os, sys, unicodedata

BASE = os.environ.get("CIP_BASE", os.path.expanduser("~/workspace/cip_collected"))
DATA = "2026-10-01"
lotes = {l["cod"]: l for l in json.load(open(f"{BASE}/batches/lote2.json"))}
dist_list = json.load(open(f"{BASE}/municipio_distribuidora.json"))
dist_map = {d["cod_ibge"]: d["distribuidoras"] for d in dist_list}
# normalize keys: nome_sem_acento
def na(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").lower()

by_name = {}
for cod, l in lotes.items():
    nome, _, uf = l["nome"].rpartition(" - ")
    l["nome"], l["uf"] = nome.strip(), uf.strip()
    by_name[na(l["nome"])] = (cod, l)

def dist(cod, nome):
    d = dist_map.get(str(cod))
    if d is None:
        raise SystemExit(f"distribuidora nao achada: {nome} {cod}")
    return d

def F(lo, hi, val, un, nota=None):
    e = {"faixa_kwh": {"min": lo, "max": hi}, "valor": val, "unidade": un}
    if nota: e["nota"] = nota
    return e

def mk(nome, status, mecanismo, exercicio, tabelas, base_legal, fontes,
       isencoes=None, ressalvas=None, pendencias=None, obs=None):
    cod_s, l = by_name[na(nome)]
    fixed = []
    for i in (isencoes or []):
        ni = {}
        for k, v in i.items():
            ni["descricao" if k == "condicao" else k] = v
        fixed.append(ni)
    isencoes = fixed
    slug = na(l["nome"]).replace(" ", "-").replace(",", "").replace(".", "")
    descricao = None
    if status == "completo" and base_legal:
        ex = f" exercício {exercicio}" if exercicio else ""
        descricao = (f"Alíquotas de CIP (Contribuição de Iluminação Pública) de "
                     f"{l['nome']}/{l['uf']} — {mecanismo}.{ex} Base legal: {base_legal[0]['norma']}.")
    r = {
        "cod_ibge": cod_s, "municipio": l["nome"], "uf": l["uf"], "slug": slug,
        "descricao": descricao,
        "distribuidoras": dist(cod_s, l["nome"]),
        "status": status, "mecanismo": mecanismo, "exercicio": exercicio,
        "tabelas": tabelas,
        "base_legal": base_legal,
        "fontes": [{"url": u, "titulo": t, "tipo": ty, "data_coleta": DATA}
                   for (u, t, ty) in fontes],
        "atualizado_em": DATA, "proxima_revisao": "2026-10-31",
        "ressalvas": ressalvas or [], "pendencias": pendencias or [],
        "isencoes": isencoes or [], "observacoes": obs or "",
    }
    return r

regs = []

# ============ COMPLETOS (7) ============

# 1. Serra-ES — alíquotas % sobre base R$309,26 (Lei 5.125/2019)
PB = "PERCENTUAL_BASE"
regs.append(mk("Serra", "completo", "outro", 2019, {
    "residencial_b": [F(None,50,"isento",PB,"Residencial grupo B"), *[
        F(51,70,2.93,PB), F(71,100,4.42,PB), F(101,150,6.31,PB), F(151,200,9.25,PB),
        F(201,300,11.31,PB), F(301,400,15.25,PB), F(401,500,17.97,PB), F(500,None,20.22,PB)]],
    "nao_residencial_b": [
        F(None,30,3.97,PB,"Demais classes grupo B"), F(31,50,4.73,PB), F(51,70,7.85,PB),
        F(71,100,9.25,PB), F(101,150,11.13,PB), F(151,200,15.24,PB), F(201,300,17.97,PB),
        F(301,400,18.19,PB), F(401,500,19.89,PB), F(500,None,25.05,PB)],
    "residencial_a": [F(None,1000,20.00,PB,"Residencial grupo A (Alta Tensão)"),
                      F(1001,5000,40.00,PB), F(5000,None,60.00,PB)],
    "nao_residencial_a": [F(None,1000,75.00,PB,"Demais classes grupo A"),
                          F(1001,5000,100.00,PB), F(5000,None,150.00,PB)],
}, [{"norma": "Lei 5.125/2019 (base de cálculo R$309,26, art.3º; alíquotas Anexos I-B/I-C/I-D/I-E)", "vigencia": "2019", "fonte_url": "https://legislacao.serra.es.gov.br/Arquivo/Documents/legislacao/html/L51252019.html"},
    {"norma": "Lei 6.154/2025 (altera §1º art.1º)", "vigencia": "2025", "fonte_url": "https://legislacao.serra.es.gov.br/Arquivo/Documents/legislacao/html/L51252019.html"}],
    [("https://legislacao.serra.es.gov.br/Arquivo/Documents/legislacao/html/L51252019.html", "Lei 5.125/2019 — Serra/ES", "fonte_oficial")],
    isencoes=[{"tipo": "faixa_consumo", "limite_kwh": 50, "condicao": "Residencial grupo B até 50 kWh (art.1º §3º)", "base_legal": "Lei 5.125/2019", "fonte_url": "https://legislacao.serra.es.gov.br/Arquivo/Documents/legislacao/html/L51252019.html"},
              {"tipo": "classe_ou_condicao", "condicao": "Imóveis de entidades filantrópicas (art.11 §1º)", "base_legal": "Lei 5.125/2019", "fonte_url": "https://legislacao.serra.es.gov.br/Arquivo/Documents/legislacao/html/L51252019.html"}],
    ressalvas=["Alíquotas em % sobre base fixa de R$309,26 (não é % de TIP/TEIP) — art.1º §1º; Lei 6.154/2025 alterou o §1º",
               "Tabelas I-B/I-C extraídas do HTML oficial (layout do portal sem cabeçalho visível na captura)"],
    pendencias=["Confirmar exercício corrente da base R$309,26 (atualização prevista na lei)"],
    obs="Grupo A = alta tensão."))

# 2. Porto Velho-RO — LC 675/2017, R$/faixa kWh
BRL = "BRL"
regs.append(mk("Porto Velho", "completo", "valor_fixo", None, {
    "residencial_urbano": [F(None,30,"isento",BRL), F(31,50,2.03,BRL), F(51,100,4.31,BRL),
                           F(101,200,7.61,BRL), F(201,500,20.29,BRL), F(501,1000,30.43,BRL),
                           F(1001,1500,45.64,BRL), F(1500,None,68.97,BRL)],
    "residencial_rural": [F(None,100,"isento",BRL), F(101,200,7.61,BRL), F(201,500,17.75,BRL),
                          F(501,1000,26.63,BRL), F(1001,1500,40.83,BRL), F(1500,None,60.35,BRL)],
    "nao_residencial": [F(None,30,0.83,BRL), F(31,50,1.95,BRL), F(51,100,13.94,BRL),
                        F(101,200,27.89,BRL), F(201,500,55.79,BRL), F(501,1000,83.68,BRL),
                        F(1001,1500,111.57,BRL), F(1500,None,139.47,BRL)],
}, [{"norma": "LC 675/2017 art.6º (tabelas I/II/III)", "vigencia": "2017", "fonte_url": "https://www.legisweb.com.br/legislacao/?id=384808"}],
    [("https://www.legisweb.com.br/legislacao/?id=384808", "LC 675/2017 — Porto Velho/RO (legisweb)", "agregador_legislacao")],
    isencoes=[{"tipo": "faixa_consumo", "limite_kwh": 30, "condicao": "Residencial urbano até 30 kWh", "base_legal": "LC 675/2017", "fonte_url": "https://www.legisweb.com.br/legislacao/?id=384808"},
              {"tipo": "faixa_consumo", "limite_kwh": 100, "condicao": "Residencial rural até 100 kWh", "base_legal": "LC 675/2017", "fonte_url": "https://www.legisweb.com.br/legislacao/?id=384808"}],
    ressalvas=["Valores da LC 675/2017; atualização anual por Resolução SEMFAZ (ex.: Res. 001/2023, IPCA) — exercício corrente não confirmado"],
    pendencias=["Verificar última Resolução SEMFAZ de atualização da COSIP"],
    obs="Também há tabelas para imóveis não edificados e especial."))

# 3. Macapá-AP — LC 116/2017 Anexo X, % TEIP
PT = "PERCENTUAL_TEIP"
regs.append(mk("Macapá", "completo", "percentual_teip", 2019, {
    "residencial": [F(None,30,0.00,PT), F(31,50,0.00,PT), F(51,100,1.70,PT), F(101,200,3.70,PT),
                    F(201,300,5.70,PT), F(301,400,7.30,PT), F(401,500,9.00,PT), F(501,600,9.80,PT),
                    F(601,750,11.00,PT), F(751,1000,12.20,PT), F(1000,None,14.20,PT)],
    "poder_publico": [F(None,200,10.20,PT), F(201,600,13.40,PT), F(600,None,20.40,PT)],
    "comercial": [F(None,100,6.90,PT), F(101,200,8.10,PT), F(201,300,9.80,PT), F(301,400,11.00,PT),
                  F(401,500,12.20,PT), F(501,600,15.10,PT), F(601,750,17.50,PT), F(751,1000,19.50,PT),
                  F(1000,None,20.80,PT)],
    "industrial": [F(None,5000,13.40,PT), F(5001,20000,26.90,PT), F(20001,50000,40.30,PT),
                   F(50001,110000,69.20,PT), F(110000,None,134.40,PT)],
}, [{"norma": "LC 116/2017 Anexo X", "vigencia": "2017", "fonte_url": "https://lefisc.com.br/regulamentos/stmMacapa/anexoX.asp"},
    {"norma": "LC 132/2019 (redação)", "vigencia": "2019", "fonte_url": "https://lefisc.com.br/regulamentos/stmMacapa/anexoX.asp"}],
    [("https://lefisc.com.br/regulamentos/stmMacapa/anexoX.asp", "Anexo X da LC 116/2017 — Macapá/AP (lefisc)", "agregador_legislacao")],
    isencoes=[{"tipo": "faixa_consumo", "limite_kwh": 30, "condicao": "Residencial até 30 kWh (não ligados: 0-30 isentos)", "base_legal": "LC 116/2017 Anexo X", "fonte_url": "https://lefisc.com.br/regulamentos/stmMacapa/anexoX.asp"}],
    ressalvas=["Possível alteração pela LC 212/2026 (legisweb id=493490) — conferir vigência"],
    pendencias=["Conferir LC 212/2026"],
    obs="Não ligados à rede (exercício 2016): 0-30=0,00% ... >1500=71,00% (%TB4a)."))

# 4. Rio Branco-AC — Lei 1.508/2003 art.114, % sobre custo (rateio)
regs.append(mk("Rio Branco", "completo", "outro", 2003, {
    "geral": [F(None,50,"isento",PB,"Até 50 kWh é isento (art.116)"),
              F(51,100,5.00,PB), F(101,500,6.00,PB), F(500,None,7.00,PB)],
    "alta_tensao": [F(None,None,3.00,PB,"Alta tensão — percentual fixo (art.114 IV)")],
}, [{"norma": "Lei 1.508/2003 (CTM) arts. 113-116", "vigencia": "2003", "fonte_url": "https://portalcgm.riobranco.ac.gov.br/portal/wp-content/uploads/2013/10/LEI-1508-DE-08.12.2003-Codigo-Tributario-Municipal.pdf"}],
    [("https://portalcgm.riobranco.ac.gov.br/portal/wp-content/uploads/2013/10/LEI-1508-DE-08.12.2003-Codigo-Tributario-Municipal.pdf", "CTM Lei 1.508/2003 — Rio Branco/AC (PDF oficial)", "fonte_oficial")],
    isencoes=[{"tipo": "faixa_consumo", "limite_kwh": 50, "condicao": "Consumo mensal até 50 kWh (art.116)", "base_legal": "Lei 1.508/2003", "fonte_url": "https://portalcgm.riobranco.ac.gov.br/portal/wp-content/uploads/2013/10/LEI-1508-DE-08.12.2003-Codigo-Tributario-Municipal.pdf"}],
    ressalvas=["CTM de 2003 — não confirmada vigência integral; percentuais sobre base de rateio (custo individualizado), não sobre TIP/TEIP"],
    pendencias=["Conferir alterações ao CTM desde 2003"],
    obs="Imóveis não edificados: 0,01 UFMRB/m de testada (art.115)."))

# 5. Niterói-RJ — Res. SMF 011/2015, exercício 2016, R$/faixa
regs.append(mk("Niterói", "completo", "valor_fixo", 2016, {
    "grupo_a": [F(None,2000,79.28,BRL,"Grupo A — todas as classes"), F(2001,5000,132.15,BRL),
                F(5001,10000,211.43,BRL), F(10000,None,264.30,BRL)],
    "residencial": [F(None,30,0.00,BRL), F(31,100,2.64,BRL), F(101,200,5.28,BRL),
                    F(201,300,10.57,BRL), F(301,400,15.84,BRL), F(401,500,21.14,BRL),
                    F(501,1000,26.42,BRL), F(1000,None,34.36,BRL)],
    "comercial": [F(None,30,2.64,BRL), F(31,100,5.28,BRL), F(101,200,13.20,BRL),
                  F(201,300,21.14,BRL), F(301,400,23.78,BRL), F(401,500,31.71,BRL),
                  F(501,1000,39.64,BRL), F(1000,None,47.56,BRL)],
    "industrial": [F(None,30,5.28,BRL), F(31,100,7.93,BRL), F(101,200,13.20,BRL),
                   F(201,300,21.14,BRL), F(301,400,29.06,BRL), F(401,500,39.64,BRL),
                   F(501,1000,47.56,BRL), F(1000,None,58.14,BRL)],
}, [{"norma": "Resolução SMF 011/2015 (tabelas COSIP exerc. 2016)", "vigencia": "2016", "fonte_url": "https://www.fazenda.niteroi.rj.gov.br/site/wp-content/uploads/2016/05/Resolucao-SMF-11-2015.pdf"}],
    [("https://www.fazenda.niteroi.rj.gov.br/site/wp-content/uploads/2016/05/Resolucao-SMF-11-2015.pdf", "Resolução SMF 011/2015 — Niterói/RJ (PDF oficial)", "fonte_oficial")],
    isencoes=[{"tipo": "faixa_consumo", "limite_kwh": 30, "condicao": "Residencial até 30 kWh", "base_legal": "Resolução SMF 011/2015", "fonte_url": "https://www.fazenda.niteroi.rj.gov.br/site/wp-content/uploads/2016/05/Resolucao-SMF-11-2015.pdf"}],
    ressalvas=["Valores do exercício 2016; atualização anual por nova Resolução SMF — exercício corrente não confirmado"],
    pendencias=["Buscar resolução SMF mais recente (valores 2025/2026)"],
    obs="Tabela sai anualmente por resolução, mesma estrutura de faixas."))

# 6. Mauá-SP — LC 59/2025 Anexo III, exercício 2026, R$/mês por classe
regs.append(mk("Mauá", "completo", "valor_fixo", 2026, {
    "residencial": [F(None,None,21.73,BRL,"Valor fixo mensal por classe (sem faixa de consumo)")],
    "comercial_servicos": [F(None,None,43.73,BRL,"Valor fixo mensal por classe")],
    "industrial": [F(None,None,65.35,BRL,"Valor fixo mensal por classe")],
    "poder_publico": [F(None,None,44.89,BRL,"Valor fixo mensal por classe")],
    "rural": [F(None,None,18.82,BRL,"Valor fixo mensal por classe")],
    "outras_classes": [F(None,None,44.89,BRL,"Demais classes (Enel SP)")],
}, [{"norma": "LC 59/2025 Anexo III", "vigencia": "2025", "fonte_url": "https://dom.maua.sp.gov.br/public/docs/76985da9b8996be2b3db9b2cc9763913.pdf"}],
    [("https://dom.maua.sp.gov.br/public/docs/76985da9b8996be2b3db9b2cc9763913.pdf", "LC 59/2025 Anexo III — Mauá/SP (DOM)", "fonte_oficial")],
    ressalvas=["Valores fixos mensais por classe (não há faixa de consumo); exercício 2026"],
    pendencias=[], obs=""))

# 7. Caruaru-PE — CTM LC 015/2009, % sobre consumo x tarifa
regs.append(mk("Caruaru", "completo", "outro", None, {
    "residencial": [F(None,None,4.00,PB,"Alíquota única sobre consumo x tarifa")],
    "rural": [F(None,None,4.00,PB,"Alíquota única")],
    "comercial": [F(None,None,5.00,PB,"Alíquota única")],
    "servicos": [F(None,None,5.00,PB,"Alíquota única")],
    "industrial": [F(None,None,6.00,PB,"Alíquota única")],
    "poder_publico": [F(None,None,6.00,PB,"Alíquota única")],
}, [{"norma": "LC 015/2009 arts. 478-491 (alterada pelas LC 023/2010 e 043/2013)", "vigencia": "2009", "fonte_url": "https://sapl.caruaru.pe.leg.br/media/sapl/public/normajuridica/2009/2813/014.pdf"}],
    [("https://sapl.caruaru.pe.leg.br/media/sapl/public/normajuridica/2009/2813/014.pdf", "CTM LC 015/2009 — Caruaru/PE (SAPL)", "fonte_oficial")],
    isencoes=[{"tipo": "faixa_consumo", "limite_kwh": 30, "condicao": "Residencial até 30 kWh", "base_legal": "LC 015/2009 art.479", "fonte_url": "https://sapl.caruaru.pe.leg.br/media/sapl/public/normajuridica/2009/2813/014.pdf"},
              {"tipo": "faixa_consumo", "limite_kwh": 80, "condicao": "Rural até 80 kWh", "base_legal": "LC 015/2009 art.479", "fonte_url": "https://sapl.caruaru.pe.leg.br/media/sapl/public/normajuridica/2009/2813/014.pdf"}],
    ressalvas=["Há 2 regimes no texto (rateio e %); Anexo XVII (base 1000 kWh B4A) não consta no PDF acessado"],
    pendencias=["Conferir Anexo XVII do CTM"], obs=""))

# ============ PARCIAIS (9) ============
def parcial(nome, mecanismo, base_legal, fontes, pend, ress=None, obs=None, exerc=None):
    regs.append(mk(nome, "parcial", mecanismo, exerc, None, base_legal, fontes,
                   ressalvas=ress, pendencias=pend, obs=obs))

parcial("Piracicaba", "valor_fixo",
    [{"norma": "CIP instituída em 2026 (leis específicas não identificadas)", "vigencia": "2026", "fonte_url": "https://g1.globo.com/sp/piracicaba-regiao/noticia/2026/04/08/piracicaba-aumenta-taxa-de-iluminacao-publica-a-partir-de-maio-confira-valores.ghtml"}],
    [("https://g1.globo.com/sp/piracicaba-regiao/noticia/2026/04/08/piracicaba-aumenta-taxa-de-iluminacao-publica-a-partir-de-maio-confira-valores.ghtml", "g1 — Piracicaba aumenta taxa de iluminação pública (04/2026)", "noticia")],
    ["Achar a lei/decreto de 2026 com a tabela completa (só faixas residenciais 1-150 kWh noticiadas: 3,06/4,59/7,64)"],
    ress=["Valores de 2026 vêm de notícia; não localizada lei íntegra"],
    exerc=2026)

parcial("Bauru", "outro",
    [{"norma": "Lei 5.075/2003 (CIP) alterada pela Lei 7.152/2018", "vigencia": "2018", "fonte_url": "https://www2.bauru.sp.gov.br/arquivos/sist_juridico/documentos/leis/lei7152.pdf"}],
    [("https://www2.bauru.sp.gov.br/arquivos/sist_juridico/documentos/leis/lei7152.pdf", "Lei 7.152/2018 — Bauru/SP (portal oficial)", "fonte_oficial")],
    ["Extrair tabela de alíquotas do CTM (Lei 5.075/2003) e desconto de 50% residencial 0-100 kWh"],
    ress=["Cálculo por rateio com desconto; valores exatos não extraídos"])

parcial("Maringá", "desconhecido",
    [{"norma": "LC 1.506/2025 Anexo XIX (tabela CCSIP)", "vigencia": "2025", "fonte_url": "https://sapl.cmm.pr.gov.br/norma/15032"}],
    [("https://sapl.cmm.pr.gov.br/norma/15032", "LC 1.506/2025 — Maringá/PR (SAPL)", "fonte_oficial")],
    ["Extrair Anexo XIX (tabela CCSIP) do PDF da norma"])

parcial("Boa Vista", "desconhecido",
    [{"norma": "LC 2/2011 altera CTM LC 1.223/2009 art.177-A", "vigencia": "2011", "fonte_url": "https://www.legisweb.com.br/legislacao/?id=241729"}],
    [("https://www.legisweb.com.br/legislacao/?id=241729", "LC 2/2011 — Boa Vista/RR (legisweb)", "agregador_legislacao")],
    ["Localizar tabela de alíquotas (art.177-A do CTM)"])

parcial("Anápolis", "outro",
    [{"norma": "CTM — cota-padrão por zona fiscal", "vigencia": "2006", "fonte_url": "https://sapl.anapolis.go.leg.br/media/sapl/public/normajuridica/2006/218/218_texto_integral.pdf"}],
    [("https://sapl.anapolis.go.leg.br/media/sapl/public/normajuridica/2006/218/218_texto_integral.pdf", "CTM — Anápolis/GO (SAPL)", "fonte_oficial")],
    ["Extrair valores de cota-padrão por zona fiscal"])

parcial("Betim", "desconhecido",
    [{"norma": "Lei Municipal 8.021/2025 (COSIP)", "vigencia": "2025", "fonte_url": "https://www.mpmg.mp.br/data/files/47/20/CF/19/E36FF91021C3EDF9B9A8F9C2/Betim%20-%20MPe%20n.%2034.16.0024.0367276.2026.92%20-%20Lei%20Municipal%20n.%208.021-2025%20-%20COSIP.pdf"}],
    [("https://www.mpmg.mp.br/data/files/47/20/CF/19/E36FF91021C3EDF9B9A8F9C2/Betim%20-%20MPe%20n.%2034.16.0024.0367276.2026.92%20-%20Lei%20Municipal%20n.%208.021-2025%20-%20COSIP.pdf", "MPMG — Lei 8.021/2025 COSIP (Betim/MG)", "fonte_oficial")],
    ["Extrair tabela de alíquotas da Lei 8.021/2025"])

parcial("Petrolina", "desconhecido",
    [{"norma": "Lei 1.609/2004 alterada pela Lei 3.648/2023", "vigencia": "2023", "fonte_url": "https://petrolina.pe.gov.br/lei-no-3-648-de-12-de-setembro-de-2023/"}],
    [("https://petrolina.pe.gov.br/lei-no-3-648-de-12-de-setembro-de-2023/", "Lei 3.648/2023 — Petrolina/PE (portal oficial)", "fonte_oficial")],
    ["Localizar tabela de alíquotas da CIP"])

parcial("Vitória da Conquista", "desconhecido",
    [{"norma": "COSIP-MU (PL 026/2025, aprovada 11/2025)", "vigencia": "2025", "fonte_url": "https://pmvc.ba.gov.br/apos-entender-que-cosip-mu-nao-representa-novo-tributo-camara-aprova-projeto-de-lei-em-primeira-votacao/"}],
    [("https://pmvc.ba.gov.br/apos-entender-que-cosip-mu-nao-representa-novo-tributo-camara-aprova-projeto-de-lei-em-primeira-votacao/", "Prefeitura de VdC — COSIP-MU (BA)", "noticia")],
    ["Localizar lei final com tabelas (alíquotas 5%-18% por faixa conforme apuração preliminar)"],
    ress=["Fonte é notícia sobre aprovação; texto final da lei não extraído"])

parcial("Caxias do Sul", "desconhecido",
    [{"norma": "PLC 34/2021 (atualiza tabelas COSIP por classe/faixa)", "vigencia": "2021", "fonte_url": "https://www.camaracaxias.rs.gov.br/noticias/index/22791"}],
    [("https://www.camaracaxias.rs.gov.br/noticias/index/22791", "Câmara de Caxias do Sul — PLC 34/2021", "fonte_oficial")],
    ["Extrair tabelas COSIP (descontos baixa renda) do PLC/lei"])

# ============ NÃO ENCONTRADOS (14) ============
for n in ["Campos dos Goytacazes", "Belford Roxo", "São José do Rio Preto", "Ananindeua",
          "Vila Velha", "Mogi das Cruzes", "Jundiaí", "São João de Meriti",
          "Campina Grande", "Santos", "Montes Claros", "Diadema", "Carapicuíba",
          "Itaquaquecetuba"]:
    regs.append(mk(n, "nao_encontrado", "desconhecido", None, None, [], [],
                   pendencias=["Nova coleta — busca por portal da prefeitura/SAPL"]))

# ---- salvar ----
l = len(regs)
assert l == 30, f"esperado 30, veio {l}"
out = f"{BASE}/batches/saida_lote2.json"
json.dump(regs, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"gravação: {out} ({l} registros)")

# ---- validar ----
from jsonschema import Draft7Validator
schema = json.load(open(f"{BASE}/schema.json"))
v = Draft7Validator(schema)
errs = 0
for i, r in enumerate(regs):
    es = list(v.iter_errors(r))
    if es:
        errs += len(es)
        for e in es[:3]:
            print(f"  registro {i} {r['municipio']}: {e.message[:180]}")
from collections import Counter
print("erros:", errs, "| status:", dict(Counter(r["status"] for r in regs)))
print("mecanismos:", dict(Counter(r["mecanismo"] for r in regs)))
sys.exit(1 if errs else 0)
