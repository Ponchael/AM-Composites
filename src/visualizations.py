import streamlit as st      # Librería de interfaz: Convierte las instrucciones de Python en una página web visible.
import plotly.express as px # Librería matemática/visual: Crea gráficas interactivas (donde puedes acercar o pasar el ratón).
import pandas as pd         # Librería de datos: Maneja la información en formato de tablas (filas y columnas), casi como un Excel invisible.

# ==========================================
# CONFIGURACIÓN VISUAL GLOBAL PARA PLOTLY
# ==========================================
# Aquí definimos el "tema" o los "colores por defecto" para todas las gráficas del proyecto.
# Hacer esto al principio evita tener que repetir estas instrucciones de diseño en cada gráfica individual.
# Si tu asesor pide que el fondo sea blanco, solo cambias el color aquí y todas las gráficas se actualizan.

GRAFICA_LAYOUT = dict(
    plot_bgcolor='#E5E7EB',       # Color del fondo donde van los puntos (es un código hexadecimal para gris muy clarito).
    paper_bgcolor='rgba(0,0,0,0)',# Color del marco exterior de la gráfica. "rgba(0,0,0,0)" significa 100% transparente.
    margin=dict(l=40, r=40, t=60, b=40) # Tamaño de los márgenes en píxeles: left (izq), right (der), top (arriba), bottom (abajo).
)

EJES_CONFIG = dict(
    showgrid=True, gridwidth=1, gridcolor='#D1D5DB', # Dibuja una cuadrícula gris muy tenue en el fondo para facilitar la lectura.
    showline=True, linewidth=1, linecolor='#9CA3AF', mirror=True, # Dibuja un marco rectangular cerrado alrededor de toda la gráfica.
    zeroline=True, zerolinewidth=2, zerolinecolor='#4B5563' # Dibuja la línea del "0" un poco más gruesa para que destaque.
)

# ==========================================
# FUNCIONES AUXILIARES DE LIMPIEZA DE DATOS
# ==========================================
# En programación, cuando una función empieza con un guion bajo (ej. _clean_numeric),
# le indica a otros programadores: "Esta función es una herramienta interna, no la uses fuera de este archivo".

def _clean_numeric(series):
    """
    Soluciona el problema número uno al importar datos internacionales: el formato de los decimales.
    En países latinos/europeos se usa coma (0,35), pero Python exige un punto (0.35) para hacer matemáticas.
    Esta función toma una columna entera (series) y la repara.
    """
    # Explicación paso a paso de la línea de abajo:
    # 1. .astype(str): Convierte temporalmente toda la columna en texto puro (palabras).
    # 2. .str.replace(',', '.'): Busca cualquier coma y la reemplaza por un punto.
    # 3. .str.strip(): Borra espacios en blanco accidentales que el usuario pudo teclear (ej. " 0.35 " se vuelve "0.35").
    # 4. pd.to_numeric(...): Vuelve a convertir el texto en un número matemático real.
    # 5. errors='coerce': Es una red de seguridad. Si alguien escribió "Hola" en la columna de números, 
    #    en lugar de hacer que el programa colapse y se cierre, simplemente borra esa celda dejándola como "NaN" (Not a Number).
    return pd.to_numeric(series.astype(str).str.replace(',', '.').str.strip(), errors='coerce')

def _standardize_na(val):
    """
    Soluciona el problema de las celdas vacías o mal escritas en columnas de texto (categorías).
    Si alguien dejó la celda en blanco, o escribió "None", "Null", etc., lo unificamos a "NA" (Not Available).
    Así, en la gráfica, todos los experimentos sin datos se agrupan en una sola columna limpia llamada "NA".
    """
    s = str(val).strip().upper() # Convierte el valor a texto, le quita espacios y lo pone en MAYÚSCULAS.
    if s in ['NAN', 'NA', 'NONE', 'NULL', '']: # Si el valor coincide con alguna de estas palabras de error típicas...
        return 'NA' # ...lo reemplazamos obligatoriamente por 'NA'.
    return str(val).strip() # Si todo está bien, simplemente devolvemos el texto limpio.

