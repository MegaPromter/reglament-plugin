"""Закрытие задачи из ДСХ — свой скрипт, не общий с Claude Code.

Полная форма: хэш в «Историю» заметки, статус «сделано», закрывающий коммит.
Малая форма:  строка в журнал мелких правок, закрывающий коммит.
Перед коммитом гоняется валидатор vault (общий для проекта), после — табло
очищается.

Чем отличается от скрипта Claude Code (`.claude/hooks/close_task.py`), который
в ДСХ не используется:

- коммит идёт через склад проверяльщика в рабочей папке (`PRE_COMMIT_HOME`) —
  значит проверки при закрывающем коммите работают и в ДСХ, а не падают;
- вывод git читается с заменой непонятных байтов и печатается при отказе —
  причина сбоя видна, а не превращается в пустоту (DSH_REPORT, раздел 20);
- замер усилия не ведётся: он читает стенограмму Claude Code, которой в ДСХ нет.

Запуск (полная):  python .dsh/tools/close_task.py [--hash abc1234]
Запуск (малая):   python .dsh/tools/close_task.py --desc "что сделано" \
                  --files "какие файлы" [--hash abc1234]
Без --hash берётся последний коммит (HEAD).
"""

import argparse
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pre_commit_cache import КОРЕНЬ, среда_со_складом  # noqa: E402

for _поток in (sys.stdout, sys.stderr):
    if hasattr(_поток, "reconfigure"):
        _поток.reconfigure(encoding="utf-8")

ТАБЛО = КОРЕНЬ / ".claude" / "task-state.json"
ЖУРНАЛ = КОРЕНЬ / "docs" / "vault" / "задачи" / "Мелкие правки (журнал).md"
ВАЛИДАТОР = КОРЕНЬ / ".claude" / "hooks" / "validate_vault.py"


def гит(*аргументы: str, проверять: bool = True) -> subprocess.CompletedProcess[str]:
    """git в проекте: склад проверяльщика подставлен, вывод читается терпимо."""
    итог = subprocess.run(
        ["git", "-C", str(КОРЕНЬ), *аргументы],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=среда_со_складом(КОРЕНЬ),
    )
    if проверять and итог.returncode != 0:
        причина = f"{итог.stdout or ''}{итог.stderr or ''}".strip()
        raise RuntimeError(f"git {' '.join(аргументы)}:\n{причина}")
    return итог


def проверить_vault() -> bool:
    """Валидатор vault — общий для проекта: закрывать можно только чистый."""
    итог = subprocess.run(
        [sys.executable, str(ВАЛИДАТОР)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    print(итог.stdout, end="")
    return итог.returncode == 0


def записать_в_журнал(сегодня: str, хэш: str, сделано: str, файлы: str) -> None:
    """Малая форма: строка в таблицу журнала мелких правок."""
    строки = ЖУРНАЛ.read_text(encoding="utf-8").splitlines(keepends=True)
    for номер, строка in enumerate(строки):
        if строка.startswith("|---"):
            строки.insert(номер + 1, f"| {сегодня} | {сделано} | {файлы} | {хэш} |\n")
            break
    else:
        raise SystemExit("В журнале не найдена шапка таблицы.")
    ЖУРНАЛ.write_text("".join(строки), encoding="utf-8")


def закрыть_полную(сегодня: str, хэш: str, путь: Path) -> None:
    """Полная форма: хэш в «Историю», статус «сделано», свежая дата."""
    текст = путь.read_text(encoding="utf-8")
    for старый in ("статус: в работе", "статус: запланировано"):
        if старый in текст:
            текст = текст.replace(старый, "статус: сделано", 1)
            break
    текст = "\n".join(
        f"обновлено: {сегодня}" if строка.startswith("обновлено:") else строка
        for строка in текст.splitlines()
    )
    if not текст.endswith("\n"):
        текст += "\n"
    текст += f"- {сегодня}: реализовано в коммите {хэш}.\n"
    путь.write_text(текст, encoding="utf-8")


def main() -> int:
    разбор = argparse.ArgumentParser()
    разбор.add_argument("--hash", help="хэш коммита (по умолчанию HEAD)")
    разбор.add_argument("--desc", help="малая форма: что сделано")
    разбор.add_argument("--files", help="малая форма: какие файлы")
    аргументы = разбор.parse_args()

    табло = json.loads(ТАБЛО.read_text(encoding="utf-8")) if ТАБЛО.exists() else {}
    if not табло.get("задача"):
        print("Активной задачи в табло нет — закрывать нечего.")
        return 1

    хэш = аргументы.hash or гит("rev-parse", "--short", "HEAD").stdout.strip()
    сегодня = date.today().isoformat()
    имя = табло["задача"]
    форма = табло.get("форма", "полная")

    if форма == "малая":
        if not (аргументы.desc and аргументы.files):
            print("Для малой формы обязательны --desc и --files.")
            return 1
        записать_в_журнал(сегодня, хэш, аргументы.desc, аргументы.files)
        изменён = ЖУРНАЛ
        сообщение = f"docs(vault): запись в журнал мелких правок ({хэш})"
    else:
        заметка = КОРЕНЬ / табло["заметка"]
        if not заметка.exists():
            print(f"Заметка не найдена: {заметка}")
            return 1
        закрыть_полную(сегодня, хэш, заметка)
        изменён = заметка
        сообщение = f"docs(vault): закрытие задачи «{имя}» — хэш {хэш}, статус сделано"

    if not проверить_vault():
        print("Валидатор нашёл нарушения — закрывающий коммит не сделан.")
        return 1

    # Только явные пути этой задачи: `git add -u` утащил бы чужие правки.
    гит("add", str(изменён.relative_to(КОРЕНЬ)))
    коммит = гит("commit", "-m", сообщение, проверять=False)
    if коммит.returncode != 0:
        print("Первый проход коммита не прошёл. Ответ git:")
        print(f"{коммит.stdout or ''}{коммит.stderr or ''}".strip())
        # Проверяльщик мог поправить файл (пробелы) — добавить и повторить.
        гит("add", str(изменён.relative_to(КОРЕНЬ)))
        коммит = гит("commit", "-m", сообщение)
    новый = гит("rev-parse", "--short", "HEAD").stdout.strip()

    ТАБЛО.write_text("{}\n", encoding="utf-8")
    print(
        f"Задача «{имя}» закрыта: хэш {хэш} записан, "
        f"закрывающий коммит {новый}, табло очищено."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
