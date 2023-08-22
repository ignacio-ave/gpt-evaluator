import json
import pandas as pd
import re
from models.evaluation import EvaluationJSON, QuestionInfo, EvaluationCriteria
from utils.dataframe_utils import reorganize_dataframe
from utils.file_utils import get_processed_prompts_count, save_processed_prompts_count
from utils.json_utils import flatten_list, extract_from_json_adjusted
from utils.openai_utils import get_openai_key_from_input, init_openai
import openai
from pydantic import BaseModel, Field, validator
from langchain.output_parsers import PydanticOutputParser
import hashlib


def load_json_data():
    """ """
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
    """ """
    pauta_df = pd.read_excel(filepath)
    questions = []
    for index, row in pauta_df.iterrows():
        question_info = {
            'question_id': row["ID"],
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
    """ """
    question_dict = {question.question: question for question in questions}
    prompts = []
    for (student, question_text), row in df.iterrows():
        question = question_dict.get(question_text, {})
        topic = getattr(question, 'topic', "Desconocido")
        scoring_guideline = getattr(question, 'scoring_guideline', "Desconocido")
        criteria = getattr(question, 'criteria', "Desconocido")
        prompt = f'''
        Actúa como un evaluador universitario de la materia ESTRUCTURA DE DATOS. En esta materia se evalúa el conocimiento de los estudiantes del departamento de informática en estructura de datos bien conocida.
        Las respuestas serán teóricas y breves.

        La pregunta a evaluar trata sobre la estructura {topic}
        Información de la Estructura: {scoring_guideline}

        Pregunta: {question_text}
        Respuesta Proporcionada: {row['Respuesta']}

        Criterios de evaluación: {criteria}

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
        prompts.append(prompt)

    return prompts




def generate_responses_recursiva(prompts, responses=None, parsed_evaluations=None):
    """Genera respuestas a partir de una lista de prompts con reintentos ."""
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
            messages = [{'role': 'system', 'content': prompt}]

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
            generate_responses_recursiva(prompts[processed_prompts + n_prompts:], max_tokens, max_attempts, responses, parsed_evaluations)

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


def load_settings():
    """Carga configuraciones desde settings.json"""
    with open('settings.json', 'r') as file:
        return json.load(file)

def save_settings(settings):
    """Guarda configuraciones en settings.json"""
    with open('settings.json', 'w') as file:
        json.dump(settings, file, indent=4)

def save_to_file(data, filename):
    """Guarda datos en un archivo JSON"""
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)

def load_from_file(filename):
    """Carga datos desde un archivo JSON"""
    with open(filename, 'r') as file:
        return json.load(file)





def main():
    df = load_json_data()
    
    df = reorganize_dataframe(df)
    
    questions = load_questions_from_excel(input("Ingrese el nombre del archivo y su ruta: "))

    pydantic_parser = PydanticOutputParser(pydantic_object=EvaluationJSON)
    format_instructions = pydantic_parser.get_format_instructions()
    
    init_openai()

    prompts = generate_prompts_from_dataframe(df, questions, format_instructions)

    

    responses, parsed_responses = generate_responses_recursiva(prompts, responses ,parsed_responses)
    


    
    for response in responses:
        print(response)

if __name__ == "__main__":
    main()
