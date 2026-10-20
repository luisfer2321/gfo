"""Aplicación complementaria · Presupuesto personal (independiente del presupuesto maestro empresarial)."""

import numpy as np
import streamlit as st

from gfo import calculos as calc
from gfo import datos, ui

ui.encabezado("Presupuesto personal",
              "Registre sus ingresos y gastos mensuales por categoría para conocer su saldo disponible y su capacidad "
              "de ahorro. Es una aplicación práctica independiente del presupuesto empresarial; los datos de ejemplo son "
              "ficticios.", "Aplicación práctica complementaria")

izq, der = st.columns([1, 1.5])
with izq:
    st.markdown("##### Ingresos del mes")
    ingresos = ui.editor("ingresos", num_rows="dynamic", hide_index=True, column_config={
        "Concepto": st.column_config.TextColumn("Concepto", required=True, width="medium"),
        "Monto": st.column_config.NumberColumn("Monto (C$)", min_value=0.0, format="accounting", required=True),
    })
    c1, c2 = st.columns(2)
    with c1:
        ui.entrada("Ahorro planificado (C$)", "pp_ahorro", min_value=0.0, step=500.0, format="%.2f",
                   help="Monto que decide apartar este mes para ahorro.")
    with c2:
        meta = ui.entrada("Meta de ahorro (% del ingreso)", "pp_meta", min_value=0, max_value=100, step=5)
with der:
    st.markdown("##### Gastos del mes")
    gastos = ui.editor("gastos", num_rows="dynamic", hide_index=True, height=380, column_config={
        "Categoría": st.column_config.SelectboxColumn("Categoría", options=datos.CATEGORIAS_GASTO, required=True),
        "Descripción": st.column_config.TextColumn("Descripción", width="medium"),
        "Monto": st.column_config.NumberColumn("Monto (C$)", min_value=0.0, format="accounting", required=True),
        "Tipo": st.column_config.SelectboxColumn("Tipo", options=["Necesidad", "Deseo"], required=True,
                                                 help="Necesidad: gasto indispensable. Deseo: gasto prescindible."),
    })

r = datos.personal()
cumple = (r["pct_ahorro"] or 0) >= meta / 100
ui.fila_kpis([
    ui.kpi("Total de ingresos", ui.cs(r["total_ingresos"]), "mensual"),
    ui.kpi("Total de gastos", ui.cs(r["total_gastos"]), f"{ui.pct(calc.dividir(r['total_gastos'], r['total_ingresos']), 1)} del ingreso"),
    ui.kpi("Capacidad de ahorro", ui.cs(r["capacidad_ahorro"]), f"{ui.pct(r['pct_ahorro'], 1)} del ingreso · meta {meta} %",
           "bueno" if cumple else "aceptable" if r["capacidad_ahorro"] > 0 else "critico"),
    ui.kpi("Saldo disponible", ui.cs(r["saldo_disponible"]), f"después de ahorrar {ui.cs(r['ahorro_planificado'])}",
           "bueno" if r["saldo_disponible"] >= 0 else "critico"),
])
st.write("")
ui.formula("<b>Capacidad de ahorro</b> = Total ingresos − Total gastos &nbsp;·&nbsp; <b>% de ahorro</b> = Capacidad de ahorro ÷ "
           "Total ingresos &nbsp;·&nbsp; <b>Saldo disponible</b> = Total ingresos − Total gastos − Ahorro planificado"
           "<br><span class='note'>Código: <code>gfo/calculos.py → presupuesto_personal()</code></span>")
st.write("")

g1, g2 = st.columns([1.3, 1])
with g1:
    cat = r["por_categoria"].iloc[::-1]
    fig = ui.figura("Gastos por categoría", 360, leyenda=False)
    ui.barras(fig, cat["Categoría"], cat["Monto"], "Gasto", ui.SERIES[0], horizontal=True,
              texto=[f"{ui.cs(m, 0)} · {ui.pct(p, 1)}" for m, p in zip(cat["Monto"], cat["% del ingreso"])],
              hovertemplate="%{y}: C$ %{x:,.2f}<extra></extra>")
    fig.update_xaxes(showgrid=True, gridcolor=ui.GRID, range=[0, cat["Monto"].max() * 1.35 if len(cat) else 1])
    fig.update_yaxes(showgrid=False)
    ui.mostrar(fig)
