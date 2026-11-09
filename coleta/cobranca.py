"""Regras do modelo de cobrança da CIP (fixa ou percentual)."""
from datetime import date, datetime


def brl(v):
    if not isinstance(v, (int, float)):
        return "n/d"
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_data(iso):
    if not iso:
        return "data não informada"
    try:
        return datetime.strptime(iso, "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return str(iso)


def tipo_label(tipo):
    return "Valor fixo" if tipo == "fixa" else "Percentual" if tipo == "percentual" else "Não informado"


def esta_desatualizado(reg, ano=None):
    exercicio = reg.get("exercicio")
    return isinstance(exercicio, int) and exercicio < (ano or date.today().year)


def fmt_faixa(f, reg=None):
    lo, hi = f["faixa_kwh"]["min"], f["faixa_kwh"]["max"]
    novo = bool(reg and reg.get("tipo"))
    if lo is None and hi is None:
        return "todas as faixas"
    if lo is None:
        return f"até {hi} kWh"
    if hi is None:
        if novo:
            return f"acima de {lo - 1} kWh" if lo > 0 else "todas as faixas"
        return f"acima de {lo} kWh"
    if novo:
        return f"{lo}–{hi} kWh"
    return f"{lo + 1}–{hi} kWh" if lo != 0 else f"0–{hi} kWh"


def valor_estimado(f, reg):
    v = f.get("valor")
    base = reg.get("base_calculo") or {}
    if reg.get("tipo") == "percentual" and isinstance(v, (int, float)) and isinstance(base.get("valor"), (int, float)):
        return round(v / 100 * base["valor"], 2)
    return None


def fmt_valor(f, reg=None):
    reg = reg or {}
    v = f.get("valor")
    if isinstance(v, str):
        if v.lower() == "n/d":
            return "n/d"
        return v.capitalize()
    unidade = f.get("unidade", "")
    if unidade == "FORMULA_TEIP":
        return f.get("formula") or brl(v)
    if reg.get("tipo") == "percentual" or unidade.startswith("PERCENTUAL"):
        texto = f"{v:g}%".replace(".", ",")
        estimado = valor_estimado(f, reg)
        return f"{texto} · {brl(estimado)}/mês" if estimado is not None else texto
    return brl(v)


def validate_record(reg):
    tipo = reg.get("tipo")
    if tipo is None:
        return reg
    if tipo not in ("fixa", "percentual"):
        raise ValueError(f"{reg.get('municipio')}: tipo de cobrança inválido: {tipo!r}")

    base = reg.get("base_calculo")
    if tipo == "percentual":
        if not isinstance(base, dict):
            raise ValueError(f"{reg.get('municipio')}: cobrança percentual sem base_calculo")
        if not isinstance(base.get("valor"), (int, float)) or base["valor"] <= 0:
            raise ValueError(f"{reg.get('municipio')}: base_calculo.valor deve ser positivo")
        for campo in ("descricao", "exercicio", "fonte_url"):
            if not base.get(campo):
                raise ValueError(f"{reg.get('municipio')}: base_calculo.{campo} é obrigatório")

    for linhas in (reg.get("tabelas") or {}).values():
        for faixa in linhas:
            if faixa.get("tipo", tipo) != tipo:
                raise ValueError(f"{reg.get('municipio')}: faixa com tipo diferente do registro")
            valor = faixa.get("valor")
            if isinstance(valor, (int, float)) and valor < 0:
                raise ValueError(f"{reg.get('municipio')}: valor negativo em faixa")
    return reg
