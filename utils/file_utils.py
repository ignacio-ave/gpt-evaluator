
import os
import json
from models.evaluation import EvaluationJSON

def get_processed_prompts_count(filename="processed_prompts.txt"):
    """Obtiene la cantidad de prompts procesados desde un archivo"""
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return int(f.read().strip())
    return 0

def save_processed_prompts_count(count, filename="processed_prompts.txt"):
    """Guarda la cantidad de prompts procesados en un archivo"""
    with open(filename, 'w') as f:
        f.write(str(count))

def save_to_file(data, filename):
    """Guarda datos en un archivo JSON en la carpeta 'data_created'."""
    
    filepath = filename
    
    with open(filepath, 'w') as file:
        if isinstance(data, list):
            data = [item.dict() if isinstance(item, EvaluationJSON) else item for item in data]
        elif isinstance(data, EvaluationJSON):
            data = data.dict()
        
        json.dump(data, file, indent=4)



def load_from_file(filename):
    """Carga datos desde un archivo JSON"""
    with open(filename, 'r') as file:
        return json.load(file)


def improved_save_to_file(data, filename):
    """Guarda datos en un archivo JSON en la carpeta 'data_created'."""

    filepath = filename

    def serialize_item(item):
        if isinstance(item, EvaluationJSON):
            return item.to_dict()  
        elif isinstance(item, (dict, list, str, int, float, bool, type(None))):
            return item
        else:
            raise TypeError(f"Object of type {item.__class__.__name__} is not serializable")

    with open(filepath, 'w') as file:
        if isinstance(data, list):
            data = [serialize_item(item) for item in data]
        else:
            data = serialize_item(data)

        json.dump(data, file, indent=4)

    return "Data saved successfully!"

