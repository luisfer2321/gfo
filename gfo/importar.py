"""Importación de estados financieros desde Excel (o CSV).

Lee hojas con el nombre de la cuenta en una columna y los períodos en las
columnas siguientes, por ejemplo:

    Cuenta                 | 2024      | 2025
    Efectivo y equivalentes| 450,000   | 520,000
    Cuentas por cobrar     | 820,000   | 900,000

Las cuentas se reconocen por su nombre (con sinónimos comunes) y se agrupan en
el catálogo del sistema. Las cuentas que no tienen equivalente directo se suman
al rubro "otros" de la sección donde aparecen (activo corriente, pasivo
corriente, etc.). Las filas de totales y utilidades se usan solo para verificar.
"""

from __future__ import annotations

import io
import re
import unicodedata

import pandas as pd

from gfo import calculos as calc
from gfo import datos


def normalizar(texto) -> str:
    """Minúsculas, sin tildes, sin signos ni espacios repetidos."""
    t = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode().lower()
    t = re.sub(r"[^a-z0-9 ]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def a_numero(v) -> float | None:
    """Convierte 1,234.50 / C$ 1 234 / (1,234) / 1.234,50 / -1234 en número; None si no es número."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if not s:
        return None
    negativo = s.startswith("(") and s.endswith(")")
    s = re.sub(r"(?i)c\$|us\$|\$|cordobas?|\s|\(|\)", "", s)
    if s.endswith("-"):
        negativo, s = True, s[:-1]
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".") else s.replace(",", "")
    elif "," in s:
        partes = s.split(",")
        s = s.replace(",", "") if all(len(p) == 3 for p in partes[1:]) else s.replace(",", ".")
    try:
        n = float(s)
    except ValueError:
        return None
    return -abs(n) if negativo else n


# ---------------------------------------------------------------------------
# Reglas de reconocimiento
# ---------------------------------------------------------------------------

# Encabezados de sección del Balance General
SECCIONES = [
    ("ac", r"^(activos? (corrientes?|circulantes?)|activo a corto plazo)$"),
    ("anc", r"^(activos? (no corrientes?|no circulantes?|fijos?|de largo plazo|a largo plazo)|propiedad planta y equipo neto)$"),
    ("pc", r"^(pasivos? (corrientes?|circulantes?|a corto plazo|de corto plazo))$"),
    ("pnc", r"^(pasivos? (no corrientes?|no circulantes?|a largo plazo|de largo plazo|fijos?))$"),
    ("pat", r"^(patrimonio( neto)?|capital contable|capital y reservas|patrimonio de los (socios|accionistas))$"),
    ("activo", r"^activos?$"),
    ("pasivo", r"^pasivos?$"),
]

# Filas de totales o resultados: no se suman, se usan para verificar
TOTALES = [
    ("activo_total", r"^(total|suma) (de )?(los )?activos?$|^total activos? (y|neto)?$"),
    ("pasivo_patrimonio", r"^(total|suma) (de )?(pasivos?|pasivo) (y|mas|\+)? ?(patrimonio|capital)"),
    ("pasivo_total", r"^(total|suma) (de )?(los )?pasivos?$"),
    ("patrimonio", r"^(total|suma) (del? )?(patrimonio|capital contable)"),
    ("utilidad_neta", r"^(utilidad|perdida|resultado|ganancia)( o perdida)? (neta|liquida|del (ejercicio|periodo))"),
    ("uai", r"antes de (impuestos?|ir)"),
    ("uaii", r"^(utilidad|resultado|ganancia) (de |en )?(la )?(operacion|operativa|operacional)|^uaii"),
    ("utilidad_bruta", r"^(utilidad|ganancia|margen|resultado) brut[ao]"),
]
ES_TOTAL = r"^(total|suma|subtotal)\b|^(utilidad|perdida|ganancia|resultado|margen)\b"

# Cuentas del Estado de Resultados (en orden: la primera coincidencia gana)
REGLAS_ER = [
    ("devoluciones", r"devoluci|descuentos? (sobre|en) ventas|rebajas sobre ventas"),
    ("costo_ventas", r"costos? (de|de las|de lo) (ventas?|vendido|mercaderias? vendidas?|bienes vendidos|produccion vendida)|^costo de venta|^costos? de ventas"),
    ("gastos_venta", r"gastos? (de|en) (ventas?|comercializacion|distribucion|mercadeo|venta)|gastos? comerciales?"),
    ("gastos_admin", r"gastos? (de )?(administracion|administrativos?|generales?)|otros gastos (de operacion|operativos?|operacionales?)"),
    ("depreciacion", r"depreciacion|amortizacion"),
    ("intereses", r"intereses|gastos? financieros?|costos? financieros?|cargos? financieros?"),
    ("impuesto", r"impuesto|^ir\b|^i r\b"),
    ("ventas_netas", r"^(ventas|ingresos)( por ventas)? net[oa]s$|^ingresos (netos|totales)$"),
    ("ventas", r"^ventas\b|^ingresos (por|de) (ventas?|actividades ordinarias|operacion)|^ingresos operac|^ventas brutas|^ingresos$"),
]

# Cuentas del Balance General
REGLAS_BG = [
    ("dep_acumulada", r"depreciacion acumulada|amortizacion acumulada|\(?menos\)? depreciacion"),
    ("efectivo", r"^(caja|bancos?|efectivo)\b|efectivo y equivalentes|caja y bancos|caja chica"),
    ("cuentas_cobrar", r"cuentas? por cobrar|clientes|documentos? por cobrar|deudores|estimacion (para )?(cuentas )?incobrables"),
    ("inventarios", r"inventarios?|mercaderias?|mercancias?|almacen|materias? primas?|productos? terminados?"),
    ("ppe", r"propiedad(es)?,? planta|planta y equipo|^terrenos?|^edificios?|maquinaria|mobiliario|vehiculos?|equipo de (computo|oficina|transporte|reparto)|^equipos?$|activos? fijos?|construcciones"),
    ("cuentas_pagar", r"cuentas? por pagar|proveedores|documentos? por pagar"),
    ("prestamos", r"prestamos?|obligaciones (bancarias|financieras)|deudas? (bancarias|financieras)|creditos? bancarios?|hipoteca|sobregiros?|porcion corriente"),
    ("capital", r"^capital( social| suscrito| pagado| aportado| de los socios)?$|^aportes?|^acciones comunes"),
    ("utilidades_retenidas", r"utilidad|perdida|resultados? (acumulados?|del ejercicio|del periodo)|reservas?|superavit|ganancias? retenidas"),
]

# Rubro "otros" según la sección en que aparece una cuenta no reconocida
OTROS_POR_SECCION = {"ac": "otros_ac", "anc": "otros_anc", "pc": "otros_pc", "pnc": "prestamos_lp",
                     "pat": "utilidades_retenidas"}

GASTOS = {"costo_ventas", "gastos_venta", "gastos_admin", "depreciacion", "intereses", "impuesto"}


def _seccion(n: str) -> str | None:
    for clave, patron in SECCIONES:
        if re.search(patron, n):
            return clave
    return None


def _clasificar(n: str, bloque: str, seccion: str | None) -> tuple[str, str | None]:
    """Devuelve (tipo, clave) con tipo en 'cuenta', 'total', 'otros' o 'ignorada'."""
    for clave, patron in TOTALES:
        if re.search(patron, n):
            # "Utilidad del ejercicio" dentro del patrimonio es una cuenta, no un total
            if bloque == "bg" and seccion == "pat" and clave == "utilidad_neta":
                return "cuenta", "utilidades_retenidas"
            return "total", clave
    if re.search(r"^(total|suma|subtotal)\b", n):
        return "total", None
    if bloque == "er":
        for clave, patron in REGLAS_ER:
            if re.search(patron, n):
                return "cuenta", clave
        if re.search(ES_TOTAL, n):
            return "total", None
        return "ignorada", None
    for clave, patron in REGLAS_BG:
        if not re.search(patron, n):
            continue
        if clave == "utilidades_retenidas" and seccion != "pat":
            continue
        if clave == "prestamos":
            return "cuenta", "prestamos_lp" if seccion == "pnc" or "largo plazo" in n else "prestamos_cp"
        if clave == "cuentas_pagar" and (seccion == "pnc" or "largo plazo" in n):
            return "cuenta", "prestamos_lp"
        if clave == "capital" and seccion not in (None, "pat"):
            continue
        return "cuenta", clave
    if re.search(ES_TOTAL, n):
        return "total", None
    if seccion in OTROS_POR_SECCION:
        return "otros", OTROS_POR_SECCION[seccion]
    return "ignorada", None


def _nombre_periodo(v) -> str:
    if isinstance(v, pd.Timestamp) or hasattr(v, "year") and hasattr(v, "month"):
        return str(v.year)
    n = a_numero(v)
    if n is not None and float(n).is_integer():
        return str(int(n))
    s = str(v).strip()
    anios = re.findall(r"\b(?:19|20)\d{2}\b", s)
    return anios[0] if len(set(anios)) == 1 else s


def _es_columna_excluida(encabezado: str) -> bool:
    n = normalizar(encabezado)
    return "%" in str(encabezado) or bool(re.search(r"\b(variacion|var|analisis|porcentaje|codigo|cod|nota|notas)\b", n))


ENCABEZADO_CUENTA = r"^(cuenta|cuentas|concepto|conceptos|descripcion|detalle|rubro|partida|nombre( de la cuenta)?)$"


def leer_hoja(df: pd.DataFrame, hoja: str) -> list[dict]:
    """Extrae las filas de una hoja: [{hoja, fila, cuenta, valores{periodo: num}}]."""
    df = df.dropna(how="all").dropna(axis=1, how="all")
    if df.empty:
        return []
    filas = []
    for idx, fila in df.iterrows():
        celdas = list(fila.values)
        pos = None
        for i, c in enumerate(celdas):
            if c is None or (isinstance(c, float) and pd.isna(c)):
                continue
            if a_numero(c) is None and str(c).strip():
                pos = i
                break
            # Un código contable (1101, 1.1.01) a la izquierda del nombre se salta
        filas.append((idx, celdas, pos))

    # Fila de encabezado: la última fila, antes de la primera fila con montos, cuyas
    # celdas (aparte del rótulo) son todas años o todas texto: "Cuenta | 2024 | 2025".
    encabezado = None
    for idx, celdas, pos in filas:
        resto = [c for j, c in enumerate(celdas) if j != pos and not (c is None or (isinstance(c, float) and pd.isna(c)))]
        if not resto:
            continue
        numeros = [a_numero(c) for c in resto]
        es_anios = all(n is not None and float(n).is_integer() and 1900 <= n <= 2100 for n in numeros)
        textos = all(n is None for n in numeros)
        if es_anios or textos:
            encabezado = (idx, celdas, pos)
        else:
            break

    col_etiqueta = min((p for _, _, p in filas if p is not None), default=0)
    columnas = {}
    if encabezado:
        _, celdas_e, pos_e = encabezado
        for j, c in enumerate(celdas_e):
            if j <= col_etiqueta or j == pos_e or c is None or (isinstance(c, float) and pd.isna(c)):
                continue
            if not _es_columna_excluida(str(c)):
                columnas[j] = _nombre_periodo(c)
    if not columnas:
        n_cols = len(filas[0][1])
        con_numeros = [j for j in range(col_etiqueta + 1, n_cols)
                       if any(p is not None and j > p and a_numero(c[j]) is not None for _, c, p in filas)]
        columnas = {j: f"Período {k + 1}" for k, j in enumerate(con_numeros)}

    salida = []
    for idx, celdas, pos in filas:
        if pos is None or (encabezado and idx == encabezado[0]):
            continue
        valores = {}
        for j, periodo in columnas.items():
            if j < len(celdas) and j > pos:
                n = a_numero(celdas[j])
                if n is not None:
                    valores[periodo] = n
        salida.append({"hoja": hoja, "fila": int(idx) + 1 if isinstance(idx, (int, float)) else idx,
                       "cuenta": str(celdas[pos]).strip(), "valores": valores})
    return salida


def leer_archivos(archivos: list[tuple[str, bytes]]) -> list[dict]:
    """Lee todas las hojas de los archivos subidos (nombre, contenido)."""
    filas = []
    for nombre, contenido in archivos:
        if nombre.lower().endswith((".csv", ".txt")):
            texto = contenido.decode("utf-8-sig", errors="replace")
            sep = ";" if texto.count(";") > texto.count(",") else ","
            hojas = {nombre: pd.read_csv(io.StringIO(texto), header=None, dtype=object, sep=sep)}
        else:
            hojas = pd.read_excel(io.BytesIO(contenido), sheet_name=None, header=None, dtype=object)
        for hoja, df in hojas.items():
            filas += leer_hoja(df, f"{nombre} · {hoja}" if len(archivos) > 1 else str(hoja))
    return filas


def _orden_periodos(periodos: list[str]) -> list[str]:
    if all(re.fullmatch(r"(19|20)\d{2}", p) for p in periodos):
        return sorted(periodos)
    return periodos


def interpretar(filas: list[dict]) -> dict:
    """Asigna cada fila a una cuenta del sistema y arma los estados por período.

    Devuelve: estados {periodo: cuentas}, detalle (DataFrame de asignaciones),
    no_reconocidas, verificaciones (totales del archivo vs. calculados) y avisos.
    """
    periodos: list[str] = []
    acumulado: dict[str, dict] = {}
    totales_archivo: dict[str, dict] = {}
    detalle, no_reconocidas = [], []
    bloque, seccion, hoja_actual = None, None, None

    for f in filas:
        n = normalizar(f["cuenta"])
        if f["hoja"] != hoja_actual:
            hoja_actual, seccion = f["hoja"], None
            hn = normalizar(f["hoja"])
            bloque = "er" if re.search(r"resultado|perdidas|ganancias|er\b", hn) else "bg" if re.search(r"balance|situacion|bg\b", hn) else None
        if re.search(r"estado de resultados?|estado de (perdidas|ganancias)|perdidas y ganancias", n):
            bloque, seccion = "er", None
            continue
        if re.search(r"balance general|estado de situacion", n):
            bloque, seccion = "bg", None
            continue
        s = _seccion(n)
        if s:
            if bloque != "bg":
                bloque = "bg"
            seccion = {"activo": "ac", "pasivo": "pc"}.get(s, s) if s in ("activo", "pasivo") and seccion is None else (s if s not in ("activo", "pasivo") else seccion)
            if not f["valores"]:
                continue
        if not f["valores"]:
            continue
        if bloque is None:
            bloque = "er" if any(re.search(p, n) for _, p in REGLAS_ER[:3] + REGLAS_ER[-2:]) else "bg"
        tipo, clave = _clasificar(n, bloque, seccion)
        for p in f["valores"]:
            if p not in periodos:
                periodos.append(p)
        if tipo == "total":
            if clave:
                for p, v in f["valores"].items():
                    totales_archivo.setdefault(p, {}).setdefault(clave, v)
            detalle.append({"Hoja": f["hoja"], "Cuenta del archivo": f["cuenta"], "Se asignó a": "— (total, solo para verificar)"})
            continue
        if tipo == "ignorada":
            no_reconocidas.append({"Hoja": f["hoja"], "Cuenta del archivo": f["cuenta"],
                                   **{p: v for p, v in f["valores"].items()}})
            continue
        for p, v in f["valores"].items():
            a = acumulado.setdefault(p, {})
            if clave in GASTOS or clave == "devoluciones":
                v = abs(v)
            if clave == "dep_acumulada":
                a["ppe"] = a.get("ppe", 0) - abs(v)
            else:
                a[clave] = a.get(clave, 0) + v
        destino = {"dep_acumulada": "ppe", "devoluciones": "ventas", "ventas_netas": "ventas",
                   "impuesto": "tasa_impuesto"}.get(clave, clave)
        nombre = datos.NOMBRES.get(destino, destino)
        nota = {"dep_acumulada": " (se resta)", "devoluciones": " (se resta)", "impuesto": " (para calcular la tasa)"}.get(clave, "")
        if tipo == "otros":
            nota = " (cuenta no identificada; se agrupa por su sección)"
        detalle.append({"Hoja": f["hoja"], "Cuenta del archivo": f["cuenta"], "Se asignó a": nombre + nota})

    periodos = _orden_periodos(periodos)
    claves_entrada = [k for k, *_ in datos.CUENTAS_BALANCE + datos.CUENTAS_RESULTADOS]
    estados, avisos = {}, []
    for p in periodos:
        a = acumulado.get(p, {})
        e = {k: float(a.get(k, 0.0)) for k in claves_entrada}
        if "ventas_netas" in a:
            e["ventas"] = a["ventas_netas"]
        else:
            e["ventas"] = a.get("ventas", 0.0) - a.get("devoluciones", 0.0)
        er = calc.estado_resultados({**e, "tasa_impuesto": 0})
        if a.get("impuesto") and er["uai"] > 0:
            tasa = round(a["impuesto"] / er["uai"] * 100, 2)
        else:
            tasa = 30.0
            if er["uai"] > 0:
                avisos.append(f"{p}: no se encontró el impuesto sobre la renta; se usó una tasa de 30 %.")
        e.update({"tasa_impuesto": tasa, "acciones": 0.0, "precio_accion": 0.0, "dividendos": 0.0})
        estados[p] = e

    # Dividendos implícitos: UR anterior + Utilidad neta − UR actual
    for anterior, actual in zip(periodos, periodos[1:]):
        un = calc.estado_resultados({**estados[actual], "tasa_impuesto": estados[actual]["tasa_impuesto"] / 100})["utilidad_neta"]
        div = estados[anterior]["utilidades_retenidas"] + un - estados[actual]["utilidades_retenidas"]
        if div > 0.5:
            estados[actual]["dividendos"] = round(div, 2)

    # Verificaciones contra los totales del archivo
    verif = []
    nombres_v = {"activo_total": "Total activo", "pasivo_total": "Total pasivo", "patrimonio": "Total patrimonio",
                 "pasivo_patrimonio": "Total pasivo + patrimonio", "utilidad_bruta": "Utilidad bruta",
                 "uaii": "Utilidad operativa", "uai": "Utilidad antes de impuestos", "utilidad_neta": "Utilidad neta"}
    for p in periodos:
        calculado = calc.periodo_completo({**estados[p], "tasa_impuesto": estados[p]["tasa_impuesto"] / 100})
        for clave, valor in totales_archivo.get(p, {}).items():
            if clave in calculado and clave in nombres_v:
                ok = abs(calculado[clave] - valor) <= max(1.0, abs(valor) * 0.0005)
                verif.append({"Período": p, "Concepto": nombres_v[clave], "Según el archivo": valor,
                              "Calculado por el sistema": calculado[clave], "Coincide": "✓" if ok else "✕"})
        if abs(calculado["diferencia"]) > 0.5:
            avisos.append(f"{p}: el balance no cuadra (Activo − Pasivo − Patrimonio = {calculado['diferencia']:,.2f}).")
        if not calculado["ventas"]:
            avisos.append(f"{p}: no se encontraron ventas; revise el Estado de Resultados.")
        if not calculado["activo_total"]:
            avisos.append(f"{p}: no se encontraron cuentas de activo; revise el Balance General.")

    return {"periodos": periodos, "estados": estados, "detalle": pd.DataFrame(detalle),
            "no_reconocidas": pd.DataFrame(no_reconocidas), "verificaciones": pd.DataFrame(verif), "avisos": avisos}


def a_tabla(estados: dict) -> pd.DataFrame:
    """Convierte los estados interpretados en la tabla cuentas × períodos del sistema."""
    orden = [k for k, *_ in datos.CUENTAS_BALANCE + datos.CUENTAS_RESULTADOS + datos.DATOS_ADICIONALES]
    return pd.DataFrame(estados).astype(float).loc[orden]


def plantilla_excel(tabla: pd.DataFrame) -> bytes:
    """Genera un Excel de ejemplo con Balance General, Estado de Resultados y datos complementarios."""
    periodos = list(tabla.columns)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        filas = []
        grupo = None
        for k, n, g in datos.CUENTAS_BALANCE:
            if g != grupo:
                filas.append([g.upper()] + [None] * len(periodos))
                grupo = g
            filas.append([n] + [tabla.loc[k, p] for p in periodos])
        bg = pd.DataFrame(filas, columns=["Cuenta"] + periodos)
        bg.to_excel(w, sheet_name="Balance General", index=False)
        er = pd.DataFrame([[n] + [tabla.loc[k, p] for p in periodos] for k, n in datos.CUENTAS_RESULTADOS]
                          + [["Impuesto sobre la renta"] + [calc.estado_resultados(
                              {**tabla[p].to_dict(), "tasa_impuesto": tabla.loc["tasa_impuesto", p] / 100})["impuestos"]
                              for p in periodos]],
                          columns=["Cuenta"] + periodos)
        er.to_excel(w, sheet_name="Estado de Resultados", index=False)
        for hoja in w.sheets.values():
            hoja.column_dimensions["A"].width = 38
            for col in "BCDEFG":
                hoja.column_dimensions[col].width = 16
            for fila in hoja.iter_rows(min_row=2, min_col=2):
                for c in fila:
                    c.number_format = "#,##0.00"
    return buf.getvalue()
