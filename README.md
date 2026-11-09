# cip-nacional

Site estático de CIP (Contribuição de Iluminação Pública) por município: valores pagos, faixas, base legal e fontes.

## Estrutura

- `index.html` — home
- `cip/<uf>/<slug>/index.html` — página por município (1 URL = 1 município)
- `distribuidora/<slug>/index.html` — hub por distribuidora
- `assets/` — CSS
- `coleta/` — scripts e dados de origem (coleta, verificação, render)

A arrecadação oficial da CIP por município fica em repositório separado:
https://github.com/brunohdc/cip-arrecadada-por-municipio

## Pipeline

Ver `coleta/README.md`. Resumo:

```bash
export CIP_BASE=~/workspace/cip_collected   # dados (default)
export CIP_SITE=~/workspace/cip_site        # saída do site (default)
python3 coleta/render_site.py               # gera as páginas estáticas
```

Deploy: push em `main` → GitHub Pages.
