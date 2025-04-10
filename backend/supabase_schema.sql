-- Create briefings table
CREATE TABLE briefings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT NOT NULL,
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