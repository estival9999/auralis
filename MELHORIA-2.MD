# MELHORIA-2: Solicitar Contexto em Perguntas sobre Reuniões Específicas

## 📋 Resumo Executivo
Este documento detalha como melhorar a interação do sistema quando usuários perguntam genericamente sobre reuniões específicas, solicitando mais contexto antes de fornecer uma resposta completa.

## 🔴 PROBLEMA: Respostas Genéricas sobre Reuniões Específicas

### Exemplos do Problema:

**Situação 1 - Pergunta sobre reunião sem especificar o que quer saber:**
```
USUÁRIO: "Me fale sobre a reunião de ontem"
SISTEMA ATUAL: [Despeja todas as informações disponíveis sobre a reunião]
SISTEMA IDEAL: "Encontrei a reunião de ontem. O que você gostaria de saber especificamente?
- Um resumo geral
- Os principais pontos discutidos
- As decisões tomadas
- Os participantes
- Os próximos passos definidos"
```

**Situação 2 - Pergunta vaga sobre reunião específica:**
```
USUÁRIO: "O que teve na reunião de vendas?"
SISTEMA ATUAL: [Retorna todo o conteúdo disponível]
SISTEMA IDEAL: "Sobre a reunião de vendas, você gostaria de saber:
- Os resultados apresentados?
- As metas discutidas?
- Os problemas identificados?
- O plano de ação definido?"
```

**Situação 3 - Referência a reunião por título:**
```
USUÁRIO: "Me conte sobre a reunião RAPADURA"
SISTEMA ATUAL: [Retorna todos os chunks relacionados]
SISTEMA IDEAL: "Encontrei a reunião RAPADURA. Como posso ajudá-lo melhor?
- Precisa de um resumo executivo?
- Quer saber sobre algum tópico específico?
- Interessado nas decisões e ações?
- Ou prefere a transcrição completa?"
```

### Por que isso é um problema?
1. **Sobrecarga de Informação**: O usuário recebe muito mais informação do que precisa
2. **Ineficiência**: Gasta tokens e tempo processando informações desnecessárias
3. **Experiência Ruim**: O usuário precisa filtrar mentalmente o que é relevante
4. **Falta de Personalização**: Não atende à necessidade específica do usuário

## 🔍 Código Atual Causando o Problema:

```python
# Em agente_busca_melhorado.py, método processar_pergunta()
# O sistema não verifica se a pergunta é sobre uma reunião específica mas genérica

def processar_pergunta(self, pergunta: str) -> str:
    # ... código anterior ...
    
    # VAI DIRETO BUSCAR CHUNKS SEM PERGUNTAR O QUE O USUÁRIO QUER
    chunks_relevantes = self.buscar_chunks_relevantes(pergunta, num_resultados=5)
    
    # E ENTÃO GERA RESPOSTA COM TUDO QUE ENCONTROU
    resposta = self._gerar_resposta(pergunta, contexto, contexto_memoria)
```

## ✅ Solução Conservadora Proposta:

### 1. Adicionar Detecção de Perguntas sobre Reuniões Específicas:

```python
def _e_pergunta_sobre_reuniao_especifica(self, pergunta: str) -> tuple[bool, str]:
    """
    Detecta se a pergunta é sobre uma reunião específica mas sem detalhar o que quer saber
    Retorna: (é_sobre_reunião, nome_possível_reunião)
    """
    pergunta_lower = pergunta.lower()
    
    # Padrões que indicam pergunta sobre reunião específica
    padroes_reuniao = [
        r'me (?:fale|conte|diga) sobre a reuni[ãa]o (?:de |do |da )?(.+)',
        r'o que (?:teve|houve|aconteceu) na reuni[ãa]o (?:de |do |da )?(.+)',
        r'(?:sobre|qual foi) a reuni[ãa]o (?:de |do |da )?(.+)',
        r'reuni[ãa]o (?:de |do |da )?(.+?)(?:\?|$)',
        r'me (?:fale|conte) (?:sobre|da) (.+)' # Para casos como "me fale sobre RAPADURA"
    ]
    
    # Termos que indicam aspecto específico (não precisa solicitar contexto)
    aspectos_especificos = [
        'resumo', 'principais pontos', 'decisões', 'participantes',
        'ações', 'próximos passos', 'problemas', 'riscos', 'data',
        'horário', 'duração', 'responsável', 'pauta'
    ]
    
    # Verifica se já está pedindo algo específico
    for aspecto in aspectos_especificos:
        if aspecto in pergunta_lower:
            return False, ""
    
    # Verifica padrões de reunião
    import re
    for padrao in padroes_reuniao:
        match = re.search(padrao, pergunta_lower)
        if match:
            possivel_reuniao = match.group(1) if match.groups() else ""
            # Verifica se não é muito genérico
            if possivel_reuniao and len(possivel_reuniao.split()) <= 3:
                return True, possivel_reuniao.strip()
    
    return False, ""
```

### 2. Adicionar Geração de Opções Contextuais:

