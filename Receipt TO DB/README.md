Markdown
# 🪐 Unified AI-Native Systems Architecture (UASA)

An open-source, modular framework designed to bridge the gap between unstructured real-world assets, composable execution engines, and dynamic user interfaces. 

---

## 🏗️ Core Architectural Pillars

UASA maps out the entire lifecycle of an AI-native application, moving from raw assets to modular capabilities, tying them together, and dynamically delivering them to the end user:

1. **Gold & Storage (Data Engine):** Converts unstructured real-world noise into structured, validated database records.
2. **Tool Pooler (Capability Pool):** Decouples execution engines into reusable pools (AI Builders/Usagers, Code execution, and APIs).
3. **Process Glue (Orchestration):** The control plane handling low-level states (`Job & Process & Status`) and macro-level execution (`Plan & Guide & Work`).
4. **Agent & Cross-Platform (Delivery UI):** Generates interfaces on the fly via a **Generative GUI Auto Builder** alongside conversational Chat apps.

---

## 🌟 Deep Dive: Receipt TO DB (Local Model Distillation)

The code inside the [`Receipt TO DB`](https://github.com/jlam1983/UASA/tree/2198172b79a24e0b41f0a577a4e855e6e9067d17/Receipt%20TO%20DB) module is a production-grade implementation of the **Gold & Storage** pillar. 

Data is everywhere, but capturing and structuring it has traditionally been a high-friction, manual typing chore. This module solves the bottleneck by leveraging an **In-Context Few-Shot Pipeline** to fine-tune a localized Vision-LLM (`Qwen`), compiling it directly down to a private edge engine (`Ollama`).

[Raw Invoices/Receipts] ──> [Schema Generator] ──> [Baseline Extract] ──> [SQLite DB]
│
▼
[Ollama Edge Engine] <── [Export Modelfile] <── [LoRA Fine-Tune (Qwen)] ─────┘


### 🔄 The 7-Step Pipeline Execution

The pipeline automates data extraction and model distillation through seven sequential scripts:

* **`step1_generate_receipt_prompts.py`**: Analyzes the structural patterns of target documents to build robust, descriptive extraction prompts.
* **`step2_generate_sql_schemas.py`**: Dynamically crafts targeted relational SQL database structures to hold the extracted attributes.
* **`step3_init_sqlite_db.py`**: Initializes the localized, lightweight SQLite storage layer.
* **`step4_extract_and_insert_receipts.py`**: Runs baseline evaluations, processing raw text/images and logging initial relational records into the database.
* **`step5_train_lora_qwen.py`**: Injects structural knowledge into a base `Qwen` vision-language model by training a lightweight **LoRA (Low-Rank Adaptation)** layer using the sample data.
* **`step6_load_lora.py`**: Merges, tests, and evaluates the fine-tuned adapter weights to ensure rigid JSON/schema adherence.
* **`step7_export_to_ollama.py`**: Compiles the final fine-tuned weights into an Ollama-compatible `Modelfile`. This allows any local machine to run high-speed, 100% private inference with zero variable cloud costs.

---

## ⚖️ Open-Core Monetization Blueprint

This framework is built using an open-core commercialization philosophy to balance open-source contribution with sustainable business growth:

* **The Open-Source Core (Free Forever):** The base repository, the 7-step local distillation pipeline, SQLite/Ollama integration scripts, and core schema tools are completely free to clone, modify, and run locally.
* **The Enterprise Layer (Commercial):** * Pre-trained LoRA adapter weights tailored for complex vertical documents (e.g., medical billing, corporate flight logs, customs manifests).
    * Hosted distributed training pipelines (Upload 10 files, download a custom edge model).
    * Dynamic frontend generation using the **GUI Auto Builder** to construct full dashboards from the distilled data schemas.

---

## 🚀 Quick Start (Local Setup)

1. **Clone the Repository:**
   ```bash
   git clone [https://github.com/jlam1983/UASA.git](https://github.com/jlam1983/UASA.git)
   cd UASA/"Receipt TO DB"
Install Dependencies:

Bash
pip install -r requirements.txt
Initialize and Train:
Run scripts step1 through step7 sequentially to build your schemas, train your localized model, and register it directly into Ollama.