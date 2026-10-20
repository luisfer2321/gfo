"""Motor de cálculos financieros del sistema.

Todas las fórmulas del proyecto viven en este archivo, sin dependencia de la
interfaz web. Cada función recibe datos simples (números, diccionarios o
DataFrames) y devuelve resultados que las páginas solo se encargan de mostrar.
Así, durante la defensa, cualquier cálculo puede localizarse aquí por nombre.

Convenciones:
- Los montos están en córdobas (C$).
- Las tasas y porcentajes se manejan como fracciones (0.30 = 30 %).
- Una división entre cero devuelve ``None`` (se muestra como "N/D").
"""

from __future__ import annotations

import math

import pandas as pd


def dividir(a: float | None, b: float | None) -> float | None:
    """División segura: devuelve None si el divisor es cero o falta un dato."""
    if a is None or b is None or b == 0:
        return None
    return a / b


# ---------------------------------------------------------------------------
# Unidad 2 · Estados financieros
# ---------------------------------------------------------------------------

def estado_resultados(p: dict) -> dict:
    """Construye el Estado de Resultados a partir de las cuentas de un período.

    Utilidad bruta = Ventas − Costo de ventas
    UAII = Utilidad bruta − (Gastos de venta + Gastos de administración + Depreciación)
    UAI = UAII − Gastos por intereses
    Impuesto = UAI × tasa (solo si UAI > 0)
    Utilidad neta = UAI − Impuesto
    """
    ventas = p["ventas"]
    utilidad_bruta = ventas - p["costo_ventas"]
    gastos_operacion = p["gastos_venta"] + p["gastos_admin"] + p["depreciacion"]
    uaii = utilidad_bruta - gastos_operacion
    uai = uaii - p["intereses"]
    impuestos = max(uai, 0) * p["tasa_impuesto"]
    utilidad_neta = uai - impuestos
    return {
        "ventas": ventas,
        "costo_ventas": p["costo_ventas"],
        "utilidad_bruta": utilidad_bruta,
        "gastos_venta": p["gastos_venta"],
        "gastos_admin": p["gastos_admin"],
        "depreciacion": p["depreciacion"],
        "gastos_operacion": gastos_operacion,
        "uaii": uaii,
        "intereses": p["intereses"],
        "uai": uai,
        "impuestos": impuestos,
        "utilidad_neta": utilidad_neta,
    }


def totales_balance(p: dict) -> dict:
    """Totales del Balance General y verificación de la ecuación contable."""
    ac = p["efectivo"] + p["cuentas_cobrar"] + p["inventarios"] + p["otros_ac"]
    anc = p["ppe"] + p["otros_anc"]
    pc = p["cuentas_pagar"] + p["prestamos_cp"] + p["otros_pc"]
    pnc = p["prestamos_lp"]
    patrimonio = p["capital"] + p["utilidades_retenidas"]
    activo = ac + anc
    pasivo = pc + pnc
    return {
        "activo_corriente": ac,
        "activo_no_corriente": anc,
        "activo_total": activo,
        "pasivo_corriente": pc,
        "pasivo_no_corriente": pnc,
        "pasivo_total": pasivo,
        "patrimonio": patrimonio,
        "pasivo_patrimonio": pasivo + patrimonio,
        "diferencia": activo - (pasivo + patrimonio),
    }


def periodo_completo(p: dict) -> dict:
    """Une cuentas, totales del balance y estado de resultados en un solo dict."""
    return {**p, **totales_balance(p), **estado_resultados(p)}


# ---------------------------------------------------------------------------
# Unidad 2 · Análisis horizontal y vertical
# ---------------------------------------------------------------------------

def analisis_horizontal(base: pd.Series, actual: pd.Series) -> pd.DataFrame:
    """Variación absoluta = Actual − Base;  Variación % = (Actual − Base) / Base."""
    df = pd.DataFrame({"base": base, "actual": actual})
    df["var_abs"] = df["actual"] - df["base"]
    df["var_pct"] = [dividir(v, b) for v, b in zip(df["var_abs"], df["base"])]
    return df


def analisis_vertical(valores: pd.Series, total: float) -> pd.Series:
    """Participación % = Cuenta / Total de referencia (Activo total o Ventas)."""
    return valores.apply(lambda v: dividir(v, total))


# ---------------------------------------------------------------------------
# Unidad 2 · Razones financieras
# ---------------------------------------------------------------------------