```python
def _gerar_opcoes_contexto_reuniao(self, nome_reuniao: str = "") -> str:
    """Gera opções de contexto para o usuário escolher"""
    intro = f"Encontrei informações sobre "
    if nome_reuniao:
        intro += f"a reunião '{nome_reuniao}'. "
    else:
        intro += "essa reunião. "
    
    opcoes = """O que você gostaria de saber especificamente?

• **Resumo geral** - Visão executiva dos principais tópicos
• **Pontos discutidos** - Detalhamento dos assuntos abordados  
• **Decisões tomadas** - Ações e deliberações definidas
• **Participantes** - Quem esteve presente
• **Próximos passos** - Tarefas e prazos estabelecidos
• **Problemas identificados** - Questões e riscos levantados
• **Transcrição completa** - Todo o conteúdo disponível

Por favor, especifique o que mais lhe interessa."""
    
    return intro + opcoes
```

### 3. Modificar o Processamento Principal:

```python
def processar_pergunta(self, pergunta: str) -> str:
    print(f"Processando pergunta: {pergunta}")
    
    # ... código de saudações ...
    
    # NOVO: Verificar ambiguidade primeiro
    if self._e_pergunta_ambigua(pergunta):
        # ... código existente de ambiguidade ...
    
    # NOVO: Verificar se é pergunta sobre reunião específica mas genérica
    e_sobre_reuniao, nome_reuniao = self._e_pergunta_sobre_reuniao_especifica(pergunta)
    if e_sobre_reuniao:
        # Fazer busca rápida para confirmar que a reunião existe
        chunks_teste = self.buscar_chunks_relevantes(pergunta, num_resultados=1)
        
        if chunks_teste:
            # Reunião encontrada - solicitar contexto
            resposta = self._gerar_opcoes_contexto_reuniao(nome_reuniao)
            self.gerenciador_memoria.processar_interacao(pergunta, resposta)
            return resposta
        else:
            # Reunião não encontrada - continuar fluxo normal
            pass
    
    # Continua processamento normal...
```

### 4. Exemplo de Implementação Completa:

```python
# Inserir após a função _e_pergunta_generica() (por volta da linha 455)

def _e_pergunta_sobre_reuniao_especifica(self, pergunta: str) -> tuple[bool, str]:
    """Detecta perguntas genéricas sobre reuniões específicas"""
    import re
    
    pergunta_lower = pergunta.lower()
    
    # Padrões comuns
    padroes_reuniao = [
        r'me (?:fale|conte|diga) sobre a reuni[ãa]o (?:de |do |da )?(.+)',
        r'o que (?:teve|houve|aconteceu) na reuni[ãa]o (?:de |do |da )?(.+)',
        r'(?:sobre|qual foi) a reuni[ãa]o (?:de |do |da )?(.+)',
    ]
    
    # Se já pede algo específico, não precisa contexto
    if any(termo in pergunta_lower for termo in ['resumo', 'decisões', 'participantes']):
        return False, ""
    
    for padrao in padroes_reuniao:
        match = re.search(padrao, pergunta_lower)
        if match and match.groups():
            return True, match.group(1).strip()
    
    return False, ""

def _gerar_opcoes_contexto_reuniao(self, nome_reuniao: str = "") -> str:
    """Gera menu de opções para reunião"""
    return f"""Certo, sobre a reunião{f' "{nome_reuniao}"' if nome_reuniao else ''}. 
O que você gostaria de saber?

• **Resumo geral** - Principais pontos em formato executivo
• **Discussões detalhadas** - Todos os tópicos abordados
• **Decisões e ações** - O que foi definido
• **Participantes** - Quem estava presente
• **Próximos passos** - Tarefas e responsáveis

Especifique sua necessidade para uma resposta mais precisa."""
```

## 📊 Comparação Antes x Depois

| Aspecto | ANTES | DEPOIS |
|---------|-------|--------|
| Interação | Uma pergunta → Resposta completa | Uma pergunta → Solicita contexto → Resposta focada |
| Tokens usados | Alto (resposta completa sempre) | Otimizado (só o necessário) |
| Experiência | Sobrecarga de informação | Resposta personalizada |
| Eficiência | Baixa | Alta |

## 🎯 Benefícios da Solução

1. **Melhor UX**: Usuário recebe exatamente o que precisa
2. **Economia de Tokens**: Reduz custos ao evitar respostas desnecessárias
3. **Interação Natural**: Simula um assistente humano que pergunta para entender melhor
4. **Flexibilidade**: Usuário pode escolher nível de detalhe desejado

## 💡 Observações Finais

Esta solução:
- **É conservadora**: Adiciona apenas ~50 linhas de código
- **É não-invasiva**: Não quebra funcionalidades existentes
- **É extensível**: Fácil adicionar mais padrões e opções
- **É testável**: Funções isoladas facilitam testes unitários

Total de código a adicionar: ~50 linhas
Complexidade: Baixa
Risco: Mínimo