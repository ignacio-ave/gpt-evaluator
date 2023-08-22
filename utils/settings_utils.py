import json 
import os


def save_settings(settings):
    """Guarda configuraciones en settings.json"""
    with open('settings.json', 'w') as file:
        json.dump(settings, file, indent=4)

def load_settings():
    """Carga configuraciones desde settings.json"""
    with open('settings.json', 'r') as file:
        return json.load(file)


def ensure_settings_exists():
    """Asegura que exista un archivo settings.json. Si no existe, lo crea solicitando los parámetros al usuario."""
    
    if not os.path.exists("settings.json"):
        print("Archivo settings.json no encontrado. Vamos a crear uno.")
        
        openai_token = input("Por favor, ingresa tu token de OpenAI: ").strip()
        max_tokens = input("Por favor, ingresa el número máximo de tokens (sugerencia: 500): ").strip() or "500"
        max_attempts = input("Por favor, ingresa el número máximo de intentos (sugerencia: 3): ").strip() or "3"
        data_folder_path = input("Por favor, ingresa la ruta de la carpeta de datos: ").strip()
        
        settings = {
            "openai_token": openai_token,
            "max_tokens": int(max_tokens),
            "max_attempts": int(max_attempts),
            "data_folder_path": data_folder_path
        }
        
        save_settings(settings)

        print("Archivo settings.json creado exitosamente.")
    else:
        print("Archivo settings.json encontrado.")
