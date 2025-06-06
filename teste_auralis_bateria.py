#!/usr/bin/env python3
"""
Teste massivo e estressante do sistema AURALIS
Avalia todas as capacidades do agente em contexto corporativo/financeiro
"""

import json
import time
from datetime import datetime
from typing import List, Dict, Tuple
import sys
import os

# Adicionar o diretório pai ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import AURALISBackend

# Lista de perguntas organizadas por categoria
PERGUNTAS_TESTE = {
    "reunioes_especificas": [
        "Qual foi o tema principal da última reunião?",
        "Quem participou da reunião sobre orçamento?",
        "Quais decisões foram tomadas na reunião de planejamento estratégico?",
        "Quando ocorreu a reunião sobre compliance?",
        "Quais foram os principais pontos discutidos na reunião de ontem?",
        "Houve alguma reunião sobre riscos operacionais este mês?",
        "Quem foi o responsável por apresentar o relatório financeiro?",
        "Qual foi a duração da reunião sobre novos produtos?",
        "Quais ações foram definidas na última reunião do comitê?",
        "Teve alguma reunião cancelada esta semana?"
    ],
    
    "base_conhecimento": [
        "O que é análise de crédito?",
        "Como funciona o processo de compliance?",
        "Quais são os principais indicadores financeiros?",
        "Explique o conceito de gestão de riscos",
        "O que é KYC (Know Your Customer)?",
        "Como calcular o ROI de um investimento?",
        "Quais são as melhores práticas em auditoria interna?",
        "O que significa liquidez no contexto bancário?",
        "Como funciona a política de crédito da instituição?",
        "Quais são os requisitos regulatórios atuais?"
    ],
    
    "cruzamento_informacoes": [
        "Compare as decisões das duas últimas reuniões de diretoria",
        "Qual a relação entre as metas discutidas e os resultados apresentados?",
        "Como as políticas de compliance afetam as operações discutidas?",
        "Relacione os riscos identificados com as medidas propostas",
        "Compare o orçamento aprovado com as despesas realizadas",
        "Quais reuniões trataram de temas relacionados à regulamentação?",
        "Como os indicadores apresentados se relacionam com as metas?",
        "Identifique contradições entre diferentes reuniões sobre o mesmo tema",
        "Correlacione as decisões de crédito com a política vigente",
        "Analise a evolução dos temas ao longo das reuniões"
    ],
    
    "perguntas_complexas": [
        "Faça uma análise SWOT baseada nas informações das últimas reuniões",
        "Elabore um resumo executivo das principais decisões do trimestre",
        "Identifique tendências e padrões nas discussões sobre riscos",
        "Proponha melhorias baseadas nos problemas recorrentes identificados",
        "Analise o impacto das decisões tomadas nos indicadores apresentados",
        "Sintetize as principais preocupações levantadas pelos participantes",
        "Avalie a eficácia das medidas implementadas conforme discutido",
        "Projete cenários futuros baseados nas tendências observadas",
        "Identifique gaps entre o planejado e o executado",
        "Sugira uma pauta para a próxima reunião baseada em pendências"
    ],
    
    "perguntas_genericas": [
        "Me ajude",
        "O que você pode fazer?",
        "Preciso de informações",
        "Tem algo importante?",
        "Resumo geral",
        "O que aconteceu?",
        "Novidades?",
        "Status atual",
        "Próximos passos",
        "Alguma sugestão?"
    ],
    
    "contexto_financeiro": [
        "Qual o status da carteira de crédito?",
        "Como está a inadimplência?",
        "Quais produtos foram mais rentáveis?",
        "Análise da margem financeira",
        "Performance dos investimentos",
        "Custos operacionais estão controlados?",
        "Qual o nível de provisionamento?",
        "Como está o capital regulatório?",
        "Rentabilidade por segmento de clientes",
        "Eficiência operacional do último período"
    ],
    
    "perguntas_teste_limite": [
        "asdfghjkl",
        "???",
        "",
        "REUNIÃO REUNIÃO REUNIÃO",
        "Explique tudo sobre tudo",
        "Quero saber de uma reunião que não existe",
        "Me fale sobre a reunião do dia 32 de dezembro",
        "Qual o sentido da vida segundo as reuniões?",
        "Compare isso com aquilo sem contexto",
        "Faça uma análise de dados que não foram fornecidos"
    ]
}


