# markdown_renderer.py

import markdown
import tkinter as tk
from ttkbootstrap import ttk
from tkhtmlview import HTMLText


def render_markdown_window(parent, content, title="Markdown Preview", width=1000, height=600, on_close_callback=None):
    """
    将 Markdown 文本渲染为 HTML，并在一个新的 Toplevel 窗口中显示。
    
    参数:
      parent: 父窗口（tk.Tk 或 tk.Toplevel）。
      content: Markdown 格式的文本内容。
      title: 窗口标题，默认为 "Markdown Preview"。
      width: 窗口宽度，默认 1000 像素。
      height: 窗口高度，默认 600 像素。
      
    返回:
      新创建的 Toplevel 窗口实例。
    """
    # 将 Markdown 转换为 HTML（支持 fenced_code 和 tables 扩展）
    html_content = markdown.markdown(
        content, 
        extensions=['fenced_code', 'tables']
    )
    
    # 包装 HTML（内联样式，可根据需要调整）
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 10px;">
        <div style="font-family: Consolas, monospace; background-color: #f5f5f5; padding: 5px; 
                    white-space: pre-wrap; word-wrap: break-word;">
            {html_content}
        </div>
    </body>
    </html>
    """
    
    # 创建 Toplevel 窗口
    window = tk.Toplevel(parent)
    window.title(title)
    window.wm_attributes("-topmost", True)
    
    # 定义窗口关闭时的处理函数
    def on_close():
        # 如果传入了回调函数，调用它
        if on_close_callback:
            on_close_callback()
        window.destroy()
    # 当窗口关闭时，执行回调（可选）
    window.protocol("WM_DELETE_WINDOW",on_close)

    # 创建容器 Frame
    container = ttk.Frame(window)
    container.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
    
    # 创建 HTMLText 组件（支持选择文本）
    html_text = HTMLText(container, html=html_content, background="white")
    html_text.pack(expand=True, fill="both", padx=5, pady=5)
    
    # 设置为只读
    html_text.configure(state="disabled")
    
    # 调整窗口大小
    window.update_idletasks()
    window.geometry(f"{width}x{height}")
    
    return window