with g2:
    ti = r["total_ingresos"] or 1
    partes = [("Necesidades", r["necesidades"], 50, ui.SERIES[0]), ("Deseos", r["deseos"], 30, ui.SERIES[1]),
              ("Ahorro", max(r["capacidad_ahorro"], 0), 20, ui.SERIES[2])]
    fig = ui.figura("Distribución del ingreso vs. regla 50/30/20", 360)
    ui.barras(fig, [p[0] for p in partes], [p[1] / ti * 100 for p in partes], "Real", [p[3] for p in partes],
              texto=[f"{p[1] / ti * 100:.1f} %" for p in partes], hovertemplate="%{x}: %{y:.2f} % del ingreso<extra></extra>",
              showlegend=False)
    fig.add_scatter(x=[p[0] for p in partes], y=[p[2] for p in partes], mode="markers", name="Referencia 50/30/20",
                    marker=dict(symbol="line-ew", size=38, line=dict(width=2.5, color=ui.INK)),
                    hovertemplate="%{x} recomendado: %{y} %<extra></extra>")
    fig.update_yaxes(ticksuffix=" %")
    ui.mostrar(fig)

st.markdown("##### Diagnóstico")
mensajes = []
if r["capacidad_ahorro"] < 0:
    mensajes.append(("critico", f"Los gastos superan los ingresos en {ui.cs(-r['capacidad_ahorro'])}. Reduzca gastos de tipo «Deseo»."))
elif cumple:
    mensajes.append(("bueno", f"Cumple la meta de ahorro: ahorra {ui.pct(r['pct_ahorro'], 1)} de su ingreso (meta {meta} %)."))
else:
    falta = meta / 100 * r["total_ingresos"] - r["capacidad_ahorro"]
    mensajes.append(("aceptable", f"Le faltan {ui.cs(falta)} al mes para alcanzar la meta de ahorro del {meta} %."))
if r["saldo_disponible"] < 0:
    mensajes.append(("critico", f"El ahorro planificado ({ui.cs(r['ahorro_planificado'])}) supera su capacidad de ahorro: ajústelo a {ui.cs(max(r['capacidad_ahorro'], 0))} o menos."))
if (r["pct_necesidades"] or 0) > 0.5:
    mensajes.append(("aceptable", f"Las necesidades representan {ui.pct(r['pct_necesidades'], 1)} del ingreso (referencia: 50 %)."))
if (r["pct_deseos"] or 0) > 0.3:
    mensajes.append(("aceptable", f"Los deseos representan {ui.pct(r['pct_deseos'], 1)} del ingreso (referencia: 30 %)."))
if len(r["por_categoria"]):
    mayor = r["por_categoria"].iloc[0]
    mensajes.append(("info", f"La categoría con mayor gasto es {mayor['Categoría']} ({ui.cs(mayor['Monto'])}, {ui.pct(mayor['% del ingreso'], 1)} del ingreso)."))
st.markdown("".join(f"<div style='margin:.35rem 0'>{ui.chip(e)} <span class='note' style='color:#0b0b0b'>{t}</span></div>"
                    for e, t in mensajes), unsafe_allow_html=True)

with st.expander("Proyección del ahorro acumulado a 12 meses", icon=":material/savings:"):
    meses = np.arange(1, 13)
    fig = ui.figura("", 300, leyenda=False)
    ui.barras(fig, [f"Mes {m}" for m in meses], r["ahorro_planificado"] * meses, "Ahorro acumulado", ui.SERIES[2],
              hovertemplate="%{x}: C$ %{y:,.2f}<extra></extra>")
    ui.mostrar(fig)
    st.caption(ui.md(f"Ahorrando {ui.cs(r['ahorro_planificado'])} cada mes, en un año acumularía {ui.cs(r['ahorro_planificado'] * 12)} "
               "(sin considerar intereses)."))
