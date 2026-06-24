import time
import math
import random
from copy import deepcopy
from collections import defaultdict
import pandas as pd

# ============================================================
# RESTRICCIONES DEL PROBLEMA
# ============================================================

RESTRICCIONES = {

    # --------------------------------------------------------
    # TIEMPO MÁXIMO PERMITIDO POR RUTA (En Minutos)
    # --------------------------------------------------------
    "TIEMPO_MAXIMO_RUTA": 90, 

    # --------------------------------------------------------
    # CAPACIDADES VÁLIDAS DE AUTOBUSES
    # --------------------------------------------------------
    "CAPACIDADES_AUTOBUS": [38, 55],

    # --------------------------------------------------------
    # OCUPACIÓN MÍNIMA DESEABLE (restricción blanda)
    # --------------------------------------------------------
    "OCUPACION_MINIMA_DESEABLE": 8,

    # --------------------------------------------------------
    # CENTRO ÚNICO POR RUTA (restricción dura)
    # --------------------------------------------------------
    "CENTRO_UNICO_POR_RUTA": False,

    # --------------------------------------------------------
    # CONSERVACIÓN DE ALUMNOS (restricción dura)
    # --------------------------------------------------------
    "CONSERVAR_TOTAL_ALUMNOS": True,

    # --------------------------------------------------------
    # NO DUPLICAR (PARADA, CENTRO) (restricción dura)
    # --------------------------------------------------------
    "NO_DUPLICAR_PARADA_CENTRO": True,

    # --------------------------------------------------------
    # RUTAS VACÍAS NO PERMITIDAS
    # --------------------------------------------------------
    "PERMITIR_RUTAS_VACIAS": False,

    # --------------------------------------------------------
    # LÍMITE DE PARADAS
    # --------------------------------------------------------
    "LIMITE_PARADAS": None,

    # --------------------------------------------------------
    # DEFINICIÓN DE TRAMOS TEMPORALES (En Minutos)
    # --------------------------------------------------------
    "TRAMOS_TIEMPO": {
        "TRAMO_1": {"MIN": 0, "MAX": 60},
        "TRAMO_2": {"MIN": 60, "MAX": 90},
        "TRAMO_3": {"MIN": 90, "MAX": float("inf")}
    },

    # --------------------------------------------------------
    # RESTRICCIONES BLANDAS / OBJETIVOS
    # --------------------------------------------------------
    "OPTIMIZACION": {
        "MINIMIZAR_COSTE": True,
        "MINIMIZAR_TIEMPO_TOTAL": True,
        "MINIMIZAR_DISTANCIA_TOTAL": True,
        "MINIMIZAR_NUMERO_RUTAS": True,
        "EQUILIBRAR_OCUPACION": True
    }
}

# ============================================================
# TARIFAS DE AUTOBUSES
# ============================================================

TARIFAS_AUTOBUS = [
    {
        "TIPO": "BUS_38",
        "CAPACIDAD": 38,
        "ALUMNOS_DESDE": 1,
        "ALUMNOS_HASTA": 38,
        "COSTES": {
            "TRAMO_1": 96.14,
            "TRAMO_2": 124.98,
            "TRAMO_3": 153.82
        }
    },
    {
        "TIPO": "BUS_55",
        "CAPACIDAD": 55,
        "ALUMNOS_DESDE": 39,
        "ALUMNOS_HASTA": 55,
        "COSTES": {
            "TRAMO_1": 119.86,
            "TRAMO_2": 155.82,
            "TRAMO_3": 191.78
        }
    }
]


def obtener_capacidad_bus(total_alumnos):
    if total_alumnos <= 38:
        return 38
    return 55


def obtener_tramo_tiempo(tiempo_total):
    for tramo, valores in RESTRICCIONES["TRAMOS_TIEMPO"].items():
        if tiempo_total >= valores["MIN"] and tiempo_total <= valores["MAX"]:
            return tramo
    return "TRAMO_3"


def calcular_coste_bus(total_alumnos, tiempo_total):
    tramo = obtener_tramo_tiempo(tiempo_total)
    for tarifa in TARIFAS_AUTOBUS:
        if total_alumnos >= tarifa["ALUMNOS_DESDE"] and total_alumnos <= tarifa["ALUMNOS_HASTA"]:
            return tarifa["COSTES"][tramo]
    return float("inf")


def calcular_total_alumnos(ruta):
    return sum(parada["alumnos"] for parada in ruta["paradas"])


def calcular_ocupacion(total_alumnos, capacidad_bus):
    if capacidad_bus == 0:
        return float("inf")
    return round((total_alumnos / capacidad_bus) * 100, 2)


