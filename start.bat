@echo off
REM 获取当前目录
set SCRIPT_DIR=%~dp0
python "%SCRIPT_DIR%auto_create_diary.py"
