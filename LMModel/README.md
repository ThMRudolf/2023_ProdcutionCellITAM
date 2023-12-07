# INIT

Para abrir la aplicación correr en terminal:
1. `Rscript data/create_csv.R` 
2. `docker-compose up`.

# Integrantes del equipo:

| Nombre | CU | Github |
|--------------|--------------|--------------|
| Lauro Reyes Rosas  | 214532    | LauShang    |
| Claudia Ximena Paz Cendejas | 214570 | XimenaPaz22    |
| Carlos Guillermo Mayorga Tapia | 149617    | maggss44    |
| Thomas Martin Rudolf | 169296 | ThMRudolf |


# Proyecto de Predicción de Consumo de Energía en Cortes de Maquinaria
### Objetivo del Proyecto

El objetivo principal de este proyecto es desarrollar un modelo predictivo de consumo de energía para máquinas de corte mediante la recopilación de datos manuales. Se pretende optimizar la eficiencia energética y reducir costos al predecir el consumo de energía necesario para realizar cortes específicos. El enfoque se basa en la implementación de un algoritmo de Random Forest que utiliza variables como la profundidad de corte, el tipo de herramienta, el número de insertos, entre otros.

## Descripción del Proceso
### Recopilación Manual de Datos:

Se recopilan datos de cortes de maquinaria de forma manual, incluyendo información detallada sobre la profundidad de corte, el tipo de herramienta utilizada, el número de insertos, y otros factores relevantes.

### Preprocesamiento de Datos:

Los datos recopilados se someten a un proceso de preprocesamiento para garantizar su calidad y coherencia. Se realizó tareas como la limpieza de datos.

### Construcción del Modelo Random Forest:

Se implementa un modelo de Random Forest en R, un algoritmo de aprendizaje supervisado, utilizando los datos recolectados, la base final consta de 1,184 datos. El modelo se entrena para aprender patrones y relaciones entre las variables de entrada y el consumo de energía.

### Beneficios Esperados
* **Optimización de la Eficiencia Energética:**

    * Al predecir el consumo de energía necesario para cada corte, se busca optimizar el uso de recursos, reduciendo así los costos asociados.

* **Mejora en la Planificación de Operaciones:**

    * La capacidad de prever el consumo de energía permite una planificación más eficiente de las operaciones de corte, mejorando la programación y la asignación de recursos.
* **Reducción de Residuos y Tiempo de Inactividad:**

    * Al contar con un modelo predictivo preciso, se espera minimizar los residuos generados y reducir el tiempo de inactividad de las máquinas al planificar cortes de manera más efectiva.

Este proyecto marca un milestone en el desarrollo de un modelo destinado a mejorar la eficiencia y sostenibilidad en las operaciones de maquinaria de corte industrial.