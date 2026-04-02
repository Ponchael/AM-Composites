import streamlit as st
import pandas as pd
import os
import plotly.express as px
from src.utils import generate_universe, find_gaps

st.set_page_config(page_title="DoE - CFRTPC Composites", layout="wide")

FILE_PATH = os.path.join('data', 'dataset.xlsx')

@st.cache_data
def load_data():
    if os.path.exists(FILE_PATH):
        return pd.read_excel(FILE_PATH, sheet_name=None)
    return None

# ==========================================
# MAIN TITLE AND DESCRIPTION
# ==========================================
st.title("🔬 CFRTPC Dataset Viewer")
st.markdown("**Continuous Fibre-Reinforced Thermoplastic Composites (CFRTPC)** manufactured by **Fused Deposition Modelling (FDM)**.")
st.markdown("Visualize experimental data and analyze missing 3D printer configurations.")

excel_sheets = load_data()

if excel_sheets:
    df_universe = generate_universe()
    
    # Extract only the first 3 relevant tabs
    materials = list(excel_sheets.keys())[:3]
    
    # ==========================================
    # TAB NAMES
    # ==========================================
    tab_titles = []
    for mat in materials:
        mat_lower = mat.lower()
        if 'carb' in mat_lower or 'crtp' in mat_lower:
            tab_titles.append("CRTP")
        elif 'glass' in mat_lower or 'fgrtp' in mat_lower or 'fg' in mat_lower:
            tab_titles.append("FGRTP")
        elif 'kev' in mat_lower or 'kvrtp' in mat_lower or 'kv' in mat_lower:
            tab_titles.append("KvRTP")
        else:
            tab_titles.append(mat)
            
    tabs = st.tabs(tab_titles)
    
    pattern_names = {
        'T': 'Triangular', 'H': 'Hexagonal', 'R': 'Rectangular',
        'G': 'Gyroid', 'S': 'Solid', 'NA': 'N/A'
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
    
    # Physical Vf Constraints for the Printer
    printer_constraints = {
        'T': (0, 45), 'H': (0, 45), 'R': (0, 45), 'G': (0, 45), 'S': (0, 45) 
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
            st.subheader(f"Raw Data: {tab_titles[i]}")
            st.dataframe(df_actual, use_container_width=True, height=300, column_config=col_cfg)
            
            csv_raw = df_actual.to_csv(index=False).encode('utf-8')
            st.download_button(
                label=f"📥 Download Full {tab_titles[i]} Dataset (CSV)",
                data=csv_raw,
                file_name=f'full_dataset_{material}.csv',
                mime='text/csv',
                key=f'btn_raw_{material}'
            )
            
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
                * **Load:** Type of mechanical loading applied.
                * **Source:** Author(s) or institution.
                * **Vf:** Fiber Volume Fraction ($V_f$) - ratio of fiber to total composite volume.
                * **σ [MPa]:** Ultimate Stress ($\sigma$) in Megapascals. 
                * **E [GPa]:** Elastic Modulus ($E$) in Gigapascals.
                * **Vf method:** Technique used to measure or calculate the volume fraction.
                * **Standard Test:** International testing standard followed (e.g., ASTM D3039).
                * **E [GPa]\*Vf:** Theoretical $E$ multiplied by $V_f$ (Rule of Mixtures analysis).
                * **Filling (T, H, R, G, S):** Matrix infill pattern: **T**riangular, **H**exagonal, **R**ectangular, **G**yroid, **S**olid.
                * **Fiber Layout (C, I):** Fiber routing strategy: **C**oncentric or **I**sotropic.
                """)
            
            st.markdown("---")
            
            # ==========================================
            # 1.5 INTERACTIVE DATA VISUALIZATION
            # ==========================================
            st.subheader(f"📊 Interactive Data Visualization")
            st.markdown("""
                * Points with unknown geometry or fiber are grouped under the 'NA' category.
                * Hover to interact with plots; **double click** on a category to set focus.
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
                    plot_bgcolor='#E5E7EB', paper_bgcolor='rgba(0,0,0,0)', 
                    margin=dict(l=40, r=40, t=60, b=40)
                )
                ejes_config = dict(
                    showgrid=True, gridwidth=1, gridcolor='#D1D5DB', 
                    showline=True, linewidth=1, linecolor='#9CA3AF', mirror=True,
                    zeroline=True, zerolinewidth=2, zerolinecolor='#4B5563' 
                )
                
                col_plot1, col_plot2 = st.columns(2)
                reporte_e, reporte_s = {}, {}
                
                with col_plot1:
                    if col_e and col_e in df_actual.columns:
                        df_actual['E_clean'] = clean_numeric(df_actual[col_e])
                        mask_valid_e = df_actual['Vf_clean'].notna() & df_actual['E_clean'].notna()
                        df_plot_e = df_actual[mask_valid_e].copy()
                        reporte_e['eliminados'] = df_actual[~mask_valid_e].copy()
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

                with col_plot2:
                    if col_sigma and col_sigma in df_actual.columns:
                        df_actual['Sigma_clean'] = clean_numeric(df_actual[col_sigma])
                        mask_valid_s = df_actual['Vf_clean'].notna() & df_actual['Sigma_clean'].notna()
                        df_plot_s = df_actual[mask_valid_s].copy()
                        reporte_s['eliminados'] = df_actual[~mask_valid_s].copy()
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
                
                with st.expander("📋 Chart Data Audit", expanded=False):
                    st.markdown("Identify rows omitted due to missing numerical data or plotted as 'NA'.")
                    tab_aud_e, tab_aud_s = st.tabs(["Audit: Elastic Modulus (E)", "Audit: Ultimate Stress (σ)"])
                    
                    def render_reporte(dic_reporte, col_objetivo_cruda):
                        col_elim, col_na = st.columns(2)
                        with col_elim:
                            df_elim = dic_reporte.get('eliminados', pd.DataFrame())
                            if not df_elim.empty:
                                st.error(f"❌ **{len(df_elim)} rows NOT PLOTTED** due to missing numbers in `Vf` or `{col_objetivo_cruda}`.")
                                st.dataframe(df_elim[[c for c in ['Reference', 'Source', col_vf, col_objetivo_cruda] if c in df_elim.columns]], use_container_width=True, column_config=col_cfg)
                            else: st.success("✅ No rows were dropped.")
                        with col_na:
                            df_na = dic_reporte.get('na_graficados', pd.DataFrame())
                            if not df_na.empty:
                                st.warning(f"⚠️ **{len(df_na)} rows PLOTTED as 'NA'** due to missing Filling or Fiber data.")
                                st.dataframe(df_na[[c for c in ['Reference', 'Source', col_vf, col_objetivo_cruda, col_filling, col_layout] if c in df_na.columns]], use_container_width=True, column_config=col_cfg)
                            else: st.success("✅ All plotted points have complete geometry data.")

                    with tab_aud_e: render_reporte(reporte_e, col_e)
                    with tab_aud_s: render_reporte(reporte_s, col_sigma)

            st.markdown("---")
            
            # ==========================================
            # 2. GAP ANALYSIS 
            # ==========================================
            st.subheader(f"🔍 Gap Analysis: Missing Experiments for {tab_titles[i]}")
            
            with st.expander("📝 Methodological Note: Matrix Density vs. Fiber Volume Fraction ($V_f$)", expanded=False):
                st.markdown("""
                To correctly interpret missing experiments in this **Design of Experiments (DoE)**, distinguish between configurable printer parameters and physical resulting properties:
                
                * **Matrix Infill Density:** Controls the plastic amount (Nylon/Onyx) in areas without fiber. Software limits vary by geometry: **Triangular** (25-55%), **Hexagonal** (18-62%), **Rectangular** (0-92%), **Gyroid** (28-52%), and **Solid** (100%).
                * **Reinforced Volume Region ($V_r$):** The volume reported by Eiger, including fiber and the matrix flowing through it. $V_r$ is frequently misreported as $V_f$ in literature.
                * **Fiber Volume Fraction ($V_f$):** The actual volume occupied strictly by the structural fiber. For accurate analysis, $V_f = 0.4 \\times V_r$ for Carbon and $V_f = 0.5 \\times V_r$ for Glass.
                
                **Audit Criterion:** Physically, the maximum printable $V_f$ limit is around **40-45%**, even for Solid (100% matrix) parts. This panel evaluates missing experiments based on the realistic physical range of $V_f$ (4% to 45%) to set the stage for future data collection.
                """)
            
            columnas_visuales = ['Filling (T, H, R, G, S)', 'Vf', 'Fiber Layout (C, I)']
            
            if set(columnas_visuales).issubset(df_actual.columns):
                df_gaps = find_gaps(df_actual.copy(), df_universe.copy())
                
                if not df_gaps.empty:
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Theoretical Universe", len(df_universe))
                    col2.metric("Completed (In Universe)", len(df_universe) - len(df_gaps))
                    col3.metric("Missing (Total)", len(df_gaps))
                    
                    # OUTLIERS
                    outliers_mask = []
                    for _, row in df_actual.iterrows():
                        fill, vf = row.get('Filling_clean', 'NA'), row.get('Vf_clean', pd.NA)
                        is_out = False
                        if pd.notna(vf) and fill in printer_constraints:
                            min_p, max_p = printer_constraints[fill]
                            if (vf * 100) < min_p or (vf * 100) > max_p: is_out = True
                        outliers_mask.append(is_out)
                    
                    df_outliers = df_actual[outliers_mask]
                    if not df_outliers.empty:
                        with st.expander("⚠️ Configurations Outside Physical Restrictions", expanded=False):
                            st.markdown("Logged experiments with a Fiber Volume Fraction ($V_f$) outside realistic limits (0-45%).")
                            st.info("**Research Note:** The Eiger software reports a reinforced volume region ($V_r$) that contains a matrix phase, often misreported as $V_f$. This dashboard audits actual $V_f$ (physical limit ~40-45%).")
                            st.dataframe(df_outliers[[c for c in ['Reference', 'Source', col_filling, col_vf, col_layout] if c in df_outliers.columns]].reset_index(drop=True), use_container_width=True, column_config=col_cfg)
                    
                    st.markdown("#### 1) Missing Tasks by Filling Pattern")
                    unique_fillings = df_universe['Filling (T, H, R, G, S)'].unique()
                    cols = st.columns(len(unique_fillings))
                    
                    for idx, fill_type in enumerate(unique_fillings):
                        with cols[idx]:
                            full_name = pattern_names.get(fill_type, fill_type)
                            st.markdown(f"**Pattern: {full_name}**")
                            if pattern_image_urls.get(fill_type): st.image(pattern_image_urls[fill_type], use_container_width=True)
                            
                            df_subset = df_gaps[df_gaps['Filling (T, H, R, G, S)'] == fill_type]
                            if not df_subset.empty:
                                st.dataframe(df_subset[columnas_visuales].rename(columns={'Filling (T, H, R, G, S)': 'Filling Type'}).reset_index(drop=True), use_container_width=True, height=250)
                                st.download_button(label=f"📥 Download {full_name} template", data=df_subset.to_csv(index=False).encode('utf-8'), file_name=f'missing_{full_name.lower()}_{material}.csv', key=f'btn_sub_{fill_type}_{material}')
                            else: st.success(f"All {full_name} done!")
                    
                    st.markdown("") 
                    st.markdown("**Fiber Layout Reference:** Visual guide for continuous fiber routing strategies.")
                    col_h_c, col_h_i = st.columns(2)
                    col_h_c.markdown("<h5 style='text-align: center;'>Concentric (C)</h5>", unsafe_allow_html=True)
                    col_h_i.markdown("<h5 style='text-align: center;'>Isotropic (I)</h5>", unsafe_allow_html=True)
                    
                    col_img1, col_img2, col_img3, col_img4 = st.columns(4)
                    col_img1.image('https://hawkridgesys.com/wp-content/uploads/content/four-fibers-markforged-blog-2.gif', use_container_width=True)
                    if os.path.exists('assets/im_concentric.png'): col_img2.image('assets/im_concentric.png', use_container_width=True)
                    if os.path.exists('assets/im_isotropic.png'): col_img3.image('assets/im_isotropic.png', use_container_width=True)
                    col_img4.image('https://hawkridgesys.com/wp-content/uploads/content/four-fibers-markforged-blog-3.gif', use_container_width=True)

                    st.markdown("---")
                    st.markdown("#### 2) Complete Missing Tasks")
                    st.dataframe(df_gaps[columnas_visuales].rename(columns={'Filling (T, H, R, G, S)': 'Filling Type'}), use_container_width=True, height=300)
                    st.download_button(label=f"📥 Download ALL Missing Tasks for {tab_titles[i]} (Template CSV)", data=df_gaps.to_csv(index=False).encode('utf-8'), file_name=f'missing_tasks_template_{material}.csv', key=f'btn_gaps_all_{material}')
                else: st.success("All theoretical configurations have been completed!")
            else: st.warning(f"Could not perform Gap Analysis. Missing columns: {columnas_visuales}")
else: st.error("Please ensure 'dataset.xlsx' is in the 'data/' folder.")