# (clave, categoría, nombre, unidad, fórmula)
RAZONES = [
    ("razon_corriente", "Liquidez", "Razón corriente", "veces", "Activo corriente ÷ Pasivo corriente"),
    ("prueba_acida", "Liquidez", "Prueba ácida", "veces", "(Activo corriente − Inventarios) ÷ Pasivo corriente"),
    ("razon_efectivo", "Liquidez", "Razón de efectivo", "veces", "Efectivo ÷ Pasivo corriente"),
    ("capital_trabajo", "Liquidez", "Capital de trabajo neto", "C$", "Activo corriente − Pasivo corriente"),
    ("rotacion_inventario", "Actividad", "Rotación de inventarios", "veces", "Costo de ventas ÷ Inventarios"),
    ("dias_inventario", "Actividad", "Días de inventario", "días", "365 ÷ Rotación de inventarios"),
    ("rotacion_cxc", "Actividad", "Rotación de cuentas por cobrar", "veces", "Ventas ÷ Cuentas por cobrar"),
    ("periodo_cobro", "Actividad", "Período promedio de cobro", "días", "Cuentas por cobrar ÷ (Ventas ÷ 365)"),
    ("rotacion_cxp", "Actividad", "Rotación de cuentas por pagar", "veces", "Costo de ventas ÷ Cuentas por pagar"),
    ("periodo_pago", "Actividad", "Período promedio de pago", "días", "Cuentas por pagar ÷ (Costo de ventas ÷ 365)"),
    ("rotacion_activos", "Actividad", "Rotación de activos totales", "veces", "Ventas ÷ Activo total"),
    ("razon_deuda", "Endeudamiento", "Razón de endeudamiento", "%", "Pasivo total ÷ Activo total"),
    ("deuda_patrimonio", "Endeudamiento", "Deuda a patrimonio", "veces", "Pasivo total ÷ Patrimonio"),
    ("multiplicador_capital", "Endeudamiento", "Multiplicador del capital", "veces", "Activo total ÷ Patrimonio"),
    ("cobertura_intereses", "Endeudamiento", "Cobertura de intereses", "veces", "UAII ÷ Gastos por intereses"),
    ("margen_bruto", "Rentabilidad", "Margen de utilidad bruta", "%", "Utilidad bruta ÷ Ventas"),
    ("margen_operativo", "Rentabilidad", "Margen de utilidad operativa", "%", "UAII ÷ Ventas"),
    ("margen_neto", "Rentabilidad", "Margen de utilidad neta", "%", "Utilidad neta ÷ Ventas"),
    ("roa", "Rentabilidad", "Rendimiento sobre activos (ROA)", "%", "Utilidad neta ÷ Activo total"),
    ("roe", "Rentabilidad", "Rendimiento sobre patrimonio (ROE)", "%", "Utilidad neta ÷ Patrimonio"),
    ("upa", "Mercado", "Utilidad por acción (UPA)", "C$", "Utilidad neta ÷ Acciones en circulación"),
    ("precio_utilidad", "Mercado", "Relación precio/utilidad (P/U)", "veces", "Precio por acción ÷ UPA"),
    ("valor_libros_accion", "Mercado", "Valor en libros por acción", "C$", "Patrimonio ÷ Acciones en circulación"),
    ("precio_valor_libros", "Mercado", "Relación precio/valor en libros", "veces", "Precio por acción ÷ Valor en libros por acción"),
    ("dividendo_accion", "Mercado", "Dividendo por acción", "C$", "Dividendos pagados ÷ Acciones en circulación"),
]

INFO_RAZON = {r[0]: {"categoria": r[1], "nombre": r[2], "unidad": r[3], "formula": r[4]} for r in RAZONES}


def razones_financieras(p: dict) -> dict:
    """Calcula todas las razones de un período (usa saldos de cierre)."""
    d = periodo_completo(p)
    rot_inv = dividir(d["costo_ventas"], d["inventarios"])
    rot_cxc = dividir(d["ventas"], d["cuentas_cobrar"])
    rot_cxp = dividir(d["costo_ventas"], d["cuentas_pagar"])
    upa = dividir(d["utilidad_neta"], d["acciones"])
    vla = dividir(d["patrimonio"], d["acciones"])
    precio = d["precio_accion"] or None
    return {
        "razon_corriente": dividir(d["activo_corriente"], d["pasivo_corriente"]),
        "prueba_acida": dividir(d["activo_corriente"] - d["inventarios"], d["pasivo_corriente"]),
        "razon_efectivo": dividir(d["efectivo"], d["pasivo_corriente"]),
        "capital_trabajo": d["activo_corriente"] - d["pasivo_corriente"],
        "rotacion_inventario": rot_inv,
        "dias_inventario": dividir(365, rot_inv),
        "rotacion_cxc": rot_cxc,
        "periodo_cobro": dividir(365, rot_cxc),
        "rotacion_cxp": rot_cxp,
        "periodo_pago": dividir(365, rot_cxp),
        "rotacion_activos": dividir(d["ventas"], d["activo_total"]),
        "razon_deuda": dividir(d["pasivo_total"], d["activo_total"]),
        "deuda_patrimonio": dividir(d["pasivo_total"], d["patrimonio"]),
        "multiplicador_capital": dividir(d["activo_total"], d["patrimonio"]),
        "cobertura_intereses": dividir(d["uaii"], d["intereses"]),
        "margen_bruto": dividir(d["utilidad_bruta"], d["ventas"]),
        "margen_operativo": dividir(d["uaii"], d["ventas"]),
        "margen_neto": dividir(d["utilidad_neta"], d["ventas"]),
        "roa": dividir(d["utilidad_neta"], d["activo_total"]),
        "roe": dividir(d["utilidad_neta"], d["patrimonio"]),
        "upa": upa,
        "precio_utilidad": dividir(precio, upa) if upa and upa > 0 else None,
        "valor_libros_accion": vla,
        "precio_valor_libros": dividir(precio, vla),
        "dividendo_accion": dividir(d["dividendos"], d["acciones"]),
    }


