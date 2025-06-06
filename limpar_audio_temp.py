"""
Script para limpar arquivos residuais da pasta audio_temp
"""

import os
from pathlib import Path

def limpar_audio_temp():
    """Limpa todos os arquivos da pasta audio_temp"""
    audio_temp = Path("audio_temp")
    
    if not audio_temp.exists():
        print("📁 Pasta audio_temp não encontrada")
        return
    
    # Listar arquivos
    arquivos = list(audio_temp.glob("*"))
    
    if not arquivos:
        print("✅ Pasta audio_temp já está vazia")
        return
    
    print(f"🗑️  Encontrados {len(arquivos)} arquivo(s) para limpar:")
    
    for arquivo in arquivos:
        print(f"   - {arquivo.name}")
        try:
            arquivo.unlink()
            print(f"     ✅ Removido")
        except Exception as e:
            print(f"     ❌ Erro: {e}")
    
    print("\n✨ Limpeza concluída!")

if __name__ == "__main__":
    limpar_audio_temp()