# ==========================================
# 1. GRÁFICAS DE DISPERSIÓN (SCATTER PLOTS)
# ==========================================
def render_scatter_plots(df_actual, col_e, col_sigma, col_vf, col_filling, col_layout, hover_cols):
    """
    Esta es la función principal que dibuja las gráficas de puntos (Scatter Plots).
    Estas gráficas sirven para ver la correlación entre dos números (Ej: ¿A mayor fibra, mayor resistencia?).
    """
    # st.subheader y st.markdown escriben los títulos y descripciones en la página web.
    st.subheader("📊 Interactive Data Visualization")
    st.markdown("""
        * Points with unknown geometry or fiber are grouped under the 'NA' category.
        * Hover to interact with plots; **double click** on a legend category to set focus.
        """)
    
    # MUY IMPORTANTE: .copy() hace una "fotocopia" de la tabla original.
    # Así podemos limpiar y rayar esta copia sin modificar los datos originales de la memoria.
    df_plot = df_actual.copy()
    
    # 1. Limpiamos la columna de Fracción de Fibra (Vf) usando nuestra función reparadora de comas.
    df_plot['Vf_clean'] = _clean_numeric(df_plot[col_vf])
    
    # 2. Revisamos si la columna de Patrón de Relleno existe en el Excel.
    if col_filling in df_plot.columns:
        # Si existe, aplicamos la función que estandariza los espacios vacíos a "NA".
        df_plot['Filling_clean'] = df_plot[col_filling].apply(_standardize_na)
    else:
        # Si alguien borró la columna en el Excel, rellenamos todo con "NA" para que el programa no colapse.
        df_plot['Filling_clean'] = 'NA'
        
    # Repetimos la misma revisión de seguridad para la columna del Layout (Concéntrico/Isotrópico).
    if col_layout in df_plot.columns:
        df_plot['Layout_clean'] = df_plot[col_layout].apply(_standardize_na)
    else:
        df_plot['Layout_clean'] = 'NA'

    # st.columns(2) es una instrucción de diseño web. Parte la pantalla verticalmente en dos mitades exactas.
    col_plot1, col_plot2 = st.columns(2)
    
    # Creamos diccionarios vacíos (son como cajas u organizadores).
    # Aquí guardaremos el registro de las filas que NO se pudieron graficar por culpa de errores en el Excel.
    reporte_e, reporte_s = {}, {} 

    # --- COLUMNA IZQUIERDA DE LA PÁGINA: MÓDULO ELÁSTICO (E) ---
    with col_plot1: # Todo lo que esté "dentro" de este bloque se dibujará en la mitad izquierda.
        
        # Validamos si tenemos una columna llamada "E [GPa]" en el archivo Excel.
        if col_e and col_e in df_plot.columns:
            
            # Limpiamos los números de E (cambiamos comas por puntos).
            df_plot['E_clean'] = _clean_numeric(df_plot[col_e])
            
            # MÁSCARA BOOLEANA (El Filtro): 
            # Esto funciona exactamente como los filtros de las flechitas en Excel.
            # Evaluamos condición: "La celda de Vf NO está vacía (.notna()) Y la celda de E NO está vacía".
            # Esto nos asegura que solo intentemos graficar experimentos que tengan ambos números completos.
            mask_valid_e = df_plot['Vf_clean'].notna() & df_plot['E_clean'].notna()
            
            # Aplicamos el filtro: Nos quedamos con una tabla que SOLO contiene las filas perfectas.
            df_valid_e = df_plot[mask_valid_e].copy()
            
            # Para fines de transparencia, guardamos las filas que fallaron el filtro en nuestra caja de "eliminados".
            # El símbolo '~' es el inversor matemático. Significa "dame los que NO pasaron la condición".
            reporte_e['eliminados'] = df_plot[~mask_valid_e].copy()
            
            # Guardamos un registro de puntos que SÍ se graficaron, pero que el autor no documentó qué Patrón o Layout usó.
            reporte_e['na_graficados'] = df_valid_e[(df_valid_e['Filling_clean'] == 'NA') | (df_valid_e['Layout_clean'] == 'NA')]
            
            # Si nuestra tabla filtrada NO está vacía (es decir, sí tenemos datos útiles para dibujar)...
            if not df_valid_e.empty:
                
                # px.scatter es la instrucción de Plotly que DIBUJA la gráfica.
                fig_e = px.scatter(
                    df_valid_e,               # 1. Le decimos qué tabla de datos usar.
                    x='Vf_clean',             # 2. Qué columna va en el eje horizontal (X).
                    y='E_clean',              # 3. Qué columna va en el eje vertical (Y).
                    color='Filling_clean',    # 4. El punto cambia de color automáticamente según el patrón (T, H, S).
                    symbol='Layout_clean',    # 5. El punto cambia de forma (círculo, tache, rombo) según el Layout (I, C).
                    hover_data=hover_cols,    # 6. Datos extra (Autor, Referencia) que flotarán al pasar el ratón por encima.
                    title="Elastic Modulus (E)", # 7. El título principal de la gráfica.
                    # 8. Un diccionario para cambiar los nombres técnicos de las columnas por nombres formales y legibles.
                    labels={'Vf_clean': "Fiber Volume Fraction (Vf)", 'E_clean': col_e, 'Filling_clean': "Filling Pattern", 'Layout_clean': "Fiber Layout"}
                )
                
                # update_traces ajusta la estética de los puntitos en la pantalla.
                # size=9 (tamaño ideal), opacity=0.8 (un poco transparentes para ver si hay puntos amontonados),
                # line=dict(width=1) le pone un borde negro de 1 píxel a cada punto para que se distinga.
                fig_e.update_traces(marker=dict(size=9, opacity=0.8, line=dict(width=1, color='DarkSlateGrey')))
                
                # Le inyectamos los estilos de fondo y cuadrícula que definimos al inicio del código.
                fig_e.update_layout(**GRAFICA_LAYOUT)
                fig_e.update_xaxes(**EJES_CONFIG)
                fig_e.update_yaxes(**EJES_CONFIG)
                
                # Finalmente, agarramos la figura creada y le decimos a Streamlit que la imprima en la página web.
                st.plotly_chart(fig_e, use_container_width=True)
            else:
                # Si la tabla filtrada estaba vacía, mostramos este mensaje azul en vez de una gráfica en blanco.
                st.info("No numerical data available for Vf and E.")

    # --- COLUMNA DERECHA DE LA PÁGINA: ESFUERZO MÁXIMO (σ) ---
    with col_plot2: 
        # Este bloque hace EXACTAMENTE la misma matemática y filtrado que la sección anterior,
        # pero enfocado en la columna de Resistencia Mecánica (Sigma) en lugar del Módulo Elástico (E).
        if col_sigma and col_sigma in df_plot.columns:
            df_plot['Sigma_clean'] = _clean_numeric(df_plot[col_sigma])
            
            mask_valid_s = df_plot['Vf_clean'].notna() & df_plot['Sigma_clean'].notna()
            df_valid_s = df_plot[mask_valid_s].copy()
            
            reporte_s['eliminados'] = df_plot[~mask_valid_s].copy()
            reporte_s['na_graficados'] = df_valid_s[(df_valid_s['Filling_clean'] == 'NA') | (df_valid_s['Layout_clean'] == 'NA')]
            
            if not df_valid_s.empty:
                fig_s = px.scatter(
                    df_valid_s, x='Vf_clean', y='Sigma_clean',
                    color='Filling_clean', symbol='Layout_clean',
                    hover_data=hover_cols, title="Ultimate Stress (σ)",
                    labels={'Vf_clean': "Fiber Volume Fraction (Vf)", 'Sigma_clean': col_sigma, 'Filling_clean': "Filling Pattern", 'Layout_clean': "Fiber Layout"}
                )
                fig_s.update_traces(marker=dict(size=9, opacity=0.8, line=dict(width=1, color='DarkSlateGrey')))
                fig_s.update_layout(**GRAFICA_LAYOUT)
                fig_s.update_xaxes(**EJES_CONFIG)
                fig_s.update_yaxes(**EJES_CONFIG)
                st.plotly_chart(fig_s, use_container_width=True)
            else:
                st.info("No numerical data available for Vf and σ.")
                
    # Una vez que ambas gráficas se terminaron de dibujar, llamamos a una función interna
    # que se encargará de mostrarle al usuario el reporte de los errores que encontramos en el proceso.
    _render_chart_audit(reporte_e, reporte_s, col_vf, col_e, col_sigma, col_filling, col_layout)
    st.markdown("---") # Dibuja una línea horizontal separadora en la página.


