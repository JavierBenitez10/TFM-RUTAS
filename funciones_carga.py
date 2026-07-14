import oracledb
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text


def cargar_datos_distancias():
    conn_str = os.getenv("ORACLE_CONNECTION")
    engine = create_engine(conn_str)


    query = """
        SELECT
            ORIGEN,
            ORIGEN_X_Y,
            DESTINO,
            DESTINO_X_Y,
            DISTANCIA,
            TIEMPO_MIN
        FROM TFM_MATRIZ
    """

    df = pd.read_sql(query, engine)

    df.columns = [c.strip().upper() for c in df.columns]

    matriz_datos = {
        (row['ORIGEN'], row['DESTINO']): {
            'tiempo': row['TIEMPO_MIN'],
            'distancia': row['DISTANCIA'],
            'origen_coords': row['ORIGEN_X_Y'],
            'destino_coords': row['DESTINO_X_Y']
        }
        for _, row in df.iterrows()
    }

    print(f"✅ Matriz cargada: {len(matriz_datos)} registros")

    return matriz_datos

def cargar_alumnos():    
    conn_str = os.getenv("ORACLE_CONNECTION")
    engine = create_engine(conn_str)     
    # Aquí es donde cambia: una parada puede aparecer varias veces con destinos distintos
    df_alumnos = pd.read_sql("SELECT ORIGEN, CENTRO, ALUMNOS FROM TFM_ALUMNOS_V where nvl(alumnos,0) > 0 order by origen", engine)
    df_alumnos.columns = [c.strip().upper() for c in df_alumnos.columns]
    
    # Creamos una lista de "Tareas de Recogida"
    # Cada elemento es: {'id_parada': X, 'centro': Y, 'alumnos': Z}
    tareas_recogida = []
    for _, row in df_alumnos.iterrows():
        tareas_recogida.append({
            'PARADA': row['ORIGEN'],
            'CENTRO': row['CENTRO'],
            'ALUMNOS': row['ALUMNOS']
        })
    
    print(f" Cargadas {len(tareas_recogida)} tareas de recogida independientes.")    
    return tareas_recogida


def visualizar_diccionario_generico(dato, n=5):
    """
    Muestra las primeras n líneas de cualquier estructura (dict o list).
    Gestiona automáticamente claves, tuplas y valores anidados.
    """
    if not dato:
        print(" El objeto está vacío.")
        return

    lista_para_df = []

    # 1. Caso: Es un DICCIONARIO (como matriz_tiempos)
    if isinstance(dato, dict):
        muestreo_items = list(dato.items())[:n]
        for clave, valor in muestreo_items:
            fila = {}
            # Procesar la Clave (Tupla o Simple)
            if isinstance(clave, tuple):
                for i, parte in enumerate(clave):
                    fila[f'Clave_{i+1}'] = parte
            else:
                fila['ID_Clave'] = clave
            
            # Procesar el Valor
            if isinstance(valor, dict):
                fila.update(valor)
            else:
                fila['Valor_Dato'] = valor
            lista_para_df.append(fila)

    # 2. Caso: Es una LISTA (como matriz_tareas)
    elif isinstance(dato, list):
        muestreo_items = dato[:n]
        for elemento in muestreo_items:
            if isinstance(elemento, dict):
                lista_para_df.append(elemento)
            else:
                lista_para_df.append({'Valor': elemento})

    # 3. Crear DataFrame y aplicar formato
    df_visual = pd.DataFrame(lista_para_df)
    
    print(f" Muestreo de {len(lista_para_df)} registros (Total: {len(dato)})")
    
    estilo = df_visual.style.set_properties(**{
        'text-align': 'center',
        'border': '1px solid #ddd',
        'padding': '6px'
    }).set_table_styles([{
        'selector': 'th',
        'props': [
            ('background-color', '#1a5276'), 
            ('color', 'white'), 
            ('font-weight', 'bold'),
            ('text-transform', 'uppercase')
        ]
    }])
    
    display(estilo)