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

def fix_supabase_schema():
    """Corrige o esquema da tabela briefings no Supabase."""
    try:
        print("Verificando e corrigindo o esquema da tabela 'briefings'...")
        
        # Verificar se a tabela briefings existe
        print("\nVerificando tabela 'briefings'...")
        try:
            response = supabase.table("briefings").select("id").limit(1).execute()
            print(f"Tabela 'briefings' existe. Resposta: {response}")
        except Exception as e:
            print(f"Erro ao verificar tabela 'briefings': {str(e)}")
            print("A tabela 'briefings' pode não existir ou ter um esquema incorreto.")
        
        # Verificar a estrutura da tabela
        print("\nVerificando estrutura da tabela 'briefings'...")
        try:
            # Tentar selecionar todas as colunas para verificar a estrutura
            columns_response = supabase.table("briefings").select("*").limit(1).execute()
            print(f"Estrutura da tabela: {columns_response}")
            
            # Verificar se a coluna briefing_result existe
            if hasattr(columns_response, 'data') and columns_response.data:
                columns = columns_response.data[0].keys()
                print(f"Colunas encontradas: {columns}")
                
                if 'briefing_result' not in columns:
                    print("A coluna 'briefing_result' não foi encontrada na tabela.")
                    print("É necessário recriar a tabela com o esquema correto.")
                else:
                    print("A coluna 'briefing_result' foi encontrada na tabela.")
            else:
                print("Não foi possível verificar a estrutura da tabela.")
        except Exception as e:
            print(f"Erro ao verificar estrutura da tabela: {str(e)}")
        
        print("\nPara corrigir o esquema da tabela, execute o seguinte SQL no console do Supabase:")
        print("""
-- Recriar a tabela briefings
DROP TABLE IF EXISTS briefings;

CREATE TABLE briefings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT NOT NULL,
    input_text TEXT NOT NULL,
    briefing_result TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES auth.users(id)
);

-- Enable Row Level Security
ALTER TABLE briefings ENABLE ROW LEVEL SECURITY;

-- Create policy to allow users to read their own briefings
CREATE POLICY "Users can read their own briefings"
    ON briefings
    FOR SELECT
    USING (auth.uid() = user_id);

-- Create policy to allow users to insert their own briefings
CREATE POLICY "Users can insert their own briefings"
    ON briefings
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Create policy to allow users to update their own briefings
CREATE POLICY "Users can update their own briefings"
    ON briefings
    FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Create policy to allow users to delete their own briefings
CREATE POLICY "Users can delete their own briefings"
    ON briefings
    FOR DELETE
    USING (auth.uid() = user_id);
        """)
        
        print("\nApós executar o SQL, execute este script novamente para verificar se o problema foi resolvido.")
        
    except Exception as e:
        print(f"Erro ao corrigir esquema da tabela: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_supabase_schema() 