import os
from supabase import create_client, Client
from dotenv import load_dotenv
import json

load_dotenv()

# Initialize Supabase client
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

def test_supabase_connection():
    """Testa a conexão com o Supabase e verifica se a tabela briefings está configurada corretamente."""
    try:
        print("Testando conexão com o Supabase...")
        
        # Verificar se a tabela briefings existe
        print("\nVerificando tabela 'briefings'...")
        response = supabase.table("briefings").select("id").limit(1).execute()
        print(f"Resposta: {response}")
        
        # Verificar se há registros
        print("\nVerificando registros...")
        count_response = supabase.table("briefings").select("id", count="exact").execute()
        print(f"Total de registros: {count_response.count if hasattr(count_response, 'count') else 'Não disponível'}")
        
        # Testar inserção de um registro
        print("\nTestando inserção de um registro...")
        test_data = {
            "user_id": "test_user_id",
            "input_text": "Teste de conexão com o Supabase",
            "briefing_result": json.dumps({
                "objetivo": "Teste de conexão",
                "publico_alvo": "Desenvolvedores",
                "referencias": ["Teste"],
                "prazos": {
                    "entrega_final": "01/01/2023",
                    "etapas_intermediarias": ["Teste"]
                },
                "orcamento": {
                    "valor_total": 1000.00,
                    "descontos": 0.00,
                    "valor_final": 1000.00
                },
                "observacoes": ["Teste de conexão"]
            })
        }
        
        insert_response = supabase.table("briefings").insert(test_data).execute()
        print(f"Resposta da inserção: {insert_response}")
        
        if insert_response.data:
            print(f"Registro inserido com sucesso! ID: {insert_response.data[0]['id']}")
            
            # Testar exclusão do registro inserido
            print("\nTestando exclusão do registro inserido...")
            delete_response = supabase.table("briefings").delete().eq("id", insert_response.data[0]['id']).execute()
            print(f"Resposta da exclusão: {delete_response}")
            print("Registro excluído com sucesso!")
        else:
            print("Falha ao inserir registro.")
        
        print("\nTeste concluído com sucesso!")
        
    except Exception as e:
        print(f"Erro ao testar conexão com o Supabase: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_supabase_connection() 