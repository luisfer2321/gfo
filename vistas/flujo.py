"""Módulo 5 · Estado de flujo de efectivo (operación, inversión y financiamiento)."""

import plotly.graph_objects as go
import streamlit as st

from gfo import calculos as calc
from gfo import datos, ui

ui.encabezado("Flujo de efectivo",
              "Clasifique las entradas y salidas de efectivo en actividades de operación, inversión y "
              "financiamiento para obtener la variación neta y el saldo final de efectivo.", "Unidad 3 · Módulo 5")

periodos = datos.periodos()
t1, t2 = st.tabs([":material/link: Método indirecto (desde los estados financieros)",
                  ":material/edit_note: Registro de entradas y salidas"])


def cascada(titulo: str, inicial: float, fo: float, fi: float, ff: float, final: float):
    fig = ui.figura(titulo, 380, leyenda=False)
    fig.add_trace(go.Waterfall(
        x=["Saldo inicial", "Operación", "Inversión", "Financiamiento", "Saldo final"],
        measure=["absolute", "relative", "relative", "relative", "total"], y=[inicial, fo, fi, ff, 0],
        text=[ui.corto(v) for v in (inicial, fo, fi, ff, final)], textposition="outside", cliponaxis=False, constraintext="none",
        textfont=dict(color=ui.INK2), increasing=dict(marker=dict(color=ui.SERIES[0])),
        decreasing=dict(marker=dict(color=ui.SERIES[7])), totals=dict(marker=dict(color="#104281")),
        connector=dict(line=dict(color=ui.BASELINE, width=1)), hovertemplate="%{x}: C$ %{y:,.2f}<extra></extra>"))
    return fig


with t1:
    if len(periodos) < 2:
        st.info("El método indirecto necesita dos balances consecutivos. Agregue otro período en **Estados financieros**.")
    else:
        c1, _ = st.columns([1, 2])
        actual = c1.selectbox("Período", periodos[1:], index=len(periodos) - 2)
        anterior = periodos[periodos.index(actual) - 1]
        f = calc.flujo_efectivo_indirecto(datos.cuentas_periodo(anterior), datos.cuentas_periodo(actual))
        ui.fila_kpis([
            ui.kpi("Flujo de operación", ui.cs(f["flujo_operacion"]), "actividades principales", "bueno" if f["flujo_operacion"] > 0 else "critico"),
            ui.kpi("Flujo de inversión", ui.cs(f["flujo_inversion"]), "activos de largo plazo"),
            ui.kpi("Flujo de financiamiento", ui.cs(f["flujo_financiamiento"]), "deuda, capital y dividendos"),
            ui.kpi("Variación neta", ui.cs(f["variacion_neta"]), f"Saldo final: {ui.cs(f['saldo_final'])}"),
        ])
        st.write("")
        izq, der = st.columns([1.25, 1])
        with izq:
            filas = [("ACTIVIDADES DE OPERACIÓN", [], "grupo")] + [(n, [v], "") for n, v in f["operacion"]]
            filas += [("Flujo neto de operación", [f["flujo_operacion"]], "sub"), ("ACTIVIDADES DE INVERSIÓN", [], "grupo")]
            filas += [(n, [v], "") for n, v in f["inversion"]] + [("Flujo neto de inversión", [f["flujo_inversion"]], "sub")]
            filas += [("ACTIVIDADES DE FINANCIAMIENTO", [], "grupo")] + [(n, [v], "") for n, v in f["financiamiento"]]
            filas += [("Flujo neto de financiamiento", [f["flujo_financiamiento"]], "sub"),
                      ("Variación neta del efectivo", [f["variacion_neta"]], "sub"),
                      (f"(+) Efectivo al inicio ({anterior})", [f["saldo_inicial"]], ""),
                      (f"Efectivo al final ({actual})", [f["saldo_final"]], "total")]
            ui.tabla_estado(filas, [f"{anterior} → {actual}"])
        with der:
            ui.mostrar(cascada("Del saldo inicial al saldo final", f["saldo_inicial"], f["flujo_operacion"],
                               f["flujo_inversion"], f["flujo_financiamiento"], f["saldo_final"]))
            if f["conciliado"]:
                st.success(ui.md(f"Conciliado: el saldo final calculado coincide con el efectivo del Balance General {actual} "
                           f"({ui.cs(f['saldo_balance'])})."), icon=":material/check_circle:")
            else:
                st.warning(ui.md(f"El saldo calculado ({ui.cs(f['saldo_final'])}) no coincide con el efectivo del balance "
                           f"({ui.cs(f['saldo_balance'])}). Revise los dividendos y la variación de utilidades retenidas."),
                           icon=":material/warning:")
            ui.formula("<b>Operación</b> = Utilidad neta + Depreciación ± variaciones del capital de trabajo<br>"
                       "<b>Inversión</b> = −(Δ PPE neto + Depreciación) − Δ otros activos no corrientes<br>"
                       "<b>Financiamiento</b> = Δ préstamos + Δ capital − Dividendos<br>"
                       "<span class='note'>Código: <code>gfo/calculos.py → flujo_efectivo_indirecto()</code></span>")
        fo, un = f["flujo_operacion"], f["operacion"][0][1]
        st.info(ui.md(f"La operación generó {ui.cs(fo)}, equivalente a {ui.num(calc.dividir(fo, un), 2)} veces la utilidad neta. "
                + ("La empresa financia sus inversiones con recursos propios de la operación." if fo >= -f["flujo_inversion"]
                   else "Las inversiones superaron el efectivo de la operación y requirieron financiamiento.")),
                icon=":material/lightbulb:")

with t2:
    st.markdown("Registre cada movimiento de efectivo con su actividad y tipo. Puede agregar o eliminar filas.")
    c1, _ = st.columns([1, 2])
    with c1:
        inicial = ui.entrada("Saldo inicial de efectivo (C$)", "fd_saldo_inicial", step=10_000.0, format="%.2f")
    izq, der = st.columns([1.3, 1])
    with izq:
        mov = ui.editor("mov_caja", num_rows="dynamic", hide_index=True, height=420, column_config={
            "Concepto": st.column_config.TextColumn("Concepto", required=True, width="large"),
            "Actividad": st.column_config.SelectboxColumn("Actividad", options=calc.ACTIVIDADES, required=True),
            "Tipo": st.column_config.SelectboxColumn("Tipo", options=["Entrada", "Salida"], required=True),
            "Monto": st.column_config.NumberColumn("Monto (C$)", min_value=0.0, format="accounting", required=True),
        })
    r = calc.flujo_efectivo_directo(mov, inicial)
    with der:
        res = r["resumen"].copy()
        for c in ("Entradas", "Salidas", "Flujo neto"):
            res[c] = res[c].map(ui.cs)
        st.dataframe(res, hide_index=True)
        ui.fila_kpis([ui.kpi("Variación neta", ui.cs(r["variacion_neta"])), ui.kpi("Saldo final", ui.cs(r["saldo_final"]),
                      estado="bueno" if r["saldo_final"] >= 0 else "critico")])
        fl = r["resumen"].set_index("Actividad")["Flujo neto"]
        ui.mostrar(cascada("", r["saldo_inicial"], fl["Operación"], fl["Inversión"], fl["Financiamiento"], r["saldo_final"]),
                   key="cascada_directo")
    ui.formula("<b>Flujo por actividad</b> = Σ Entradas − Σ Salidas &nbsp;·&nbsp; <b>Saldo final</b> = Saldo inicial + "
               "Variación neta <br><span class='note'>Código: <code>gfo/calculos.py → flujo_efectivo_directo()</code></span>")
