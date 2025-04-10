import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Initialize Supabase client
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

def check_tables():
    try:
        # Verificar se a tabela briefings existe
        print("Verificando tabela 'briefings'...")
        response = supabase.table("briefings").select("id").limit(1).execute()
        print(f"Resposta: {response}")
        
        # Verificar a estrutura da tabela
        print("\nEstrutura da tabela 'briefings':")
        print("Colunas esperadas: id, user_id, input_text, briefing_result, created_at")
        
        # Verificar se há registros
        print("\nVerificando registros...")
        count_response = supabase.table("briefings").select("id", count="exact").execute()
        print(f"Total de registros: {count_response.count if hasattr(count_response, 'count') else 'Não disponível'}")
        
        # Verificar políticas de segurança
        print("\nVerificando políticas de segurança...")
        print("As políticas devem permitir que usuários vejam apenas seus próprios briefings.")
        
    except Exception as e:
        print(f"Erro ao verificar tabelas: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_tables() 