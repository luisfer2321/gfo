"""Módulo 6 · Planeación y presupuestos (presupuesto maestro de operación y de caja)."""

import pandas as pd
import streamlit as st

from gfo import datos, ui

ui.encabezado("Planeación y presupuestos",
              "Presupuesto maestro trimestral: ventas, cobros, compras, pagos, costo de bienes vendidos, gastos de "
              "operación y presupuesto de caja con saldo mínimo y financiamiento. Los saldos iniciales se toman del "
              "último Balance General registrado.", "Unidad 3 · Módulo 6")

ultimo = datos.periodos()[-1]
b = datos.cuentas_periodo(ultimo)
P = datos.params()

with st.expander("Supuestos de planificación", icon=":material/tune:", expanded=True):
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        ui.entrada("Precio de venta unitario (C$)", "pm_precio", min_value=0.0, step=5.0, format="%.2f")
        ui.entrada("Ventas al contado (%)", "pm_contado", min_value=0, max_value=100, step=5,
                   help="El resto se cobra en el trimestre siguiente.")
        ui.entrada("Saldo mínimo de caja (C$)", "pm_saldo_min", min_value=0.0, step=10_000.0, format="%.2f")
    with c2:
        ui.entrada("Costo unitario de compra (C$)", "pm_costo", min_value=0.01, step=5.0, format="%.2f")
        ui.entrada("Compras al contado (%)", "pm_compras_contado", min_value=0, max_value=100, step=5,
                   help="El resto se paga en el trimestre siguiente.")
        ui.entrada("Intereses anuales (C$)", "pm_intereses", min_value=0.0, step=10_000.0, format="%.2f")
    with c3:
        ui.entrada("Inventario final deseado (% ventas del trimestre siguiente)", "pm_inv_final", min_value=0, max_value=200, step=5)
        ui.entrada("Unidades a vender el T1 del año siguiente", "pm_unidades_sig", min_value=0.0, step=100.0, format="%.0f")
        ui.entrada("Gastos de venta (% de las ventas)", "pm_gastos_venta", min_value=0.0, max_value=100.0, step=0.5, format="%.2f")
    with c4:
        ui.entrada("Gastos de administración por trimestre (C$)", "pm_admin_trim", min_value=0.0, step=5_000.0, format="%.2f")
        ui.entrada("Depreciación por trimestre (C$)", "pm_dep_trim", min_value=0.0, step=5_000.0, format="%.2f")
        st.markdown(f"<div class='note' style='margin-top:.6rem'>Saldos iniciales del Balance <b>{ultimo}</b>:<br>"
                    f"Efectivo {ui.cs(b['efectivo'])}<br>Cuentas por cobrar {ui.cs(b['cuentas_cobrar'])}<br>"
                    f"Inventario {ui.cs(b['inventarios'])}<br>Cuentas por pagar {ui.cs(b['cuentas_pagar'])}</div>",
                    unsafe_allow_html=True)
    st.markdown("**Datos por trimestre**")
    ui.editor("trimestres", hide_index=True, column_config={
        "Trimestre": st.column_config.TextColumn("Trimestre", disabled=True),
        "Unidades": st.column_config.NumberColumn("Unidades a vender", min_value=0, format="%d"),
        "Inversiones": st.column_config.NumberColumn("Inversiones en activo fijo (C$)", min_value=0.0, format="accounting"),
        "Dividendos": st.column_config.NumberColumn("Dividendos a pagar (C$)", min_value=0.0, format="accounting"),
    })

pm = datos.presupuesto()
er = pm["er_proforma"]
caja = pm["caja"]

ui.fila_kpis([
    ui.kpi("Ventas presupuestadas", ui.corto(er["ventas"]), f"{ui.num(pm['ventas'].loc['Unidades a vender', 'Total'])} unidades"),
    ui.kpi("Total cobros", ui.corto(caja.loc["(+) Cobros a clientes", "Total"]), "entradas de efectivo"),
    ui.kpi("Compras", ui.corto(pm["compras"].loc["Compras (C$)", "Total"]), f"{ui.num(pm['compras'].loc['(=) Unidades a comprar', 'Total'])} unidades"),
    ui.kpi("Financiamiento requerido", ui.corto(max(caja.loc["Financiamiento (+) / pago (−)", pm["trimestres"]].max(), 0)),
           "máximo en un trimestre", "aceptable" if caja.loc["Financiamiento (+) / pago (−)", pm["trimestres"]].max() > 0 else "bueno"),
    ui.kpi("Saldo final de caja", ui.corto(pm["saldos"][-1]), f"al cierre de {pm['trimestres'][-1]}"),
])
st.write("")


def mostrar_tabla(df: pd.DataFrame, enteros: tuple = ()) -> None:
    filas = []
    for idx, fila in df.iterrows():
        estilo = "total" if idx.startswith(("Total", "(=) Costo", "Saldo final")) else "sub" if idx.startswith("(=)") else ""
        if idx in enteros:
            filas.append((idx, [ui.num(v, 2) if pd.notna(v) else "" for v in fila], estilo))
        else:
            filas.append((idx, [None if pd.isna(v) else v for v in fila], estilo))
    ui.tabla_estado(filas, list(df.columns))


tabs = st.tabs(["Ventas", "Cobros", "Compras", "Pagos", "Costo de bienes vendidos", "Gastos de operación", "Presupuesto de caja"])
with tabs[0]:
    mostrar_tabla(pm["ventas"], ("Unidades a vender",))
    ui.formula("<b>Ventas</b> = Unidades a vender × Precio de venta")
