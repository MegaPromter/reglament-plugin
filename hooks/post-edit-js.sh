#!/bin/bash
# Проверка синтаксиса JS после правки
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.filePath // empty')
if [ -z "$FILE_PATH" ]; then
  exit 0
fi
node --check "$FILE_PATH" 2>&1
exit 0
