@echo off
REM 设置工作目录为脚本所在的目录
cd /d "%~dp0"

REM 设置 PYTHONPATH，将当前目录添加到模块搜索路径
set PYTHONPATH=%CD%

REM 调用嵌入式 Python 解释器运行第一个脚本
echo Running update_knowledge.py...
"python-3.10.6-embed-amd64\python.exe" "update_knowledge.py"
if %ERRORLEVEL% neq 0 (
    echo update_knowledge.py failed to execute.
    goto end
) else (
    echo update_knowledge.py executed successfully.
)

REM 第一个脚本执行成功后，运行第二个脚本
echo Running main.py...
"python-3.10.6-embed-amd64\python.exe" "main.py"
if %ERRORLEVEL% neq 0 (
    echo main.py failed to execute.
    goto end
) else (
    echo main.py executed successfully.
)

:end
REM 暂停，以便查看输出
pause