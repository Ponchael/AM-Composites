import pandas as pd

def generate_universe():
    """Generates all theoretical combinations based on specific 3D printer constraints."""
    data = []
    
    # Dictionary mapping the filling pattern to its (min, max) percentage range
    printer_constraints = {
        'T': (25, 55),
        'H': (18, 62),
        'R': (0, 92),
        'G': (28, 52),
        'S': (100, 100)
    }
    
    layouts = ['I', 'C']
    
    for filling, (min_pct, max_pct) in printer_constraints.items():
        for vf_int in range(min_pct, max_pct + 1):
            vf_val = round(vf_int / 100.0, 2)
            for layout in layouts:
                data.append([filling, vf_val, layout])
                
    # Se actualizó el nombre de la columna para incluir G
    return pd.DataFrame(data, columns=['Filling (T, H, R, G, S)', 'Vf', 'Fiber Layout (C, I)'])

def find_gaps(df_actual, df_universe):
    """Cross-references actual data with the universe to find missing experiments."""
    key_columns = ['Filling (T, H, R, G, S)', 'Vf', 'Fiber Layout (C, I)']
    
    if not set(key_columns).issubset(df_actual.columns):
        return pd.DataFrame() 
    
    df_act_clean = df_actual[key_columns].copy()
    df_act_clean['Vf'] = pd.to_numeric(df_act_clean['Vf'], errors='coerce').round(2)
    df_universe['Vf'] = pd.to_numeric(df_universe['Vf'], errors='coerce').round(2)
    
    for col in key_columns:
        df_act_clean[col] = df_act_clean[col].astype(str).str.strip().str.upper()
        df_universe[col] = df_universe[col].astype(str).str.strip().str.upper()
        
    df_gaps = pd.merge(df_universe, df_act_clean, on=key_columns, how='left', indicator=True)
    df_gaps = df_gaps[df_gaps['_merge'] == 'left_only'].drop(columns=['_merge'])
    
    # NUEVA LÓGICA: Reordenar y expandir las columnas para que coincidan con el Excel original.
    # Al hacer esto, automáticamente adquiere el orden exacto de la pestaña actual
    # (ej. pone 'Load', 'Source', etc., dejándolas vacías listas para rellenar).
    df_gaps_full = df_gaps.reindex(columns=df_actual.columns)
    
    return df_gaps_full