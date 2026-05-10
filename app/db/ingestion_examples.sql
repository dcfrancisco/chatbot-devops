-- Example: register a source for local markdown ingestion.
INSERT INTO sources (
    id,
    source_key,
    source_type,
    uri,
    status,
    metadata_json
) VALUES (
    gen_random_uuid(),
    'local-assets',
    'filesystem',
    'file:///workspace/assets',
    'active',
    '{"team":"devops","environment":"local"}'::jsonb
);

-- Example: create an ingestion run.
INSERT INTO ingestion_runs (
    id,
    source_ref_id,
    status,
    metadata_json
) VALUES (
    gen_random_uuid(),
    (SELECT id FROM sources WHERE source_key = 'local-assets'),
    'running',
    '{"trigger":"manual","actor":"developer"}'::jsonb
);

-- Example: insert a document tracked to a source and ingestion run.
INSERT INTO documents (
    id,
    source_ref_id,
    ingestion_run_id,
    source_id,
    title,
    mime_type,
    content_sha256,
    metadata_json
) VALUES (
    gen_random_uuid(),
    (SELECT id FROM sources WHERE source_key = 'local-assets'),
    (SELECT id FROM ingestion_runs ORDER BY started_at DESC LIMIT 1),
    'jenkins-guide-md',
    'Jenkins Guide',
    'text/markdown',
    'sha256-placeholder',
    '{"path":"assets/jenkins-guide.md","labels":["jenkins","ci"]}'::jsonb
);

-- Example: insert a chunk with a synthetic 768-d embedding for testing.
INSERT INTO document_chunks (
    id,
    document_id,
    source_ref_id,
    chunk_index,
    content,
    token_count,
    content_sha256,
    metadata_json,
    embedding
) VALUES (
    gen_random_uuid(),
    (SELECT id FROM documents WHERE source_id = 'jenkins-guide-md'),
    (SELECT id FROM sources WHERE source_key = 'local-assets'),
    0,
    'Jenkins pipelines are commonly defined in Jenkinsfiles and executed by agents.',
    11,
    'chunk-sha256-placeholder',
    '{"heading":"Pipelines"}'::jsonb,
    array_fill(0.01::real, ARRAY[768])::vector(768)
);

-- Example: complete the ingestion run.
UPDATE ingestion_runs
SET
    status = 'completed',
    completed_at = NOW(),
    documents_seen = 1,
    documents_written = 1,
    chunks_written = 1
WHERE id = (SELECT id FROM ingestion_runs ORDER BY started_at DESC LIMIT 1);
