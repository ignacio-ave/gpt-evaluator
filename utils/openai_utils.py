
import openai
from getpass import getpass
import json

def get_openai_key_from_input():
    """Obtiene el token del API de OpenAI a través de una entrada segura"""
    try:
        openai_api_key = getpass('Por favor, ingrese su token de API de OpenAI: ')
        if not openai_api_key:
            raise ValueError('No se proporcionó el token de API de OpenAI.')
        return openai_api_key
    except Exception as e:
        print(f'Error obteniendo el token de API de OpenAI: {e}')
        raise

import json

def load_openai_key_from_settings():
    """Carga el token del API de OpenAI desde settings.json"""
    try:
        with open('settings.json', 'r') as file:
            settings = json.load(file)
        return settings.get("openai_token")
    except Exception as e:
        print(f'Error cargando el token de API de OpenAI desde settings.json: {e}')
        raise

def init_openai():
    """Inicializa el cliente de OpenAI con el token del API"""
    try:
        openai.api_key = load_openai_key_from_settings()
        if not openai.api_key:
            try:
                openai.api_key = get_openai_key_from_input()

            except Exception as e:
                print(f'Error inicializando OpenAI: {e}')
                raise

    except Exception as e:
        print(f'Error inicializando OpenAI: {e}')
        raise