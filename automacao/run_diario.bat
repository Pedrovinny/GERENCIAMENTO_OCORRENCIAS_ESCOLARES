@echo off
REM Wrapper de agendamento (Windows Task Scheduler) para o robo de panorama diario.
REM Aponte a tarefa do Task Scheduler para este arquivo (Acao: "Start a program").

set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..

"%PROJECT_ROOT%\venv\Scripts\python.exe" "%SCRIPT_DIR%bot.py"