def _render_chart_audit(reporte_e, reporte_s, col_vf, col_e, col_sigma, col_filling, col_layout):
    """
    Función de Auditoría o "Transparencia".
    Cuando un experimento del Excel no aparece en la gráfica, el usuario (tu asesor) puede pensar que el 
    programa falló. Esta sección despliega una caja justificando y mostrando exactamente por qué 
    algunas filas se ignoraron (ej. el autor nunca anotó cuánto Vf tenía su experimento).
    """
    # st.expander crea una caja con un título que se puede abrir o cerrar haciendo clic.
    # Inicia cerrada (expanded=False) para no abarrotar la pantalla de inicio con puro texto de advertencias.
    with st.expander("📋 Chart Data Audit", expanded=False):
        st.markdown("Identify rows omitted due to missing numerical data or plotted as 'NA'.")
        
        # st.tabs crea sub-pestañitas dentro de la caja para organizar los reportes de E y Sigma.
        tab_aud_e, tab_aud_s = st.tabs(["Audit: Elastic Modulus (E)", "Audit: Ultimate Stress (σ)"])
        
        # Creamos una sub-función pequeñita aquí adentro. 
        # Sirve para no tener que escribir las instrucciones de las tablas de error dos veces repetidas.
        def render_reporte(dic_reporte, col_objetivo_cruda):
            col_elim, col_na = st.columns(2) # Partimos la cajita en izquierda y derecha.
            
            with col_elim: # Lado izquierdo: Mostramos los errores fatales (filas que NO se graficaron).
                # Buscamos nuestra caja de "eliminados". Si no hay nada, devuelve una tabla vacía.
                df_elim = dic_reporte.get('eliminados', pd.DataFrame())
                
                if not df_elim.empty:
                    # st.error imprime una alerta de color rojo.
                    st.error(f"❌ **{len(df_elim)} rows NOT PLOTTED** due to missing numbers in `Vf` or `{col_objetivo_cruda}`.")
                    
                    # Seleccionamos las columnas más importantes para no mostrar toda la tabla gigante del Excel.
                    cols_to_show = [c for c in ['Reference', 'Source', col_vf, col_objetivo_cruda] if c in df_elim.columns]
                    # Imprime la tabla de los acusados.
                    st.dataframe(df_elim[cols_to_show], use_container_width=True)
                else: 
                    # st.success imprime una barra verde de éxito.
                    st.success("✅ No rows were dropped.") 
                    
            with col_na: # Lado derecho: Mostramos las advertencias (filas que SÍ se graficaron pero están incompletas).
                df_na = dic_reporte.get('na_graficados', pd.DataFrame())
                if not df_na.empty:
                    # st.warning imprime una alerta de color amarillo.
                    st.warning(f"⚠️ **{len(df_na)} rows PLOTTED as 'NA'** due to missing Filling or Fiber data.")
                    cols_to_show = [c for c in ['Reference', 'Source', col_vf, col_objetivo_cruda, col_filling, col_layout] if c in df_na.columns]
                    st.dataframe(df_na[cols_to_show], use_container_width=True)
                else: 
                    st.success("✅ All plotted points have complete geometry data.")

        # Inyectamos nuestra sub-función dentro de cada pestañita correspondiente.
        with tab_aud_e: render_reporte(reporte_e, col_e)
        with tab_aud_s: render_reporte(reporte_s, col_sigma)