def obtener_metricas_nodos(origen, destino, matriz_distancias):
    clave = (origen, destino)
    if clave in matriz_distancias:
        return {
            "tiempo": matriz_distancias[clave]["tiempo"],
            "distancia": matriz_distancias[clave]["distancia"]
        }

    clave_inversa = (destino, origen)
    if clave_inversa in matriz_distancias:
        return {
            "tiempo": matriz_distancias[clave_inversa]["tiempo"],
            "distancia": matriz_distancias[clave_inversa]["distancia"]
        }

    return {"tiempo": 0, "distancia": 0}


# ============================================================
# OPTIMIZAR ORDEN PARADAS (Algoritmo Greedy / Nearest Neighbor)
# ============================================================

def optimizar_orden_paradas(ruta, matriz_distancias):
    paradas = ruta["paradas"]
    if len(paradas) <= 2:
        return ruta

    restantes = paradas.copy()
    ordenadas = []
    actual = restantes.pop(0)
    ordenadas.append(actual)

    while len(restantes) > 0:
        parada_actual = actual["parada"]
        mejor = None
        mejor_distancia = float("inf")

        for candidata in restantes:
            parada_candidata = candidata["parada"]
            clave = (parada_actual, parada_candidata)

            if clave not in matriz_distancias:
                continue

            distancia = matriz_distancias[clave]["distancia"]
            if distancia < mejor_distancia:
                mejor_distancia = distancia
                mejor = candidata

        if mejor is None:
            mejor = restantes[0]

        ordenadas.append(mejor)
        restantes.remove(mejor)
        actual = mejor

    ruta["paradas"] = ordenadas
    return ruta


# ============================================================
# CALCULAR MÉTRICAS DE UNA RUTA
# ============================================================

def calcular_metricas_ruta(ruta, matriz_distancias):
    """
    Recalcula completamente todas las métricas de una ruta de forma directa.
    Nota: Se ha removido la ejecución de optimizar_orden_paradas desde este punto
    para resolver el cuello de botella crítico durante la evaluación del vecindario.
    """
    paradas = ruta["paradas"]
    centro = ruta["centro"]

    if len(paradas) == 0:
        return {
            "alumnos": 0,
            "bus": 38,
            "ocupacion": 0,
            "num_paradas": 0,
            "tiempo": 0,
            "distancia": 0,
            "coste": 0
        }

    total_alumnos = calcular_total_alumnos(ruta)
    capacidad_bus = obtener_capacidad_bus(total_alumnos)
    ocupacion = calcular_ocupacion(total_alumnos, capacidad_bus)

    tiempo_total = 0
    distancia_total = 0

    # Entre paradas consecutivas
    for i in range(len(paradas) - 1):
        origen = paradas[i]["parada"]
        destino = paradas[i + 1]["parada"]
        metricas = obtener_metricas_nodos(origen, destino, matriz_distancias)
        tiempo_total += metricas["tiempo"]
        distancia_total += metricas["distancia"]

    # Última parada hacia el centro escolar
    ultima_parada = paradas[-1]["parada"]
    metricas_centro = obtener_metricas_nodos(ultima_parada, centro, matriz_distancias)
    tiempo_total += metricas_centro["tiempo"]
    distancia_total += metricas_centro["distancia"]

    coste = calcular_coste_bus(total_alumnos, tiempo_total)

    return {
        "alumnos": total_alumnos,
        "bus": capacidad_bus,
        "ocupacion": ocupacion,
        "num_paradas": len(paradas),
        "tiempo": round(tiempo_total, 2),
        "distancia": round(distancia_total, 2),
        "coste": round(coste, 2)
    }


# ============================================================
# RECALCULAR SOLUCIÓN COMPLETA
# ============================================================

def recalcular_solucion(solucion, matriz_distancias):
    for ruta in solucion:
        metricas = calcular_metricas_ruta(ruta, matriz_distancias)
        ruta["alumnos"] = metricas["alumnos"]
        ruta["bus"] = metricas["bus"]
        ruta["ocupacion"] = metricas["ocupacion"]
        ruta["num_paradas"] = metricas["num_paradas"]
        ruta["tiempo"] = metricas["tiempo"]
        ruta["distancia"] = metricas["distancia"]
        ruta["coste"] = metricas["coste"]
    return solucion


# ============================================================
# VALIDACIONES DE RESTRICCIONES
# ============================================================

def validar_solucion(solucion, tareas_recogida):
    errores = []
    for ruta in solucion:
        errores_ruta = validar_ruta(ruta)
        errores.extend(errores_ruta)

    errores_demanda = validar_demanda_global(solucion, tareas_recogida)
    errores.extend(errores_demanda)

    if len(errores) == 0:
        return True, []
    return False, errores


