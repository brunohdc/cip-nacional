#!/usr/bin/env python3
"""Monta batches/saida_lote3.json (30 registros) a partir dos dados coletados."""
import json, os, sys, unicodedata

BASE = os.environ.get("CIP_BASE", os.path.expanduser("~/workspace/cip_collected"))
DATA = "2026-10-01"
lotes = {l["cod"]: l for l in json.load(open(f"{BASE}/batches/lote3.json"))}
dist_list = json.load(open(f"{BASE}/municipio_distribuidora.json"))
dist_map = {d["cod_ibge"]: d["distribuidoras"] for d in dist_list}

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

BRL, PB, PT = "BRL", "PERCENTUAL_BASE", "PERCENTUAL_TEIP"

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
    return {
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

regs = []

# ============ COMPLETOS (6) ============

# 1. Vitória-ES — Lei 5.815/2002, % sobre tarifa
regs.append(mk("Vitoria", "completo", "outro", 2002, {
    "residencial_a": [F(None,1000,26.69,PB,"Grupo A (Alta Tensão)"), F(1001,5000,50.18,PB), F(5000,None,74.73,PB)],
    "residencial_b": [F(None,50,"isento",PB,"Grupo B isento até 50 kWh"), F(51,70,2.12,PB),
                      F(71,100,3.17,PB), F(101,150,4.54,PB), F(151,200,6.65,PB), F(201,300,8.14,PB),
                      F(301,400,10.96,PB), F(401,500,12.92,PB), F(500,None,14.53,PB)],
    "nao_residencial_a": [F(None,1000,74.73,PB,"Demais classes grupo A"), F(1001,5000,99.28,PB), F(5000,None,199.63,PB)],
    "nao_residencial_b": [F(None,30,2.85,PB,"Demais classes grupo B"), F(31,50,3.40,PB), F(51,70,5.65,PB),
                          F(71,100,6.65,PB), F(101,150,8.14,PB), F(151,200,10.96,PB), F(201,300,12.92,PB),
                          F(301,400,14.53,PB), F(401,500,15.89,PB), F(500,None,18.00,PB)],
}, [{"norma": "Lei 5.815/2002 Anexos I/II", "vigencia": "2002", "fonte_url": "https://camarasempapel.cmv.es.gov.br/Arquivo/Documents/legislacao/html/L58152002.html"}],
    [("https://camarasempapel.cmv.es.gov.br/Arquivo/Documents/legislacao/html/L58152002.html", "Lei 5.815/2002 — Vitória/ES (câmara sem papel)", "agregador_legislacao")],
    isencoes=[{"tipo": "faixa_consumo", "limite_kwh": 50, "condicao": "Residencial grupo B até 50 kWh", "base_legal": "Lei 5.815/2002", "fonte_url": "https://camarasempapel.cmv.es.gov.br/Arquivo/Documents/legislacao/html/L58152002.html"}],
    ressalvas=["Lei de 2002 — conferir alterações posteriores; percentuais sobre a tarifa (não TIP/TEIP)"],
    pendencias=["Conferir vigência/alterações da Lei 5.815/2002"],
    obs="Grupo A = alta tensão (consumo alto); Grupo B = baixa tensão."))

# 2. Taubaté-SP — LC 358/2014, % sobre consumo
regs.append(mk("Taubate", "completo", "outro", 2014, {
    "residencial": [F(None,200,4.00,PB,"Baixa renda isento"), F(201,500,5.00,PB), F(501,1000,6.00,PB),
                    F(1001,10000,7.50,PB), F(10000,None,10.00,PB)],
}, [{"norma": "LC 358/2014 (Anexo Único)", "vigencia": "2014", "fonte_url": "https://www.taubate.sp.gov.br/anexos/leis/2014/358%20CONTRIBUICAO%20PARA%20CUSTEIO%20SERVICO%20ILUMINACAO%20PUBLICA.pdf"}],
    [("https://www.taubate.sp.gov.br/anexos/leis/2014/358%20CONTRIBUICAO%20PARA%20CUSTEIO%20SERVICO%20ILUMINACAO%20PUBLICA.pdf", "LC 358/2014 — Taubaté/SP (PDF oficial)", "fonte_oficial")],
    isencoes=[{"tipo": "outras_condicoes", "condicao": "Baixa renda isento", "base_legal": "LC 358/2014", "fonte_url": "https://www.taubate.sp.gov.br/anexos/leis/2014/358%20CONTRIBUICAO%20PARA%20CUSTEIO%20SERVICO%20ILUMINACAO%20PUBLICA.pdf"}],
    ressalvas=["Transcrita apenas a tabela residencial; o PDF contém tabelas de comercial/industrial/poder público/rural e lotes (R$/m²)"],
    pendencias=["Transcrever demais tabelas do anexo"], obs=""))

# 3. Pelotas-RS — COSIP 2019, % sobre TEIP
regs.append(mk("Pelotas", "completo", "percentual_teip", 2019, {
    "residencial": [F(None,30,"isento",PT), F(31,100,1.80,PT), F(101,150,3.10,PT), F(151,200,4.40,PT),
                    F(201,250,5.60,PT), F(251,500,7.90,PT), F(501,2400,15.80,PT), F(2400,None,78.30,PT)],
    "comercial": [F(None,30,"isento",PT), F(31,100,3.60,PT), F(101,150,6.30,PT), F(151,200,8.90,PT),
                  F(201,250,11.40,PT), F(251,500,17.80,PT), F(501,6000,53.10,PT), F(6000,None,508.80,PT)],
}, [{"norma": "Lei COSIP 2019 (Mensagem 042/2019)", "vigencia": "2019", "fonte_url": "https://pelotas.com.br/storage/iluminacao/ContribuicaoIluminacaoPublica.pdf"}],
    [("https://pelotas.com.br/storage/iluminacao/ContribuicaoIluminacaoPublica.pdf", "COSIP Pelotas/RS (PDF prefeitura)", "fonte_oficial")],
    isencoes=[{"tipo": "faixa_consumo", "limite_kwh": 30, "condicao": "Até 30 kWh isento (residencial e comercial)", "base_legal": "Lei COSIP 2019", "fonte_url": "https://pelotas.com.br/storage/iluminacao/ContribuicaoIluminacaoPublica.pdf"}],
    ressalvas=["Número da lei sancionada não identificado no PDF (só Mensagem 042/2019); industrial/poder público têm % próprios não transcritos"],
    pendencias=["Identificar número/ano da lei", "Transcrever tabelas industrial e poder público"], obs=""))

# 4. Palmas-TO — LC 102/2005, valor fixo
regs.append(mk("Palmas", "completo", "valor_fixo", 2005, {
    "residencial": [F(None,50,"isento",BRL), F(51,100,2.95,BRL), F(101,150,5.80,BRL), F(151,200,8.85,BRL),
                    F(201,300,10.40,BRL), F(301,400,12.70,BRL), F(401,500,15.85,BRL), F(501,1000,19.60,BRL),
                    F(1001,1500,22.75,BRL), F(1501,2000,29.70,BRL), F(2000,None,38.60,BRL)],
    "nao_residencial": [F(None,50,"isento",BRL), F(51,100,5.95,BRL), F(101,150,7.80,BRL), F(151,200,9.70,BRL),
                        F(201,300,11.90,BRL), F(301,400,13.80,BRL), F(401,500,17.60,BRL), F(501,1000,21.75,BRL),
                        F(1001,1500,28.40,BRL), F(1501,2000,39.90,BRL), F(2000,None,59.80,BRL)],
}, [{"norma": "LC 102/2005", "vigencia": "2005", "fonte_url": "https://legislativo.palmas.to.gov.br/media/leis/lei-complementar-102-2005.pdf"}],
    [("https://legislativo.palmas.to.gov.br/media/leis/lei-complementar-102-2005.pdf", "LC 102/2005 — Palmas/TO (PDF legislativo)", "fonte_oficial")],
    isencoes=[{"tipo": "faixa_consumo", "limite_kwh": 50, "condicao": "Até 50 kWh isento (residencial e não residencial)", "base_legal": "LC 102/2005", "fonte_url": "https://legislativo.palmas.to.gov.br/media/leis/lei-complementar-102-2005.pdf"}],
    ressalvas=["URL do PDF montada no padrão do portal (leis seguem legislativo.palmas.to.gov.br/media/leis/...) — conferir nome exato do arquivo"],
    pendencias=["Confirmar URL exata do PDF da LC 102/2005"], obs=""))

# 5. Suzano-SP — LC 262/2014
regs.append(mk("Suzano", "completo", "outro", 2014, {
    "residencial": [F(None,None,3.00,PB,"Alíquota única (redação consolidada)")],
    "nao_residencial": [F(None,None,3.00,PB,"Alíquota única (redação consolidada)")],
    "nao_edificado": [F(None,None,4.2787,PB,"4,2787 UF por metro linear de testada")],
}, [{"norma": "LC 262/2014 (alterada pelas LC 270/2015 e 297/2017)", "vigencia": "2014", "fonte_url": "https://suzano.sp.gov.br/wp-content/uploads/2018/11/262-14-Contribuicao-de-Iluminacao-Publica-CIP.pdf"}],
    [("https://suzano.sp.gov.br/wp-content/uploads/2018/11/262-14-Contribuicao-de-Iluminacao-Publica-CIP.pdf", "LC 262/2014 — Suzano/SP (PDF oficial)", "fonte_oficial")],
    isencoes=[{"tipo": "outras_condicoes", "condicao": "Conectados à tarifa social isentos", "base_legal": "LC 262/2014", "fonte_url": "https://suzano.sp.gov.br/wp-content/uploads/2018/11/262-14-Contribuicao-de-Iluminacao-Publica-CIP.pdf"}],
    ressalvas=["Redação consolidada: 3% residencial e não residencial (texto original citava 6% não residencial)"],
    pendencias=[], obs=""))

# 6. Cascavel-PR — Lei 6.572/2015, valor fixo (UVC)
regs.append(mk("Cascavel", "completo", "valor_fixo", 2015, {
    "residencial": [F(None,100,0.00,BRL), F(101,150,9.35,BRL), F(151,200,12.47,BRL), F(201,250,18.70,BRL),
                    F(251,300,24.94,BRL), F(301,350,31.17,BRL), F(351,500,37.41,BRL), F(501,700,43.64,BRL),
                    F(701,1000,49.88,BRL), F(1000,None,62.35,BRL,"UVC = R$ 62,35")],
}, [{"norma": "Lei 6.572/2015 (tabela residencial; ver também LC 8/2002, LC 48/2007, Lei 5.318/2009)", "vigencia": "2015", "fonte_url": "https://sapl.cascavel.pr.leg.br/media/sapl/public/materialegislativa/2015/8271/8271_texto_integral.pdf"}],
    [("https://sapl.cascavel.pr.leg.br/media/sapl/public/materialegislativa/2015/8271/8271_texto_integral.pdf", "Lei 6.572/2015 — Cascavel/PR (SAPL)", "fonte_oficial")],
    ressalvas=["Arquivo acessado é o anteprojeto/lei de 2015 — conferir sanção e alterações; tabelas comercial/industrial/poder público não transcritas", "Valores em R$ fixos indexados à UVC (R$ 62,35 no documento)"],
    pendencias=["Conferir vigência e tabelas demais classes", "Verificar UVC corrente"], obs=""))

# ============ PARCIAIS (22) ============
def parcial(nome, mecanismo, base_legal, fontes, pend, ress=None, obs=None, exerc=None, isenc=None):
    regs.append(mk(nome, "parcial", mecanismo, exerc, None, base_legal, fontes,
                   isencoes=isenc, ressalvas=ress, pendencias=pend, obs=obs))

parcial("Blumenau", "desconhecido",
    [{"norma": "Lei 13.479/2002 alterada pela Lei 17.719/2021 (valores 2026 por Portaria SF 330/2025)", "vigencia": "2021", "fonte_url": "https://www.blumenau.sc.gov.br/governo/secretaria-de-gestao-financeira/pagina/codigo-tributario-sefaz"}],
    [("https://www.blumenau.sc.gov.br/governo/secretaria-de-gestao-financeira/pagina/codigo-tributario-sefaz", "Sefaz Blumenau/SC — código tributário (link 'Tabela Cosip 2026')", "fonte_oficial")],
    ["Baixar a 'Tabela Cosip 2026' linkada na página da Sefaz"],
    obs="Portaria SF 330/2025 traz valores 2026 (conforme sinesp.org.br).")

parcial("Ponta Grossa", "desconhecido",
    [{"norma": "Lei 7.094/2002; reforma Lei 16.017/2026; reajuste Decreto 26.122/2025", "vigencia": "2026", "fonte_url": "https://pontagrossa.pr.gov.br/iluminacao-publica/"}],
    [("https://pontagrossa.pr.gov.br/iluminacao-publica/", "Ponta Grossa/PR — iluminação pública (portal oficial)", "fonte_oficial")],
    ["Extrair tabela vigente da página oficial (Lei 16.017/2026 em vigor)"])

parcial("Caucaia", "desconhecido",
    [{"norma": "LC 23/2002 alterada pela LC 156/2025", "vigencia": "2025", "fonte_url": "https://leis.org/municipais/ce/caucaia/"}],
    [("https://leis.org/municipais/ce/caucaia/", "Caucaia/CE — leis municipais (leis.org)", "agregador_legislacao")],
    ["Extrair tabela da LC 156/2025"])

parcial("Praia Grande", "desconhecido",
    [{"norma": "LC 465/2006 alterada pela LC 1007/2024", "vigencia": "2024", "fonte_url": "https://www.praiagrande.sp.gov.br/Administracao/leisdecretos_view.asp?codLeis=2571"}],
    [("https://www.praiagrande.sp.gov.br/Administracao/leisdecretos_view.asp?codLeis=2571", "Praia Grande/SP — consulta de leis", "fonte_oficial")],
    ["Extrair tabela de alíquotas vigente"])

parcial("Uberaba", "desconhecido",
    [{"norma": "Lei 10.710 (valores fixados por regulamento/decreto de lançamento anual)", "vigencia": "s/d", "fonte_url": "https://servico.uberaba.mg.gov.br/tributos/leis_dec/LEI10710.pdf"}],
    [("https://servico.uberaba.mg.gov.br/tributos/leis_dec/LEI10710.pdf", "Lei 10.710 — Uberaba/MG (PDF oficial)", "fonte_oficial")],
    ["Localizar decreto/regulamento de lançamento corrente com os valores"])

parcial("Camacari", "desconhecido",
    [{"norma": "Lei 1.366/2014 (altera Tabela de COSIP do CTM — Lei 1.039/2009)", "vigencia": "2014", "fonte_url": "https://sefaz.camacari.ba.gov.br/legislacao/"}],
    [("https://sefaz.camacari.ba.gov.br/legislacao/", "Sefaz Camaçari/BA — legislação", "fonte_oficial")],
    ["Extrair tabela de COSIP da Lei 1.366/2014"])

parcial("Petropolis", "outro",
    [{"norma": "Lei 5.951/2002 (Anexos I/II) alterada pelas Leis 6.214/2004 e 8.906/2024", "vigencia": "2024", "fonte_url": "https://petropolis.processolegislativo.com.br/areapublica/documento/?Lei/1621"}],
    [("https://petropolis.processolegislativo.com.br/areapublica/documento/?Lei/1621", "Lei — Petrópolis/RJ (processo legislativo)", "fonte_oficial")],
    ["Extrair percentuais dos Anexos I/II vigentes"],
    obs="CIP = percentuais fixos sobre a tarifa básica.")

parcial("Juazeiro do Norte", "outro",
    [{"norma": "Lei 2.722/2002 alterada pela Lei 2.776/2003 (base = tarifa B4b R$/MWh)", "vigencia": "2003", "fonte_url": "https://juazeiro1.websiteseguro.com/site/midia/9158/"}],
    [("https://juazeiro1.websiteseguro.com/site/midia/9158/", "Lei 2.722/2003 — Juazeiro do Norte/CE", "fonte_oficial")],
    ["Obter Anexo I (tabela de %) — ausente no PDF acessado"],
    obs="Base de cálculo: tarifa B4b em R$/MWh; Anexo I com percentuais.")

parcial("Guaruja", "valor_fixo",
    [{"norma": "LC 67/2002 (valores R$ fixos atualizados a partir de 03/2018)", "vigencia": "2018", "fonte_url": "https://camaraguaruja.sp.gov.br/Arquivos/Downloads/2017128_pcosip.pdf"}],
    [("https://camaraguaruja.sp.gov.br/Arquivos/Downloads/2017128_pcosip.pdf", "LC 67/2002 — Guarujá/SP (Câmara)", "fonte_oficial")],
    ["Confirmar tabela corrente de valores"],
    obs="Valores apurados: baixa renda/residencial/comércio R$ 2,25/9,00/22,50 a partir de 03/2018 (conferir).")

parcial("Sao Vicente", "valor_fixo",
    [{"norma": "Decreto 6.635/2024 (fixa valores da COSIP)", "vigencia": "2024", "fonte_url": "https://leis.org/municipais/sp/sao-vicente/lei/decreto/2024/6635/"}],
    [("https://leis.org/municipais/sp/sao-vicente/lei/decreto/2024/6635/", "Decreto 6.635/2024 — São Vicente/SP (leis.org)", "agregador_legislacao")],
    ["Extrair valores do decreto (portal leis.org deu 403 no acesso direto)"],
    obs="Também há Decretos 6.284/2023 e anteriores fixando valores.")

parcial("Canoas", "desconhecido",
    [{"norma": "Lei 6.838/2025 (altera arts. 85-A a 85-C do CTM)", "vigencia": "2025", "fonte_url": "https://canoas.rs.gov.br/servicos/legislacao-tributaria-municipal-2/"}],
    [("https://canoas.rs.gov.br/servicos/legislacao-tributaria-municipal-2/", "Canoas/RS — legislação tributária", "fonte_oficial")],
    ["Extrair alíquotas dos arts. 85-A a 85-C"])

parcial("Barueri", "valor_fixo",
    [{"norma": "LC 380/2016 com valores do Decreto 10.102/2024", "vigencia": "2024", "fonte_url": "https://barueri.sp.gov.br/Transparencia/legislacao.aspx"}],
    [("https://barueri.sp.gov.br/Transparencia/legislacao.aspx", "Barueri/SP — legislação (transparência)", "fonte_oficial")],
    ["Extrair tabela de valores do Decreto 10.102/2024"])

parcial("Ribeirao das Neves", "valor_fixo",
    [{"norma": "Decreto 243/2023 (valor por metro linear)", "vigencia": "2023", "fonte_url": "https://leismunicipais.com.br/"}],
    [("https://leismunicipais.com.br/", "Leis Municipais — Ribeirão das Neves/MG", "agregador_legislacao")],
    ["Obter texto do Decreto 243/2023 (portal 403)"],
    obs="CIP por metro linear de testada.")

parcial("Sao Jose dos Pinhais", "desconhecido",
    [{"norma": "Lei 383/2002", "vigencia": "2002", "fonte_url": "https://leismunicipais.com.br/"}],
    [("https://leismunicipais.com.br/", "Leis Municipais — São José dos Pinhais/PR", "agregador_legislacao")],
    ["Obter texto da Lei 383/2002 (portais deram 403)"])

parcial("Varzea Grande", "desconhecido",
    [{"norma": "Lei 2.527/2002", "vigencia": "2002", "fonte_url": "https://www.varzeagrande.mt.gov.br/"}],
    [("https://www.varzeagrande.mt.gov.br/", "Várzea Grande/MT — portal oficial", "fonte_oficial")],
    ["Localizar Lei 2.527/2002 e tabela de alíquotas"])

parcial("Cotia", "desconhecido",
    [{"norma": "Lei 1.745/2012", "vigencia": "2012", "fonte_url": "https://leismunicipais.com.br/"}],
    [("https://leismunicipais.com.br/", "Leis Municipais — Cotia/SP", "agregador_legislacao")],
    ["Obter texto da Lei 1.745/2012 (portal 403)"])

parcial("Sumare", "desconhecido",
    [{"norma": "Lei 7.278/2024 / LC 399/2024", "vigencia": "2024", "fonte_url": "https://legislacaodigital.com.br/"}],
    [("https://legislacaodigital.com.br/", "Legislação Digital — Sumaré/SP", "agregador_legislacao")],
    ["Obter texto da LC 399/2024 (portal 403)"])

parcial("Limeira", "desconhecido",
    [{"norma": "CTM municipal — artigo da CIP a localizar", "vigencia": "2026", "fonte_url": "https://limeira.sp.gov.br/secretarias/fazenda/codigo-tributario-municipal"}],
    [("https://limeira.sp.gov.br/secretarias/fazenda/codigo-tributario-municipal", "Limeira/SP — CTM (PDFs 2026)", "fonte_oficial")],
    ["Baixar PDFs do CTM 2026 e localizar artigo da CIP"])

parcial("Santarem", "desconhecido", [],
    [("https://transparencia.santarem.pa.gov.br/", "Santarém/PA — transparência (receita/despesa CIP)", "fonte_oficial")],
    ["Localizar lei/tabela da CIP — só há dados de arrecadação"],
    ress=["Sem lei nem tabela localizados"])

parcial("Olinda", "desconhecido",
    [{"norma": "PL 129/2022 (projeto — não enactado localizado)", "vigencia": "2022", "fonte_url": "https://www.olinda.pe.leg.br/institucional/projeto-de-lei/projetos-de-lei-2022/pl-129-2022-autor-poder-executivo.pdf"}],
    [("https://www.olinda.pe.leg.br/institucional/projeto-de-lei/projetos-de-lei-2022/pl-129-2022-autor-poder-executivo.pdf", "PL 129/2022 — Olinda/PE (Câmara)", "fonte_oficial")],
    ["Ver se o PL 129/2022 foi sancionado; localizar lei vigente + tabela"])

parcial("Cariacica", "outro",
    [{"norma": "Lei 3.908/2001 Anexo Único (possivelmente revogada pelo CTM LC 27/2009 art. 312-A, alt. LC 122/2022)", "vigencia": "2001", "fonte_url": "https://cariacica.camarasempapel.com.br/Arquivo/Documents/legislacao/html/L39082001.html"}],
    [("https://cariacica.camarasempapel.com.br/Arquivo/Documents/legislacao/html/L39082001.html", "Lei 3.908/2001 — Cariacica/ES (câmara sem papel)", "agregador_legislacao"),
     ("https://cariacica.camarasempapel.com.br/legislacao/norma.aspx?id=15075", "Norma 15075 — Cariacica/ES (câmara sem papel)", "agregador_legislacao")],
    ["Confirmar se o vigente é o CTM LC 27/2009 art. 312-A", "Completar faixas acima de 300 kWh"],
    ress=["Tabela da Lei 3.908/2001 parcialmente transcrita: res. 0-30=2,55% / 31-50=2,91% / 51-70=4,11% / 71-100=4,73% / 101-150=5,78% / 151-200=12,35% / 201-300=15,16% (sobre tarifa B4a)"],
    obs="Percentuais sobre tarifa B4a segundo a Lei 3.908/2001.")

parcial("Foz do Iguacu", "desconhecido",
    [{"norma": "CTM art.617 (COSIP dos imóveis ligados definida na concessionária); Edital TCL/COSIP 2025", "vigencia": "2025", "fonte_url": "https://foz.pr.gov.br/wp-content/uploads/2025/09/EDITAL-DE-LANCAMENTO-TCL-E-COSIP-2025.pdf"}],
    [("https://foz.pr.gov.br/wp-content/uploads/2025/09/EDITAL-DE-LANCAMENTO-TCL-E-COSIP-2025.pdf", "Edital TCL/COSIP 2025 — Foz do Iguaçu/PR (PDF oficial)", "fonte_oficial")],
    ["Tabela de consumo para imóveis LIGADOS à rede fica na concessionária (art.617 CTM) — obter da Copel"],
    obs="Edital 2025 (imóveis SEM ligação regular): UVC R$ 188,43; Região A=26%, B=36%, C=48%, rural=0%.")

# ============ NÃO ENCONTRADOS (2) ============
regs.append(mk("Franca", "nao_encontrado", "desconhecido", None, None, [], [],
               pendencias=["CTM não contém COSIP; lei específica não localizada em 3 rodadas — nova coleta"]))
regs.append(mk("Paulista", "nao_encontrado", "desconhecido", None, None, [],
    [("https://transparencia.paulista.pe.leg.br/uploads/5311/2/atos-oficiais/2025/leis/1772477016_54752025.pdf", "Lei 5.475/2025 — Paulista/PE (PDF digitalizado)", "fonte_oficial")],
    ressalvas=["Tabela não extraída (PDF image)"],
    pendencias=["Lei 5.475/2025 existe mas o PDF é digitalizado sem texto extraível — fazer OCR"]))

# ---- salvar ----
assert len(regs) == 30, f"esperado 30, veio {len(regs)}"
out = f"{BASE}/batches/saida_lote3.json"
json.dump(regs, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"gravação: {out} ({len(regs)} registros)")

from jsonschema import Draft7Validator
from collections import Counter
schema = json.load(open(f"{BASE}/schema.json"))
v = Draft7Validator(schema)
errs = 0
for i, r in enumerate(regs):
    for e in list(v.iter_errors(r))[:3]:
        errs += 1
        print(f"  registro {i} {r['municipio']}: {e.message[:160]}")
print("erros:", errs, "| status:", dict(Counter(r["status"] for r in regs)))
print("mecanismos:", dict(Counter(r["mecanismo"] for r in regs)))
sys.exit(1 if errs else 0)
