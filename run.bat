@echo off
cd /d "%~dp0"

set PYTHONPATH=%CD%

echo Running update_knowledge.py...
"python-3.10.6-embed-amd64\python.exe" "update_knowledge.py"
if %ERRORLEVEL% neq 0 (
    echo update_knowledge.py failed to execute.
    goto end
) else (
    echo update_knowledge.py executed successfully.
)

echo Running main.py...
"python-3.10.6-embed-amd64\python.exe" "main.py"
if %ERRORLEVEL% neq 0 (
    echo main.py failed to execute.
    goto end
) else (
    echo main.py executed successfully.
)

:end
pause