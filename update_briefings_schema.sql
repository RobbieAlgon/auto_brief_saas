-- Verificar se a coluna 'content' existe
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'briefings'
        AND column_name = 'content'
    ) THEN
        -- Adicionar a coluna 'content' se não existir
        ALTER TABLE briefings ADD COLUMN content JSONB;
        
        -- Copiar dados da coluna 'conteudo' para 'content' se existir
        IF EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = 'briefings'
            AND column_name = 'conteudo'
        ) THEN
            UPDATE briefings SET content = conteudo;
        END IF;
        
        -- Tornar a coluna 'content' NOT NULL
        ALTER TABLE briefings ALTER COLUMN content SET NOT NULL;
    END IF;
END $$;

-- Verificar se a coluna 'titulo' existe
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'briefings'
        AND column_name = 'titulo'
    ) THEN
        -- Adicionar a coluna 'titulo' se não existir
        ALTER TABLE briefings ADD COLUMN titulo TEXT;
    END IF;
END $$;

-- Verificar o esquema atual da tabela 'briefings'
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'briefings'
ORDER BY ordinal_position; 