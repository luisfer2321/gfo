"""Catálogo de cuentas, datos de ejemplo y manejo del estado de la sesión.

El sistema no usa base de datos: durante la ejecución toda la información vive
en ``st.session_state`` (memoria de la sesión del navegador). Desde la barra
lateral se puede exportar a un archivo JSON y volver a importarla.
"""

from __future__ import annotations

import copy
import json

import pandas as pd
import streamlit as st

from gfo import calculos as calc

# (clave, nombre, grupo)
CUENTAS_BALANCE = [
    ("efectivo", "Efectivo y equivalentes", "Activo corriente"),
    ("cuentas_cobrar", "Cuentas por cobrar", "Activo corriente"),
    ("inventarios", "Inventarios", "Activo corriente"),
    ("otros_ac", "Otros activos corrientes", "Activo corriente"),
    ("ppe", "Propiedad, planta y equipo (neto)", "Activo no corriente"),
    ("otros_anc", "Otros activos no corrientes", "Activo no corriente"),
    ("cuentas_pagar", "Cuentas por pagar a proveedores", "Pasivo corriente"),
    ("prestamos_cp", "Préstamos a corto plazo", "Pasivo corriente"),
    ("otros_pc", "Otros pasivos corrientes", "Pasivo corriente"),
    ("prestamos_lp", "Préstamos a largo plazo", "Pasivo no corriente"),
    ("capital", "Capital social", "Patrimonio"),
    ("utilidades_retenidas", "Utilidades retenidas", "Patrimonio"),
]

CUENTAS_RESULTADOS = [
    ("ventas", "Ventas netas"),
    ("costo_ventas", "Costo de ventas"),
    ("gastos_venta", "Gastos de venta"),
    ("gastos_admin", "Gastos de administración"),
    ("depreciacion", "Depreciación"),
    ("intereses", "Gastos por intereses"),
]

DATOS_ADICIONALES = [
    ("tasa_impuesto", "Tasa de impuesto sobre la renta (%)"),
    ("acciones", "Acciones en circulación"),
    ("precio_accion", "Precio de mercado por acción (C$)"),
    ("dividendos", "Dividendos pagados (C$)"),
]

NOMBRES = {k: n for k, n, *_ in CUENTAS_BALANCE + CUENTAS_RESULTADOS + DATOS_ADICIONALES}
NOMBRES.update({
    "activo_corriente": "Total activo corriente", "activo_no_corriente": "Total activo no corriente",
    "activo_total": "TOTAL ACTIVO", "pasivo_corriente": "Total pasivo corriente",
    "pasivo_no_corriente": "Total pasivo no corriente", "pasivo_total": "TOTAL PASIVO",
    "patrimonio": "TOTAL PATRIMONIO", "pasivo_patrimonio": "TOTAL PASIVO + PATRIMONIO",
    "utilidad_bruta": "Utilidad bruta", "gastos_operacion": "Total gastos de operación",
    "uaii": "Utilidad operativa (UAII)", "uai": "Utilidad antes de impuestos (UAI)",
    "impuestos": "Impuesto sobre la renta", "utilidad_neta": "Utilidad neta",
})

EMPRESA = {
    "nombre": "Distribuidora El Progreso, S.A.",
    "giro": "Distribución mayorista de granos básicos y abarrotes",
    "moneda": "C$",
}

ESTADOS_EJEMPLO = {
    "2024": {
        "efectivo": 450_000, "cuentas_cobrar": 820_000, "inventarios": 1_100_000, "otros_ac": 80_000,
        "ppe": 3_200_000, "otros_anc": 350_000,
        "cuentas_pagar": 700_000, "prestamos_cp": 400_000, "otros_pc": 200_000, "prestamos_lp": 1_700_000,
        "capital": 2_000_000, "utilidades_retenidas": 1_000_000,
        "ventas": 8_000_000, "costo_ventas": 5_200_000, "gastos_venta": 900_000, "gastos_admin": 700_000,
        "depreciacion": 300_000, "intereses": 200_000,
        "tasa_impuesto": 30, "acciones": 200_000, "precio_accion": 35, "dividendos": 150_000,
    },
    "2025": {
        "efectivo": 520_000, "cuentas_cobrar": 900_000, "inventarios": 1_248_000, "otros_ac": 92_000,
        "ppe": 3_500_000, "otros_anc": 340_000,
        "cuentas_pagar": 780_000, "prestamos_cp": 380_000, "otros_pc": 190_000, "prestamos_lp": 1_800_000,
        "capital": 2_000_000, "utilidades_retenidas": 1_450_000,
        "ventas": 9_200_000, "costo_ventas": 5_888_000, "gastos_venta": 980_000, "gastos_admin": 760_000,
        "depreciacion": 320_000, "intereses": 210_000,
        "tasa_impuesto": 30, "acciones": 200_000, "precio_accion": 45, "dividendos": 279_400,
    },
}