def validar_ruta(ruta):
    errores = []
    if len(ruta["paradas"]) == 0:
        errores.append(f'Ruta {ruta["id"]}: vacía')
        return errores

    if ruta["alumnos"] > ruta["bus"]:
        errores.append(f'Ruta {ruta["id"]}: capacidad excedida ({ruta["alumnos"]} > {ruta["bus"]})')

    if ruta["tiempo"] > RESTRICCIONES["TIEMPO_MAXIMO_RUTA"]:
        errores.append(f'Ruta {ruta["id"]}: tiempo excedido ({ruta["tiempo"]})')

    centros = set(parada["centro"] for parada in ruta["paradas"])
    if len(centros) > 1:
        errores.append(f'Ruta {ruta["id"]}: múltiples centros')

    vistos = set()
    for parada in ruta["paradas"]:
        clave = (parada["parada"], parada["centro"])
        if clave in vistos:
            errores.append(f'Ruta {ruta["id"]}: duplicado {clave}')
        vistos.add(clave)
    
    return errores


def validar_demanda_global(solucion, tareas_recogida):
    errores = []
    demanda_original = defaultdict(int)
    for _, row in tareas_recogida.iterrows():
        clave = (row["PARADA"], row["CENTRO"])
        demanda_original[clave] += row["ALUMNOS"]

    demanda_solucion = defaultdict(int)
    for ruta in solucion:
        for parada in ruta["paradas"]:
            clave = (parada["parada"], parada["centro"])
            demanda_solucion[clave] += parada["alumnos"]

    claves_original = set(demanda_original.keys())
    claves_solucion = set(demanda_solucion.keys())

    faltantes = claves_original - claves_solucion
    for clave in faltantes:
        errores.append(f'Falta demanda {clave}')

    sobrantes = claves_solucion - claves_original
    for clave in sobrantes:
        errores.append(f'Demanda extra {clave}')

    claves_comunes = claves_original.intersection(claves_solucion)
    for clave in claves_comunes:
        original = demanda_original[clave]
        solucion_valor = demanda_solucion[clave]
        if original != solucion_valor:
            errores.append(f'Demanda inconsistente {clave}: original={original}, solucion={solucion_valor}')

    return errores


# ============================================================
# CONSTRUIR SOLUCIÓN INICIAL
# ============================================================

def construir_solucion_inicial(tareas_recogida, matriz_distancias):
    solucion = []
    id_ruta = 1

    for centro, df_centro in tareas_recogida.groupby("CENTRO"):
        df_centro = df_centro.sort_values(by="ALUMNOS", ascending=False)
        ruta_actual = {"id": id_ruta, "centro": centro, "paradas": []}

        for _, row in df_centro.iterrows():
            nueva_parada = {
                "parada": row["PARADA"],
                "centro": row["CENTRO"],
                "alumnos": row["ALUMNOS"]
            }

            ruta_test = deepcopy(ruta_actual)
            ruta_test["paradas"].append(nueva_parada)
            
            # Se optimiza la secuencia de paradas greedy antes de verificar factibilidad en solución inicial
            ruta_test = optimizar_orden_paradas(ruta_test, matriz_distancias)
            metricas = calcular_metricas_ruta(ruta_test, matriz_distancias)

            capacidad_ok = (metricas["alumnos"] <= 55)
            tiempo_ok = (metricas["tiempo"] <= RESTRICCIONES["TIEMPO_MAXIMO_RUTA"])

            if capacidad_ok and tiempo_ok:
                ruta_actual["paradas"].append(nueva_parada)
                ruta_actual = optimizar_orden_paradas(ruta_actual, matriz_distancias)
            else:
                if len(ruta_actual["paradas"]) > 0:
                    solucion.append(deepcopy(ruta_actual))

                id_ruta += 1
                ruta_actual = {
                    "id": id_ruta,
                    "centro": centro,
                    "paradas": [nueva_parada]
                }

        if len(ruta_actual["paradas"]) > 0:
            solucion.append(deepcopy(ruta_actual))
            id_ruta += 1

    solucion = recalcular_solucion(solucion, matriz_distancias)
    return solucion


# ============================================================
# REPORTES Y MÉTRICAS GLOBALES
# ============================================================

def generar_resumen_rutas(solucion):
    resumen = []
    for ruta in solucion:
        resumen.append({
            "RUTA": ruta["id"],
            "CENTRO": ruta["centro"],
            "NUM_PARADAS": ruta["num_paradas"],
            "ALUMNOS": ruta["alumnos"],
            "BUS": ruta["bus"],
            "OCUPACION_%": ruta["ocupacion"],
            "TIEMPO_MIN": ruta["tiempo"],
            "DISTANCIA_KM": ruta["distancia"],
            "COSTE_€": ruta["coste"]
        })
    return pd.DataFrame(resumen)


