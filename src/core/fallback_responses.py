"""
Respostas de fallback para o Auralis quando não há conexão com APIs
"""
import random
from datetime import datetime

class FallbackResponses:
    """Gera respostas simples quando APIs não estão disponíveis"""
    
    @staticmethod
    def get_simple_response(pergunta: str) -> str:
        """
        Gera resposta simples baseada em palavras-chave
        
        Args:
            pergunta: Pergunta do usuário
            
        Returns:
            Resposta simples
        """
        pergunta_lower = pergunta.lower()
        
        # Saudações
        if any(word in pergunta_lower for word in ['oi', 'olá', 'hello', 'bom dia', 'boa tarde', 'boa noite']):
            return random.choice([
                "Olá! Como posso ajudar você hoje?",
                "Oi! Estou aqui para ajudar com suas consultas sobre reuniões.",
                "Olá! Sou o Auralis, seu assistente de reuniões. Como posso auxiliar?"
            ])
        
        # Sobre o sistema
        if any(word in pergunta_lower for word in ['auralis', 'sistema', 'você', 'quem']):
            return """Sou o Auralis, seu assistente inteligente para gestão de reuniões.
            
Posso ajudar você a:
• Buscar informações em reuniões anteriores
• Gerar ideias e sugestões
• Consultar a base de conhecimento
• Analisar dinâmica de equipe

No momento estou funcionando em modo offline, mas ainda posso ajudar com consultas básicas!"""
        
        # Reuniões
        if any(word in pergunta_lower for word in ['reunião', 'reuniões', 'meeting']):
            return """Para consultar reuniões, você pode:

• Acessar o Histórico no menu principal
• Usar a busca para encontrar reuniões específicas
• Filtrar por período ou participantes

No momento, a conexão com o banco está com problemas, mas você pode gravar novas reuniões normalmente."""
        
        # Gravação
        if any(word in pergunta_lower for word in ['gravar', 'gravação', 'áudio']):
            return """Para gravar uma reunião:

1. Vá ao Menu Principal
2. Clique em "🔴 Iniciar"
3. Preencha o título da reunião
4. Confirme para começar a gravação

A gravação será salva automaticamente quando você finalizar."""
        
        # Problemas técnicos
        if any(word in pergunta_lower for word in ['erro', 'problema', 'não funciona', 'bug']):
            return """Se você está enfrentando problemas:

• Verifique se as credenciais estão configuradas no arquivo .env
• Tente reiniciar o sistema
• Consulte os logs em logs/auralis.log para mais detalhes

No momento, algumas funcionalidades podem estar limitadas devido a problemas de conexão."""
        
        # Ajuda
        if any(word in pergunta_lower for word in ['ajuda', 'help', 'como', 'tutorial']):
            return """Como usar o Auralis:

🔴 **Gravar Reunião:**
Menu Principal → Iniciar → Preencher título → Gravar

📜 **Ver Histórico:**
Menu Principal → Histórico → Buscar/Filtrar

🤖 **Chat Auralis:**
Menu Principal → Auralis → Fazer perguntas

🎤 **Pergunta por voz:**
No chat, clique no ícone do microfone"""
        
        # Default
        return f"""Desculpe, no momento não consigo processar sua pergunta completamente devido a problemas de conexão.

Você perguntou: "{pergunta}"

Enquanto isso, você pode:
• Gravar novas reuniões
• Consultar o histórico local
• Verificar as configurações do sistema

Tente novamente em alguns minutos ou verifique as configurações de rede."""

    @staticmethod
    def get_error_response(error_type: str = "general") -> str:
        """
        Retorna resposta de erro apropriada
        
        Args:
            error_type: Tipo do erro
            
        Returns:
            Mensagem de erro amigável
        """
        if error_type == "openai":
            return """Não foi possível conectar com o serviço de IA no momento.

Isso pode ser devido a:
• Chave API do OpenAI inválida ou expirada
• Problemas de conectividade
• Limite de uso excedido

Verifique as configurações no arquivo .env e tente novamente."""
        
        elif error_type == "supabase":
            return """Não foi possível conectar com o banco de dados.

Isso pode ser devido a:
• Credenciais Supabase inválidas
• Problemas de conectividade
• Configuração incorreta

O sistema ainda funciona em modo offline para novas gravações."""
        
        else:
            return f"""Ocorreu um erro inesperado.

Detalhes técnicos: {error_type}

Você pode tentar:
• Reiniciar o sistema
• Verificar as configurações
• Consultar os logs para mais informações"""