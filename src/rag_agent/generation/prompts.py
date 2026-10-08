def build_grounded_prompt(
    question: str,
    contexts: list[dict],
) -> str:
    context_blocks = []

    for context in contexts:
        context_blocks.append(
            "\n".join(
                [
                    f"[chunk_id={context['chunk_id']}]",
                    f"[document_version_id={context['document_version_id']}]",
                    f"[chunk_index={context['chunk_index']}]",
                    context["content"],
                ]
            )
        )

    context_text = "\n\n---\n\n".join(context_blocks)

    return f"""You are the Nexus-RAG document question-answering assistant.

Answer the user's question using ONLY the supplied document context.

Rules:
- Do not use outside knowledge.
- Do not invent facts.
- If the supplied context does not contain enough information to answer,
  say that the information is not available in the provided documents.
- Keep the answer concise and factual.
- Do not invent or modify source identifiers.

DOCUMENT CONTEXT:
{context_text}

USER QUESTION:
{question}
"""