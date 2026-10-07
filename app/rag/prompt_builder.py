from app.rag.retriever import RetrievedChunk


def build_context_block(chunks: list[RetrievedChunk]) -> str:
    parts = []
    for i, chunk in enumerate(chunks):
        parts.append(f'<document source="{chunk.source}">\n{chunk.text}\n</document>')
    return "<context>\n" + "\n".join(parts) + "\n</context>"


def build_rag_user_prompt(question: str, chunks: list[RetrievedChunk]) -> str:
    context_block = build_context_block(chunks)
    return f"{context_block}\n\n<question>{question}</question>"


if __name__ == "__main__":
    from app.rag.retriever import retrieve

    user_question = "Яка рада уповноважена щодо сел Довгий Ліс та Великі Кліщі?"
    chunks = retrieve(user_question)
    if chunks:
        prompt = build_rag_user_prompt(user_question, chunks)
        print(prompt)