class TestadorAuralis:
    def __init__(self):
        self.sistema = AURALISBackend()
        self.resultados = []
        self.tempo_inicio = time.time()
        
    def executar_pergunta(self, pergunta: str, categoria: str) -> Dict:
        """Executa uma pergunta e coleta a resposta"""
        print(f"\n[{categoria}] Pergunta: {pergunta}")
        
        inicio = time.time()
        try:
            resposta = self.sistema.buscar_informacao_reuniao(pergunta)
            tempo_resposta = time.time() - inicio
            
            resultado = {
                "categoria": categoria,
                "pergunta": pergunta,
                "resposta": resposta,
                "tempo_resposta": tempo_resposta,
                "sucesso": True,
                "erro": None
            }
            
            print(f"Resposta ({tempo_resposta:.2f}s): {resposta[:100]}...")
            
        except Exception as e:
            tempo_resposta = time.time() - inicio
            resultado = {
                "categoria": categoria,
                "pergunta": pergunta,
                "resposta": None,
                "tempo_resposta": tempo_resposta,
                "sucesso": False,
                "erro": str(e)
            }
            print(f"ERRO ({tempo_resposta:.2f}s): {str(e)}")
            
        return resultado
    
    def avaliar_resposta(self, resultado: Dict) -> Dict:
        """Avalia a qualidade da resposta"""
        avaliacao = {
            "relevante": False,
            "completa": False,
            "concisa": False,
            "tempo_adequado": False,
            "pontuacao": 0
        }
        
        if not resultado["sucesso"]:
            return avaliacao
            
        resposta = resultado["resposta"]
        
        # Relevância - resposta não é genérica demais
        respostas_genericas = ["não encontrei", "não há informações", "erro", "desculpe"]
        avaliacao["relevante"] = not any(gen in resposta.lower() for gen in respostas_genericas)
        
        # Completude - resposta tem tamanho adequado
        avaliacao["completa"] = 20 < len(resposta) < 500
        
        # Concisão - resposta é direta
        avaliacao["concisa"] = len(resposta) < 200
        
        # Tempo adequado - menos de 3 segundos
        avaliacao["tempo_adequado"] = resultado["tempo_resposta"] < 3.0
        
        # Pontuação
        avaliacao["pontuacao"] = sum([
            avaliacao["relevante"] * 40,
            avaliacao["completa"] * 30,
            avaliacao["concisa"] * 20,
            avaliacao["tempo_adequado"] * 10
        ])
        
        return avaliacao
    
    def executar_teste_completo(self):
        """Executa todas as perguntas do teste"""
        print("=== INICIANDO TESTE MASSIVO DO AURALIS ===")
        print(f"Total de perguntas: {sum(len(pergs) for pergs in PERGUNTAS_TESTE.values())}")
        
        for categoria, perguntas in PERGUNTAS_TESTE.items():
            print(f"\n\n{'='*60}")
            print(f"CATEGORIA: {categoria.upper()}")
            print(f"{'='*60}")
            
            for pergunta in perguntas:
                resultado = self.executar_pergunta(pergunta, categoria)
                resultado["avaliacao"] = self.avaliar_resposta(resultado)
                self.resultados.append(resultado)
                
                # Pequena pausa para não sobrecarregar
                time.sleep(0.5)
        
        tempo_total = time.time() - self.tempo_inicio
        print(f"\n\nTESTE COMPLETO EM {tempo_total:.2f} segundos")
        
    def gerar_relatorio(self) -> str:
        """Gera relatório detalhado dos resultados"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Salvar resultados em JSON
        with open(f'teste_auralis_resultados_{timestamp}.json', 'w', encoding='utf-8') as f:
            json.dump(self.resultados, f, ensure_ascii=False, indent=2)
        
        # Análise geral
        total_perguntas = len(self.resultados)
        sucessos = sum(1 for r in self.resultados if r["sucesso"])
        tempo_medio = sum(r["tempo_resposta"] for r in self.resultados) / total_perguntas
        
        # Análise por categoria
        analise_categorias = {}
        for categoria in PERGUNTAS_TESTE.keys():
            resultados_cat = [r for r in self.resultados if r["categoria"] == categoria]
            if resultados_cat:
                analise_categorias[categoria] = {
                    "total": len(resultados_cat),
                    "sucessos": sum(1 for r in resultados_cat if r["sucesso"]),
                    "tempo_medio": sum(r["tempo_resposta"] for r in resultados_cat) / len(resultados_cat),
                    "pontuacao_media": sum(r["avaliacao"]["pontuacao"] for r in resultados_cat) / len(resultados_cat)
                }
        
        # Gerar relatório Markdown
        relatorio = f"""# Relatório de Teste Massivo - Sistema AURALIS

