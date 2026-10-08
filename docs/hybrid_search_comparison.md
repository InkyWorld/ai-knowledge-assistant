# Hybrid vs Dense Search Evaluation

**Date:** October 8, 2026  
**Corpus:** Qdrant collection `knowledge_base` (66 points, 12 documents).  
**Models:** `gemini-embedding-2` (1536 dims), sparse `Qdrant/bm25`, RRF fusion.  
**Metric:** Expected document in top-3 (`limit=3`).

---

### Executive Summary

- **5 Exact Queries (Number + Date):** Dense 2/5 | Hybrid **5/5**
- **5 Semantic Queries (Paraphrased):** Dense 5/5 | Hybrid 5/5
- **Total:** Dense **7/10** | Hybrid **10/10**

Hybrid successfully fixed Dense failures in 3 cases (E1, E3, E4). On semantic queries, both performed equally well without regression.

---

### Key Findings

- **Exact Queries:** Dense failed on queries with document numbers (e.g., `Постанова № 1187`) because all legal documents share identical boilerplate headers like `ЗАТВЕРДЖЕНО постановою...`. Dense vectors became confused by this similarity, whereas BM25 precisely matched specific numbers and dates.
- **Semantic Queries:** Both Dense and Hybrid achieved 100% success (5/5). Hybrid matched or exceeded Dense's confidence scores through RRF fusion without losing semantic accuracy.
