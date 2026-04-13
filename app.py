import streamlit as st  # La librería principal que transforma este script en una página web interactiva.
import pandas as pd     # El motor de análisis de datos que usamos para manipular las tablas (DataFrames).
import os               # Proporciona funciones para interactuar con el sistema operativo (leer carpetas y archivos).

# ==========================================
# IMPORTACIÓN DE MÓDULOS PERSONALIZADOS (Modularización)
# ==========================================
# En lugar de tener un archivo de 500 líneas, "dividimos el trabajo". 
# Estos archivos viven en la carpeta /src y cada uno tiene una tarea específica:
from src.utils import generate_universe  # Genera la "tabla ideal" de experimentos.
from src.visualizations import render_scatter_plots, render_categorical_impact  # Dibuja las gráficas.
from src.gap_analysis_ui import render_gap_analysis  # Gestiona la lógica de qué experimentos faltan.

# ==========================================
# CONFIGURACIÓN DE LA PÁGINA
# ==========================================
# st.set_page_config DEBE ser el primer comando de Streamlit. 
# Define el título que veo en la pestaña del navegador y usa el diseño 'wide' (ancho) 
# para aprovechar todo el espacio horizontal de la pantalla.
st.set_page_config(page_title="DoE - CFRTPC Composites", layout="wide")

# Definimos la ruta donde vive nuestra base de datos.
# Usar os.path.join asegura que el código funcione tanto en Windows como en la nube (Linux).
FILE_PATH = os.path.join('data', 'dataset.xlsx')

# @st.cache_data es una función mágica de Streamlit. 
# "Memoriza" el contenido del Excel en la RAM. Si cambias de pestaña en la web, 
# Streamlit no vuelve a leer el archivo del disco (lo cual es lento), 
# sino que usa la copia en memoria. Esto hace que la app sea instantánea.
@st.cache_data
def load_data():
    """Lee el archivo Excel y devuelve un diccionario donde cada llave es el nombre de una pestaña."""
    if os.path.exists(FILE_PATH):
        # sheet_name=None le ordena a Pandas cargar TODAS las pestañas del archivo.
        return pd.read_excel(FILE_PATH, sheet_name=None)
    return None

# ==========================================
# 1. ENCABEZADO Y TÍTULOS
# ==========================================
# st.title y st.markdown renderizan texto en formato web (HTML/Markdown).
st.title("🔬 CFRTPC Dataset Viewer")
st.markdown("**Continuous Fibre-Reinforced Thermoplastic Composites (CFRTPC)** manufactured by **Fused Deposition Modelling (FDM)**.")
st.markdown("Visualize experimental data and analyze missing 3D printer configurations.")

# Intentamos cargar los datos del Excel.
excel_sheets = load_data()