# Rangos de referencia académicos generales: (bueno_desde, aceptable_desde, mayor_es_mejor)
_RANGOS = {
    "razon_corriente": (1.5, 1.0, True),
    "prueba_acida": (1.0, 0.7, True),
    "razon_efectivo": (0.2, 0.1, True),
    "capital_trabajo": (0.0001, 0, True),
    "razon_deuda": (0.5, 0.7, False),
    "deuda_patrimonio": (1.0, 2.0, False),
    "cobertura_intereses": (3.0, 1.5, True),
    "margen_bruto": (0.25, 0.10, True),
    "margen_operativo": (0.10, 0.03, True),
    "margen_neto": (0.05, 0.0, True),
    "roa": (0.05, 0.02, True),
    "roe": (0.12, 0.05, True),
}


def evaluar_razon(clave: str, valor: float | None) -> str:
    """Clasifica una razón como 'bueno', 'aceptable', 'critico' o 'info'."""
    if valor is None:
        return "info"
    if clave not in _RANGOS:
        return "info"
    bueno, aceptable, mayor_mejor = _RANGOS[clave]
    if mayor_mejor:
        return "bueno" if valor >= bueno else "aceptable" if valor >= aceptable else "critico"
    return "bueno" if valor <= bueno else "aceptable" if valor <= aceptable else "critico"


def interpretar_razon(clave: str, v: float | None) -> str:
    """Interpretación breve en lenguaje sencillo de cada razón."""
    if v is None:
        return "No se puede calcular con los datos disponibles (división entre cero)."
    pct = f"{v * 100:,.2f} %"
    textos = {
        "razon_corriente": f"Por cada C$ 1 de deuda a corto plazo hay C$ {v:,.2f} de activos corrientes para cubrirla.",
        "prueba_acida": f"Sin vender inventario, la empresa cubre C$ {v:,.2f} por cada C$ 1 de pasivo corriente.",
        "razon_efectivo": f"Solo con el efectivo disponible se cubre el {pct} del pasivo corriente.",
        "capital_trabajo": (f"Quedan C$ {v:,.2f} de activos corrientes después de cubrir las deudas de corto plazo."
                            if v >= 0 else f"Faltan C$ {-v:,.2f} para cubrir las deudas de corto plazo."),
        "rotacion_inventario": f"El inventario se renueva {v:,.2f} veces durante el año.",
        "dias_inventario": f"En promedio, la mercadería permanece {v:,.0f} días en bodega antes de venderse.",
        "rotacion_cxc": f"Las cuentas por cobrar se recuperan {v:,.2f} veces al año.",
        "periodo_cobro": f"Los clientes tardan en promedio {v:,.0f} días en pagar.",
        "rotacion_cxp": f"Las cuentas por pagar se liquidan {v:,.2f} veces al año.",
        "periodo_pago": f"La empresa tarda en promedio {v:,.0f} días en pagar a sus proveedores.",
        "rotacion_activos": f"Cada C$ 1 invertido en activos genera C$ {v:,.2f} en ventas.",
        "razon_deuda": f"El {pct} de los activos está financiado por acreedores.",
        "deuda_patrimonio": f"Por cada C$ 1 aportado por los dueños hay C$ {v:,.2f} de deuda.",
        "multiplicador_capital": f"Los activos equivalen a {v:,.2f} veces el patrimonio.",
        "cobertura_intereses": f"La utilidad operativa cubre {v:,.2f} veces los intereses del período.",
        "margen_bruto": f"De cada C$ 100 vendidos quedan C$ {v * 100:,.2f} después del costo de ventas.",
        "margen_operativo": f"De cada C$ 100 vendidos quedan C$ {v * 100:,.2f} después de los gastos de operación.",
        "margen_neto": f"De cada C$ 100 vendidos quedan C$ {v * 100:,.2f} de utilidad neta para los dueños.",
        "roa": f"Los activos generan un rendimiento neto del {pct}.",
        "roe": f"La inversión de los accionistas rinde un {pct} en el período.",
        "upa": f"Cada acción generó C$ {v:,.2f} de utilidad neta.",
        "precio_utilidad": f"Los inversionistas pagan C$ {v:,.2f} por cada C$ 1 de utilidad.",
        "valor_libros_accion": f"Contablemente, cada acción respalda C$ {v:,.2f} de patrimonio.",
        "precio_valor_libros": f"El mercado valora la acción en {v:,.2f} veces su valor contable.",
        "dividendo_accion": f"Cada acción recibió C$ {v:,.2f} en dividendos.",
    }
    return textos.get(clave, "")


