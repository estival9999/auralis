#!/usr/bin/env python3
"""
Teste do sistema de histórico melhorado
Verifica busca do Supabase e reconstrução de reuniões
"""

import os
import sys
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.append(str(Path(__file__).parent))

# Carregar variáveis de ambiente
from dotenv import load_dotenv
load_dotenv()

def testar_busca_reunioes():
    """Testa busca de reuniões do Supabase"""
    print("🔍 Testando busca de reuniões do Supabase...")
    
    from main import AURALISBackend
    backend = AURALISBackend()
    
    try:
        # Buscar reuniões
        resultado = backend.supabase.table('reunioes_embbed').select(
            'arquivo_origem, titulo, responsavel, data_reuniao, hora_inicio, created_at, metadados'
        ).order('created_at', desc=True).execute()
        
        if resultado.data:
            print(f"✅ Encontradas {len(resultado.data)} reuniões no banco")
            
            # Agrupar por arquivo_origem
            reunioes_dict = {}
            for registro in resultado.data:
                arquivo = registro['arquivo_origem']
                if arquivo not in reunioes_dict:
                    reunioes_dict[arquivo] = registro
            
            print(f"📋 {len(reunioes_dict)} reuniões únicas encontradas")
            
            # Mostrar primeira reunião
            if reunioes_dict:
                primeira = list(reunioes_dict.values())[0]
                print(f"\n📄 Primeira reunião:")
                print(f"   Título: {primeira.get('titulo', 'Sem título')}")
                print(f"   Arquivo: {primeira.get('arquivo_origem', '')}")
                print(f"   Responsável: {primeira.get('responsavel', 'N/A')}")
                print(f"   Data: {primeira.get('data_reuniao', 'N/A')}")
                
                return primeira.get('arquivo_origem')
        else:
            print("⚠️  Nenhuma reunião encontrada no banco")
            return None
            
    except Exception as e:
        print(f"❌ Erro ao buscar reuniões: {e}")
        return None

def testar_reconstrucao(arquivo_origem):
    """Testa reconstrução de reunião"""
    if not arquivo_origem:
        print("⚠️  Sem arquivo para testar reconstrução")
        return
        
    print(f"\n🔧 Testando reconstrução da reunião: {arquivo_origem}")
    
    try:
        from src.reuniao_reconstructor import ReconstructorReunioes
        from main import AURALISBackend
        
        backend = AURALISBackend()
        reconstructor = ReconstructorReunioes(backend.supabase)
        
        reuniao_dict = reconstructor.reconstruir_reuniao(arquivo_origem)
        
        if reuniao_dict and 'conteudo_completo' in reuniao_dict:
            texto_completo = reuniao_dict['conteudo_completo']
            
            if texto_completo:
                print("✅ Reunião reconstruída com sucesso!")
                print(f"📏 Tamanho do texto: {len(texto_completo)} caracteres")
                print(f"\n📝 Primeiros 500 caracteres:")
                print("-" * 50)
                print(texto_completo[:500] + "...")
                print("-" * 50)
            else:
                print("❌ Texto vazio na reunião reconstruída")
        else:
            print("❌ Falha ao reconstruir reunião")
            
    except Exception as e:
        print(f"❌ Erro ao reconstruir: {e}")

def testar_analise_ia(arquivo_origem):
    """Testa análise com IA"""
    if not arquivo_origem:
        return
        
    print(f"\n🤖 Testando análise com IA...")
    
    try:
        from main import AURALISBackend
        from src.reuniao_reconstructor import ReconstructorReunioes
        
        backend = AURALISBackend()
        reconstructor = ReconstructorReunioes(backend.supabase)
        
        # Buscar info da reunião
        info_resultado = backend.supabase.table('reunioes_embbed').select(
            'titulo, responsavel, data_reuniao, hora_inicio, observacoes'
        ).eq('arquivo_origem', arquivo_origem).limit(1).execute()
        
        if not info_resultado.data:
            print("❌ Não foi possível buscar informações da reunião")
            return
            
        info_reuniao = info_resultado.data[0]
        reuniao_dict = reconstructor.reconstruir_reuniao(arquivo_origem)
        
        if not reuniao_dict or 'conteudo_completo' not in reuniao_dict:
            print("❌ Não foi possível reconstruir texto")
            return
        
        texto_completo = reuniao_dict['conteudo_completo']
        
        # Simular análise (sem chamar OpenAI para economizar)
        print("✅ Sistema pronto para análise com IA")
        print(f"   Texto disponível: {len(texto_completo)} caracteres")
        print(f"   Responsável: {info_reuniao.get('responsavel', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Erro na preparação para análise: {e}")

def main():
    """Executa todos os testes"""
    print("🚀 Iniciando testes do histórico melhorado...")
    print("=" * 60)
    
    # Testar busca
    arquivo_origem = testar_busca_reunioes()
    
    # Testar reconstrução
    if arquivo_origem:
        testar_reconstrucao(arquivo_origem)
        testar_analise_ia(arquivo_origem)
    
    print("\n✅ Testes concluídos!")

if __name__ == "__main__":
    main()