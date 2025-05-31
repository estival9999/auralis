# 🎯 AURALIS - Sistema Inteligente de Reuniões e Gestão do Conhecimento

Sistema integrado de gravação, transcrição e análise inteligente de reuniões com assistente IA para consultas e brainstorming.

## 🚀 Início Rápido

### Pré-requisitos
- Python 3.8+
- Node.js (para integração MCP)
- Microfone para gravação
- Credenciais Supabase e OpenAI

### Instalação

1. Clone o repositório e instale dependências:
```bash
pip install -r requirements.txt
```

2. Configure as variáveis de ambiente:
- Copie `.env.example` para `.env` (se existir)
- Ou configure manualmente as credenciais no `.env`

3. Execute o sistema:
```bash
python main.py
```

## 📁 Estrutura do Projeto

```
auralis_new/
├── main.py                    # Aplicação principal
├── windows/                   # Interfaces gráficas de referência (PyQt6)
├── src/                      # Código fonte principal
│   ├── core/                 # Módulos centrais
│   │   ├── auth_manager.py   # Autenticação
│   │   └── style_manager.py  # Gerenciamento de estilos
│   └── database/             # Integração com banco
│       └── supabase_client.py
├── backend/                  # Backend com agentes IA
│   └── agents/              # Agentes especializados
│       ├── agente_orquestrador.py
│       ├── agente_brainstorm.py
│       └── agente_consulta_inteligente.py
├── shared/                   # Código compartilhado
│   └── config.py            # Configurações centralizadas
├── supabase-mcp-main/       # Servidor MCP Supabase
└── scripts/                 # Scripts utilitários
    ├── input_base_conhecimento.py
    └── input_historico_reunioes.py
```

## 🖥️ Interface Gráfica

O sistema possui 7 janelas principais:

1. **Login** - Autenticação de usuários
2. **Menu Principal** - Hub central de navegação
3. **Histórico** - Visualização de reuniões anteriores
4. **Pré-Gravação** - Configuração antes de gravar
5. **Gravação** - Captura de áudio da reunião
6. **Chat Auralis** - Interação com assistente IA
7. **Escuta Auralis** - Gravação de perguntas por voz

## 🤖 Agentes IA

### Agente Orquestrador
- Interpreta perguntas do usuário
- Roteia para agentes especializados
- Consolida respostas múltiplas

### Agente Brainstorm
- Gera ideias criativas
- Analisa contexto de reuniões
- Propõe soluções inovadoras

### Agente Consulta Inteligente
- Busca semântica avançada
- Correção inteligente de nomes
- Análise de equipe e tendências

## 💾 Banco de Dados

### Tabelas Principais
- `login_user` - Usuários do sistema
- `base_conhecimento` - Documentos e políticas
- `historico_reunioes` - Transcrições e análises

### Integração MCP
O sistema usa Model Context Protocol para comunicação com Supabase.
Configuração em `mcp_config.json`.

## 📥 Importação de Dados

### Base de Conhecimento
```bash
python input_base_conhecimento.py
```
Importa arquivos TXT de `update_conhecimento/`

### Histórico de Reuniões
```bash
python input_historico_reunioes.py
```
Importa transcrições de `update_historico/`

## 🔧 Configuração

### Variáveis de Ambiente (.env)
```env
# Supabase
SUPABASE_URL=sua_url
SUPABASE_ANON_KEY=sua_chave
SUPABASE_ACCESS_TOKEN=seu_token

# OpenAI
OPENAI_API_KEY=sua_api_key
OPENAI_MODEL=gpt-4-turbo

# Aplicação
APP_NAME=Sistema de Reuniões AURALIS
DEBUG_MODE=True
```

## 🧪 Usuários de Teste

Para desenvolvimento, use:
- **admin** / admin123
- **joao.silva** / admin123
- **maria.santos** / admin123
- **pedro.costa** / admin123

## 📝 Licença

Propriedade de AURALIS. Todos os direitos reservados.

## 🤝 Suporte

Para suporte ou dúvidas sobre o sistema, entre em contato com a equipe de desenvolvimento.