-- Verificar o esquema atual da tabela 'briefings'
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'briefings'
ORDER BY ordinal_position;

-- Verificar se a tabela 'briefings' existe
SELECT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_name = 'briefings'
);

-- Verificar as políticas da tabela 'briefings'
SELECT * FROM pg_policies WHERE tablename = 'briefings'; 