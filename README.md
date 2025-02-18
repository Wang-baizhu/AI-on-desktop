# 使用

## 第一次使用
1. 配置你的模型（兼容openai标准接口），embedding只支持ollama，配置提示词（可选）
2. 第一次使用请先执行update_knowledge,将更新你的知识库，一开始默认为该目录下的test_markdowns，你也可以切换为你自己的路径（包含md笔记）
3. 然后再执行main.py即可，第一次会加载所有md的标题，如果不想每次都加载，注释search_module的get_vector_store()函数的vector_db.add_documents(docs) ，位于第15行

## 自定义知识库路径
- 替换update_knowledge.py的第132行md_folder = "test_markdowns" 为你自己的markdown根路径

## 更新你的标题索引
1. 需要手动删除该目录下的chroma_db文件夹
2. 如果没有注释search_module的get_vector_store()函数的vector_db.add_documents(docs)，直接执行main即可，会重新加载你的标题索引

# 功能介绍
1. 基本的对话（历史多轮对话管理）
2. 提示词功能
    - 系统提示词：全局的提示词
    - 自定义提示词：通过@快速唤出自定义的提示词
3. 知识库检索功能
    - 仅搜索功能：可以将搜索到的md笔记的最可能的标题直接显示里面的内容
    - RAG功能：可以让大模型结合搜索的内容回答