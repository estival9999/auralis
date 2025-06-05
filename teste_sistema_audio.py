#!/usr/bin/env python3
"""
Script de teste para demonstrar a funcionalidade de áudio
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.embeddings_processor import ProcessadorEmbeddings
from datetime import datetime

def testar_processamento_texto():
    """Testa o processamento de uma reunião via texto"""
    print("🧪 Teste 1: Processamento de reunião via texto")
    print("-" * 50)
    
    # Criar arquivo de teste
    titulo = "Reunião de Planejamento Q1 2025"
    conteudo = """
    Participantes: João Silva (Gerente), Maria Santos (Dev Lead), Pedro Costa (Product Owner)
    
    Agenda:
    1. Revisão dos resultados Q4 2024
    2. Definição de metas Q1 2025
    3. Alocação de recursos
    4. Cronograma de entregas
    
    Decisões tomadas:
    - Meta de crescimento: 25% no trimestre
    - Foco em melhorias de performance
    - Contratação de 2 novos desenvolvedores
    - Sprint de 2 semanas mantido
    
    Próximos passos:
    - João: Aprovar orçamento até 15/01
    - Maria: Definir roadmap técnico até 20/01
    - Pedro: Alinhar com stakeholders até 18/01
    """
    
    # Salvar em arquivo temporário
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    arquivo_temp = f"teste_reuniao_{timestamp}.txt"
    
    with open(arquivo_temp, "w", encoding="utf-8") as f:
        f.write(f"Título: {titulo}\n")
        f.write(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
        f.write(f"\n{conteudo}")
    
    print(f"✅ Arquivo criado: {arquivo_temp}")
    
    # Processar embeddings
    try:
        processador = ProcessadorEmbeddings()
        print("🔄 Processando embeddings...")
        
        # O processador extrai metadados automaticamente do arquivo
        sucesso = processador.processar_arquivo(arquivo_temp)
        
        if sucesso:
            print("✅ Embeddings processados e salvos no Supabase!")
            
            # Testar busca
            from src.agente_busca_reunioes import AgenteBuscaReunioes
            agente = AgenteBuscaReunioes()
            
            print("\n🔍 Testando busca semântica...")
            perguntas = [
                "Quais foram as decisões sobre contratação?",
                "Qual a meta de crescimento definida?",
                "Quem é responsável pelo roadmap técnico?"
            ]
            
            for pergunta in perguntas:
                print(f"\n❓ Pergunta: {pergunta}")
                resposta = agente.processar_pergunta(pergunta)
                print(f"💬 Resposta: {resposta}")
        else:
            print("❌ Erro ao processar embeddings")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
    finally:
        # Limpar arquivo temporário
        if os.path.exists(arquivo_temp):
            os.remove(arquivo_temp)
            print(f"\n🗑️  Arquivo temporário removido")

def testar_interface_audio():
    """Mostra como a interface de áudio funciona"""
    print("\n\n🧪 Teste 2: Interface de Áudio")
    print("-" * 50)
    
    print("""
    A interface de áudio no AURALIS funciona assim:
    
    1. No menu principal, clique em "NOVA GRAVAÇÃO"
    2. Você verá duas abas: "📝 Texto" e "🎤 Áudio"
    3. Clique na aba "🎤 Áudio"
    4. Digite o título da reunião
    5. Clique no botão "🎤 Iniciar Gravação"
    6. O botão mudará para "⏹️ Parar Gravação" e mostrará o tempo
    7. Fale normalmente próximo ao microfone
    8. Clique para parar quando terminar
    9. O sistema irá:
       - Salvar o áudio em fragmentos de até 25MB
       - Transcrever usando OpenAI Whisper
       - Processar embeddings automaticamente
       - Permitir busca no conteúdo transcrito
    
    Recursos visuais:
    - Contador de tempo em tempo real
    - Indicador visual do status (gravando/processando)
    - Feedback de sucesso ou erro
    """)
    
    # Verificar se PyAudio está disponível
    try:
        import pyaudio
        p = pyaudio.PyAudio()
        device_count = p.get_device_count()
        print(f"\n✅ PyAudio instalado - {device_count} dispositivos de áudio encontrados")
        
        for i in range(device_count):
            info = p.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                print(f"   🎤 Entrada: {info['name']}")
                
        p.terminate()
    except Exception as e:
        print(f"\n⚠️  PyAudio com problemas: {e}")
        print("   Para ambientes sem áudio, o sistema mostrará mensagem apropriada")

def main():
    print("🚀 AURALIS - Sistema de Teste de Funcionalidades")
    print("=" * 50)
    
    # Teste 1: Processamento de texto
    testar_processamento_texto()
    
    # Teste 2: Interface de áudio
    testar_interface_audio()
    
    print("\n\n✅ Testes concluídos!")
    print("\nPara testar a interface completa, execute:")
    print("   python3 FRONT.py")

if __name__ == "__main__":
    main()