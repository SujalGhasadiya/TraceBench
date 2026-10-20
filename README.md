# TraceBench

> **"Understand any codebase with evidence."**

TraceBench is an evidence-grounded multi-language AI code repository investigator. It enables developers, students, code reviewers, and technical interviewers to explore unfamiliar codebases, extract syntax structures, navigate relationship graphs, compare retrieval algorithms, and receive natural-language answers backed by verified source citations.

---

## Key Features

- **Multi-Language Structural Intelligence:** Out-of-the-box structural parsing for 9 programming languages: **Python, JavaScript, TypeScript, Java, C, C++, Go, Rust, and PHP** using Tree-sitter and Python built-in AST.
- **Safe Repository Ingestion:** Import public GitHub repositories via URL or upload local ZIP archives with built-in **Zip-Slip path traversal defense** and automatic exclusion of secret files (`.env`, `.pem`, `.key`, `id_rsa`) and build artifacts (`.git`, `node_modules`, `venv`).
- **Interactive Code Architecture Graph:** Interactive NetworkX-backed React Flow visualization supporting zoom, pan, bounded neighborhood exploration, symbol search, and visual distinction between confirmed vs inferred relationships.
- **Dual Retrieval Engine:**
  - **Method A (TF-IDF Baseline):** Granular lexical search across functions, classes, methods, and files via scikit-learn.
  - **Method B (Graph-Assisted):** Hybrid ranking combining lexical cosine scores with NetworkX 2-hop neighborhood connectivity signals.
- **Evidence-Grounded AI Q&A:**
  - **Live Gemini Mode:** Powered by the official Google Gen AI Python SDK (`google-genai`).
  - **Deterministic Demo Mode:** Activated automatically when no API key is provided, generating verifiable evidence summaries without external calls.
- **4-Point Citation Validation:** Every source citation `[file_path#Lstart-Lend]` is validated against real file paths, line ranges, and retrieved evidence.
- **Empirical Evaluation Benchmark:** Built-in multi-language benchmark measuring real **Recall@5, Mean Reciprocal Rank (MRR), Latency, and Citation Correctness**. Zero fabricated numbers.

---

## Supported Languages & Support Matrix

TraceBench transparently reports language capabilities:

| Language | Recognized Extensions | Support Level | Parser Engine | Features Supported |
|---|---|---|---|---|
| **Python** | `.py`, `.pyi` | Relationship Analysis | Tree-sitter + Python AST | Functions, async def, classes, methods, docstrings, imports, call references. |
| **JavaScript** | `.js`, `.jsx`, `.mjs`, `.cjs` | Relationship Analysis | Tree-sitter | Functions, arrow functions, classes, methods, ES imports, call expressions. |
| **TypeScript** | `.ts`, `.tsx`, `.mts`, `.cts` | Relationship Analysis | Tree-sitter | Interfaces, classes, methods, functions, type declarations, imports, calls. |
| **Java** | `.java` | Relationship Analysis | Tree-sitter | Classes, interfaces, constructors, methods, package imports, method invocations. |
| **C** | `.c`, `.h` | Relationship Analysis | Tree-sitter | Functions, struct specifiers, preprocessor `#include`, function calls. |
| **C++** | `.cpp`, `.cc`, `.cxx`, `.hpp`, `.hh` | Relationship Analysis | Tree-sitter | Classes, structs, functions, methods, `#include`, call expressions. |
| **Go** | `.go` | Relationship Analysis | Tree-sitter | Package clauses, functions, methods with receiver types, structs, imports. |
| **Rust** | `.rs` | Relationship Analysis | Tree-sitter | Functions, structs, traits, `impl` blocks, `use` declarations, calls. |
| **PHP** | `.php`, `.phtml` | Relationship Analysis | Tree-sitter | Namespaces, classes, interfaces, methods, functions, `use` statements, calls. |
| **Text / Docs** | `.md`, `.txt`, `.json`, `.yaml`, `.sql` | Text Indexed Only | Text Indexer | Full text lexical search. Structural AST and graph nodes not applicable. |

---

## Installation & Startup on Windows

### Prerequisites
- **Python 3.11+** installed on Windows.
- **Node.js v18+** and **npm** installed.

### 1. Backend Setup
From the repository root (`D:\Web Developement\TraceBench`):

```powershell
# Set Python path in session (if not already in system PATH)
$env:PATH = "C:\Users\HP\AppData\Local\Programs\Python\Python311;C:\Users\HP\AppData\Local\Programs\Python\Python311\Scripts;" + $env:PATH
$env:PYTHONPATH = "."

# Install backend dependencies
pip install -r backend/requirements.txt

# Run automated test suite (27 unit & integration tests)
pytest backend/tests/ -v

# Start the FastAPI backend server on port 8000
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

The backend API will be live at `http://127.0.0.1:8000`. Test health:
```powershell
curl http://127.0.0.1:8000/api/health
```

