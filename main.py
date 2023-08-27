import json
import hashlib
import pandas as pd
import openai
import openpyxl
import os
from langchain.output_parsers import PydanticOutputParser

from utils.file_utils import save_to_file, load_from_file, get_processed_prompts_count, save_processed_prompts_count
from utils.dataframe_utils import reorganize_dataframe
from utils.json_utils import extract_from_json_adjusted
from utils.openai_utils import init_openai
from utils.settings_utils import ensure_settings_exists, load_settings, save_settings
from models.evaluation import EvaluationJSON, QuestionInfo



def load_json_data():
    """ Carga archivo json con las respuestas y preguntas """
    file_path = input("Por favor, ingresa la ruta completa del archivo JSON (incluyendo el nombre del archivo): ")
    
    with open(file_path, "r") as file:
        data = json.load(file)
    
    students_data = data[0]
    all_students_data_adjusted = extract_from_json_adjusted(students_data)
    max_columns = max(len(student) for student in all_students_data_adjusted)
    
    for student in all_students_data_adjusted:
        while len(student) < max_columns:
            student.append(Nsone)
    
    num_questions = (max_columns - 6) // 2
    adjusted_columns = ["Nombre", "Email", "Estado", "Inicio", "Fin", "Tiempo"] + [f"Q{i//2+1}" if i % 2 == 0 else f"A{i//2+1}" for i in range(num_questions * 2)]
    df_all_students_final_adjusted = pd.DataFrame(all_students_data_adjusted, columns=adjusted_columns)
    

    output_path = input("Por favor, ingresa la ruta donde deseas guardar el archivo Excel (sin incluir el nombre del archivo): ")
    output_file_name = input("Por favor, ingresa el nombre que deseas para el archivo Excel (por ejemplo, 'mi_archivo.xlsx'): ")
    df_all_students_final_adjusted.to_excel(output_path + '/' + output_file_name, index=False)
    print(f"¡El archivo ha sido guardado en {output_path}/{output_file_name}!")

    df = df_all_students_final_adjusted
    return df


def load_questions_from_excel(filepath):
    """ Carga la pauta """
    pauta_df = pd.read_excel(filepath)
    questions = []
    
    for index, row in pauta_df.iterrows():
        question_id_hash = hashlib.sha256(row["Pregunta"].encode()).hexdigest()
        
        question_info = {
            'question_id': question_id_hash,
            'student': "Sample Student",
            'topic': row["Tópico"],
            'question': row["Pregunta"],
            'total_points': row["Total Puntos"],
            'criteria': row["Scoring Guideline"],
            'scoring_guideline': row["Scoring Guideline"],
            'good_response': row["Response GPT-4"],
            'bad_response': row["Bad Response GPT-4"]
        }
        questions.append(question_info)
    return questions



def generate_prompts_from_dataframe(df, questions, format_instructions):
    """ Genera prompts con la informacion relacionada a la pregunta"""
    IGNORED_RESPONSES = ["Falso", "Verdadero", "-"]
    
    question_dict = {question.question: question for question in questions}
    prompts = []
    
    for (student, question_text), row in df.iterrows():
        
        if row['Respuesta'] in IGNORED_RESPONSES:
            continue

        question = question_dict.get(question_text, {})
        topic = getattr(question, 'topic', "Desconocido")
        scoring_guideline = getattr(question, 'scoring_guideline', "Desconocido")
        criteria = getattr(question, 'criteria', "Desconocido")
        good_response = question.get('good_response', "No proporcionada")
        bad_response = question.get('bad_response', "No proporcionada")

        prompt = f'''
        Actúa como un evaluador universitario de la materia ESTRUCTURA DE DATOS. En esta materia se evalúa el conocimiento de los estudiantes del departamento de informática en estructura de datos bien conocida.
        Las respuestas serán teóricas y breves.

        La pregunta a evaluar trata sobre la estructura {topic}
        Información de la Estructura: {scoring_guideline}

        Pregunta: {question_text}
        Respuesta Proporcionada: {row['Respuesta']}

        Respuesta a evaluar con 3 puntos : {good_response}
        Respuesta a evaluar con 0 puntos : {bad_response}

        Evalua asignando un puntaje de 0 a 3 en cada criterio de evaluación. 0 es la peor calificación y 3 es la mejor calificación.

        Por favor, sigue los siguientes pasos para evaluar la respuesta según los criterios de evaluación:
        1. Analiza la estructura y la información proporcionada.
        2. Revisa la pregunta y la respuesta proporcionada.
        3. Razone sobre la adecuación de la respuesta a la pregunta, considerando los criterios específicos para la estructura en cuestión.
            - Razonamiento sobre la Correctitud de la Respuesta
            - Razonamiento sobre la Claridad de la Respuesta
            - Razonamiento sobre la Relevancia de la Respuesta
        4. Rellena el archivo JSON de evaluación adjunto, incluyendo tus razonamientos y el puntaje asignado en cada criterio.
        5. Devuelve el archivo JSON completado.

        Formato del JSON:
        {format_instructions}
        '''
        prompts.append({"student": student, "prompt": prompt})

    return prompts


