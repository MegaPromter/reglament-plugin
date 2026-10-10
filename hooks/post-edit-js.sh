#!/bin/bash
# Проверка синтаксиса JS после правки.
#
# Вход разбирается ПИТОНОМ, а не jq: jq в системе нет, и с ним хук молча
# пропускал всё (найдено 11.10.2026; тот же случай, что у pre-commit-tests.sh
# 14.08.2026).
#
# Замечание отдаётся КОДОМ 2: у моста ДСХ до ассистента доходит только запрет,
# вывод хука с кодом 0 теряется. Правка уже сделана — в тексте это сказано.
# Node не найден — видно в журнале сторожа при старте (канарейка инструментов).
INPUT=$(cat)
FILE_PATH=$(printf '%s' "$INPUT" | python -c "
import json, sys
try:
    print(json.load(sys.stdin).get('tool_input', {}).get('file_path', ''))
except Exception:
    pass
" 2>/dev/null)
if [ -z "$FILE_PATH" ]; then
  echo "post-edit-js: путь файла во входе не разобран — проверка не выполнялась" >&2
  exit 0
fi
if ! command -v node >/dev/null 2>&1; then
  echo "post-edit-js: node не найден — синтаксис правки не проверен" >&2
  exit 0
fi
ВЫВОД=$(node --check "$FILE_PATH" 2>&1)
if [ -n "$ВЫВОД" ]; then
  printf 'Замечание проверки после правки (файл уже изменён):\n%s\n' "$ВЫВОД" >&2
  exit 2
fi
exit 0
