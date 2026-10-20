"""Comprobación de los cálculos del sistema contra resultados calculados manualmente.

Ejecutar con:  python -m pytest
"""

import pandas as pd
import pytest

from gfo import calculos as calc
from gfo import datos


def periodo(anio: str) -> dict:
    p = dict(datos.ESTADOS_EJEMPLO[anio])
    p["tasa_impuesto"] /= 100
    return p


P24, P25 = periodo("2024"), periodo("2025")


def test_estado_resultados_2025():
    er = calc.estado_resultados(P25)
    assert er["utilidad_bruta"] == 3_312_000            # 9,200,000 − 5,888,000
    assert er["uaii"] == 1_252_000                      # 3,312,000 − 980,000 − 760,000 − 320,000
    assert er["uai"] == 1_042_000                       # 1,252,000 − 210,000
    assert er["impuestos"] == pytest.approx(312_600)    # 1,042,000 × 30 %
    assert er["utilidad_neta"] == pytest.approx(729_400)


def test_balance_cuadra():
    for p in (P24, P25):
        t = calc.totales_balance(p)
        assert t["diferencia"] == 0
    assert calc.totales_balance(P25)["activo_total"] == 6_600_000


def test_analisis_horizontal_y_vertical():
    h = calc.analisis_horizontal(pd.Series({"ventas": 8_000_000}), pd.Series({"ventas": 9_200_000}))
    assert h.loc["ventas", "var_abs"] == 1_200_000
    assert h.loc["ventas", "var_pct"] == pytest.approx(0.15)
    v = calc.analisis_vertical(pd.Series({"efectivo": 520_000}), 6_600_000)
    assert v["efectivo"] == pytest.approx(0.078788, rel=1e-4)


def test_razones_2025():
    r = calc.razones_financieras(P25)
    assert r["razon_corriente"] == pytest.approx(2_760_000 / 1_350_000)          # 2.04
    assert r["prueba_acida"] == pytest.approx((2_760_000 - 1_248_000) / 1_350_000)
    assert r["capital_trabajo"] == 1_410_000
    assert r["rotacion_inventario"] == pytest.approx(5_888_000 / 1_248_000)
    assert r["periodo_cobro"] == pytest.approx(900_000 / (9_200_000 / 365))      # ≈ 35.7 días
    assert r["razon_deuda"] == pytest.approx(3_150_000 / 6_600_000)              # 47.73 %
    assert r["cobertura_intereses"] == pytest.approx(1_252_000 / 210_000)
    assert r["roe"] == pytest.approx(729_400 / 3_450_000)                        # 21.14 %
    assert r["upa"] == pytest.approx(729_400 / 200_000)                          # C$ 3.647
    assert r["precio_utilidad"] == pytest.approx(45 / 3.647)


def test_dupont_igual_a_roe():
    d = calc.dupont(P25)
    assert d["roe"] == pytest.approx(calc.razones_financieras(P25)["roe"])
    assert d["roa"] == pytest.approx(729_400 / 6_600_000)


def test_division_entre_cero():
    assert calc.dividir(5, 0) is None
    p = dict(P25, intereses=0)
    assert calc.razones_financieras(p)["cobertura_intereses"] is None


def test_punto_equilibrio_manual():
    r = calc.cvu(precio=250, cv_unitario=150, costos_fijos=1_000_000, unidades=15_000)
    assert r["mcu"] == 100
    assert r["rmc"] == pytest.approx(0.4)
    assert r["pe_unidades"] == pytest.approx(10_000)
    assert r["pe_monetario"] == pytest.approx(2_500_000)
    assert r["utilidad"] == 500_000
    assert r["margen_seguridad_pct"] == pytest.approx(1 / 3)
    assert r["gao"] == pytest.approx(3)
    assert calc.unidades_para_utilidad(250, 150, 1_000_000, 200_000) == pytest.approx(12_000)


def test_escenario_cvu():
    base = calc.cvu(250, 150, 1_000_000, 15_000)
    e = calc.escenario_cvu(base, 0.10, 0, 0, 0)              # precio +10 % → 275
    assert e["mcu"] == pytest.approx(125)
    assert e["pe_unidades"] == pytest.approx(8_000)


def test_cvu_desde_estados_coincide_con_uaii():
    b = calc.cvu_desde_estados(P25, 250)
    r = calc.cvu(b["precio"], b["cv_unitario"], b["costos_fijos"], b["unidades"])
    assert r["utilidad"] == pytest.approx(calc.estado_resultados(P25)["uaii"])


def test_apalancamiento():
    a = calc.apalancamiento(9_200_000, 6_868_000, 1_080_000, 210_000)
    assert a["mc"] == 2_332_000
    assert a["uaii"] == 1_252_000
    assert a["gao"] == pytest.approx(2_332_000 / 1_252_000)       # 1.8626
    assert a["gaf"] == pytest.approx(1_252_000 / 1_042_000)       # 1.2015
    assert a["gat"] == pytest.approx(a["gao"] * a["gaf"])         # 2.2380


