#!/bin/bash
# reglament-plugin v1.4.0
# Запуск тестов перед коммитом — блокирует коммит при падении.
# Разбор JSON — на Python: jq в системе нет, и с ним хук молча
# пропускал всё (обнаружено 2026-08-14).
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

cd "$REGLAMENT_PROJECT_DIR"

# Архитектурные контракты (import-linter) — первым: прогон ~2 с,
# конфиг в pyproject.toml (vault «Архитектурные контракты
# import-linter»). PYTHONUTF8 — иначе русское имя контракта в
# консоли Windows превращается в кашу
if [ -x "venv/Scripts/lint-imports.exe" ]; then
  PYTHONUTF8=1 venv/Scripts/lint-imports.exe 2>&1
  if [ $? -ne 0 ]; then
    echo "Архитектурные контракты нарушены — коммит заблокирован" >&2
    exit 2
  fi
fi

# Проверка типов (mypy) — ПЕРЕД тестами: она в секунды (замер
# 2026-08-31: тёплый кэш 0,9–2,3 с, холодный 7,3 с), а тесты ~2 мин;
# провал типов экономит тестовый прогон. mypy стоит только в venv,
# поэтому путь явный (vault «Внедрение статической типизации (mypy)»)
if [ -x "venv/Scripts/python.exe" ]; then
  venv/Scripts/python.exe -m mypy 2>&1
  if [ $? -ne 0 ]; then
    echo "Проверка типов не прошла — коммит заблокирован" >&2
    exit 2
  fi
fi

# Покрытие меряется и локально — тот же порог, что в CI (храповик,
# vault «Порог покрытия тестами — храповик»); накладные расходы ~0.
# Тесты — Python из venv, как mypy выше: в системном Python старые
# библиотеки (DRF 3.16, psycopg2), а в venv, образе и проде — DRF 3.18
# и psycopg 3 (долг №55 реестра). Нет venv — системный Python с
# предупреждением, чтобы новая машина не осталась без коммитов.
PYTEST_PY="venv/Scripts/python.exe"
if [ ! -x "$PYTEST_PY" ]; then
  echo "venv не найден — тесты идут системным Python, версии библиотек могут расходиться с продом" >&2
  PYTEST_PY="python"
fi
"$PYTEST_PY" -m pytest tests/ -x -q --cov=apps --cov-report=term 2>&1
STATUS=$?
if [ $STATUS -ne 0 ]; then
  echo "Тесты не прошли — коммит заблокирован" >&2
  exit 2
fi
exit 0
