# cip-nacional

Site estático de CIP (Contribuição de Iluminação Pública) por município.

## Estrutura

- `index.html` — home
- `cip/<uf>/<slug>/index.html` — página por município (1 URL = 1 município)
- `arrecadacao/index.html` — arrecadação oficial da CIP (SICONFI/DCA, 2022–2025)
- `distribuidora/<slug>/index.html` — hub por distribuidora
- `assets/` — CSS
- `coleta/` — scripts e dados de origem (coleta, verificação, render)

## Pipeline

Ver `coleta/README.md`. Resumo:

```bash
export CIP_BASE=~/workspace/cip_collected   # dados (default)
export CIP_SITE=~/workspace/cip_site        # saída do site (default)
python3 coleta/coleta_arrecadacao.py        # coleta SICONFI/DCA -> arrecadacao_cip.json
python3 coleta/render_site.py               # gera as páginas estáticas
```

Deploy: push em `main` → GitHub Pages.
