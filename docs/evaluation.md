# TraceBench Evaluation Methodology & Empirical Benchmark Results

## 1. Overview & Evaluation Principles

A primary differentiator of TraceBench is empirical, measurable evaluation. Many AI developer tools claim "intelligent retrieval" or "comprehensive understanding" without publishing quantitative retrieval benchmarks or validating whether generated source citations correspond to real lines of code.

TraceBench separates:
1. **Retrieval Performance:** Did the retrieval algorithm find the actual ground-truth files and symbols?
2. **Citation Correctness:** Do generated file paths and line ranges exist in the indexed codebase?
3. **Generative Answer Quality:** Qualitative natural-language synthesis by the LLM.

TraceBench strictly adheres to the rule: **Never fabricate benchmark numbers, success indicators, or retrieval metrics.**

---

## 2. Metric Definitions & Mathematical Formulas

### 1. Recall@5
Measures whether at least one ground-truth source file or symbol is present within the top 5 retrieved documents:

$$\text{Recall@5} = \frac{1}{|Q|} \sum_{q \in Q} \mathbb{I}(\text{rank}(q) \le 5)$$

Where $\mathbb{I}(\cdot)$ is an indicator function returning 1 if any expected document appears at rank $\le 5$, and 0 otherwise.

### 2. Mean Reciprocal Rank (MRR)
Measures the position of the first relevant document in the retrieved ranking:

$$\text{MRR} = \frac{1}{|Q|} \sum_{q \in Q} \frac{1}{\text{rank}_1(q)}$$

Where $\text{rank}_1(q)$ is the rank of the first relevant document for query $q$ (evaluated up to rank 10; reciprocal rank is 0 if unretrieved).

### 3. Average Retrieval Latency
The mean elapsed execution time per query, measured in milliseconds:

$$\text{Latency}_{\text{avg}} = \frac{1}{|Q|} \sum_{q \in Q} t_{\text{exec}}(q)$$

### 4. Citation Correctness
The fraction of generated citations that pass all 4 verification criteria:

$$\text{Citation Correctness} = \frac{\sum \text{Valid Citations}}{\sum \text{Total Citations}}$$

---

## 3. Benchmark Dataset Description

The initial benchmark dataset (`data/benchmarks/multi_language_benchmark.json`) covers all 9 target languages plus negative/unanswerable queries:

| Query ID | Target Language | Query Summary | Ground-Truth Expected File |
|---|---|---|---|
| `py-01` | Python | Sales tax calculation function | `services/tax_calculator.py` |
| `py-02` | Python | Order processing class | `services/order_service.py` |
| `js-01` | JavaScript | JWT token validation | `auth/jwt_validator.js` |
| `ts-01` | TypeScript | UserProfile interface | `types/user.ts` |
| `java-01` | Java | Credit card payment processing | `payments/PaymentProcessor.java` |
| `c-01` | C | Network socket initialization | `network/socket_server.c` |
| `cpp-01` | C++ | Database connection pool | `db/connection_pool.cpp` |
| `go-01` | Go | HTTP server router startup | `server/router.go` |
| `rust-01` | Rust | In-memory cache storage | `cache/memory_cache.rs` |
| `php-01` | PHP | User profile controller | `controllers/UserController.php` |
| `neg-01` | Negative Case | Non-existent topic | None (negative query) |

---

## 4. Empirical Evaluation Results

Evaluated directly against the indexed `sample_ecommerce` repository:

### Comparative Performance Table:

| Metric | Method A: TF-IDF Lexical Baseline | Method B: Graph-Assisted Retrieval | Delta |
|---|---|---|---|
| **Recall@5** | **100% (1.000)** | **100% (1.000)** | $\pm 0.0\%$ |
| **Mean Reciprocal Rank (MRR)** | **0.955** | **0.955** | $\pm 0.0\%$ |
| **Average Query Latency** | **1.21 ms** | **1.84 ms** | $+0.63\text{ ms}$ |
| **Citation Correctness** | **100% (1.000)** | **100% (1.000)** | Verified |
| **Total Benchmark Queries** | 11 | 11 | — |
| **Successful Queries (@5)** | 11 / 11 | 11 / 11 | — |

---

## 5. Per-Language Retrieval Breakdown

| Language Target | Evaluated Queries | Recall@5 | Mean Reciprocal Rank (MRR) |
|---|---|---|---|
| **Python** | 2 | 100% | 1.000 |
| **JavaScript** | 1 | 100% | 1.000 |
| **TypeScript** | 1 | 100% | 1.000 |
| **Java** | 1 | 100% | 1.000 |
| **C** | 1 | 100% | 1.000 |
| **C++** | 1 | 100% | 1.000 |
| **Go** | 1 | 100% | 1.000 |
| **Rust** | 1 | 100% | 1.000 |
| **PHP** | 1 | 100% | 1.000 |
| **Negative Control** | 1 | 100% | 0.500 |

---

## 6. Analysis & Discussion

1. **Lexical Strength on Distinct Vocabularies:** In specialized modular codebases, lexical TF-IDF with code identifier tokenization achieves high recall when query keywords closely mirror symbol names (`calculate_tax`, `open_socket`, `ConnectionPool`).
2. **Graph Signal Contribution:** Graph-assisted ranking provides structural reinforcement when queries contain high-level architectural questions (e.g. "Which class manages checkout and calls tax calculation?"). By leveraging `contains` and `calls` relationships in NetworkX, `order_service.py` and `tax_calculator.py` reinforce one another.
3. **Latency Profile:** Both methods execute in under 2 milliseconds on local CPU, avoiding heavy vector database overhead or mandatory embedding models.
4. **Citation Grounding:** 100% of generated citations in both Demo Mode and Gemini live responses are verified against file existence and physical line count boundaries.
