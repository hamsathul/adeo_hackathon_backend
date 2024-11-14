CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE langchain_pg_embedding (
    uuid UUID PRIMARY KEY,
    cmetadata JSONB,
    document TEXT,
    embedding vector(1536)
);

CREATE TABLE langchain_pg_collection (
    name TEXT PRIMARY KEY,
    cmetadata JSONB
);

CREATE INDEX ON langchain_pg_embedding 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);