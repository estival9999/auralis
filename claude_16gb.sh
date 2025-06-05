#!/bin/bash
# Script para executar Claude Code com 16GB de memória

echo "🚀 Iniciando Claude Code com 16GB de memória..."
export NODE_OPTIONS="--max-old-space-size=16384"
claude

# Alternativa se preferir especificar diretamente:
# node --max-old-space-size=16384 $(which claude)