def calcular_metricas_globales(solucion):
    total_rutas = len(solucion)
    total_alumnos = sum(ruta["alumnos"] for ruta in solucion)
    total_paradas = sum(ruta["num_paradas"] for ruta in solucion)
    tiempo_total = sum(ruta["tiempo"] for ruta in solucion)
    distancia_total = sum(ruta["distancia"] for ruta in solucion)
    coste_total = sum(ruta["coste"] for ruta in solucion)

    ocupacion_media = round(sum(ruta["ocupacion"] for ruta in solucion) / total_rutas, 2) if total_rutas > 0 else 0
    rutas_bus_38 = sum(1 for ruta in solucion if ruta["bus"] == 38)
    rutas_bus_55 = sum(1 for ruta in solucion if ruta["bus"] == 55)

    return {
        "TOTAL_RUTAS": total_rutas,
        "TOTAL_ALUMNOS": total_alumnos,
        "TOTAL_PARADAS": total_paradas,
        "TIEMPO_TOTAL_MIN": round(tiempo_total, 2),
        "TIEMPO_MEDIO_RUTA": round(tiempo_total / total_rutas, 2) if total_rutas > 0 else 0,
        "DISTANCIA_TOTAL_KM": round(distancia_total, 2),
        "DISTANCIA_MEDIA_RUTA": round(distancia_total / total_rutas, 2) if total_rutas > 0 else 0,
        "COSTE_TOTAL_€": round(coste_total, 2),
        "COSTE_MEDIO_RUTA": round(coste_total / total_rutas, 2) if total_rutas > 0 else 0,
        "OCUPACION_MEDIA_%": ocupacion_media,
        "RUTAS_BUS_38": rutas_bus_38,
        "RUTAS_BUS_55": rutas_bus_55
    }


def mostrar_solucion_inicial(solucion, tareas_recogida, matriz_distancias):
    solucion = recalcular_solucion(solucion, matriz_distancias)
    valida, errores = validar_solucion(solucion, tareas_recogida)

    print("\n" + "=" * 90 + "\nRESUMEN SOLUCIÓN INICIAL\n" + "=" * 90)
    df_resumen = generar_resumen_rutas(solucion)
    print(df_resumen)

    print("\n" + "=" * 90 + "\nMÉTRICAS GLOBALES\n" + "=" * 90)
    metricas = calcular_metricas_globales(solucion)
    for k, v in metricas.items():
        print(f"{k:<30}: {v}")

    print("\n" + "=" * 90 + "\nVALIDACIÓN\n" + "=" * 90)
    if valida:
        print("✅ SOLUCIÓN VÁLIDA")
    else:
        print("❌ SOLUCIÓN INVÁLIDA")
        for e in errores:
            print(f" - {e}")

    return df_resumen


def dividir_tareas_exceso_capacidad(tareas_recogida):
    nuevas_tareas = []
    for _, row in tareas_recogida.iterrows():
        alumnos = row["ALUMNOS"]
        while alumnos > 55:
            nueva = row.copy()
            nueva["ALUMNOS"] = 55
            nuevas_tareas.append(nueva)
            alumnos -= 55
        nueva = row.copy()
        nueva["ALUMNOS"] = alumnos
        nuevas_tareas.append(nueva)
    return pd.DataFrame(nuevas_tareas)


def convertir_matriz_a_diccionario(matriz_distancias_df):
    matriz = {}
    for _, row in matriz_distancias_df.iterrows():
        clave = (row["CLAVE_1"], row["CLAVE_2"])
        matriz[clave] = {
            "tiempo": row["tiempo"],
            "distancia": row["distancia"]
        }
    return matriz


# ============================================================
# FUNCIÓN DE COSTE GLOBAL (Función Objetivo del SA)
# ============================================================

def funcion_coste(
    solucion,
    tareas_recogida,
    matriz_distancias,
    peso_coste=1.0,
    peso_rutas=100.0,
    peso_ocupacion=10.0,
    peso_distancia=1.0
):
    solucion = recalcular_solucion(solucion, matriz_distancias)
    valida, _ = validar_solucion(solucion, tareas_recogida)

    if not valida:
        return float("inf")

    total_coste = sum(ruta["coste"] for ruta in solucion)
    total_rutas = len(solucion)
    total_distancia = sum(ruta["distancia"] for ruta in solucion)

    penalizacion_ocupacion = 0
    for ruta in solucion:
        ocupacion = ruta["ocupacion"]
        if ocupacion < 50:
            penalizacion_ocupacion += (50 - ocupacion) * 100

    coste_total = (
        peso_coste * total_coste
        + peso_rutas * total_rutas
        + peso_ocupacion * penalizacion_ocupacion
        + peso_distancia * total_distancia
    )

    return round(coste_total, 2)


# ============================================================
# GENERAR VECINO
# ============================================================

