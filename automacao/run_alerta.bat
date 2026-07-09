@echo off
REM Wrapper de agendamento (Windows Task Scheduler) para o robo de alerta de ocorrencias graves.
REM Aponte a tarefa do Task Scheduler para este arquivo (Acao: "Start a program"),
REM com gatilho repetindo a cada 15-30 minutos (ver automacao/README.md).

set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..

"%PROJECT_ROOT%\venv\Scripts\python.exe" "%SCRIPT_DIR%alerta_grave.py"
