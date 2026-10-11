#!/usr/bin/env python3
"""Развёртывание комплекта регламента: правила — в проект, плагин — в дом ДСХ.

Зачем. Разработка регламента ведётся в этом проекте («плагин»), а работает он в
проекте ПРИЗМА: там лежит развёрнутая копия правил (хуки, инструменты, навыки),
её читают ДСХ, ворота регламента и стражи (vault: решение «Разработка регламента —
отдельный проект»). Плагин-переходник (`.dsh/plugin-reglament`) живёт отдельно — в
доме ДСХ, как второй плагин: механизм один на все проекты, а в проекте своей копии
нет (заметка «Сторож регламента — один плагин на все проекты»). Скрипт несёт
изменения из источника в обе копии и умеет сверить их, ничего не записывая.

Запуск:
    python deploy_to_project.py                  # скопировать изменения (проект и дом)
    python deploy_to_project.py --check          # только сверить, ничего не писать
    python deploy_to_project.py --target <путь>  # другой проект (по умолчанию — ПРИЗМА)

Код возврата: 0 — всё хорошо; 1 — расхождение (в режиме --check) или ошибка.
"""

import argparse
import hashlib
import os
import shutil
import sys
from pathlib import Path

# Windows-консоль по умолчанию не UTF-8 — русские сообщения превращаются в кашу.
for _поток in (sys.stdout, sys.stderr):
    if hasattr(_поток, "reconfigure"):
        _поток.reconfigure(encoding="utf-8")

КОРЕНЬ = Path(__file__).resolve().parent
ПРОЕКТ_ПО_УМОЛЧАНИЮ = Path(r"D:\Program\Body\planapp_django(DSH)")
# Дом ДСХ: там живёт плагин-переходник (как `dsh-plugin-selection-actions`), туда
# его и доставляет этот скрипт. `DSH_HOME` — переменная среды ДСХ;
# если её нет, берём привычное место дома.
ДОМ_ДСХ = Path(os.environ.get("DSH_HOME") or Path.home() / ".dsh")
ПЛАГИН_В_ДОМЕ = ДОМ_ДСХ / "plugins" / "dsh-plugin-reglament"

# Наборы «папка здесь → папка в проекте»: имена файлов перечислены поимённо —
# новый файл комплекта без строки здесь в проект не поедет (и это видно).
НАБОРЫ = (
    (
        "hooks",
        ".reglament/hooks",
        (
            "check_commit.py",
            "check_turn_end.py",
            "close_task.py",
            "gate_edit.py",
            "gate_shell.py",
            "post-edit-js.sh",
            "post-edit-python.sh",
            "pre-commit-tests.sh",
            "validate_vault.py",
        ),
    ),
    (
        "tools",
        ".dsh/tools",
        (
            "board_check.py",
            "close_task.py",
            "git_commit.py",
            "journal_report.py",
            "memory_check.py",
            "phase_rules.py",
            "pre_commit_cache.py",
            "preset_patch.py",
        ),
    ),
)

# Плагин-переходник: папка здесь → папка в доме ДСХ. Список поимённый, как у
# наборов: новый файл плагина без строки здесь в дом не поедет.
ПЛАГИН = (
    "approval.js",
    "board-log.js",
    "canary.js",
    "canary.mjs",
    "card-guard.js",
    "hooks-bridge.js",
    "hooks-map.js",
    "cordis.patch.yml",
    "index.js",
    "package.json",
    "project.js",
    "self-test.mjs",
    "settings.js",
    "stop-guard.js",
)

# Одиночные файлы: путь здесь → путь в проекте.
ОДИНОЧНЫЕ = (
    ("skills/reglament/SKILL.md", ".dsh/skills/reglament/SKILL.md"),
    ("skills/memory-cleanup/SKILL.md", ".dsh/skills/memory-cleanup/SKILL.md"),
)


def пары():
    """Полный перечень пар «файл источника → файл назначения».

    Правила едут в проект, плагин — в дом ДСХ. Путь источника считается от папки
    этого скрипта, а не от текущей папки запуска: иначе сверка работает только при
    запуске из проекта разработки (найдено проверкой 05.10.2026).
    """
    for папка_здесь, папка_в_проекте, имена in НАБОРЫ:
        for имя in имена:
            yield КОРЕНЬ / папка_здесь / имя, Path(папка_в_проекте) / имя
    for здесь, в_проекте in ОДИНОЧНЫЕ:
        yield КОРЕНЬ / здесь, Path(в_проекте)
    for имя in ПЛАГИН:
        yield КОРЕНЬ / "plugin" / имя, ПЛАГИН_В_ДОМЕ / имя


def отпечаток(путь: Path) -> str | None:
    """SHA-256 файла; нет файла — None (значит «в проекте ещё не развёрнут»)."""
    if not путь.is_file():
        return None
    return hashlib.sha256(путь.read_bytes()).hexdigest()


def main() -> int:
    разбор = argparse.ArgumentParser(description="Развернуть комплект регламента в проект ПРИЗМА")
    разбор.add_argument("--check", action="store_true", help="только сверить, ничего не писать")
    разбор.add_argument("--target", default=str(ПРОЕКТ_ПО_УМОЛЧАНИЮ), help="корень проекта ПРИЗМА")
    доводы = разбор.parse_args()

    проект = Path(доводы.target)
    if not (проект / ".reglament").is_dir():
        print(f"Не похоже на проект ПРИЗМА: {проект} (нет папки .reglament)")
        return 1

    нет_в_проекте = []
    расходятся = []
    совпадают = 0

    for источник, цель_относительная in пары():
        if not источник.is_file():
            print(f"В источнике нет файла {источник} — строку из deploy_to_project.py убрать")
            return 1
        цель = проект / цель_относительная
        отп_источника = отпечаток(источник)
        отп_цели = отпечаток(цель)
        if отп_цели is None:
            нет_в_проекте.append((источник, цель))
        elif отп_источника != отп_цели:
            расходятся.append((источник, цель))
        else:
            совпадают += 1

    всего = совпадают + len(нет_в_проекте) + len(расходятся)

    if доводы.check:
        print(f"Сверка комплекта: всего {всего}, совпадают {совпадают}")
        for _, цель in нет_в_проекте:
            print(f"  нет на месте:  {цель}")
        for _, цель in расходятся:
            print(f"  различается:   {цель}")
        if not нет_в_проекте and not расходятся:
            print("Различий нет: копии в проекте и в доме ДСХ совпадают с источником.")
            return 0
        return 1

    for источник, цель in нет_в_проекте + расходятся:
        цель.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(источник, цель)

    print(f"Развёрнуто: обновлено {len(расходятся)}, добавлено {len(нет_в_проекте)}, без изменений {совпадают}")
    for _, цель in расходятся:
        print(f"  обновлён:  {цель}")
    for _, цель in нет_в_проекте:
        print(f"  добавлен:  {цель}")
    if not расходятся and not нет_в_проекте:
        print("Копировать было нечего: версии совпадали.")
    print("Лишние файлы в проекте скрипт не удаляет — смотри состав глазами.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
