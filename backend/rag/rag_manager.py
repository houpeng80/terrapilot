import os
from pathlib import Path

from langchain_core.documents import Document

from client.chroma_client import similarity_search_from_chromadb

from assistant.config.config import get_app_config
from assistant.model import get_model
from assistant.rag.chroma_manager import get_chroma_client
from assistant.rag.es_manager import create_es_client, es_keyword_search


from sentence_transformers import CrossEncoder

MODEL_PATH = Path(__file__).parents[2] / "models/AI-ModelScope--bge-reranker-v2-m3/snapshots/master"

os.environ["TOKENIZERS_PARALLELISM"] = "false"

def get_cross_encoder() -> CrossEncoder:
    cross_encoder = CrossEncoder(MODEL_PATH, device="cpu", local_files_only=True)
    return cross_encoder

def reciprocal_rank_fusion_with_docs(
        vector_results: list[tuple[Document, float]],
        key_words_results: list[tuple[Document, float]],
        vector_weight:float=0.5,
        key_words_weight:float=0.5,
        k=60):

    if vector_weight + key_words_weight != 1:
        raise ValueError(f"the sum of vector_weight and key_words_weight must be equal to 1")

    """
    融合多个检索结果，保留文档完整信息
    """
    score_dict = {}

    for rank, vector_result in enumerate(vector_results, start=1):
        chunk = vector_result[0]
        if chunk.id not in score_dict:
            score_dict[chunk.id] = {
                "doc": vector_result,
                "score": 0
            }
        score_dict[chunk.id]["score"] += vector_weight * (1 / (k + rank))

    for rank, key_words_result in enumerate(key_words_results, start=1):
        chunk = key_words_result[0]
        if chunk.id not in score_dict:
            score_dict[chunk.id] = {
                "doc": key_words_result,
                "score": 0
            }
        score_dict[chunk.id]["score"] += key_words_weight * (1 / (k + rank))

    # 按分数降序排序
    fused_docs = sorted(score_dict.values(), key=lambda x: x["score"], reverse=True)
    return fused_docs

def rerank(model: CrossEncoder, query: str, documents: list[Document], top_k=5):
    # 准备输入， 问题与每个文档组成配对
    pairs = []
    for doc in documents:
        pairs.append((query, doc.page_content))

    # 模型预测相关性分析
    try:
        scores = model.predict(pairs, show_progress_bar=False)
    finally:
        del model

    # 将文档和分数组合，并按分数从高到低排序
    scored_docs = sorted(zip(documents, scores), key=lambda x: x[1], reverse=True)

    # 返回分数最高的 top_k 个文档
    return [doc for doc, score in scored_docs[:top_k] if score >= get_app_config().rerank_score_min]

def rag_keyword_search(query: str, top_k: int=5) -> list[str]:
    embedding_model = get_model(get_app_config().embedding_model_type)
    chroma_client = get_chroma_client(embedding_model)
    es_client = create_es_client()
    chroma_res = similarity_search_from_chromadb(chroma_client, query, 30)

    es_res = es_keyword_search(es_client, query, 30)

    merged = reciprocal_rank_fusion_with_docs(chroma_res, es_res, 0.5, 0.5)
    merged_res = [merge["doc"][0] for merge in merged]

    rerank_results = rerank(get_cross_encoder(), query, merged_res, top_k=top_k)
    res = [rerank_result.page_content for rerank_result in rerank_results]
    return res
