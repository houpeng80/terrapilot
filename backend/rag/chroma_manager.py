from pathlib import Path

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

resource_path = {
    "data_source": "docs/data-sources",
    "resource": "docs/resources",
}

PERSIST_DIRECTORY = Path(__file__).parents[2] / "vector_db"

def get_chroma_client(model: OpenAIEmbeddings) -> Chroma:
    chroma_client = Chroma(
        collection_name="my_collection",
        embedding_function=model,
        persist_directory=PERSIST_DIRECTORY
    )
    return chroma_client

def add_docs_to_chroma(chroma_client: Chroma, documents: list[tuple[str, Document]]) -> None:
    batch_size = 10
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        add_documents_ids = [document[0] for document in batch]
        add_documents = [document[1] for document in batch]
        chroma_client.add_documents(documents=add_documents, ids=add_documents_ids)

def delete_docs_from_chroma(chroma_client: Chroma, documents: list[Document]) -> None:
    batch_size = 10
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        chroma_client.delete(batch)

def similarity_search_docs_from_chroma(chroma_client: Chroma, query: str, query_size: int) -> list[Document]:
    return chroma_client.similarity_search(query, k=query_size)

def similarity_search_docs_with_score_from_chroma(chroma_client: Chroma, query: str, query_size: int =20) -> list[tuple[Document, float]]:
    # return chroma_client.similarity_search_with_score(query, k=query_size)
    return chroma_client.similarity_search_with_relevance_scores(query, k=query_size)
