-- Optimized cosine similarity search across all chunks.
SELECT
    dc.id,
    d.id AS document_id,
    d.title,
    d.source_id,
    dc.chunk_index,
    dc.content,
    dc.metadata_json,
    dc.embedding <=> CAST(:query_embedding AS vector(768)) AS cosine_distance
FROM document_chunks dc
JOIN documents d ON d.id = dc.document_id
ORDER BY dc.embedding <=> CAST(:query_embedding AS vector(768))
LIMIT 8;

-- Source-filtered similarity search for multi-source knowledge bases.
SELECT
    dc.id,
    s.source_key,
    d.title,
    dc.chunk_index,
    dc.content,
    dc.embedding <=> CAST(:query_embedding AS vector(768)) AS cosine_distance
FROM document_chunks dc
JOIN documents d ON d.id = dc.document_id
JOIN sources s ON s.id = dc.source_ref_id
WHERE s.source_key = :source_key
ORDER BY dc.embedding <=> CAST(:query_embedding AS vector(768))
LIMIT 5;

-- Memory retrieval for future semantic memory systems.
SELECT
    me.id,
    me.memory_type,
    me.key,
    me.content,
    me.importance,
    me.embedding <=> CAST(:query_embedding AS vector(768)) AS cosine_distance
FROM memory_entries me
WHERE me.embedding IS NOT NULL
  AND (me.conversation_id = :conversation_id OR me.conversation_id IS NULL)
ORDER BY me.embedding <=> CAST(:query_embedding AS vector(768)), me.importance DESC
LIMIT 10;

-- Recent assistant citations for traceability.
SELECT
    cm.conversation_id,
    cm.message_index,
    mc.citation_rank,
    mc.score,
    d.title,
    d.source_id,
    dc.chunk_index,
    mc.snippet
FROM message_citations mc
JOIN conversation_messages cm ON cm.id = mc.message_id
JOIN document_chunks dc ON dc.id = mc.document_chunk_id
JOIN documents d ON d.id = dc.document_id
WHERE cm.conversation_id = :conversation_id
ORDER BY cm.message_index DESC, mc.citation_rank ASC;
