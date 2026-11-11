import os

# 国内网络连不上 huggingface.co，改用国内镜像下载向量模型
# 必须写在 import chromadb / sentence-transformers 之前，否则镜像不生效
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

import chromadb
from chromadb.utils import embedding_functions
from app.config import BASE_DIR

KB_DIR = BASE_DIR / "data" / "kb"
CHROMA_DIR = BASE_DIR / "data" / "chroma"

_collection = None
_embedding_fn = None

def _get_embedding_fn():
    """第一次真正用到时才加载向量模型（否则每次启动都要等几十秒）"""
    global _embedding_fn
    if _embedding_fn is None:
        _embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="BAAI/bge-small-zh-v1.5"
        )
    return _embedding_fn

def get_collection() -> chromadb.Collection:
    """向量库的初始化"""
    global _collection
    if _collection is not None:
        return _collection
    KB_DIR.mkdir(parents=True, exist_ok=True)
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    col = client.get_or_create_collection(
        name="lab_kb",
        embedding_function=_get_embedding_fn(),   # 用中文向量模型
        metadata={"hnsw:space": "cosine"},   # 用余弦距离，检索更稳，也方便算相似度
    )
    if col.count() == 0:
        ids = []
        docs = []
        metas = []
        for path in sorted(KB_DIR.glob("*.md")):
            text = path.read_text(encoding="utf-8").strip()
            if not text:
                continue
            ids.append(path.stem)
            docs.append(text)
            metas.append({"source": path.name})
        if docs:
            col.add(ids=ids, documents=docs, metadatas=metas)
    _collection = col
    return col

def warmup():
    """启动的时候初始化向量库，启动预热"""
    col = get_collection()
    if col.count() > 0:
        col.query(query_texts=["预热"], n_results=1)


def search(query: str, top_k: int = 3) -> str:
    """把用户问题丢进向量库检索，返回拼好的「参考资料」文本"""
    col = get_collection()
    if col.count() == 0:          # 库里没东西，直接返回空字符串
        return ""

    query = (query or "").strip()
    if not query:
        return ""

    # 取回最相关的 top_k 段（库里的条数比 top_k 还少时，不能超过总条数）
    res = col.query(
        query_texts=[query],
        n_results=min(top_k, col.count()),
        include=["documents", "metadatas", "distances"],
    )

    # query 传的是列表，所以结果是"每个问题一组"，[0] 取第一个问题的结果
    docs = (res.get("documents") or [[]])[0]      # 正文列表
    metas = (res.get("metadatas") or [[]])[0]     # 每段对应的元数据列表
    distances = (res.get("distances") or [[]])[0]     # 每段对应的元数据列表

    score_parts = []
    for doc, meta, dist in zip(docs, metas, distances):
        # 余弦空间下：相似度 = 1 - 余弦距离，越接近 1 越相关
        score = 1 - float(dist)
        # 过滤：低于 0.5 直接扔掉，不传给大模型
        if score < 0.5:
            continue
        name = (meta or {}).get("source") or ""
        score_parts.append({"score": score, "content": f"[{name}]\n{doc}"})

    # 按相似度从高到低排序
    score_parts.sort(key=lambda x: x["score"], reverse=True)
    # 只取前2条
    final_parts = [item["content"] for item in score_parts[:2]]
    return "\n\n".join(final_parts)


