PARAMETROS_EJEMPLO = {
    # Punto de equilibrio y C-V-U
    "pe_origen": "Estados financieros", "pe_precio_ef": 250.0,
    "pe_precio": 250.0, "pe_cvu": 186.0, "pe_cf": 1_080_000.0, "pe_unidades": 36_800.0,
    "pe_utilidad_obj": 1_500_000.0,
    "esc_precio": 0, "esc_cv": 0, "esc_cf": 0, "esc_vol": 0,
    # Apalancamiento
    "ap_dividendos_pref": 0.0, "ap_cambio_ventas": 10,
    # Flujo de efectivo directo
    "fd_saldo_inicial": 520_000.0,
    # Presupuesto maestro
    "pm_precio": 260.0, "pm_costo": 160.0, "pm_contado": 60, "pm_compras_contado": 50,
    "pm_inv_final": 20, "pm_unidades_sig": 9_000.0, "pm_gastos_venta": 10.5,
    "pm_admin_trim": 200_000.0, "pm_dep_trim": 85_000.0, "pm_intereses": 210_000.0,
    "pm_saldo_min": 300_000.0,
    # Presupuesto personal
    "pp_ahorro": 5_000.0, "pp_meta": 20,
}

TRIMESTRES_EJEMPLO = pd.DataFrame({
    "Trimestre": ["T1", "T2", "T3", "T4"],
    "Unidades": [8_500, 9_200, 9_800, 10_500],
    "Inversiones": [1_500_000.0, 250_000.0, 0.0, 150_000.0],
    "Dividendos": [0.0, 150_000.0, 0.0, 200_000.0],
})

MOVIMIENTOS_CAJA_EJEMPLO = pd.DataFrame([
    ("Cobros a clientes", "Operación", "Entrada", 780_000.0),
    ("Pago a proveedores de mercadería", "Operación", "Salida", 450_000.0),
    ("Pago de salarios", "Operación", "Salida", 150_000.0),
    ("Pago de servicios básicos", "Operación", "Salida", 35_000.0),
    ("Pago de impuestos", "Operación", "Salida", 60_000.0),
    ("Compra de equipo de reparto", "Inversión", "Salida", 120_000.0),
    ("Venta de mobiliario usado", "Inversión", "Entrada", 15_000.0),
    ("Préstamo bancario recibido", "Financiamiento", "Entrada", 200_000.0),
    ("Abono a préstamo de largo plazo", "Financiamiento", "Salida", 90_000.0),
    ("Pago de dividendos", "Financiamiento", "Salida", 50_000.0),
], columns=["Concepto", "Actividad", "Tipo", "Monto"])

CATEGORIAS_GASTO = ["Vivienda", "Alimentación", "Transporte", "Servicios básicos", "Educación", "Salud",
                    "Entretenimiento", "Ropa y cuidado personal", "Deudas", "Otros"]

INGRESOS_PERSONALES_EJEMPLO = pd.DataFrame([
    ("Salario mensual", 25_000.0), ("Trabajos independientes", 6_000.0), ("Otros ingresos", 1_500.0),
], columns=["Concepto", "Monto"])

GASTOS_PERSONALES_EJEMPLO = pd.DataFrame([
    ("Vivienda", "Alquiler", 7_000.0, "Necesidad"),
    ("Alimentación", "Supermercado y mercado", 6_500.0, "Necesidad"),
    ("Transporte", "Bus y taxi", 2_200.0, "Necesidad"),
    ("Servicios básicos", "Luz, agua, internet y teléfono", 2_300.0, "Necesidad"),
    ("Educación", "Mensualidad universidad", 2_500.0, "Necesidad"),
    ("Salud", "Medicamentos y consultas", 1_000.0, "Necesidad"),
    ("Entretenimiento", "Cine, streaming y salidas", 1_800.0, "Deseo"),
    ("Ropa y cuidado personal", "Ropa y artículos personales", 1_200.0, "Deseo"),
    ("Alimentación", "Restaurantes y comida rápida", 1_500.0, "Deseo"),
], columns=["Categoría", "Descripción", "Monto", "Tipo"])

