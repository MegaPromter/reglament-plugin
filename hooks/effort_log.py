#!/usr/bin/env python3
"""Замер усилия (effort) — строка в журнал по данным сессии.

Читает журнал текущей сессии Claude Code (файлы .jsonl в папке
~/.claude/projects/<код пути проекта>/), берёт срез от начала
задачи (отметка «начато» в табло) и дописывает строку в
docs/vault/_meta/Журнал замеров усилия.md.

Запуск: python .claude/hooks/effort_log.py [--dry-run]
Вызывается из close_task.py перед закрывающим коммитом.
Ничего не решает и ничего не меняет, кроме файла журнала:
при любой нехватке данных молча отказывается, чтобы не сорвать
закрытие задачи.
"""

import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

for _поток in (sys.stdout, sys.stderr):
    if hasattr(_поток, "reconfigure"):
        _поток.reconfigure(encoding="utf-8")

КОРЕНЬ = Path(__file__).resolve().parents[2]
ТАБЛО = КОРЕНЬ / ".claude" / "task-state.json"
ЖУРНАЛ = КОРЕНЬ / "docs" / "vault" / "_meta" / "Журнал замеров усилия.md"

# Запуск тестов: «pytest» в начале команды или сегмента после
# && ; | — иначе в счёт попадёт любая команда, где это слово
# встречается просто внутри текста.
ЗАПУСК_ТЕСТОВ = re.compile(
    r"(?:^|&&|;|\|)\s*(?:\S*python\S*\s+(?:-\S+\s+)*-m\s+)?pytest\b"
)

ШАПКА = """---
тип: meta
статус: действует
создано: 2026-08-22
обновлено: 2026-08-22
---

# Журнал замеров усилия (effort)

Замеры пишет скрипт `effort_log.py` при закрытии задачи — руками
ничего вводить не нужно. Колонка «класс» заполняется вручную при
разборе: мелкая правка / миграция модуля / бизнес-правила и т. п.

Правило чтения и смысл колонок — в заметке
[[Журнал замеров усилия (effort)]].

| Дата | Задача | Класс | Модель | Усилие | Тесты (всего/красных) | Хуки | Реплик | Токены вых./размышл. | Минут |
|---|---|---|---|---|---|---|---|---|---|
"""


def папка_сессий():
    """Каталоги журналов сессий этого проекта.

    Claude Code кодирует путь проекта, заменяя все символы, кроме
    букв и цифр, на дефис: D:\\Program\\Body\\planapp_django →
    D--Program-Body-planapp-django. Рабочие копии (git worktree)
    получают тот же префикс с суффиксом ветки — берём и их.
    """
    код = re.sub(r"[^A-Za-z0-9]", "-", str(КОРЕНЬ))
    корень_сессий = Path.home() / ".claude" / "projects"
    if not корень_сессий.exists():
        return []
    return [п for п in корень_сессий.iterdir() if п.is_dir() and п.name.startswith(код)]


def момент(строка):
    """ISO-время в UTC; запись без часового пояса считается местной."""
    if not строка:
        return None
    try:
        т = datetime.fromisoformat(строка.replace("Z", "+00:00"))
    except ValueError:
        return None
    if т.tzinfo is None:
        т = т.astimezone()
    return т.astimezone(UTC)


def записи_среза(начато):
    """Записи журналов сессий, сделанные после начала задачи."""
    собрано = []
    for папка in папка_сессий():
        for файл in папка.glob("*.jsonl"):
            try:
                текст = файл.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for строка in текст.splitlines():
                if not строка.strip():
                    continue
                try:
                    д = json.loads(строка)
                except json.JSONDecodeError:
                    continue
                т = момент(д.get("timestamp"))
                if т is None or т < начато:
                    continue
                д["_время"] = т
                собрано.append(д)
    собрано.sort(key=lambda д: д["_время"])
    return собрано


