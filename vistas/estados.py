"""Módulo 1 · Estados financieros (Balance General y Estado de Resultados)."""

import streamlit as st

from gfo import calculos as calc
from gfo import datos, importar, ui

ui.encabezado("Estados financieros",
              "Registre las cuentas del Balance General y del Estado de Resultados de uno o más períodos. "
              "Estos datos alimentan automáticamente el análisis financiero, el punto de equilibrio, el "
              "apalancamiento, el flujo de efectivo y la planeación.", "Unidad 2 · Módulo 1")

periodos = datos.periodos()
calculados = {p: datos.periodo_calculado(p) for p in periodos}

def revisar_importacion(archivos) -> None:
    """Interpreta los archivos subidos, muestra la vista previa y aplica la importación."""
    try:
        r = importar.interpretar(importar.leer_archivos([(a.name, a.getvalue()) for a in archivos]))
    except Exception as e:  # archivo dañado o con formato no tabular
        st.error(f"No se pudo leer el archivo: {e}", icon=":material/error:")
        return
    if not r["periodos"] or r["detalle"].empty:
        st.error("No se encontraron cuentas con montos en el archivo. Revise que tenga una columna con los nombres "
                 "de las cuentas y columnas con los montos de cada período.", icon=":material/error:")
        return

    nueva = importar.a_tabla(r["estados"])
    calc_n = {p: calc.periodo_completo({**nueva[p].to_dict(), "tasa_impuesto": nueva.loc["tasa_impuesto", p] / 100})
              for p in r["periodos"]}
    reconocidas = int((~r["detalle"]["Se asignó a"].str.startswith("—")).sum())
    cuadra = all(abs(calc_n[p]["diferencia"]) <= 0.5 for p in r["periodos"])
    ui.fila_kpis([
        ui.kpi("Períodos encontrados", str(len(r["periodos"])), ", ".join(r["periodos"])),
        ui.kpi("Cuentas reconocidas", str(reconocidas), f"{len(r['no_reconocidas'])} sin reconocer",
               "bueno" if r["no_reconocidas"].empty else "aceptable"),
        ui.kpi("Ecuación contable", "Cuadra" if cuadra else "No cuadra", "Activo = Pasivo + Patrimonio",
               "bueno" if cuadra else "critico"),
        ui.kpi("Totales del archivo", f"{(r['verificaciones']['Coincide'] == '✓').sum() if len(r['verificaciones']) else 0}"
               f" de {len(r['verificaciones'])}", "coinciden con el cálculo",
               "info" if r["verificaciones"].empty else "bueno" if (r["verificaciones"]["Coincide"] == "✓").all() else "critico"),
    ])
    st.write("")
    for aviso in r["avisos"]:
        st.warning(ui.md(aviso), icon=":material/warning:")

    t1, t2, t3 = st.tabs(["Vista previa de los estados", "Cómo se asignó cada cuenta", "Verificación de totales"])
    with t1:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("##### Balance General")
            ui.tabla_estado([(datos.NOMBRES[k], [calc_n[p][k] for p in r["periodos"]],
                              "total" if k in ("activo_total", "pasivo_patrimonio") else "sub" if k in
                              ("activo_corriente", "pasivo_total", "patrimonio") else "")
                             for k in ["efectivo", "cuentas_cobrar", "inventarios", "otros_ac", "activo_corriente",
                                       "ppe", "otros_anc", "activo_total", "cuentas_pagar", "prestamos_cp", "otros_pc",
                                       "prestamos_lp", "pasivo_total", "capital", "utilidades_retenidas", "patrimonio",
                                       "pasivo_patrimonio"]], r["periodos"])
        with c2:
            st.markdown("##### Estado de Resultados")
            ui.tabla_estado([(datos.NOMBRES[k], [calc_n[p][k] for p in r["periodos"]],
                              "total" if k == "utilidad_neta" else "sub" if k in ("utilidad_bruta", "uaii", "uai") else "")
                             for k in ["ventas", "costo_ventas", "utilidad_bruta", "gastos_venta", "gastos_admin",
                                       "depreciacion", "uaii", "intereses", "uai", "impuestos", "utilidad_neta"]],
                            r["periodos"])
            st.caption(ui.md("Tasa de impuesto: " + ", ".join(f"{p}: {nueva.loc['tasa_impuesto', p]:.2f} %" for p in r["periodos"])
                       + ". Dividendos estimados con la variación de utilidades retenidas. Las acciones y el precio "
                       "de mercado no vienen en los estados: puede escribirlos después en «Datos complementarios»."))
    with t2:
        st.dataframe(r["detalle"], hide_index=True)
        if not r["no_reconocidas"].empty:
            st.warning("Estas filas no se pudieron asignar y **no se tomaron en cuenta**. Si son importantes, cambie su "
                       "nombre en el Excel por uno más común (por ejemplo «Otros gastos de operación») o ajuste los "
                       "montos manualmente después de importar.", icon=":material/help:")
            st.dataframe(r["no_reconocidas"], hide_index=True)
    with t3:
        if r["verificaciones"].empty:
            st.info("El archivo no trae filas de totales para comparar; revise la vista previa.")
        else:
            v = r["verificaciones"].copy()
            for c in ("Según el archivo", "Calculado por el sistema"):
                v[c] = v[c].map(ui.cs)
            st.dataframe(v, hide_index=True)

    with st.container(border=True):
        c1, c2, c3 = st.columns([1.3, 1.3, 1], vertical_alignment="bottom")
        nombre_emp = c1.text_input("Nombre de la empresa", st.session_state.empresa["nombre"], key="imp_empresa")
        modo = c2.radio("¿Qué hacer con los datos actuales?", ["Reemplazar todos los períodos",
                                                              "Agregar o actualizar solo estos períodos"],
                        key="imp_modo")
        if c3.button("Importar y analizar", type="primary", icon=":material/check:", width="stretch"):
            st.session_state.empresa["nombre"] = nombre_emp
            datos.cargar_estados(nueva, reemplazar=modo.startswith("Reemplazar"))
            st.session_state.importado = r["periodos"]
            st.rerun()



