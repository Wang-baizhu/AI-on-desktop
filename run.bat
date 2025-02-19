@echo off
REM 设置 Python 的环境变量
set PYTHONPATH=%~dp0

REM 调用嵌入式 Python 解释器运行脚本
"python-3.10.6-embed-amd64\python.exe" "main.py"

REM 检查脚本是否成功运行
if %ERRORLEVEL% == 0 (
    echo Script executed successfully.
) else (
    echo Script failed to execute.
)

REM 暂停，以便查看输出
pause