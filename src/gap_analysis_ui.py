import streamlit as st      # Librería para inyectar elementos visuales (botones, textos, tablas) en la página web.
import pandas as pd         # Librería para manipulación de datos en formato de tablas (DataFrames).
import os                   # Librería para navegar por los archivos y carpetas del sistema operativo.
from src.utils import find_gaps  # Importamos tu motor lógico que hace la resta matemática de los experimentos.

# ==========================================
# DICCIONARIOS GLOBALES PARA LA INTERFAZ
# ==========================================
# Estos diccionarios actúan como "traductores". En la base de datos es mejor usar iniciales ('T', 'H')
# para ahorrar espacio y evitar errores tipográficos, pero en la interfaz web queremos que el 
# usuario lea la palabra completa y bonita.

PATTERN_NAMES = {
    'T': 'Triangular', 'H': 'Hexagonal', 'R': 'Rectangular',
    'G': 'Gyroid', 'S': 'Solid', 'NA': 'N/A'
}

# Diccionario con los enlaces a imágenes de internet (alojadas en los servidores de Hawk Ridge Systems).
# Sirven para ilustrar gráficamente cómo se ve cada patrón de relleno del plástico.
PATTERN_IMAGE_URLS = {
    'T': 'https://hawkridgesys.com/wp-content/uploads/content/infill-pattern-blog-markforged-2.jpg',
    'H': 'https://hawkridgesys.com/wp-content/uploads/content/infill-pattern-blog-markforged-3.jpg',
    'R': 'https://hawkridgesys.com/wp-content/uploads/content/infill-pattern-blog-markforged-4.jpg',
    'G': 'https://hawkridgesys.com/wp-content/uploads/content/infill-pattern-blog-markforged-5.jpg',
    'S': 'https://hawkridgesys.com/wp-content/uploads/content/infill-pattern-blog-markforged-6.jpg',
    'NA': '' 
}

# Restricciones físicas reales del material (Razón de Fibra-Matriz del 0% al 80%).
# Se usan como el "Policía de los Datos" para auditar que nadie en el Excel haya escrito
# que logró imprimir una probeta con 150% de fibra, lo cual es físicamente imposible.
PRINTER_CONSTRAINTS = {
    'T': (0, 80), 'H': (0, 80), 'R': (0, 80), 'G': (0, 80), 'S': (0, 80) 
}

