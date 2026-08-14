#!/bin/bash
# Запуск тестов перед коммитом — блокирует коммит при падении.
# Разбор JSON — на Python: jq может отсутствовать в системе, а с
# отсутствующим jq хук молча пропускал бы всё.
# [МАСТЕР: {{КОМАНДА_ТЕСТОВ}} заменить командой тестов из анкеты
# проекта; сообщение перевести на язык проекта.]
INPUT=$(cat)
TOOL_INPUT=$(printf '%s' "$INPUT" | python -c "
import json, sys
try:
    print(json.load(sys.stdin).get('tool_input', {}).get('command', ''))
except Exception:
    pass
" 2>/dev/null)
if ! echo "$TOOL_INPUT" | grep -q "git commit"; then
  exit 0
fi

cd "$CLAUDE_PROJECT_DIR"
{{КОМАНДА_ТЕСТОВ}} 2>&1
STATUS=$?
if [ $STATUS -ne 0 ]; then
  echo "Тесты не прошли — коммит заблокирован" >&2
  exit 2
fi
exit 0
