from app.knowledge.base import BaseKnowledgeProvider
from app.knowledge.loaders.base import BaseKnowledgeSourceLoader
from app.knowledge.sync.base import BaseKnowledgeSyncAdapter
from app.shared.registry import NamedRegistry


class KnowledgeRegistry(NamedRegistry[BaseKnowledgeProvider]):
    pass


class KnowledgeLoaderRegistry(NamedRegistry[BaseKnowledgeSourceLoader]):
    pass


class KnowledgeSyncRegistry(NamedRegistry[BaseKnowledgeSyncAdapter]):
    pass