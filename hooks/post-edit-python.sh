#!/bin/bash
# ruff на отредактированном Python-файле (заменил flake8).
#
# Вход разбирается ПИТОНОМ, а не jq: jq в системе нет, и с ним хук молча
# пропускал всё — «защита» за ноль миллисекунд и с нулевой пользой (найдено
# 11.10.2026; тот же случай, что у pre-commit-tests.sh 14.08.2026).
#
# Замечание отдаётся КОДОМ 2: у моста ДСХ до ассистента доходит только запрет,
# вывод хука с кодом 0 теряется. Правка уже сделана — в тексте это сказано,
# чтобы «запрет» не читался как «файл не изменён».
# Инструмент проверки не найден — это видно в журнале сторожа при старте
# (канарейка инструментов), а не тонет в тишине.
INPUT=$(cat)
FILE_PATH=$(printf '%s' "$INPUT" | python -c "
import json, sys
try:
    print(json.load(sys.stdin).get('tool_input', {}).get('file_path', ''))
except Exception:
    pass
" 2>/dev/null)
if [ -z "$FILE_PATH" ]; then
  echo "post-edit-python: путь файла во входе не разобран — проверка не выполнялась" >&2
  exit 0
fi
# Предпочитаем ruff из venv проекта — та же версия, что в requirements-dev
RUFF="ruff"
if [ -x "${REGLAMENT_PROJECT_DIR:-.}/venv/Scripts/ruff.exe" ]; then
  RUFF="${REGLAMENT_PROJECT_DIR:-.}/venv/Scripts/ruff.exe"
fi
if [ ! -x "$RUFF" ] && ! command -v ruff >/dev/null 2>&1; then
  echo "post-edit-python: ruff не найден (ни в venv проекта, ни в PATH) — правка не проверена" >&2
  exit 0
fi
# Имя переменной — латиницей: bash не признаёт кириллицу в именах, и подстановка
# "$ВЫВОД" осталась бы текстом — условие стало бы вечно истинным, а хук «кусал» бы
# даже целый файл (найдено 11.10.2026: проверка не выполнялась вовсе).
# Судим по коду возврата: ruff на целом файле печатает «All checks passed!» — это
# не замечание (тот же случай у post-edit-js.sh).
OUT=$("$RUFF" check "$FILE_PATH" 2>&1)
STATUS=$?
if [ "$STATUS" -ne 0 ]; then
  printf 'Замечание проверки после правки (файл уже изменён):\n%s\n' "$OUT" >&2
  exit 2
fi
exit 0