def generar_vecino_mal(solucion_actual, tareas_recogida, matriz_distancias, max_intentos=100):
    """
    Genera una solución vecina válida aplicando movimientos estructurales
    o refinamiento local mediante 2-Opt de forma segura.
    """
    intentos = 0
    while intentos < max_intentos:
        solucion_propuesta = deepcopy(solucion_actual)
        
        # Evaluamos si aplicar 2-Opt o movimiento tradicional
        if random.random() < 0.5 and len(solucion_propuesta) > 0:
            idx_ruta = random.randint(0, len(solucion_propuesta) - 1)
            
            # Extraemos la ruta original
            ruta_seleccionada = solucion_propuesta[idx_ruta]
            
            # Aplicamos la inversión de tramos si tiene paradas suficientes
            if len(ruta_seleccionada["paradas"]) >= 4:
                paradas = ruta_seleccionada["paradas"]
                i, j = sorted(random.sample(range(len(paradas)), 2))
                
                # Modificación in-place segura
                solucion_propuesta[idx_ruta]["paradas"] = paradas[:i] + paradas[i:j+1][::-1] + paradas[j+1:]
        else:
            # Lógica tradicional de tu script original: mover parada de ruta
            ruta_origen = random.choice(solucion_propuesta)
            if len(ruta_origen["paradas"]) > 1:
                parada_cambio = random.choice(ruta_origen["paradas"])
                
                # Buscamos otra ruta destino al azar para transferir la parada
                rutas_destino = [r for r in solucion_propuesta if r["id"] != ruta_origen["id"]]
                if rutas_destino:
                    ruta_destino = random.choice(rutas_destino)
                    
                    # Mover el elemento físicamente
                    ruta_origen["paradas"].remove(parada_cambio)
                    ruta_destino["paradas"].append(parada_cambio)
        
        # CRÍTICO: Eliminar rutas vacías si las hubiera antes de recalcular
        solucion_propuesta = [r for r in solucion_propuesta if len(r["paradas"]) > 0]
        
        # RECALCULO INTEGRAL: Forzamos la actualización de distancias, tiempos y cargas
        solucion_propuesta = recalcular_solucion(solucion_propuesta, matriz_distancias)
        
        # VALIDACIÓN: Ahora los datos están limpios y la comprobación será fiable
        valida, _ = validar_solucion(solucion_propuesta, tareas_recogida)
        if valida:
            return solucion_propuesta
            
        intentos += 1
        
    return deepcopy(solucion_actual)

def generar_vecino(solucion, tareas_recogida, matriz_distancias, max_intentos=100):
    vecino = deepcopy(solucion)

    for _ in range(max_intentos):
        tipo_movimiento = random.choice(["mover", "swap", "merge"])
        rutas_validas = [ruta for ruta in vecino if len(ruta["paradas"]) > 0]

        if len(rutas_validas) < 2:
            return deepcopy(solucion)

        # OPERADOR MOVER
        if tipo_movimiento == "mover":
            ruta_origen = random.choice(rutas_validas)
            parada = random.choice(ruta_origen["paradas"])
            centro = parada["centro"]

            rutas_destino = [
                ruta for ruta in rutas_validas
                if (ruta["id"] != ruta_origen["id"] and ruta["centro"] == centro)
            ]

            if len(rutas_destino) == 0:
                continue

            ruta_destino = random.choice(rutas_destino)
            ruta_origen["paradas"].remove(parada)
            ruta_destino["paradas"].append(parada)

        # OPERADOR MERGE (Corregido con filtro previo de capacidad)
        elif tipo_movimiento == "merge":
            ruta_a, ruta_b = random.sample(rutas_validas, 2)
            if ruta_a["centro"] != ruta_b["centro"]:
                continue
            
            if (ruta_a["alumnos"] + ruta_b["alumnos"]) > 55:
                continue
        
            nueva_ruta = deepcopy(ruta_a)
            nuevo_id = max(r["id"] for r in vecino) + 1
            nueva_ruta["id"] = nuevo_id
            nueva_ruta["paradas"].extend(deepcopy(ruta_b["paradas"]))
        
            vecino = [ruta for ruta in vecino if ruta["id"] not in [ruta_a["id"], ruta_b["id"]]]
            vecino.append(nueva_ruta)

        # OPERADOR SWAP
        else:
            ruta_a, ruta_b = random.sample(rutas_validas, 2)
            if ruta_a["centro"] != ruta_b["centro"]:
                continue

            parada_a = random.choice(ruta_a["paradas"])
            parada_b = random.choice(ruta_b["paradas"])

            idx_a = ruta_a["paradas"].index(parada_a)
            idx_b = ruta_b["paradas"].index(parada_b)

            ruta_a["paradas"][idx_a] = parada_b
            ruta_b["paradas"][idx_b] = parada_a

        # Post-procesamiento del vecino propuesto
        vecino = [ruta for ruta in vecino if len(ruta["paradas"]) > 0]
        vecino = recalcular_solucion(vecino, matriz_distancias)
        valido, _ = validar_solucion(vecino, tareas_recogida)

        if valido:
            return vecino

        vecino = deepcopy(solucion)

    return deepcopy(solucion)


# ============================================================
# ALGORITMO DE RECOCIDO SIMULADO
# ============================================================

