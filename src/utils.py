import pandas as pd

def generate_universe():
    """Generates all theoretical combinations based on realistic Vf bounds."""
    data = []
    
    # LÍMITES DE FRACCIÓN VOLUMÉTRICA DE FIBRA (Vf)
    # Rango realista de experimentos basados en Vf (4% a 45%)
    # Esto asume que harás probetas desde 0.04 hasta 0.45 de Vf para todos los patrones
    vf_constraints = {
        'T': (4, 45),
        'H': (4, 45),
        'R': (4, 45),
        'G': (4, 45),
        'S': (4, 45)
    }
    
    layouts = ['I', 'C']
    
    for filling, (min_pct, max_pct) in vf_constraints.items():
        for vf_int in range(min_pct, max_pct + 1):
            vf_val = round(vf_int / 100.0, 2) # Genera valores decimales (ej. 0.04 a 0.45)
            for layout in layouts:
                data.append([filling, vf_val, layout])
                
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
    
    df_gaps_full = df_gaps.reindex(columns=df_actual.columns)
    
    return df_gaps_full