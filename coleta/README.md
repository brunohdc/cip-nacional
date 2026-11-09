# CIP por município — coleta de dados

## Passo 1: mapa município → distribuidora ✅
Fonte: dados abertos ANEEL (CKAN)
- `indqual-municipio.csv` — 42.699 conjuntos de UC ↔ 5.574 municípios (cód. IBGE)
- `indicadores-continuidade-coletivos-atributos.csv` (72MB) — IdeConjUndConsumidoras → SigAgente (distribuidora)

Join: município → conjunto(s) → SigAgente. Resultado em `municipio_distribuidora.json`.

Stats (`stats.json`):
- 5.574 municípios, 101 rótulos de agente (100 reais + 1 vazio)
- 12 sem match, 541 com >1 distribuidora (normal: rural/área de fronteira)
- ~170 municípios com pelo menos um conjunto de agente vazio — limpar manualmente
- Top: CEMIG-D 779, COELBA 416, COPEL-DIS 398, RGE 286, CELESC 261

Obs.: `www2.aneel.gov.br/aplicacoes/areaConcessao/` está atrás de Cloudflare (403) — usar só dados abertos.

## Passo 2: extração de alíquotas — teste de viabilidade
### Top-down (distribuidoras): FRACO
- CPFL, Cemig, Equatorial AL: página institucional SEM tabela — dizem "cada município define"
- Amazonas Energia: tem valores, mas embutido em **Power BI** (embed público; extraível via API Power BI, mas só cobre AM)
- Conclusão: distribuidoras não são fonte escalável de alíquota

### Bottom-up (lei municipal): FUNCIONA ✅
Testes com busca simples devolveram a lei com tabela de alíquotas:
- Pedra Bela/SP → lei com tabela faixa × % (camara site, download)
- Álvaro de Carvalho/SP → 13% + isentos, texto integral (alvarodecarvalho.sp.gov.br/legislacao)
- Fortaleza/CE → LC 159/2013 + emendas (SAPL câmara, legisweb, notícias)
- Poços de Caldas/MG → Lei 7.742/2002, faixas (site da DME-PC)

Padrões de portal encontrados: SAPL (sapl.*.leg.br), download-lei em câmaras SP, legisweb, PDFs de prefeitura.

## Pipeline proposto (próximo passo)
1. Top 100 municípios por população (IBGE) — prioridade
2. Pra cada um: busca `"alíquota" "iluminação pública" <município> lei` → achar texto da lei
3. Extrair: alíquotas por faixa/classe, nº da lei, data, URL da fonte
4. Registro sem fonte = `status: "não informado"` — NUNCA estimar
5. Output: `cip/<cod_ibge>-<slug>.json` + página gerada `/cip/<uf>/<município>`

## Piloto (top 10 municípios por população) — 01/10/2026 ✅
Dataset: `pilot_top10.json` (10 registros com fonte, base legal, tabelas, data de coleta)

Resultado: **6 completo · 3 parcial · 1 não encontrado**
- ✅ completos: São Paulo (R$ fixos 2026), Rio (fórmula R$+coef×TEIP, Lei 9.049/2025), Fortaleza (% módulo TIP, Sefin), Salvador (% TIP, com ressalva de célula mesclada), Manaus (R$ 2025), Curitiba (% TEIP)
- ⚠️ parciais: Brasília (falta decreto anual com valores atuais), Recife (falta tabela de alíquotas), Goiânia (falta Planilha de Custos)
- ❌ não encontrado: Belo Horizonte (3 rodadas; existe COSIP, portal não indexou a lei)

Achados de padrão (importante pra automatizar):
- 4 formatos de mecanismo: % × módulo TIP (Fortaleza, Salvador), % × TEIP (Curitiba), fórmula R$+coef×TEIP (Rio), R$ fixo por faixa (SP, Manaus, DF)
- Decretos/portarias ANUAIS mudam valores (SP, Manaus, DF) → cron de re-checagem obrigatório
- legisweb.com.br indexa bem leis municipais — bom ponto de partida nas buscas
- Fontes oficiais melhores quando existem: Sefin Fortaleza, prefeitura SP (Portaria SF)
- Busca genérica erra muito; query com nome do município + "COSIP/alíquota/faixas" funciona melhor
- Firecrawl (credencial) sem saldo — usando backend keyless; considerar scraper dedicado (SerpAPI/Firecrawl) pra escala

## Escalação — top 100 (concluída em 01/10/2026)
- Top 100 por população (Censo 2022, IBGE agregado 4709) → `cip_top100.json` (100 registros, 0 erros de schema)
- Execução: piloto (10) + 3 lotes de 30 via subagentes (mimo/deepseek-flash), depois consolidação manual dos lotes 2 e 3 (agentes esgotaram iterações antes de gravar — dados recuperados dos resumos e re-extraídos quando faltava tabela)
- **Resultado: 25 completos · 45 parciais · 30 não encontrados** (70% com alguma informação, 542 faixas parseadas)
- Mecanismos: 18 valor_fixo · 15 outro (% sobre base/tarifa) · 6 %TEIP · 2 %módulo TIP · 1 fórmula TEIP · 58 desconhecido
- Aprendizados: legisweb/lefisc indexam bem; portais alguns municípios dão 403 (Cloudflare); backend de busca keyless é ruidoso — DuckDuckGo html funciona como fallback; PDFs de CTM grandes exigem pypdf + grep por artigo
- Uniidade nova no schema: `PERCENTUAL_BASE` (% sobre base de rateio/tarifa — não TIP/TEIP)

