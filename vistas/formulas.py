"""Referencia de fórmulas, criterios de interpretación y ubicación en el código."""

import pandas as pd
import streamlit as st

from gfo import calculos as calc
from gfo import ui

ui.encabezado("Fórmulas utilizadas",
              "Resumen de las fórmulas que aplica el sistema y de la función de <code>gfo/calculos.py</code> donde se "
              "calcula cada una. Útil para la defensa individual y para comprobar los resultados manualmente.", "Referencia")

secciones = {
    "Estados financieros · estado_resultados(), totales_balance()": [
        ("Utilidad bruta", "Ventas − Costo de ventas"),
        ("Utilidad operativa (UAII)", "Utilidad bruta − Gastos de venta − Gastos de administración − Depreciación"),
        ("Utilidad antes de impuestos (UAI)", "UAII − Gastos por intereses"),
        ("Impuesto sobre la renta", "UAI × Tasa de impuesto (si UAI > 0)"),
        ("Utilidad neta", "UAI − Impuesto"),
        ("Ecuación contable", "Activo = Pasivo + Patrimonio"),
    ],
    "Análisis horizontal y vertical · analisis_horizontal(), analisis_vertical()": [
        ("Variación absoluta", "Valor período actual − Valor período base"),
        ("Variación relativa", "Variación absoluta ÷ Valor período base × 100"),
        ("Análisis vertical (Balance)", "Cuenta ÷ Activo total × 100"),
        ("Análisis vertical (Resultados)", "Cuenta ÷ Ventas netas × 100"),
    ],
    "Sistema DuPont · dupont()": [
        ("ROA", "Margen neto × Rotación de activos totales"),
        ("ROE", "Margen neto × Rotación de activos totales × Multiplicador del capital"),
    ],
    "Punto de equilibrio y C-V-U · cvu(), escenario_cvu(), unidades_para_utilidad()": [
        ("Margen de contribución unitario", "Precio − Costo variable unitario"),
        ("Razón de margen de contribución", "MCu ÷ Precio"),
        ("Punto de equilibrio en unidades", "Costos fijos ÷ MCu"),
        ("Punto de equilibrio en C$", "Costos fijos ÷ Razón de margen de contribución"),
        ("Utilidad operativa", "Unidades × MCu − Costos fijos"),
        ("Margen de seguridad", "(Unidades esperadas − PE en unidades) ÷ Unidades esperadas"),
        ("Unidades para utilidad deseada", "(Costos fijos + Utilidad deseada) ÷ MCu"),
    ],
    "Apalancamiento · apalancamiento(), efecto_apalancamiento()": [
        ("Grado de apalancamiento operativo (GAO)", "Margen de contribución ÷ UAII"),
        ("Grado de apalancamiento financiero (GAF)", "UAII ÷ [UAII − Intereses − Dividendos preferentes ÷ (1 − t)]"),
        ("Grado de apalancamiento total (GAT)", "GAO × GAF"),
        ("Efecto en la UAII", "Δ% UAII = GAO × Δ% Ventas"),
        ("Efecto en la UPA", "Δ% UPA = GAT × Δ% Ventas"),
    ],
    "Flujo de efectivo · flujo_efectivo_indirecto(), flujo_efectivo_directo()": [
        ("Flujo de operación (indirecto)", "Utilidad neta + Depreciación − Δ CxC − Δ Inventarios − Δ Otros AC + Δ CxP + Δ Otros PC"),
        ("Flujo de inversión", "−(Δ PPE neto + Depreciación) − Δ Otros activos no corrientes"),
        ("Flujo de financiamiento", "Δ Préstamos CP + Δ Préstamos LP + Δ Capital − Dividendos"),
        ("Flujo por actividad (directo)", "Σ Entradas − Σ Salidas"),
        ("Saldo final de efectivo", "Saldo inicial + Variación neta"),
    ],
    "Presupuesto maestro · presupuesto_maestro()": [
        ("Presupuesto de ventas", "Unidades × Precio"),
        ("Cobros", "Ventas del trimestre × % contado + Ventas del trimestre anterior × % crédito"),
        ("Unidades a comprar", "Ventas + Inventario final deseado − Inventario inicial"),
        ("Pagos a proveedores", "Compras del trimestre × % contado + Compras del trimestre anterior × % crédito"),
        ("Costo de bienes vendidos", "Inventario inicial + Compras − Inventario final"),
        ("Saldo de caja", "Saldo inicial + Cobros − Egresos ± Financiamiento"),
        ("Financiamiento requerido", "Saldo mínimo − Saldo antes de financiamiento (si es positivo)"),
    ],
    "Presupuesto personal · presupuesto_personal()": [
        ("Capacidad de ahorro", "Total ingresos − Total gastos"),
        ("Porcentaje de ahorro", "Capacidad de ahorro ÷ Total ingresos × 100"),
        ("Saldo disponible", "Total ingresos − Total gastos − Ahorro planificado"),
    ],
    "Control de inventario · control_inventario()": [
        ("Existencia final", "Existencia inicial + Entradas − Salidas"),
        ("Valor del inventario", "Existencia final × Costo unitario"),
        ("Alerta de reposición", "Existencia final ≤ Stock mínimo"),
        ("Cantidad sugerida", "2 × Stock mínimo − Existencia final"),
    ],
}

for titulo, filas in secciones.items():
    with st.expander(titulo, expanded=False):
        st.dataframe(pd.DataFrame(filas, columns=["Concepto", "Fórmula"]), hide_index=True)

with st.expander("Razones financieras · razones_financieras(), evaluar_razon(), interpretar_razon()", expanded=True):
    st.dataframe(pd.DataFrame([{"Categoría": i["categoria"], "Razón": i["nombre"], "Fórmula": i["formula"],
                                "Unidad": i["unidad"]} for i in calc.INFO_RAZON.values()]), hide_index=True)
    st.markdown("**Criterios de evaluación** (referencias académicas generales)")
    criterios = [
        ("Razón corriente", "≥ 1.5", "1.0 – 1.5", "< 1.0"), ("Prueba ácida", "≥ 1.0", "0.7 – 1.0", "< 0.7"),
        ("Razón de efectivo", "≥ 0.2", "0.1 – 0.2", "< 0.1"), ("Razón de endeudamiento", "≤ 50 %", "50 % – 70 %", "> 70 %"),
        ("Deuda a patrimonio", "≤ 1.0", "1.0 – 2.0", "> 2.0"), ("Cobertura de intereses", "≥ 3.0", "1.5 – 3.0", "< 1.5"),
        ("Margen bruto", "≥ 25 %", "10 % – 25 %", "< 10 %"), ("Margen operativo", "≥ 10 %", "3 % – 10 %", "< 3 %"),
        ("Margen neto", "≥ 5 %", "0 % – 5 %", "< 0 %"), ("ROA", "≥ 5 %", "2 % – 5 %", "< 2 %"), ("ROE", "≥ 12 %", "5 % – 12 %", "< 5 %"),
    ]
    st.dataframe(pd.DataFrame(criterios, columns=["Razón", "Favorable", "Aceptable", "Desfavorable"]), hide_index=True)
    st.caption("Las razones de actividad y de mercado se muestran como informativas: su nivel adecuado depende del giro de la empresa.")
