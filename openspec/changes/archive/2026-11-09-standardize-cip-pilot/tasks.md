# Tasks

## 1. Modelo e validação

- [x] 1.1 Adicionar `tipo` e `base_calculo` ao schema e criar `validate_record()` no gerador; verificar que registros percentuais sem base e faixas com valor negativo são rejeitados.
- [x] 1.2 Ajustar `fmt_faixa()` e `fmt_valor()` para calcular percentual sobre a base e formatar fórmulas como texto; verificar 4% sobre R$ 73,83 = R$ 2,95 e que `FORMULA_TEIP` não recebe `%`.

## 2. Dados do piloto

- [x] 2.1 Criar `coleta/pilot_cobranca.json` com São Paulo (fixo) e Londrina (percentual, UVC R$ 73,83, exercício 2025); verificar que o arquivo contém exatamente dois registros e que a fonte da UVC está preenchida.
- [x] 2.2 Permitir que o gerador leia `CIP_DATA` e mantenha `cip_top500.json` como padrão; verificar que `CIP_DATA=coleta/pilot_cobranca.json python coleta/render_site.py` gera apenas as duas páginas.

## 3. Página enxuta

- [x] 3.1 Reorganizar a página municipal em resumo, aviso de vigência, tabela e `<details>` para cálculo, base legal, isenções, ressalvas e fontes; verificar visualmente que os detalhes iniciam recolhidos.
- [x] 3.2 Substituir a lista longa de municípios por link do hub da UF e lista curta recolhível; verificar que a página de São Paulo não contém a lista completa de cidades de SP no corpo principal.
- [x] 3.3 Adicionar o aviso "Valores de {exercício} — confira a atualização" quando o exercício for anterior ao ano corrente; verificar que Londrina (2025) exibe o aviso e São Paulo (2026) não.

## 4. Geração e validação

- [x] 4.1 Gerar o piloto em diretório temporário e conferir as duas páginas; verificar que não há placeholders, fórmulas com `%` indevido ou valores sem fonte.
- [x] 4.2 Copiar apenas `cip/sp/sao-paulo/index.html` e `cip/pr/londrina/index.html` gerados; verificar com `git diff --stat` que nenhum outro HTML foi alterado.
- [x] 4.3 Rodar `python -m unittest coleta.test_cobranca` e `openspec validate standardize-cip-pilot --strict`; verificar que ambos terminam sem erro.

## 5. Documentação

- [x] 5.1 Atualizar `coleta/README.md` com o modelo fixo/percentual, a base municipal e o comando do piloto; verificar que o comando documentado reproduz as duas páginas.
