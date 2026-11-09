# Decisões — schema e URL

## 1. URL

**Padrão:** `/cip/<uf>/<slug>` → `cip/sp/sao-paulo`, `cip/ce/fortaleza`

Por quê:
- **1 município = 1 página** (nunca URL com distribuidora — 541 municípios têm >1
  concessionária e a alíquota é do município, não da distribuidora; criar variação
  por distribuidora = conteúdo duplicado canônico)
- Curta, legível, em PT (a query é em PT): "CIP" + cidade é o que a pessoa digita
- Slug sem acento/hífen normalizado; cod_ibge no JSON é a chave real (slug pode
  colidir — desempate por UF)

**Hubs (internal linking — o compounding):**
- `/cip/` — hub nacional (lista por UF)
- `/cip/sp/` — hub por UF
- `/distribuidora/cemig-d/` — hub por distribuidora (lista municípios atendidos,
  vindo do mapa ANEEL) — captura a query "CIP Cemig" sem duplicar páginas

**Queries alvo por página:**
- Título: `Contribuição de Iluminação Pública em {Município} ({UF}) — alíquotas {exercicio}`
- H1: `CIP em {Município}: alíquotas {exercicio}`
- Meta: faixa + valor de exemplo da tabela + base legal
- Também rankeia: "CIP {cidade}", "taxa de iluminação pública {cidade}",
  "quanto pagar de COSIP {cidade}", "alíquota iluminação pública {cidade}"

## 2. Schema (`schema.json`)

Pontos centrais:
- **`status`** dirige o render: `completo` mostra tabela; `parcial` mostra base
  legal + o que falta (campo `pendencias`); `nao_encontrado` mostra "não
  informado — sem registro localizado" + campo de correção (crowdsourcing)
- **`mecanismo`** porque não existe unidade única entre municípios — comparar
  Fortaleza (% TIP) com Manaus (R$ fixo) sem esse campo é mentira
- **`exercicio`** separado de `base_legal` — a lei é de 2013, o valor é de 2026
- **`tabelas` com `valor` number | "isento" | "n/d"** — schema impede número
  inventado: string só aceita os especiais, o resto tem que ser number real
- **`fontes` minItems=1** — registro sem fonte é inválido por construção
- **`ressalvas`** sempre visível na página (transparência = confiança)
- **`proxima_revisao`** — base do cron (30d top 500, 90d cauda)

## 3. Regras da página (anti-fabrication + SEO)

1. Tabela só renderiza se `status=completo` e `exercicio` ≥ ano atual − 1;
   senão banner: "Valores de {exercicio} — conferindo atualização"
2. Todo valor com link "Fonte: {norma} — ver original"
3. `ressalvas` exibidas como nota (não escondidas)
4. 400–700 palavras de copy sob a tabela (como é calculada, isenções, como
   contestar, o que é TIP/TEIP) + FAQ com FAQPage schema
5. SoftwareApplication/FAQ schema + breadcrumb; LastModified = atualizado_em
6. Cada página → links para: hub UF, hub distribuidora, 3–5 municípios vizinhos
   e a página irmã "simulador de conta com CIP" (futuro)

## 4. Checklist antes de publicar um registro

- [ ] cod_ibge existe no mapa ANEEL
- [ ] fontes ≥ 1 com URL testada (200)
- [ ] exercicio = ano atual ou ano anterior
- [ ] tabelas preenchidas SEM campo vazio (usar "isento"/"n/d", nunca omitir)
- [ ] ressalvas documentadas
- [ ] proxima_revisao definida
