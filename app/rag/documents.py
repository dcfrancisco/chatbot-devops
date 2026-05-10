from dataclasses import dataclass, field


@dataclass(slots=True)
class ParsedDocument:
    source_path: str
    source_id: str
    source_key: str
    source_type: str
    title: str
    mime_type: str
    text: str
    checksum: str
    metadata: dict = field(default_factory=dict)


@dataclass(slots=True)
class ChunkedDocument:
    parsed_document: ParsedDocument
    chunk_index: int
    content: str
    metadata: dict
    checksum: str
    token_count: int