with tabs[1]:
    mostrar_tabla(pm["cobros"])
    ui.formula(f"<b>Cobros del trimestre</b> = Ventas del trimestre × {P['pm_contado']} % + Ventas del trimestre anterior × "
               f"{100 - P['pm_contado']} %. En T1 se cobran las cuentas por cobrar iniciales.")
with tabs[2]:
    mostrar_tabla(pm["compras"], ("Unidades a vender", "(+) Inventario final deseado", "(=) Necesidad total",
                                  "(−) Inventario inicial", "(=) Unidades a comprar"))
    ui.formula("<b>Unidades a comprar</b> = Unidades a vender + Inventario final deseado − Inventario inicial<br>"
               f"Inventario inicial T1 = Inventario del balance ÷ Costo unitario = {ui.cs(b['inventarios'])} ÷ "
               f"{ui.cs(P['pm_costo'])} = {ui.num(b['inventarios'] / P['pm_costo'], 2)} unidades")
    inv = datos.inventario()
    if len(inv["alertas"]):
        st.warning(ui.md(f"**Integración con el control de inventario:** {len(inv['alertas'])} producto(s) están en o por "
                   f"debajo del stock mínimo. Considere incluir su reposición en las compras del próximo trimestre "
                   f"(costo estimado {ui.cs(inv['costo_reposicion'])})."), icon=":material/inventory_2:")
        st.dataframe(inv["alertas"][["Código", "Producto", "Existencia final", "Stock mínimo", "Cantidad sugerida",
                                     "Costo unitario"]].assign(**{"Costo de reposición": lambda d: (d["Cantidad sugerida"] * d["Costo unitario"]).map(ui.cs)}),
                     hide_index=True)
with tabs[3]:
    mostrar_tabla(pm["pagos"])
    ui.formula(f"<b>Pagos del trimestre</b> = Compras del trimestre × {P['pm_compras_contado']} % + Compras del trimestre "
               f"anterior × {100 - P['pm_compras_contado']} %. En T1 se pagan las cuentas por pagar iniciales.")
with tabs[4]:
    mostrar_tabla(pm["cbv"])
    ui.formula("<b>Costo de bienes vendidos</b> = Inventario inicial + Compras − Inventario final")
with tabs[5]:
    mostrar_tabla(pm["gastos"])
    ui.formula(f"<b>Gastos de venta</b> = Ventas × {ui.num(P['pm_gastos_venta'], 2)} % (variables) · "
               "<b>Gastos de administración</b> y <b>depreciación</b> son fijos por trimestre.")
with tabs[6]:
    mostrar_tabla(caja)
    ui.formula("<b>Saldo antes de financiamiento</b> = Saldo inicial + Cobros − Egresos. "
               f"Si es menor que el saldo mínimo ({ui.cs(P['pm_saldo_min'])}) se solicita un préstamo de corto plazo por la "
               "diferencia; cuando hay excedente se abona al préstamo. Los impuestos e intereses se distribuyen en partes "
               "iguales. <br><span class='note'>Código: <code>gfo/calculos.py → presupuesto_maestro()</code></span>")

st.write("")
g1, g2 = st.columns(2)
with g1:
    fig = ui.figura("Cobros vs. egresos por trimestre", 340)
    ui.barras(fig, pm["trimestres"], caja.loc["(+) Cobros a clientes", pm["trimestres"]], "Cobros", ui.SERIES[0],
              hovertemplate="%{x} cobros: C$ %{y:,.2f}<extra></extra>")
    ui.barras(fig, pm["trimestres"], caja.loc["Total egresos", pm["trimestres"]], "Egresos", ui.SERIES[1],
              hovertemplate="%{x} egresos: C$ %{y:,.2f}<extra></extra>")
    fig.update_layout(barmode="group")
    ui.mostrar(fig)
with g2:
    fig = ui.figura("Saldo de efectivo proyectado", 340)
    antes = caja.loc["Saldo antes de financiamiento", pm["trimestres"]]
    fig.add_scatter(x=pm["trimestres"], y=antes, name="Antes de financiamiento", mode="lines+markers",
                    line=dict(color=ui.SERIES[1], width=2), marker=dict(size=9, line=dict(color="#fff", width=2)),
                    hovertemplate="%{x}: C$ %{y:,.2f}<extra></extra>")
    fig.add_scatter(x=pm["trimestres"], y=pm["saldos"], name="Saldo final", mode="lines+markers+text",
                    line=dict(color=ui.SERIES[0], width=2.5), marker=dict(size=9, line=dict(color="#fff", width=2)),
                    text=[ui.corto(v) for v in pm["saldos"]], textposition="top center", textfont=dict(color=ui.INK2),
                    hovertemplate="%{x}: C$ %{y:,.2f}<extra></extra>")
    ui.linea_referencia(fig, pm["trimestres"], P["pm_saldo_min"], "Saldo mínimo")
    fig.update_xaxes(range=[-0.4, len(pm["trimestres"]) - 0.6])
    ui.mostrar(fig)

fin = caja.loc["Financiamiento (+) / pago (−)", pm["trimestres"]]
if fin.max() > 0:
    t = fin.idxmax()
    st.info(ui.md(f"En **{t}** el efectivo cae por debajo del saldo mínimo y se requieren {ui.cs(fin.max())} de financiamiento "
            f"de corto plazo. Deuda nueva pendiente al cierre del año: {ui.cs(pm['deuda_nueva'])}."), icon=":material/lightbulb:")
else:
    st.success("El efectivo se mantiene por encima del saldo mínimo durante todo el año; no se requiere financiamiento.",
               icon=":material/check_circle:")