def test_gao_se_comprueba_con_resultados_proyectados():
    a = calc.apalancamiento(9_200_000, 6_868_000, 1_080_000, 210_000)
    uaii_nueva = 9_200_000 * 1.1 - 6_868_000 * 1.1 - 1_080_000
    assert (uaii_nueva - a["uaii"]) / a["uaii"] == pytest.approx(a["gao"] * 0.10)


def test_flujo_efectivo_indirecto_concilia():
    f = calc.flujo_efectivo_indirecto(P24, P25)
    assert f["flujo_operacion"] == pytest.approx(879_400)
    assert f["flujo_inversion"] == pytest.approx(-610_000)
    assert f["flujo_financiamiento"] == pytest.approx(-199_400)
    assert f["variacion_neta"] == pytest.approx(70_000)
    assert f["conciliado"]


def test_flujo_efectivo_directo():
    r = calc.flujo_efectivo_directo(datos.MOVIMIENTOS_CAJA_EJEMPLO, 520_000)
    neto = r["resumen"].set_index("Actividad")["Flujo neto"]
    assert neto["Operación"] == 85_000
    assert neto["Inversión"] == -105_000
    assert neto["Financiamiento"] == 60_000
    assert r["saldo_final"] == 560_000


SUPUESTOS = {"precio": 260, "costo_unitario": 160, "pct_contado": 0.6, "pct_compras_contado": 0.5,
             "pct_inventario_final": 0.2, "unidades_siguiente": 9_000, "pct_gastos_venta": 0.105,
             "gastos_admin_trim": 200_000, "depreciacion_trim": 85_000, "intereses_anuales": 210_000,
             "saldo_minimo": 300_000, "tasa_impuesto": 0.3}


def test_presupuesto_maestro():
    pm = calc.presupuesto_maestro(SUPUESTOS, datos.TRIMESTRES_EJEMPLO, P25)
    assert pm["ventas"].loc["Ventas (C$)", "T1"] == 8_500 * 260
    # Cobros T1 = 2,210,000 × 60 % + CxC inicial 900,000
    assert pm["cobros"].loc["Total cobros", "T1"] == pytest.approx(2_226_000)
    # Compras T1 = 8,500 + 20 % × 9,200 − 7,800 = 2,540 unidades
    assert pm["compras"].loc["(=) Unidades a comprar", "T1"] == pytest.approx(2_540)
    assert pm["cbv"].loc["(=) Costo de bienes vendidos", "Total"] == pytest.approx(38_000 * 160)
    # El saldo final nunca queda por debajo del mínimo
    assert min(pm["saldos"]) >= 300_000 - 0.01


def test_balance_proforma_cuadra():
    pm = calc.presupuesto_maestro(SUPUESTOS, datos.TRIMESTRES_EJEMPLO, P25)
    assert calc.totales_balance(pm["balance_proforma"])["diferencia"] == pytest.approx(0, abs=0.01)


def test_presupuesto_personal():
    r = calc.presupuesto_personal(datos.INGRESOS_PERSONALES_EJEMPLO, datos.GASTOS_PERSONALES_EJEMPLO, 5_000)
    assert r["total_ingresos"] == 32_500
    assert r["total_gastos"] == 26_000
    assert r["capacidad_ahorro"] == 6_500
    assert r["pct_ahorro"] == pytest.approx(0.20)
    assert r["saldo_disponible"] == 1_500


def test_control_inventario():
    r = calc.control_inventario(datos.PRODUCTOS_EJEMPLO, datos.MOVIMIENTOS_INV_EJEMPLO)
    res = r["resumen"].set_index("Código")
    # P001: 120 + 50 − 75 = 95 ; valor 95 × 1,850
    assert res.loc["P001", "Existencia final"] == 95
    assert res.loc["P001", "Valor del inventario"] == 95 * 1_850
    assert res.loc["P002", "Estado"] == "Reponer"                 # 22 ≤ 30
    assert res.loc["P002", "Cantidad sugerida"] == 38             # 2 × 30 − 22
    assert set(r["alertas"]["Código"]) == {"P002", "P005", "P006"}
    assert r["valor_total"] == pytest.approx(500_000)
    assert r["errores"] == []


def test_inventario_detecta_existencia_negativa():
    mov = pd.DataFrame([("2026-10-01", "P005", "Salida", 100.0, "Error")],
                       columns=["Fecha", "Código", "Tipo", "Cantidad", "Detalle"])
    r = calc.control_inventario(datos.PRODUCTOS_EJEMPLO, mov)
    assert any("negativa" in e for e in r["errores"])
