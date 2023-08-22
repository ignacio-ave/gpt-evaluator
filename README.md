
# Corrector V3

Este proyecto tiene como objetivo procesar y evaluar respuestas utilizando el modelo GPT de OpenAI. El código se ha modularizado y estructurado para facilitar su mantenimiento y comprensión.

## Estructura del proyecto

El proyecto consta de varios archivos y carpetas:

- `main.py`: Es el archivo principal que coordina el flujo del programa.
- `models/`: Carpeta que contiene las definiciones de modelos.
- `utils/`: Carpeta con funciones auxiliares para manejar JSON, DataFrames, y otros.

## Instalación

1. Clonar este repositorio.
2. Instalar las dependencias:

```bash
pip install -r requirements.txt
```

## Uso

Para ejecutar el programa principal, simplemente ejecuta:

```bash
python main.py
```

Asegúrate de tener todos los archivos de entrada necesarios y de seguir las instrucciones en la consola.

# Análisis del archivo `main.py`

## Descripción General

El archivo `main.py` sirve como punto de entrada y coordinación del programa. Contiene una serie de funciones que facilitan el procesamiento, evaluación y presentación de los datos de los estudiantes.

## Funciones Principales

Dentro de este archivo, encontramos las siguientes funciones clave:

- **`load_json_data()`**: 
    - **Descripción**: Carga y estructura los datos de los estudiantes desde un archivo JSON.
    - **Salida**: DataFrame estructurado con los datos de los estudiantes.

- **`load_questions_from_excel(filepath)`**: 
    - **Descripción**: Importa las preguntas desde un archivo Excel.
    - **Parámetros**: Ruta del archivo Excel.
    - **Salida**: Lista con la información detallada de cada pregunta.

- **`generate_prompts_from_dataframe(df, questions, format_instructions)`**: 
    - **Descripción**: Crea prompts para la evaluación basados en el DataFrame de estudiantes y las preguntas.
    - **Parámetros**: DataFrame de estudiantes, preguntas, instrucciones de formato.
    - **Salida**: Lista de prompts generados.

- **`generate_responses_recursiva(prompts, responses=None, parsed_evaluations=None)`**: 
    - **Descripción**: Utiliza GPT-4 para generar respuestas a partir de los prompts.
    - **Parámetros**: Lista de prompts, respuestas previas (opcional), evaluaciones parseadas previamente (opcional).
    - **Salida**: Respuestas generadas y sus respectivas evaluaciones parseadas.

- **`init()`**: 
    - **Descripción**: Inicializa la conexión con OpenAI.

- **`load_data()`**: 
    - **Descripción**: Función de alto nivel que coordina la carga de datos de estudiantes y preguntas.
    - **Salida**: DataFrame de estudiantes y lista de preguntas.

- **`generate_and_process(df, questions)`**: 
    - **Descripción**: Coordina la generación de prompts y obtiene las respuestas.
    - **Parámetros**: DataFrame de estudiantes, preguntas.
    - **Salida**: Respuestas generadas y evaluaciones parseadas.

- **`save_data(responses, parsed_responses)`**: 
    - **Descripción**: Guarda las respuestas y evaluaciones en archivos.
    - **Parámetros**: Respuestas y evaluaciones parseadas.

- **`load_previous_data()`**: 
    - **Descripción**: Carga datos previamente guardados si existen.
    - **Salida**: Respuestas y evaluaciones parseadas previamente guardadas.

- **`display_results(responses)`**: 
    - **Descripción**: Visualiza las respuestas generadas.
    - **Parámetros**: Respuestas generadas.

- **`main()`**: 
    - **Descripción**: Función principal que coordina todas las operaciones, desde la carga de datos hasta la visualización de resultados.

## Contribuciones

Si deseas contribuir al proyecto, asegúrate de escribir pruebas para cualquier nueva función o método y de seguir las convenciones de código existentes.

## Licencia

Este proyecto está bajo la licencia MIT.

