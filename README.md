# 使用

## 第一次使用
1. 第一次使用请先执行update_knowledge,将更新你的知识库，一开始默认为该目录下的test_markdowns，你也可以切换为你自己的路径（包含md笔记）
2. 然后再执行main.py即可，第一次会加载所有md的标题，如果不想每次都加载，注释search_module的get_vector_store()函数的vector_db.add_documents(docs) ，位于第15行

## 更新你的标题索引
1. 需要手动删除该目录下的chroma_db文件夹
2. 如果没有注释search_module的get_vector_store()函数的vector_db.add_documents(docs)，直接执行main即可，会重新加载你的标题索引
