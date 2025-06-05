"""
Sistema para reconstruir reuniões completas a partir dos chunks
"""

from typing import Dict, List, Optional
from supabase import Client
import json

class ReconstructorReunioes:
    """Reconstrói reuniões completas a partir dos chunks embeddados"""
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
    
    def reconstruir_reuniao(self, arquivo_origem: str) -> Optional[Dict]:
        """
        Reconstrói uma reunião completa a partir dos chunks
        
        Args:
            arquivo_origem: Nome do arquivo da reunião
            
        Returns:
            Dict com a reunião completa ou None se não encontrada
        """
        try:
            # Buscar todos os chunks da reunião ordenados
            resultado = self.supabase.table('reunioes_embbed').select(
                "chunk_numero, chunk_texto, titulo, responsavel, data_reuniao, hora_inicio, observacoes"
            ).eq(
                'arquivo_origem', arquivo_origem
            ).order(
                'chunk_numero'
            ).execute()
            
            if not resultado.data:
                return None
            
            chunks = resultado.data
            
            # Pegar metadados do primeiro chunk
            primeiro_chunk = chunks[0]
            reuniao = {
                'arquivo_origem': arquivo_origem,
                'titulo': primeiro_chunk.get('titulo', ''),
                'responsavel': primeiro_chunk.get('responsavel', ''),
                'data_reuniao': primeiro_chunk.get('data_reuniao', ''),
                'hora_inicio': primeiro_chunk.get('hora_inicio', ''),
                'observacoes': primeiro_chunk.get('observacoes', ''),
                'total_chunks': len(chunks)
            }
            
            # Concatenar todos os textos
            conteudo_completo = '\n'.join([
                chunk['chunk_texto'] for chunk in chunks
            ])
            
            reuniao['conteudo_completo'] = conteudo_completo
            
            return reuniao
            
        except Exception as e:
            print(f"Erro ao reconstruir reunião: {e}")
            return None
    
    def listar_reunioes(self, responsavel: Optional[str] = None) -> List[Dict]:
        """
        Lista todas as reuniões únicas
        
        Args:
            responsavel: Filtrar por responsável (opcional)
            
        Returns:
            Lista de reuniões
        """
        try:
            # Buscar primeira ocorrência de cada arquivo (chunk 1)
            query = self.supabase.table('reunioes_embbed').select(
                "arquivo_origem, titulo, responsavel, data_reuniao, hora_inicio, created_at"
            ).eq('chunk_numero', 1)
            
            if responsavel:
                query = query.eq('responsavel', responsavel)
            
            resultado = query.order('created_at', desc=True).execute()
            
            return resultado.data if resultado.data else []
            
        except Exception as e:
            print(f"Erro ao listar reuniões: {e}")
            return []
    
    def buscar_por_titulo(self, termo_busca: str) -> List[Dict]:
        """
        Busca reuniões por título
        
        Args:
            termo_busca: Termo para buscar no título
            
        Returns:
            Lista de reuniões encontradas
        """
        try:
            resultado = self.supabase.table('reunioes_embbed').select(
                "arquivo_origem, titulo, responsavel, data_reuniao"
            ).ilike(
                'titulo', f'%{termo_busca}%'
            ).eq(
                'chunk_numero', 1
            ).execute()
            
            return resultado.data if resultado.data else []
            
        except Exception as e:
            print(f"Erro ao buscar por título: {e}")
            return []
    
    def exportar_reuniao(self, arquivo_origem: str, caminho_destino: str) -> bool:
        """
        Exporta uma reunião reconstruída para arquivo
        
        Args:
            arquivo_origem: Nome do arquivo da reunião
            caminho_destino: Caminho onde salvar
            
        Returns:
            True se exportado com sucesso
        """
        reuniao = self.reconstruir_reuniao(arquivo_origem)
        
        if not reuniao:
            return False
        
        try:
            with open(caminho_destino, 'w', encoding='utf-8') as f:
                # Escrever cabeçalho
                f.write(f"Título: {reuniao['titulo']}\n")
                f.write(f"Responsável: {reuniao['responsavel']}\n")
                f.write(f"Data: {reuniao['data_reuniao']}\n")
                f.write(f"Hora: {reuniao['hora_inicio']}\n")
                if reuniao['observacoes']:
                    f.write(f"Observações: {reuniao['observacoes']}\n")
                f.write("\n" + "="*60 + "\n\n")
                
                # Escrever conteúdo
                f.write(reuniao['conteudo_completo'])
                
            print(f"✅ Reunião exportada para: {caminho_destino}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao exportar: {e}")
            return False


# Funções auxiliares para integração com o assistente
def processar_comando_reconstruir(supabase_client: Client, comando: str) -> str:
    """
    Processa comandos de reconstrução de reuniões
    
    Exemplos de comandos:
    - "mostre a transcrição completa da reunião X"
    - "exporte a reunião de hoje"
    - "liste todas as reuniões do João"
    """
    reconstructor = ReconstructorReunioes(supabase_client)
    
    comando_lower = comando.lower()
    
    # Listar reuniões
    if 'liste' in comando_lower or 'listar' in comando_lower:
        if 'minhas' in comando_lower:
            # Buscar reuniões do usuário atual (precisa passar o username)
            reunioes = reconstructor.listar_reunioes()
        else:
            # Extrair nome se mencionado
            import re
            match = re.search(r'(?:do|da)\s+([A-Z][a-z]+)', comando)
            responsavel = match.group(1) if match else None
            reunioes = reconstructor.listar_reunioes(responsavel)
        
        if reunioes:
            resposta = "📋 Reuniões encontradas:\n\n"
            for r in reunioes[:10]:  # Limitar a 10
                resposta += f"• {r['titulo']} - {r['data_reuniao']} ({r['responsavel']})\n"
            return resposta
        else:
            return "Nenhuma reunião encontrada."
    
    # Mostrar transcrição completa
    elif 'transcrição completa' in comando_lower or 'reunião completa' in comando_lower:
        # Tentar identificar qual reunião
        reunioes = reconstructor.listar_reunioes()
        if reunioes:
            # Por enquanto, pegar a mais recente
            mais_recente = reunioes[0]
            reuniao = reconstructor.reconstruir_reuniao(mais_recente['arquivo_origem'])
            
            if reuniao:
                resposta = f"📄 **{reuniao['titulo']}**\n"
                resposta += f"👤 Responsável: {reuniao['responsavel']}\n"
                resposta += f"📅 Data: {reuniao['data_reuniao']} às {reuniao['hora_inicio']}\n"
                resposta += f"\n--- Conteúdo ---\n"
                resposta += reuniao['conteudo_completo'][:1000]  # Limitar tamanho
                if len(reuniao['conteudo_completo']) > 1000:
                    resposta += "\n\n[... conteúdo truncado ...]"
                return resposta
        
        return "Não foi possível encontrar a reunião solicitada."
    
    return "Comando não reconhecido. Tente: 'liste reuniões' ou 'mostre transcrição completa'"