"""Módulo 4 · Apalancamiento operativo (GAO), financiero (GAF) y total (GAT)."""

import pandas as pd
import streamlit as st

from gfo import calculos as calc
from gfo import datos, ui

ui.encabezado("Apalancamiento",
              "Mida cuánto se amplifican las variaciones en ventas sobre la utilidad operativa (GAO), cuánto se "
              "amplifican las variaciones de la UAII sobre la utilidad por acción (GAF) y el efecto combinado (GAT).",
              "Unidad 2 · Módulo 4")

periodos = datos.periodos()
c1, c2, c3 = st.columns(3)
periodo = c1.selectbox("Período", periodos, index=len(periodos) - 1)
with c2:
    dp = ui.entrada("Dividendos preferentes (C$)", "ap_dividendos_pref", min_value=0.0, step=10_000.0, format="%.2f")
with c3:
    cambio = ui.deslizador("Variación supuesta en ventas (%)", "ap_cambio_ventas", min_value=-50, max_value=50, step=1)

p = datos.cuentas_periodo(periodo)
cl = calc.clasificar_costos(p)
a = calc.apalancamiento(p["ventas"], cl["costos_variables"], cl["costos_fijos"], p["intereses"], dp, p["tasa_impuesto"])
ef = calc.efecto_apalancamiento(a["gao"] or 0, a["gaf"] or 0, cambio / 100)

ui.fila_kpis([
    ui.kpi("GAO · Operativo", ui.veces(a["gao"]), "Margen de contribución ÷ UAII"),
    ui.kpi("GAF · Financiero", ui.veces(a["gaf"]), "UAII ÷ (UAII − Intereses − DP/(1−t))"),
    ui.kpi("GAT · Total", ui.veces(a["gat"]), "GAO × GAF"),
])
st.write("")

izq, der = st.columns([1, 1.25])
with izq:
    st.markdown(f"##### Datos tomados del Estado de Resultados {periodo}")
    ui.tabla_estado([
        ("Ventas", [a["ventas"]], ""),
        ("(−) Costos variables (costo de ventas + gastos de venta)", [a["costos_variables"]], ""),
        ("Margen de contribución", [a["mc"]], "sub"),
        ("(−) Costos fijos (administración + depreciación)", [a["costos_fijos"]], ""),
        ("Utilidad operativa (UAII)", [a["uaii"]], "sub"),
        ("(−) Gastos por intereses", [a["intereses"]], ""),
        ("Utilidad antes de impuestos (UAI)", [a["uai"]], "total"),
    ], ["C$"])
    st.write("")
    ui.formula(
        f"<b>GAO</b> = {ui.cs(a['mc'])} ÷ {ui.cs(a['uaii'])} = <b>{ui.veces(a['gao'])}</b><br>"
        f"<b>GAF</b> = {ui.cs(a['uaii'])} ÷ ({ui.cs(a['uaii'])} − {ui.cs(a['intereses'])}"
        + (f" − {ui.cs(dp)} ÷ (1 − {ui.pct(p['tasa_impuesto'], 0)})" if dp else "")
        + f") = <b>{ui.veces(a['gaf'])}</b><br>"
        f"<b>GAT</b> = {ui.num(a['gao'], 4)} × {ui.num(a['gaf'], 4)} = <b>{ui.veces(a['gat'])}</b>"
        "<br><span class='note'>Código: <code>gfo/calculos.py → apalancamiento()</code></span>")

with der:
    fig = ui.figura(f"Efecto de un cambio de {cambio:+d} % en ventas", 330, leyenda=False)
    vals = [ef["cambio_ventas"] * 100, ef["cambio_uaii"] * 100, ef["cambio_upa"] * 100]
    colores = [ui.SERIES[0] if v >= 0 else ui.SERIES[7] for v in vals]
    ui.barras(fig, ["Ventas", "Utilidad operativa (UAII)", "Utilidad por acción (UPA)"], vals, "Cambio", colores,
              texto=[f"{v:+.2f} %" for v in vals], hovertemplate="%{x}: %{y:+.2f} %<extra></extra>")
    fig.update_yaxes(ticksuffix=" %")
    ui.mostrar(fig)
    st.markdown(
        f"**Interpretación:** con un GAO de {ui.num(a['gao'])}, si las ventas cambian {cambio:+d} %, la UAII cambia "
        f"**{ef['cambio_uaii'] * 100:+.2f} %**. Con un GAF de {ui.num(a['gaf'])}, ese cambio se traslada a la utilidad "
        f"por acción como **{ef['cambio_upa'] * 100:+.2f} %** (GAT = {ui.num(a['gat'])}).")
    riesgo = "alto" if (a["gat"] or 0) > 3 else "moderado" if (a["gat"] or 0) > 1.5 else "bajo"
    st.info(f"Nivel de riesgo total **{riesgo}**: cuanto mayor es el apalancamiento, mayores son las ganancias cuando "
            "las ventas suben, pero también las pérdidas cuando bajan.", icon=":material/lightbulb:")

st.markdown("##### Comprobación con estados de resultados proyectados")
nuevas = a["ventas"] * (1 + cambio / 100)
cv_n = a["costos_variables"] * (1 + cambio / 100)
uaii_n = nuevas - cv_n - a["costos_fijos"]
uai_n = uaii_n - a["intereses"]
un = lambda uai: uai - max(uai, 0) * p["tasa_impuesto"]
upa = lambda uai: calc.dividir(un(uai) - dp, p["acciones"])
comp = pd.DataFrame([
    {"Concepto": "Ventas", "Actual": ui.cs(a["ventas"]), "Proyectado": ui.cs(nuevas), "Cambio": ui.pct(cambio / 100)},
    {"Concepto": "Utilidad operativa (UAII)", "Actual": ui.cs(a["uaii"]), "Proyectado": ui.cs(uaii_n),
     "Cambio": ui.pct(calc.dividir(uaii_n - a["uaii"], a["uaii"]))},
    {"Concepto": "Utilidad por acción (UPA)", "Actual": ui.cs(upa(a["uai"])), "Proyectado": ui.cs(upa(uai_n)),
     "Cambio": ui.pct(calc.dividir((upa(uai_n) or 0) - (upa(a["uai"]) or 0), upa(a["uai"])))},
])
st.dataframe(comp, hide_index=True)
st.caption("El cambio porcentual recalculado con los estados proyectados coincide con GAO × Δ% ventas y GAT × Δ% ventas, "
           "lo que comprueba los grados de apalancamiento (válido mientras la UAI sea positiva).")
