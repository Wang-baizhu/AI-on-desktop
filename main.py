import tkinter as tk
import keyboard
import win32clipboard
import threading
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter.font as tkfont
import json
from tkinter import filedialog, messagebox
import search_module
from model_manager import ModelManager
from ai_responder import AIResponder
from search_module import init_db
from markdown_renderer import render_markdown_window

class ChatBotApp:
    def __init__(self):
        # 使用 ModelManager 管理模型
        self.model_manager = ModelManager()
        self.models = self.model_manager.get_models()
        self.current_model = self.model_manager.get_current_model()
        self.llm = self.model_manager.get_llm()   
        # 搜索模式标识
        self.search_mode_active = False
        self.embeddings = self.model_manager.embeddings
        # 创建UI组件
        # 加载 Markdown 文件并构建搜索模块相关数据
        self.md_folder = "F:/obsidian"        # Markdown 文件所在目录
        self.persist_dir = "./chroma_db"       # 向量数据库保存位置
        # )
        self.conn=init_db(db_path="markdown_docs.db")
        self.docs = search_module.load_titles_from_db(self.conn)
        # 此处可根据需求选择更新或使用现有向量库，此处简单起见直接更新：
        #创建标题索引
        self.vector_db = search_module.get_vector_store(self.docs, self.embeddings, self.persist_dir)
        self.bm25, self.tokenized_corpus = search_module.build_bm25_index(self.docs)
        
        # 初始化状态变量
        self.current_ai_thread = None
        self.stop_generation = False
        self.sidebar_visible = False
        self.conversations = {}
        self.current_conversation = None

        # 初始化界面
        self.root = ttk.Window(themename="litera")
        self.root.title("Modern-AI")
        self.root.geometry("500x600")
        self.root.minsize(500, 600)
        self.root.wm_attributes("-topmost", 1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

        self.create_widgets()
        # 初始化会话管理
        self.new_conversation()

        # 绑定热键
        keyboard.add_hotkey('alt+q', self.activate_and_focus_input)
        keyboard.add_hotkey('alt+s', self.toggle_window)
        keyboard.add_hotkey('alt+f', self.toggle_sidebar)
        keyboard.add_hotkey('alt+q', self.paste_from_clipboard)
        
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)

        # 配置消息样式
        self.chat_history.tag_configure('thinking', 
            foreground='#4a4a4a',
            font=('Segoe UI', 12, 'italic'),
            justify='center',
            spacing3=10)
        
        self.chat_history.tag_configure('termination', 
            foreground='#dc3545',
            font=('Segoe UI', 12, 'italic'),
            justify='center',
            spacing3=10)
        self.prompt_templates_path ="prompt_templates_config.json"
        self.prompt_templates = self.load_config(self.prompt_templates_path) 
        self.user_input.bind("<KeyRelease>", self.on_key_release)


    def create_widgets(self):
        # Top button bar with ttkbootstrap styling
        self.btn_frame = ttk.Frame(self.root, style='secondary.TFrame')
        self.btn_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        # Sidebar frame
        self.sidebar_frame = ttk.Frame(self.root, style='secondary.TFrame')
        
        # Chat history area with enhanced styling
        self.chat_frame = ttk.Frame(self.root)  # 新增容器Frame
        self.chat_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.chat_frame.grid_rowconfigure(0, weight=1)  # 允许垂直扩展
        self.chat_frame.grid_columnconfigure(0, weight=1)  # 允许水平扩展

        # 创建文本区域
        self.chat_history = tk.Text(self.chat_frame, 
                                font=("Segoe UI", 12),
                                wrap=tk.WORD, 
                                padx=10, pady=10,
                                bg="#ffffff", 
                                fg="#212529",
                                borderwidth=1, 
                                relief="solid")
        self.chat_history.grid(row=0, column=0, sticky="nsew")

        # 创建垂直滚动条
        self.chat_scroll = ttk.Scrollbar(self.chat_frame,
                                    orient=tk.VERTICAL,
                                    command=self.chat_history.yview)
        self.chat_scroll.grid(row=0, column=1, sticky="ns")

        # 关联滚动条与文本区域
        self.chat_history.configure(yscrollcommand=self.chat_scroll.set)

        
        # User message style
        self.chat_history.tag_configure('user', 
            background='#e3f2fd',  # Light blue background
            relief='solid',
            borderwidth=1,
            justify='right',
            lmargin1=60,
            lmargin2=60,
            rmargin=20,
            spacing3=10,
            wrap=tk.WORD)
        
        # AI message style
        self.chat_history.tag_configure('ai', 
            background='#f8f9fa',  # Light gray background
            relief='solid',
            borderwidth=1,
            justify='left',
            lmargin1=20,
            lmargin2=60,
            rmargin=60,
            spacing3=10,
            wrap=tk.WORD)

        # Input area with ttkbootstrap styling
        self.input_frame = ttk.Frame(self.root, style='secondary.TFrame')
        self.input_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        self.input_frame.grid_columnconfigure(0, weight=1)
        self.input_frame.grid_columnconfigure(1, weight=0)  # 滚动条固定宽度
        self.input_frame.grid_columnconfigure(2, weight=0)  # 发送按钮固定宽度
        self.input_frame.grid_columnconfigure(3, weight=0)

        self.user_input = tk.Text(self.input_frame, 
            width=4,  # 保持较小的初始宽度
            height=3, # 初始高度为1行
            wrap="word",  # 按词换行
            relief="solid",
            font=("仿宋 Regular",14),
            maxundo=1)  # 限制撤销次数以节省内存
        self.user_input.grid(row=0, column=0,  rowspan=2,sticky="ew", padx=5, pady=5)
        self.user_input.bind("<Return>", self.send_message)
        
        self.send_button = ttk.Button(self.input_frame, text="发送", command=self.send_message,
                                    style='primary.TButton')
        self.send_button.grid(row=0, column=2, padx=5, pady=5)      

        self.toggle_sidebar_btn = ttk.Button(self.btn_frame, text="对话管理",
                                           command=self.toggle_sidebar, style='info.TButton')
        self.toggle_sidebar_btn.pack(side=tk.LEFT, padx=5)
        
        self.system_prompt_var = tk.StringVar(value="选择系统提示词")

        self.system_prompt_templates_path ="system_prompt_templates_config.json"
        self.system_prompt_templates = self.load_config(self.system_prompt_templates_path) 
        
        self.system_prompt_dropdown = ttk.OptionMenu(
            self.btn_frame, self.system_prompt_var, "选择系统提示词", *self.system_prompt_templates.keys()
        )
        self.system_prompt_dropdown.pack(side=tk.LEFT, padx=5)
        # 新增：模式下拉菜单（3种模式）
        self.mode_options = ["不搜索模式", "仅搜索模式", "RAG模式"]
        self.search_mode_var = tk.StringVar(value="不搜索模式")
        self.mode_dropdown = ttk.OptionMenu(self.input_frame, self.search_mode_var, "不搜索模式", *self.mode_options)
        self.mode_dropdown.grid(row=1, column=2, columnspan=2, padx=5, pady=5)

        # 用于显示搜索结果的区域（初始时不显示）
        self.search_result_frame = ttk.Frame(self.root, style='secondary.TFrame')

        # Sidebar toggle button

        self.export_button = ttk.Button(self.input_frame, text="导出", command=self.export_conversation, style='success.TButton')
        self.export_button.grid(row=0, column=3, padx=5, pady=5)
        # Model下拉菜单
        self.model_var = tk.StringVar(value=self.current_model)
        self.model_dropdown = ttk.OptionMenu(self.btn_frame, self.model_var, 
                                           self.current_model, *self.models,
                                           command=self.switch_model,
                                           style='primary.TMenubutton')

        # Top button bar with ttkbootstrap styling
        self.model_dropdown.pack(side=tk.RIGHT, padx=5)
        # 创建滚动条
        # 添加导出按钮

        self.input_scrollbar = ttk.Scrollbar(self.input_frame, orient=tk.VERTICAL, command=self.user_input.yview)
        self.input_scrollbar.grid(row=0, column=1,  rowspan=2,sticky="ns")
        self.user_input.configure(yscrollcommand=self.input_scrollbar.set)

        # 将滚动条与输入框关联


    def show_search_result(self, content):
        """显示搜索结果的浮动窗口，并将 Markdown 格式的笔记渲染为 HTML 显示"""
        if hasattr(self, 'search_result_window') and self.search_result_window.winfo_exists():
            self.search_result_window.destroy()
        
        # 将 reset_send_button 作为回调函数传入
        self.search_result_window = render_markdown_window(
            parent=self.root, 
            content=content, 
            title="搜索结果",
            on_close_callback=self.reset_send_button
        )

    
    def on_search_window_close(self):
        """搜索结果窗口关闭时重置发送按钮"""
        self.search_result_window.destroy()
        self.reset_send_button()

    def reset_send_button(self):
        """将发送按钮恢复为默认状态"""
        self.send_button.configure(style='primary.TButton', text="发送", command=self.send_message)


    def switch_model(self, selected_model):
        """调用 ModelManager 切换模型"""
        self.model_manager.switch_model(selected_model)
        self.current_model = self.model_manager.get_current_model()
        self.llm = self.model_manager.get_llm()
        

    def on_key_release(self, event):
        # 在一个函数中处理所有按键释放事件
        self.check_for_prompt_trigger(event)
        self.on_input_change(event)

    def on_input_change(self, event):
        # 调用原有的提示词检查
        self.check_for_prompt_trigger(event)
        
        # 获取输入框和文本内容
        text = self.user_input.get("1.0", tk.END)
        font = tkfont.Font(font=self.user_input['font'])
        
        # 获取输入框的可用宽度，减去所有边距
        # borderwidth * 2 考虑左右边框
        # 10 是默认的内部 padding
        # 额外加上 5 像素的缓冲区
        border_width = float(self.user_input.cget('borderwidth'))
        available_width = (self.user_input.winfo_width() 
                        - (border_width * 2) 
                        - 2  # 内部 padding
                        - 5)  # 额外缓冲
        
        # 计算当前行的像素宽度
        lines = text.split('\n')
        max_height = 1
        
        for line in lines:
            # 计算当前行的像素宽度
            pixel_width = font.measure(line)
            
            # 计算这行文本需要的行数
            needed_lines = (pixel_width // available_width) + 1
            max_height = max(max_height, needed_lines)
        
        # 限制最大高度为6行
        needed_height = min(max_height, 6)

        # 更新文本框高度
        current_height = self.user_input.cget("height")
        if int(current_height) != needed_height:
            self.user_input.configure(height=max(3, needed_height))
            self.user_input.see(tk.END)



    def export_conversation(self):
        """导出当前对话历史为JSON文件"""
        if self.current_conversation not in self.conversations:
            messagebox.showerror("错误", "没有可导出的对话历史")
            return

        # 获取当前对话数据
        conversation_data = {
            "conversation_name": self.current_conversation,
            "model_used": self.current_model,
            "messages": self.conversations[self.current_conversation]
        }

        # 弹出保存文件对话框
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            title="保存对话历史"
        )

        if not file_path:  # 用户取消保存
            return

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(conversation_data, f, 
                        ensure_ascii=False,  # 保留中文
                        indent=2,  # 美化格式
                        sort_keys=True)
            
            messagebox.showinfo("成功", 
                f"对话历史已成功导出到：\n{file_path}")
        except Exception as e:
            messagebox.showerror("导出失败", 
                f"导出文件时发生错误：\n{str(e)}")

    def export_conversation(self):
        """导出当前对话历史为JSON文件"""
        if self.current_conversation not in self.conversations:
            messagebox.showerror("错误", "没有可导出的对话历史")
            return

        # 准备导出数据（包含元数据）
        conversation_data = {
            "conversation_name": self.current_conversation,
            "model_used": self.current_model,
            "messages": self.conversations[self.current_conversation]
        }

        # 弹出保存对话框
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            title="保存对话历史"
        )

        # 执行保存
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(conversation_data, f, 
                            ensure_ascii=False,
                            indent=2,
                            sort_keys=True)
                messagebox.showinfo("成功", f"对话历史已成功导出到：\n{file_path}")
            except Exception as e:
                messagebox.showerror("导出失败", f"导出文件时发生错误：\n{str(e)}")

    def build_history_prompt(self, conversation_name):
        """构建包含完整对话历史的提示"""
        prompt = ""
        for msg in self.conversations[conversation_name]:
            if msg['type'] == 'user':
                prompt += f"User: {msg['content']}\n"
            elif msg['type'] == 'ai':
                prompt += f"Assistant: {msg['content']}\n"
            elif msg['type'] == 'document':
                prompt += f"请结合此文档进行回答\n{msg['content']}\n"
        prompt += "User: "
        return prompt

    def replace_thinking_status(self):
        """用正式AI消息替换思考提示"""
        if self.current_conversation in self.conversations:
            # 移除最后的思考状态消息
            if self.conversations[self.current_conversation][-1].get('status') == 'thinking':
                self.conversations[self.current_conversation].pop()
                
            # 添加正式AI消息
            self.conversations[self.current_conversation].append({'type': 'ai', 'content': ""})

    def remove_thinking_status(self):
        """移除思考提示"""
        if self.current_conversation in self.conversations:
            if len(self.conversations[self.current_conversation]) > 0:
                if self.conversations[self.current_conversation][-1].get('status') == 'thinking':
                    self.conversations[self.current_conversation].pop()
                    self.load_conversation()

    def activate_and_focus_input(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.user_input.focus_set()

    def execute_search_only(self, query):
        """仅搜索模式：点击发送时只进行搜索，并弹出搜索结果悬浮窗"""
        results = search_module.search_titles_advanced(
            self.vector_db, query, self.docs, self.bm25, self.tokenized_corpus, self.conn, k=3
        )
        if results:
            top_result = results[0][1]["doc"]
            content = (f"标题: {top_result.metadata['title']}\n"
                       f"来源: {top_result.metadata['source']}\n\n"
                       f"{top_result.page_content}")
            # 修改发送按钮样式和命令，使其在搜索结果弹窗打开期间显示“停止”
            self.send_button.configure(style='danger.TButton', text="停止", command=self.reset_send_button)
            self.show_search_result(content)
        else:
            messagebox.showinfo("搜索结果", "未找到匹配的文档。")
            self.reset_send_button()

    def send_message(self, event=None):
        self.i=0
        user_text = self.user_input.get("1.0", tk.END).strip()
        if not user_text:
            return

        # 根据下拉菜单选择的模式分支处理
        mode = self.search_mode_var.get()
        if mode == "仅搜索模式":
            self.execute_search_only(user_text)
            return  # 仅搜索模式下不继续后续LLM对话逻辑
        elif mode == "RAG模式":
            # 在RAG模式下，先进行搜索，并将搜索结果作为上下文插入对话中
            #self.execute_search_only(user_text)
            results = search_module.search_titles_advanced(
                self.vector_db, user_text, self.docs, self.bm25, self.tokenized_corpus, self.conn, k=3
            )
            if results:
                search_context = ""
                doc = results[0][1]["doc"]
                search_context += (f"标题: {doc.metadata['title']}\n"
                                    f"来源: {doc.metadata['source']}\n"
                                    f"{doc.page_content}\n\n")
                # 将搜索结果作为系统信息加入对话
                self.conversations.setdefault(self.current_conversation, [])
                # 移除已有的所有 document 类型的消息
                self.conversations[self.current_conversation].append({
                    'type': 'document',
                    'content': f"{search_context}"
                })
        # “不搜索模式”直接使用原有逻辑

        if self.current_conversation == "未命名对话":
            self.rename_conversation(user_text)

        # 添加用户消息
        self.conversations.setdefault(self.current_conversation, [])
        self.conversations[self.current_conversation].append({'type': 'user', 'content': user_text})
        # 添加初始思考提示
        self.conversations[self.current_conversation].append({
            'type': 'status',
            'content': '我正在思考...😊',
            'status': 'thinking'
        })
        self.load_conversation()
        self.user_input.delete("1.0", tk.END)
        self.on_input_change(event)
        # 启动AI回复线程（流式回复）
        self.stop_generation = False
        self.send_button.configure(style='danger.TButton', text="停止")
        self.send_button.configure(command=self.stop_ai_response)
        self.current_ai_thread = threading.Thread(target=self.get_ai_response)
        self.current_ai_thread.start()

    def get_ai_response(self):
        """
        使用 AIResponder 模块流式获取 AI 回答，并支持自定义格式化处理。
        """
        current_conv = self.current_conversation  # 锁定当前对话名称
        prompt = self.build_history_prompt(current_conv)
        self.conversations[self.current_conversation] = [
            msg for msg in self.conversations[self.current_conversation]
            if msg['type'] != 'document'
        ]
        #print(prompt)
        # 移除思考提示并添加正式 AI 消息
        self.root.after(0, self.replace_thinking_status)
        
        # 定义各个回调函数
        def update_callback(content):
            # 安全更新当前对话内容
            self.safe_update_response(current_conv, content)
        
        def stop_flag():
            # 判断是否需要停止生成
            return self.stop_generation or (current_conv != self.current_conversation)
        
        def error_callback(e):
            self.handle_generation_error(e)
        
        def finalize_callback():
            self.finalize_response()
        
        # 如果需要自定义格式化函数，可在此定义，例如转换为 Markdown 格式
        # def custom_formatter(chunk):
        #     # 示例：直接返回原始 chunk，实际可根据需求做转换处理
        #     return markdown.markdown(chunk)
        custom_formatter = None  # 或者 custom_formatter = custom_formatter
        
        # 初始化 AIResponder，并开始流式获取回答（在新线程中执行）
        responder = AIResponder(self.llm)
        responder.stream_response(
            prompt,
            update_callback=lambda content: self.root.after(0, lambda: update_callback(content)),
            stop_flag=stop_flag,
            error_callback=lambda e: self.root.after(0, lambda: error_callback(e)),
            finalize_callback=lambda: self.root.after(0, finalize_callback),
            custom_formatter=custom_formatter,
            system_prompt=self.system_prompt_templates.get(self.system_prompt_var.get(), "")
        )


    def insert_selected_prompt(self, listbox):
        try:
            # 获取选中的提示词
            selected_index = listbox.curselection()[0]
            selected_name = listbox.get(selected_index)
            selected_prompt = self.prompt_templates[selected_name]

            # 获取当前输入框内容
            user_text = self.user_input.get("1.0", tk.END)

            # 替换 `@` 为选定的提示词
            updated_text = selected_prompt +"\n"+ user_text.replace("@", "", 1)
            # updated_text = user_text.replace("@", selected_prompt, 1)

            # 更新输入框
            self.user_input.delete("1.0", tk.END)
            self.user_input.insert("1.0", updated_text)
            
            # 将光标移到输入框末尾
            self.user_input.mark_set(tk.INSERT, tk.END)
            self.user_input.see(tk.END)

            self.on_input_change(None)
            # 关闭弹出窗口
            self.close_prompt_menu()
        except IndexError:
            pass  # 如果没有选择任何项，不执行操作

    def safe_update_response(self, conv_name, content):
        """线程安全的UI更新"""
        if conv_name == self.current_conversation:
            self.conversations[conv_name][-1]['content'] = content
            self.load_conversation()

    def finalize_response(self):
        """完成响应后的清理"""
        # 更新按钮状态
        self.send_button.config(text="发送", command=self.send_message,
                                    style='primary.TButton')
    
        
        # 重置状态
        self.stop_generation = False
        self.current_ai_thread = None

    def handle_generation_error(self, error):
        """统一处理生成错误"""
        self.remove_thinking_status()
        print(self.add_error_message(str(error)))

    def add_error_message(self, error_content):
        return f"[错误] {error_content}"

    def add_termination_message(self, target_conv):
        """给指定对话添加终止提示"""
        if target_conv in self.conversations:
            # 检查最后一条是否是AI消息且未完成
            conv_messages = self.conversations[target_conv]
            if len(conv_messages) > 0 and conv_messages[-1]['type'] == 'ai':
                # 标记为已中断
                # conv_messages[-1]['interrupted'] = True
                # 添加终止提示
                conv_messages.append({
                    'type': 'system',
                    'content': '[响应已中断]',
                    'style': 'termination'
                })
                # 如果目标对话不是当前对话，也需要更新显示
                self.load_conversation()

    def toggle_sidebar(self):
        if self.sidebar_visible:
            self.sidebar_frame.grid_forget()
            self.sidebar_visible = False
        else:
            self.sidebar_frame.grid(row=0, column=1, rowspan=3, sticky="ns")
            self.sidebar_visible = True
        self.update_conversation_list()

    def new_conversation(self):
        self.last_conversation = self.current_conversation
        if self.current_ai_thread and self.current_ai_thread.is_alive() and self.stop_generation == False:
            self.add_termination_message(self.last_conversation)
            self.stop_generation = True
        self.current_conversation = "未命名对话"
        self.conversations[self.current_conversation] = []
        self.update_conversation_list()
        self.load_conversation()


    def rename_conversation(self, first_message):
        new_name = first_message[:15] + "..." if len(first_message) > 15 else first_message
        if new_name not in self.conversations:
            self.conversations[new_name] = self.conversations.pop(self.current_conversation)
            self.current_conversation = new_name
            self.update_conversation_list()

    def update_conversation_list(self):
        for widget in self.sidebar_frame.winfo_children():
            widget.destroy()

        # Set a fixed width for the sidebar frame
        self.sidebar_frame.configure(width=200)  # Adjust this value as needed
        
        # New conversation button with fixed width
        self.new_conv_button = tk.Button(self.sidebar_frame, text="➕ 新对话", 
                                    command=self.new_conversation,
                                    bg="#4CAF50", fg="white", 
                                    font=("Arial", 12), 
                                    relief="flat",
                                    width=15)  # Set fixed width in characters
        self.new_conv_button.pack(pady=5)

        for conv_name in list(self.conversations.keys()):
            frame = tk.Frame(self.sidebar_frame, bg="#F5F5F5")
            frame.pack(pady=2, padx=2)

            # Set fixed width for conversation button
            conv_button = tk.Button(frame, text=conv_name,
                                command=lambda name=conv_name: self.switch_conversation(name),
                                bg="white", 
                                font=("Arial", 10),
                                relief="flat",
                                width=15)  # Match width with new conversation button
            conv_button.pack(side=tk.LEFT)

            del_button = tk.Button(frame, text="❌",
                                command=lambda name=conv_name: self.delete_conversation(name),
                                bg="red", fg="white",
                                font=("Arial", 10),
                                relief="flat",
                                width=2)  # Small fixed width for delete button
            del_button.pack(side=tk.LEFT)

    def switch_conversation(self, conv_name ): 
                           
        """安全切换对话处理"""
        self.i += 1
        # 如果当前有正在进行的生成任务
        if self.current_ai_thread and self.current_ai_thread.is_alive() and self.stop_generation == False and self.i == 1:
            self.send_button.config(text="发送", command=self.send_message,
                                    style='primary.TButton')
            # 设置停止标志并记录需要终止的对话
            self.stop_generation = True
            last_conv = self.current_conversation           
            # 延迟处理终止提示（等待生成线程退出）
            self.root.after(0, lambda: [
                self.add_termination_message(last_conv),
                self.load_conversation()  # 确保界面刷新
            ])
        
        # 切换到新对话
        self.current_conversation = conv_name
        self.load_conversation()

    def check_for_prompt_trigger(self, event):
        user_text = self.user_input.get("1.0", tk.END).strip()
        #print(f"Current input: {user_text}")
        # 如果输入 `@`，则弹出提示词选择框
        if user_text and user_text[-1] == "@" and not hasattr(self, 'prompt_menu'):  # 防止重复创建菜单
            self.show_prompt_menu()

    def show_prompt_menu(self):
        # 获取输入框的屏幕位置
        x = self.user_input.winfo_rootx()
        y = self.user_input.winfo_rooty() + self.user_input.winfo_height()

        # 创建 Toplevel 窗口（提示词选择框）
        self.prompt_menu = tk.Toplevel(self.root)
        self.prompt_menu.overrideredirect(True)  # 去掉窗口边框
        self.prompt_menu.geometry(f"200x150+{x}+{y}")  # 设定大小和位置
        self.prompt_menu.configure(bg="white")
        
        # 使其始终浮在 UI 之上
        self.prompt_menu.attributes("-topmost", True)

        # 创建列表框
        self.prompt_listbox = tk.Listbox(self.prompt_menu, font=("Arial", 12))
        self.prompt_listbox.pack(fill=tk.BOTH, expand=True)

        # 插入提示词选项
        for name in self.prompt_templates.keys():
            self.prompt_listbox.insert(tk.END, name)

        # 绑定选择事件（双击选项后插入提示词）
        self.prompt_listbox.bind("<Double-Button-1>", lambda event: self.insert_selected_prompt(self.prompt_listbox))
        
        # 为整个窗口和listbox都绑定焦点事件
        self.prompt_menu.bind("<FocusOut>", self.check_focus_lost)
        self.prompt_listbox.bind("<FocusOut>", self.check_focus_lost)
        
        # 绑定鼠标离开事件
        self.prompt_menu.bind("<Leave>", self.check_focus_lost)
        self.prompt_listbox.bind("<Leave>", self.check_focus_lost)
        
        # 将焦点设置到列表框上
        self.prompt_listbox.focus_set()

    def check_focus_lost(self, event):
        # 检查鼠标是否在提示框内
        x, y = self.prompt_menu.winfo_pointerxy()
        widget_under_mouse = event.widget.winfo_containing(x, y)
        
        # 如果鼠标不在提示框或其子控件内，则关闭提示框
        if not (widget_under_mouse == self.prompt_menu or 
                widget_under_mouse == self.prompt_listbox):
            self.close_prompt_menu()
            
    def close_prompt_menu(self, event=None):
        if hasattr(self, 'prompt_menu'):
            self.prompt_menu.destroy()
            delattr(self, 'prompt_menu')
            delattr(self, 'prompt_listbox')

    def insert(self, index, *elements):
        """Insert ELEMENTS at INDEX."""
        self.tk.call((self._w, 'insert', index) + elements)

    def delete_conversation(self, conv_name):
        if conv_name in self.conversations:
            #print(f"删除{conv_name}的对话，内容为{self.conversations[conv_name]}")
            del self.conversations[conv_name]
            if conv_name == self.current_conversation:
                self.new_conversation()
            self.update_conversation_list()

    def load_conversation(self, conv_name=None):
        """支持强制重载指定对话"""
        conv = conv_name or self.current_conversation
        self.chat_history.configure(state='normal')
        self.chat_history.delete(1.0, tk.END)

        if conv in self.conversations:
            for msg in self.conversations[conv]:
                content = msg['content']                
                if msg.get('type') == 'status':
                    self.chat_history.insert(tk.END, f"{content}\n\n", 'thinking')
                elif msg['type'] == 'user':
                    self.chat_history.insert(tk.END, f"You: {content}\n", 'user')
                elif msg.get('type') == 'system':
                    self.chat_history.insert(tk.END, f"{content}\n\n", 'termination')
                elif msg.get('type') == 'document':
                    self.chat_history.insert(tk.END, f"已开启参考文档\n",'document')
                else:
                    self.chat_history.insert(tk.END, f"{self.current_model}:\n {content}\n", 'ai')
        #print(f"Loaded conversation: {conv}\n内容为:{self.chat_history}")
        self.chat_history.configure(state='disabled')
        self.chat_history.see(tk.END)   #视角拉到最后
        
    def stop_ai_response(self):
        """停止生成并立即更新状态"""
        self.stop_generation = True
        self.send_button.configure(style='primary.TButton', text="发送")
        self.send_button.configure(command=self.send_message)
        self.add_termination_message(self.current_conversation)
        self.load_conversation()


    def toggle_window(self):
        if self.root.winfo_viewable():
            self.hide_window()
        else:
            self.show_window()

    def show_window(self):
        self.root.deiconify()
        self.user_input.focus_set()

    def hide_window(self):
        self.root.withdraw()

    def paste_from_clipboard(self):
        win32clipboard.OpenClipboard()
        try:
            if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT):
                clipboard_data = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT).strip()
                self.user_input.insert(tk.END, clipboard_data)
                self.on_input_change(None)
                self.user_input.update_idletasks()
                # 将光标移到输入框末尾 
                self.user_input.mark_set(tk.INSERT, tk.END)
                self.user_input.see(tk.END)
                
                win32clipboard.EmptyClipboard()
        finally:
            win32clipboard.CloseClipboard()

    def load_config(self, config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"加载配置文件出错: {e}")
            return {}

if __name__ == "__main__":
    app = ChatBotApp()
    app.root.mainloop()
