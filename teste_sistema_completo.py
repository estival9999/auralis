"""
Teste completo do sistema AURALIS com memória contextual e limpeza automática
"""

import os
import time
from pathlib import Path
from datetime import datetime

# Configurar ambiente
os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY', '')
os.environ['SUPABASE_URL'] = os.getenv('SUPABASE_URL', '')
os.environ['SUPABASE_SERVICE_ROLE_KEY'] = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')

from src.agente_busca_melhorado import AgenteBuscaMelhorado
from src.embeddings_processor import ProcessadorEmbeddings
from src.audio_processor import AudioRecorder
from src.memoria_contextual import obter_gerenciador_memoria

def testar_sistema_completo():
    """Testa todo o fluxo do sistema"""
    print("=== TESTE COMPLETO DO SISTEMA AURALIS ===\n")
    
    # 1. Testar memória contextual
    print("1. Testando Sistema de Memória Contextual")
    print("-" * 50)
    
    gerenciador = obter_gerenciador_memoria()
    
    # Simular conversação
    perguntas = [
        "Qual foi a última reunião gravada?",
        "Quem participou dessa reunião?",
        "Quais foram as principais decisões?",
        "Existe alguma reunião sobre TAMANDUAS?"
    ]
    
    agente = AgenteBuscaMelhorado()
    
    for i, pergunta in enumerate(perguntas):
        print(f"\n🔍 Pergunta {i+1}: {pergunta}")
        resposta = agente.processar_pergunta(pergunta)
        print(f"💬 Resposta: {resposta[:100]}...")
        time.sleep(0.5)
    
    # Mostrar estatísticas
    print("\n\n2. Estatísticas da Memória")
    print("-" * 50)
    stats = gerenciador.memoria.obter_estatisticas()
    for k, v in stats.items():
        print(f"   {k}: {v}")
    
    # Mostrar contexto
    print("\n\n3. Contexto Acumulado")
    print("-" * 50)
    contexto = gerenciador.obter_contexto()
    print(contexto)
    
    # 2. Testar processamento de arquivos com exclusão
    print("\n\n4. Testando Processamento com Limpeza Automática")
    print("-" * 50)
    
    # Criar arquivo temporário de teste
    temp_dir = Path("audio_temp")
    temp_dir.mkdir(exist_ok=True)
    
    arquivo_teste = temp_dir / f"teste_reuniao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    conteudo_teste = """Título: Reunião de Teste de Sistema
Responsável: Sistema Automatizado
Data: 05/01/2025
Hora: 14:30
Observações: Teste de processamento com exclusão automática

Participantes:
- João Silva (Gerente)
- Maria Santos (Analista)

Pauta:
1. Teste do sistema de memória contextual
2. Verificação da limpeza automática de arquivos
3. Validação do processamento de embeddings

Decisões:
- Sistema aprovado para produção
- Implementar melhorias incrementais
- Documentar processos

Esta é uma reunião de teste para validar o sistema completo."""
    
    # Escrever arquivo
    with open(arquivo_teste, 'w', encoding='utf-8') as f:
        f.write(conteudo_teste)
    
    print(f"✅ Arquivo criado: {arquivo_teste.name}")
    print(f"   Tamanho: {arquivo_teste.stat().st_size} bytes")
    
    # Processar com exclusão automática
    processador = ProcessadorEmbeddings()
    sucesso = processador.processar_arquivo(str(arquivo_teste), excluir_apos_processar=True)
    
    if sucesso:
        print("✅ Arquivo processado com sucesso!")
        
        # Verificar se foi excluído
        if not arquivo_teste.exists():
            print("✅ Arquivo removido automaticamente após processamento!")
        else:
            print("❌ Erro: arquivo não foi removido")
    else:
        print("❌ Erro no processamento")
    
    # 3. Testar busca após novo processamento
    print("\n\n5. Testando Busca Após Novo Processamento")
    print("-" * 50)
    
    pergunta_teste = "Qual foi a última reunião sobre teste de sistema?"
    print(f"🔍 Pergunta: {pergunta_teste}")
    resposta = agente.processar_pergunta(pergunta_teste)
    print(f"💬 Resposta: {resposta}")
    
    # 4. Fechar sessão e mostrar resumo
    print("\n\n6. Fechando Sessão e Limpando Memória")
    print("-" * 50)
    
    gerenciador.fechar_sessao()
    
    # Verificar que memória foi limpa
    stats_depois = gerenciador.memoria.obter_estatisticas()
    print("\nEstatísticas após limpeza:")
    print(f"   Total de entradas: {stats_depois['total_entradas']}")
    print(f"   Memória limpa: {'✅' if stats_depois['total_entradas'] == 0 else '❌'}")
    
    # 5. Testar limpeza de arquivos de áudio temporários
    print("\n\n7. Testando Limpeza de Arquivos de Áudio")
    print("-" * 50)
    
    # Listar arquivos em audio_temp
    audio_files = list(temp_dir.glob("*.wav"))
    txt_files = list(temp_dir.glob("*.txt"))
    
    print(f"📁 Pasta audio_temp:")
    print(f"   Arquivos .wav: {len(audio_files)}")
    print(f"   Arquivos .txt: {len(txt_files)}")
    
    if audio_files:
        print("   ⚠️  Arquivos .wav encontrados (deveriam ser limpos após transcrição):")
        for f in audio_files[:3]:  # Mostrar até 3
            print(f"      - {f.name}")
    else:
        print("   ✅ Nenhum arquivo .wav residual")
    
    print("\n=== TESTE COMPLETO FINALIZADO ===")


if __name__ == "__main__":
    testar_sistema_completo()