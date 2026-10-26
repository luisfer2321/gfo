"""Módulo 3 · Punto de equilibrio y relación Costo-Volumen-Utilidad (C-V-U)."""

import numpy as np
import pandas as pd
import streamlit as st

from gfo import calculos as calc
from gfo import datos, ui

ui.encabezado("Punto de equilibrio y C-V-U",
              "Calcule el margen de contribución, el punto de equilibrio en unidades y en córdobas, el margen de "
              "seguridad y simule cambios en el precio, el costo variable, los costos fijos o el volumen.",
              "Unidad 2 · Módulo 3")

P = datos.params()
ultimo = datos.periodos()[-1]

with st.container(border=True):
    origen = ui.selector("Origen de los datos", "pe_origen", ["Estados financieros", "Manual"])
    if origen == "Estados financieros":
        c1, c2 = st.columns([1, 2], vertical_alignment="bottom")
        with c1:
            ui.entrada("Precio de venta promedio por unidad (C$)", "pe_precio_ef", min_value=0.01, step=5.0, format="%.2f")
        b = datos.cvu_base()
        c2.markdown(
            f"<div class='note'>Tomado del Estado de Resultados <b>{ultimo}</b>: "
            f"unidades = Ventas ÷ Precio = <b>{ui.num(b['unidades'], 2)}</b> · "
            f"costo variable unitario = (Costo de ventas + Gastos de venta) ÷ Unidades = <b>{ui.cs(b['cv_unitario'])}</b> · "
            f"costos fijos = Gastos de administración + Depreciación = <b>{ui.cs(b['costos_fijos'])}</b></div>",
            unsafe_allow_html=True)
    else:
        # Al pasar de "Estados financieros" a "Manual" se parte de los mismos datos, para que el
        # resultado solo cambie cuando el usuario modifique algún valor.
        if P.get("pe_origen_previo") == "Estados financieros":
            b0 = calc.cvu_desde_estados(datos.cuentas_periodo(ultimo), P["pe_precio_ef"])
            P.update(pe_precio=b0["precio"], pe_cvu=b0["cv_unitario"], pe_cf=b0["costos_fijos"], pe_unidades=b0["unidades"])
            for k in ("pe_precio", "pe_cvu", "pe_cf", "pe_unidades"):
                st.session_state.pop(f"w_{k}_{st.session_state.version}", None)
        st.caption(ui.md(f"Los valores iniciales vienen del Estado de Resultados {ultimo}. Modifíquelos para simular "
                         "otro producto o escenario."))
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            ui.entrada("Precio de venta unitario (C$)", "pe_precio", min_value=0.01, step=5.0, format="%.2f")
        with c2:
            ui.entrada("Costo variable unitario (C$)", "pe_cvu", min_value=0.0, step=5.0, format="%.2f")
        with c3:
            ui.entrada("Costos fijos totales (C$)", "pe_cf", min_value=0.0, step=10_000.0, format="%.2f")
        with c4:
            ui.entrada("Unidades a vender", "pe_unidades", min_value=0.0, step=100.0, format="%.0f")
    P["pe_origen_previo"] = origen
    b = datos.cvu_base()

r = calc.cvu(b["precio"], b["cv_unitario"], b["costos_fijos"], b["unidades"])

if r["mcu"] <= 0:
    st.error("El precio debe ser mayor que el costo variable unitario: con margen de contribución cero o negativo "
             "no existe punto de equilibrio.", icon=":material/error:")
    st.stop()

ui.fila_kpis([
    ui.kpi("Margen de contribución unitario", ui.cs(r["mcu"]), f"Razón de MC: {ui.pct(r['rmc'])}"),
    ui.kpi("Punto de equilibrio", f"{ui.num(r['pe_unidades'], 2)} u", "unidades"),
    ui.kpi("Punto de equilibrio", ui.corto(r["pe_monetario"]), ui.cs(r["pe_monetario"])),
    ui.kpi("Utilidad operativa", ui.corto(r["utilidad"]), f"con {ui.num(r['unidades'])} unidades",
           "bueno" if r["utilidad"] > 0 else "critico"),
    ui.kpi("Margen de seguridad", ui.pct(r["margen_seguridad_pct"]), f"{ui.num(r['margen_seguridad_u'], 2)} unidades",
           "bueno" if (r["margen_seguridad_pct"] or 0) >= 0.2 else "aceptable" if (r["margen_seguridad_pct"] or 0) > 0 else "critico"),
])
st.write("")

t1, t2, t3 = st.tabs([":material/show_chart: Gráfica de equilibrio", ":material/tune: Análisis de escenarios",
                      ":material/flag: Utilidad deseada"])

