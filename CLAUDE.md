# 🎯 AURALIS - Sistema Inteligente de Reuniões e Gestão do Conhecimento

## 📋 Visão Geral do Projeto

Sistema integrado de gravação, transcrição e análise inteligente de reuniões com assistente IA para consultas e brainstorming, desenvolvido em Python com Supabase e OpenAI.

---

## 🖥️ INTERFACE GRÁFICA

### Especificações Técnicas
- **Dimensões:** 320x240 pixels
- **Framework:** Python (Tkinter/PyQt/Kivy)
- **Navegação:** Sistema de janelas sequenciais

### 📱 Estrutura de Janelas

#### **Janela 0 - Login**
**Campos:**
- Campo de usuário
- Campo de senha
- Botão confirmar (redireciona para Janela 1 após autenticação)

**Integração:**
- Validação via Supabase (tabela `login_user`)
- Sem funcionalidade de cadastro (gerenciado externamente)

#### **Janela 1 - Menu Principal**
**Opções:**
- **Histórico:** Acessa histórico de reuniões (Janela 2)
- **Iniciar:** Inicia gravação de reunião (Janela 3)
- **Auralis:** Interação com assistente IA (Janela 5)

#### **Janela 2 - Histórico de Reuniões**
**Funcionalidades:**
- Lista de reuniões com formato: `[Título] - [DD/MM/AAAA HH:MM] - [Responsável]`
- Exemplo: `Alinhamento de cadastro - 25/03/2025 10:19 - Mateus Estival`
- Ao clicar: exibe transcrição completa estruturada

**Formato da Transcrição:**
```
📋 **RESUMO EXECUTIVO:** [Síntese principal]
🎯 **DECISÕES TOMADAS:** • [Decisão] - Responsável: [Nome] - Prazo: [Data]
✅ **AÇÕES DEFINIDAS:** • [Ação] - [Responsável] - [Prazo]
⚠️ **PENDÊNCIAS/BLOQUEIOS:** • [Pendência identificada]
📊 **INSIGHTS DA EQUIPE:** • [Observação sobre dinâmica]
📄 **TRANSCRIÇÃO COMPLETA:** [Conteúdo integral]
```

**Integração:**
- Dados da tabela `historico_reunioes` (Supabase)
- Reconstituição de chunks/embeddings para visualização completa
- Botão voltar para Janela 1

#### **Janela 3 - Pré-Gravação**
**Campos Automáticos:**
- Usuário (do login)
- Área (do login)
- Data/Hora (formato: DD/MM/AA - HH:MM)

**Campo Manual:**
- Título da reunião

**Ações:**
- Confirmar → Janela 4
- Cancelar → Janela 1

#### **Janela 4 - Gravação em Andamento**
**Elementos:**
- Timer de duração
- Botão Pausar → Janela de pausa (apenas botão retomar)
- Botão Finalizar → Confirmação → Transcrever e salvar
- Botão Cancelar → Confirmação → Janela 1

**Processamento:**
- Transcrição via OpenAI Whisper
- Salvamento em `historico_reunioes`

#### **Janela 5 - Assistente IA Auralis**
**Interface:**
- Botão Perguntar → Janela 6 (gravação de áudio)
- Chat visual (estilo conversacional)
- Animação durante processamento
- Botão Voltar → Janela 1 (limpa memória)

**Gestão de Memória:**
- Armazenamento local em `auralis_memoria/`
- Contexto mantido durante sessão
- Limpeza ao sair da janela

#### **Janela 6 - Gravação de Pergunta**
- Interface de gravação de áudio
- Indicador visual de captura
- Processamento e retorno para Janela 5

### 🎙️ Especificações de Áudio
- **Formato:** WAV
- **Taxa de amostragem:** 44.1 kHz
- **Chunk size:** 1024
- **Limite OpenAI:** 25MB por arquivo
- **Estratégia para arquivos grandes:** Segmentação automática

---

## 🤖 ARQUITETURA DE AGENTES IA

### 🎭 Agente Orquestrador
**Arquivo:** `agente_orquestrador.py`
**Função:** 
- Interpreta perguntas do usuário
- Roteia para agentes especializados
- Consolida respostas múltiplas
- Gerencia contexto conversacional

### 🧠 Agentes Especializados

#### 1. Agente Brainstorm
**Arquivo:** `agente_brainstorm.py`
**Capacidades:**
- Geração de ideias e soluções
- Análise baseada em reuniões específicas
- Cruzamento de informações entre reuniões
- Propostas criativas contextualizadas

#### 2. Agente Consulta Inteligente
**Arquivo:** `agente_consulta_inteligente.py`
**Funcionalidades:**
- Busca semântica em `base_conhecimento`
- Análise de `historico_reunioes`
- Extração de informações específicas
- Correção inteligente de nomes (ex: "Mateus Estivau" → "Matheus Estival")

### 🔧 Características Técnicas dos Agentes
- **Busca semântica avançada** com embeddings
- **Tolerância a erros** de transcrição
- **Contexto conversacional** persistente
- **Análise profunda** de transcrições
- **Identificação automática** de decisões, ações e responsáveis
- **Extração de prazos** e compromissos
- **Análise de dinâmica** de equipe
- **Geração de relatórios** executivos

### 🔄 Comunicação Inter-Agentes
- Protocolo seguro e escalável
- Preparado para arquitetura distribuída
- API RESTful/gRPC para futuro deployment
- Sistema de mensageria assíncrona

---

## 💾 BANCO DE DADOS SUPABASE

### 🔌 Integração via MCP (Model Context Protocol)
- Consultas e manipulação de dados
- Análise de esquemas
- Execução de SQL customizado
- Upload/download de arquivos

