"""Módulo 1 · Estados financieros (Balance General y Estado de Resultados)."""

import streamlit as st

from gfo import calculos as calc
from gfo import datos, ui

ui.encabezado("Estados financieros",
              "Registre las cuentas del Balance General y del Estado de Resultados de uno o más períodos. "
              "Estos datos alimentan automáticamente el análisis financiero, el punto de equilibrio, el "
              "apalancamiento, el flujo de efectivo y la planeación.", "Unidad 2 · Módulo 1")

periodos = datos.periodos()
calculados = {p: datos.periodo_calculado(p) for p in periodos}

tab_reg, tab_bg, tab_er, tab_graf = st.tabs([":material/edit_note: Registro de datos", ":material/account_balance: Balance General",
                                             ":material/receipt_long: Estado de Resultados", ":material/bar_chart: Gráficos"])

with tab_reg:
    c1, c2 = st.columns(2)
    emp = st.session_state.empresa
    emp["nombre"] = c1.text_input("Nombre de la empresa", emp["nombre"], key=f"w_emp_nombre_{st.session_state.version}")
    emp["giro"] = c2.text_input("Actividad económica", emp["giro"], key=f"w_emp_giro_{st.session_state.version}")

    with st.container(border=True):
        st.markdown("**Períodos**")
        a, b, c, d = st.columns([2, 1.2, 2, 1.2], vertical_alignment="bottom")
        nuevo = a.text_input("Nuevo período", placeholder="Ej.: 2026", key="nuevo_periodo")
        if b.button("Agregar período", icon=":material/add:", width="stretch"):
            if not nuevo.strip():
                st.warning("Escriba el nombre del período.")
            elif nuevo.strip() in periodos:
                st.warning("Ese período ya existe.")
            else:
                datos.agregar_periodo(nuevo.strip())
                st.rerun()
        quitar = c.selectbox("Eliminar período", periodos, index=None, placeholder="Seleccione…")
        if d.button("Eliminar", icon=":material/delete:", width="stretch", disabled=quitar is None or len(periodos) == 1):
            datos.eliminar_periodo(quitar)
            st.rerun()
        st.caption("Un período nuevo se crea copiando los valores del último período para que solo modifique lo necesario. "
                   "Los períodos se analizan en el orden en que aparecen (de izquierda a derecha).")

    config = {p: st.column_config.NumberColumn(p, format="accounting", step=1.0) for p in periodos}
    col_a, col_b = st.columns([1.15, 1])
    with col_a:
        st.markdown(ui.md("##### Balance General (C$)"))
        ui.editor("estados", filas=[k for k, *_ in datos.CUENTAS_BALANCE],
                  etiquetas={k: n for k, n, _ in datos.CUENTAS_BALANCE}, column_config=config)
    with col_b:
        st.markdown(ui.md("##### Estado de Resultados (C$)"))
        ui.editor("estados", filas=[k for k, _ in datos.CUENTAS_RESULTADOS],
                  etiquetas=dict(datos.CUENTAS_RESULTADOS), column_config=config)
        st.markdown("##### Datos complementarios")
        ui.editor("estados", filas=[k for k, _ in datos.DATOS_ADICIONALES],
                  etiquetas=dict(datos.DATOS_ADICIONALES),
                  column_config={p: st.column_config.NumberColumn(p, format="accounting", step=0.01) for p in periodos})
        st.caption("La tasa de impuesto se escribe como porcentaje (30 = 30 %). Las acciones, el precio y los "
                   "dividendos se usan en las razones de mercado y en el flujo de efectivo.")

    for p in periodos:
        dif = calculados[p]["diferencia"]
        if abs(dif) > 0.5:
            st.error(ui.md(f"**{p}:** el balance no cuadra. Activo − (Pasivo + Patrimonio) = {ui.cs(dif)}. "
                     "Revise las cuentas antes de interpretar los resultados."), icon=":material/error:")
    if all(abs(calculados[p]["diferencia"]) <= 0.5 for p in periodos):
        st.success("La ecuación contable se cumple en todos los períodos: **Activo = Pasivo + Patrimonio**.",
                   icon=":material/check_circle:")

