@echo off
REM 设置工作目录为脚本所在的目录
cd /d "%~dp0"

REM 设置 PYTHONPATH，将当前目录添加到模块搜索路径
set PYTHONPATH=%CD%

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