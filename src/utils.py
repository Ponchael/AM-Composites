import pandas as pd

def generate_universe():
    """
    Genera un "Universo Teórico" de todas las combinaciones posibles de experimentos
    que deberían probarse en el laboratorio. 
    
    Se basa en una métrica de "Razón Fibra-Matriz" (Fiber-to-Matrix ratio), 
    evaluando desde el 0% (pieza de puro plástico sin fibra) hasta el 80%, 
    avanzando en escalones del 5%.
    """
    # Esta lista vacía será el contenedor donde se irá guardando cada experimento generado.
    data = []
    
    # ==========================================
    # 1. DEFINICIÓN DE LÍMITES Y VARIABLES
    # ==========================================
    
    # Rango de la Razón Fibra-Matriz (Vf): Del 0% al 80% en pasos de 5%.
    # La función 'range' en Python funciona así: range(inicio, fin_exclusivo, paso).
    # - Inicia en 0 (Representa el experimento de control: Nylon/Onyx puro, 0% fibra).
    # - Termina en 81 (Se usa 81 porque el límite superior es exclusivo, así nos aseguramos de incluir el 80).
    # - Da saltos de 5 en 5 (0, 5, 10, 15... hasta 80).
    vf_range = range(0, 81, 5) 
    
    # Patrones de relleno de la matriz plástica permitidos por la impresora Markforged:
    # T=Triangular, H=Hexagonal, R=Rectangular, G=Gyroid, S=Solid.
    fillings = ['T', 'H', 'R', 'G', 'S']
    
    # Estrategias de enrutamiento de la fibra continua:
    # I=Isotropic (Capas completas de fibra), C=Concentric (Fibra siguiendo el patrón de los bordes).
    layouts = ['I', 'C']
    
    # ==========================================
    # 2. CREACIÓN DE LAS COMBINACIONES (Ciclos anidados)
    # ==========================================
    
    # Se itera a través de cada patrón de relleno...
    for filling in fillings:
        # Para cada patrón, probamos todos los porcentajes del rango (0, 5, 10...)...
        for vf_int in vf_range:
            
            # Convertimos el número entero (ej. 5) a decimal (0.05) para que coincida con el Excel.
            # Se usa round(..., 2) para evitar errores de precisión de Python con los decimales (ej. 0.150000000001).
            vf_val = round(vf_int / 100.0, 2) 
            
            # Para cada porcentaje y patrón, aplicamos los dos tipos de fibra (Isotrópico y Concéntrico)...
            for layout in layouts:
                # Agregamos esta combinación perfecta a nuestra lista de datos
                data.append([filling, vf_val, layout])
                
    # ==========================================
    # 3. EMPAQUETADO FINAL
    # ==========================================
    # Convertimos nuestra lista de datos en una tabla de Pandas (DataFrame) y nombramos las columnas
    # exactamente igual a como vienen en el archivo 'dataset.xlsx'.
    return pd.DataFrame(data, columns=['Filling (T, H, R, G, S)', 'Vf', 'Fiber Layout (C, I)'])


def find_gaps(df_actual, df_universe):
    """
    Cruza la base de datos de experimentos ya realizados (df_actual) con el
    universo teórico (df_universe) para descubrir qué experimentos faltan por hacer (Gaps).
    """
    
    # Estas son las "Llaves Primarias". Son las 3 variables que definen un experimento único.
    key_columns = ['Filling (T, H, R, G, S)', 'Vf', 'Fiber Layout (C, I)']
    
    # Comprobación de seguridad: Si al Excel le falta alguna de estas columnas clave, 
    # abortamos y devolvemos una tabla vacía para que el programa no colapse.
    if not set(key_columns).issubset(df_actual.columns):
        return pd.DataFrame() 
    
    # ==========================================
    # 1. LIMPIEZA EXTREMA (Anticipando errores humanos)
    # ==========================================
    # Hacemos una copia de las columnas clave del Excel para no alterar los datos originales.
    df_act_clean = df_actual[key_columns].copy()
    
    # --- LIMPIEZA DE NÚMEROS (Vf) ---
    # Convertimos explícitamente la columna 'Vf' a formato numérico (por si alguien escribió un texto por error).
    # 'errors='coerce'' convierte los textos irrecuperables en NaN (vacíos).
    # '.round(2)' fuerza a que todo tenga 2 decimales para que el 0.05 del Excel sea igual al 0.05 del Universo.
    df_act_clean['Vf'] = pd.to_numeric(df_act_clean['Vf'], errors='coerce').round(2)
    df_universe['Vf'] = pd.to_numeric(df_universe['Vf'], errors='coerce').round(2)
    
    # --- LIMPIEZA DE TEXTOS (Patrones y Layouts) ---
    for col in key_columns:
        # .astype(str): Asegura que todo sea leído como texto.
        # .str.strip(): Elimina espacios en blanco invisibles al inicio o final (ej. " C " se vuelve "C").
        # .str.upper(): Convierte todo a mayúsculas (ej. "t" minúscula se vuelve "T").
        # Esto evita que Python crea que "c" minúscula y "C" mayúscula son experimentos distintos.
        df_act_clean[col] = df_act_clean[col].astype(str).str.strip().str.upper()
        df_universe[col] = df_universe[col].astype(str).str.strip().str.upper()
    
    # ==========================================
    # 2. EL CRUCE DE DATOS (Teoría de Conjuntos)
    # ==========================================
    # El truco del Merge: pd.merge con how='left' toma la tabla del Universo Teórico (izquierda) 
    # y busca si en el Excel (derecha) existe una fila con exactamente las mismas llaves (Filling, Vf, Layout).
    #
    # El parámetro indicator=True crea una columna oculta llamada '_merge' que actúa como un semáforo:
    # - Si el experimento está en ambas tablas, dice 'both' (Significa que ya se hizo la probeta).
    # - Si el experimento SOLO está en el universo, dice 'left_only' (Significa que falta hacerla).
    df_gaps = pd.merge(df_universe, df_act_clean, on=key_columns, how='left', indicator=True)
    
    # El Filtro: Nos quedamos únicamente con las filas que dicen 'left_only'. 
    # Es decir, desechamos todo lo que ya se hizo y nos quedamos con el "Gap" real de tareas faltantes.
    # Luego se elimina la columna '_merge' porque ya no nos sirve visualmente.
    df_gaps = df_gaps[df_gaps['_merge'] == 'left_only'].drop(columns=['_merge'])

    # ==========================================
    # 3. FORMATO DE SALIDA (Preparar Plantilla)
    # ==========================================
    # El método 'reindex' toma las columnas que tenía nuestro 'df_gaps' (que son solo 3), 
    # y las expande para que tenga exactamente todas las columnas que tiene el Excel original (Reference, Source, Load, etc.).
    # Como no tenemos datos para esas columnas extras, Pandas las deja en blanco (NaN).
    # Esto se hace para que cuando alguien descargue el CSV desde la página web, 
    # ya tenga el formato perfecto de plantilla listo para anotar nuevos resultados de laboratorio.
    df_gaps_full = df_gaps.reindex(columns=df_actual.columns)
    
    return df_gaps_full