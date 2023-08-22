
import json
import re

def flatten_list(l):
    """Función para aplanar listas anidadas"""
    flat_list = []
    for item in l:
        if isinstance(item, list):
            flat_list.extend(flatten_list(item))
        else:
            flat_list.append(item)
    return flat_list

def extract_from_json_adjusted(data):
    """Función para extraer los datos del archivo JSON y generar una lista de listas con los datos de cada estudiante"""
    extracted_data = []
    for student_data in data:
        flattened_data = flatten_list(student_data)
        email_pattern = r"\S+@\S+"
        date_pattern = r"\d{1,2} de \w+ de \d{4}"
        time_pattern = r"\d+ minutos \d+ segundos"
        email = re.search(email_pattern, ' '.join(flattened_data)).group()
        dates = re.findall(date_pattern, ' '.join(flattened_data))
        start_date = dates[0] if len(dates) > 0 else None
        end_date = dates[1] if len(dates) > 1 else None
        time_spent = re.search(time_pattern, ' '.join(flattened_data)).group() if re.search(time_pattern, ' '.join(flattened_data)) else None
        name = flattened_data[0]
        status = flattened_data[3]
        answers = flattened_data[8:]
        student_info = [name, email, status, start_date, end_date, time_spent] + answers
        extracted_data.append(student_info)
    return extracted_data
