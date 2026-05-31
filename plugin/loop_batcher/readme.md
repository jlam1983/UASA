# LoopBatcher

Batch processor that holds multiple items (images, data, etc.) and runs them through a list of actions.

## Concept

```
LoopBatcher
    ├── add("item1")          # queue items
    ├── add("item2")
    ├── add({"json": "data"})
    │
    └── run([action1, action2])  # pipe each item through actions
        │
        item1 → action1 → action2 → output
        item2 → action1 → action2 → output
        ...
```

Each action receives the **output of the previous action** (or the raw item for the first action). Chain transforms together cleanly.

---

## Usage

### Basic — single action chain

```python
from plugin.loop_batcher import LoopBatcher

batcher = LoopBatcher()
batcher.add_many(["img1.png", "img2.png", "img3.png"])

def load_image(path):
    return {"path": path, "loaded": True}

results = batcher.run([load_image])
# results[0].output → {"path": "img1.png", "loaded": True}
```

### Multiple actions — chained

```python
from plugin.loop_batcher import LoopBatcher

batcher = LoopBatcher()
batcher.add("raw_data.json")

def read_file(x):
    with open(x) as f:
        return f.read()

def parse_json(x):
    import json
    return json.loads(x)

def extract_fields(x):
    return {"count": len(x), "data": x}

results = batcher.run([read_file, parse_json, extract_fields])
# Output: {"count": 42, "data": {...}}
```

### Mixed data types

```python
batcher = LoopBatcher()
batcher.add("text_file.txt")
batcher.add({"json": "doc"})
batcher.add([1, 2, 3])

results = batcher.run([lambda x: str(x)])  # all items go through same action
```

### With image_to_json

```python
from plugin.loop_batcher import LoopBatcher
from plugin.image_to_json import ImageToJSONConverter

conv = ImageToJSONConverter()

batcher = LoopBatcher()
batcher.add_many(["receipt1.png", "receipt2.png", "receipt3.png"])

results = batcher.run([
    lambda path: conv.process(path, title="Receipt", use_llm=False),
    lambda result: result["fields"]  # extract just the fields
])

# results[0].output → {"text": "..."}
```

---

## API

### LoopBatcher

| Method | Description |
|--------|-------------|
| `add(item)` | Add one item. Returns self for chaining. |
| `add_many(items)` | Add multiple items at once. |
| `run(actions)` | Run all items through actions sequentially. |
| `run_parallel(actions, workers=4)` | Run in parallel with threads. |
| `clear()` | Clear all items and results. |

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `items` | `list[BatchItem]` | All queued items (before run) |
| `results` | `list[BatchItem]` | Processed items (after run) |
| `errors` | `list[BatchItem]` | Items that raised exceptions |
| `success_count` | `int` | Number of successfully processed items |

### BatchItem

| Field | Type | Description |
|-------|------|-------------|
| `input` | `Any` | Original input item |
| `output` | `Any` | Final output after all actions |
| `error` | `str \| None` | Exception message if failed |
| `processed` | `bool` | Whether run completed (success or fail) |

---

## Project Structure

```
plugin/
└── loop_batcher/
    ├── __init__.py
    ├── readme.md
    ├── batcher.py    # LoopBatcher + BatchItem
    └── test_case.py
```
