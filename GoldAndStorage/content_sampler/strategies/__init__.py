"""Sampling strategies."""

from .base import SamplingStrategy
from .random import RandomSampling
from .stratified import StratifiedSampling
from .systematic import SystematicSampling
from .time_based import TimeBasedSampling
from .cluster import ClusterSampling
from .custom import CustomFilterSampling

STRATEGIES = {
    "random": RandomSampling,
    "stratified": StratifiedSampling,
    "systematic": SystematicSampling,
    "time_based": TimeBasedSampling,
    "cluster": ClusterSampling,
    "custom": CustomFilterSampling,
}


def get_strategy(strategy_name: str, **kwargs) -> SamplingStrategy:
    """Get sampling strategy by name."""
    if strategy_name not in STRATEGIES:
        raise ValueError(f"Unknown strategy: {strategy_name}. Available: {list(STRATEGIES.keys())}")
    return STRATEGIES[strategy_name](**kwargs)

__all__ = [
    "SamplingStrategy",
    "RandomSampling",
    "StratifiedSampling",
    "SystematicSampling",
    "TimeBasedSampling",
    "ClusterSampling",
    "CustomFilterSampling",
    "get_strategy",
    "STRATEGIES",
]