# ==========================================
# 2. ANÁLISIS DE IMPACTO CATEGÓRICO (BOX PLOTS)
# ==========================================
def render_categorical_impact(df_actual, col_e, col_sigma, hover_cols):
    """
    Dibuja los Boxplots (Diagramas de caja y bigotes) combinados con Strip Plots (puntos horizontales).
    
    A diferencia de las gráficas Scatter (que comparan Número vs Número), esta función compara 
    un Número vs una Palabra/Categoría (Ej: ¿Es más rígido el Patrón Isotrópico o el Concéntrico?).
    El cuadro central del Boxplot agrupa el 50% de los experimentos para que veas dónde está el "promedio real",
    ignorando los extremos raros.
    """
    st.subheader("📈 Categorical Impact Analysis")
    st.markdown("Observe the dispersion of mechanical properties across different printing parameters.")
    
    # Volvemos a hacer nuestra fotocopia de seguridad de los datos.
    df_plot = df_actual.copy()
    
    # 1. BÚSQUEDA DEL ÁNGULO DE LA FIBRA.
    # En muchos artículos (papers), el autor nunca menciona a qué ángulo imprimió.
    # Por eso, usamos "next" con una condición lógica: Busca en el Excel si hay alguna columna 
    # que contenga la palabra "Angle" y "Fiber". Si existe, la guardamos. Si no, devuelve "None" (Nulo).
    col_angle = next((col for col in df_plot.columns if 'Angle' in col and 'Fiber' in col), None)
    if col_angle:
        df_plot['Angle_clean'] = df_plot[col_angle].apply(_standardize_na)
        
    # 2. LIMPIAMOS LOS DATOS NUMÉRICOS (Que irán en el eje Vertical / Y)
    if col_e in df_plot.columns: df_plot['E_clean'] = _clean_numeric(df_plot[col_e])
    if col_sigma in df_plot.columns: df_plot['Sigma_clean'] = _clean_numeric(df_plot[col_sigma])
    
    # 3. LIMPIAMOS LAS CATEGORÍAS (Que irán en el eje Horizontal / X)
    col_filling = 'Filling (T, H, R, G, S)'
    col_layout = 'Fiber Layout (C, I)'
    
    if col_filling in df_plot.columns: df_plot['Filling_clean'] = df_plot[col_filling].apply(_standardize_na)
    if col_layout in df_plot.columns: df_plot['Layout_clean'] = df_plot[col_layout].apply(_standardize_na)
    
    # Creamos sub-pestañas para que el usuario pueda saltar entre ver el efecto del Patrón, Layout o Ángulo 
    # sin que las gráficas se amontonen todas de golpe hacia abajo.
    tab_layout, tab_filling, tab_angle = st.tabs(["By Fiber Layout", "By Filling Pattern", "By Fiber Angle"])
    
    # Creamos una función auxiliar que DIBUJA la pareja de gráficas (E y Sigma).
    # Se hace como función para escribir las instrucciones de diseño una sola vez y reciclarla 3 veces.
    def create_boxplots(x_column, x_label_title):
        c1, c2 = st.columns(2) # Partimos la pantalla
        
        with c1: # Lado Izquierdo: Efecto sobre la Rigidez (E)
            if 'E_clean' in df_plot.columns:
                
                # Filtro: Asegúrate de que el número E exista Y que la categoría que queremos ver (ej. Layout) también exista.
                df_cat_e = df_plot[df_plot['E_clean'].notna() & df_plot[x_column].notna()]
                
                if not df_cat_e.empty:
                    # px.box es la instrucción de Plotly que dibuja la caja estadística.
                    fig_box_e = px.box(
                        df_cat_e,                 # Tabla de datos
                        x=x_column,               # Eje Horizontal (Ej. La columna de "Layout")
                        y='E_clean',              # Eje Vertical (El número de rigidez)
                        color=x_column,           # Cambia el color de la caja según el Layout
                        points="all",             # ¡VITAL! Esta instrucción hace que, además de dibujar la caja matemática,
                                                  # también imprima todos los puntitos reales al lado de ella (Strip Plot).
                                                  # Es el formato estándar y moderno para artículos de investigación.
                        title=f"Elastic Modulus (E) vs {x_label_title}",
                        labels={'E_clean': col_e, x_column: x_label_title},
                        hover_data=hover_cols
                    )
                    
                    # Apagamos el cuadro de "Simbología/Leyenda" (showlegend=False). 
                    # Como el eje X ya dice "Concéntrico" e "Isotrópico", la leyenda lateral era repetitiva
                    # y solo quitaba espacio útil en la pantalla.
                    fig_box_e.update_layout(**GRAFICA_LAYOUT, showlegend=False)
                    fig_box_e.update_xaxes(**EJES_CONFIG)
                    fig_box_e.update_yaxes(**EJES_CONFIG)
                    
                    st.plotly_chart(fig_box_e, use_container_width=True)
                else:
                    st.info(f"No valid data to plot E vs {x_label_title}")
                    
        with c2: # Lado Derecho: Efecto sobre la Resistencia Máxima (Sigma)
            # Exactamente la misma matemática, pero para la columna Sigma.
            if 'Sigma_clean' in df_plot.columns:
                df_cat_s = df_plot[df_plot['Sigma_clean'].notna() & df_plot[x_column].notna()]
                if not df_cat_s.empty:
                    fig_box_s = px.box(
                        df_cat_s, x=x_column, y='Sigma_clean', color=x_column, 
                        points="all", 
                        title=f"Ultimate Stress (σ) vs {x_label_title}",
                        labels={'Sigma_clean': col_sigma, x_column: x_label_title},
                        hover_data=hover_cols
                    )
                    fig_box_s.update_layout(**GRAFICA_LAYOUT, showlegend=False)
                    fig_box_s.update_xaxes(**EJES_CONFIG)
                    fig_box_s.update_yaxes(**EJES_CONFIG)
                    st.plotly_chart(fig_box_s, use_container_width=True)
                else:
                    st.info(f"No valid data to plot σ vs {x_label_title}")

    # Paso final: Usamos la función auxiliar que acabamos de crear y la inyectamos en cada pestaña.
    with tab_layout:
        if 'Layout_clean' in df_plot.columns: 
            create_boxplots('Layout_clean', "Fiber Layout") # Le mandamos la columna Layout
            
    with tab_filling:
        if 'Filling_clean' in df_plot.columns: 
            create_boxplots('Filling_clean', "Filling Pattern") # Le mandamos la columna Patrón
            
    with tab_angle:
        if col_angle and 'Angle_clean' in df_plot.columns: 
            create_boxplots('Angle_clean', "Fiber Angle") # Le mandamos la columna Ángulo
        else: 
            # Si en todo el Excel nunca encontramos la palabra "Angle", mostramos este aviso suave
            # en vez de intentar dibujar una gráfica imposible.
            st.info("No 'Fiber Angle' column detected in the dataset.")
            
    st.markdown("---") # Línea visual que marca el fin de la sección de gráficas.