unprocessed_prompts_dict = {}

def generate_responses_recursiva(prompts, responses=None, parsed_evaluations=None):
    """Genera respuestas a partir de una lista de prompts con reintentos ."""
    global unprocessed_prompts_dict
    settings = load_settings()
    max_tokens = settings.get("max_tokens", 500)
    max_attempts = settings.get("max_attempts", 3)

    pydantic_parser = PydanticOutputParser(pydantic_object=EvaluationJSON)
    format_instructions = pydantic_parser.get_format_instructions()
    
    if responses is None:
        responses = []
    
    if parsed_evaluations is None:
        parsed_evaluations = []

    total_prompts = len(prompts)
    print(f"Total de prompts a procesar: {total_prompts}")

    processed_prompts = get_processed_prompts_count()
    
    if processed_prompts > 0:
        user_input = input(f"Ya has procesado {processed_prompts} prompts anteriormente. ¿Quieres continuar desde donde lo dejaste? (s/n): ").strip().lower()
        if user_input != 's':
            processed_prompts = 0  # Restablecer el conteo si el usuario no quiere continuar

    n_prompts = int(input(f"¿Cuántos prompts quieres procesar? (Máximo {total_prompts - processed_prompts}): "))

    with open("output.txt", "a") as f:
        
        for i, prompt in enumerate(prompts[processed_prompts:processed_prompts + n_prompts]):
            student = prompt["student"]
            prompt_content = prompt["prompt"]
            messages = [{'role': 'system', 'content': prompt_content}]

            response_content = None

            # Intentar obtener una respuesta que se pueda parsear
            for attempt in range(max_attempts):
                try:
                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=messages,
                        max_tokens=max_tokens
                    )
                    response_content = response.choices[0].message['content']
                    responses.append(response_content)

                    # Intentar parsear la respuesta
                    eval_parsed = pydantic_parser.parse(response_content)
                    parsed_evaluations.append(eval_parsed)
                    break  # Si se parsea correctamente, salimos del bucle de intentos

                except Exception as e:  # Esto manejará tanto errores de la API como errores de parseo
                    if attempt == max_attempts - 1:
                        print(f"Error en el intento {attempt+1} para el prompt {i+1}: {e}")
                        unprocessed_prompts_dict[student] = prompt_content
                        responses.append(None)
                        break

                # Escribir en el archivo solo si se parsea correctamente
                f.write(f"###Human:{prompt}\n###Assistant:{response_content}\n\n")

            # Imprimir la respuesta
            if response_content:
                print(f"Response {i+1}:\n{response_content}\n{'-'*50}")
                save_processed_prompts_count(processed_prompts + i + 1)
                print(f"Prompt {processed_prompts + i + 1}/{total_prompts} procesado correctamente.")

        # Preguntar al usuario si desea continuar
        user_input = input(f"Procesados {processed_prompts + n_prompts}/{total_prompts}. ¿Quieres llamar nuevamente a la función? (s/n): ").strip().lower()
        if user_input == 's':
            #additional_prompts = int(input(f"¿Cuántos prompts adicionales quieres procesar? (Máximo {total_prompts - processed_prompts - n_prompts}): "))

            # Llamada recursiva para procesar más prompts, pasando las listas existentes con argumentos en orden correcto
            generate_responses_recursiva(prompts[processed_prompts + n_prompts:], responses, parsed_evaluations)



    # Si es que existen prompts que no se pudieron procesar
    if unprocessed_prompts_dict:
        save_to_file(unprocessed_prompts_dict, "unprocessed_prompts.json")
        unprocessed_count = len(unprocessed_prompts_dict)
        print(f"\nQuedan {unprocessed_count} prompts sin procesar.")
        user_input = input(f"¿Deseas procesar nuevamente los prompts no procesados? (s/n): ").strip().lower()
        if user_input == 's':
            max_attempts = int(input("Por favor, indica el número de intentos que deseas realizar: "))
            unprocessed_prompts = [{"student": k, "prompt": v} for k, v in unprocessed_prompts_dict.items()]
            generate_responses_recursiva(unprocessed_prompts)

    return responses, parsed_evaluations