# ---------------------------------------------------------------------------
# Unidad 2 · Sistema DuPont
# ---------------------------------------------------------------------------

def dupont(p: dict) -> dict:
    """ROE = Margen neto × Rotación de activos totales × Multiplicador del capital."""
    d = periodo_completo(p)
    margen = dividir(d["utilidad_neta"], d["ventas"])
    rotacion = dividir(d["ventas"], d["activo_total"])
    multiplicador = dividir(d["activo_total"], d["patrimonio"])
    roa = margen * rotacion if None not in (margen, rotacion) else None
    roe = roa * multiplicador if None not in (roa, multiplicador) else None
    return {"margen_neto": margen, "rotacion_activos": rotacion, "roa": roa,
            "multiplicador_capital": multiplicador, "roe": roe}


# ---------------------------------------------------------------------------
# Unidad 2 · Punto de equilibrio y modelo Costo-Volumen-Utilidad
# ---------------------------------------------------------------------------

def cvu(precio: float, cv_unitario: float, costos_fijos: float, unidades: float) -> dict:
    """Modelo C-V-U.

    Margen de contribución unitario (MCu) = Precio − Costo variable unitario
    Razón de margen de contribución (RMC) = MCu ÷ Precio
    PE (unidades) = Costos fijos ÷ MCu
    PE (C$) = Costos fijos ÷ RMC
    Utilidad operativa = Unidades × MCu − Costos fijos
    Margen de seguridad = (Ventas esperadas − Ventas en PE) ÷ Ventas esperadas
    GAO = Margen de contribución total ÷ Utilidad operativa
    """
    mcu = precio - cv_unitario
    rmc = dividir(mcu, precio)
    pe_u = dividir(costos_fijos, mcu) if mcu > 0 else None
    pe_c = dividir(costos_fijos, rmc) if rmc and rmc > 0 else None
    ventas = unidades * precio
    costos_variables = unidades * cv_unitario
    mc_total = unidades * mcu
    utilidad = mc_total - costos_fijos
    ms_u = unidades - pe_u if pe_u is not None else None
    return {
        "precio": precio, "cv_unitario": cv_unitario, "costos_fijos": costos_fijos, "unidades": unidades,
        "mcu": mcu, "rmc": rmc, "pe_unidades": pe_u, "pe_monetario": pe_c,
        "ventas": ventas, "costos_variables": costos_variables, "costo_total": costos_variables + costos_fijos,
        "mc_total": mc_total, "utilidad": utilidad,
        "margen_seguridad_u": ms_u,
        "margen_seguridad_pct": dividir(ms_u, unidades) if ms_u is not None else None,
        "gao": dividir(mc_total, utilidad),
    }


def unidades_para_utilidad(precio: float, cv_unitario: float, costos_fijos: float,
                           utilidad_objetivo: float) -> float | None:
    """Unidades necesarias = (Costos fijos + Utilidad deseada) ÷ MCu."""
    mcu = precio - cv_unitario
    return dividir(costos_fijos + utilidad_objetivo, mcu) if mcu > 0 else None


def escenario_cvu(base: dict, cambio_precio: float, cambio_cv: float, cambio_cf: float,
                  cambio_volumen: float) -> dict:
    """Recalcula el modelo C-V-U aplicando cambios porcentuales a cada variable."""
    return cvu(base["precio"] * (1 + cambio_precio),
               base["cv_unitario"] * (1 + cambio_cv),
               base["costos_fijos"] * (1 + cambio_cf),
               base["unidades"] * (1 + cambio_volumen))


def clasificar_costos(p: dict) -> dict:
    """Clasificación de costos del Estado de Resultados para C-V-U y apalancamiento.

    Variables: costo de ventas + gastos de venta (varían con el volumen vendido).
    Fijos: gastos de administración + depreciación.
    """
    return {"costos_variables": p["costo_ventas"] + p["gastos_venta"],
            "costos_fijos": p["gastos_admin"] + p["depreciacion"]}


def cvu_desde_estados(p: dict, precio: float) -> dict:
    """Deriva unidades, costo variable unitario y costos fijos de los estados financieros."""
    c = clasificar_costos(p)
    unidades = dividir(p["ventas"], precio) or 0
    return {"precio": precio, "unidades": unidades,
            "cv_unitario": dividir(c["costos_variables"], unidades) or 0,
            "costos_fijos": c["costos_fijos"]}


# ---------------------------------------------------------------------------
# Unidad 2 · Apalancamiento operativo, financiero y total
# ---------------------------------------------------------------------------

