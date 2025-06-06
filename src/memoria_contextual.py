"""
Sistema de memória contextual com estratégia LRU para o agente AURALIS
Mantém contexto da conversa com gerenciamento eficiente de memória
"""

import time
import json
from collections import OrderedDict
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import threading

class MemoriaContextualLRU:
    """
    Sistema de memória contextual usando Least Recently Used (LRU)
    para manter histórico de conversas com limite de capacidade
    """
    
    def __init__(self, capacidade_maxima: int = 100, tempo_expiracao_minutos: int = 30):
        """
        Inicializa o sistema de memória
        
        Args:
            capacidade_maxima: Número máximo de entradas na memória
            tempo_expiracao_minutos: Tempo em minutos para expirar entradas antigas
        """
        self.capacidade_maxima = capacidade_maxima
        self.tempo_expiracao = timedelta(minutes=tempo_expiracao_minutos)
        
        # OrderedDict mantém ordem de inserção e permite reordenar
        self.memoria: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        
        # Lock para operações thread-safe
        self.lock = threading.Lock()
        
        # Estatísticas
        self.hits = 0
        self.misses = 0
        self.total_acessos = 0
        
        # ID da sessão atual
        self.sessao_id = self._gerar_sessao_id()
        
        print(f"✅ Sistema de memória contextual iniciado (capacidade: {capacidade_maxima}, expiração: {tempo_expiracao_minutos}min)")
    
    def _gerar_sessao_id(self) -> str:
        """Gera ID único para a sessão"""
        return f"sessao_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def adicionar_interacao(self, pergunta: str, resposta: str, metadados: Optional[Dict] = None):
        """
        Adiciona uma interação pergunta-resposta à memória
        
        Args:
            pergunta: Pergunta do usuário
            resposta: Resposta do sistema
            metadados: Informações adicionais (reuniões encontradas, contexto, etc)
        """
        with self.lock:
            # Criar chave única para a interação
            timestamp = datetime.now()
            chave = f"{self.sessao_id}_{timestamp.strftime('%H%M%S%f')}"
            
            # Preparar entrada
            entrada = {
                'timestamp': timestamp,
                'pergunta': pergunta,
                'resposta': resposta,
                'metadados': metadados or {},
                'acessos': 1,
                'ultimo_acesso': timestamp
            }
            
            # Se atingiu capacidade máxima, remover entrada mais antiga
            if len(self.memoria) >= self.capacidade_maxima:
                # Remove o item menos recentemente usado (primeiro da OrderedDict)
                item_removido = self.memoria.popitem(last=False)
                print(f"🗑️  Memória LRU: removida entrada antiga {item_removido[0]}")
            
            # Adicionar nova entrada
            self.memoria[chave] = entrada
            
            # Limpar entradas expiradas
            self._limpar_expiradas()
            
            print(f"💾 Memória: adicionada interação (total: {len(self.memoria)})")
    
    def obter_contexto_recente(self, limite: int = 5) -> List[Dict[str, Any]]:
        """
        Obtém as interações mais recentes
        
        Args:
            limite: Número máximo de interações a retornar
            
        Returns:
            Lista com as interações mais recentes
        """
        with self.lock:
            self.total_acessos += 1
            
            # Pegar as últimas N entradas
            entradas_recentes = list(self.memoria.values())[-limite:]
            
            # Atualizar estatísticas
            if entradas_recentes:
                self.hits += 1
            else:
                self.misses += 1
            
            # Atualizar último acesso
            for entrada in entradas_recentes:
                entrada['ultimo_acesso'] = datetime.now()
                entrada['acessos'] += 1
            
            return entradas_recentes
    
    def buscar_por_tema(self, tema: str, limite: int = 10) -> List[Dict[str, Any]]:
        """
        Busca interações relacionadas a um tema específico
        
        Args:
            tema: Tema ou palavra-chave para buscar
            limite: Número máximo de resultados
            
        Returns:
            Lista de interações relevantes
        """
        with self.lock:
            self.total_acessos += 1
            tema_lower = tema.lower()
            
            resultados = []
            for chave, entrada in self.memoria.items():
                # Buscar tema na pergunta, resposta ou metadados
                if (tema_lower in entrada['pergunta'].lower() or 
                    tema_lower in entrada['resposta'].lower() or
                    any(tema_lower in str(v).lower() for v in entrada['metadados'].values())):
                    
                    resultados.append(entrada)
                    # Mover para o final (mais recente) na OrderedDict
                    self.memoria.move_to_end(chave)
                    # Atualizar acesso
                    entrada['ultimo_acesso'] = datetime.now()
                    entrada['acessos'] += 1
                
                if len(resultados) >= limite:
                    break
            
            # Atualizar estatísticas
            if resultados:
                self.hits += 1
            else:
                self.misses += 1
            
            return resultados
    
    def obter_resumo_sessao(self) -> Dict[str, Any]:
        """
        Obtém resumo da sessão atual
        
        Returns:
            Dicionário com estatísticas e resumo
        """
        with self.lock:
            if not self.memoria:
                return {
                    'sessao_id': self.sessao_id,
                    'total_interacoes': 0,
                    'duracao': '0 minutos',
                    'temas_principais': [],
                    'estatisticas': self.obter_estatisticas()
                }
            
            # Calcular duração
            timestamps = [entrada['timestamp'] for entrada in self.memoria.values()]
            inicio = min(timestamps)
            fim = max(timestamps)
            duracao = fim - inicio
            
            # Extrair temas dos metadados
            todos_temas = []
            for entrada in self.memoria.values():
                if 'temas' in entrada['metadados']:
                    todos_temas.extend(entrada['metadados']['temas'])
            
            # Contar frequência de temas
            from collections import Counter
            temas_freq = Counter(todos_temas)
            temas_principais = [tema for tema, _ in temas_freq.most_common(5)]
            
            return {
                'sessao_id': self.sessao_id,
                'total_interacoes': len(self.memoria),
                'duracao': f"{duracao.total_seconds() / 60:.1f} minutos",
                'temas_principais': temas_principais,
                'inicio_sessao': inicio.strftime('%H:%M:%S'),
                'ultima_interacao': fim.strftime('%H:%M:%S'),
                'estatisticas': self.obter_estatisticas()
            }
    
    def _limpar_expiradas(self):
        """Remove entradas que expiraram"""
        agora = datetime.now()
        chaves_remover = []
        
        for chave, entrada in self.memoria.items():
            if agora - entrada['ultimo_acesso'] > self.tempo_expiracao:
                chaves_remover.append(chave)
        
        for chave in chaves_remover:
            del self.memoria[chave]
            
        if chaves_remover:
            print(f"🧹 Memória: removidas {len(chaves_remover)} entradas expiradas")
    
    def obter_estatisticas(self) -> Dict[str, Any]:
        """Obtém estatísticas de uso da memória"""
        taxa_acerto = (self.hits / self.total_acessos * 100) if self.total_acessos > 0 else 0
        
        return {
            'total_entradas': len(self.memoria),
            'capacidade_usada': f"{len(self.memoria) / self.capacidade_maxima * 100:.1f}%",
            'total_acessos': self.total_acessos,
            'hits': self.hits,
            'misses': self.misses,
            'taxa_acerto': f"{taxa_acerto:.1f}%"
        }
    
    def limpar_memoria(self):
        """Limpa toda a memória"""
        with self.lock:
            tamanho_anterior = len(self.memoria)
            self.memoria.clear()
            self.hits = 0
            self.misses = 0
            self.total_acessos = 0
            print(f"🗑️  Memória limpa: {tamanho_anterior} entradas removidas")
    
    def exportar_sessao(self) -> Dict[str, Any]:
        """
        Exporta dados da sessão para possível persistência
        
        Returns:
            Dicionário com todos os dados da sessão
        """
        with self.lock:
            return {
                'sessao_id': self.sessao_id,
                'timestamp_export': datetime.now().isoformat(),
                'resumo': self.obter_resumo_sessao(),
                'interacoes': [
                    {
                        'timestamp': entrada['timestamp'].isoformat(),
                        'pergunta': entrada['pergunta'],
                        'resposta': entrada['resposta'],
                        'metadados': entrada['metadados'],
                        'acessos': entrada['acessos']
                    }
                    for entrada in self.memoria.values()
                ]
            }
    
    def formatar_contexto_para_agente(self, limite: int = 3) -> str:
        """
        Formata o contexto recente para ser usado pelo agente
        
        Args:
            limite: Número de interações a incluir
            
        Returns:
            String formatada com o contexto
        """
        interacoes = self.obter_contexto_recente(limite)
        
        if not interacoes:
            return ""
        
        contexto_parts = ["### Contexto da Conversa Anterior ###\n"]
        
        for i, interacao in enumerate(interacoes, 1):
            contexto_parts.append(f"**Interação {i}:**")
            contexto_parts.append(f"- Pergunta: {interacao['pergunta']}")
            contexto_parts.append(f"- Resposta: {interacao['resposta'][:200]}...")
            
            if interacao['metadados'].get('reunioes_encontradas'):
                contexto_parts.append(f"- Reuniões mencionadas: {', '.join(interacao['metadados']['reunioes_encontradas'])}")
            
            contexto_parts.append("")
        
        return "\n".join(contexto_parts)


