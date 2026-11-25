# Glossary

One name per thing, used the same way in chat, code, API fields and the database. The trap to watch: LangChain's `Document` class is a **page** here, not a document.

| Term | Meaning | Don't call it |
| --- | --- | --- |
| Workspace | An isolated set of documents, keyed by a UUID4 `workspace_id` | user, account, tenant, namespace |
| Sample workspace | The read-only workspace holding the eval corpus | demo data |
| Document | One uploaded file in a workspace, keyed by `document_id`; a row in `documents` | file (except raw bytes), LangChain Document |
| Page | Text of one PDF page (or a whole TXT/MD file); a LangChain `Document` in code | document |
| Chunk | Up to 1,500 characters of a document with its embedding; a row in `chunks` | split, segment, node |
| Corpus | All documents and chunks at rest; also the module that owns them | knowledge base, index |
| Library | The module that turns files into documents: add, list, remove | ingestion service |
| Passage | A chunk returned by a search, with its score | context, hit, result |
| Thread | One conversation, keyed by `thread_id` within a workspace | session, chat |
| Question | What the user typed | prompt, query |
| Standalone question | The question rewritten to stand without history | contextualized query |
| Search query | Text sent to the corpus: the standalone question or its one rewrite | question |
| Grade | The grader's verdict: sufficient, and which passages are relevant | score (that's vector similarity) |
| Rewrite | One new search query after a failed grade | retry |
| Writer, grader, rewriter | The model roles; slots in `Models` | the LLM |
| Citation | A marker `[n]` pointing at one passage, with document, page and snippet | source, reference |
| Snippet | The first 200 characters of a cited passage, for display only | quote |
| Answer | Text whose every marker points at a real passage, with at least one marker | response |
| Refusal | v1's fixed sentence, returned with `refused: true` | error, fallback |
| Daily cap | The global limit on questions per UTC day | quota (that's the module) |
| Golden set | The fixed eval questions in `evals/golden.jsonl` | test data |