tab_reg, tab_imp, tab_bg, tab_er, tab_graf = st.tabs([":material/edit_note: Registro de datos", ":material/upload_file: Importar desde Excel",
                                             ":material/account_balance: Balance General",
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

with tab_imp:
    st.markdown("Si ya tiene el **Balance General** y el **Estado de Resultados** en Excel, súbalos aquí y el sistema "
                "hará todo el análisis automáticamente. Puede subir un solo archivo con ambos estados (en una o varias "
                "hojas) o un archivo por estado.")
    izq, der = st.columns([1.6, 1])
    with izq:
        archivos = st.file_uploader("Archivos de Excel o CSV", type=["xlsx", "xlsm", "csv"], accept_multiple_files=True,
                                    key=f"excel_{st.session_state.version}")
    with der:
        with st.container(border=True):
            st.markdown("**Formato esperado**")
            st.caption("Una columna con el nombre de la cuenta y una columna por período (2024, 2025…). Se aceptan "
                       "códigos contables, títulos, filas de totales y gastos en negativo. Las cuentas se reconocen por "
                       "su nombre: «Caja», «Bancos», «Clientes», «Proveedores», «Costo de ventas», etc.")
            st.download_button("Descargar plantilla de ejemplo", importar.plantilla_excel(datos.tabla("estados")),
                               "plantilla_estados_financieros.xlsx",
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               icon=":material/download:", width="stretch")

    if archivos:
        revisar_importacion(archivos)

    if st.session_state.get("importado"):
        st.success(f"Se importaron los períodos {', '.join(st.session_state.pop('importado'))}. Todos los módulos ya usan estos datos.",
                   icon=":material/check_circle:")
        c1, c2, c3 = st.columns(3)
        c1.page_link("vistas/analisis.py", label="Ver análisis financiero", icon=":material/query_stats:")
        c2.page_link("vistas/inicio.py", label="Ver panel principal", icon=":material/dashboard:")
        c3.page_link("vistas/flujo.py", label="Ver flujo de efectivo", icon=":material/payments:")

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
