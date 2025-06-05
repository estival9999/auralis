#!/usr/bin/env python3
"""
Script de configuração e teste do sistema AURALIS
Configura banco de dados e processa arquivos de teste
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def verificar_dependencias():
    """Verifica se todas as dependências estão instaladas"""
    print("🔍 Verificando dependências...")
    
    dependencias = {
        'openai': 'OpenAI API',
        'supabase': 'Supabase client',
        'numpy': 'NumPy',
        'customtkinter': 'CustomTkinter'
    }
    
    faltando = []
    for modulo, nome in dependencias.items():
        try:
            __import__(modulo)
            print(f"   ✅ {nome} instalado")
        except ImportError:
            print(f"   ❌ {nome} não encontrado")
            faltando.append(modulo)
    
    if faltando:
        print(f"\n⚠️  Instale as dependências faltantes com:")
        print(f"   pip install {' '.join(faltando)}")
        return False
    
    return True

def verificar_env():
    """Verifica se as variáveis de ambiente estão configuradas"""
    print("\n🔐 Verificando configurações...")
    
    variaveis = [
        'OPENAI_API_KEY',
        'SUPABASE_URL',
        'SUPABASE_ANON_KEY',
        'SUPABASE_SERVICE_ROLE_KEY'
    ]
    
    configurado = True
    for var in variaveis:
        valor = os.getenv(var)
        if valor:
            print(f"   ✅ {var} configurada")
        else:
            print(f"   ❌ {var} não encontrada")
            configurado = False
    
    if not configurado:
        print("\n⚠️  Configure as variáveis no arquivo .env")
        print("\nExemplo de .env:")
        print("OPENAI_API_KEY=sua-chave-aqui")
        print("SUPABASE_URL=sua-url-aqui")
        print("SUPABASE_ANON_KEY=sua-chave-anon-aqui")
        print("SUPABASE_SERVICE_ROLE_KEY=sua-chave-service-aqui")
    
    return configurado

def criar_arquivo_teste():
    """Cria arquivo de teste se não existir"""
    pasta_teste = Path("teste_reuniao")
    pasta_teste.mkdir(exist_ok=True)
    
    arquivo_teste = pasta_teste / "reuniao_04_02_2024.txt"
    
    if not arquivo_teste.exists():
        print("\n📝 Criando arquivo de teste...")
        
        conteudo = """Reunião de Planejamento Estratégico - 04/02/2024

Participantes presentes: João Silva (Diretor de Tecnologia), Maria Santos (Gerente de Projetos), Pedro Costa (Analista Sênior), Ana Oliveira (Coordenadora de Desenvolvimento).

A reunião iniciou com João Silva apresentando os resultados do último trimestre. Foram destacados os principais pontos positivos, incluindo a conclusão do projeto Alpha com duas semanas de antecedência e economia de 15% no orçamento previsto. Maria Santos complementou informando que a equipe de desenvolvimento superou as metas de produtividade em 20%.

Durante a discussão sobre os desafios enfrentados, Pedro Costa levantou a questão da necessidade de modernização da infraestrutura de servidores. Ficou decidido que será realizado um estudo detalhado sobre migração para cloud, com prazo de entrega até o final de março. Pedro ficou responsável por liderar este estudo em conjunto com a equipe de infraestrutura.

Ana Oliveira apresentou a proposta de implementação de uma nova metodologia ágil adaptada às necessidades específicas da empresa. Após debate, foi aprovada a implementação piloto em dois projetos: Beta e Gamma. Ana será a responsável por conduzir os treinamentos necessários e acompanhar a adaptação das equipes.

Sobre o orçamento para o próximo trimestre, João Silva informou que foi aprovado um aumento de 30% no investimento em capacitação técnica. Maria Santos ficou encarregada de elaborar o plano de treinamentos, priorizando as tecnologias emergentes identificadas como estratégicas: inteligência artificial, automação de processos e segurança cibernética.

Foi discutida também a necessidade de contratação de novos profissionais. Ficou definido que serão abertas 5 vagas imediatas: 2 desenvolvedores sênior, 1 arquiteto de soluções, 1 especialista em segurança e 1 analista de dados. O processo seletivo deve iniciar na próxima semana, sob coordenação do RH com apoio técnico de Pedro Costa.

Em relação aos projetos em andamento, Maria Santos atualizou o status: Projeto Delta está em 70% de conclusão e dentro do cronograma; Projeto Epsilon enfrentou atrasos devido a mudanças de escopo, nova previsão de entrega para abril; Projeto Zeta foi concluído com sucesso e já está em produção.

Decisões importantes tomadas:
1. Aprovar orçamento de R$ 500.000 para modernização da infraestrutura
2. Implementar programa de trabalho híbrido a partir de março
3. Criar comitê de inovação liderado por Ana Oliveira
4. Estabelecer parceria com universidade local para programa de estágio
5. Investir em ferramentas de colaboração remota

Próximos passos acordados:
- João Silva: Apresentar plano estratégico consolidado até 15/02
- Maria Santos: Finalizar cronograma de projetos Q2 até 20/02
- Pedro Costa: Entregar relatório de infraestrutura até 28/02
- Ana Oliveira: Iniciar piloto de metodologia ágil em 01/03

A reunião foi encerrada às 16h com o compromisso de reunião de acompanhamento em 15 dias."""
        
        arquivo_teste.write_text(conteudo, encoding='utf-8')
        print(f"   ✅ Arquivo de teste criado: {arquivo_teste}")
    else:
        print(f"\n✅ Arquivo de teste já existe: {arquivo_teste}")

def main():
    print("=== CONFIGURAÇÃO DO SISTEMA AURALIS ===\n")
    
    # Verificar dependências
    if not verificar_dependencias():
        sys.exit(1)
    
    # Verificar configurações
    if not verificar_env():
        sys.exit(1)
    
    # Criar arquivo de teste
    criar_arquivo_teste()
    
    print("\n✅ Sistema configurado e pronto para uso!")
    print("\n📌 Próximos passos:")
    print("1. Execute o SQL em create_tables.sql no Supabase")
    print("2. Execute: python main.py (para processar reuniões e criar usuários)")
    print("3. Execute: python FRONT.py (para iniciar a interface)")

if __name__ == "__main__":
    main()