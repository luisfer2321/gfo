# Sistema de Análisis y Planeación Financiera

Proyecto integrador de **Gestión Financiera Operativa (IS2122)**. Es una aplicación web hecha en Python que
integra los contenidos de la **Unidad 2 – Análisis Financiero** y la **Unidad 3 – Planeación Financiera**. También
incluye dos aplicaciones prácticas complementarias: un **presupuesto personal** y un **control básico de inventario**.

## Tecnologías

| Herramienta | Uso |
|---|---|
| Python 3.10+ | Lenguaje del sistema |
| [Streamlit](https://streamlit.io) | Interfaz web, navegación y formularios |
| [Plotly](https://plotly.com/python/) | Gráficos interactivos |
| pandas / NumPy | Tablas y cálculos |
| pytest | Pruebas que comparan los cálculos con resultados hechos a mano |

## Cómo ejecutarlo

```bash
pip install -r requirements.txt
streamlit run app.py
```

Se abre en el navegador en `http://localhost:8501`. Para correr las pruebas:

```bash
python -m pytest
```

## Módulos

| Módulo | Contenido | Página |
|---|---|---|
| Panel principal | Indicadores clave de todos los módulos y acceso rápido | `vistas/inicio.py` |
| Estados financieros | Balance General y Estado de Resultados de uno o más períodos, escritos a mano o importados desde Excel | `vistas/estados.py` |
| Análisis financiero | Análisis horizontal y vertical, 25 razones financieras y sistema DuPont | `vistas/analisis.py` |
| Punto de equilibrio y C-V-U | PE en unidades y en C$, margen de seguridad, escenarios, sensibilidad y utilidad deseada | `vistas/equilibrio.py` |
| Apalancamiento | GAO, GAF y GAT, con su comprobación | `vistas/apalancamiento.py` |
| Flujo de efectivo | Método indirecto desde los balances y registro directo de entradas y salidas | `vistas/flujo.py` |
| Planeación y presupuestos | Presupuestos de ventas, cobros, compras, pagos, costo de bienes vendidos, gastos y caja | `vistas/presupuestos.py` |
| Proforma y reporte integrado | Estado de resultados y balance proforma, indicadores reales vs. proyectados y hallazgos | `vistas/proforma.py` |
| Presupuesto personal | Ingresos, gastos, capacidad de ahorro, saldo disponible y regla 50/30/20 | `vistas/personal.py` |
| Control de inventario | Existencia final, valor del inventario, alertas de reposición y kárdex | `vistas/inventario.py` |
| Fórmulas utilizadas | Referencia de fórmulas, criterios y ubicación en el código | `vistas/formulas.py` |

## Integración entre módulos

```
Estados financieros ──► Análisis (horizontal, vertical, razones, DuPont)
        │           ──► Punto de equilibrio (unidades, costo variable y costos fijos desde el ER)
        │           ──► Apalancamiento (MC, UAII e intereses desde el ER)
        │           ──► Flujo de efectivo (método indirecto entre dos balances)
        └─ último balance ──► Presupuesto maestro (saldos iniciales) ──► Estados proforma ──► Reporte integrado
Control de inventario ──► alertas de reposición en el presupuesto de compras y en el reporte integrado
```

Los datos se capturan una sola vez y los demás módulos los reutilizan. Por ejemplo, si cambia las ventas en
*Estados financieros*, se actualizan las razones, el punto de equilibrio, el apalancamiento y el panel principal.

## Organización del código

```
app.py              Punto de entrada: configuración, navegación y barra lateral
gfo/calculos.py     TODAS las fórmulas financieras (funciones puras, sin interfaz)
gfo/importar.py     Lectura de estados financieros desde Excel/CSV
gfo/reporte.py      Reporte de análisis en Excel (exportación)
gfo/datos.py        Catálogo de cuentas, datos de ejemplo y manejo del estado de la sesión
gfo/ui.py           Estilos, formatos (C$, %, veces, días), tarjetas y gráficos
vistas/*.py         Una página por módulo (solo muestra resultados)
tests/              Pruebas que validan los cálculos con resultados hechos a mano
```

Para encontrar un cálculo durante la defensa, busque en `gfo/calculos.py`. Cada página indica debajo de la fórmula
qué función hace el cálculo (por ejemplo, `gfo/calculos.py → cvu()`).

## Importar estados financieros desde Excel

En **Estados financieros → Importar desde Excel** se pueden subir el Balance General y el Estado de Resultados
(`.xlsx` o `.csv`), en un solo archivo o en varios. El formato es libre: una columna con el nombre de la cuenta y
una columna por período (`2024`, `2025`, `Al 31/12/2025`…). Se aceptan títulos, códigos contables, filas de
totales, montos con `C$`, montos entre paréntesis y gastos en negativo.

- Las cuentas se reconocen por su nombre y sinónimos comunes (Caja + Bancos → Efectivo; Clientes → Cuentas por
  cobrar; Edificios + Vehículos − Depreciación acumulada → PPE neto; Ventas − Devoluciones → Ventas netas…).
- Una cuenta sin equivalente directo se suma al rubro "otros" de la sección donde aparece (por ejemplo, IVA
  acreditable → Otros activos corrientes).
- La tasa de impuesto se calcula con Impuesto ÷ UAI, y los dividendos con la variación de las utilidades retenidas.
- Las filas de totales del archivo se comparan con los totales que calcula el sistema.
- Antes de aplicar, se muestra una vista previa, cómo se asignó cada fila y las filas que no se reconocieron.

Hay una plantilla de ejemplo para descargar en esa misma pestaña. El código está en `gfo/importar.py`.

## Exportar el análisis a Excel

El botón **Exportar análisis a Excel** (barra lateral, y también en *Proforma y reporte integrado*) descarga un
libro con una hoja por análisis de la empresa:

Resumen (indicadores clave, diagnóstico, hallazgos y gráfico) · Balance General · Estado de Resultados ·
Análisis horizontal · Análisis vertical · Razones financieras · Sistema DuPont · Punto de equilibrio (con
escenarios, sensibilidad y gráfico) · Apalancamiento · Flujo de efectivo · Presupuesto maestro (cédulas y
gráficos) · Estados proforma.

No incluye el presupuesto personal ni el control de inventario. El código está en `gfo/reporte.py` y usa las
mismas funciones de `gfo/calculos.py` que la aplicación, así que los valores coinciden con los de pantalla.

## Manejo de datos

El sistema **no usa base de datos**. Mientras está abierto, la información se guarda en la memoria de la sesión
del navegador (`st.session_state`). Desde la barra lateral, en **Guardar o cargar datos**, se puede:

- **Exportar** todos los datos a un archivo JSON.
- **Importar** un archivo JSON guardado antes.
- **Restaurar** los datos de ejemplo.

## Caso de ejemplo

Los datos de ejemplo son ficticios pero coherentes: *Distribuidora El Progreso, S.A.*, períodos 2024 y 2025, en
córdobas. Con ellos:

- El balance cuadra en ambos períodos.
- El flujo de efectivo indirecto concilia con el efectivo del balance (C$ 450,000 + C$ 70,000 = C$ 520,000).
- El ROE de DuPont es igual a Utilidad neta ÷ Patrimonio (21.14 %).
- La utilidad del modelo C-V-U es igual a la UAII del Estado de Resultados (C$ 1,252,000).
- El balance proforma cuadra.

Las pruebas en `tests/test_calculos.py` verifican estos resultados y otros cálculos hechos a mano.
