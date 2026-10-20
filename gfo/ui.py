"""Componentes visuales compartidos: estilos, formatos, tarjetas y gráficos."""

from __future__ import annotations

import html

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Paleta categórica (orden fijo, validada para daltonismo) y colores de estado.
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
ESTADO = {"bueno": "#0ca30c", "aceptable": "#fab219", "alerta": "#ec835a", "critico": "#d03b3b", "info": "#898781"}
ESTADO_TXT = {"bueno": "Favorable", "aceptable": "Aceptable", "critico": "Desfavorable", "info": "Informativo"}
ESTADO_ICONO = {"bueno": "✓", "aceptable": "!", "critico": "✕", "info": "i"}
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, BASELINE, SURFACE = "#e1e0d9", "#c3c2b7", "#ffffff"
FUENTE = 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif'


# ---------------------------------------------------------------------------
# Formatos con unidades
# ---------------------------------------------------------------------------

def nd(f):
    def envoltura(v, *a, **k):
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return "N/D"
        return f(v, *a, **k)
    return envoltura


@nd
def cs(v, dec: int = 2) -> str:
    signo = "−" if v < 0 else ""
    return f"{signo}C$ {abs(v):,.{dec}f}"


@nd
def pct(v, dec: int = 2) -> str:
    return f"{v * 100:,.{dec}f} %".replace("-", "−")


@nd
def veces(v, dec: int = 2) -> str:
    return f"{v:,.{dec}f} veces"


@nd
def dias(v) -> str:
    return f"{v:,.0f} días"


@nd
def num(v, dec: int = 0) -> str:
    return f"{v:,.{dec}f}".replace("-", "−")


def por_unidad(v, unidad: str) -> str:
    return {"C$": cs, "%": pct, "veces": veces, "días": dias}.get(unidad, num)(v)


def md(texto: str) -> str:
    """Escapa "$" para que Markdown no interprete "C$ … C$" como una fórmula LaTeX."""
    return texto.replace("$", "\\$")


def corto(v: float) -> str:
    """C$ 1.25 M / C$ 830.5 mil para etiquetas de gráficos."""
    a = abs(v)
    s = "−" if v < 0 else ""
    if a >= 1e6:
        return f"{s}C$ {a / 1e6:,.2f} M"
    if a >= 1e3:
        return f"{s}C$ {a / 1e3:,.1f} mil"
    return f"{s}C$ {a:,.0f}"


# ---------------------------------------------------------------------------
# Estilos de la página
# ---------------------------------------------------------------------------

