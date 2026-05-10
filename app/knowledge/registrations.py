from app.core.config import Settings
from app.knowledge.base import BaseKnowledgeProvider
from app.knowledge.loaders import (
    BaseKnowledgeSourceLoader,
    ConfluenceKnowledgeLoader,
    GitRepositoryKnowledgeLoader,
    MarkdownKnowledgeLoader,
    PdfKnowledgeLoader,
    SharePointKnowledgeLoader,
    TextKnowledgeLoader,
    YamlKnowledgeLoader,
)
from app.knowledge.registry import KnowledgeLoaderRegistry, KnowledgeRegistry, KnowledgeSyncRegistry
from app.knowledge.retrieval import RetrievalKnowledgeProvider
from app.knowledge.sync.base import BaseKnowledgeSyncAdapter
from app.knowledge.sync.examples import NoOpKnowledgeSyncAdapter
from app.rag.retriever import RetrieverService
from app.shared.registration import FactoryCatalog, register_factory


KNOWLEDGE_PROVIDER_CATALOG = FactoryCatalog[BaseKnowledgeProvider]()
KNOWLEDGE_LOADER_CATALOG = FactoryCatalog[BaseKnowledgeSourceLoader]()
KNOWLEDGE_SYNC_CATALOG = FactoryCatalog[BaseKnowledgeSyncAdapter]()


@register_factory(
    KNOWLEDGE_PROVIDER_CATALOG,
    name="semantic-retrieval",
    capabilities=("retrieval", "citations", "source-tracking"),
    metadata={"kind": "knowledge", "provider_type": "retrieval"},
)
def build_retrieval_provider(*, retriever_service: RetrieverService) -> BaseKnowledgeProvider:
    return RetrievalKnowledgeProvider(retriever_service)


@register_factory(KNOWLEDGE_LOADER_CATALOG, name="markdown-loader", capabilities=("markdown",), metadata={"kind": "knowledge-loader"})
def build_markdown_loader(*, settings: Settings) -> BaseKnowledgeSourceLoader:
    return MarkdownKnowledgeLoader()


@register_factory(KNOWLEDGE_LOADER_CATALOG, name="yaml-loader", capabilities=("yaml",), metadata={"kind": "knowledge-loader"})
def build_yaml_loader(*, settings: Settings) -> BaseKnowledgeSourceLoader:
    return YamlKnowledgeLoader()


@register_factory(KNOWLEDGE_LOADER_CATALOG, name="txt-loader", capabilities=("txt",), metadata={"kind": "knowledge-loader"})
def build_txt_loader(*, settings: Settings) -> BaseKnowledgeSourceLoader:
    return TextKnowledgeLoader()


@register_factory(KNOWLEDGE_LOADER_CATALOG, name="pdf-loader", capabilities=("pdf",), metadata={"kind": "knowledge-loader"})
def build_pdf_loader(*, settings: Settings) -> BaseKnowledgeSourceLoader:
    return PdfKnowledgeLoader()


@register_factory(KNOWLEDGE_LOADER_CATALOG, name="git-repo-loader", capabilities=("git-repo",), metadata={"kind": "knowledge-loader", "status": "future"})
def build_git_loader(*, settings: Settings) -> BaseKnowledgeSourceLoader:
    return GitRepositoryKnowledgeLoader()


@register_factory(KNOWLEDGE_LOADER_CATALOG, name="confluence-loader", capabilities=("confluence",), metadata={"kind": "knowledge-loader", "status": "future"})
def build_confluence_loader(*, settings: Settings) -> BaseKnowledgeSourceLoader:
    return ConfluenceKnowledgeLoader()


@register_factory(KNOWLEDGE_LOADER_CATALOG, name="sharepoint-loader", capabilities=("sharepoint",), metadata={"kind": "knowledge-loader", "status": "future"})
def build_sharepoint_loader(*, settings: Settings) -> BaseKnowledgeSourceLoader:
    return SharePointKnowledgeLoader()


@register_factory(KNOWLEDGE_SYNC_CATALOG, name="noop-sync", capabilities=("sync",), metadata={"kind": "knowledge-sync"})
def build_noop_sync(*, settings: Settings) -> BaseKnowledgeSyncAdapter:
    return NoOpKnowledgeSyncAdapter()


def build_knowledge_registry(*, retriever_service: RetrieverService) -> KnowledgeRegistry:
    return KnowledgeRegistry(KNOWLEDGE_PROVIDER_CATALOG.build_all(retriever_service=retriever_service))


def build_loader_registry(*, settings: Settings) -> KnowledgeLoaderRegistry:
    return KnowledgeLoaderRegistry(KNOWLEDGE_LOADER_CATALOG.build_all(settings=settings))


def build_sync_registry(*, settings: Settings) -> KnowledgeSyncRegistry:
    return KnowledgeSyncRegistry(KNOWLEDGE_SYNC_CATALOG.build_all(settings=settings))