def apalancamiento(ventas: float, costos_variables: float, costos_fijos: float, intereses: float,
                   dividendos_preferentes: float = 0.0, tasa_impuesto: float = 0.0) -> dict:
    """GAO = MC ÷ UAII;  GAF = UAII ÷ [UAII − I − DP ÷ (1 − t)];  GAT = GAO × GAF."""
    mc = ventas - costos_variables
    uaii = mc - costos_fijos
    dp_ajustado = dividir(dividendos_preferentes, 1 - tasa_impuesto) or 0
    base_gaf = uaii - intereses - dp_ajustado
    gao = dividir(mc, uaii)
    gaf = dividir(uaii, base_gaf)
    gat = gao * gaf if None not in (gao, gaf) else None
    return {"ventas": ventas, "costos_variables": costos_variables, "mc": mc,
            "costos_fijos": costos_fijos, "uaii": uaii, "intereses": intereses,
            "uai": uaii - intereses, "gao": gao, "gaf": gaf, "gat": gat}


def efecto_apalancamiento(gao: float, gaf: float, cambio_ventas: float) -> dict:
    """Δ% UAII = GAO × Δ% Ventas;  Δ% UPA = GAT × Δ% Ventas."""
    return {"cambio_ventas": cambio_ventas, "cambio_uaii": gao * cambio_ventas,
            "cambio_upa": gao * gaf * cambio_ventas}


# ---------------------------------------------------------------------------
# Unidad 3 · Estado de flujo de efectivo
# ---------------------------------------------------------------------------

def flujo_efectivo_indirecto(ant: dict, act: dict) -> dict:
    """Flujo de efectivo por el método indirecto a partir de dos balances.

    Operación: Utilidad neta + Depreciación − Δ activos corrientes operativos + Δ pasivos operativos
    Inversión: −(Δ PPE neto + Depreciación) − Δ otros activos no corrientes
    Financiamiento: Δ préstamos + Δ capital − dividendos
    """
    un = estado_resultados(act)["utilidad_neta"]
    def delta(k):
        return act[k] - ant[k]
    operacion = [
        ("Utilidad neta", un),
        ("(+) Depreciación", act["depreciacion"]),
        ("(−) Aumento / (+) disminución en cuentas por cobrar", -delta("cuentas_cobrar")),
        ("(−) Aumento / (+) disminución en inventarios", -delta("inventarios")),
        ("(−) Aumento / (+) disminución en otros activos corrientes", -delta("otros_ac")),
        ("(+) Aumento / (−) disminución en cuentas por pagar", delta("cuentas_pagar")),
        ("(+) Aumento / (−) disminución en otros pasivos corrientes", delta("otros_pc")),
    ]
    inversion = [
        ("Compra (−) / venta (+) de propiedad, planta y equipo", -(delta("ppe") + act["depreciacion"])),
        ("Variación de otros activos no corrientes", -delta("otros_anc")),
    ]
    financiamiento = [
        ("Préstamos a corto plazo obtenidos (+) / pagados (−)", delta("prestamos_cp")),
        ("Préstamos a largo plazo obtenidos (+) / pagados (−)", delta("prestamos_lp")),
        ("Aportes (+) / retiros (−) de capital", delta("capital")),
        ("(−) Dividendos pagados", -act["dividendos"]),
    ]
    fo = sum(v for _, v in operacion)
    fi = sum(v for _, v in inversion)
    ff = sum(v for _, v in financiamiento)
    variacion = fo + fi + ff
    return {
        "operacion": operacion, "inversion": inversion, "financiamiento": financiamiento,
        "flujo_operacion": fo, "flujo_inversion": fi, "flujo_financiamiento": ff,
        "variacion_neta": variacion, "saldo_inicial": ant["efectivo"],
        "saldo_final": ant["efectivo"] + variacion, "saldo_balance": act["efectivo"],
        "conciliado": math.isclose(ant["efectivo"] + variacion, act["efectivo"], abs_tol=0.5),
    }


ACTIVIDADES = ["Operación", "Inversión", "Financiamiento"]


def flujo_efectivo_directo(movimientos: pd.DataFrame, saldo_inicial: float) -> dict:
    """Flujo de efectivo a partir de movimientos de entrada y salida clasificados.

    Flujo por actividad = Σ entradas − Σ salidas de esa actividad
    Saldo final = Saldo inicial + Variación neta
    """
    m = movimientos.dropna(subset=["Monto"]).copy()
    m["Neto"] = m.apply(lambda r: r["Monto"] if r["Tipo"] == "Entrada" else -r["Monto"], axis=1)
    resumen = []
    for act in ACTIVIDADES:
        sub = m[m["Actividad"] == act]
        entradas = sub.loc[sub["Tipo"] == "Entrada", "Monto"].sum()
        salidas = sub.loc[sub["Tipo"] == "Salida", "Monto"].sum()
        resumen.append({"Actividad": act, "Entradas": entradas, "Salidas": salidas, "Flujo neto": entradas - salidas})
    resumen = pd.DataFrame(resumen)
    variacion = resumen["Flujo neto"].sum()
    return {"resumen": resumen, "variacion_neta": variacion, "saldo_inicial": saldo_inicial,
            "saldo_final": saldo_inicial + variacion}