def recocido_simulado(
    solucion_inicial,
    tareas_recogida,
    matriz_distancias,
    temperatura_inicial=100,
    temperatura_minima=1,
    factor_enfriamiento=0.95,
    iteraciones_por_temperatura=20,
    peso_coste=1.0,
    peso_rutas=20.0,
    peso_ocupacion=5.0,
    peso_distancia=2.0,
    mostrar_logs=True
):
    tiempo_inicio = time.time()
    solucion_actual = deepcopy(solucion_inicial)
    coste_actual = funcion_coste(
        solucion_actual, tareas_recogida, matriz_distancias,
        peso_coste, peso_rutas, peso_ocupacion, peso_distancia
    )

    mejor_solucion = deepcopy(solucion_actual)
    mejor_coste = coste_actual
    temperatura = temperatura_inicial
    historial = []
    iteracion_global = 0

    while temperatura > temperatura_minima:
        for _ in range(iteraciones_por_temperatura):
            iteracion_global += 1
            vecino = generar_vecino(solucion_actual, tareas_recogida, matriz_distancias)
            coste_vecino = funcion_coste(
                vecino, tareas_recogida, matriz_distancias,
                peso_coste, peso_rutas, peso_ocupacion, peso_distancia
            )

            delta = coste_vecino - coste_actual
            aceptar = False

            if delta < 0:
                aceptar = True
            else:
                probabilidad = math.exp(-delta / temperatura)
                if random.random() < probabilidad:
                    aceptar = True

            if aceptar:
                solucion_actual = deepcopy(vecino)
                coste_actual = coste_vecino

            if coste_actual < mejor_coste:
                mejor_solucion = deepcopy(solucion_actual)
                mejor_coste = coste_actual

            historial.append({
                "ITERACION": iteracion_global,
                "TEMPERATURA": round(temperatura, 4),
                "COSTE_ACTUAL": round(coste_actual, 2),
                "MEJOR_COSTE": round(mejor_coste, 2)
            })

        temperatura *= factor_enfriamiento
        if mostrar_logs:
            print(f'T={temperatura:.2f} | Mejor coste={mejor_coste:.2f}')

    tiempo_total = round(time.time() - tiempo_inicio, 2)
    df_historial = pd.DataFrame(historial)
    
    # Reordenar de forma definitiva la secuencia de paradas de la mejor solución antes de entregar el resultado
    for r in mejor_solucion:
        r = optimizar_orden_paradas(r, matriz_distancias)
    mejor_solucion = recalcular_solucion(mejor_solucion, matriz_distancias)
    
    metricas = calcular_metricas_globales(mejor_solucion)

    df_resultado = pd.DataFrame({
        "Metrica": [
            "Temperatura inicial", "Temperatura minima", "Factor enfriamiento",
            "Iteraciones temperatura", "Peso coste", "Peso rutas",
            "Peso ocupacion", "Peso distancia", "Mejor coste",
            "Tiempo ejecucion (s)", "Numero rutas", "Total alumnos",
            "Ocupacion media", "Distancia total", "Coste total"
        ],
        "Valor": [
            temperatura_inicial, temperatura_minima, factor_enfriamiento,
            iteraciones_por_temperatura, peso_coste, peso_rutas,
            peso_ocupacion, peso_distancia, round(mejor_coste, 2),
            tiempo_total, metricas["TOTAL_RUTAS"], metricas["TOTAL_ALUMNOS"],
            metricas["OCUPACION_MEDIA_%"], metricas["DISTANCIA_TOTAL_KM"], metricas["COSTE_TOTAL_€"]
        ]
    })

    return mejor_solucion, df_resultado, df_historial

# Mejorar recocido simulado
def aplicar_2opt(ruta):
    """
    Invierte el orden de un subsegmento de paradas dentro de una ruta
    para eliminar cruces de caminos (bucles).
    """
    paradas = ruta["paradas"]
    # Se necesitan al menos 4 paradas para que un intercambio 2-opt altere el orden con sentido
    if len(paradas) < 4:
        return ruta
        
    # Selecciona dos índices aleatorios para delimitar el segmento a invertir
    i, j = sorted(random.sample(range(len(paradas)), 2))
    
    nueva_ruta = deepcopy(ruta)
    # Invierte el segmento entre i y j
    nueva_ruta["paradas"] = paradas[:i] + paradas[i:j+1][::-1] + paradas[j+1:]
    return nueva_ruta

# ============================================================
# EJECUTAR EXPERIMENTOS CON PARAMETRIZACIONES MÚLTIPLES
# ============================================================

