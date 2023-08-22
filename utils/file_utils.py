
import os
import json

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
            data = [item.to_dict() if hasattr(item, "to_dict") else item for item in data]
        elif hasattr(data, "to_dict"):
            data = data.to_dict()
        
        json.dump(data, file, indent=4)


def load_from_file(filename):
    """Carga datos desde un archivo JSON"""
    with open(filename, 'r') as file:
        return json.load(file)