CSS = """
<style>
:root { --ink:#0b0b0b; --ink2:#52514e; --muted:#898781; --line:rgba(11,11,11,.09);
        --accent:#2a78d6; --card:#ffffff; }
.block-container { padding-top: 3.2rem; padding-bottom: 4rem; max-width: 1280px; }
h1, h2, h3 { letter-spacing: -0.01em; }
[data-testid="stSidebar"] { border-right: 1px solid var(--line); }
.hero { border-radius: 18px; padding: 26px 30px; margin-bottom: 18px; color: #fff;
        background: linear-gradient(120deg, #0d366b 0%, #1c5cab 55%, #2a78d6 100%);
        box-shadow: 0 10px 30px rgba(13,54,107,.18); }
.hero .eyebrow { text-transform: uppercase; letter-spacing: .12em; font-size: .74rem; opacity: .8; font-weight: 600; }
.hero h1 { color: #fff; margin: .2rem 0 .3rem 0; font-size: 1.9rem; padding: 0; }
.hero p { margin: 0; opacity: .88; font-size: .98rem; }
.page-head { margin-bottom: 1.1rem; }
.page-head .eyebrow { color: var(--accent); text-transform: uppercase; letter-spacing: .1em; font-size: .74rem; font-weight: 700; }
.page-head h1 { margin: .15rem 0 .25rem 0; font-size: 1.85rem; padding: 0; }
.page-head p { color: var(--ink2); margin: 0; font-size: .98rem; max-width: 860px; }
.kpi { background: var(--card); border: 1px solid var(--line); border-radius: 14px; padding: 15px 17px 13px;
       height: 100%; box-shadow: 0 1px 2px rgba(11,11,11,.04); }
.kpi .lbl { color: var(--ink2); font-size: .8rem; font-weight: 600; display:flex; gap:.4rem; align-items:center; }
.kpi .val { color: var(--ink); font-size: 1.55rem; font-weight: 700; margin-top: 4px; line-height: 1.2; }
.kpi .sub { color: var(--muted); font-size: .8rem; margin-top: 5px; display:flex; flex-wrap:wrap; gap:.35rem; align-items:center; }
.kpi .delta-up { color: #006300; font-weight: 600; } .kpi .delta-down { color: #b42828; font-weight: 600; }
.chip { display:inline-flex; align-items:center; gap:.3rem; font-size:.74rem; font-weight:600; padding:2px 9px 2px 6px;
        border-radius:999px; border:1px solid var(--line); color: var(--ink); background:#fff; white-space:nowrap; }
.chip i { font-style:normal; display:inline-grid; place-items:center; width:15px; height:15px; border-radius:50%;
          color:#fff; font-size:.62rem; font-weight:800; }
.ratio { background: var(--card); border: 1px solid var(--line); border-radius: 14px; padding: 14px 16px; margin-bottom: 12px; }
.ratio .top { display:flex; justify-content:space-between; gap:.6rem; align-items:flex-start; }
.ratio .name { font-weight: 650; color: var(--ink); font-size: .93rem; }
.ratio .formula { color: var(--muted); font-size: .76rem; margin-top: 1px; }
.ratio .vals { display:flex; gap:1.2rem; margin-top: 8px; flex-wrap: wrap; }
.ratio .vals div { font-size: .78rem; color: var(--ink2); }
.ratio .vals b { display:block; font-size: 1.18rem; color: var(--ink); font-weight: 700; }
.ratio .txt { color: var(--ink2); font-size: .84rem; margin-top: 7px; line-height: 1.4; }
.formula-box { background:#f4f8fd; border:1px solid #d6e5f7; border-radius: 12px; padding: 12px 15px;
               color:#0d366b; font-size:.88rem; line-height:1.55; }
.formula-box code { background: transparent; color:#0d366b; font-weight:600; }
.note { color: var(--ink2); font-size: .85rem; }
.stmt { width:100%; border-collapse: collapse; font-size: .9rem; font-variant-numeric: tabular-nums; }
.stmt th { text-align:right; color: var(--ink2); font-weight:600; font-size:.8rem; border-bottom: 1px solid #c3c2b7; padding: 6px 8px; }
.stmt th:first-child { text-align:left; }
.stmt td { padding: 5px 8px; border-bottom: 1px solid #efeee9; text-align:right; color: var(--ink); }
.stmt td:first-child { text-align:left; }
.stmt tr.grupo td { font-weight:700; color: var(--accent); background:#f7f9fc; text-transform: uppercase; font-size:.76rem; letter-spacing:.06em; }
.stmt tr.sub td { font-weight:650; background:#fafaf8; }
.stmt tr.total td { font-weight:800; border-top: 1.5px solid #52514e; border-bottom: 3px double #52514e; }
.stmt td.neg { color:#b42828; }
.module-card { background:#fff; border:1px solid var(--line); border-radius:14px; padding:14px 16px; height:100%; }
.module-card .t { font-weight:700; font-size:.95rem; } .module-card .d { color:var(--ink2); font-size:.82rem; margin-top:2px; }
div[data-testid="stMetric"] { background:#fff; border:1px solid var(--line); border-radius:14px; padding:12px 16px; }
.stTabs [data-baseweb="tab-list"] { gap: 4px; }
.stTabs [data-baseweb="tab"] { padding: 8px 14px; border-radius: 8px 8px 0 0; }
footer { visibility: hidden; }
</style>
"""


def estilos() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def encabezado(titulo: str, descripcion: str, unidad: str = "") -> None:
    st.markdown(
        f'<div class="page-head"><div class="eyebrow">{html.escape(unidad)}</div>'
        f"<h1>{html.escape(titulo)}</h1><p>{descripcion}</p></div>",
        unsafe_allow_html=True,
    )