class GerenciadorMemoria:
    """
    Gerenciador de memória que integra com o sistema AURALIS
    """
    
    def __init__(self):
        self.memoria = MemoriaContextualLRU()
        self.ativo = True
        
    def processar_interacao(self, pergunta: str, resposta: str, 
                          reunioes_encontradas: Optional[List[str]] = None,
                          confidence_score: Optional[float] = None):
        """
        Processa e armazena uma interação completa
        """
        metadados = {}
        
        if reunioes_encontradas:
            metadados['reunioes_encontradas'] = reunioes_encontradas
        
        if confidence_score is not None:
            metadados['confidence_score'] = confidence_score
        
        # Extrair possíveis temas da pergunta
        palavras_chave = [p for p in pergunta.lower().split() 
                         if len(p) > 4 and p not in ['sobre', 'quais', 'quando', 'onde', 'como']]
        if palavras_chave:
            metadados['temas'] = palavras_chave[:3]
        
        self.memoria.adicionar_interacao(pergunta, resposta, metadados)
    
    def obter_contexto(self) -> str:
        """Obtém contexto formatado para o agente"""
        return self.memoria.formatar_contexto_para_agente()
    
    def fechar_sessao(self):
        """Finaliza a sessão e limpa a memória"""
        if self.ativo:
            resumo = self.memoria.obter_resumo_sessao()
            print("\n📊 Resumo da Sessão:")
            print(f"   - ID: {resumo['sessao_id']}")
            print(f"   - Duração: {resumo['duracao']}")
            print(f"   - Total de interações: {resumo['total_interacoes']}")
            print(f"   - Taxa de acerto do cache: {resumo['estatisticas']['taxa_acerto']}")
            
            self.memoria.limpar_memoria()
            self.ativo = False


