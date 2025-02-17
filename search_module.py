import sqlite3
import jieba
from langchain.docstore.document import Document
from langchain_chroma import Chroma
from rank_bm25 import BM25Okapi

# 初始化或连接 SQLite 数据库
def init_db(db_path="markdown_docs.db"):
    conn = sqlite3.connect(db_path)
    return conn

# 创建向量数据库（仅存储标题）
def get_vector_store(docs, embeddings, persist_directory="chroma_db"):
    vector_db = Chroma(persist_directory="chroma_db", embedding_function=embeddings)
    vector_db.add_documents(docs)  #删除完向量表后通过此添加
    return vector_db

# 从数据库加载标题（仅存储在内存中）
def load_titles_from_db(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT file_name, title, level, source FROM markdown_docs")
    rows = cursor.fetchall()
    
    documents = []
    for row in rows:
        file_name, title, level, source = row
        metadata = {"title": f" {title}", "level": level, "source": source}
        doc = Document(page_content=metadata["title"], metadata=metadata)
        documents.append(doc)
    
    return documents

# 从数据库加载文档内容
def load_content_from_db(conn, title):
    cursor = conn.cursor()
    #print(f"Loading content for title: {title}")  # 添加调试信息
    cursor.execute("SELECT content FROM markdown_docs WHERE title=?", (title,))
    result = cursor.fetchone()
    return result[0] if result else ""

# 构建 BM25 索引（仅针对标题）
def build_bm25_index(docs):
    tokenized_corpus = [list(jieba.cut(doc.metadata["title"])) for doc in docs]
    bm25 = BM25Okapi(tokenized_corpus)
    return bm25, tokenized_corpus

# 语义 + 关键词搜索融合
def search_titles_advanced(vector_db, query, docs, bm25, tokenized_corpus, conn, k=3):
    # 1. 语义搜索
    semantic_results = vector_db.similarity_search(query, k=k)
    
    # 2. BM25 搜索
    query_tokens = list(jieba.cut(query))
    bm25_scores = bm25.get_scores(query_tokens)

    # 3. 结合搜索结果
    results = {}
    for i, doc in enumerate(docs):
        title = doc.metadata["title"]
        #print(title)  # 打印标题以调试
        semantic_score = sum(1 for res in semantic_results if res.page_content == title)
        bm25_score = bm25_scores[i]
        final_score = (semantic_score * 0.7) + (bm25_score * 0.3)

        if final_score > 0:
            # 从数据库加载实际内容
            first_line = title.splitlines()[0].strip()
            content = load_content_from_db(conn, first_line)
            #print(content)
            results[title] = {"score": final_score, "doc": Document(page_content=content, metadata=doc.metadata)}

    # 结果排序
    sorted_results = sorted(results.items(), key=lambda x: x[1]["score"], reverse=True)
    return sorted_results
