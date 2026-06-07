import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

chave = os.getenv("GROQ_API_KEY")
cliente = Groq(api_key=chave)

resposta = cliente.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": "Explique o que é um token de IA em 2 frases."}],
)

print(resposta.choices[0].message.content)
