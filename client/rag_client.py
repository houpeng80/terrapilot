from client.chroma_client import similarity_search_from_chromadb

from assistant.model import get_model
from assistant.rag.chroma_manager import get_chroma_client
from assistant.rag.es_manager import create_es_client, es_keyword_search
from assistant.rag.rag_manager import rag_keyword_search, reciprocal_rank_fusion_with_docs
from assistant.tool import rag_search_tool

def get_reciprocal_rank_fusion_with_docs():
    embedding_model = get_model("qwen_embedding")
    chroma_client = get_chroma_client(embedding_model)
    es_client = create_es_client()

    chroma_res = similarity_search_from_chromadb(chroma_client, query, 30)
    es_res = es_keyword_search(es_client, query, 30)

    merged = reciprocal_rank_fusion_with_docs(chroma_res + es_res)
    for merge in merged:
        print("==============")
        print(merge)
        print("==============")

if "__main__" == __name__:
    query = "RDS backup stop"

    # get_reciprocal_rank_fusion_with_docs()

    rerank_res = rag_search_tool("resource", query)
    print(rerank_res)
    for rr in rerank_res:
        print("==============")
        print(rr)
