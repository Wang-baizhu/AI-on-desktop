import os
import re
import sqlite3
from langchain.docstore.document import Document

def init_db(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS markdown_docs")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS markdown_docs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT,
            title TEXT,
            level INTEGER,
            source TEXT,
            content TEXT
        )
    ''')
    conn.commit()
    return conn

def extract_md_titles_and_content(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    file_name = os.path.basename(file_path).replace(".md", "")
    
    # 只识别井号后面跟至少一个空格的行（行首匹配），支持1到6级标题
    heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.M)
    
    # 寻找以 ``` 开始和结束的代码块（多行代码块），避免代码块中错误匹配标题
    code_block_pattern = re.compile(r"^```.*$", re.M)
    code_block_spans = []
    in_code_block = False
    block_start = None
    for match in code_block_pattern.finditer(content):
        if not in_code_block:
            in_code_block = True
            block_start = match.start()
        else:
            code_block_spans.append((block_start, match.end()))
            in_code_block = False
            block_start = None
    # 如果代码块未闭合，则认为一直到文件末尾
    if in_code_block and block_start is not None:
        code_block_spans.append((block_start, len(content)))
    
    # 找出不在代码块内的标题匹配
    matches = []
    for match in heading_pattern.finditer(content):
        if any(start <= match.start() < end for start, end in code_block_spans):
            continue  # 跳过代码块内的匹配
        matches.append(match)
    
    docs = []
    # 无论是否存在标题，都先存储一个“全文”文档，标题为文件名，内容为整个文件内容
    docs.append({
        "file_name": file_name,
        "title": file_name,
        "level": 0,
        "source": file_path,
        "content": content.strip()
    })
    
    # 如果没有识别到标题，则直接返回全文文档
    if not matches:
        return docs

    # 使用栈维护标题层级，便于拼接上级标题信息（仅影响标题，不改变内容存储逻辑）
    stack = []
    for i, match in enumerate(matches):
        title_level = len(match.group(1))
        title_text = match.group(2).strip()
        start_index = match.start()
        # 当前标题的内容截止到下一个标题开始处（或文件结尾）
        end_index = matches[i + 1].start() if i < len(matches) - 1 else len(content)
        block_content = content[start_index:end_index].strip()

        # 弹出同级或更低级的标题，保证栈中保存的是当前标题的所有上级标题
        while stack and stack[-1]["level"] >= title_level:
            stack.pop()

        # 生成完整标题：若存在上级标题，则将上级标题内容依次拼接，否则以文件名开头
        if stack:
            full_title = stack[-1]["title"] + title_text
            # 同时保持上级标题内容包含所有子标题的内容
            stack[-1]["content"] += "\n\n" + block_content
        else:
            full_title = file_name + title_text

        current_doc = {
            "file_name": file_name,
            "title": full_title,
            "level": title_level,
            "source": file_path,
            "content": block_content
        }
        docs.append(current_doc)
        stack.append(current_doc)
        
    return docs

def store_docs_in_db(conn, docs):
    cursor = conn.cursor()
    for doc in docs:
        cursor.execute('''
            INSERT INTO markdown_docs (file_name, title, level, source, content)
            VALUES (?, ?, ?, ?, ?)
        ''', (doc["file_name"], doc["title"], doc["level"], doc["source"], doc["content"]))
    conn.commit()

def load_docs_from_db(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT file_name, title, level, source, content FROM markdown_docs')
    rows = cursor.fetchall()
    documents = []
    for row in rows:
        file_name, title, level, source, content = row
        metadata = {"file_name": file_name, "title": title, "level": level, "source": source}
        doc = Document(page_content=content, metadata=metadata)
        documents.append(doc)
    return documents


if __name__ == "__main__":
    db_path = "markdown_docs.db"
    conn = sqlite3.connect(db_path)
    user_input = input("请确定是否更新知识库(y/n):")
    if user_input.lower() == 'y':
        conn = init_db(db_path)
        md_folder = "test_markdowns"
        exclude_folders = {"待整理", "template"}  # 要排除的文件夹名称
        print("知识库开始更新")
        for root, dirs, files in os.walk(md_folder):
            # 从 dirs 列表中移除不需要遍历的目录
            dirs[:] = [d for d in dirs if d not in exclude_folders]
            
            for file in files:
                if file.endswith(".md"):
                    file_path = os.path.join(root, file)
                    docs = extract_md_titles_and_content(file_path)
                    store_docs_in_db(conn, docs)
        print("知识库更新完成")
        conn.close()
    else:
        print("不更新知识库")

