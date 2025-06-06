"""
Sistema de Clarificação de Intenção para Perguntas Ambíguas
Detecta perguntas vagas e oferece opções específicas ao usuário
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class TipoPergunta(Enum):
    """Tipos de pergunta identificados pelo sistema"""
    INFORMACAO_SIMPLES = "informacao_simples"
    ANALISE_COMPLEXA = "analise_complexa"
    ACAO_ESPECIFICA = "acao_especifica"
    AJUDA_GENERICA = "ajuda_generica"
    AMBIGUA = "ambigua"
    SAUDACAO = "saudacao"


@dataclass
class ClassificacaoPergunta:
    """Resultado da classificação de uma pergunta"""
    tipo: TipoPergunta
    confianca: float
    palavras_chave: List[str]
    precisa_clarificacao: bool
    sugestoes_clarificacao: Optional[List[str]] = None


class ClarificadorIntencao:
    """
    Sistema para detectar e clarificar perguntas ambíguas
    """
    
    def __init__(self):
        # Padrões para identificar tipos de pergunta
        self.padroes_pergunta = {
            TipoPergunta.INFORMACAO_SIMPLES: {
                "palavras": ["o que é", "qual", "quando", "quem", "onde", "quanto"],
                "regex": r"(o que é|qual|quando|quem|onde|quanto)\s+",
                "peso": 0.8
            },
            TipoPergunta.ANALISE_COMPLEXA: {
                "palavras": ["compare", "analise", "avalie", "projete", "identifique", "relacione"],
                "regex": r"(compar|analis|avali|projet|identifi|relacion)",
                "peso": 0.9
            },
            TipoPergunta.ACAO_ESPECIFICA: {
                "palavras": ["liste", "mostre", "encontre", "busque", "extraia", "resuma"],
                "regex": r"(list|mostr|encontr|busc|extra|resum)",
                "peso": 0.85
            },
            TipoPergunta.SAUDACAO: {
                "palavras": ["oi", "olá", "bom dia", "boa tarde", "boa noite", "opa"],
                "regex": r"^(oi|olá|bom dia|boa tarde|boa noite|opa)",
                "peso": 0.95
            }
        }
        
        # Perguntas genéricas que precisam clarificação
        self.perguntas_ambiguas = {
            "ajuda": {
                "variacoes": ["me ajude", "ajuda", "preciso de ajuda", "help"],
                "sugestoes": [
                    "📊 Ver resumo das últimas reuniões",
                    "🔍 Buscar informação específica",
                    "📈 Consultar indicadores financeiros",
                    "👥 Informações sobre participantes",
                    "📅 Verificar agenda e datas"
                ]
            },
            "informacoes": {
                "variacoes": ["preciso de informações", "informações", "info", "dados"],
                "sugestoes": [
                    "📋 Informações sobre reuniões específicas",
                    "💰 Dados financeiros e indicadores",
                    "📖 Conceitos e definições (base de conhecimento)",
                    "🎯 Decisões e ações definidas",
                    "📊 Relatórios e análises"
                ]
            },
            "status": {
                "variacoes": ["status", "status atual", "situação", "como está"],
                "sugestoes": [
                    "📅 Status das últimas reuniões",
                    "💼 Status de projetos em andamento",
                    "👤 Status de responsabilidades da equipe",
                    "📈 Status de indicadores e metas",
                    "✅ Status de ações e pendências"
                ]
            },
            "resumo": {
                "variacoes": ["resumo", "resumo geral", "visão geral", "overview"],
                "sugestoes": [
                    "📄 Resumo da última reunião",
                    "📊 Resumo do último período (semana/mês)",
                    "🎯 Resumo de decisões importantes",
                    "📈 Resumo de indicadores chave",
                    "👥 Resumo por área/departamento"
                ]
            },
            "novidades": {
                "variacoes": ["novidades", "o que há de novo", "news", "atualizações"],
                "sugestoes": [
                    "🆕 Últimas reuniões realizadas",
                    "📢 Novas decisões e diretrizes",
                    "👤 Mudanças na equipe",
                    "📊 Novos indicadores ou metas",
                    "🔄 Atualizações de projetos"
                ]
            }
        }
        
        # Mapeamento de clarificações para respostas diretas
        self.respostas_diretas = {
            "oi": "Olá! Como posso ajudar você hoje?",
            "olá": "Olá! Em que posso ser útil?",
            "bom dia": "Bom dia! Como posso auxiliar?",
            "boa tarde": "Boa tarde! Em que posso ajudar?",
            "boa noite": "Boa noite! Como posso ser útil?"
        }
    
    def classificar_pergunta(self, pergunta: str) -> ClassificacaoPergunta:
        """
        Classifica uma pergunta e determina se precisa clarificação
        """
        pergunta_lower = pergunta.lower().strip()
        
        # Verificar se é uma saudação simples
        if pergunta_lower in self.respostas_diretas:
            return ClassificacaoPergunta(
                tipo=TipoPergunta.SAUDACAO,
                confianca=1.0,
                palavras_chave=[pergunta_lower],
                precisa_clarificacao=False
            )
        
        # Verificar se é uma pergunta ambígua conhecida
        for categoria, info in self.perguntas_ambiguas.items():
            for variacao in info["variacoes"]:
                if variacao in pergunta_lower or pergunta_lower in variacao:
                    return ClassificacaoPergunta(
                        tipo=TipoPergunta.AMBIGUA,
                        confianca=0.9,
                        palavras_chave=[variacao],
                        precisa_clarificacao=True,
                        sugestoes_clarificacao=info["sugestoes"]
                    )
        
        # Tentar classificar por padrões
        melhor_tipo = TipoPergunta.AJUDA_GENERICA
        melhor_confianca = 0.0
        palavras_encontradas = []
        
        for tipo, padrao in self.padroes_pergunta.items():
            # Verificar palavras-chave
            palavras_match = [p for p in padrao["palavras"] if p in pergunta_lower]
            
            # Verificar regex
            regex_match = re.search(padrao["regex"], pergunta_lower, re.IGNORECASE)
            
            # Calcular confiança
            confianca = 0.0
            if palavras_match:
                confianca += padrao["peso"] * len(palavras_match) / len(padrao["palavras"])
            if regex_match:
                confianca += padrao["peso"] * 0.5
            
            if confianca > melhor_confianca:
                melhor_tipo = tipo
                melhor_confianca = confianca
                palavras_encontradas = palavras_match
        
        # Determinar se precisa clarificação
        precisa_clarificacao = (
            melhor_confianca < 0.5 or 
            len(pergunta_lower.split()) <= 2 or
            melhor_tipo == TipoPergunta.AJUDA_GENERICA
        )
        
        return ClassificacaoPergunta(
            tipo=melhor_tipo,
            confianca=melhor_confianca,
            palavras_chave=palavras_encontradas,
            precisa_clarificacao=precisa_clarificacao
        )
    
    def gerar_resposta_clarificacao(self, classificacao: ClassificacaoPergunta) -> str:
        """
        Gera uma resposta solicitando clarificação
        """
        if classificacao.tipo == TipoPergunta.SAUDACAO:
            return "Olá! Como posso ajudar você hoje? Você pode me perguntar sobre reuniões, indicadores financeiros ou conceitos."
        
        if classificacao.sugestoes_clarificacao:
            resposta = "Entendi que você precisa de ajuda. Por favor, seja mais específico. Você gostaria de:\n\n"
            for sugestao in classificacao.sugestoes_clarificacao:
                resposta += f"{sugestao}\n"
            resposta += "\nEscolha uma opção ou faça uma pergunta específica."
            return resposta
        
        # Resposta genérica para clarificação
        return """Sua pergunta está um pouco genérica. Para ajudar melhor, preciso saber o que você procura:

