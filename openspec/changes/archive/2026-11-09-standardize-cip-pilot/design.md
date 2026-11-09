# Design

## Context

O gerador atual em `coleta/render_site.py` lê um único JSON de 500 municípios, mistura unidades por faixa e publica as páginas na raiz do repositório. O piloto precisa validar o novo modelo com dois municípios sem migrar o restante da base. A fonte de Londrina confirma UVC de R$ 73,83 vigente em setembro de 2025.

## Goals / Non-Goals

**Goals:**
- Reaproveitar o gerador estático existente, adicionando o modelo fixo/percentual.
- Manter os dados e a saída do piloto reproduzíveis com um comando.
- Entregar páginas visivelmente menores, com detalhes recolhíveis.
- Detectar dados inválidos antes de gerar HTML.

**Non-Goals:**
- Migrar os 500 municípios ou reescrever o site como aplicação dinâmica.
- Calcular fórmulas que dependem de TEIP ou de tarifa externa.
- Atualizar automaticamente valores anuais.
- Alterar a página de arrecadação nesta mudança.

## Decisions

**1. Estender o schema existente em vez de criar outro formato de tabela.**
Cada registro recebe `tipo` (`fixa` ou `percentual`) e, quando percentual, `base_calculo`. As faixas continuam em `tabelas[classe][]` com `faixa_kwh` e `valor`, mas deixam de depender de `unidade` para determinar reais ou percentual.

Alternativa descartada: criar uma coleção separada de faixas. Aumentaria a migração e duplicaria a estrutura atual.

**2. A base de cálculo fica no registro, não em cada faixa.**
O percentual de Londrina incide sobre a mesma UVC em todas as faixas. A base contém `valor`, `descricao`, `exercicio` e `fonte_url`, e a página calcula o valor estimado por faixa a partir dela.

Alternativa descartada: repetir a base em cada faixa. Facilitaria bases variáveis por faixa, mas criaria dados duplicados e divergentes.

**3. Um conjunto piloto separado e um parâmetro de entrada.**
Criar `coleta/pilot_cobranca.json` com São Paulo e Londrina. O gerador passa a aceitar `CIP_DATA`; sem a variável, mantém o comportamento atual com `cip_top500.json`.

Alternativa descartada: editar `cip_top500.json` diretamente. Misturaria o piloto com a base antiga e dificultaria a revisão.

**4. Validação mínima no próprio gerador.**
Uma função `validate_record()` rejeita tipo inválido, valor negativo, base percentual incompleta e faixa fora do tipo do registro. A geração para no primeiro erro, antes de escrever qualquer HTML.

Alternativa descartada: adicionar `jsonschema` como dependência. Para o piloto, a validação explícita cobre as regras e evita uma nova dependência.

**5. Página com detalhes progressivos nativos.**
O conteúdo principal fica em uma coluna curta: resumo, aviso de vigência, tabela e uma linha de cálculo. Base legal, isenções, ressalvas, fontes e lista de municípios vizinhos ficam em `<details>`. Não é necessário JavaScript.

Alternativa descartada: abas ou componentes JavaScript. `<details>` é acessível, funciona sem build e resolve a queixa de excesso de texto.

**6. Formatação por tipo, não por presença de unidade.**
`fmt_valor()` passa a decidir o formato por `tipo` e por `unidade`. `FORMULA_TEIP` mostra `formula` como texto; percentual mostra `%`; fixo mostra `R$`.

## Risks / Trade-offs

- **Página de Londrina ficar marcada como desatualizada** → o exercício é 2025 e a fonte não informa 2026; a página mostrará o aviso e não inventará valor.
- **Gerar na raiz sobrescrever páginas existentes** → o piloto será gerado em diretório temporário e comparado; a publicação dos dois HTMLs será uma etapa explícita.
- **Campo `base_calculo` ausente em registros antigos** → a validação só exige a base para `tipo: percentual`; registros antigos com `unidade` continuam renderizáveis no caminho legado.
- **Lista de municípios muito curta reduz links internos** → o link para o hub da UF mantém a navegação e evita repetir dezenas de links em cada página.

## Migration Plan

1. Adicionar o modelo e a validação ao gerador sem alterar o caminho padrão.
2. Criar o conjunto piloto e gerar em diretório temporário.
3. Conferir as duas páginas e copiar apenas esses HTMLs para `cip/`.
4. Rodar `openspec validate` e os testes do gerador.
5. Reverter é remover o conjunto piloto e restaurar os dois HTMLs anteriores; nenhuma outra página é tocada.

## Open Questions

<!-- Nenhuma. -->