with t1:
    g, txt = st.columns([2.2, 1])
    with g:
        maximo = max(r["unidades"], r["pe_unidades"]) * 1.35
        q = np.linspace(0, maximo, 120)
        ingresos = q * r["precio"]
        costos = r["costos_fijos"] + q * r["cv_unitario"]
        fig = ui.figura("Ingresos vs. costos totales", 430)
        fig.add_scatter(x=q, y=np.minimum(ingresos, costos), mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip")
        fig.add_scatter(x=q, y=np.maximum(ingresos, costos), mode="lines", line=dict(width=0), fill="tonexty",
                        fillcolor="rgba(42,120,214,0.07)", showlegend=False, hoverinfo="skip")
        fig.add_scatter(x=q, y=ingresos, name="Ingresos totales", mode="lines", line=dict(color=ui.SERIES[0], width=2.5),
                        hovertemplate="%{x:,.0f} u<br>Ingresos: C$ %{y:,.2f}<extra></extra>")
        fig.add_scatter(x=q, y=costos, name="Costos totales", mode="lines", line=dict(color=ui.SERIES[1], width=2.5),
                        hovertemplate="%{x:,.0f} u<br>Costos totales: C$ %{y:,.2f}<extra></extra>")
        fig.add_scatter(x=q, y=[r["costos_fijos"]] * len(q), name="Costos fijos", mode="lines",
                        line=dict(color=ui.MUTED, width=1.5), hovertemplate="Costos fijos: C$ %{y:,.2f}<extra></extra>")
        fig.add_scatter(x=[r["pe_unidades"]], y=[r["pe_monetario"]], mode="markers+text", name="Punto de equilibrio",
                        marker=dict(size=13, color="#0d366b", line=dict(color="#fff", width=2)),
                        text=[f"PE: {ui.num(r['pe_unidades'])} u · {ui.corto(r['pe_monetario'])}"], textposition="top left",
                        textfont=dict(color=ui.INK, size=12),
                        hovertemplate="Punto de equilibrio<br>%{x:,.2f} u<br>C$ %{y:,.2f}<extra></extra>")
        fig.add_vline(x=r["unidades"], line=dict(color=ui.BASELINE, width=1))
        fig.add_annotation(x=r["unidades"], y=1, yref="paper", text=f"Ventas esperadas: {ui.num(r['unidades'])} u",
                           showarrow=False, xanchor="left", yanchor="top", xshift=4, font=dict(color=ui.INK2, size=11.5))
        fig.add_annotation(x=maximo * 0.97, y=ingresos[-1] * 0.85, xanchor="right", text="Zona de utilidad", showarrow=False,
                           font=dict(color="#006300", size=12))
        fig.add_annotation(x=maximo * 0.1, y=r["costos_fijos"] * 0.55, text="Zona de pérdida", showarrow=False,
                           font=dict(color="#b42828", size=12))
        fig.update_xaxes(title=dict(text="Unidades vendidas", font=dict(color=ui.MUTED)), separatethousands=True)
        fig.update_yaxes(title=dict(text="C$", font=dict(color=ui.MUTED)))
        fig.update_layout(hovermode="x unified", legend=dict(y=-0.2))
        ui.mostrar(fig)
    with txt:
        ui.formula(
            "<b>MCu</b> = Precio − CVu<br><b>RMC</b> = MCu ÷ Precio<br>"
            "<b>PE (u)</b> = CF ÷ MCu<br><b>PE (C$)</b> = CF ÷ RMC<br>"
            "<b>Utilidad</b> = Q × MCu − CF<br><b>Margen de seguridad</b> = (Q − PE) ÷ Q<br>"
            "<span class='note'>Código: <code>gfo/calculos.py → cvu()</code></span>")
        st.write("")
        st.markdown(ui.md(f"**Comprobación:** {ui.cs(r['costos_fijos'])} ÷ {ui.cs(r['mcu'])} = **{ui.num(r['pe_unidades'], 2)} unidades**. "
            f"En ese nivel las ventas ({ui.cs(r['pe_monetario'])}) cubren exactamente los costos fijos y variables."))
        st.markdown(ui.md(f"**Interpretación:** cada unidad vendida aporta {ui.cs(r['mcu'])} para cubrir costos fijos. "
            f"Las ventas esperadas pueden caer hasta un {ui.pct(r['margen_seguridad_pct'])} antes de generar pérdidas."))

with t2:
    st.markdown("Mueva los controles para simular cambios porcentuales respecto del escenario base.")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        dp = ui.deslizador("Cambio en el precio (%)", "esc_precio", min_value=-30, max_value=30, step=1)
    with c2:
        dcv = ui.deslizador("Cambio en el costo variable (%)", "esc_cv", min_value=-30, max_value=30, step=1)
    with c3:
        dcf = ui.deslizador("Cambio en costos fijos (%)", "esc_cf", min_value=-30, max_value=30, step=1)
    with c4:
        dq = ui.deslizador("Cambio en el volumen (%)", "esc_vol", min_value=-30, max_value=30, step=1)
    e = calc.escenario_cvu(r, dp / 100, dcv / 100, dcf / 100, dq / 100)
    filas = [("Precio de venta unitario", "precio", ui.cs), ("Costo variable unitario", "cv_unitario", ui.cs),
             ("Costos fijos", "costos_fijos", ui.cs), ("Unidades vendidas", "unidades", lambda v: ui.num(v, 2)),
             ("Margen de contribución unitario", "mcu", ui.cs), ("Razón de margen de contribución", "rmc", ui.pct),
             ("Punto de equilibrio (unidades)", "pe_unidades", lambda v: ui.num(v, 2)),
             ("Punto de equilibrio (C$)", "pe_monetario", ui.cs), ("Ventas totales", "ventas", ui.cs),
             ("Utilidad operativa", "utilidad", ui.cs), ("Margen de seguridad", "margen_seguridad_pct", ui.pct)]
    tabla = pd.DataFrame([{"Concepto": n, "Escenario base": f(r[k]), "Escenario simulado": f(e[k]),
                           "Cambio": ui.pct(calc.dividir(e[k] - r[k], r[k]), 1) if None not in (e[k], r[k]) else "N/D"}
                          for n, k, f in filas])
    izq, der = st.columns([1.3, 1])
    izq.dataframe(tabla, hide_index=True, height=422)
    with der:
        fig = ui.figura("Utilidad operativa", 250, leyenda=False)
        ui.barras(fig, ["Base", "Simulado"], [r["utilidad"], e["utilidad"]], "Utilidad",
                  [ui.SERIES[0], ui.SERIES[0] if e["utilidad"] >= 0 else ui.SERIES[7]],
                  texto=[ui.corto(r["utilidad"]), ui.corto(e["utilidad"])], hovertemplate="%{x}: C$ %{y:,.2f}<extra></extra>")
        ui.mostrar(fig)
        cambio = e["utilidad"] - r["utilidad"]
        if e["mcu"] <= 0:
            st.error("Con estos cambios el precio no cubre el costo variable: no hay punto de equilibrio.")
        else:
            st.info(ui.md(f"La utilidad {'aumenta' if cambio >= 0 else 'disminuye'} {ui.cs(abs(cambio))} "
                    f"({ui.pct(calc.dividir(cambio, abs(r['utilidad'])), 1)}) y el punto de equilibrio pasa de "
                    f"{ui.num(r['pe_unidades'])} a {ui.num(e['pe_unidades'])} unidades."), icon=":material/lightbulb:")
    st.markdown("##### Sensibilidad: efecto de un cambio de ±10 % en cada variable sobre la utilidad")
    sens = []
    for nombre, args in [("Precio", (0.1, 0, 0, 0)), ("Costo variable", (0, 0.1, 0, 0)),
                         ("Costos fijos", (0, 0, 0.1, 0)), ("Volumen", (0, 0, 0, 0.1))]:
        sube = calc.escenario_cvu(r, *args)["utilidad"] - r["utilidad"]
        baja = calc.escenario_cvu(r, *[-a for a in args])["utilidad"] - r["utilidad"]
        sens.append((nombre, sube, baja))
    fig = ui.figura("", 260)
    fig.add_bar(y=[s[0] for s in sens], x=[s[1] for s in sens], orientation="h", name="Variable +10 %",
                marker=dict(color=ui.SERIES[0], cornerradius=4, line=dict(color="#fff", width=2)),
                hovertemplate="%{y} +10 %: C$ %{x:,.2f}<extra></extra>")
    fig.add_bar(y=[s[0] for s in sens], x=[s[2] for s in sens], orientation="h", name="Variable −10 %",
                marker=dict(color=ui.SERIES[1], cornerradius=4, line=dict(color="#fff", width=2)),
                hovertemplate="%{y} −10 %: C$ %{x:,.2f}<extra></extra>")
    fig.update_layout(barmode="overlay", bargap=0.45)
    fig.update_xaxes(title=dict(text="Cambio en la utilidad operativa (C$)", font=dict(color=ui.MUTED)), showgrid=True, gridcolor=ui.GRID)
    ui.mostrar(fig)
    st.caption("El precio es la variable más sensible: un cambio en él afecta todas las unidades vendidas sin modificar los costos.")

with t3:
    c1, c2 = st.columns([1, 2])
    with c1:
        obj = ui.entrada("Utilidad operativa deseada (C$)", "pe_utilidad_obj", min_value=0.0, step=50_000.0, format="%.2f")
    u = calc.unidades_para_utilidad(r["precio"], r["cv_unitario"], r["costos_fijos"], obj)
    with c2:
        ui.formula("<b>Unidades necesarias</b> = (Costos fijos + Utilidad deseada) ÷ MCu"
                   f"<br>= ({ui.cs(r['costos_fijos'])} + {ui.cs(obj)}) ÷ {ui.cs(r['mcu'])} = <b>{ui.num(u, 2)} unidades</b>"
                   "<br><span class='note'>Código: <code>gfo/calculos.py → unidades_para_utilidad()</code></span>")
    ui.fila_kpis([
        ui.kpi("Unidades requeridas", ui.num(u, 2), "para lograr la utilidad deseada"),
        ui.kpi("Ventas requeridas", ui.cs(u * r["precio"]), "ingresos totales"),
        ui.kpi("Diferencia vs. ventas esperadas", f"{ui.num(u - r['unidades'], 2)} u",
               "unidades adicionales" if u > r["unidades"] else "ya se alcanza la meta",
               "aceptable" if u > r["unidades"] else "bueno"),
    ])
