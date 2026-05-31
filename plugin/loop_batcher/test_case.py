"""Test cases for loop_batcher."""

import pytest


class TestLoopBatcher:
    def test_add_single_item(self):
        from plugin.loop_batcher import LoopBatcher

        batcher = LoopBatcher()
        batcher.add("image1.png")

        assert len(batcher.items) == 1
        assert batcher.items[0].input == "image1.png"

    def test_add_chain(self):
        from plugin.loop_batcher import LoopBatcher

        result = LoopBatcher().add("a").add("b").add("c")

        assert len(result.items) == 3

    def test_add_many(self):
        from plugin.loop_batcher import LoopBatcher

        batcher = LoopBatcher()
        batcher.add_many(["img1.png", "img2.png", "img3.png"])

        assert len(batcher.items) == 3

    def test_run_single_action(self):
        from plugin.loop_batcher import LoopBatcher

        batcher = LoopBatcher()
        batcher.add_many([1, 2, 3])

        def double(x):
            return x * 2

        results = batcher.run([double])

        assert results[0].output == 2
        assert results[1].output == 4
        assert results[2].output == 6
        assert batcher.success_count == 3

    def test_run_multiple_actions(self):
        from plugin.loop_batcher import LoopBatcher

        batcher = LoopBatcher()
        batcher.add(5)

        def add_ten(x):
            return x + 10

        def multiply_three(x):
            return x * 3

        results = batcher.run([add_ten, multiply_three])

        assert results[0].output == 45  # (5 + 10) * 3

    def test_run_with_error(self):
        from plugin.loop_batcher import LoopBatcher

        batcher = LoopBatcher()
        batcher.add("valid").add("error")

        def fail_on_error(x):
            if x == "error":
                raise ValueError("boom")
            return x.upper()

        results = batcher.run([fail_on_error])

        assert results[0].output == "VALID"
        assert results[0].error is None
        assert results[1].error == "boom"

    def test_errors_property(self):
        from plugin.loop_batcher import LoopBatcher

        batcher = LoopBatcher()
        batcher.add("ok").add("fail")

        def always_fail(x):
            raise RuntimeError("oops")

        batcher.run([always_fail])

        assert len(batcher.errors) == 2

    def test_clear(self):
        from plugin.loop_batcher import LoopBatcher

        batcher = LoopBatcher()
        batcher.add("item")
        batcher.run([lambda x: x])
        batcher.clear()

        assert len(batcher.items) == 0
        assert len(batcher.results) == 0

    def test_mixed_data_types(self):
        from plugin.loop_batcher import LoopBatcher

        batcher = LoopBatcher()
        batcher.add("text").add({"json": "data"}).add([1, 2, 3])

        def identity(x):
            return x

        results = batcher.run([identity])

        assert results[0].output == "text"
        assert results[1].output == {"json": "data"}
        assert results[2].output == [1, 2, 3]
