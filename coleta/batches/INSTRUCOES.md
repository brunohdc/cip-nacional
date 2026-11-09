# Instruções — coleta CIP (lote)

Você é um coletor de dados. Para CADA município do seu lote JSON, produza um
registro de alíquota de CIP (Contribuição de Iluminação Pública) conforme o
schema, SEM NUNCA inventar dado.

## Arquivos
- Seu lote: `batches/loteN.json` → [{cod, nome ("Porto Alegre - RS"), pop}, ...]
- Schema: `schema.json` (JSON Schema draft-07 — OBRIGATÓRIO)
- Exemplo validado: `pilot_top10.v2.json` (10 registros — siga o formato EXATO)
- Mapa município→distribuidora: `municipio_distribuidora.json` (lookup por cod_ibge)
- Seu output: `batches/saida_loteN.json` → array de registros

## Workflow por município (máx. ~3 rodadas de busca + 3 extrações)
1. `web_search` com queries nesta ordem (pare quando achar):
   - `"{Nome}" COSIP alíquota faixas kWh lei iluminação pública`
   - `legisweb "{Nome}" contribuição iluminação pública alíquota tabela`
   - `"{Nome}" "iluminação pública" valor faixa kWh decreto prefeitura`
2. `web_extract` nas URLs com cara de ter a TABELA (lei, decreto, portaria,
   página de secretaria de fazenda). Prioridade: fonte oficial da prefeitura >
   legisweb/lefisc (agregador) > notícia (só se citar a tabela inteira).
3. Extraia: mecanismo, faixas (kWh → valor), isenções, base legal (nº da lei),
   URL da fonte.
4. Achei tabela vigente → `status: "completo"`. Achei só base legal/lei antiga →
   `parcial` + `pendencias: ["o que falta"]`. 3 buscas sem nada →
   `nao_encontrado` (fontes=[]).

## Regras anti-fabricação (CRÍTICO)
- Número só se estiver visível na fonte com URL que você acessou.
- Não achou valor da faixa → `"n/d"` (string) + nota. NUNCA estimar/linearizar.
- Notícia sem a tabela não serve de fonte de valor (serve de `pendencias`).
- `ressalvas`: registre qualquer dúvida (ex.: "tabela em PDF com layout quebrado").
- Data de hoje: 2026-10-01 → `atualizado_em: "2026-10-01"`, `proxima_revisao: "2026-10-31"`, `data_coleta: "2026-10-01"`.

## Campos obrigatórios (veja schema + exemplo)
- `slug`: minúsculo ascii sem acento, hífens (`porto-alegre`)
- `mecanismo`: enum do schema. Corresponder: "% do módulo da TIP"→
  `percentual_modulo_tip`; "% da TEIP"→`percentual_teip`;
  "R$ fixo + coef × TEIP"→`formula_teip`; "R$ por faixa"→`valor_fixo`;
  outra coisa→`outro`; não descobriu→`desconhecido`
- `tabelas`: {"residencial": [{faixa_kwh:{min,max}, valor(number|"isento"|"n/d"),
  unidade, formula?}], "nao_residencial": [...]}
  - `unidade`: BRL (R$ fixo) | PERCENTUAL_MODULO_TIP | PERCENTUAL_TEIP | FORMULA_TEIP
  - Linhas "isento"/"n/d" TAMBÉM levam `unidade` (a unidade padrão da tabela)
  - Faixa aberta: max=null ("acima de X") ou min=0 ("até X")
- `base_legal`: [{norma, vigencia, fonte_url}] (só nº/ano — "Lei 12.345/2018")
- `fontes`: [{url, titulo, tipo, data_coleta}] — tipo: fonte_oficial |
  agregador_legislacao | noticia | outro
- `distribuidoras`: lookup no mapa ANEEL (array de siglas)
- `exercicio`: ano DOS VALORES da tabela (não da lei). Null se não souber.

## Validação (obrigatória antes de terminar)
```python
import json
from jsonschema import Draft7Validator
schema = json.load(open(".../schema.json"))       # caminho absoluto
saida = json.load(open(".../batches/saida_loteN.json"))
v = Draft7Validator(schema)
erros = [(r["municipio"], "/".join(map(str, e.path)), e.message)
         for r in saida for e in v.iter_errors(r)]
print(len(saida), "registros |", len(erros), "erros")
```
Corrija até 0 erros. Confira também: nenhum registro sem `fontes` (exceto
nao_encontrado), nenhum `completo` sem `tabelas`.

## Eficiência
- Não tente esgotar cada município: se 2-3 buscas não acharem, siga em frente.
- `web_extract` aceita até 5 URLs por chamada — agrupe.
- Objetivo: 30 registros entregues, validados, honestos (parcial/não encontrado
  é resultado VÁLIDO — fraude não é).

# RODADA 2 — instruções adicionais (lotes 4/5/6)
Cada item do lote JSON já é um registro ANTERIOR com status parcial ou
nao_encontrado. Objetivo: completar, mantendo o que já foi apurado.

1. Comece pelas `pendencias` do registro (elas dizem exatamente o que falta:
   "baixar tabela X", "OCR do PDF Y", "artigo Z do CTM").
2. Mantenha `base_legal` e `fontes` já coletados (pode ADICIONAR fontes novas,
   nunca remover as existentes).
3. Técnicas que funcionaram na rodada 1:
   - busca: "<município> COSIP alíquota faixas kWh lei iluminação pública"
   - agregadores: legisweb.com.br/legislacao/?id=, lefisc.com.br, leis.org,
     camarasempapel (HTML de lei), sapl (PDFs de normas)
   - busca fallback: web_extract em https://html.duckduckgo.com/html/?q=...
   - PDF grande: curl para ~/.hermes/cache/scratch/cip2/ + pypdf + grep por
     "Art." / "kWh" / "ANEXO"
   - portais com 403 (Cloudflare): leismunicipais, leis.org, jusbrasil,
     legislacaodigital → não insistir, use busca/cache/agregador
4. NUNCA promova a completo sem tabela efetivamente extraída com URL acessada.
   Parcial→completo só com: tabelas preenchidas + exercicio + 1+ fonte.
5. Se em ~3 buscas + 3 extrações não achar, mantenha o status atual com
   pendencias atualizadas (o que tentou) — também é resultado válido.
6. Saída: batches/saida_loteN.json (mesmo formato do lote N), validado com
    Draft7Validator(schema.json) até 0 erros. atualizado_em=2026-10-01,
   proxima_revisao=2026-10-31.