# ---------------------------------------------------------------------------
# Unidad 3 · Presupuesto maestro y estados proforma
# ---------------------------------------------------------------------------

def presupuesto_maestro(s: dict, trimestres: pd.DataFrame, balance: dict) -> dict:
    """Presupuesto maestro trimestral y estados proforma.

    s: supuestos escalares (fracciones para porcentajes).
    trimestres: DataFrame con columnas Trimestre, Unidades, Inversiones (CAPEX), Dividendos.
    balance: cuentas del último período real (saldos iniciales del presupuesto).
    """
    t = trimestres.reset_index(drop=True)
    n = len(t)
    nombres = list(t["Trimestre"])
    unidades = [float(x) for x in t["Unidades"]]
    capex = [float(x) for x in t["Inversiones"]]
    dividendos = [float(x) for x in t["Dividendos"]]
    precio, costo = s["precio"], s["costo_unitario"]

    # 1. Presupuesto de ventas: Ventas = Unidades × Precio
    ventas = [u * precio for u in unidades]

    # 2. Cédula de cobros: contado del trimestre + crédito del trimestre anterior
    contado = s["pct_contado"]
    cobros = []
    for i in range(n):
        anterior = balance["cuentas_cobrar"] if i == 0 else ventas[i - 1] * (1 - contado)
        cobros.append(ventas[i] * contado + anterior)

    # 3. Presupuesto de compras (unidades):
    #    Compras = Ventas + Inventario final deseado − Inventario inicial
    inv_ini_u = dividir(balance["inventarios"], costo) or 0
    sig = unidades[1:] + [s["unidades_siguiente"]]
    inv_final_u = [x * s["pct_inventario_final"] for x in sig]
    inv_inicial_u = [inv_ini_u] + inv_final_u[:-1]
    compras_u = [max(unidades[i] + inv_final_u[i] - inv_inicial_u[i], 0) for i in range(n)]
    compras = [c * costo for c in compras_u]

    # 4. Cédula de pagos a proveedores
    pc = s["pct_compras_contado"]
    pagos = []
    for i in range(n):
        anterior = balance["cuentas_pagar"] if i == 0 else compras[i - 1] * (1 - pc)
        pagos.append(compras[i] * pc + anterior)

    # 5. Costo de bienes vendidos = Inv. inicial + Compras − Inv. final
    inv_final_real = [inv_inicial_u[i] + compras_u[i] - unidades[i] for i in range(n)]
    cbv = [(inv_inicial_u[i] + compras_u[i] - inv_final_real[i]) * costo for i in range(n)]

    # 6. Gastos de operación: variables (% ventas) + fijos + depreciación
    g_var = [v * s["pct_gastos_venta"] for v in ventas]
    g_fijos = [s["gastos_admin_trim"]] * n
    dep = [s["depreciacion_trim"]] * n

    # 7. Estado de resultados proforma (anual)
    p_res = {
        "ventas": sum(ventas), "costo_ventas": sum(cbv), "gastos_venta": sum(g_var),
        "gastos_admin": sum(g_fijos), "depreciacion": sum(dep), "intereses": s["intereses_anuales"],
        "tasa_impuesto": s["tasa_impuesto"],
    }
    er = estado_resultados(p_res)
    impuesto_trim = er["impuestos"] / n
    interes_trim = s["intereses_anuales"] / n

    # 8. Presupuesto de caja con saldo mínimo y financiamiento a corto plazo
    caja = []
    saldo = balance["efectivo"]
    deuda_nueva = 0.0
    for i in range(n):
        egresos = pagos[i] + g_var[i] + g_fijos[i] + interes_trim + impuesto_trim + capex[i] + dividendos[i]
        disponible = saldo + cobros[i]
        antes = disponible - egresos
        financiamiento = 0.0
        if antes < s["saldo_minimo"]:
            financiamiento = s["saldo_minimo"] - antes
        elif deuda_nueva > 0:
            financiamiento = -min(deuda_nueva, antes - s["saldo_minimo"])
        deuda_nueva += financiamiento
        final = antes + financiamiento
        caja.append({
            "Saldo inicial": saldo, "(+) Cobros a clientes": cobros[i], "Efectivo disponible": disponible,
            "(−) Pagos a proveedores": pagos[i], "(−) Gastos de venta": g_var[i],
            "(−) Gastos de administración": g_fijos[i], "(−) Intereses": interes_trim,
            "(−) Impuestos": impuesto_trim, "(−) Inversiones (CAPEX)": capex[i],
            "(−) Dividendos": dividendos[i], "Total egresos": egresos,
            "Saldo antes de financiamiento": antes,
            "Financiamiento (+) / pago (−)": financiamiento, "Saldo final": final,
        })
        saldo = final

    # 9. Balance General proforma (al cierre del último trimestre)
    bp = dict(balance)
    bp.update({
        "efectivo": saldo,
        "cuentas_cobrar": ventas[-1] * (1 - contado),
        "inventarios": inv_final_real[-1] * costo,
        "ppe": balance["ppe"] + sum(capex) - sum(dep),
        "cuentas_pagar": compras[-1] * (1 - pc),
        "prestamos_cp": balance["prestamos_cp"] + deuda_nueva,
        "utilidades_retenidas": balance["utilidades_retenidas"] + er["utilidad_neta"] - sum(dividendos),
    })
    bp.update({k: p_res[k] for k in p_res})
    bp["dividendos"] = sum(dividendos)
    bp["precio_accion"] = balance.get("precio_accion", 0)

    def tabla(filas: dict, primero: tuple = (), ultimo: tuple = (), sin_total: tuple = ()) -> pd.DataFrame:
        """Cédula trimestral con columna anual: suma, o saldo inicial (primero) / final (ultimo) del año."""
        df = pd.DataFrame(filas, index=nombres).T
        df["Total"] = df.sum(axis=1)
        for fila in primero:
            df.loc[fila, "Total"] = df.loc[fila, nombres[0]]
        for fila in ultimo:
            df.loc[fila, "Total"] = df.loc[fila, nombres[-1]]
        for fila in sin_total:
            df.loc[fila, "Total"] = None
        return df

    df_caja = pd.DataFrame(caja, index=nombres).T
    df_caja["Total"] = [
        caja[0][k] if k in ("Saldo inicial",) else caja[-1][k] if k == "Saldo final"
        else None if k in ("Efectivo disponible", "Saldo antes de financiamiento")
        else sum(c[k] for c in caja) for k in df_caja.index
    ]
    compras_df = tabla({"Unidades a vender": unidades, "(+) Inventario final deseado": inv_final_u,
                        "(=) Necesidad total": [unidades[i] + inv_final_u[i] for i in range(n)],
                        "(−) Inventario inicial": inv_inicial_u, "(=) Unidades a comprar": compras_u,
                        "Costo unitario (C$)": [costo] * n, "Compras (C$)": compras},
                       primero=("(−) Inventario inicial",), ultimo=("(+) Inventario final deseado",),
                       sin_total=("Costo unitario (C$)",))
    compras_df.loc["(=) Necesidad total", "Total"] = sum(unidades) + inv_final_u[-1]
    cbv_df = tabla({"Inventario inicial (C$)": [x * costo for x in inv_inicial_u], "(+) Compras (C$)": compras,
                    "(=) Mercadería disponible": [(inv_inicial_u[i] + compras_u[i]) * costo for i in range(n)],
                    "(−) Inventario final (C$)": [x * costo for x in inv_final_real],
                    "(=) Costo de bienes vendidos": cbv},
                   primero=("Inventario inicial (C$)",), ultimo=("(−) Inventario final (C$)",))
    cbv_df.loc["(=) Mercadería disponible", "Total"] = inv_inicial_u[0] * costo + sum(compras)

    return {
        "ventas": tabla({"Unidades a vender": unidades, "Precio de venta (C$)": [precio] * n, "Ventas (C$)": ventas},
                        sin_total=("Precio de venta (C$)",)),
        "cobros": tabla({"Cobro de cuentas por cobrar iniciales / ventas a crédito anteriores":
                         [cobros[i] - ventas[i] * contado for i in range(n)],
                         "Cobro de ventas al contado del trimestre": [v * contado for v in ventas],
                         "Total cobros": cobros}),
        "compras": compras_df,
        "pagos": tabla({"Pago de cuentas por pagar iniciales / compras a crédito anteriores":
                        [pagos[i] - compras[i] * pc for i in range(n)],
                        "Pago de compras al contado del trimestre": [c * pc for c in compras],
                        "Total pagos": pagos}),
        "cbv": cbv_df,
        "gastos": tabla({"Gastos de venta (variables)": g_var, "Gastos de administración (fijos)": g_fijos,
                         "Depreciación (no es salida de efectivo)": dep,
                         "Total gastos de operación": [g_var[i] + g_fijos[i] + dep[i] for i in range(n)]}),
        "caja": df_caja,
        "er_proforma": er,
        "balance_proforma": bp,
        "deuda_nueva": deuda_nueva,
        "saldos": [c["Saldo final"] for c in caja],
        "trimestres": nombres,
    }


