"""Panel principal: indicadores clave de todos los módulos y acceso rápido."""

import streamlit as st

from gfo import calculos as calc
from gfo import datos, ui

emp = st.session_state.empresa
periodos = datos.periodos()
ultimo = periodos[-1]
anterior = periodos[-2] if len(periodos) > 1 else None

st.markdown(
    f'<div class="hero"><div class="eyebrow">Sistema de Análisis y Planeación Financiera · Gestión Financiera Operativa IS2122</div>'
    f'<h1>{emp["nombre"]}</h1><p>{emp["giro"]} · Último período registrado: <b>{ultimo}</b></p></div>',
    unsafe_allow_html=True)

d = datos.periodo_calculado(ultimo)
da = datos.periodo_calculado(anterior) if anterior else None
r = calc.razones_financieras(datos.cuentas_periodo(ultimo))
var = (lambda k: calc.dividir(d[k] - da[k], abs(da[k]))) if da else (lambda k: None)

st.markdown("##### Análisis financiero")
ui.fila_kpis([
    ui.kpi("Ventas", ui.corto(d["ventas"]), f"vs. {anterior}" if anterior else ultimo, delta=var("ventas")),
    ui.kpi("Utilidad neta", ui.corto(d["utilidad_neta"]), f"vs. {anterior}" if anterior else ultimo, delta=var("utilidad_neta")),
    ui.kpi("Razón corriente", ui.veces(r["razon_corriente"]), "liquidez", calc.evaluar_razon("razon_corriente", r["razon_corriente"])),
    ui.kpi("Endeudamiento", ui.pct(r["razon_deuda"]), "pasivo ÷ activo", calc.evaluar_razon("razon_deuda", r["razon_deuda"])),
    ui.kpi("ROE", ui.pct(r["roe"]), "rentabilidad del patrimonio", calc.evaluar_razon("roe", r["roe"])),
])
st.write("")

b = datos.cvu_base()
cv = calc.cvu(b["precio"], b["cv_unitario"], b["costos_fijos"], b["unidades"])
cl = calc.clasificar_costos(datos.cuentas_periodo(ultimo))
ap = calc.apalancamiento(d["ventas"], cl["costos_variables"], cl["costos_fijos"], d["intereses"])
pm = datos.presupuesto()
pers = datos.personal()
inv = datos.inventario()

st.markdown("##### Equilibrio, apalancamiento y planeación")
ui.fila_kpis([
    ui.kpi("Punto de equilibrio", ui.corto(cv["pe_monetario"]) if cv["pe_monetario"] else "N/D",
           f"{ui.num(cv['pe_unidades'])} unidades" if cv["pe_unidades"] else "margen de contribución ≤ 0"),
    ui.kpi("Margen de seguridad", ui.pct(cv["margen_seguridad_pct"], 1), "caída tolerable en ventas"),
    ui.kpi("Apalancamiento total", ui.veces(ap["gat"]), f"GAO {ui.num(ap['gao'], 2)} · GAF {ui.num(ap['gaf'], 2)}"),
    ui.kpi("Ventas presupuestadas", ui.corto(pm["er_proforma"]["ventas"]), "año proyectado"),
    ui.kpi("Saldo de caja proyectado", ui.corto(pm["saldos"][-1]), f"al cierre de {pm['trimestres'][-1]}"),
])
st.write("")

g1, g2 = st.columns([1.35, 1])
with g1:
    fig = ui.figura("Ventas y utilidades por período", 340)
    conceptos = [("Ventas", "ventas"), ("Utilidad bruta", "utilidad_bruta"), ("UAII", "uaii"), ("Utilidad neta", "utilidad_neta")]
    todos = {p: datos.periodo_calculado(p) for p in periodos}
    todos["Proforma"] = calc.periodo_completo(pm["balance_proforma"])
    for i, p in enumerate(todos):
        ui.barras(fig, [c for c, _ in conceptos], [todos[p][k] for _, k in conceptos], p, ui.SERIES[i % 8],
                  hovertemplate="%{x} " + p + ": C$ %{y:,.2f}<extra></extra>")
    fig.update_layout(barmode="group")
    ui.mostrar(fig)
with g2:
    fig = ui.figura("Saldo de caja proyectado por trimestre", 340)
    ui.barras(fig, pm["trimestres"], pm["saldos"], "Saldo final", ui.SERIES[0], texto=[ui.corto(v) for v in pm["saldos"]],
              hovertemplate="%{x}: C$ %{y:,.2f}<extra></extra>")
    ui.linea_referencia(fig, pm["trimestres"], datos.params()["pm_saldo_min"], "Saldo mínimo")
    ui.mostrar(fig)

st.markdown("##### Aplicaciones prácticas")
ui.fila_kpis([
    ui.kpi("Presupuesto personal · saldo disponible", ui.cs(pers["saldo_disponible"]),
           f"ahorro {ui.pct(pers['pct_ahorro'], 1)} del ingreso", "bueno" if pers["saldo_disponible"] >= 0 else "critico"),
    ui.kpi("Valor del inventario", ui.cs(inv["valor_total"]), f"{len(inv['resumen'])} productos"),
    ui.kpi("Alertas de reposición", str(len(inv["alertas"])),
           ", ".join(inv["alertas"]["Producto"].str.split(" \\(").str[0]) if len(inv["alertas"]) else "inventario suficiente",
           "critico" if len(inv["alertas"]) else "bueno"),
])
st.write("")

st.markdown("##### Módulos del sistema")
modulos = [
    ("vistas/estados.py", "Estados financieros", "Balance General y Estado de Resultados", ":material/account_balance:"),
    ("vistas/analisis.py", "Análisis financiero", "Horizontal, vertical, razones y DuPont", ":material/query_stats:"),
    ("vistas/equilibrio.py", "Punto de equilibrio y C-V-U", "PE, margen de seguridad y escenarios", ":material/balance:"),
    ("vistas/apalancamiento.py", "Apalancamiento", "GAO, GAF y GAT", ":material/trending_up:"),
    ("vistas/flujo.py", "Flujo de efectivo", "Operación, inversión y financiamiento", ":material/payments:"),
    ("vistas/presupuestos.py", "Planeación y presupuestos", "Presupuesto maestro y de caja", ":material/event_note:"),
    ("vistas/proforma.py", "Proforma y reporte integrado", "Estados proyectados y hallazgos", ":material/summarize:"),
    ("vistas/personal.py", "Presupuesto personal", "Ingresos, gastos, ahorro y saldo", ":material/savings:"),
    ("vistas/inventario.py", "Control de inventario", "Existencias, valor y reposición", ":material/inventory_2:"),
]
for fila in range(0, len(modulos), 3):
    cols = st.columns(3)
    for c, (ruta, titulo, desc, icono) in zip(cols, modulos[fila:fila + 3]):
        with c.container(border=True):
            st.page_link(ruta, label=titulo, icon=icono)
            st.caption(desc)

st.caption("Flujo de integración: los estados financieros alimentan el análisis, el punto de equilibrio, el apalancamiento "
           "y el flujo de efectivo; el último balance es el punto de partida del presupuesto maestro, que a su vez genera "
           "los estados proforma. El inventario alerta sobre necesidades de compra en la planeación.")