### 📊 Estrutura de Tabelas

#### 1. `login_user`
```sql
- id (UUID, PK)
- username (TEXT, UNIQUE)
- password (TEXT, hashed)
- nome_completo (TEXT)
- cpf (TEXT)
- cargo (TEXT)
- area (TEXT)
- created_at (TIMESTAMP)
- last_login (TIMESTAMP)
```

#### 2. `base_conhecimento`
```sql
- id (UUID, PK)
- titulo_arquivo (TEXT)
- conteudo (TEXT)
- embedding (VECTOR)
- categoria (TEXT)
- tags (TEXT[])
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
```

#### 3. `historico_reunioes`
```sql
- id (UUID, PK)
- titulo (TEXT)
- data_reuniao (TIMESTAMP)
- responsavel (TEXT)
- area (TEXT)
- participantes (TEXT[])
- duracao (INTEGER)
- transcricao_completa (TEXT)
- resumo_executivo (TEXT)
- decisoes (JSONB)
- acoes (JSONB)
- pendencias (JSONB)
- insights (JSONB)
- embedding_chunks (JSONB[])
- created_at (TIMESTAMP)
```

### 📥 Scripts de Importação
- `input_base_conhecimento.py`: Importa TXTs da pasta `update_conhecimento/`
- `input_historico_reunioes.py`: Importa TXTs da pasta `update_historico/`

---

## 🏗️ ARQUITETURA DO SISTEMA

### 🌐 Arquitetura Distribuída
- **Frontend:** Interface gráfica (futuro: cliente remoto)
- **Backend:** API de agentes IA (futuro: servidor centralizado)
- **Comunicação:** REST API / WebSockets / gRPC
- **Transcrição:** Processamento local no frontend

### 📁 Estrutura de Arquivos
```
auralis/
├── frontend/
│   ├── windows/          # Interfaces gráficas
│   ├── audio/           # Processamento de áudio
│   └── api_client.py    # Comunicação com backend
│
├── backend/
│   ├── agents/          # Agentes IA
│   ├── database/        # Integração Supabase
│   └── api_server.py    # Servidor API
│
├── shared/
│   ├── config.py        # Configurações
│   └── utils.py         # Utilitários
│
└── tests/               # Testes automatizados
```

### 🔒 Segurança e Performance
- Autenticação JWT
- Rate limiting
- Cache inteligente
- Fallback gracioso
- Logs detalhados
- Monitoramento de performance

---

## 🧠 INTELIGÊNCIA DO SISTEMA

### Capacidades Cognitivas
- **Compreensão contextual:** Entende referências implícitas
- **Precisão factual:** Baseia-se apenas em dados reais
- **Resposta adaptativa:** Ajusta formato conforme preferência
- **Memória associativa:** Conecta informações relacionadas

### Cenários de Uso

#### 📊 Acompanhamento de Projetos
```
Usuário: "Como está o projeto Alpha?"
Sistema: [Busca reuniões] → [Extrai status] → [Consolida progresso]
```

#### 📋 Consulta de Políticas
```
Usuário: "Qual o procedimento de home office?"
Sistema: [Busca base_conhecimento] → [Retorna procedimento]
```

#### 🔍 Análise de Decisões
```
Usuário: "O que decidimos sobre orçamento nas últimas 3 reuniões?"
Sistema: [Filtra reuniões] → [Extrai decisões] → [Compara evolução]
```

---

## ⚙️ CONFIGURAÇÕES DO AMBIENTE

### 🔑 Credenciais Supabase
```env
MCP_TOKEN=sbp_faebbe0cceb05fa50d714b8ba3108e033b462320
```

### 🤖 Configurações OpenAI
```env
OPENAI_API_KEY=sk-proj-ER9S7sD-C-StVBC_Z_HKk7jq4NBB...
OPENAI_MODEL=gpt-4-turbo
```

### 🖥️ Configurações da Aplicação
```env
BACKEND_BASE_URL=http://localhost:8000
BACKEND_TIMEOUT=30
APP_NAME=Sistema de Reuniões
APP_VERSION=1.0.0
DEBUG_MODE=True
```

### 🎙️ Configurações de Áudio
```env
AUDIO_FORMAT=wav
AUDIO_SAMPLE_RATE=44100
AUDIO_CHUNK_SIZE=1024
MAX_RECORDING_DURATION=3600  # 1 hora
```

---

## 📚 DIRETRIZES DE DESENVOLVIMENTO

### Princípios
1. **Modularidade:** Código bem separado por responsabilidade
2. **Documentação:** Comentários em português
3. **Escalabilidade:** Preparado para crescimento
4. **Resiliência:** Tratamento robusto de erros
5. **Performance:** Otimização contínua

### Boas Práticas
- Testes automatizados abrangentes
- Logging estruturado para debugging
- Limpeza automática de arquivos temporários
- Validação de entrada em todas as camadas
- Padrões de código consistentes

### Segurança
- Sanitização de inputs
- Criptografia de dados sensíveis
- Princípio do menor privilégio
- Auditoria de ações
- Proteção contra injeção SQL

---

## 🚀 RESULTADO ESPERADO

Um sistema inteligente que funciona como um **assistente corporativo especializado**, capaz de:
- Gravar e transcrever reuniões automaticamente
- Responder perguntas complexas sobre o histórico
- Gerar insights e propostas baseadas em dados
- Manter contexto conversacional sofisticado        
- Escalar para múltiplos usuários simultâneos

**Disponível 24/7, preciso, rápido e adaptativo!** 🎉