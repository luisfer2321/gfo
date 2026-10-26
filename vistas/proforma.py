"""Módulo 7 · Estados proforma y reporte integrado para la toma de decisiones."""

import pandas as pd
import streamlit as st

from gfo import calculos as calc
from gfo import datos, ui

periodos = datos.periodos()
ultimo = periodos[-1]
proy = "Proforma"

ui.encabezado("Proforma y reporte integrado",
              f"Estados financieros proyectados a partir del presupuesto maestro y del Balance General {ultimo}, junto "
              "con un resumen de indicadores reales y proyectados que apoya la toma de decisiones.", "Unidad 3 · Módulo 7")

pm = datos.presupuesto()
bp = pm["balance_proforma"]
real = {p: datos.periodo_calculado(p) for p in periodos}
pro = calc.periodo_completo(bp)
cols = periodos + [proy]
todos = {**real, proy: pro}

t1, t2, t3 = st.tabs([":material/receipt_long: Estado de resultados proforma", ":material/account_balance: Balance general proforma",
                      ":material/insights: Reporte integrado"])

with t1:
    lineas = [("ventas", ""), ("costo_ventas", "-"), ("utilidad_bruta", "sub"), ("gastos_venta", "-"),
              ("gastos_admin", "-"), ("depreciacion", "-"), ("uaii", "sub"), ("intereses", "-"), ("otros_ingresos", ""), ("uai", "sub"),
              ("impuestos", "-"), ("utilidad_neta", "total")]
    izq, der = st.columns([1.3, 1])
    with izq:
        ui.tabla_estado([(("(−) " if e == "-" else "") + datos.NOMBRES[k], [real[ultimo][k], pro[k],
                          ui.pct(calc.dividir(pro[k] - real[ultimo][k], real[ultimo][k]), 1)], "" if e == "-" else e)
                         for k, e in lineas], [ultimo, proy, "Cambio"])
    with der:
        ui.formula("Ventas, costo de bienes vendidos y gastos provienen de las cédulas del presupuesto maestro. "
                   "Impuesto = UAI × tasa del último período.<br><span class='note'>Código: "
                   "<code>gfo/calculos.py → presupuesto_maestro()</code>, paso 7</span>")
        fig = ui.figura("Real vs. proforma", 300)
        conceptos = [("Ventas", "ventas"), ("Utilidad bruta", "utilidad_bruta"), ("UAII", "uaii"), ("Utilidad neta", "utilidad_neta")]
        ui.barras(fig, [c for c, _ in conceptos], [real[ultimo][k] for _, k in conceptos], ultimo, ui.SERIES[0],
                  hovertemplate="%{x} " + ultimo + ": C$ %{y:,.2f}<extra></extra>")
        ui.barras(fig, [c for c, _ in conceptos], [pro[k] for _, k in conceptos], proy, ui.SERIES[1],
                  texto=[ui.corto(pro[k]) for _, k in conceptos], hovertemplate="%{x} proforma: C$ %{y:,.2f}<extra></extra>")
        fig.update_layout(barmode="group")
        ui.mostrar(fig)

with t2:
    izq, der = st.columns([1.3, 1])
    with izq:
        filas = []
        for grupo, claves, total in [("ACTIVO", ["efectivo", "cuentas_cobrar", "inventarios", "otros_ac", "activo_corriente",
                                                 "ppe", "otros_anc", "activo_no_corriente"], "activo_total"),
                                     ("PASIVO", ["cuentas_pagar", "prestamos_cp", "otros_pc", "pasivo_corriente", "prestamos_lp"],
                                      "pasivo_total"),
                                     ("PATRIMONIO", ["capital", "utilidades_retenidas"], "patrimonio")]:
            filas.append((grupo, [], "grupo"))
            for k in claves:
                filas.append((datos.NOMBRES[k], [real[ultimo][k], pro[k]], "sub" if k.startswith(("activo", "pasivo")) else ""))
            filas.append((datos.NOMBRES[total], [real[ultimo][total], pro[total]], "total"))
        filas.append(("TOTAL PASIVO + PATRIMONIO", [real[ultimo]["pasivo_patrimonio"], pro["pasivo_patrimonio"]], "total"))
        ui.tabla_estado(filas, [ultimo, proy])
    with der:
        if abs(pro["diferencia"]) < 1:
            st.success("El balance proforma cuadra: **Activo = Pasivo + Patrimonio**.", icon=":material/check_circle:")
        else:
            st.error(ui.md(f"Diferencia en el balance proforma: {ui.cs(pro['diferencia'])}"), icon=":material/error:")
        ui.formula(
            "<b>Efectivo</b> = saldo final del presupuesto de caja<br>"
            "<b>Cuentas por cobrar</b> = ventas a crédito del último trimestre<br>"
            "<b>Inventario</b> = inventario final × costo unitario<br>"
            "<b>PPE</b> = PPE inicial + Inversiones − Depreciación<br>"
            "<b>Cuentas por pagar</b> = compras a crédito del último trimestre<br>"
            "<b>Préstamos CP</b> = saldo inicial + financiamiento neto del año<br>"
            "<b>Utilidades retenidas</b> = saldo inicial + Utilidad neta − Dividendos")

