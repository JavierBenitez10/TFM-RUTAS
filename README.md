# Optimización de rutas de transporte escolar mediante Inteligencia Artificial

## Repositorio de apoyo al Trabajo Fin de Máster

**Autor:** José Javier Benítez Guerrero

**Máster Universitario en Inteligencia Artificial**

**Universidad Internacional de La Rioja (UNIR)**


## Introducción

Este repositorio contiene el código fuente desarrollado durante la realización del Trabajo Fin de Máster del Máster Universitario en Inteligencia Artificial de la Universidad Internacional de La Rioja (UNIR).

La memoria del Trabajo Fin de Máster constituye el documento principal de la investigación y es el único documento presentado para su evaluación.

La publicación de este repositorio se realiza de forma voluntaria con el objetivo de favorecer la transparencia, la reproducibilidad y la difusión del trabajo desarrollado, permitiendo a cualquier persona interesada consultar la implementación de los algoritmos descritos en la memoria.

Por tanto, este repositorio debe entenderse como un material complementario de apoyo y no como parte de la documentación oficialmente requerida para la evaluación del Trabajo Fin de Máster.

---

# Descripción del proyecto

El proyecto aborda el problema de optimización de rutas de transporte escolar (*School Bus Routing Problem - SBRP*), perteneciente a la familia de problemas de optimización conocidos como *Vehicle Routing Problem (VRP)*.

El objetivo consiste en generar automáticamente rutas de transporte escolar que permitan mejorar la eficiencia del servicio respetando las restricciones operativas existentes, tales como la capacidad de los vehículos, los tiempos máximos de recorrido y la correcta asignación de los alumnos a sus respectivos centros educativos.

Para ello se implementan y comparan dos técnicas metaheurísticas ampliamente utilizadas en problemas de optimización combinatoria:

- Recocido Simulado (*Simulated Annealing*)
- Algoritmo Genético (*Genetic Algorithm*)

Ambos algoritmos han sido desarrollados íntegramente en Python y aplicados sobre un modelo de datos diseñado específicamente para este trabajo.

---

# Objetivos del proyecto

La implementación persigue los siguientes objetivos:

- Automatizar el proceso de planificación de rutas de transporte escolar.
- Reducir el coste económico asociado al servicio.
- Minimizar la distancia total recorrida por la flota.
- Reducir el número de rutas necesarias.
- Mejorar la ocupación media de los vehículos.
- Garantizar el cumplimiento de todas las restricciones operativas definidas para el problema.

---

# Funcionalidades implementadas

El proyecto incluye, entre otras, las siguientes funcionalidades:

- Construcción automática de una solución inicial.
- Validación completa de las restricciones del problema.
- Cálculo automático de métricas operativas.
- Optimización mediante Recocido Simulado.
- Optimización mediante Algoritmo Genético.
- Comparación objetiva entre ambos algoritmos.
- Generación de indicadores globales de rendimiento.

---

# Restricciones consideradas

El modelo contempla las principales restricciones presentes en un problema real de transporte escolar:

- Capacidad máxima de los vehículos.
- Tiempo máximo permitido por ruta.
- Asignación de un único centro educativo por ruta.
- Conservación íntegra de la demanda.
- Eliminación de duplicidades en las asignaciones.
- Validación automática de todas las soluciones generadas.

Asimismo, la función objetivo combina distintos criterios de optimización mediante un sistema configurable de ponderaciones.

---

# Tecnologías utilizadas

El desarrollo se ha realizado utilizando las siguientes herramientas:

- Python 3
- Pandas
- NumPy
- SQLAlchemy
- Oracle Database
- Jupyter Notebook

---

# Estructura del repositorio

```
.
├── Modulo_Principal.ipynb      # Ejecución principal del proyecto
├── funciones.py                # Implementación de algoritmos y lógica de negocio
├── funciones_carga.py          # Carga y preparación de datos
├── preprocesado.sql            # Preparación del modelo de datos
├── matriz_alumnos.xlsx         # Datos de ejemplo
├── matriz_distancias.xlsx      # Matriz de distancias y tiempos
├── requirements.txt
└── README.md
```

---

# Ejecución

## 1. Instalar las dependencias

```bash
pip install -r requirements.txt
```

## 2. Ejecutar el proyecto

Abrir el cuaderno

```
Modulo_Principal.ipynb
```

y ejecutar las celdas de forma secuencial.

---

# Datos

Los datos empleados durante el desarrollo del Trabajo Fin de Máster proceden de información utilizada para la investigación.

Con el fin de facilitar la comprensión del funcionamiento del proyecto, el repositorio incluye únicamente la información necesaria para reproducir la ejecución del algoritmo.

Cuando ha sido necesario, determinados elementos han sido simplificados o anonimizados para evitar la publicación de información no relevante para la comprensión del trabajo.

---

# Contexto académico

Este repositorio acompaña al Trabajo Fin de Máster titulado:

**"Optimización de la elaboración de rutas de transporte escolar mediante Inteligencia Artificial"**

desarrollado en el marco del Máster Universitario en Inteligencia Artificial de la Universidad Internacional de La Rioja (UNIR).

El objetivo del repositorio es facilitar el acceso a la implementación desarrollada durante la investigación y favorecer la reproducibilidad del trabajo realizado.

---

# Licencia

Este proyecto se publica exclusivamente con fines académicos y de investigación.

El código puede consultarse libremente como material de apoyo al Trabajo Fin de Máster.

---

# Contacto

**José Javier Benítez Guerrero**

GitHub: https://github.com/JavierBenitez10/TFM-RUTAS
