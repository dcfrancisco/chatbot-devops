from __future__ import annotations

from collections import Counter

from app.observability.metrics.models import CounterMetric


class MetricsService:
    def __init__(self) -> None:
        self._counters: Counter[str] = Counter()

    def increment(self, metric: CounterMetric) -> None:
        self._counters[metric.name] += metric.value

    def snapshot(self) -> dict[str, int]:
        return dict(self._counters)