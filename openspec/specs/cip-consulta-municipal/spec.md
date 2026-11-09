# cip-consulta-municipal Specification

## Purpose

Apresenta a cobrança da CIP de um município de forma curta e verificável, priorizando a tabela e a base de cálculo e deixando detalhes em seções recolhíveis.

## Requirements

### Requirement: Resumo objetivo no topo

A página municipal SHALL começar pelo nome do município, exercício, tipo de cobrança, data da verificação e uma tabela de faixas. A página MUST NOT repetir a mesma explicação em uma introdução, em uma seção de cálculo e em perguntas frequentes.

#### Scenario: Município com cobrança fixa
- **WHEN** a página de um município fixo é aberta
- **THEN** o tipo "Valor fixo" e a tabela em reais aparecem antes de qualquer texto explicativo longo

#### Scenario: Município com cobrança percentual
- **WHEN** a página de um município percentual é aberta
- **THEN** o resumo informa o percentual, a base municipal e o valor estimado por faixa

### Requirement: Detalhes progressivos

O cálculo explicado, a base legal, as isenções, as ressalvas e as fontes SHALL ficar em seções recolhíveis nativas, abertas apenas por ação do usuário. A seção de resumo MUST permanecer visível.

#### Scenario: Conteúdo recolhido
- **WHEN** a página é carregada
- **THEN** a tabela está visível e os detalhes legais e metodológicos estão recolhidos

#### Scenario: Conteúdo acessível
- **WHEN** o usuário abre uma seção recolhível
- **THEN** o conteúdo aparece sem JavaScript adicional

### Requirement: Aviso de valores antigos

Quando o exercício da tabela for anterior ao ano corrente, a página SHALL exibir um aviso de que os valores podem estar desatualizados. O selo MUST NOT afirmar verificação atual sem essa ressalva.

#### Scenario: Exercício anterior
- **WHEN** a tabela é de exercício anterior ao ano corrente
- **THEN** a página mostra "Valores de {exercício} — confira a atualização" junto ao selo

#### Scenario: Exercício atual
- **WHEN** a tabela é do ano corrente
- **THEN** a página mostra o selo de verificação sem o aviso de desatualização

### Requirement: Navegação compacta

A lista de outros municípios SHALL ser limitada a um conjunto curto e recolhível, com link para o hub do estado. A página MUST NOT listar dezenas de municípios no corpo principal.

#### Scenario: Lista de municípios do estado
- **WHEN** a página de um município é exibida
- **THEN** há um link para o hub da UF e, no máximo, uma lista curta recolhível
