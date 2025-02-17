# ai_responder.py
from langchain_core.messages import HumanMessage, SystemMessage

class AIResponder:
    def __init__(self, llm):
        self.llm = llm

    def stream_response(self, prompt, update_callback, stop_flag, 
                        error_callback, finalize_callback, custom_formatter=None, system_prompt=""):
        full_response = ""
        try:
            # 构建消息格式，包含 system_prompt
            messages = [SystemMessage(content=system_prompt), HumanMessage(content=prompt)]
            
            # 调用流式接口
            for chunk in self.llm.stream(messages):
                if stop_flag():
                    break
                
                # 提取内容（适配不同响应格式）
                content = chunk.content if hasattr(chunk, 'content') else str(chunk)
                
                if custom_formatter:
                    content = custom_formatter(content)
                
                full_response += content
                update_callback(full_response)
                
        except Exception as e:
            error_callback(e)
        finally:
            finalize_callback()