def load_questions_from_excel(filepath):
    """Carga las preguntas de un archivo excel y las retorna como una lista de QuestionInfo"""
    pauta_df = pd.read_excel(filepath)
    questions = []
    
    for index, row in pauta_df.iterrows():
        question_info = QuestionInfo(
            question_id=row["ID"],
            student="Sample Student",  # Ejemplo para la desmostracion de la pauta
            topic=row["Tópico"],
            question=row["Pregunta"],
            total_points=row["Total Puntos"],
            criteria=row["Scoring Guideline"],
            scoring_guideline=row["Scoring Guideline"],
            good_response=row["Response GPT-4"],
            bad_response=row["Bad Response GPT-4"]
        )
        questions.append(question_info)
    return questions


def init():
    """Inicialización: carga configuraciones y inicializa OpenAI"""
    init_openai()

def load_data():
    """Cargar datos de estudiantes y preguntas."""
    df = load_json_data()
    df = reorganize_dataframe(df)
    questions_filepath = input("Por favor, ingrese el nombre del archivo 'pauta.xlsx' y su ruta: ")
    questions = load_questions_from_excel(questions_filepath)
    return df, questions

def generate_and_process(df, questions):
    """Generar prompts y obtener respuestas."""
    pydantic_parser = PydanticOutputParser(pydantic_object=EvaluationJSON)
    format_instructions = pydantic_parser.get_format_instructions()
    prompts = generate_prompts_from_dataframe(df, questions, format_instructions)
    responses, parsed_responses = generate_responses_recursiva(prompts)
    return responses, parsed_responses

def save_data(responses, parsed_responses):
    """Guardar respuestas y parsed_responses en archivos."""
    save_to_file(responses, "responses.json")
    save_to_file(parsed_responses, "parsed_responses.json")

def load_previous_data():
    """Cargar datos previamente guardados."""
    try:
        responses = load_from_file("responses.json")
        parsed_responses = load_from_file("parsed_responses.json")
        return responses, parsed_responses
    except:
        return None, None

def display_results(responses):
    """Mostrar las respuestas."""
    for response in responses:
        print(response)


def main():
    """
    Función principal que coordina el flujo del programa.

    1. Verifica la existencia del archivo settings.json y, si no existe, crea uno solicitando los parámetros necesarios al usuario.
    2. Inicializa las configuraciones y la conexión con OpenAI.
    3. Ofrece al usuario la opción de cargar datos previamente guardados o nuevos datos.
    4. Si se elige cargar datos previos:
        - Carga las respuestas y evaluaciones previas.
        - Si hay un error al cargar, procesa nuevos datos.
        - Si no hay error, muestra las respuestas previamente generadas.
        - Ofrece la opción de procesar nuevos datos.
    5. Si se elige cargar nuevos datos o continuar con nuevos datos:
        - Carga datos de estudiantes y preguntas.
        - Genera prompts y obtiene respuestas de OpenAI.
        - Guarda las respuestas y evaluaciones en archivos.
        - Muestra las respuestas obtenidas.

    Esta función se ejecuta cuando el script es llamado directamente.
    """
    ensure_settings_exists()
    init()
    
    # Opción para cargar datos previamente guardados o nuevos datos
    option = input("¿Desea cargar datos previamente guardados? (s/n): ").strip().lower()
    if option == 's':
        responses, parsed_responses = load_previous_data()
        if not responses or not parsed_responses:
            print("Error cargando datos. Cargando nuevos datos...")
            df, questions = load_data()
            responses, parsed_responses = generate_and_process(df, questions)
            save_data(responses, parsed_responses)
        else:
            # Mostrar las respuestas previamente generadas
            display_results(responses)
            # Pregunta al usuario si desea continuar procesando nuevos datos
            option_continue = input("¿Desea continuar procesando nuevos datos? (s/n): ").strip().lower()
            if option_continue == 's':
                df, questions = load_data()
                new_responses, new_parsed_responses = generate_and_process(df, questions)
                responses.extend(new_responses)
                parsed_responses.extend(new_parsed_responses)
                save_data(responses, parsed_responses)
                display_results(new_responses)
    else:
        df, questions = load_data()
        responses, parsed_responses = generate_and_process(df, questions)
        save_data(responses, parsed_responses)
        display_results(responses)

if __name__ == "__main__":
    main()