**Data/Hora:** {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
**Total de Perguntas:** {total_perguntas}
**Taxa de Sucesso:** {(sucessos/total_perguntas)*100:.1f}%
**Tempo Médio de Resposta:** {tempo_medio:.2f}s

## Resumo Executivo

O teste massivo do sistema AURALIS foi executado com {total_perguntas} perguntas diversificadas, 
abrangendo diferentes categorias e níveis de complexidade. O sistema apresentou uma taxa de 
sucesso de {(sucessos/total_perguntas)*100:.1f}%, com tempo médio de resposta de {tempo_medio:.2f} segundos.

## Análise por Categoria

"""
        
        for categoria, analise in analise_categorias.items():
            relatorio += f"""### {categoria.replace('_', ' ').title()}
- **Total de perguntas:** {analise['total']}
- **Taxa de sucesso:** {(analise['sucessos']/analise['total'])*100:.1f}%
- **Tempo médio:** {analise['tempo_medio']:.2f}s
- **Pontuação média:** {analise['pontuacao_media']:.1f}/100

"""

        relatorio += """## Perguntas e Respostas Detalhadas

"""
        
        for i, resultado in enumerate(self.resultados, 1):
            relatorio += f"""### Pergunta {i} - {resultado['categoria']}

**Pergunta:** {resultado['pergunta']}

**Resposta:** {resultado['resposta'] if resultado['sucesso'] else f"ERRO: {resultado['erro']}"}

**Métricas:**
- Tempo de resposta: {resultado['tempo_resposta']:.2f}s
- Sucesso: {'✅' if resultado['sucesso'] else '❌'}
- Relevância: {'✅' if resultado['avaliacao']['relevante'] else '❌'}
- Completude: {'✅' if resultado['avaliacao']['completa'] else '❌'}
- Concisão: {'✅' if resultado['avaliacao']['concisa'] else '❌'}
- Tempo adequado: {'✅' if resultado['avaliacao']['tempo_adequado'] else '❌'}
- Pontuação: {resultado['avaliacao']['pontuacao']}/100

---

"""

        # Análise de problemas e sugestões
        problemas = [r for r in self.resultados if not r["sucesso"] or r["avaliacao"]["pontuacao"] < 50]
        
        relatorio += f"""## Análise de Problemas Identificados

**Total de respostas problemáticas:** {len(problemas)}/{total_perguntas}

### Principais Problemas:

"""
        
        if problemas:
            # Agrupar por tipo de problema
            erros = {}
            for p in problemas:
                if not p["sucesso"]:
                    erro = p["erro"]
                    if erro not in erros:
                        erros[erro] = []
                    erros[erro].append(p["pergunta"])
            
            for erro, perguntas in erros.items():
                relatorio += f"""#### Erro: {erro}
Perguntas afetadas:
"""
                for perg in perguntas[:5]:  # Mostrar no máximo 5 exemplos
                    relatorio += f"- {perg}\n"
                if len(perguntas) > 5:
                    relatorio += f"- ... e mais {len(perguntas)-5} perguntas\n"
                relatorio += "\n"

        # Sugestões de melhoria
        relatorio += """## Sugestões de Melhoria

Com base nos resultados do teste, seguem as principais recomendações:

"""
        
        # Análise automática de sugestões
        if tempo_medio > 2:
            relatorio += """### 1. **Otimização de Performance**
- O tempo médio de resposta está acima do ideal (>2s)
- Considerar implementação de cache mais agressivo
- Otimizar queries e processamento de embeddings
- Implementar índices para buscas frequentes

"""

        taxa_relevancia = sum(1 for r in self.resultados if r["avaliacao"]["relevante"]) / total_perguntas
        if taxa_relevancia < 0.8:
            relatorio += """### 2. **Melhoria na Relevância das Respostas**
- Muitas respostas são genéricas ou não atendem à pergunta
- Melhorar o sistema de análise semântica
- Implementar validação de contexto antes de responder
- Adicionar fallbacks mais inteligentes

"""

        perguntas_genericas = [r for r in self.resultados if r["categoria"] == "perguntas_genericas"]
        pontuacao_genericas = sum(r["avaliacao"]["pontuacao"] for r in perguntas_genericas) / len(perguntas_genericas) if perguntas_genericas else 0
        
        if pontuacao_genericas < 60:
            relatorio += """### 3. **Tratamento de Perguntas Vagas**
- O sistema tem dificuldade com perguntas genéricas
- Implementar sistema de clarificação interativa
- Criar respostas padrão mais úteis para perguntas vagas
- Sugerir opções específicas ao usuário

"""

        erros_busca = sum(1 for r in self.resultados if not r["sucesso"] and "busca" in str(r.get("erro", "")).lower())
        if erros_busca > 5:
            relatorio += """### 4. **Robustez do Sistema de Busca**
- Muitos erros relacionados à busca de informações
- Implementar tratamento de exceções mais robusto
- Adicionar validação de entrada antes da busca
- Criar índices alternativos para fallback

"""

        relatorio += """### 5. **Recomendações Gerais**

1. **Implementar Sistema de Feedback**
   - Permitir que usuários avaliem as respostas
   - Usar feedback para treinar e melhorar o sistema
   
2. **Adicionar Contexto de Sessão**
   - Manter histórico da conversa
   - Permitir perguntas de follow-up
   
3. **Melhorar Base de Conhecimento**
   - Adicionar mais conteúdo específico do domínio financeiro
   - Atualizar regularmente com novas regulamentações
   
4. **Implementar Métricas de Qualidade**
   - Dashboard de monitoramento em tempo real
   - Alertas para degradação de performance
   
5. **Segurança e Compliance**
   - Adicionar logs de auditoria detalhados
   - Implementar controle de acesso granular
   - Garantir conformidade com LGPD/GDPR

## Conclusão

"""
        
        # Classificação geral
        pontuacao_geral = sum(r["avaliacao"]["pontuacao"] for r in self.resultados) / total_perguntas
        
        if pontuacao_geral >= 80:
            classificacao = "EXCELENTE"
            emoji = "🌟"
        elif pontuacao_geral >= 70:
            classificacao = "BOM"
            emoji = "✅"
        elif pontuacao_geral >= 60:
            classificacao = "REGULAR"
            emoji = "⚠️"
        else:
            classificacao = "NECESSITA MELHORIAS"
            emoji = "🔴"
            
        relatorio += f"""O sistema AURALIS apresentou desempenho **{classificacao}** {emoji} com pontuação geral de **{pontuacao_geral:.1f}/100**.

### Pontos Fortes:
- Arquitetura modular bem estruturada
- Capacidade de processar diferentes tipos de perguntas
- Sistema de busca semântica funcional

### Pontos de Atenção:
- Tempo de resposta pode ser otimizado
- Tratamento de perguntas vagas precisa melhorar
- Necessidade de mais conteúdo na base de conhecimento

### Próximos Passos Recomendados:
1. Implementar as otimizações de performance sugeridas
2. Expandir a base de conhecimento com conteúdo específico
3. Adicionar sistema de feedback e aprendizado contínuo
4. Realizar testes de carga e stress
5. Implementar monitoramento e observabilidade

---
*Relatório gerado automaticamente pelo Sistema de Testes AURALIS*
"""
        
        return relatorio


def main():
    """Executa o teste completo"""
    testador = TestadorAuralis()
    
    print("Iniciando teste massivo do AURALIS...")
    print("Este teste pode levar alguns minutos para ser concluído.")
    
    try:
        testador.executar_teste_completo()
        
        print("\nGerando relatório...")
        relatorio = testador.gerar_relatorio()
        
        # Salvar relatório
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_arquivo = f"RELATORIO_TESTE_AURALIS_{timestamp}.md"
        
        with open(nome_arquivo, 'w', encoding='utf-8') as f:
            f.write(relatorio)
            
        print(f"\n✅ Teste completo! Relatório salvo em: {nome_arquivo}")
        
    except Exception as e:
        print(f"\n❌ Erro durante o teste: {str(e)}")
        raise


if __name__ == "__main__":
    main()