PRODUCTOS_EJEMPLO = pd.DataFrame([
    ("P001", "Arroz (saco 100 lb)", 120.0, 1_850.0, 40.0),
    ("P002", "Frijol rojo (saco 100 lb)", 80.0, 2_600.0, 30.0),
    ("P003", "Azúcar (saco 50 kg)", 150.0, 1_450.0, 50.0),
    ("P004", "Aceite vegetal (caja 12 u)", 60.0, 980.0, 25.0),
    ("P005", "Café molido (caja 24 u)", 45.0, 1_320.0, 20.0),
    ("P006", "Harina de trigo (saco 50 lb)", 70.0, 890.0, 30.0),
], columns=["Código", "Producto", "Existencia inicial", "Costo unitario", "Stock mínimo"])

MOVIMIENTOS_INV_EJEMPLO = pd.DataFrame([
    ("2026-10-01", "P001", "Salida", 35.0, "Venta a supermercado"),
    ("2026-10-02", "P002", "Salida", 30.0, "Venta a pulpería"),
    ("2026-10-03", "P003", "Entrada", 60.0, "Compra a proveedor"),
    ("2026-10-05", "P004", "Salida", 20.0, "Venta a mayorista"),
    ("2026-10-06", "P005", "Salida", 15.0, "Venta a cafetería"),
    ("2026-10-08", "P001", "Entrada", 50.0, "Compra a proveedor"),
    ("2026-10-09", "P006", "Salida", 25.0, "Venta a panadería"),
    ("2026-10-10", "P002", "Salida", 28.0, "Venta a mercado"),
    ("2026-10-12", "P003", "Salida", 90.0, "Venta a mayorista"),
    ("2026-10-13", "P004", "Entrada", 30.0, "Compra a proveedor"),
    ("2026-10-15", "P004", "Salida", 22.0, "Venta a pulpería"),
    ("2026-10-16", "P005", "Salida", 12.0, "Venta a cafetería"),
    ("2026-10-18", "P006", "Salida", 20.0, "Venta a panadería"),
    ("2026-10-19", "P001", "Salida", 40.0, "Venta a supermercado"),
], columns=["Fecha", "Código", "Tipo", "Cantidad", "Detalle"])
MOVIMIENTOS_INV_EJEMPLO["Fecha"] = pd.to_datetime(MOVIMIENTOS_INV_EJEMPLO["Fecha"]).dt.date


def _estados_df(estados: dict) -> pd.DataFrame:
    """Tabla cuentas × períodos (todas las cuentas de entrada)."""
    df = pd.DataFrame(estados).astype(float)
    orden = [k for k, *_ in CUENTAS_BALANCE + CUENTAS_RESULTADOS + DATOS_ADICIONALES]
    return df.loc[orden]


TABLAS_EJEMPLO = {
    "estados": lambda: _estados_df(ESTADOS_EJEMPLO),
    "trimestres": lambda: TRIMESTRES_EJEMPLO.copy(),
    "mov_caja": lambda: MOVIMIENTOS_CAJA_EJEMPLO.copy(),
    "ingresos": lambda: INGRESOS_PERSONALES_EJEMPLO.copy(),
    "gastos": lambda: GASTOS_PERSONALES_EJEMPLO.copy(),
    "productos": lambda: PRODUCTOS_EJEMPLO.copy(),
    "mov_inv": lambda: MOVIMIENTOS_INV_EJEMPLO.copy(),
}


# ---------------------------------------------------------------------------
# Estado de la sesión
# ---------------------------------------------------------------------------

def inicializar(forzar: bool = False) -> None:
    """Carga los datos de ejemplo la primera vez (o al restaurar)."""
    ss = st.session_state
    if forzar or "tablas" not in ss:
        ss.tablas = {k: f() for k, f in TABLAS_EJEMPLO.items()}
        ss.params = copy.deepcopy(PARAMETROS_EJEMPLO)
        ss.empresa = copy.deepcopy(EMPRESA)
        _reiniciar_widgets()


def _reiniciar_widgets() -> None:
    ss = st.session_state
    ss.version = ss.get("version", 0) + 1
    for k in [k for k in ss.keys() if str(k).startswith(("w_", "ed_"))]:
        del ss[k]


def tabla(nombre: str) -> pd.DataFrame:
    return st.session_state.tablas[nombre]


def params() -> dict:
    return st.session_state.params


def periodos() -> list[str]:
    return list(tabla("estados").columns)


def cuentas_periodo(periodo: str) -> dict:
    """Cuentas de entrada de un período, con la tasa de impuesto como fracción."""
    p = tabla("estados")[periodo].fillna(0).to_dict()
    p["tasa_impuesto"] = p["tasa_impuesto"] / 100
    return p


def periodo_calculado(periodo: str) -> dict:
    return calc.periodo_completo(cuentas_periodo(periodo))


