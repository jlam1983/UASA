from typing import Optional, Callable, List, Dict, Any
from .base import SamplingStrategy


class CustomFilterSampling(SamplingStrategy):
    """Custom filter sampling - user-defined filter function."""

    def __init__(self, filter_func: Optional[Callable] = None):
        self.filter_func = filter_func

    def sample(self, data: List[Dict], sample_size: int, **kwargs) -> List[Dict]:
        if self.filter_func is None:
            return data.copy()[:sample_size]

        filtered = [r for r in data if self.filter_func(r)]
        return filtered[:sample_size]
