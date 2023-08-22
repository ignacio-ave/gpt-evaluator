
import os

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
