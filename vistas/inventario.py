"""Aplicación complementaria · Control básico de inventario."""

import datetime as dt

import pandas as pd
import streamlit as st

from gfo import datos, ui

ui.encabezado("Control de inventario",
              "Registre productos y movimientos de entrada y salida para obtener la existencia final, el valor del "
              "inventario y las alertas de reposición cuando un producto llega a su stock mínimo.",
              "Aplicación práctica complementaria")

r = datos.inventario()
res = r["resumen"]

ui.fila_kpis([
    ui.kpi("Valor total del inventario", ui.cs(r["valor_total"]), f"{len(res)} productos"),
    ui.kpi("Unidades en existencia", ui.num(res["Existencia final"].sum() if len(res) else 0), "existencia final total"),
    ui.kpi("Productos por reponer", str(len(r["alertas"])), "en o bajo el stock mínimo",
           "critico" if len(r["alertas"]) else "bueno"),
    ui.kpi("Costo estimado de reposición", ui.cs(r["costo_reposicion"]), "hasta 2 × stock mínimo"),
])
st.write("")
for e in r["errores"]:
    st.error(e, icon=":material/error:")

t1, t2, t3 = st.tabs([":material/inventory: Existencias", ":material/swap_vert: Movimientos", ":material/history: Kárdex por producto"])

with t1:
    if len(r["alertas"]):
        st.warning("**Alerta de reposición:** " + ", ".join(f"{a['Producto']} ({ui.num(a['Existencia final'])} u; mínimo "
                   f"{ui.num(a['Stock mínimo'])})" for _, a in r["alertas"].iterrows()), icon=":material/notification_important:")
    vista = res.copy()
    st.dataframe(vista, hide_index=True, column_config={
        "Existencia inicial": st.column_config.NumberColumn(format="%d"),
        "Entradas": st.column_config.NumberColumn(format="%d"),
        "Salidas": st.column_config.NumberColumn(format="%d"),
        "Existencia final": st.column_config.NumberColumn(format="%d"),
        "Costo unitario": st.column_config.NumberColumn(format="accounting"),
        "Valor del inventario": st.column_config.NumberColumn(format="accounting"),
        "Stock mínimo": st.column_config.NumberColumn(format="%d"),
        "Cantidad sugerida": st.column_config.NumberColumn(format="%d"),
    })
    ui.formula("<b>Existencia final</b> = Existencia inicial + Entradas − Salidas &nbsp;·&nbsp; "
               "<b>Valor del inventario</b> = Existencia final × Costo unitario &nbsp;·&nbsp; "
               "<b>Alerta</b> si Existencia final ≤ Stock mínimo &nbsp;·&nbsp; <b>Cantidad sugerida</b> = 2 × Stock mínimo − Existencia final"
               "<br><span class='note'>Código: <code>gfo/calculos.py → control_inventario()</code></span>")
    st.write("")
    if len(res):
        g1, g2 = st.columns(2)
        with g1:
            fig = ui.figura("Existencia final vs. stock mínimo", 360)
            colores = [ui.ESTADO["critico"] if e == "Reponer" else ui.SERIES[0] for e in res["Estado"]]
            ui.barras(fig, res["Código"], res["Existencia final"], "Existencia final", colores,
                      customdata=res["Producto"], texto=[ui.num(v) for v in res["Existencia final"]],
                      hovertemplate="%{customdata}<br>Existencia: %{y:,.0f} u<extra></extra>")
            fig.add_scatter(x=res["Código"], y=res["Stock mínimo"], mode="markers", name="Stock mínimo",
                            marker=dict(symbol="line-ew", size=34, line=dict(width=2.5, color=ui.INK)),
                            hovertemplate="Stock mínimo: %{y:,.0f} u<extra></extra>")
            ui.mostrar(fig)
            st.caption("Las barras rojas indican productos que deben reponerse.")
        with g2:
            orden = res.sort_values("Valor del inventario")
            fig = ui.figura("Valor del inventario por producto", 360, leyenda=False)
            ui.barras(fig, orden["Producto"], orden["Valor del inventario"], "Valor", ui.SERIES[0], horizontal=True,
                      texto=[ui.corto(v) for v in orden["Valor del inventario"]], hovertemplate="%{y}: C$ %{x:,.2f}<extra></extra>")
            fig.update_xaxes(showgrid=True, gridcolor=ui.GRID, range=[0, orden["Valor del inventario"].max() * 1.3])
            fig.update_yaxes(showgrid=False)
            ui.mostrar(fig)