• **Informações de reuniões** - datas, participantes, decisões
• **Conceitos financeiros** - definições e explicações
• **Análises e relatórios** - comparações e tendências
• **Status e acompanhamento** - projetos e responsáveis

Por favor, reformule sua pergunta com mais detalhes."""
    
    def processar_pergunta(self, pergunta: str) -> Tuple[bool, Optional[str]]:
        """
        Processa uma pergunta e retorna se precisa clarificação e a mensagem
        
        Returns:
            (precisa_clarificacao, mensagem_clarificacao)
        """
        # Classificar a pergunta
        classificacao = self.classificar_pergunta(pergunta)
        
        # Se precisa clarificação, gerar resposta
        if classificacao.precisa_clarificacao:
            mensagem = self.gerar_resposta_clarificacao(classificacao)
            return True, mensagem
        
        # Não precisa clarificação
        return False, None


# Função auxiliar para integração fácil
def verificar_clarificacao(pergunta: str) -> Tuple[bool, Optional[str]]:
    """
    Função simples para verificar se uma pergunta precisa clarificação
    """
    clarificador = ClarificadorIntencao()
    return clarificador.processar_pergunta(pergunta)


if __name__ == "__main__":
    # Testes do sistema
    clarificador = ClarificadorIntencao()
    
    perguntas_teste = [
        "Me ajude",
        "O que você pode fazer?",
        "Status",
        "Informações",
        "Qual foi o tema da última reunião?",
        "Compare as duas últimas reuniões",
        "asdfghjkl",
        "???",
        "",
        "Oi",
        "Resumo geral",
        "Novidades?"
    ]
    
    print("=== TESTE DO CLARIFICADOR DE INTENÇÃO ===\n")
    
    for pergunta in perguntas_teste:
        print(f"Pergunta: '{pergunta}'")
        precisa, mensagem = clarificador.processar_pergunta(pergunta)
        
        if precisa:
            print("✓ Precisa clarificação:")
            print(f"{mensagem}\n")
        else:
            print("✗ Pergunta clara, pode processar normalmente\n")
        
        print("-" * 60 + "\n")