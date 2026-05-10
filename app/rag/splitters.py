from __future__ import annotations

from hashlib import sha256

from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

from app.core.config import Settings
from app.rag.documents import ChunkedDocument, ParsedDocument


class IntelligentChunker:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._default_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.retrieval_max_chunk_chars,
            chunk_overlap=settings.retrieval_chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len,
            is_separator_regex=False,
        )
        self._markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[("#", "h1"), ("##", "h2"), ("###", "h3")],
            strip_headers=False,
        )

    def split(self, document: ParsedDocument) -> list[ChunkedDocument]:
        if document.mime_type == "text/markdown":
            return self._split_markdown(document)
        return self._split_generic(document)

    def _split_markdown(self, document: ParsedDocument) -> list[ChunkedDocument]:
        header_docs = self._markdown_splitter.split_text(document.text)
        chunked: list[ChunkedDocument] = []
        chunk_index = 0
        for header_doc in header_docs:
            metadata = dict(document.metadata)
            metadata.update(header_doc.metadata)
            for chunk in self._default_splitter.split_text(header_doc.page_content):
                normalized = chunk.strip()
                if not normalized:
                    continue
                chunked.append(
                    self._make_chunk(document, chunk_index, normalized, metadata)
                )
                chunk_index += 1
        if chunked:
            return chunked
        return self._split_generic(document)

    def _split_generic(self, document: ParsedDocument) -> list[ChunkedDocument]:
        chunks: list[ChunkedDocument] = []
        for chunk_index, chunk in enumerate(self._default_splitter.split_text(document.text)):
            normalized = chunk.strip()
            if not normalized:
                continue
            chunks.append(self._make_chunk(document, chunk_index, normalized, dict(document.metadata)))
        return chunks

    def _make_chunk(
        self,
        document: ParsedDocument,
        chunk_index: int,
        content: str,
        metadata: dict,
    ) -> ChunkedDocument:
        metadata = dict(metadata)
        metadata["chunk_index"] = chunk_index
        metadata["source_id"] = document.source_id
        return ChunkedDocument(
            parsed_document=document,
            chunk_index=chunk_index,
            content=content,
            metadata=metadata,
            checksum=sha256(content.encode("utf-8")).hexdigest(),
            token_count=len(content.split()),
        )