def ejecutar_experimentos_sa(
    df_configuraciones,
    solucion_inicial,
    tareas_recogida,
    matriz_distancias
):
    resultados = []

    for idx, row in df_configuraciones.iterrows():
        print("\n" + "=" * 90)
        print(f'CONFIGURACIÓN {idx + 1} / {len(df_configuraciones)}')
        print("=" * 90)
        print(row.to_dict())

        inicio = time.time()

        mejor_solucion, df_resultado, df_historial = recocido_simulado(
            solucion_inicial,
            tareas_recogida,
            matriz_distancias,
            temperatura_inicial=float(row["temperatura_inicial"]),
            temperatura_minima=float(row["temperatura_minima"]),
            factor_enfriamiento=float(row["factor_enfriamiento"]),
            iteraciones_por_temperatura=int(row["iteraciones_por_temperatura"]),
            peso_coste=row["peso_coste"],
            peso_rutas=row["peso_rutas"],
            peso_ocupacion=row["peso_ocupacion"],
            peso_distancia=row["peso_distancia"],
            mostrar_logs=False
        )
        
        tiempo_total = round(time.time() - inicio, 2)
        print(f"Tiempo de ejecución de configuración: {tiempo_total} s")
        
        metricas = calcular_metricas_globales(mejor_solucion)

        resultados.append({
            "temperatura_inicial": row["temperatura_inicial"],
            "factor_enfriamiento": row["factor_enfriamiento"],
            "iteraciones_por_temperatura": int(row["iteraciones_por_temperatura"]),
            "peso_coste": row["peso_coste"],
            "peso_rutas": row["peso_rutas"],
            "peso_ocupacion": row["peso_ocupacion"],
            "peso_distancia": row["peso_distancia"],
            "mejor_coste": df_resultado.loc[df_resultado["Metrica"] == "Mejor coste", "Valor"].values[0],
            "numero_rutas": metricas["TOTAL_RUTAS"],
            "ocupacion_media": metricas["OCUPACION_MEDIA_%"],
            "distancia_total": metricas["DISTANCIA_TOTAL_KM"],
            "coste_total": metricas["COSTE_TOTAL_€"],
            "tiempo_total_min": metricas["TIEMPO_TOTAL_MIN"],
            "tiempo_ejecucion_s": tiempo_total,
            "mejor_solucion": mejor_solucion,
            "df_resultado": df_resultado,
            "df_historial": df_historial
        })

    return pd.DataFrame(resultados)



# ============================================================
# ALGORITMO GENÉTICO (GA) - IMPLEMENTACIÓN INTEGRADA
# ============================================================

def generar_poblacion_inicial(solucion_base, tareas_recogida, matriz_distancias, tamano_poblacion):
    """Genera una población inicial aplicando variaciones válidas sobre la solución base."""
    poblacion = []
    poblacion.append(deepcopy(solucion_base))
    
    intentos = 0
    while len(poblacion) < tamano_poblacion and intentos < tamano_poblacion * 10:
        individuo = generar_vecino(solucion_base, tareas_recogida, matriz_distancias, max_intentos=50)
        valido, _ = validar_solucion(individuo, tareas_recogida)
        if valido and individuo not in poblacion:
            poblacion.append(individuo)
        intentos += 1
        
    while len(poblacion) < tamano_poblacion:
        poblacion.append(deepcopy(solucion_base))
        
    return poblacion


def seleccion_torneo(poblacion, fitness, k=3):
    """Selecciona el mejor individuo de un grupo aleatorio de tamaño k."""
    seleccionados = random.sample(list(zip(poblacion, fitness)), k)
    seleccionados.sort(key=lambda x: x[1])
    return deepcopy(seleccionados[0][0])


def cruce_rutas(padre_a, padre_b, tareas_recogida, matriz_distancias):
    """Intercambia rutas entre padres y repara las inconsistencias de demanda global."""
    if random.random() > 0.8 or len(padre_a) < 2 or len(padre_b) < 2:
        return deepcopy(padre_a), deepcopy(padre_b)
        
    punto_a = random.randint(1, len(padre_a) - 1)
    punto_b = random.randint(1, len(padre_b) - 1)
    
    hijo_a_pre = padre_a[:punto_a] + padre_b[punto_b:]
    hijo_b_pre = padre_b[:punto_b] + padre_a[punto_a:]
    
    hijo_a = reparar_secuencia_demandas(hijo_a_pre, tareas_recogida, matriz_distancias)
    hijo_b = reparar_secuencia_demandas(hijo_b_pre, tareas_recogida, matriz_distancias)
    
    return hijo_a, hijo_b


