"""LoopBatcher — batch processor for multi-image or multi-data."""

from typing import Any, Callable
from dataclasses import dataclass, field


@dataclass
class BatchItem:
    """Single item in a batch with input, output, and status."""

    input: Any
    output: Any = None
    error: str | None = None
    processed: bool = False


class LoopBatcher:
    """Container for batch processing multiple items through a list of actions.

    Usage:
        batcher = LoopBatcher()
        batcher.add("image1.png")
        batcher.add("image2.png")
        batcher.add({"type": "json", "data": {"id": 1}})

        results = batcher.run([action1, action2])
    """

    def __init__(self):
        self._items: list[BatchItem] = []
        self._results: list[BatchItem] = []

    def add(self, item: Any) -> "LoopBatcher":
        """Add an item to the batch. Returns self for chaining."""
        self._items.append(BatchItem(input=item))
        return self

    def add_many(self, items: list[Any]) -> "LoopBatcher":
        """Add multiple items at once."""
        for item in items:
            self._items.append(BatchItem(input=item))
        return self

    def run(self, actions: list[Callable[[Any], Any]]) -> list[BatchItem]:
        """Run each item through the list of actions sequentially.

        Args:
            actions: List of callables. Each takes the item (or previous action output)
                     and returns a result.

        Returns:
            List of BatchItem objects with output or error set.
        """
        self._results = []

        for item in self._items:
            current = item.input
            try:
                for action in actions:
                    current = action(current)
                item.output = current
                item.processed = True
            except Exception as e:
                item.error = str(e)
                item.processed = True
            self._results.append(item)

        return self._results

    def run_parallel(self, actions: list[Callable[[Any], Any]], workers: int = 4) -> list[BatchItem]:
        """Run items through actions in parallel using threads.

        Args:
            actions: List of callables to apply sequentially per item.
            workers: Number of worker threads.

        Returns:
            List of BatchItem objects.
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        self._results = []

        def process(item: BatchItem) -> BatchItem:
            current = item.input
            try:
                for action in actions:
                    current = action(current)
                item.output = current
                item.processed = True
            except Exception as e:
                item.error = str(e)
                item.processed = True
            return item

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(process, item): item for item in self._items}
            for future in as_completed(futures):
                self._results.append(future.result())

        return self._results

    @property
    def items(self) -> list[BatchItem]:
        return self._items

    @property
    def results(self) -> list[BatchItem]:
        return self._results

    @property
    def errors(self) -> list[BatchItem]:
        return [r for r in self._results if r.error]

    @property
    def success_count(self) -> int:
        return sum(1 for r in self._results if r.processed and r.error is None)

    def clear(self) -> None:
        """Clear all items and results."""
        self._items.clear()
        self._results.clear()
