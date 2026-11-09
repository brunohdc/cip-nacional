# Spec Delta

## Purpose

Define um modelo único de cobrança da CIP por município, com valores fixos em reais ou percentuais aplicados sobre uma base municipal documentada.

## ADDED Requirements

### Requirement: Tipo de cobrança explícito

Cada registro de município SHALL declarar `tipo` como `fixa` ou `percentual` e cada faixa SHALL usar o mesmo tipo do registro, com `valor` numérico não negativo expresso em reais por mês ou em percentual, respectivamente.

#### Scenario: Cobrança fixa
- **WHEN** o registro declara `tipo: "fixa"`
- **THEN** o valor da faixa representa reais por mês e não depende de base de cálculo

#### Scenario: Cobrança percentual
- **WHEN** o registro declara `tipo: "percentual"`
- **THEN** o valor da faixa representa percentual e o registro informa uma base de cálculo municipal

#### Scenario: Valor inválido
- **WHEN** uma faixa tem valor negativo ou tipo diferente do registro
- **THEN** a validação rejeita o registro e nenhuma página é gerada para ele

### Requirement: Base de cálculo municipal

Todo registro com cobrança percentual SHALL informar `base_calculo` com `valor` positivo em reais, `descricao`, `exercicio` e `fonte_url`. A base SHALL ser específica do município e a página SHALL exibir seu valor, descrição e exercício.

#### Scenario: Base documentada
- **WHEN** um município percentual tem base com valor, descrição, exercício e fonte
- **THEN** a página informa a base e o percentual aplicado

#### Scenario: Base ausente
- **WHEN** um município percentual não tem base completa
- **THEN** o registro é rejeitado e nenhum valor em reais é calculado ou exibido

#### Scenario: Base desatualizada
- **WHEN** o exercício da base é anterior ao exercício do registro
- **THEN** a página exibe a base com seu exercício explícito e não a apresenta como valor do exercício atual

### Requirement: Cálculo do valor estimado

Para cobrança percentual, o sistema SHALL calcular o valor mensal estimado como `valor / 100 × base_calculo.valor`, arredondado para duas casas decimais. Para cobrança fixa, o valor estimado SHALL ser o próprio valor da faixa.

#### Scenario: Percentual sobre UVC
- **WHEN** a faixa tem 4% e a base municipal é R$ 73,83
- **THEN** o valor estimado exibido é R$ 2,95

#### Scenario: Arredondamento
- **WHEN** o resultado tem mais de duas casas decimais
- **THEN** o valor é arredondado para duas casas e formatado em reais no padrão brasileiro

### Requirement: Preservação de fórmulas especiais

Fórmulas que dependem de tarifa externa SHALL ser exibidas como texto e MUST NOT ser convertidas em percentual nem ter valor em reais calculado sem a tarifa de referência.

#### Scenario: Fórmula TEIP
- **WHEN** um registro legado usa fórmula sobre TEIP
- **THEN** a página mostra a expressão da fórmula e não acrescenta o símbolo de percentual