# Instância global do gerenciador (será criada quando necessário)
_gerenciador_memoria: Optional[GerenciadorMemoria] = None

def obter_gerenciador_memoria() -> GerenciadorMemoria:
    """Obtém ou cria a instância global do gerenciador de memória"""
    global _gerenciador_memoria
    if _gerenciador_memoria is None:
        _gerenciador_memoria = GerenciadorMemoria()
    return _gerenciador_memoria


# Testes da memória
if __name__ == "__main__":
    print("🧪 Testando sistema de memória contextual\n")
    
    # Criar gerenciador
    gerenciador = GerenciadorMemoria()
    
    # Simular interações
    interacoes = [
        ("Qual foi a última reunião sobre vendas?", 
         "A última reunião sobre vendas foi em 04/02/2024...", 
         ["reuniao_04_02_2024.txt"]),
        
        ("Quem participou dessa reunião?", 
         "Participaram João Silva, Maria Santos e Pedro Costa...", 
         ["reuniao_04_02_2024.txt"]),
        
        ("Quais foram as decisões sobre o novo produto?", 
         "As principais decisões foram: lançamento em março, preço inicial de R$ 99...", 
         ["reuniao_04_02_2024.txt"]),
        
        ("Existe alguma reunião sobre marketing?", 
         "Encontrei 2 reuniões sobre marketing...", 
         ["reuniao_15_01_2024.txt", "reuniao_20_01_2024.txt"])
    ]
    
    # Processar interações
    for pergunta, resposta, reunioes in interacoes:
        print(f"\n🔄 Processando: {pergunta[:50]}...")
        gerenciador.processar_interacao(pergunta, resposta, reunioes, confidence_score=0.95)
        time.sleep(0.1)
    
    # Mostrar contexto
    print("\n📋 Contexto atual:")
    print(gerenciador.obter_contexto())
    
    # Buscar por tema
    print("\n🔍 Buscando interações sobre 'vendas':")
    resultados = gerenciador.memoria.buscar_por_tema("vendas", limite=3)
    for r in resultados:
        print(f"   - {r['pergunta'][:60]}...")
    
    # Estatísticas
    print("\n📊 Estatísticas:")
    stats = gerenciador.memoria.obter_estatisticas()
    for k, v in stats.items():
        print(f"   - {k}: {v}")
    
    # Fechar sessão
    print("\n")
    gerenciador.fechar_sessao()