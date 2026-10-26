"""Pruebas de la importación de estados financieros desde Excel."""

import io

import pandas as pd
import pytest

from gfo import calculos as calc
from gfo import datos, importar


def excel(filas, hoja="Hoja1") -> bytes:
    buf = io.BytesIO()
    pd.DataFrame(filas).to_excel(buf, header=False, index=False, sheet_name=hoja)
    return buf.getvalue()


def test_a_numero():
    assert importar.a_numero("C$ 1,234.50") == 1234.5
    assert importar.a_numero("(2,000)") == -2000
    assert importar.a_numero("1.234,50") == 1234.5
    assert importar.a_numero("Caja") is None


def test_plantilla_ida_y_vuelta():
    tabla = datos._estados_df(datos.ESTADOS_EJEMPLO)
    r = importar.interpretar(importar.leer_archivos([("p.xlsx", importar.plantilla_excel(tabla))]))
    nueva = importar.a_tabla(r["estados"])
    cuentas = [k for k, *_ in datos.CUENTAS_BALANCE + datos.CUENTAS_RESULTADOS] + ["tasa_impuesto"]
    pd.testing.assert_frame_equal(nueva.loc[cuentas], tabla.loc[cuentas])
    assert nueva.loc["dividendos", "2025"] == pytest.approx(279_400)   # UR 1,000,000 + UN 729,400 − UR 1,450,000
    assert r["no_reconocidas"].empty


FORMATO_LIBRE = [
    ["EMPRESA X", None, None, None],
    ["Código", "Cuenta", "Al 31/12/2024", "Al 31/12/2025"],
    [None, "ACTIVOS CORRIENTES", None, None],
    ["1101", "Caja", 50_000, 60_000],
    ["1102", "Bancos", "C$ 250,000.00", "300,000"],
    ["1103", "Clientes", 400_000, 380_000],
    ["1104", "Inventario de mercadería", 600_000, 650_000],
    ["1105", "IVA acreditable", 20_000, 25_000],
    [None, "ACTIVOS NO CORRIENTES", None, None],
    ["1201", "Edificios", 900_000, 900_000],
    ["1202", "Vehículos", 300_000, 400_000],
    ["1203", "Depreciación acumulada", "(200,000)", "(280,000)"],
    [None, "TOTAL ACTIVOS", 2_320_000, 2_435_000],
    [None, "PASIVOS CORRIENTES", None, None],
    ["2101", "Proveedores", 300_000, 320_000],
    ["2103", "Impuestos por pagar", 40_000, 55_000],
    [None, "PASIVOS NO CORRIENTES", None, None],
    ["2201", "Préstamo hipotecario", 300_000, 200_000],
    [None, "PATRIMONIO", None, None],
    ["3101", "Capital social", 1_450_000, 1_450_000],
    ["3103", "Utilidades acumuladas", 230_000, 410_000],
    [None, "TOTAL PASIVO Y PATRIMONIO", 2_320_000, 2_435_000],
    [None, "ESTADO DE RESULTADOS", None, None],
    ["4101", "Ventas", 3_000_000, 3_400_000],
    ["4102", "Devoluciones sobre ventas", -50_000, -60_000],
    ["5101", "Costo de ventas", -1_900_000, -2_100_000],
    ["6101", "Gastos de venta", -300_000, -330_000],
    ["6102", "Gastos de administración", -250_000, -270_000],
    ["6103", "Depreciación", -70_000, -80_000],
    ["7101", "Gastos financieros", -60_000, -50_000],
    ["7201", "Impuesto sobre la renta", -111_000, -153_000],
    [None, "Utilidad neta del ejercicio", 259_000, 357_000],
]


def test_formato_libre_una_hoja():
    r = importar.interpretar(importar.leer_archivos([("x.xlsx", excel(FORMATO_LIBRE))]))
    assert r["periodos"] == ["2024", "2025"]
    e = r["estados"]["2025"]
    assert e["efectivo"] == 360_000                 # Caja + Bancos
    assert e["ppe"] == 1_020_000                    # Edificios + Vehículos − Depreciación acumulada
    assert e["otros_ac"] == 25_000                  # IVA acreditable → otros activos corrientes
    assert e["otros_pc"] == 55_000
    assert e["prestamos_lp"] == 200_000
    assert e["ventas"] == 3_340_000                 # Ventas − Devoluciones
    assert e["costo_ventas"] == 2_100_000           # gastos en negativo se toman en valor absoluto
    assert e["tasa_impuesto"] == pytest.approx(30)  # 153,000 ÷ 510,000
    assert (r["verificaciones"]["Coincide"] == "✓").all()
    assert r["avisos"] == []
    assert e["dividendos"] == pytest.approx(177_000)  # 230,000 + 357,000 − 410,000
    p = {**e, "tasa_impuesto": 0.30}
    assert calc.estado_resultados(p)["utilidad_neta"] == pytest.approx(357_000)


def test_dos_archivos_se_combinan_por_periodo():
    bg = [r for r in FORMATO_LIBRE if FORMATO_LIBRE.index(r) < 22]
    er = [FORMATO_LIBRE[1]] + FORMATO_LIBRE[23:]
    r = importar.interpretar(importar.leer_archivos([("bg.xlsx", excel(bg, "Balance")),
                                                     ("er.xlsx", excel(er, "Resultados"))]))
    assert r["estados"]["2024"]["ventas"] == 2_950_000
    assert r["estados"]["2024"]["capital"] == 1_450_000


def test_fila_desconocida_se_reporta():
    filas = [["Cuenta", 2025], ["Ventas", 1000], ["Costo de ventas", 600], ["Regalías extraordinarias", 50]]
    r = importar.interpretar(importar.leer_archivos([("er.xlsx", excel(filas, "Estado de resultados"))]))
    assert list(r["no_reconocidas"]["Cuenta del archivo"]) == ["Regalías extraordinarias"]