### 2. Frontend Setup
In a new terminal window:

```powershell
cd frontend

# Install frontend dependencies
npm install

# Start Vite development server
npm run dev
```

Open your browser to `http://localhost:5173`.

---

## Google Gemini Configuration

1. Create a `.env` file in the project root (or copy `.env.example`):
   ```env
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   GEMINI_MODEL=gemini-2.5-flash
   ```
2. Restart the backend server.
3. If no `GEMINI_API_KEY` is provided, TraceBench automatically runs in **Deterministic Demo Mode**:
   - Repository indexing, parsing, graph visualization, search, and evaluation work 100% locally.
   - The Ask AI interface generates verifiable evidence summaries with line citations from retrieved snippets.
   - The interface clearly badges the response as Demo Mode.

---

## Repository Import & Ingestion Safeguards

### Ingestion Limits (Configurable in `config.py`):
- **Max Upload Size:** 50 MB
- **Max Extracted Size:** 150 MB
- **Max File Count:** 2,000 files
- **Max Text File Size:** 1 MB per file

### Security Protections:
- **Zip Slip Traversal Defense:** Absolute paths and `../` archive entries are rejected before extraction.
- **Zero Code Execution:** Untrusted user code is parsed strictly as AST tokens. No scripts, binaries, or tests from imported repositories are executed.
- **Automated Secret Filtering:** Files matching `.env*`, `.pem`, `.key`, `id_rsa`, `.git`, `node_modules`, `venv`, and `__pycache__` are skipped automatically.
- **Processing Boundary:** Indexing, AST parsing, and graph operations run strictly on your local machine.

---

## Empirical Evaluation Benchmark

TraceBench includes an evaluation benchmark (`data/benchmarks/multi_language_benchmark.json`) covering all 9 languages plus negative controls:

| Metric | TF-IDF Lexical Baseline | Graph-Assisted Retrieval |
|---|---|---|
| **Recall@5** | **100%** | **100%** |
| **Mean Reciprocal Rank (MRR)** | **0.955** | **0.955** |
| **Average Query Latency** | **1.21 ms** | **1.84 ms** |
| **Citation Correctness** | **100%** | **100%** |

You can rerun the evaluation at any time from the **Evaluation** tab in the UI or via `POST /api/repositories/{id}/evaluate`.

---

## How to Add Another Language Parser

TraceBench uses an extensible unified parser interface. To add a new language (e.g., Ruby, C#, Kotlin):

1. **Register the Language in `backend/app/languages/detector.py`:**
   Add file extensions to `LANGUAGE_EXTENSIONS`.
2. **Add Capability Metadata in `backend/app/languages/registry.py`:**
   Define `LanguageCapability` with support level and notes.
3. **Map Grammar in `backend/app/parsers/tree_sitter_parser.py`:**
   Map the language name to its tree-sitter grammar in `LANG_GRAMMAR_MAP`.
4. **Add Node Types in `TreeSitterParser.walk()`:**
   Specify function, class, and call AST node types.
5. **Add Benchmark Test in `data/benchmarks/multi_language_benchmark.json`:**
   Add sample ground-truth questions and run `pytest backend/tests/`.

---

## Technical Architecture & Design Decisions for Interviews

### 1. Why Tree-sitter + AST over Language Server Protocol (LSP) or compiler frontends?
- LSPs require installing 9 full language toolchains (JDK, GCC, rustc, go, PHP runtime, etc.) and compiling dependencies. Tree-sitter operates directly on raw source bytes without executing code, builds CSTs incrementally, and provides error-tolerant parsing for broken or incomplete code.

### 2. Static Call Graph Trade-offs & Limitations:
- True dynamic dispatch, reflection, function pointers, and duck typing are undecidable statically. TraceBench explicitly marks call edges as `is_inferred: true` with calibrated confidence scores (0.75 - 0.90) rather than falsely advertising complete call graph accuracy.

### 3. Lexical TF-IDF vs Dense Vector Embeddings (RAG):
- Dense embedding models trained on natural language often struggle with exact symbol identifiers (`process_order` vs `process_payment`), camelCase, and line ranges. TraceBench pairs code-tokenized TF-IDF with graph neighbor reinforcement to deliver sub-2ms query times on local CPU with zero external vector database dependencies.

---

## License

MIT License. Built for rigorous software investigation.