with tab_bg:
    st.markdown(ui.md(f"#### {st.session_state.empresa['nombre']}  \nBalance General al cierre de cada período · cifras en C$"))
    filas = []
    grupos = [("ACTIVO", ["Activo corriente", "Activo no corriente"]),
              ("PASIVO", ["Pasivo corriente", "Pasivo no corriente"]), ("PATRIMONIO", ["Patrimonio"])]
    subtotal = {"Activo corriente": "activo_corriente", "Activo no corriente": "activo_no_corriente",
                "Pasivo corriente": "pasivo_corriente", "Pasivo no corriente": "pasivo_no_corriente"}
    for titulo, subgrupos in grupos:
        filas.append((titulo, [], "grupo"))
        for g in subgrupos:
            for k, n, gg in datos.CUENTAS_BALANCE:
                if gg == g:
                    filas.append((n, [calculados[p][k] for p in periodos], ""))
            if g in subtotal:
                filas.append((datos.NOMBRES[subtotal[g]], [calculados[p][subtotal[g]] for p in periodos], "sub"))
        total = {"ACTIVO": "activo_total", "PASIVO": "pasivo_total", "PATRIMONIO": "patrimonio"}[titulo]
        filas.append((datos.NOMBRES[total], [calculados[p][total] for p in periodos], "total"))
    filas.append(("TOTAL PASIVO + PATRIMONIO", [calculados[p]["pasivo_patrimonio"] for p in periodos], "total"))
    ui.tabla_estado(filas, periodos)

with tab_er:
    st.markdown(ui.md(f"#### {st.session_state.empresa['nombre']}  \nEstado de Resultados del período · cifras en C$"))
    lineas = [("ventas", ""), ("costo_ventas", "-"), ("utilidad_bruta", "sub"), ("gastos_venta", "-"),
              ("gastos_admin", "-"), ("depreciacion", "-"), ("gastos_operacion", "sub"), ("uaii", "sub"),
              ("intereses", "-"), ("uai", "sub"), ("impuestos", "-"), ("utilidad_neta", "total")]
    filas = []
    for k, estilo in lineas:
        nombre = ("(−) " if estilo == "-" else "") + datos.NOMBRES[k]
        filas.append((nombre, [calculados[p][k] for p in periodos], "" if estilo == "-" else estilo))
    ui.tabla_estado(filas, periodos)
    ui.formula("<b>Cálculo:</b> Utilidad bruta = Ventas − Costo de ventas · "
               "UAII = Utilidad bruta − Gastos de operación · UAI = UAII − Intereses · "
               "Impuesto = UAI × tasa · Utilidad neta = UAI − Impuesto "
               "<br><span class='note'>Código: <code>gfo/calculos.py → estado_resultados()</code></span>")

with tab_graf:
    g1, g2 = st.columns(2)
    with g1:
        fig = ui.figura("Estructura del balance", 400)
        partes = [("Activo corriente", "activo_corriente", "Activos"), ("Activo no corriente", "activo_no_corriente", "Activos"),
                  ("Pasivo corriente", "pasivo_corriente", "Pasivo + Patrimonio"),
                  ("Pasivo no corriente", "pasivo_no_corriente", "Pasivo + Patrimonio"),
                  ("Patrimonio", "patrimonio", "Pasivo + Patrimonio")]
        x = [[p for p in periodos for _ in (0, 1)], ["Activos", "Pasivo + Patrimonio"] * len(periodos)]
        for i, (nombre, k, lado) in enumerate(partes):
            y = [calculados[p][k] if l == lado else None for p, l in zip(*x)]
            fig.add_bar(x=x, y=y, name=nombre, marker=dict(color=ui.SERIES[i], line=dict(color="#fff", width=2), cornerradius=4),
                        hovertemplate="%{x}<br>" + nombre + ": C$ %{y:,.2f}<extra></extra>")
        fig.update_layout(barmode="stack", legend=dict(y=-0.32, yanchor="top", x=0, xanchor="left"), margin=dict(b=90))
        ui.mostrar(fig)
    with g2:
        fig = ui.figura("Resultados por período", 400)
        conceptos = [("Ventas", "ventas"), ("Utilidad bruta", "utilidad_bruta"), ("UAII", "uaii"), ("Utilidad neta", "utilidad_neta")]
        for i, p in enumerate(periodos):
            vals = [calculados[p][k] for _, k in conceptos]
            ui.barras(fig, [c for c, _ in conceptos], vals, p, ui.SERIES[i % 8],
                      texto=[ui.corto(v) for v in vals] if i == len(periodos) - 1 else None,
                      hovertemplate="%{x} " + p + ": C$ %{y:,.2f}<extra></extra>")
        fig.update_layout(barmode="group")
        ui.mostrar(fig)