def chip(estado: str, texto: str | None = None) -> str:
    color = ESTADO.get(estado, MUTED)
    icono = ESTADO_ICONO.get(estado, "i")
    texto = texto or ESTADO_TXT.get(estado, "")
    return f'<span class="chip"><i style="background:{color}">{icono}</i>{html.escape(texto)}</span>'


def kpi(etiqueta: str, valor: str, sub: str = "", estado: str | None = None, delta: float | None = None) -> str:
    extra = chip(estado) if estado else ""
    d = ""
    if delta is not None:
        clase = "delta-up" if delta >= 0 else "delta-down"
        flecha = "▲" if delta >= 0 else "▼"
        d = f'<span class="{clase}">{flecha} {pct(abs(delta), 1)}</span> '
    return (f'<div class="kpi"><div class="lbl">{html.escape(etiqueta)}</div>'
            f'<div class="val">{html.escape(valor)}</div><div class="sub">{extra} {d}{html.escape(sub)}</div></div>')


def fila_kpis(items: list[str]) -> None:
    cols = st.columns(len(items))
    for c, h in zip(cols, items):
        c.markdown(h, unsafe_allow_html=True)


def formula(texto: str) -> None:
    st.markdown(f'<div class="formula-box">{texto}</div>', unsafe_allow_html=True)


def tabla_estado(filas: list[tuple], columnas: list[str], fmt=cs) -> None:
    """Tabla con formato contable. filas: (etiqueta, valores, estilo) con estilo en '', 'grupo', 'sub', 'total'."""
    cab = "".join(f"<th>{html.escape(c)}</th>" for c in ["Cuenta"] + columnas)
    cuerpo = []
    for etiqueta, valores, estilo in filas:
        if estilo == "grupo":
            cuerpo.append(f'<tr class="grupo"><td colspan="{len(columnas) + 1}">{html.escape(etiqueta)}</td></tr>')
            continue
        celdas = []
        for v in valores:
            if isinstance(v, str):
                celdas.append(f"<td>{html.escape(v)}</td>")
            else:
                neg = ' class="neg"' if v is not None and v < 0 else ""
                celdas.append(f"<td{neg}>{fmt(v)}</td>")
        cuerpo.append(f'<tr class="{estilo}"><td>{html.escape(etiqueta)}</td>{"".join(celdas)}</tr>')
    st.markdown(f'<div style="overflow-x:auto"><table class="stmt"><thead><tr>{cab}</tr></thead>'
                f'<tbody>{"".join(cuerpo)}</tbody></table></div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Gráficos (Plotly)
# ---------------------------------------------------------------------------

def figura(titulo: str = "", alto: int = 360, leyenda: bool = True) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        title=dict(text=f"<b>{titulo}</b>" if titulo else "", x=0, xanchor="left", font=dict(size=15, color=INK)),
        height=alto, font=dict(family=FUENTE, color=INK2, size=12.5),
        paper_bgcolor=SURFACE, plot_bgcolor=SURFACE, colorway=SERIES,
        margin=dict(l=12, r=16, t=56 if titulo else 24, b=12),
        showlegend=leyenda,
        legend=dict(orientation="h", yanchor="top", y=-0.12, xanchor="left", x=0, bgcolor="rgba(0,0,0,0)",
                    font=dict(size=12, color=INK2)),
        hoverlabel=dict(bgcolor="#ffffff", bordercolor=BASELINE, font=dict(family=FUENTE, color=INK, size=12.5)),
        bargap=0.32, bargroupgap=0.08,
    )
    fig.update_xaxes(showgrid=False, linecolor=BASELINE, ticks="", tickfont=dict(color=MUTED), zeroline=False)
    fig.update_xaxes(automargin=True)
    fig.update_yaxes(gridcolor=GRID, gridwidth=1, zeroline=True, zerolinecolor=BASELINE, zerolinewidth=1,
                     linecolor=GRID, tickfont=dict(color=MUTED), separatethousands=True, automargin=True,
                     exponentformat="none")
    return fig


