"""Sistema de Análisis y Planeación Financiera — punto de entrada.

Ejecutar con:  streamlit run app.py
"""

import streamlit as st

from gfo import datos, ui

st.set_page_config(page_title="Sistema de Análisis y Planeación Financiera", page_icon="📊",
                   layout="wide", initial_sidebar_state="expanded")

datos.inicializar()
ui.estilos()

paginas = {
    "Inicio": [
        st.Page("vistas/inicio.py", title="Panel principal", icon=":material/dashboard:", default=True),
    ],
    "Unidad 2 · Análisis financiero": [
        st.Page("vistas/estados.py", title="Estados financieros", icon=":material/account_balance:"),
        st.Page("vistas/analisis.py", title="Análisis financiero", icon=":material/query_stats:"),
        st.Page("vistas/equilibrio.py", title="Punto de equilibrio y C-V-U", icon=":material/balance:"),
        st.Page("vistas/apalancamiento.py", title="Apalancamiento", icon=":material/trending_up:"),
    ],
    "Unidad 3 · Planeación financiera": [
        st.Page("vistas/flujo.py", title="Flujo de efectivo", icon=":material/payments:"),
        st.Page("vistas/presupuestos.py", title="Planeación y presupuestos", icon=":material/event_note:"),
        st.Page("vistas/proforma.py", title="Proforma y reporte integrado", icon=":material/summarize:"),
    ],
    "Aplicaciones prácticas": [
        st.Page("vistas/personal.py", title="Presupuesto personal", icon=":material/savings:"),
        st.Page("vistas/inventario.py", title="Control de inventario", icon=":material/inventory_2:"),
    ],
    "Referencia": [
        st.Page("vistas/formulas.py", title="Fórmulas utilizadas", icon=":material/function:"),
    ],
}
pagina = st.navigation(paginas, expanded=True)

with st.sidebar:
    st.markdown(f"**{st.session_state.empresa['nombre']}**  \n"
                f"<span class='note'>{st.session_state.empresa['giro']}</span>", unsafe_allow_html=True)
    st.caption(f"Períodos registrados: {', '.join(datos.periodos())}")
    st.download_button("Exportar análisis a Excel", datos.generador_reporte(), file_name=datos.nombre_reporte(),
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       icon=":material/download:", type="primary", width="stretch",
                       help="Reporte con los estados financieros y todos los análisis de la empresa "
                            "(no incluye el presupuesto personal ni el inventario).")
    with st.expander("Guardar o cargar datos", icon=":material/save:"):
        st.download_button("Exportar datos (JSON)", datos.exportar_json(), file_name="datos_financieros.json",
                           mime="application/json", icon=":material/download:", width="stretch")
        archivo = st.file_uploader("Importar datos (JSON)", type=["json"], key=f"imp_{st.session_state.version}")
        if archivo is not None:
            try:
                datos.importar_json(archivo.getvalue().decode("utf-8"))
                st.toast("Datos importados correctamente.", icon="✅")
                st.rerun()
            except Exception as e:  # archivo con formato incorrecto
                st.error(f"No se pudo importar el archivo: {e}")
        if st.button("Restaurar datos de ejemplo", icon=":material/restart_alt:", width="stretch"):
            datos.inicializar(forzar=True)
            st.rerun()
    st.caption("Gestión Financiera Operativa · IS2122")

pagina.run()