# ==========================================
# FUNCIÓN PRINCIPAL DE RENDERIZADO
# ==========================================
def render_gap_analysis(df_actual, df_universe, tab_title, material_key, col_cfg):
    """
    Dibuja toda la sección final de la página: El "Gap Analysis" (Análisis de Brechas).
    Esta función toma los datos que YA TIENES (df_actual) y los compara con los que DEBERÍAS TENER (df_universe).
    
    Parámetros:
    - df_actual: Tabla con los experimentos de tu Excel.
    - df_universe: Tabla ideal perfecta generada por utils.py.
    - tab_title: El nombre bonito del material (ej. "CRTP").
    - material_key: El nombre de la pestaña original en Excel (sirve para nombrar los archivos de descarga).
    - col_cfg: Configuración visual de las columnas de Streamlit.
    """
    
    st.subheader(f"🔍 Gap Analysis: Missing Experiments for {tab_title}")

    # ------------------------------------------
    # 1. NOTA METODOLÓGICA (Justificación Científica)
    # ------------------------------------------
    # st.expander crea una caja plegable. Se usa para poner texto denso (como la teoría) 
    # sin quitarle espacio a las tablas y botones importantes.
    with st.expander("📝 Methodological Note: Fiber-to-Matrix Ratio Definition", expanded=False):
        st.markdown("""
        **Updated DoE Strategy:**
        Following the experimental route, the Fiber Volume parameter is defined here as a **Fiber-to-Matrix Ratio** ($V_{fiber} / V_{matrix}$), sampled in **5% increments** from 0% to 80%.
        
        * **Baseline (0%):** Represents the pure unreinforced polymer matrix, serving as the experimental control.
        * **Physical Equivalence:** An 80% ratio corresponds to a total volume fraction ($V_f$) of approximately 44.4%. This aligns with high-performance standards where fiber content is optimized without compromising matrix adhesion.
        * **Gap Analysis Logic:** The "Missing Tasks" now reflect this 5% step (0.00, 0.05, 0.10, etc.). Data is rounded to 2 decimal places to match the theoretical grid.
        """)
    
    # Lista de las 3 variables fundamentales que definen la "identidad" de una probeta.
    columnas_visuales = ['Filling (T, H, R, G, S)', 'Vf', 'Fiber Layout (C, I)']
    
    # MECANISMO DE DEFENSA (Guard Clause):
    # Verificamos si en tu Excel alguien borró o le cambió el nombre a una de esas 3 columnas vitales.
    # Si falta alguna, imprimimos una alerta amarilla (st.warning) y usamos `return` para abortar y salir 
    # de esta función inmediatamente, evitando que toda la aplicación colapse con un error rojo feo.
    if not set(columnas_visuales).issubset(df_actual.columns):
        st.warning(f"Could not perform Gap Analysis. Missing columns: {columnas_visuales}")
        return 
        
    # ------------------------------------------
    # 2. CÁLCULO DE FALTANTES (EL GAP)
    # ------------------------------------------
    # Llamamos a nuestro motor lógico pasándole COPIAS (.copy()) de nuestras tablas.
    # Se usan copias para garantizar que el motor lógico no altere por accidente los datos originales en la memoria.
    df_gaps = find_gaps(df_actual.copy(), df_universe.copy())
    
    # Si la tabla resultante está vacía (.empty), significa que el Gap es cero. ¡Terminaste el semestre!
    if df_gaps.empty:
        st.success("All theoretical configurations have been completed!")
        return # Salimos de la función porque ya no hay tareas pendientes que dibujar.
        
    # ------------------------------------------
    # 3. MÉTRICAS PRINCIPALES (KPIs / Los 3 Números Grandes)
    # ------------------------------------------
    # Dividimos la pantalla en 3 bloques horizontales
    col1, col2, col3 = st.columns(3)
    
    # st.metric dibuja esos números grandes y estilizados estilo tablero de control empresarial.
    # len() cuenta cuántas filas tiene una tabla.
    col1.metric("Theoretical Universe", len(df_universe)) # Total de experimentos posibles (ej. 80)
    col2.metric("Completed (In Universe)", len(df_universe) - len(df_gaps)) # Lo que llevas hecho
    col3.metric("Missing (Total)", len(df_gaps)) # Lo que te falta por hacer (El Gap)
    
    # ------------------------------------------
    # 4. AUDITORÍA FÍSICA (Detección de Outliers)
    # ------------------------------------------
    # Aquí buscamos errores humanos en el registro de datos (ej. un Vf del 90%).
    outliers_mask = [] # Lista vacía que actuará como un colador (Verdadero o Falso).
    
    # .iterrows() permite leer la tabla fila por fila.
    for _, row in df_actual.iterrows():
        fill = row.get('Filling_clean', 'NA')  # Extrae la inicial del patrón (ej. 'S')
        vf = row.get('Vf_clean', pd.NA)        # Extrae el número del Vf (ej. 0.35)
        is_out = False                         # Asumimos que la fila está bien (Falso)
        
        # Si tiene un patrón válido y un número de Vf válido...
        if pd.notna(vf) and fill in PRINTER_CONSTRAINTS:
            min_p, max_p = PRINTER_CONSTRAINTS[fill] # Extraemos los límites de nuestro diccionario (0, 80)
            
            # El Vf está en decimal (0.35), lo multiplicamos por 100 para compararlo como porcentaje (35)
            # Si se sale del rango permitido, cambiamos nuestro veredicto a Verdadero (es un Outlier).
            if (vf * 100) < min_p or (vf * 100) > max_p: 
                is_out = True 
                
        outliers_mask.append(is_out) # Guardamos el veredicto en la lista
    
    # Filtramos la tabla original aplicando la lista de verdaderos y falsos.
    # df_outliers solo contendrá las filas donde 'is_out' fue True.
    df_outliers = df_actual[outliers_mask]
    
    # Si atrapamos algún error, desplegamos la caja de advertencia.
    if not df_outliers.empty:
        with st.expander("⚠️ Configurations Outside Physical Restrictions", expanded=False):
            st.markdown("Logged experiments with a Fiber-to-Matrix Ratio outside realistic limits (0-80%).")
            st.info("**Research Note:** The Eiger software reports a reinforced volume region ($V_r$) that contains a matrix phase, often misreported as $V_f$. This dashboard audits the actual Ratio.")
            
            # Filtramos para no mostrar columnas irrelevantes en la tabla de advertencia.
            col_vf = 'Vf'
            col_filling = 'Filling (T, H, R, G, S)'
            col_layout = 'Fiber Layout (C, I)'
            cols_to_show = [c for c in ['Reference', 'Source', col_filling, col_vf, col_layout] if c in df_outliers.columns]
            
            # Mostramos los infractores
            st.dataframe(df_outliers[cols_to_show].reset_index(drop=True), use_container_width=True, column_config=col_cfg)
    
    # ------------------------------------------
    # 5. DESGLOSE DE TAREAS POR PATRÓN (Templates modulares)
    # ------------------------------------------
    st.markdown("#### 1) Missing Tasks by Filling Pattern")
    
    # .unique() mira la tabla del Universo y nos devuelve una lista de los patrones que existen (T, H, R, G, S).
    unique_fillings = df_universe['Filling (T, H, R, G, S)'].unique()
    
    # st.columns toma el número total de patrones (5) y parte la pantalla verticalmente en 5 columnas iguales.
    cols = st.columns(len(unique_fillings)) 
    
    # Iteramos a través de cada columna visual y de cada patrón al mismo tiempo...
    for idx, fill_type in enumerate(unique_fillings):
        with cols[idx]: # "Enfócate en esta columna específica de la pantalla"
            
            # Traducimos la letra ('T') a la palabra completa ('Triangular')
            full_name = PATTERN_NAMES.get(fill_type, fill_type)
            st.markdown(f"**Pattern: {full_name}**")
            
            # Dibuja la imagen ilustrativa del patrón sacada del servidor web.
            if PATTERN_IMAGE_URLS.get(fill_type): 
                st.image(PATTERN_IMAGE_URLS[fill_type], use_container_width=True)
            
            # Filtramos la tabla gigante de todas las tareas faltantes (df_gaps) para dejar SOLO 
            # las que pertenecen a este patrón específico.
            df_subset = df_gaps[df_gaps['Filling (T, H, R, G, S)'] == fill_type]
            
            if not df_subset.empty:
                # Si hay tareas, mostramos la tabla pequeñita.
                # .rename() cambia el nombre de la columna temporalmente para que se vea más limpio.
                df_to_show = df_subset[columnas_visuales].rename(columns={'Filling (T, H, R, G, S)': 'Filling Type'}).reset_index(drop=True)
                st.dataframe(df_to_show, use_container_width=True, height=250)
                
                # Creamos un botón para descargar SOLO la plantilla de este patrón (muy útil para organizar días de impresión).
                csv_data = df_subset.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label=f"📥 Download {full_name} template", 
                    data=csv_data, 
                    file_name=f'missing_{full_name.lower()}_{material_key}.csv', 
                    key=f'btn_sub_{fill_type}_{material_key}' # Clave única del botón
                )
            else: 
                # Si no hay faltantes en este patrón, imprimimos una caja verde de felicitación.
                st.success(f"All {full_name} done!")
    
    # ------------------------------------------
    # 6. REFERENCIA VISUAL DE FIBRA (Layouts)
    # ------------------------------------------
    st.markdown("") 
    st.markdown("**Fiber Layout Reference:** Visual guide for continuous fiber routing strategies.")
    
    col_h_c, col_h_i = st.columns(2)
    # Streamlit no centra el texto por defecto. 
    # 'unsafe_allow_html=True' es un truco avanzado que nos permite usar código HTML nativo (como <h5>) 
    # y así poder centrar los títulos sobre las imágenes de las fibras.
    col_h_c.markdown("<h5 style='text-align: center;'>Concentric (C)</h5>", unsafe_allow_html=True)
    col_h_i.markdown("<h5 style='text-align: center;'>Isotropic (I)</h5>", unsafe_allow_html=True)
    
    col_img1, col_img2, col_img3, col_img4 = st.columns(4)
    # Insertamos un GIF animado desde internet para el layout Concéntrico
    col_img1.image('https://hawkridgesys.com/wp-content/uploads/content/four-fibers-markforged-blog-2.gif', use_container_width=True)
    
    # Insertamos imágenes fijas. Buscamos primero si existen en la carpeta local 'assets/'.
    if os.path.exists('assets/im_concentric.png'): 
        col_img2.image('assets/im_concentric.png', use_container_width=True)
    if os.path.exists('assets/im_isotropic.png'): 
        col_img3.image('assets/im_isotropic.png', use_container_width=True)
        
    # Insertamos un GIF animado desde internet para el layout Isotrópico
    col_img4.image('https://hawkridgesys.com/wp-content/uploads/content/four-fibers-markforged-blog-3.gif', use_container_width=True)

    st.markdown("---")
    
    # ------------------------------------------
    # 7. DESCARGA DE MASTER TEMPLATE (Todo el Gap)
    # ------------------------------------------
    # Al final, ofrecemos la "Tabla Maestra" con TODAS las probetas faltantes juntas, 
    # independientemente de su patrón o forma.
    st.markdown("#### 2) Complete Missing Tasks")
    df_all_to_show = df_gaps[columnas_visuales].rename(columns={'Filling (T, H, R, G, S)': 'Filling Type'})
    st.dataframe(df_all_to_show, use_container_width=True, height=300)
    
    csv_all_data = df_gaps.to_csv(index=False).encode('utf-8')
    st.download_button(
        label=f"📥 Download ALL Missing Tasks for {tab_title} (Template CSV)", 
        data=csv_all_data, 
        file_name=f'missing_tasks_template_{material_key}.csv', 
        key=f'btn_gaps_all_{material_key}'
    )