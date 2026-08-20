# ADR 0002: Evidence-First LLM Design

## Status

Accepted

## Context

The AI Analyst feature allows users to ask natural language questions about system data. Large language models (LLMs) are powerful but prone to hallucination—generating plausible-sounding but false claims.

Key concerns:
- Misinformation risk in decision-support context
- User over-trust in AI responses
- Lack of provenance for claims
- Liability if incorrect information leads to poor decisions

## Decision

**The AI Analyst must use retrieval-first, evidence-grounded design.** Every response must be derived exclusively from retrieved facts, with citations linking each claim to specific evidence IDs.

Implementation rules:
1. **Retrieve before generating**: Search entities, anomalies, observations first
2. **Empty retrieval → refusal**: If no evidence found, return "Insufficient evidence" without calling LLM
3. **Grounded prompt construction**: Include only retrieved facts in prompt context
4. **Citation requirement**: Response must include list of evidence IDs used
5. **Confidence scoring**: Attach confidence level based on evidence quality
6. **Limitations disclosure**: Explicitly state what the model cannot know
7. **Mock fallback**: If no API key available, use deterministic rule-based responses

Prompt template:
```
You are an AI analyst answering questions about a decision intelligence system.
Answer ONLY using the following retrieved facts. If the facts are insufficient, say so.

Retrieved Evidence:
{evidence_json}

Question: {user_query}

Response format:
{{
  "answer": "...",
  "citations": ["obs_123", "entity_456"],
  "confidence": "high|medium|low",
  "limitations": "..."
}}
```

## Consequences

### Positive
- Eliminates hallucination (claims tied to evidence)
- Builds user trust through transparency
- Enables audit trail (which evidence supported which answer)
- Graceful degradation (mock mode without API key)
- Defensible design (can explain why a claim was made)

### Negative
- Limited to answering questions about stored data only
- Cannot provide general knowledge or opinions
- Retrieval quality directly impacts answer quality
- Additional latency for retrieval step

### Mitigations
- Clear UI messaging: "I can only answer based on system data"
- Retrieval optimization (indexes, caching)
- Hybrid search (keyword + semantic when available)

## Alternatives Considered

### Option A: Direct LLM Query (Rejected)
Send user query directly to LLM with minimal context.
- **Problem**: High hallucination risk, no citations, un-auditable

### Option B: Fine-Tuned Model (Rejected)
Fine-tune LLM on system data schema.
- **Problem**: Still hallucinates, expensive to maintain, stale data

### Option C: RAG with Vector Store (Deferred)
Use embeddings + vector database for semantic retrieval.
- **Problem**: Adds complexity, requires external service
- **Future**: May implement when production deployment justified

## Compliance

This design aligns with:
- **AI Analyst Grounding Policy** in `docs/SECURITY_MODEL.md`
- **Explainability requirements** (every claim has source)
- **Audit trail requirements** (queries logged with evidence)

## References

- `backend/llm/llm_analyst.py`
- `backend/api/analyst_routes.py`
- `docs/SECURITY_MODEL.md` § AI Analyst Grounding Policy
- `README.md` § Evidence-First AI Analyst

---

*ADR authored: 2025-01-15*
*Review cycle: Annual*
