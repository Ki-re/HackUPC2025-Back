import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=API_KEY)

model = genai.GenerativeModel('gemini-2.0-flash-lite')

def obtener_codigo_iata(ciudad):

    
    prompt = (
        f"Quiero coger una avión desde la ciudad {ciudad} dame el código IATA del aeropuerto principal más cercano. "
        "Respóndeme únicamente con el código IATA, nada más."
    )
    
    try:
        response = model.generate_content(prompt)
        codigo = response.text.strip().upper()

        if len(codigo) == 3 and codigo.isalpha():
            return codigo
        else:
            raise ValueError(f"Respuesta inesperada: {codigo}")
    except Exception as e:
        print(f"Error al obtener el código IATA: {e}")
        return None