def reparar_secuencia_demandas(solucion_preliminar, tareas_recogida, matriz_distancias):
    """Ajusta el exceso o falta de paradas/alumnos debido al cruce de rutas."""
    demanda_original = defaultdict(int)
    for _, row in tareas_recogida.iterrows():
        demanda_original[(row["PARADA"], row["CENTRO"])] += row["ALUMNOS"]
        
    paradas_vistas = set()
    solucion_limpia = []
    
    for ruta in solucion_preliminar:
        nueva_ruta = {"id": ruta["id"], "centro": ruta["centro"], "paradas": []}
        for parada in ruta["paradas"]:
            clave = (parada["parada"], parada["centro"])
            if clave not in paradas_vistas:
                nueva_ruta["paradas"].append(parada)
                paradas_vistas.add(clave)
        if len(nueva_ruta["paradas"]) > 0:
            solucion_limpia.append(nueva_ruta)
            
    claves_completas = set(demanda_original.keys())
    faltantes = claves_completas - paradas_vistas
    
    id_ruta = max([r["id"] for r in solucion_limpia]) + 1 if solucion_limpia else 1
    for clave in faltantes:
        nueva_parada = {
            "parada": clave[0],
            "centro": clave[1],
            "alumnos": demanda_original[clave]
        }
        asignado = False
        for ruta in solucion_limpia:
            if ruta["centro"] == clave[1] and (calcular_total_alumnos(ruta) + nueva_parada["alumnos"]) <= 55:
                ruta["paradas"].append(nueva_parada)
                asignado = True
                break
        if not asignado:
            solucion_limpia.append({"id": id_ruta, "centro": clave[1], "paradas": [nueva_parada]})
            id_ruta += 1
            
    for idx, r in enumerate(solucion_limpia):
        r["id"] = idx + 1
        r = optimizar_orden_paradas(r, matriz_distancias)
        
    return recalcular_solucion(solucion_limpia, matriz_distancias)


def algoritmo_genetico(
    solucion_inicial,
    tareas_recogida,
    matriz_distancias,
    tamano_poblacion=30,
    generaciones=50,
    probabilidad_mutacion=0.2,
    peso_coste=1.0,
    peso_rutas=20.0,
    peso_ocupacion=5.0,
    peso_distancia=2.0,
    mostrar_logs=True
):
    tiempo_inicio = time.time()
    
    poblacion = generar_poblacion_inicial(solucion_inicial, tareas_recogida, matriz_distancias, tamano_poblacion)
    
    historial = []
    mejor_solucion_global = deepcopy(solucion_inicial)
    mejor_coste_global = funcion_coste(
        mejor_solucion_global, tareas_recogida, matriz_distancias,
        peso_coste, peso_rutas, peso_ocupacion, peso_distancia
    )
    
    for gen in range(1, generaciones + 1):
        fitness = [
            funcion_coste(ind, tareas_recogida, matriz_distancias, peso_coste, peso_rutas, peso_ocupacion, peso_distancia)
            for ind in poblacion
        ]
        
        for i, ind in enumerate(poblacion):
            if fitness[i] < mejor_coste_global:
                mejor_coste_global = fitness[i]
                mejor_solucion_global = deepcopy(ind)
                
        idx_mejor = fitness.index(min(fitness))
        nueva_poblacion = [deepcopy(poblacion[idx_mejor])]
        
        while len(nueva_poblacion) < tamano_poblacion:
            padre_a = seleccion_torneo(poblacion, fitness)
            padre_b = seleccion_torneo(poblacion, fitness)
            
            hijo_a, hijo_b = cruce_rutas(padre_a, padre_b, tareas_recogida, matriz_distancias)
            
            if random.random() < probabilidad_mutacion:
                hijo_a = generar_vecino(hijo_a, tareas_recogida, matriz_distancias, max_intentos=20)
            if random.random() < probabilidad_mutacion:
                hijo_b = generar_vecino(hijo_b, tareas_recogida, matriz_distancias, max_intentos=20)
                
            nueva_poblacion.append(hijo_a)
            if len(nueva_poblacion) < tamano_poblacion:
                nueva_poblacion.append(hijo_b)
                
        poblacion = nueva_poblacion
        
        coste_medio_gen = round(sum(f for f in fitness if f != float("inf")) / tamano_poblacion, 2)
        historial.append({
            "GENERACION": gen,
            "MEJOR_COSTE": round(mejor_coste_global, 2),
            "COSTE_MEDIO": coste_medio_gen
        })
        
        if mostrar_logs:
            print(f"Gen {gen}/{generaciones} | Mejor Coste: {mejor_coste_global:.2f} | Coste Medio: {coste_medio_gen:.2f}")
            
    tiempo_total = round(time.time() - tiempo_inicio, 2)
    df_historial = pd.DataFrame(historial)
    
    for r in mejor_solucion_global:
        r = optimizar_orden_paradas(r, matriz_distancias)
    mejor_solucion_global = recalcular_solucion(mejor_solucion_global, matriz_distancias)
    metricas = calcular_metricas_globales(mejor_solucion_global)
    
    df_resultado = pd.DataFrame({
        "Metrica": [
            "Algoritmo", "Poblacion", "Generaciones", "Mejor coste", 
            "Tiempo ejecucion (s)", "Numero rutas", "Ocupacion media", 
            "Distancia total", "Coste total"
        ],
        "Valor": [
            "Genético", tamano_poblacion, generaciones, round(mejor_coste_global, 2), 
            tiempo_total, metricas["TOTAL_RUTAS"], metricas["OCUPACION_MEDIA_%"], 
            metricas["DISTANCIA_TOTAL_KM"], metricas["COSTE_TOTAL_€"]
        ]
    })
    
    return mejor_solucion_global, df_resultado, df_historial