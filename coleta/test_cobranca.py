import unittest

from coleta.cobranca import esta_desatualizado, fmt_faixa, fmt_valor, validate_record


class CobrancaTest(unittest.TestCase):
    def test_percentual_sobre_uvc(self):
        reg = {
            "municipio": "Londrina",
            "tipo": "percentual",
            "base_calculo": {"valor": 73.83, "descricao": "UVC", "exercicio": 2025, "fonte_url": "https://exemplo"},
        }
        faixa = {"faixa_kwh": {"min": 31, "max": 50}, "valor": 4, "tipo": "percentual"}
        self.assertEqual(fmt_valor(faixa, reg), "4% · R$ 2,95/mês")
        self.assertEqual(fmt_faixa(faixa, reg), "31–50 kWh")

    def test_faixa_legada_usa_limite_exclusivo(self):
        faixa = {"faixa_kwh": {"min": 120, "max": 140}}
        self.assertEqual(fmt_faixa(faixa), "121–140 kWh")

    def test_faixa_aberta(self):
        self.assertEqual(fmt_faixa({"faixa_kwh": {"min": 401, "max": None}}), "acima de 401 kWh")
        self.assertEqual(fmt_faixa({"faixa_kwh": {"min": 401, "max": None}}, {"tipo": "percentual"}), "acima de 400 kWh")

    def test_formula_nao_recebe_percentual(self):
        reg = {"municipio": "Rio de Janeiro", "tipo": "fixa"}
        faixa = {"valor": 6.2, "unidade": "FORMULA_TEIP", "formula": "6,2 + 0,01602 x TEIP"}
        self.assertEqual(fmt_valor(faixa, reg), "6,2 + 0,01602 x TEIP")

    def test_percentual_sem_base_falha(self):
        with self.assertRaises(ValueError):
            validate_record({"municipio": "Teste", "tipo": "percentual", "tabelas": {}})

    def test_valor_negativo_falha(self):
        with self.assertRaises(ValueError):
            validate_record({
                "municipio": "Teste",
                "tipo": "fixa",
                "tabelas": {"residencial": [{"faixa_kwh": {"min": 0, "max": 10}, "valor": -1}]},
            })

    def test_exercicio_anterior_fica_desatualizado(self):
        self.assertTrue(esta_desatualizado({"exercicio": 2025}, ano=2026))
        self.assertFalse(esta_desatualizado({"exercicio": 2026}, ano=2026))


if __name__ == "__main__":
    unittest.main()