# ---------------------------------------------------------------------------
# Aplicación complementaria · Presupuesto personal
# ---------------------------------------------------------------------------

def presupuesto_personal(ingresos: pd.DataFrame, gastos: pd.DataFrame, ahorro_planificado: float) -> dict:
    """Total ingresos, total gastos, capacidad de ahorro y saldo disponible.

    Capacidad de ahorro = Total ingresos − Total gastos
    % de ahorro = Capacidad de ahorro ÷ Total ingresos
    Saldo disponible = Total ingresos − Total gastos − Ahorro planificado
    """
    ti = float(ingresos["Monto"].fillna(0).sum())
    tg = float(gastos["Monto"].fillna(0).sum())
    capacidad = ti - tg
    g = gastos.dropna(subset=["Monto"])
    por_categoria = (g.groupby("Categoría", as_index=False)["Monto"].sum()
                     .sort_values("Monto", ascending=False).reset_index(drop=True))
    por_categoria["% del ingreso"] = por_categoria["Monto"].apply(lambda m: dividir(m, ti))
    necesidades = float(g.loc[g["Tipo"] == "Necesidad", "Monto"].sum())
    deseos = float(g.loc[g["Tipo"] == "Deseo", "Monto"].sum())
    return {
        "total_ingresos": ti, "total_gastos": tg, "capacidad_ahorro": capacidad,
        "pct_ahorro": dividir(capacidad, ti), "ahorro_planificado": ahorro_planificado,
        "saldo_disponible": capacidad - ahorro_planificado, "por_categoria": por_categoria,
        "necesidades": necesidades, "deseos": deseos,
        "pct_necesidades": dividir(necesidades, ti), "pct_deseos": dividir(deseos, ti),
    }


