import streamlit as st
import pandas as pd
import os
import plotly.express as px
from src.utils import generate_universe, find_gaps

st.set_page_config(page_title="DoE - Composite Materials", layout="wide")

FILE_PATH = os.path.join('data', 'dataset.xlsx')

@st.cache_data
def load_data():
    if os.path.exists(FILE_PATH):
        return pd.read_excel(FILE_PATH, sheet_name=None)
    return None

st.title("🔬 Composite Materials Dataset Viewer")
st.markdown("Visualize the experimental data and analyze missing 3D printer configurations.")

excel_sheets = load_data()

if excel_sheets:
    df_universe = generate_universe()
    
    # Extract ONLY the first 3 tabs
    materials = list(excel_sheets.keys())[:3]
    tabs = st.tabs(materials)
    
    pattern_names = {
        'T': 'Triangular', 'H': 'Hexagonal', 'R': 'Rectangular',
        'G': 'Gyroid', 'S': 'Solid', 'NA': 'N/A'
    }
    
    # ==========================================
    # PRINTER CONSTRAINTS (Min, Max) %
    # ==========================================


    # FIBER VOLUME FRACTION (Vf) CONSTRAINTS (%)
    # Límite físico de la fibra, NO del relleno de plástico.
    # Dado que en Markforged, es físicamente casi imposible superar el 40-45% de Vf
    printer_constraints = {
        'T': (0, 45),
        'H': (0, 45),
        'R': (0, 45),
        'G': (0, 45),
        'S': (0, 45) # Incluso en matriz sólida, la fibra no pasa del 45%
    }

    ## UNUSED
    fill_density = {
        'T': (25, 55),
        'H': (18, 62),
        'R': (0, 92),
        'G': (28, 52),
        'S': (100, 100)
    }
    
    # ==========================================
    # IMAGE DICTIONARY (Filling Patterns)
    # ==========================================
    pattern_image_urls = {
        'T': 'https://hawkridgesys.com/wp-content/uploads/content/infill-pattern-blog-markforged-2.jpg',
        'H': 'https://hawkridgesys.com/wp-content/uploads/content/infill-pattern-blog-markforged-3.jpg',
        'R': 'https://hawkridgesys.com/wp-content/uploads/content/infill-pattern-blog-markforged-4.jpg',
        'G': 'https://hawkridgesys.com/wp-content/uploads/content/infill-pattern-blog-markforged-5.jpg',
        'S': 'https://hawkridgesys.com/wp-content/uploads/content/infill-pattern-blog-markforged-6.jpg',
        'NA': '' 
    }
    
    col_cfg = {
        "Reference": st.column_config.TextColumn("Reference", width="small")
    }
    
    for i, material in enumerate(materials):
        with tabs[i]:
            df_actual = excel_sheets[material].copy()
            df_actual.columns = df_actual.columns.str.strip() 
            
            # ==========================================
            # 1. FULL DATASET VIEWER
            # ==========================================
            st.subheader(f"Raw Data: {material}")
            st.dataframe(df_actual, use_container_width=True, height=300, column_config=col_cfg)
            
            csv_raw = df_actual.to_csv(index=False).encode('utf-8')
            st.download_button(
                label=f"📥 Download Full {material} Dataset (CSV)",
                data=csv_raw,
                file_name=f'full_dataset_{material}.csv',
                mime='text/csv',
                key=f'btn_raw_{material}'
            )
            
            with st.expander("📖 Column Glossary & Abbreviations"):
                st.markdown("""
                * **Reference:** Citation number or identifier of the research article/experiment.
                * **Load:** Type of mechanical loading applied (e.g., Tensile, Flexural, Compressive).
                * **Source:** Author(s) or institution that published the data.
                * **$V_f$:** Fiber Volume Fraction (ratio of fiber volume to total composite volume).
                * **σ [MPa]:** Ultimate Stress in Megapascals. Depending on the material tab, it refers to Carbon (C), Fiberglass (FG), or Kevlar (Kv).
                * **E [GPa]:** Elastic Modulus (stiffness) in Gigapascals.
                * **$V_f$ method:** Technique used to measure or calculate the volume fraction (e.g., Analytical, Burn-off, Micro-CT).
                * **Standard Test:** International testing standard followed (e.g., ASTM D3039).
                * **E [GPa]\*$V_f$:** Theoretical Elastic Modulus multiplied by Volume Fraction (useful for Rule of Mixtures analysis).
                * **# layers:** Total number of printed layers in the test specimen.
                * **Filling (T, H, R, G, S):** 3D printing matrix infill pattern: **T**riangular, **H**exagonal, **R**ectangular, **G**yroid, **S**olid.
                * **Fiber Layout (C, I):** Continuous fiber routing strategy: **C**oncentric or **I**sotropic.
                * **Fiber Angle:** Orientation angle of the continuous reinforcing fibers.
                * **Matrix Angle:** Raster orientation angle of the thermoplastic matrix.
                """)
            
            st.markdown("---")
            
            # ==========================================
            # 1.5 INTERACTIVE DATA VISUALIZATION
            # ==========================================
            st.subheader(f"📊 Interactive Data Visualization")
            st.markdown("""
                * Points with unknown geometry or fiber are grouped under the 'NA' category.
                * Hover your mouse to interact with the plots; **double click** on a category to set focus on it.
                """)
            
            col_sigma = next((col for col in df_actual.columns if 'σ' in col), None)
            col_e = next((col for col in df_actual.columns if col.startswith('E') and '*' not in col), None)
            col_vf = 'Vf'
            col_filling = 'Filling (T, H, R, G, S)'
            col_layout = 'Fiber Layout (C, I)'
            
            def clean_numeric(series):
                return pd.to_numeric(series.astype(str).str.replace(',', '.').str.strip(), errors='coerce')
            
            def standardize_na(val):
                s = str(val).strip().upper()
                if s in ['NAN', 'NA', 'NONE', 'NULL', '']: return 'NA'
                return str(val).strip()

            if col_vf in df_actual.columns:
                df_actual['Vf_clean'] = clean_numeric(df_actual[col_vf])
                
                if col_filling in df_actual.columns:
                    df_actual['Filling_clean'] = df_actual[col_filling].apply(standardize_na)
                if col_layout in df_actual.columns:
                    df_actual['Layout_clean'] = df_actual[col_layout].apply(standardize_na)
                
                hover_cols = []
                if 'Reference' in df_actual.columns: hover_cols.append('Reference')
                if 'Source' in df_actual.columns: hover_cols.append('Source')
                
                grafica_layout = dict(
                    plot_bgcolor='#E5E7EB', 
                    paper_bgcolor='rgba(0,0,0,0)', 
                    margin=dict(l=40, r=40, t=60, b=40)
                )
                ejes_config = dict(
                    showgrid=True, gridwidth=1, gridcolor='#D1D5DB', 
                    showline=True, linewidth=1, linecolor='#9CA3AF', mirror=True,
                    zeroline=True, zerolinewidth=2, zerolinecolor='#4B5563' 
                )
                
                col_plot1, col_plot2 = st.columns(2)
                
                reporte_e = {}
                reporte_s = {}
                
                with col_plot1:
                    if col_e and col_e in df_actual.columns:
                        df_actual['E_clean'] = clean_numeric(df_actual[col_e])
                        mask_valid_e = df_actual['Vf_clean'].notna() & df_actual['E_clean'].notna()
                        df_plot_e = df_actual[mask_valid_e].copy()
                        df_dropped_e = df_actual[~mask_valid_e].copy()
                        
                        reporte_e['eliminados'] = df_dropped_e
                        reporte_e['na_graficados'] = df_plot_e[(df_plot_e['Filling_clean'] == 'NA') | (df_plot_e['Layout_clean'] == 'NA')]
                        
                        if not df_plot_e.empty:
                            fig_e = px.scatter(
                                df_plot_e, x='Vf_clean', y='E_clean',
                                color='Filling_clean' if 'Filling_clean' in df_plot_e.columns else None,
                                symbol='Layout_clean' if 'Layout_clean' in df_plot_e.columns else None,
                                hover_data=hover_cols, title=f"Elastic Modulus (E)",
                                labels={'Vf_clean': "Fiber Volume Fraction (Vf)", 'E_clean': col_e, 'Filling_clean': "Filling Pattern", 'Layout_clean': "Fiber Layout"}
                            )
                            fig_e.update_traces(marker=dict(size=9, opacity=0.8, line=dict(width=1, color='DarkSlateGrey')))
                            fig_e.update_layout(**grafica_layout)
                            fig_e.update_xaxes(**ejes_config)
                            fig_e.update_yaxes(**ejes_config)
                            st.plotly_chart(fig_e, use_container_width=True)
                        else:
                            st.info("No numerical data available for Vf and E.")
                    else:
                        st.warning("Could not find Elastic Modulus (E) column.")
                        
                with col_plot2:
                    if col_sigma and col_sigma in df_actual.columns:
                        df_actual['Sigma_clean'] = clean_numeric(df_actual[col_sigma])
                        mask_valid_s = df_actual['Vf_clean'].notna() & df_actual['Sigma_clean'].notna()
                        df_plot_s = df_actual[mask_valid_s].copy()
                        df_dropped_s = df_actual[~mask_valid_s].copy()
                        
                        reporte_s['eliminados'] = df_dropped_s
                        reporte_s['na_graficados'] = df_plot_s[(df_plot_s['Filling_clean'] == 'NA') | (df_plot_s['Layout_clean'] == 'NA')]
                        
                        if not df_plot_s.empty:
                            fig_s = px.scatter(
                                df_plot_s, x='Vf_clean', y='Sigma_clean',
                                color='Filling_clean' if 'Filling_clean' in df_plot_s.columns else None,
                                symbol='Layout_clean' if 'Layout_clean' in df_plot_s.columns else None,
                                hover_data=hover_cols, title=f"Ultimate Stress (σ)",
                                labels={'Vf_clean': "Fiber Volume Fraction (Vf)", 'Sigma_clean': col_sigma, 'Filling_clean': "Filling Pattern", 'Layout_clean': "Fiber Layout"}
                            )
                            fig_s.update_traces(marker=dict(size=9, opacity=0.8, line=dict(width=1, color='DarkSlateGrey')))
                            fig_s.update_layout(**grafica_layout)
                            fig_s.update_xaxes(**ejes_config)
                            fig_s.update_yaxes(**ejes_config)
                            st.plotly_chart(fig_s, use_container_width=True)
                        else:
                            st.info("No numerical data available for Vf and σ.")
                    else:
                        st.warning("Could not find Ultimate Stress (σ) column.")
                
                with st.expander("📋 Chart Data Audit", expanded=False):
                    st.markdown("This section shows exactly which rows from the Excel were **omitted** due to missing numerical data, and which were plotted under the **'NA' category**.")
                    tab_aud_e, tab_aud_s = st.tabs(["Audit: Elastic Modulus (E)", "Audit: Ultimate Stress (σ)"])
                    
                    def render_reporte(dic_reporte, col_objetivo_cruda):
                        col_elim, col_na = st.columns(2)
                        with col_elim:
                            df_elim = dic_reporte.get('eliminados', pd.DataFrame())
                            if not df_elim.empty:
                                st.error(f"❌ **{len(df_elim)} rows NOT PLOTTED** due to missing numbers in `Vf` or `{col_objetivo_cruda}`.")
                                cols_mostrar = [c for c in ['Reference', 'Source', col_vf, col_objetivo_cruda] if c in df_elim.columns]
                                st.dataframe(df_elim[cols_mostrar], use_container_width=True, column_config=col_cfg)
                            else:
                                st.success("✅ No rows were dropped due to missing numbers.")
                                
                        with col_na:
                            df_na = dic_reporte.get('na_graficados', pd.DataFrame())
                            if not df_na.empty:
                                st.warning(f"⚠️ **{len(df_na)} rows PLOTTED as 'NA'** due to missing Filling or Fiber data.")
                                cols_mostrar_na = [c for c in ['Reference', 'Source', col_vf, col_objetivo_cruda, col_filling, col_layout] if c in df_na.columns]
                                st.dataframe(df_na[cols_mostrar_na], use_container_width=True, column_config=col_cfg)
                            else:
                                st.success("✅ All plotted points have complete geometry and fiber data.")

                    with tab_aud_e:
                        render_reporte(reporte_e, col_e)
                    with tab_aud_s:
                        render_reporte(reporte_s, col_sigma)

            st.markdown("---")
            
            # ==========================================
            # 2. GAP ANALYSIS 
            # ==========================================
            st.subheader(f"🔍 Gap Analysis: Missing Experiments for {material}")
            
            # --- NUEVA SECCIÓN DE EXPLICACIÓN METODOLÓGICA ---
            with st.expander("📝 Nota Metodológica: Densidad de Matriz vs. Fracción Volumétrica ($V_f$)", expanded=False):
                st.markdown("""
                Para la correcta interpretación de los experimentos faltantes en este **Diseño de Experimentos (DoE)**, se debe distinguir entre los parámetros configurables en el software de la impresora (Eiger) y las propiedades físicas resultantes en la probeta:
                
                * **Densidad de Relleno de la Matriz (Matrix Infill):** Controla exclusivamente la cantidad de plástico (Nylon/Onyx) en las zonas sin fibra. Los límites permitidos por el software varían según la geometría: **Triangular** (25-55%), **Hexagonal** (18-62%), **Rectangular** (0-92%), **Gyroid** (28-52%) y **Sólido** (100%).
                * **Región Volumétrica Reforzada ($V_r$):** Es el volumen reportado por el software Eiger, el cual incluye tanto la fibra continua como la matriz plástica que fluye entre ella. Debido a esto, el $V_r$ es frecuentemente confundido y reportado de manera errónea en la literatura como si fuera la fracción de fibra real.
                * **Fracción Volumétrica de Fibra ($V_f$):** Es el volumen real ocupado estrictamente por la fibra estructural. Para obtener el $V_f$ correcto, el $V_r$ debe multiplicarse por la fracción de fibra de fábrica del carrete (ej. $V_f = 0.4 \\times V_r$ para el carbono y $V_f = 0.5 \\times V_r$ para el vidrio).
                
                **Criterio de Auditoría:** Físicamente, el límite máximo imprimible de $V_f$ ronda entre el **40% y 45%**, incluso si la matriz plástica se imprime al 100% de densidad (Sólido). Por lo tanto, el universo teórico de este panel evalúa los experimentos faltantes basándose en el rango físico realista del $V_f$ (4% a 45%) registrado en la base de datos, preparando el terreno para la futura recolección de las densidades de matriz.
                """)
            # -------------------------------------------------
            columnas_visuales = ['Filling (T, H, R, G, S)', 'Vf', 'Fiber Layout (C, I)']
            
            if set(columnas_visuales).issubset(df_actual.columns):
                df_gaps = find_gaps(df_actual.copy(), df_universe.copy())
                
                if not df_gaps.empty:
                    total_universe = len(df_universe)
                    total_missing = len(df_gaps)
                    completed_in_universe = total_universe - total_missing
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Theoretical Universe", total_universe)
                    col2.metric("Completed (In Universe)", completed_in_universe)
                    col3.metric("Missing (Total)", total_missing)
                    

                    # ==========================================
                    # OUTLIERS IDENTIFICATION (Strictly Vf Bounds)
                    # ==========================================
                    outliers_mask = []
                    for _, row in df_actual.iterrows():
                        fill = row.get('Filling_clean', 'NA')
                        vf = row.get('Vf_clean', pd.NA)
                        is_out = False
                        
                        if pd.notna(vf) and fill in printer_constraints:
                            min_pct, max_pct = printer_constraints[fill]
                            vf_pct = round(vf * 100, 2) # Convierte tu decimal (0.35) a porcentaje (35.0)
                            
                            # Compara el % de fibra real contra el límite realista (0-45%)
                            if vf_pct < min_pct or vf_pct > max_pct:
                                is_out = True
                                
                        outliers_mask.append(is_out)
                        
                    df_outliers = df_actual[outliers_mask]
                    
                    if not df_outliers.empty:
                        with st.expander("⚠️ Configurations Outside Physical Restrictions", expanded=False):
                            st.markdown("The following logged experiments have a Fiber Volume Fraction ($V_f$) that falls outside the realistic printable limits (0-45%).")
                            
                            st.info("**Research Note:** The Eiger software reports a reinforced volume region ($V_r$) that contains a matrix phase, which is frequently misreported as the actual fiber volume fraction ($V_f$). This dashboard audits the actual $V_f$, which physically maxes out around 40-45%, rather than the matrix infill density.")
                            
                            cols_outliers = [c for c in ['Reference', 'Source', col_filling, col_vf, col_layout] if c in df_outliers.columns]
                            st.dataframe(df_outliers[cols_outliers].reset_index(drop=True), use_container_width=True, column_config=col_cfg)

                    
                    st.markdown("#### 1) Missing Tasks by Filling Pattern")
                    unique_fillings = df_universe['Filling (T, H, R, G, S)'].unique()
                    cols = st.columns(len(unique_fillings))
                    
                    for idx, fill_type in enumerate(unique_fillings):
                        with cols[idx]:
                            full_name = pattern_names.get(fill_type, fill_type)
                            st.markdown(f"**Pattern: {full_name}**")
                            
                            img_url = pattern_image_urls.get(fill_type, "")
                            if img_url:
                                st.image(img_url, use_container_width=True)
                            
                            df_subset = df_gaps[df_gaps['Filling (T, H, R, G, S)'] == fill_type]
                            
                            if not df_subset.empty:
                                df_visual = df_subset[columnas_visuales].reset_index(drop=True)
                                df_visual = df_visual.rename(columns={'Filling (T, H, R, G, S)': 'Filling Type'})
                                st.dataframe(df_visual, use_container_width=True, height=250)
                                
                                csv_subset = df_subset.to_csv(index=False).encode('utf-8')
                                st.download_button(
                                    label=f"📥 Download {full_name} template",
                                    data=csv_subset,
                                    file_name=f'missing_{full_name.lower()}_template_{material}.csv',
                                    mime='text/csv',
                                    key=f'btn_sub_{fill_type}_{material}'
                                )
                            else:
                                st.success(f"All {full_name} done!")
                    
                    # ==========================================
                    # FIBER LAYOUT VISUAL REFERENCE (Integrado en sección 1)
                    # ==========================================
                    st.markdown("") 
                    st.markdown("**Fiber Layout Reference:** Visual guide for the continuous fiber routing strategies.")
                    
                    col_h_c, col_h_i = st.columns(2)
                    with col_h_c:
                        st.markdown("<h5 style='text-align: center;'>Concentric (C)</h5>", unsafe_allow_html=True)
                    with col_h_i:
                        st.markdown("<h5 style='text-align: center;'>Isotropic (I)</h5>", unsafe_allow_html=True)
                    
                    col_img1, col_img2, col_img3, col_img4 = st.columns(4)
                    
                    with col_img1:
                        st.image('https://hawkridgesys.com/wp-content/uploads/content/four-fibers-markforged-blog-2.gif', use_container_width=True)
                        
                    with col_img2:
                        if os.path.exists('assets/im_concentric.png'):
                            st.image('assets/im_concentric.png', use_container_width=True)
                        else:
                            st.info("Missing: assets/im_concentric.png")
                            
                    with col_img3:
                        if os.path.exists('assets/im_isotropic.png'):
                            st.image('assets/im_isotropic.png', use_container_width=True)
                        else:
                            st.info("Missing: assets/im_isotropic.png")
                            
                    with col_img4:
                        st.image('https://hawkridgesys.com/wp-content/uploads/content/four-fibers-markforged-blog-3.gif', use_container_width=True)

                    st.markdown("---")
                    st.markdown("#### 2) Complete Missing Tasks")
                    
                    df_visual_all = df_gaps[columnas_visuales].rename(columns={'Filling (T, H, R, G, S)': 'Filling Type'})
                    st.dataframe(df_visual_all, use_container_width=True, height=300)
                    
                    csv_gaps_all = df_gaps.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label=f"📥 Download ALL Missing Tasks for {material} (Template CSV)",
                        data=csv_gaps_all,
                        file_name=f'missing_tasks_template_{material}.csv',
                        mime='text/csv',
                        key=f'btn_gaps_all_{material}'
                    )
                else:
                    st.success("All theoretical configurations have been completed for this material!")
            else:
                st.warning(f"Could not perform Gap Analysis. Ensure columns '{columnas_visuales}' exist exactly as written in your Excel file.")
else:
    st.error("Please make sure your 'dataset.xlsx' file is placed inside the 'data/' folder.")