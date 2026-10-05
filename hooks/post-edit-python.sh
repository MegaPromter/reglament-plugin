#!/bin/bash
# ruff на отредактированном Python-файле (заменил flake8)
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.filePath // empty')
if [ -z "$FILE_PATH" ]; then
  exit 0
fi
# Предпочитаем ruff из venv проекта — та же версия, что в requirements-dev
RUFF="ruff"
if [ -x "${CLAUDE_PROJECT_DIR:-.}/venv/Scripts/ruff.exe" ]; then
  RUFF="${CLAUDE_PROJECT_DIR:-.}/venv/Scripts/ruff.exe"
fi
"$RUFF" check "$FILE_PATH" 2>&1
exit 0
