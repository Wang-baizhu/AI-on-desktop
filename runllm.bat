@echo off
cd /d "%~dp0"

set PYTHONPATH=%CD%

start "" "D:\Conda\envs\lang\pythonw.exe" "textshot.py"
start "" "D:\Conda\envs\lang\python.exe" "update_knowledge.py"
if %ERRORLEVEL% neq 0 (
    echo update_knowledge.py failed to execute.
    goto end
) else (
    echo update_knowledge.py executed successfully.
)

"D:\Conda\envs\lang\pythonw.exe" "main.py"
if %ERRORLEVEL% neq 0 (
    echo main.py failed to execute.
    goto end
) else (
    echo main.py executed successfully.
)

:end
pause