## Arrecadação oficial (nova página)
- Fonte: **SICONFI/DCA** (Tesouro Nacional) — conta `1.2.4.0.00.0.0 – Contribuição para o Custeio do Serviço de Iluminação Pública`, linha "Receitas Brutas Realizadas" (Anexo I-C)
- Coleta: `coleta_arrecadacao.py` → `arrecadacao_cip.json` (100 municípios × 2022–2025, gravação incremental, `anexo` param é ignorado pela API)
- Resultado: 49 com 4 anos · 44 parciais · 7 sem dado (Barueri, Carapicuíba, Franca, Limeira, Piracicaba, Sorocaba, Brasília-DF)
- Soma acumulada dos 100: **R$ 21,95 bi** · top: São Paulo R$ 2,20 bi, Rio R$ 1,41 bi, Manaus R$ 1,00 bi
- Página: `/arrecadacao/` (ranking + total acumulado + R$/hab + FAQ + JSON-LD Dataset) e bloco "Arrecadação oficial da CIP" em cada página de município

## Expansão top 500 + filtro por estado (concluída em 02/10/2026)
- Base ampliada de 100 → **500 municípios** pelo ranking de população do Censo 2022/IBGE (`cip_top500.json`); 500 páginas municipais geradas (419 novas páginas começam como `não informado`, sem inventar alíquota)
- Arrecadação SICONFI/DCA 2022–2025 coletada para os 500: **235 com os 4 exercícios · 245 parciais · 20 sem dado**; 480 municípios têm pelo menos um valor; soma acumulada atual: **R$ 35,58 bi**
- `/arrecadacao/` agora tem **filtro client-side por UF**, sem recarregar a página; 26 estados aparecem com dados
- Dataset de alíquotas permanece disciplinado: os 37 completos anteriores + placeholders transparentes para os municípios novos; expansão legal será rodada própria

## Pendências
- [x] Rodada 2 nos 45 parciais + 30 não (concluída 01/10/2026 → 37 completos, 44 parciais, 19 não)
- [x] Londrina completada via Obsidian + fonte câmara (UVC R$73,83)
- [ ] Download manual dos links bloqueados por Cloudflare → ver `links_download_manual.md` (34 links 403 + 63 pendências)
- [x] Decidir gate de URL → `/cip/<uf>/<slug>` (DECISOES.md)
- [ ] Cron mensal de re-checagem → criado `9fd8876ba9e8` (dia 1, 12h UTC; proxima_revisao 2026-10-31)
- [x] Render + publicação → https://brunohdc.github.io/cip-nacional/ (GitHub Pages, push automático)

## Modelo padronizado de cobrança (piloto)
- Cada registro novo declara `tipo: "fixa"` (R$/mês) ou `tipo: "percentual"` (%).
- Registro percentual precisa de `base_calculo` com `valor`, `descricao`, `exercicio` e `fonte_url`.
- `coleta/pilot_cobranca.json` traz São Paulo (fixo, 2026) e Londrina (percentual sobre UVC de R$ 73,83 em set/2025).
- `CIP_DATA` aponta para o conjunto piloto; nesse modo o gerador publica apenas as páginas municipais. Use `CIP_ONLY=0` para gerar o site completo.

```bash
CIP_DATA=coleta/pilot_cobranca.json CIP_SITE=/tmp/cip-pilot python3 coleta/render_site.py
python3 -m unittest coleta.test_cobranca
```

No PowerShell:

```powershell
$env:CIP_DATA="coleta/pilot_cobranca.json"; $env:CIP_SITE="$env:TEMP\cip-pilot"; python coleta/render_site.py
```

Registros antigos sem `tipo` continuam no caminho legado, usando apenas `unidade`.

## Como reproduzir (scripts versionados neste diretório)

Layout esperado: os dados brutos ficam em `CIP_BASE` (default `~/workspace/cip_collected`) e o
site gerado em `CIP_SITE` (default `~/workspace/cip_site`). Ambos são sobrescrevíveis por env var.

```bash
export CIP_BASE=~/workspace/cip_collected
export CIP_SITE=~/workspace/cip_site

python3 coleta_arrecadacao.py     # SICONFI/DCA -> $CIP_BASE/arrecadacao_cip.json (incremental)
python3 render_site.py            # $CIP_BASE/cip_top500.json -> $CIP_SITE/*.html
```

Verificação anti-fabricação (recheck): `recheck_2026-11/fetch.py` baixa as fontes para
`recheck_2026-11/cache/` (fora do git) e `verify*.py` conferem cada valor publicado contra o
texto do documento de origem. Requer `requests`, `pypdf` (`pip install requests pypdf`).
`batches/build_lote*.py` montam os lotes de coleta de alíquotas a partir de `batches/lote*.json`.

Regra de dados: valor ausente na fonte = `null` + `status` explícito; nada é estimado.

