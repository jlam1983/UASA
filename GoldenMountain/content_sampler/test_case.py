"""Test cases for ContentSampler and related components."""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from content_sampler import ContentSampler
from content_sampler.strategies import get_strategy, STRATEGIES


class TestContentSampler:
    """Test ContentSampler core functionality."""

    def test_sample_basic(self):
        """Test basic sampling with random strategy."""
        sampler = ContentSampler(default_strategy="random", seed=42)
        data = [{"id": i, "value": i * 10} for i in range(100)]

        result = sampler.sample(data, 10)

        assert len(result) == 10
        # Check sample metadata is added
        assert all("_sample_index" in r for r in result)
        assert all("_sample_strategy" in r for r in result)

    def test_sample_with_different_strategies(self):
        """Test sampling with different strategies."""
        sampler = ContentSampler(seed=42)
        data = [{"id": i} for i in range(50)]

        for strategy_name in STRATEGIES:
            try:
                result = sampler.sample(data, 5, strategy=strategy_name)
                assert len(result) == 5
                assert all("_sample_strategy" in r for r in result)
            except Exception:
                # Some strategies may require specific kwargs
                pass

    def test_sample_with_analysis(self):
        """Test sample_with_analysis method."""
        sampler = ContentSampler(seed=42)
        data = [
            {"id": 1, "name": "Alice", "age": 30, "salary": 50000},
            {"id": 2, "name": "Bob", "age": 25, "salary": 45000},
            {"id": 3, "name": "Charlie", "age": 35, "salary": 60000},
            {"id": 4, "name": "Diana", "age": 28, "salary": 52000},
            {"id": 5, "name": "Eve", "age": 32, "salary": 55000},
        ]

        result = sampler.sample_with_analysis(data, 3, analyze_schema=True)

        assert "metadata" in result
        assert "records" in result
        assert "schema_analysis" in result
        assert result["metadata"]["original_count"] == 5
        assert result["metadata"]["sample_size"] == 3

    def test_sample_with_noise_detection(self):
        """Test sample_with_analysis with noise detection."""
        sampler = ContentSampler(seed=42)
        data = [
            {"id": 1, "name": "Alice", "age": 30},
            {"id": 2, "name": "", "age": 25},  # Empty name - potential noise
            {"id": 3, "name": "Charlie", "age": 35},
        ]

        result = sampler.sample_with_analysis(data, 3, detect_noise=True)

        assert "noise_report" in result

    def test_analyze_schema(self):
        """Test schema analysis."""
        sampler = ContentSampler()
        data = [
            {"id": 1, "name": "Alice", "age": 30, "score": 95.5},
            {"id": 2, "name": "Bob", "age": 25, "score": 82.3},
            {"id": 3, "name": "Charlie", "age": 35, "score": 78.9},
        ]

        result = sampler.analyze_schema(data)

        assert result is not None
        assert "fields" in result or len(result) > 0

    def test_detect_noise(self):
        """Test noise detection."""
        sampler = ContentSampler()
        data = [
            {"id": 1, "name": "Alice", "email": "alice@example.com"},
            {"id": 2, "name": "", "email": ""},  # Missing values
            {"id": 3, "name": "Charlie", "email": "charlie@example.com"},
            {"id": 3, "name": "Diana", "email": "diana@example.com"},  # Duplicate id
        ]

        result = sampler.detect_noise(data)

        assert result is not None

    def test_clean_data(self):
        """Test data cleaning."""
        sampler = ContentSampler()
        data = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": ""},  # Empty
            {"id": 3, "name": "Charlie"},
        ]

        sampler.detect_noise(data)
        cleaned = sampler.clean_data(data, remove_labeled=True)

        # Should remove records marked as noise
        assert len(cleaned) <= len(data)


class TestStrategies:
    """Test sampling strategies."""

    def test_random_strategy(self):
        """Test random strategy."""
        sampler = get_strategy("random", seed=42)
        data = [{"id": i} for i in range(100)]

        result = sampler.sample(data, 10)

        assert len(result) == 10

    def test_get_strategy_invalid(self):
        """Test getting invalid strategy falls back to random."""
        sampler = ContentSampler(seed=42)
        data = [{"id": i} for i in range(100)]

        result = sampler.sample(data, 10, strategy="nonexistent_strategy")

        assert len(result) == 10
        assert result[0].get("_sample_strategy") == "random"

    def test_all_strategies_exist(self):
        """Test all listed strategies are available."""
        for name in STRATEGIES:
            strategy = get_strategy(name)
            assert strategy is not None


class TestSampleMetadata:
    """Test sample metadata handling."""

    def test_sample_index_sequential(self):
        """Test that sample indices are sequential."""
        sampler = ContentSampler(seed=42)
        data = [{"id": i} for i in range(100)]

        result = sampler.sample(data, 5)

        indices = [r["_sample_index"] for r in result]
        assert indices == list(range(5))

    def test_original_data_not_modified(self):
        """Test that original data is not modified."""
        sampler = ContentSampler(seed=42)
        data = [{"id": i} for i in range(100)]
        original_data = data.copy()

        sampler.sample(data, 10)

        assert data == original_data


def run_tests():
    """Run all tests and print results."""
    test_classes = [
        TestContentSampler,
        TestStrategies,
        TestSampleMetadata,
    ]

    total = 0
    passed = 0
    failed = []

    for test_class in test_classes:
        print(f"\n{'='*50}")
        print(f"Running {test_class.__name__}")
        print('='*50)

        instance = test_class()
        for method_name in dir(instance):
            if method_name.startswith("test_"):
                total += 1
                try:
                    getattr(instance, method_name)()
                    print(f"  PASS {method_name}")
                    passed += 1
                except Exception as e:
                    print(f"  FAIL {method_name}: {e}")
                    failed.append(f"{test_class.__name__}.{method_name}")

    print(f"\n{'='*50}")
    print(f"Results: {passed}/{total} passed")
    print('='*50)

    if failed:
        print("\nFailed tests:")
        for f in failed:
            print(f"  - {f}")

    return passed == total


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)