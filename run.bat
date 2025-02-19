@echo off
REM 设置嵌入式 Python 环境的相对路径
set PYTHON_HOME=python-3.10.6-embed-amd64

REM 调用嵌入式 Python 解释器运行脚本
"%PYTHON_HOME%\python.exe" "main.py"

REM 检查脚本是否成功运行
if %ERRORLEVEL% == 0 (
    echo Script executed successfully.
) else (
    echo Script failed to execute.
)

REM 暂停，以便查看输出
pause