with t3:
    rz = {p: calc.razones_financieras(todos[p]) for p in cols}
    ui.fila_kpis([
        ui.kpi("Ventas proyectadas", ui.corto(pro["ventas"]), f"vs. {ultimo}", delta=calc.dividir(pro["ventas"] - real[ultimo]["ventas"], real[ultimo]["ventas"])),
        ui.kpi("Utilidad neta proyectada", ui.corto(pro["utilidad_neta"]), f"vs. {ultimo}",
               delta=calc.dividir(pro["utilidad_neta"] - real[ultimo]["utilidad_neta"], abs(real[ultimo]["utilidad_neta"]))),
        ui.kpi("ROE proyectado", ui.pct(rz[proy]["roe"]), f"{ultimo}: {ui.pct(rz[ultimo]['roe'])}", calc.evaluar_razon("roe", rz[proy]["roe"])),
        ui.kpi("Razón corriente proyectada", ui.veces(rz[proy]["razon_corriente"]), f"{ultimo}: {ui.veces(rz[ultimo]['razon_corriente'])}",
               calc.evaluar_razon("razon_corriente", rz[proy]["razon_corriente"])),
    ])
    st.write("")
    claves = ["razon_corriente", "prueba_acida", "capital_trabajo", "dias_inventario", "periodo_cobro", "razon_deuda",
              "cobertura_intereses", "margen_bruto", "margen_neto", "roa", "roe", "upa"]
    tabla = pd.DataFrame([{"Indicador": calc.INFO_RAZON[k]["nombre"],
                           **{p: ui.por_unidad(rz[p][k], calc.INFO_RAZON[k]["unidad"]) for p in cols},
                           "Evaluación proforma": ui.ESTADO_TXT[calc.evaluar_razon(k, rz[proy][k])]} for k in claves])
    izq, der = st.columns([1.4, 1])
    with izq:
        st.markdown("##### Indicadores clave: históricos y proyectados")
        st.dataframe(tabla, hide_index=True, height=458)
        st.download_button("Exportar análisis completo (Excel)", datos.generador_reporte(), file_name=datos.nombre_reporte(),
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           icon=":material/table_view:", type="primary")
        st.download_button("Descargar resumen (CSV)", tabla.to_csv(index=False).encode("utf-8-sig"), "reporte_integrado.csv",
                           "text/csv", icon=":material/download:")
    with der:
        fig = ui.figura("Rentabilidad: real y proyectada", 300)
        for i, (k, n) in enumerate([("margen_neto", "Margen neto"), ("roa", "ROA"), ("roe", "ROE")]):
            fig.add_scatter(x=cols, y=[(rz[p][k] or 0) * 100 for p in cols], name=n, mode="lines+markers",
                            line=dict(color=ui.SERIES[i], width=2), marker=dict(size=9, line=dict(color="#fff", width=2)),
                            hovertemplate="%{x} " + n + ": %{y:.2f} %<extra></extra>")
        fig.update_yaxes(ticksuffix=" %", rangemode="tozero")
        ui.mostrar(fig)

        # Conclusiones automáticas para la toma de decisiones
        st.markdown("##### Hallazgos para la toma de decisiones")
        r_u = rz[ultimo]
        hallazgos = []
        if pro["utilidad_neta"] > real[ultimo]["utilidad_neta"]:
            hallazgos.append(("bueno", f"La utilidad neta proyectada crece {ui.pct(calc.dividir(pro['utilidad_neta'] - real[ultimo]['utilidad_neta'], real[ultimo]['utilidad_neta']), 1)}."))
        else:
            hallazgos.append(("critico", "La utilidad neta proyectada disminuye: revise precios, costos y gastos."))
        if pm["deuda_nueva"] > 0:
            hallazgos.append(("aceptable", f"Queda deuda de corto plazo nueva por {ui.cs(pm['deuda_nueva'])}: negocie la línea de crédito con anticipación."))
        elif max(pm["caja"].loc["Financiamiento (+) / pago (−)", pm["trimestres"]]) > 0:
            hallazgos.append(("bueno", "El préstamo de corto plazo requerido se paga dentro del mismo año."))
        exceso = pm["saldos"][-1] - datos.params()["pm_saldo_min"]
        if exceso > 0.5 * pro["activo_corriente"]:
            hallazgos.append(("aceptable", f"Se proyecta un excedente de efectivo de {ui.cs(exceso)}: evalúe invertirlo o reducir deuda."))
        ev = calc.evaluar_razon("razon_deuda", rz[proy]["razon_deuda"])
        hallazgos.append((ev, f"El endeudamiento proyectado es {ui.pct(rz[proy]['razon_deuda'])} (antes {ui.pct(r_u['razon_deuda'])})."))
        ev = calc.evaluar_razon("razon_corriente", rz[proy]["razon_corriente"])
        hallazgos.append((ev, f"La liquidez proyectada es {ui.veces(rz[proy]['razon_corriente'])} de activo corriente por cada córdoba de pasivo corriente."))
        inv = datos.inventario()
        if len(inv["alertas"]):
            hallazgos.append(("aceptable", f"{len(inv['alertas'])} producto(s) del inventario requieren reposición (≈ {ui.cs(inv['costo_reposicion'])})."))
        st.markdown("".join(f"<div style='margin:.35rem 0'>{ui.chip(e)} <span class='note' style='color:#0b0b0b'>{t}</span></div>"
                            for e, t in hallazgos), unsafe_allow_html=True)
