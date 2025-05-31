#!/usr/bin/env python3
"""
Teste da versão e funcionalidade do OpenAI
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testando OpenAI...")

try:
    import openai
    print(f"OpenAI importado com sucesso")
    print(f"Versão: {openai.__version__ if hasattr(openai, '__version__') else 'Desconhecida'}")
    
    # Testar nova API
    from openai import OpenAI
    from shared.config import OPENAI_API_KEY
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    print("Cliente OpenAI criado com sucesso")
    
    # Testar chamada simples
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Diga apenas 'OK'"}],
        max_tokens=10
    )
    print(f"Teste de chat: {response.choices[0].message.content}")
    
except Exception as e:
    print(f"Erro: {e}")
    import traceback
    traceback.print_exc()