def сводка(записи, начато):
    """Считает показатели среза; время задачи — от её начала."""
    усилия = []
    модели = []
    ходов = выход = размышления = 0
    реплик = блокировок = 0
    тестов = красных = 0
    последнее = None
    вызовы_тестов = set()  # идентификаторы вызовов инструмента с pytest

    for д in записи:
        тип = д.get("type")
        последнее = д["_время"]

        if тип == "assistant":
            ходов += 1
            у = д.get("effort")
            if у and у not in усилия:
                усилия.append(у)
            # Имя модели без приставки «claude-»; служебные записи
            # («<synthetic>») ходами модели не являются.
            модель = (д.get("message", {}).get("model") or "").removeprefix("claude-")
            if модель and not модель.startswith("<") and модель not in модели:
                модели.append(модель)
            использование = д.get("message", {}).get("usage") or {}
            выход += использование.get("output_tokens") or 0
            подробности = использование.get("output_tokens_details") or {}
            размышления += подробности.get("thinking_tokens") or 0
            for блок in д.get("message", {}).get("content") or []:
                if not isinstance(блок, dict) or блок.get("type") != "tool_use":
                    continue
                команда = str((блок.get("input") or {}).get("command", ""))
                # Тело вложенного документа (heredoc, «<<») — это данные,
                # а не команда: в нём может лежать текст с «pytest»,
                # который тестов не запускает.
                if ЗАПУСК_ТЕСТОВ.search(команда.split("<<", 1)[0]):
                    вызовы_тестов.add(блок.get("id"))

        elif тип == "user":
            if (д.get("origin") or {}).get("kind") == "human":
                реплик += 1
            результат = д.get("toolUseResult")
            if результат is None:
                continue
            ид = None
            for блок in д.get("message", {}).get("content") or []:
                if isinstance(блок, dict) and блок.get("type") == "tool_result":
                    ид = блок.get("tool_use_id")
            if ид not in вызовы_тестов:
                continue
            тестов += 1
            # Провал: результат пришёл строкой с ошибкой либо в выводе
            # есть отчёт pytest о падениях.
            if isinstance(результат, str) or re.search(
                r"\d+ failed|\d+ error", результат.get("stdout", "")
            ):
                красных += 1

        elif тип == "system" and д.get("hookErrors"):
            блокировок += 1

    минут = 0
    if последнее:
        минут = round((последнее - начато).total_seconds() / 60)

    return {
        "модели": ", ".join(модели) or "—",
        "усилия": ", ".join(усилия) or "—",
        "ходов": ходов,
        "выход": выход,
        "размышления": размышления,
        "реплик": реплик,
        "блокировок": блокировок,
        "тестов": тестов,
        "красных": красных,
        "минут": минут,
    }


def дописать(строка):
    """Вставляет строку сразу после шапки таблицы (новые сверху)."""
    if not ЖУРНАЛ.exists():
        ЖУРНАЛ.parent.mkdir(parents=True, exist_ok=True)
        ЖУРНАЛ.write_text(ШАПКА, encoding="utf-8")
    строки = ЖУРНАЛ.read_text(encoding="utf-8").splitlines(keepends=True)
    for i, с in enumerate(строки):
        if с.startswith("|---"):
            строки.insert(i + 1, строка)
            break
    else:
        return False
    ЖУРНАЛ.write_text("".join(строки), encoding="utf-8")
    return True


def main():
    сухой = "--dry-run" in sys.argv

    if not ТАБЛО.exists():
        print("Замер усилия: табло задачи не найдено — строка не пишется.")
        return 0
    try:
        табло = json.loads(ТАБЛО.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print("Замер усилия: табло не читается — строка не пишется.")
        return 0

    задача = табло.get("задача")
    начато = момент(табло.get("начато"))
    if not задача or начато is None:
        print("Замер усилия: нет задачи или отметки начала — строка не пишется.")
        return 0

    записи = записи_среза(начато)
    if not записи:
        print("Замер усилия: журнал сессии не найден — строка не пишется.")
        return 0

    п = сводка(записи, начато)
    строка = (
        f"| {datetime.now().date().isoformat()} | {задача} | — | {п['модели']} | "
        f"{п['усилия']} | {п['тестов']}/{п['красных']} | {п['блокировок']} | "
        f"{п['реплик']} | "
        f"{п['выход']}/{п['размышления']} | {п['минут']} |\n"
    )

    if сухой:
        print(строка, end="")
        return 0

    if not дописать(строка):
        print("Замер усилия: в журнале нет шапки таблицы — строка не пишется.")
        return 0

    print(
        f"Замер записан: {п['модели']}, усилие {п['усилия']}, "
        f"тестов {п['тестов']}/{п['красных']}."
    )
    print(f"ЖУРНАЛ: {ЖУРНАЛ.relative_to(КОРЕНЬ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