def agregar_periodo(nombre: str) -> None:
    df = tabla("estados")
    df[nombre] = df[df.columns[-1]]
    _reiniciar_widgets()


def cargar_estados(nueva: pd.DataFrame, reemplazar: bool) -> None:
    """Carga estados importados: reemplaza todos los períodos o agrega/actualiza los importados."""
    ss = st.session_state
    if reemplazar:
        ss.tablas["estados"] = nueva.copy()
    else:
        actual = tabla("estados").copy()
        for p in nueva.columns:
            datos_previos = actual[p] if p in actual.columns else None
            actual[p] = nueva[p]
            # Conserva los datos de mercado ya registrados si el archivo no los trae
            if datos_previos is not None:
                for k in ("acciones", "precio_accion"):
                    if not nueva.loc[k, p]:
                        actual.loc[k, p] = datos_previos[k]
        cols = list(actual.columns)
        if all(str(c).isdigit() for c in cols):
            cols = sorted(cols)
        ss.tablas["estados"] = actual[cols]
    _reiniciar_widgets()


def eliminar_periodo(nombre: str) -> None:
    tabla("estados").drop(columns=[nombre], inplace=True)
    _reiniciar_widgets()


def supuestos_presupuesto() -> dict:
    """Supuestos del presupuesto maestro en el formato que espera el motor de cálculo."""
    P = params()
    ultimo = cuentas_periodo(periodos()[-1])
    return {
        "precio": P["pm_precio"], "costo_unitario": P["pm_costo"],
        "pct_contado": P["pm_contado"] / 100, "pct_compras_contado": P["pm_compras_contado"] / 100,
        "pct_inventario_final": P["pm_inv_final"] / 100, "unidades_siguiente": P["pm_unidades_sig"],
        "pct_gastos_venta": P["pm_gastos_venta"] / 100, "gastos_admin_trim": P["pm_admin_trim"],
        "depreciacion_trim": P["pm_dep_trim"], "intereses_anuales": P["pm_intereses"],
        "saldo_minimo": P["pm_saldo_min"], "tasa_impuesto": ultimo["tasa_impuesto"],
    }


def presupuesto() -> dict:
    """Ejecuta el presupuesto maestro partiendo del último balance registrado."""
    return calc.presupuesto_maestro(supuestos_presupuesto(), tabla("trimestres"),
                                    cuentas_periodo(periodos()[-1]))


def inventario() -> dict:
    return calc.control_inventario(tabla("productos"), tabla("mov_inv"))


def personal() -> dict:
    return calc.presupuesto_personal(tabla("ingresos"), tabla("gastos"), params()["pp_ahorro"])


def cvu_base() -> dict:
    """Datos base del modelo C-V-U según el origen elegido (estados financieros o manual)."""
    P = params()
    if P["pe_origen"] == "Estados financieros":
        return calc.cvu_desde_estados(cuentas_periodo(periodos()[-1]), P["pe_precio_ef"])
    return {"precio": P["pe_precio"], "cv_unitario": P["pe_cvu"], "costos_fijos": P["pe_cf"],
            "unidades": P["pe_unidades"]}


# ---------------------------------------------------------------------------
# Exportar / importar
# ---------------------------------------------------------------------------

def exportar_json() -> str:
    ss = st.session_state
    tablas = {}
    for k, df in ss.tablas.items():
        d = df.copy()
        for c in d.columns:
            if d[c].dtype == object:
                d[c] = d[c].astype(str)
        tablas[k] = json.loads(d.to_json(orient="split", date_format="iso"))
    return json.dumps({"empresa": ss.empresa, "params": ss.params, "tablas": tablas},
                      ensure_ascii=False, indent=2)


def importar_json(texto: str) -> None:
    data = json.loads(texto)
    tablas = {}
    for k, v in data["tablas"].items():
        df = pd.DataFrame(v["data"], index=v["index"], columns=v["columns"])
        if k == "mov_inv":
            df["Fecha"] = pd.to_datetime(df["Fecha"]).dt.date
        if k == "estados":
            df = df.astype(float)
        else:
            df = df.reset_index(drop=True)
        tablas[k] = df
    faltan = set(TABLAS_EJEMPLO) - set(tablas)
    if faltan:
        raise ValueError(f"Faltan tablas en el archivo: {', '.join(sorted(faltan))}")
    ss = st.session_state
    ss.tablas = tablas
    ss.params = {**PARAMETROS_EJEMPLO, **data.get("params", {})}
    ss.empresa = {**EMPRESA, **data.get("empresa", {})}
    _reiniciar_widgets()
