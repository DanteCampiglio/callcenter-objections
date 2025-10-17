import streamlit as st
import pandas as pd
import plotly.express as px
from collections import Counter
import unicodedata

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Tablero de Llamadas", layout="wide")

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .caja {
        background-color: #F8F9F4;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #d9d9d9;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    .titulo {
        font-size: 18px;
        font-weight: bold;
        color: #6BA539;
    }
    .valor {
        font-size: 20px;
        font-weight: bold;
        color: #333;
    }
    .scroll-table {
        max-height: 400px;
        overflow-y: auto;
    }
    </style>
""", unsafe_allow_html=True)

# --- CARGA DE DATOS ---
df = pd.read_excel(r"C:\Users\s1246678\syngenta-callcenter\Syngena_callcenter.xlsx")

# Normalizar nombres de columnas
df.columns = [
    unicodedata.normalize('NFKD', col)
    .encode('ascii', 'ignore')
    .decode('utf-8')
    .strip()
    .lower()
    for col in df.columns
]

# --- FILTRO ---
llamadas = ["Todas"] + sorted(df["archivo"].unique().tolist())
seleccion = st.sidebar.selectbox("Seleccionar llamada", llamadas)

if seleccion != "Todas":
    df_filtrado = df[df["archivo"] == seleccion]
else:
    df_filtrado = df.copy()

# --- CÁLCULOS ---
id_llamada = seleccion if seleccion != "Todas" else "Varias"

if seleccion != "Todas":
    exito = "Sí" if (df_filtrado["exito"] == "si").mean() > 0.5 else "No"
else:
    exito = "Varias"

resumen = df_filtrado["resumen"].iloc[0] if seleccion != "Todas" else "Múltiples llamadas"

# Sentimiento promedio
if "sentimiento_speaker1" in df_filtrado.columns and "sentimiento_speaker2" in df_filtrado.columns:
    sentimiento_prom = round((df_filtrado["sentimiento_speaker1"].mean() + df_filtrado["sentimiento_speaker2"].mean()) / 2, 3)
else:
    sentimiento_prom = None

# Duración promedio en minutos
if "duracion_total_seg" in df_filtrado.columns:
    duracion_prom_min = round(df_filtrado["duracion_total_seg"].mean() / 60, 2)
else:
    duracion_prom_min = None

# --- CAJA 1: Métricas principales ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"<div class='caja'><div class='titulo'>ID de la llamada</div><div class='valor'>{id_llamada}</div></div>", unsafe_allow_html=True)
with col2:
    color_exito = "#6BA539" if exito == "Sí" else ("#D9534F" if exito == "No" else "#666666")
    st.markdown(f"<div class='caja'><div class='titulo'>Éxito</div><div class='valor' style='color:{color_exito}'>{exito}</div></div>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<div class='caja'><div class='titulo'>Sentimiento promedio</div><div class='valor'>{sentimiento_prom}</div></div>", unsafe_allow_html=True)
with col4:
    st.markdown(f"<div class='caja'><div class='titulo'>Duración promedio (min)</div><div class='valor'>{duracion_prom_min}</div></div>", unsafe_allow_html=True)

# --- CAJA 2: Resumen ---
st.markdown(f"<div class='caja'><div class='titulo'>Resumen</div><div>{resumen}</div></div>", unsafe_allow_html=True)

# --- PREPARAR DATOS PARA EL GRÁFICO ---
categorias_expandidas = []
for cats in df_filtrado["categoria"].dropna():
    categorias_expandidas.extend([c.strip() for c in str(cats).split(",") if c.strip()])

obj_counts = pd.DataFrame(Counter(categorias_expandidas).items(), columns=["categoria", "cantidad"])

# --- CAJA 3 y 4: Gráfico + Tabla en la misma fila ---
col_izq, col_der = st.columns([1, 1])

with col_izq:
    if obj_counts.empty:
        st.info("No hay objeciones registradas para esta llamada.")
    else:
        st.markdown("<div class='caja'>", unsafe_allow_html=True)
        st.subheader("Distribución de Objeciones")
        fig = px.pie(
            obj_counts,
            names="categoria",
            values="cantidad",
            color_discrete_sequence=["#6BA539", "#A3C940", "#D1E8B1"]
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

with col_der:
    st.markdown("<div class='caja'>", unsafe_allow_html=True)
    st.subheader("Detalle de frases y categorías")
    tabla = df_filtrado[["frase_original", "categoria"]]
    st.markdown("<div class='scroll-table'>", unsafe_allow_html=True)
    st.dataframe(tabla, use_container_width=True, height=400)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)