# Si los datos existen (excel_sheets no es None), procedemos a construir la interfaz.
if excel_sheets:
    # Generamos una sola vez el "Universo Teórico" (las 80 combinaciones ideales) 
    # para usarlo como referencia en todas las pestañas de materiales.
    df_universe = generate_universe()
    
    # Extraemos los nombres de las pestañas del Excel. 
    # Limitamos a las primeras 3 (usualmente Carbono, Vidrio y Kevlar) para mantener el enfoque.
    materials = list(excel_sheets.keys())[:3]
    
    # ==========================================
    # 2. SISTEMA DE NAVEGACIÓN (TABS)
    # ==========================================
    # Aquí creamos los nombres que aparecerán en los botones de navegación superiores.
    tab_titles = []
    for mat in materials:
        mat_lower = mat.lower() # Convertimos a minúsculas para una detección más robusta.
        
        # Lógica de Normalización: Si en el Excel la pestaña se llama "Carbon_Data", 
        # aquí la corregimos al estándar científico "CRTP".
        if 'carb' in mat_lower or 'crtp' in mat_lower: 
            tab_titles.append("CRTP")
        # Corrección de Bug: Validamos cada término por separado para evitar falsos positivos.
        elif 'glass' in mat_lower or 'fgrtp' in mat_lower or 'fg' in mat_lower: 
            tab_titles.append("FGRTP")
        elif 'kev' in mat_lower or 'kvrtp' in mat_lower or 'kv' in mat_lower: 
            tab_titles.append("KvRTP")
        else: 
            tab_titles.append(mat) # Si no coincide, dejamos el nombre original.
            
    # st.tabs crea los contenedores visuales. 'tabs' se convierte en una lista de objetos.
    tabs = st.tabs(tab_titles)
    
    # Configuramos el diseño de las columnas para las tablas que mostraremos más abajo.
    # Por ejemplo, forzamos a que la columna 'Reference' sea pequeña para ahorrar espacio.
    col_cfg = {"Reference": st.column_config.TextColumn("Reference", width="small")}
    
    # ==========================================
    # 3. CICLO DE RENDERIZADO (El Corazón de la App)
    # ==========================================
    # Iteramos a través de cada pestaña. 'i' es el índice (0, 1, 2) y 'material' es el nombre real en el Excel.
    for i, material in enumerate(materials):
        # 'with tabs[i]' le dice a Streamlit: "Todo lo que escriba a continuación mételo SOLO en esta pestaña".
        with tabs[i]:
            # Extraemos la tabla correspondiente a este material y hacemos una copia limpia.
            df_actual = excel_sheets[material].copy()
            # Limpiamos los nombres de las columnas borrando espacios accidentales al inicio o final.
            df_actual.columns = df_actual.columns.str.strip() 
            
            # --- A) VISOR DE DATOS CRUDOS ---
            st.subheader(f"Raw Data: {tab_titles[i]}")
            # Mostramos la tabla tal cual viene del Excel de forma interactiva.
            st.dataframe(df_actual, use_container_width=True, height=300, column_config=col_cfg)
            
            # Agregamos un botón para descargar esta tabla específica en formato CSV.
            st.download_button(
                label=f"📥 Download Full {tab_titles[i]} Dataset (CSV)",
                data=df_actual.to_csv(index=False).encode('utf-8'),
                file_name=f'full_dataset_{material}.csv',
                mime='text/csv',
                key=f'btn_raw_{material}' # Cada botón necesita una llave única para no confundir a Streamlit.
            )
            
            # Un "Expander" para explicar qué significa cada columna del dataset.
            with st.expander("📖 Column Glossary & Abbreviations"):
                st.markdown("""
                **Nomenclature:**
                * **CFRTPC:** Continuous Fibre-Reinforced Thermoplastic Composites.
                * **FDM:** Fused Deposition Modelling.
                * **CRTP:** Carbon fibre reinforced thermoplastic.
                * **FGRTP:** Fibreglass reinforced thermoplastic.
                * **KvRTP:** Kevlar fibre reinforced thermoplastic.
                
                **Variables:**
                * **Reference:** Identifier of the research article/experiment.
                * **Vf:** Fiber-to-Matrix Ratio (0 to 0.80) OR Fiber Volume Fraction.
                * **σ [MPa]:** Ultimate Stress ($\sigma$) in Megapascals. 
                * **E [GPa]:** Elastic Modulus ($E$) in Gigapascals.
                * **Filling (T, H, R, G, S):** Matrix infill pattern: **T**riangular, **H**exagonal, **R**ectangular, **G**yroid, **S**olid.
                * **Fiber Layout (C, I):** Fiber routing strategy: **C**oncentric or **I**sotropic.
                """)
            
            st.markdown("---") # Línea divisoria visual.
            
            # --- B) DETECCIÓN DINÁMICA DE COLUMNAS ---
            # Como los archivos de Excel pueden variar (algunos usan σ y otros Sigma), 
            # usamos lógica de búsqueda para encontrar las columnas correctas sin romper el código.
            col_sigma = next((col for col in df_actual.columns if 'σ' in col), None)
            col_e = next((col for col in df_actual.columns if col.startswith('E') and '*' not in col), None)
            
            # Columnas estandarizadas que DEBEN existir para que el DoE funcione.
            col_vf = 'Vf'
            col_filling = 'Filling (T, H, R, G, S)'
            col_layout = 'Fiber Layout (C, I)'
            
            # Definimos qué información queremos que aparezca al pasar el ratón sobre un punto en las gráficas.
            hover_cols = [c for c in ['Reference', 'Source'] if c in df_actual.columns]
            
            # ==========================================
            # 4. DELEGACIÓN A MÓDULOS ESPECIALIZADOS
            # ==========================================
            # Aquí es donde la modularización brilla. En lugar de escribir 300 líneas aquí, 
            # llamamos a las funciones que definimos en los otros archivos de /src.
            
            # LLAMADA 1: Dibuja los diagramas de dispersión (Scatter Plots) de E vs Vf y σ vs Vf.
            render_scatter_plots(df_actual, col_e, col_sigma, col_vf, col_filling, col_layout, hover_cols)
            
            # LLAMADA 2: Dibuja los Boxplots que muestran el impacto de las variables categóricas.
            render_categorical_impact(df_actual, col_e, col_sigma, hover_cols)
            
            # LLAMADA 3: Ejecuta la lógica matemática para encontrar qué experimentos faltan 
            # comparando tu tabla actual con el Universo Teórico de 5% en 5%.
            render_gap_analysis(df_actual, df_universe, tab_titles[i], material, col_cfg)

else:
    # Mensaje de error amigable por si el usuario olvida poner el archivo Excel en la carpeta data/
    st.error("Please ensure 'dataset.xlsx' is in the 'data/' folder.")