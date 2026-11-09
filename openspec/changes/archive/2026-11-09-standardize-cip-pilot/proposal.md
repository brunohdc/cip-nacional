# Proposal

## Why

O piloto atual é funcional, mas mistura formatos de cobrança e exibe percentuais sem uma base municipal estruturada. Isso impede calcular ou comparar valores com segurança e deixa as páginas longas e repetitivas.

## What Changes

- Padronizar cada faixa de cobrança em dois tipos explícitos: `fixa` (R$) ou `percentual` (%).
- Vincular todo percentual a uma base municipal própria, com valor, descrição, vigência e fonte.
- Tratar a base ausente ou vencida de forma explícita, sem calcular nem presumir valor.
- Reduzir o texto da página municipal ao essencial: resumo, tabela, cálculo, base legal e fontes.
- Aplicar o novo formato a um piloto com São Paulo (valor fixo) e Londrina (percentual sobre UVC).
- Corrigir a exibição de fórmulas especiais para que não sejam apresentadas como percentual.

## Capabilities

### New Capabilities

- `cip-modelo-cobranca`: modelo único para cobrança fixa ou percentual e sua base municipal.
- `cip-consulta-municipal`: apresentação enxuta da cobrança e das fontes na página do município.

### Modified Capabilities

<!-- Nenhuma capability existente. -->

## Impact

- `coleta/schema.json`: novo formato de faixa e base de cálculo.
- `coleta/render_site.py`: renderização das páginas e formatação de valores.
- `coleta/pilot_top10.v2.json` ou um novo conjunto piloto: dados de São Paulo e Londrina.
- `cip/sp/sao-paulo/index.html` e `cip/pr/londrina/index.html`: saída gerada para validação.
- Apenas o piloto será migrado nesta mudança; os demais municípios permanecem no formato atual.