def linea_referencia(fig: go.Figure, x, valor: float, nombre: str, color: str = ESTADO["critico"]) -> None:
    """Línea horizontal de referencia identificada en la leyenda (no tapa etiquetas)."""
    fig.add_scatter(x=[x[0], x[-1]] if len(x) else [], y=[valor, valor], mode="lines", name=nombre,
                    line=dict(color=color, width=1.5), hovertemplate=nombre + ": %{y:,.2f}<extra></extra>")


def mostrar(fig: go.Figure, key: str | None = None) -> None:
    st.plotly_chart(fig, theme=None, key=key, config={"displayModeBar": False, "locale": "es"})


def barras(fig: go.Figure, x, y, nombre: str, color: str, texto=None, horizontal: bool = False, **kw) -> None:
    """Barra delgada con esquinas redondeadas y separación respecto de la superficie."""
    datos = dict(y=x, x=y, orientation="h") if horizontal else dict(x=x, y=y)
    fig.add_bar(name=nombre, marker=dict(color=color, line=dict(color=SURFACE, width=2), cornerradius=4),
                text=texto, textposition="outside" if texto is not None else None,
                textfont=dict(color=INK2, size=11.5), constraintext="none", cliponaxis=False, **datos, **kw)


# ---------------------------------------------------------------------------
# Entradas que conservan su valor al cambiar de página
# ---------------------------------------------------------------------------

def _params() -> dict:
    return st.session_state.params


def entrada(etiqueta: str, clave: str, **kw):
    """number_input enlazado a st.session_state.params[clave]."""
    P = _params()
    k = f"w_{clave}_{st.session_state.version}"
    valor = st.number_input(etiqueta, value=P[clave], key=k, **kw)
    P[clave] = valor
    return valor


def deslizador(etiqueta: str, clave: str, **kw):
    P = _params()
    k = f"w_{clave}_{st.session_state.version}"
    valor = st.slider(etiqueta, value=P[clave], key=k, **kw)
    P[clave] = valor
    return valor


def selector(etiqueta: str, clave: str, opciones: list, **kw):
    P = _params()
    k = f"w_{clave}_{st.session_state.version}"
    valor = st.segmented_control(etiqueta, opciones, default=P[clave], key=k, required=True, **kw)
    P[clave] = valor
    return valor


def _aplicar_cambios(nombre: str, clave: str, filas: list | None) -> None:
    """Aplica las ediciones del data_editor a la tabla guardada en la sesión."""
    cambios = st.session_state[clave]
    df = st.session_state.tablas[nombre].copy()
    indice = filas if filas is not None else list(df.index)
    for pos, valores in cambios.get("edited_rows", {}).items():
        fila = indice[int(pos)]
        for col, v in valores.items():
            df.loc[fila, col] = v
    if filas is None:
        borrar = [df.index[int(i)] for i in cambios.get("deleted_rows", [])]
        df = df.drop(index=borrar)
        nuevas = [{c: f.get(c) for c in df.columns} for f in cambios.get("added_rows", [])]
        if nuevas:
            df = pd.concat([df, pd.DataFrame(nuevas)], ignore_index=True)
        df = df.reset_index(drop=True)
    st.session_state.tablas[nombre] = df
    st.session_state.ver_tablas = st.session_state.get("ver_tablas", 0) + 1


def editor(nombre: str, filas: list | None = None, etiquetas: dict | None = None, **kw) -> pd.DataFrame:
    """data_editor persistente: los cambios se guardan en st.session_state.tablas[nombre].

    filas: subconjunto de filas (índices) a mostrar; etiquetas: nombres visibles de esas filas.
    """
    ver = f"{st.session_state.version}_{st.session_state.get('ver_tablas', 0)}"
    clave = f"ed_{nombre}_{'-'.join(map(str, filas or []))[:40]}_{ver}"
    df = st.session_state.tablas[nombre]
    vista = df.loc[filas] if filas is not None else df
    if etiquetas:
        vista = vista.rename(index=etiquetas)
    if filas is not None:
        kw.setdefault("height", (len(filas) + 1) * 35 + 3)  # muestra todas las cuentas sin desplazamiento
    st.data_editor(vista, key=clave, on_change=_aplicar_cambios, args=(nombre, clave, filas), **kw)
    return st.session_state.tablas[nombre]
