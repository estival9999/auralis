"""
Configurações centralizadas do sistema AURALIS
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Diretórios base
BASE_DIR = Path(__file__).resolve().parent.parent
WINDOWS_DIR = BASE_DIR / "windows"
SRC_DIR = BASE_DIR / "src"
BACKEND_DIR = BASE_DIR / "backend"
SHARED_DIR = BASE_DIR / "shared"

# Diretórios de dados
UPDATE_CONHECIMENTO_DIR = BASE_DIR / "update_conhecimento"
UPDATE_HISTORICO_DIR = BASE_DIR / "update_historico"
AURALIS_MEMORIA_DIR = BASE_DIR / "auralis_memoria"

# Criar diretórios se não existirem
for directory in [UPDATE_CONHECIMENTO_DIR, UPDATE_HISTORICO_DIR, AURALIS_MEMORIA_DIR]:
    directory.mkdir(exist_ok=True)

# Configurações Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")
SUPABASE_ACCESS_TOKEN = os.getenv("SUPABASE_ACCESS_TOKEN")

# Configurações OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4-turbo")

# Configurações da Aplicação
APP_NAME = os.getenv("APP_NAME", "Sistema de Reuniões AURALIS")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"

# Configurações Backend
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")
BACKEND_TIMEOUT = int(os.getenv("BACKEND_TIMEOUT", "30"))

# Configurações de Áudio
AUDIO_FORMAT = os.getenv("AUDIO_FORMAT", "wav")
AUDIO_SAMPLE_RATE = int(os.getenv("AUDIO_SAMPLE_RATE", "44100"))
AUDIO_CHUNK_SIZE = int(os.getenv("AUDIO_CHUNK_SIZE", "1024"))
MAX_RECORDING_DURATION = int(os.getenv("MAX_RECORDING_DURATION", "3600"))

# Configurações da Interface
WINDOW_WIDTH = 320
WINDOW_HEIGHT = 240

# Configurações de Logging
LOG_LEVEL = "DEBUG" if DEBUG_MODE else "INFO"
LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}:{function}:{line} - {message}"

# Usuários de teste (temporário para desenvolvimento)
TEST_USERS = {
    "admin": {
        "password": "admin123",
        "nome_completo": "Administrador",
        "cargo": "Administrador",
        "area": "TI"
    },
    "joao.silva": {
        "password": "admin123",
        "nome_completo": "João Silva",
        "cargo": "Gerente de Projetos",
        "area": "Desenvolvimento"
    },
    "maria.santos": {
        "password": "admin123",
        "nome_completo": "Maria Santos",
        "cargo": "Analista de Negócios",
        "area": "Comercial"
    },
    "pedro.costa": {
        "password": "admin123",
        "nome_completo": "Pedro Costa",
        "cargo": "Desenvolvedor Senior",
        "area": "Desenvolvimento"
    }
}