# ---------------------------------------------------------------------------
# Aplicación complementaria · Control básico de inventario
# ---------------------------------------------------------------------------

def control_inventario(productos: pd.DataFrame, movimientos: pd.DataFrame) -> dict:
    """Existencias y valoración del inventario.

    Existencia final = Existencia inicial + Entradas − Salidas
    Valor del inventario = Existencia final × Costo unitario
    Alerta de reposición cuando Existencia final ≤ Stock mínimo
    Cantidad sugerida a comprar = 2 × Stock mínimo − Existencia final
    """
    prod = productos.dropna(subset=["Código"]).copy()
    mov = movimientos.dropna(subset=["Código", "Cantidad"]).copy()
    mov["Fecha"] = pd.to_datetime(mov["Fecha"], errors="coerce")
    filas, kardex, errores = [], [], []
    for _, p in prod.iterrows():
        cod = p["Código"]
        m = mov[mov["Código"] == cod].sort_values("Fecha", kind="stable")
        entradas = float(m.loc[m["Tipo"] == "Entrada", "Cantidad"].sum())
        salidas = float(m.loc[m["Tipo"] == "Salida", "Cantidad"].sum())
        ei = float(p["Existencia inicial"] or 0)
        ef = ei + entradas - salidas
        costo = float(p["Costo unitario"] or 0)
        minimo = float(p["Stock mínimo"] or 0)
        saldo = ei
        kardex.append({"Código": cod, "Fecha": None, "Detalle": "Existencia inicial", "Entrada": 0.0,
                       "Salida": 0.0, "Saldo": saldo, "Valor": saldo * costo})
        for _, r in m.iterrows():
            e = float(r["Cantidad"]) if r["Tipo"] == "Entrada" else 0.0
            s_ = float(r["Cantidad"]) if r["Tipo"] == "Salida" else 0.0
            saldo += e - s_
            if saldo < 0:
                errores.append(f"{cod} · {p['Producto']}: la salida del {r['Fecha']:%d/%m/%Y} deja existencia negativa ({saldo:,.0f}).")
            kardex.append({"Código": cod, "Fecha": r["Fecha"], "Detalle": r.get("Detalle", ""), "Entrada": e,
                           "Salida": s_, "Saldo": saldo, "Valor": saldo * costo})
        alerta = ef <= minimo
        filas.append({
            "Código": cod, "Producto": p["Producto"], "Existencia inicial": ei, "Entradas": entradas,
            "Salidas": salidas, "Existencia final": ef, "Costo unitario": costo,
            "Valor del inventario": ef * costo, "Stock mínimo": minimo,
            "Estado": "Reponer" if alerta else "Suficiente",
            "Cantidad sugerida": max(2 * minimo - ef, 0) if alerta else 0.0,
        })
    resumen = pd.DataFrame(filas)
    sin_producto = sorted(set(mov["Código"]) - set(prod["Código"]))
    for cod in sin_producto:
        errores.append(f"El código {cod} tiene movimientos pero no está registrado en el catálogo de productos.")
    valor = float(resumen["Valor del inventario"].sum()) if len(resumen) else 0.0
    alertas = resumen[resumen["Estado"] == "Reponer"] if len(resumen) else resumen
    return {"resumen": resumen, "kardex": pd.DataFrame(kardex), "valor_total": valor,
            "alertas": alertas, "errores": errores,
            "costo_reposicion": float((alertas["Cantidad sugerida"] * alertas["Costo unitario"]).sum()) if len(alertas) else 0.0}