with t2:
    with st.form("nuevo_mov", clear_on_submit=True, border=True):
        st.markdown("**Registrar movimiento rápido**")
        productos = datos.tabla("productos").dropna(subset=["Código"])
        c1, c2, c3, c4, c5 = st.columns([1.1, 2, 1, 1, 2])
        fecha = c1.date_input("Fecha", dt.date.today(), format="DD/MM/YYYY")
        cod = c2.selectbox("Producto", productos["Código"], format_func=lambda c: f"{c} · {productos.set_index('Código').loc[c, 'Producto']}")
        tipo = c3.selectbox("Tipo", ["Entrada", "Salida"])
        cant = c4.number_input("Cantidad", min_value=1.0, step=1.0, format="%.0f")
        det = c5.text_input("Detalle", placeholder="Compra, venta, devolución…")
        if st.form_submit_button("Registrar", icon=":material/add:", type="primary"):
            disponible = res.set_index("Código").loc[cod, "Existencia final"] if cod in set(res["Código"]) else 0
            if tipo == "Salida" and cant > disponible:
                st.error(f"No hay existencia suficiente: disponible {ui.num(disponible)} unidades.")
            else:
                nuevo = pd.DataFrame([{"Fecha": fecha, "Código": cod, "Tipo": tipo, "Cantidad": cant, "Detalle": det}])
                st.session_state.tablas["mov_inv"] = pd.concat([datos.tabla("mov_inv"), nuevo], ignore_index=True)
                st.session_state.ver_tablas = st.session_state.get("ver_tablas", 0) + 1
                st.toast("Movimiento registrado.", icon="✅")
                st.rerun()
    izq, der = st.columns([1.35, 1])
    with izq:
        st.markdown("##### Movimientos registrados")
        ui.editor("mov_inv", num_rows="dynamic", hide_index=True, height=440, column_config={
            "Fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY", required=True),
            "Código": st.column_config.SelectboxColumn("Código", options=list(productos["Código"]), required=True),
            "Tipo": st.column_config.SelectboxColumn("Tipo", options=["Entrada", "Salida"], required=True),
            "Cantidad": st.column_config.NumberColumn("Cantidad", min_value=0, format="%d", required=True),
            "Detalle": st.column_config.TextColumn("Detalle", width="medium"),
        })
    with der:
        st.markdown("##### Catálogo de productos")
        ui.editor("productos", num_rows="dynamic", hide_index=True, column_config={
            "Código": st.column_config.TextColumn("Código", required=True),
            "Producto": st.column_config.TextColumn("Producto", required=True, width="medium"),
            "Existencia inicial": st.column_config.NumberColumn("Exist. inicial", min_value=0, format="%d"),
            "Costo unitario": st.column_config.NumberColumn("Costo unit. (C$)", min_value=0.0, format="%.2f"),
            "Stock mínimo": st.column_config.NumberColumn("Stock mín.", min_value=0, format="%d"),
        })

with t3:
    if len(res):
        cod = st.selectbox("Producto", res["Código"], format_func=lambda c: f"{c} · {res.set_index('Código').loc[c, 'Producto']}",
                           key="kardex_prod")
        k = r["kardex"][r["kardex"]["Código"] == cod].reset_index(drop=True)
        info = res.set_index("Código").loc[cod]
        izq, der = st.columns([1.2, 1])
        with izq:
            vista = k.drop(columns=["Código"]).copy()
            vista["Fecha"] = vista["Fecha"].map(lambda f: f"{f:%d/%m/%Y}" if pd.notna(f) else "—")
            st.dataframe(vista, hide_index=True, column_config={
                "Entrada": st.column_config.NumberColumn(format="%d"), "Salida": st.column_config.NumberColumn(format="%d"),
                "Saldo": st.column_config.NumberColumn(format="%d"), "Valor": st.column_config.NumberColumn("Valor (C$)", format="accounting")})
        with der:
            fig = ui.figura(f"Evolución de la existencia · {info['Producto']}", 330)
            x = list(range(len(k)))
            etiquetas = ["Inicial"] + [f"{f:%d/%m}" for f in k["Fecha"][1:]]
            fig.add_scatter(x=x, y=k["Saldo"], name="Existencia", mode="lines+markers", line=dict(color=ui.SERIES[0], width=2, shape="hv"),
                            marker=dict(size=8, line=dict(color="#fff", width=2)), customdata=k["Detalle"],
                            hovertemplate="%{customdata}<br>Saldo: %{y:,.0f} u<extra></extra>")
            fig.update_xaxes(tickvals=x, ticktext=etiquetas)
            ui.linea_referencia(fig, x, info["Stock mínimo"], "Stock mínimo")
            fig.update_yaxes(rangemode="tozero")
            ui.mostrar(fig)
