-- Drop existing policies
DROP POLICY IF EXISTS "Users can read their own briefings" ON briefings;
DROP POLICY IF EXISTS "Users can insert their own briefings" ON briefings;
DROP POLICY IF EXISTS "Users can update their own briefings" ON briefings;
DROP POLICY IF EXISTS "Users can delete their own briefings" ON briefings;

-- Drop existing table
DROP TABLE IF EXISTS briefings;

-- Create briefings table with new schema
CREATE TABLE briefings (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    titulo TEXT,
    content JSONB NOT NULL,
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

-- Verificar o esquema atual da tabela 'briefings'
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'briefings'
ORDER BY ordinal_position; 