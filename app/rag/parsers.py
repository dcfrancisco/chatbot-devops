from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import yaml
from pypdf import PdfReader

from app.rag.documents import ParsedDocument


SUPPORTED_EXTENSIONS = {".md", ".markdown", ".txt", ".pdf", ".yaml", ".yml"}


class DocumentParser:
    def parse(self, path: Path, *, source_key: str) -> ParsedDocument:
        suffix = path.suffix.lower()
        if suffix not in SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported document type: {suffix}")

        if suffix in {".md", ".markdown"}:
            text = path.read_text(encoding="utf-8")
            metadata = self._base_metadata(path, "markdown")
            return self._build(path, source_key=source_key, text=text, mime_type="text/markdown", metadata=metadata)

        if suffix == ".txt":
            text = path.read_text(encoding="utf-8")
            metadata = self._base_metadata(path, "text")
            return self._build(path, source_key=source_key, text=text, mime_type="text/plain", metadata=metadata)

        if suffix == ".pdf":
            reader = PdfReader(str(path))
            pages: list[str] = []
            for index, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                pages.append(page_text)
            text = "\n\n".join(pages)
            metadata = self._base_metadata(path, "pdf")
            metadata["page_count"] = len(reader.pages)
            return self._build(path, source_key=source_key, text=text, mime_type="application/pdf", metadata=metadata)

        yaml_content = path.read_text(encoding="utf-8")
        loaded = yaml.safe_load(yaml_content)
        normalized = yaml.safe_dump(loaded, sort_keys=False) if loaded is not None else yaml_content
        metadata = self._base_metadata(path, "yaml")
        if isinstance(loaded, dict):
            metadata["top_level_keys"] = sorted(loaded.keys())
        return self._build(path, source_key=source_key, text=normalized, mime_type="application/yaml", metadata=metadata)

    def _build(self, path: Path, *, source_key: str, text: str, mime_type: str, metadata: dict) -> ParsedDocument:
        normalized_text = text.strip()
        checksum = sha256(normalized_text.encode("utf-8")).hexdigest()
        return ParsedDocument(
            source_path=str(path),
            source_id=path.as_posix(),
            source_key=source_key,
            source_type="filesystem",
            title=path.stem.replace("_", " ").replace("-", " ").title(),
            mime_type=mime_type,
            text=normalized_text,
            checksum=checksum,
            metadata=metadata,
        )

    def _base_metadata(self, path: Path, format_name: str) -> dict:
        stat = path.stat()
        return {
            "path": path.as_posix(),
            "filename": path.name,
            "extension": path.suffix.lower(),
            "format": format_name,
            "size_bytes": stat.st_size,
            "modified_at": stat.st_mtime,
        }