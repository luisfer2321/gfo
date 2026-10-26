"""Módulo 2 · Análisis financiero: horizontal, vertical, razones financieras y sistema DuPont."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from gfo import calculos as calc
from gfo import datos, ui

ui.encabezado("Análisis financiero",
              "Compare períodos con el análisis horizontal, mida la estructura con el análisis vertical, "
              "evalúe liquidez, actividad, endeudamiento, rentabilidad y mercado con las razones financieras, "
              "y descomponga el ROE con el sistema DuPont.", "Unidad 2 · Módulo 2")

periodos = datos.periodos()
calc_p = {p: datos.periodo_calculado(p) for p in periodos}

c1, c2 = st.columns(2)
actual = c1.selectbox("Período de análisis", periodos, index=len(periodos) - 1)
anteriores = [p for p in periodos if p != actual]
base = c2.selectbox("Período de comparación (base)", anteriores, index=len(anteriores) - 1 if anteriores else None,
                    disabled=not anteriores, placeholder="Registre otro período para comparar")

LINEAS_BG = ([(k, n, "") for k, n, _ in datos.CUENTAS_BALANCE[:4]] + [("activo_corriente", datos.NOMBRES["activo_corriente"], "sub")]
             + [(k, n, "") for k, n, _ in datos.CUENTAS_BALANCE[4:6]] + [("activo_no_corriente", datos.NOMBRES["activo_no_corriente"], "sub"),
                                                                     ("activo_total", "TOTAL ACTIVO", "total")]
             + [(k, n, "") for k, n, _ in datos.CUENTAS_BALANCE[6:9]] + [("pasivo_corriente", datos.NOMBRES["pasivo_corriente"], "sub")]
             + [(k, n, "") for k, n, _ in datos.CUENTAS_BALANCE[9:10]] + [("pasivo_total", "TOTAL PASIVO", "sub")]
             + [(k, n, "") for k, n, _ in datos.CUENTAS_BALANCE[10:]] + [("patrimonio", "TOTAL PATRIMONIO", "sub"),
                                                                    ("pasivo_patrimonio", "TOTAL PASIVO + PATRIMONIO", "total")])
LINEAS_ER = [(k, datos.NOMBRES[k], e) for k, e in [
    ("ventas", ""), ("costo_ventas", ""), ("utilidad_bruta", "sub"), ("gastos_venta", ""), ("gastos_admin", ""),
    ("depreciacion", ""), ("uaii", "sub"), ("intereses", ""), ("otros_ingresos", ""), ("uai", "sub"), ("impuestos", ""), ("utilidad_neta", "total")]]

t_h, t_v, t_r, t_d = st.tabs([":material/compare_arrows: Análisis horizontal", ":material/stacked_bar_chart: Análisis vertical",
                              ":material/speed: Razones financieras", ":material/account_tree: Sistema DuPont"])

# ---------------------------------------------------------------- Horizontal
with t_h:
    if base is None:
        st.info("El análisis horizontal necesita al menos dos períodos. Agregue otro período en **Estados financieros**.")
    else:
        ui.formula(f"<b>Variación absoluta</b> = {actual} − {base} &nbsp;·&nbsp; <b>Variación relativa</b> = "
                   f"({actual} − {base}) ÷ {base} × 100 <br><span class='note'>Código: <code>gfo/calculos.py → analisis_horizontal()</code></span>")
        st.write("")
        for titulo, lineas in (("Balance General", LINEAS_BG), ("Estado de Resultados", LINEAS_ER)):
            claves = [k for k, _, _ in lineas]
            h = calc.analisis_horizontal(pd.Series({k: calc_p[base][k] for k in claves}),
                                         pd.Series({k: calc_p[actual][k] for k in claves}))
            st.markdown(f"##### {titulo}")
            ui.tabla_estado([(n, [h.loc[k, "base"], h.loc[k, "actual"], h.loc[k, "var_abs"], ui.pct(h.loc[k, "var_pct"])], e)
                             for k, n, e in lineas], [base, actual, "Variación C$", "Variación %"])
            st.write("")
        claves = ["ventas", "costo_ventas", "utilidad_bruta", "uaii", "utilidad_neta", "efectivo", "cuentas_cobrar",
                  "inventarios", "activo_total", "pasivo_total", "patrimonio"]
        h = calc.analisis_horizontal(pd.Series({k: calc_p[base][k] for k in claves}),
                                     pd.Series({k: calc_p[actual][k] for k in claves})).dropna()
        h = h.iloc[::-1]
        fig = ui.figura(f"Variación relativa {base} → {actual}", 440, leyenda=False)
        colores = [ui.SERIES[0] if v >= 0 else ui.SERIES[7] for v in h["var_pct"]]
        fig.add_bar(y=[datos.NOMBRES[k] for k in h.index], x=h["var_pct"] * 100, orientation="h",
                    marker=dict(color=colores, line=dict(color="#fff", width=2), cornerradius=4),
                    text=[ui.pct(v, 1) for v in h["var_pct"]], textposition="outside", cliponaxis=False,
                    textfont=dict(color=ui.INK2), customdata=h["var_abs"],
                    hovertemplate="%{y}<br>Variación: %{x:.2f} %<br>C$ %{customdata:,.2f}<extra></extra>")
        fig.update_xaxes(ticksuffix=" %", showgrid=True, gridcolor=ui.GRID)
        fig.update_yaxes(showgrid=False)
        ui.mostrar(fig)
        crec_v = h.loc["ventas", "var_pct"] if "ventas" in h.index else None
        crec_un = h.loc["utilidad_neta", "var_pct"] if "utilidad_neta" in h.index else None
        if crec_v is not None and crec_un is not None:
            msg = (f"Las ventas variaron {ui.pct(crec_v)} y la utilidad neta {ui.pct(crec_un)}. ")
            msg += ("La utilidad creció más rápido que las ventas: los costos y gastos se controlaron mejor "
                    "(efecto del apalancamiento operativo y financiero)." if crec_un > crec_v else
                    "La utilidad creció menos que las ventas: los costos o gastos aumentaron proporcionalmente más.")
            st.info(msg, icon=":material/lightbulb:")

# ---------------------------------------------------------------- Vertical
with t_v:
    ui.formula("<b>Balance General:</b> % = Cuenta ÷ Activo total × 100 &nbsp;·&nbsp; "
               "<b>Estado de Resultados:</b> % = Cuenta ÷ Ventas netas × 100"
               "<br><span class='note'>Código: <code>gfo/calculos.py → analisis_vertical()</code></span>")
    st.write("")
    cols = st.columns(2)
    for col, (titulo, lineas, total) in zip(cols, (("Balance General (% del activo total)", LINEAS_BG, "activo_total"),
                                                   ("Estado de Resultados (% de las ventas)", LINEAS_ER, "ventas"))):
        with col:
            st.markdown(f"##### {titulo}")
            claves = [k for k, _, _ in lineas]
            vals = {p: calc.analisis_vertical(pd.Series({k: calc_p[p][k] for k in claves}), calc_p[p][total]) for p in periodos}
            ui.tabla_estado([(n, [ui.pct(vals[p][k]) for p in periodos], e) for k, n, e in lineas], periodos)
    st.write("")
    g1, g2 = st.columns(2)
    with g1:
        fig = ui.figura("Composición del activo", 380)
        for i, (k, n, _) in enumerate(datos.CUENTAS_BALANCE[:6]):
            y = [calc_p[p][k] / calc_p[p]["activo_total"] * 100 if calc_p[p]["activo_total"] else 0 for p in periodos]
            fig.add_bar(x=periodos, y=y, name=n, marker=dict(color=ui.SERIES[i], line=dict(color="#fff", width=2)),
                        hovertemplate=n + " %{x}: %{y:.2f} %<extra></extra>")
        fig.update_layout(barmode="stack", legend=dict(y=-0.15, yanchor="top", x=0, xanchor="left"), margin=dict(b=110))
        fig.update_yaxes(ticksuffix=" %", range=[0, 100])
        ui.mostrar(fig)
    with g2:
        d = calc_p[actual]
        pasos = [("Ventas", d["ventas"], "absolute"), ("Costo de ventas", -d["costo_ventas"], "relative"),
                 ("Gastos de venta", -d["gastos_venta"], "relative"), ("Gastos admin.", -d["gastos_admin"], "relative"),
                 ("Depreciación", -d["depreciacion"], "relative"), ("Intereses", -d["intereses"], "relative"),
                 ("Otros ingresos/gastos", d["otros_ingresos"], "relative"),
                 ("Impuestos", -d["impuestos"], "relative"), ("Utilidad neta", d["utilidad_neta"], "total")]
        fig = ui.figura(f"De las ventas a la utilidad neta · {actual}", 380, leyenda=False)
        fig.add_trace(go.Waterfall(
            x=[p[0] for p in pasos], y=[p[1] if p[2] != "total" else 0 for p in pasos], measure=[p[2] for p in pasos],
            text=[ui.pct(abs(p[1]) / d["ventas"], 1) if d["ventas"] else "" for p in pasos], textposition="outside",
            textfont=dict(color=ui.INK2), cliponaxis=False, constraintext="none",
            increasing=dict(marker=dict(color=ui.SERIES[0])), decreasing=dict(marker=dict(color=ui.SERIES[7])),
            totals=dict(marker=dict(color="#104281")), connector=dict(line=dict(color=ui.BASELINE, width=1)),
            hovertemplate="%{x}: C$ %{y:,.2f}<extra></extra>"))
        ui.mostrar(fig)

# ---------------------------------------------------------------- Razones
with t_r:
    r_act = calc.razones_financieras(datos.cuentas_periodo(actual))
    r_base = calc.razones_financieras(datos.cuentas_periodo(base)) if base else None
    todas = {p: calc.razones_financieras(datos.cuentas_periodo(p)) for p in periodos}

    categorias = ["Liquidez", "Actividad", "Endeudamiento", "Rentabilidad", "Mercado"]
    resumen = {"bueno": 0, "aceptable": 0, "critico": 0}
    for k in r_act:
        e = calc.evaluar_razon(k, r_act[k])
        if e in resumen:
            resumen[e] += 1
    ui.fila_kpis([
        ui.kpi("Razón corriente", ui.veces(r_act["razon_corriente"]), "Liquidez", calc.evaluar_razon("razon_corriente", r_act["razon_corriente"])),
        ui.kpi("Razón de endeudamiento", ui.pct(r_act["razon_deuda"]), "Endeudamiento", calc.evaluar_razon("razon_deuda", r_act["razon_deuda"])),
        ui.kpi("ROE", ui.pct(r_act["roe"]), "Rentabilidad", calc.evaluar_razon("roe", r_act["roe"])),
        ui.kpi("Diagnóstico", f"{resumen['bueno']} favorables", f"{resumen['aceptable']} aceptables · {resumen['critico']} desfavorables"),
    ])
    st.write("")
    cat = st.segmented_control("Categoría", categorias, default="Liquidez", required=True, key="cat_razones")
    claves = [k for k, info in calc.INFO_RAZON.items() if info["categoria"] == cat]

    izq, der = st.columns([1.25, 1])
    with izq:
        for k in claves:
            info = calc.INFO_RAZON[k]
            v = r_act[k]
            estado = calc.evaluar_razon(k, v)
            previo = (f"<div>{base}<b>{ui.por_unidad(r_base[k], info['unidad'])}</b></div>" if r_base else "")
            st.markdown(
                f'<div class="ratio"><div class="top"><div><div class="name">{info["nombre"]}</div>'
                f'<div class="formula">{info["formula"]}</div></div>{ui.chip(estado)}</div>'
                f'<div class="vals"><div>{actual}<b>{ui.por_unidad(v, info["unidad"])}</b></div>{previo}</div>'
                f'<div class="txt">{calc.interpretar_razon(k, v)}</div></div>', unsafe_allow_html=True)
    with der:
        unidades = {}
        for k in claves:
            unidades.setdefault(calc.INFO_RAZON[k]["unidad"], []).append(k)
        for unidad, ks in unidades.items():
            fig = ui.figura(f"{cat} · {unidad}", 300)
            for i, p in enumerate(periodos):
                factor = 100 if unidad == "%" else 1
                ys = [todas[p][k] * factor if todas[p][k] is not None else None for k in ks]
                ui.barras(fig, [calc.INFO_RAZON[k]["nombre"] for k in ks], ys, p, ui.SERIES[i % 8],
                          hovertemplate="%{x}<br>" + p + ": %{y:,.2f}" + (" %" if unidad == "%" else "") + "<extra></extra>")
            fig.update_layout(barmode="group")
            if unidad == "%":
                fig.update_yaxes(ticksuffix=" %")
            ui.mostrar(fig)
        st.caption("Los criterios (favorable / aceptable / desfavorable) son referencias académicas generales; "
                   "lo ideal es compararlos con el promedio de la industria. Las razones usan saldos al cierre.")

    with st.expander("Ver tabla completa de razones", icon=":material/table:"):
        tabla = pd.DataFrame([{"Categoría": i["categoria"], "Razón": i["nombre"], "Fórmula": i["formula"],
                               **{p: ui.por_unidad(todas[p][k], i["unidad"]) for p in periodos},
                               "Evaluación": ui.ESTADO_TXT[calc.evaluar_razon(k, r_act[k])]}
                              for k, i in calc.INFO_RAZON.items()])
        st.dataframe(tabla, hide_index=True)
        st.download_button("Descargar CSV", tabla.to_csv(index=False).encode("utf-8-sig"), "razones_financieras.csv",
                           "text/csv", icon=":material/download:")

# ---------------------------------------------------------------- DuPont
with t_d:
    dp = {p: calc.dupont(datos.cuentas_periodo(p)) for p in periodos}
    a = dp[actual]
    ui.formula("<b>ROE</b> = Margen neto × Rotación de activos × Multiplicador del capital "
               "= (Utilidad neta ÷ Ventas) × (Ventas ÷ Activo total) × (Activo total ÷ Patrimonio)"
               "<br><b>ROA</b> = Margen neto × Rotación de activos"
               "<br><span class='note'>Código: <code>gfo/calculos.py → dupont()</code></span>")
    st.write("")
    caja = ('<div style="background:#fff;border:1px solid rgba(11,11,11,.09);border-radius:14px;padding:12px 10px;'
            'text-align:center;height:100%"><div style="color:#52514e;font-size:.78rem;font-weight:600">{t}</div>'
            '<div style="font-size:1.35rem;font-weight:750;color:#0b0b0b">{v}</div>'
            '<div style="color:#898781;font-size:.74rem">{s}</div></div>')
    op = '<div style="display:grid;place-items:center;height:100%;font-size:1.4rem;color:#898781;font-weight:700">{}</div>'
    cs = st.columns([1.2, .3, 1.2, .3, 1.2, .3, 1.2], vertical_alignment="center")
    cs[0].markdown(caja.format(t="Margen neto", v=ui.pct(a["margen_neto"]), s="Eficiencia en costos"), unsafe_allow_html=True)
    cs[1].markdown(op.format("×"), unsafe_allow_html=True)
    cs[2].markdown(caja.format(t="Rotación de activos", v=ui.veces(a["rotacion_activos"]), s="Eficiencia en uso de activos"), unsafe_allow_html=True)
    cs[3].markdown(op.format("×"), unsafe_allow_html=True)
    cs[4].markdown(caja.format(t="Multiplicador del capital", v=ui.veces(a["multiplicador_capital"]), s="Apalancamiento financiero"), unsafe_allow_html=True)
    cs[5].markdown(op.format("="), unsafe_allow_html=True)
    cs[6].markdown(caja.format(t=f"ROE {actual}", v=ui.pct(a["roe"]), s=f"ROA = {ui.pct(a['roa'])}").replace("#fff;", "#eef5fd;"), unsafe_allow_html=True)
    st.write("")
    g1, g2 = st.columns([1.3, 1])
    with g1:
        fig = ui.figura("Factores DuPont por período", 340)
        fig.update_layout(barmode="group")
        nombres = ["Margen neto (%)", "Rotación de activos (veces)", "Multiplicador (veces)", "ROE (%)"]
        for i, p in enumerate(periodos):
            d = dp[p]
            ys = [d["margen_neto"] * 100 if d["margen_neto"] is not None else None, d["rotacion_activos"],
                  d["multiplicador_capital"], d["roe"] * 100 if d["roe"] is not None else None]
            ui.barras(fig, nombres, ys, p, ui.SERIES[i % 8], hovertemplate="%{x}<br>" + p + ": %{y:,.2f}<extra></extra>")
        ui.mostrar(fig)
    with g2:
        if base:
            b = dp[base]
            st.markdown(f"##### ¿Qué explica el cambio del ROE {base} → {actual}?")
            filas = []
            for k, n in [("margen_neto", "Margen neto"), ("rotacion_activos", "Rotación de activos"),
                         ("multiplicador_capital", "Multiplicador del capital"), ("roe", "ROE")]:
                var = calc.dividir((a[k] or 0) - (b[k] or 0), b[k])
                filas.append({"Factor": n, base: (ui.pct(b[k]) if k in ("margen_neto", "roe") else ui.veces(b[k])),
                              actual: (ui.pct(a[k]) if k in ("margen_neto", "roe") else ui.veces(a[k])),
                              "Cambio": ui.pct(var, 1)})
            st.dataframe(pd.DataFrame(filas), hide_index=True)
            cambios = {n: calc.dividir((a[k] or 0) - (b[k] or 0), b[k]) or 0 for k, n in
                       [("margen_neto", "el margen neto"), ("rotacion_activos", "la rotación de activos"),
                        ("multiplicador_capital", "el apalancamiento (multiplicador)")]}
            principal = max(cambios, key=lambda n: abs(cambios[n]))
            direccion = "aumentó" if (a["roe"] or 0) >= (b["roe"] or 0) else "disminuyó"
            st.info(f"El ROE {direccion} de {ui.pct(b['roe'])} a {ui.pct(a['roe'])}. El factor que más cambió fue "
                    f"**{principal}** ({ui.pct(cambios[principal], 1)}).", icon=":material/lightbulb:")
        else:
            st.info("Registre otro período para comparar los factores DuPont.")
