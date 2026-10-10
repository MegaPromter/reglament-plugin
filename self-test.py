#!/usr/bin/env python3
"""Самопроверка регламента — без ДСХ, без прежней среды и без живых проектов.

Проверяется то, чего не видно чтением: поведение автозакрытия задачи
(`tools/close_task.py` и его близнец `hooks/close_task.py`) на временном проекте.
Случаи подобраны по живым отказам: неприменённая миграция не пускает закрытие,
сбой проверки не считается разрешением, отказ не портит состояние, осознанный
обход оставляет след.

Валидатор vault внутри временного проекта — заглушка: сам валидатор принадлежит
проекту, а не комплекту. Заглушка нужна ещё и затем, чтобы проверить отказ
валидатора: закрытие обязано откатить свою правку заметки.

Запуск:  python self-test.py
Код выхода: 0 — все случаи пройдены; 1 — есть провалы.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

КОРЕНЬ = Path(__file__).resolve().parent
ЗАМЕТКА = "Проба закрытия"
ЗАГОЛОВОК_ЗАМЕТКИ = (
    "---\n"
    "тип: задача\n"
    "статус: в работе\n"
    "создано: 2026-10-01\n"
    "обновлено: 2026-10-01\n"
    "---\n\n"
    f"# {ЗАМЕТКА}\n"
)
ЖУРНАЛ = "docs/vault/задачи/Мелкие правки (журнал).md"

ЗАГЛУШКА_ВАЛИДАТОРА = '''\
"""Заглушка валидатора vault — для самопроверки закрытия задачи."""
import sys
from pathlib import Path

if Path(__file__).with_name("ПРОВАЛ").exists():
    print("✗ Проба: валидатор отказал намеренно.")
    sys.exit(1)
print("Валидатор vault: чисто (заглушка).")
sys.exit(0)
'''

МИГРАЦИЯ_НЕ_ПРИМЕНЕНА = "[X] contenttypes 0001_initial\n[ ] works 0085_pp_plan_blocking\n"
МИГРАЦИИ_ПРИМЕНЕНЫ = "[X] contenttypes 0001_initial\n[X] works 0085_pp_plan_blocking\n"

ЛИЧНОСТЬ = {
    "GIT_AUTHOR_NAME": "проба",
    "GIT_AUTHOR_EMAIL": "proba@example.com",
    "GIT_COMMITTER_NAME": "проба",
    "GIT_COMMITTER_EMAIL": "proba@example.com",
}

СЛУЧАЕВ = 0
ПРОВАЛЫ: list[str] = []


def случай(имя: str):
    """Зарегистрировать и сразу выполнить случай проверки."""

    def обёртка(функция):
        global СЛУЧАЕВ
        СЛУЧАЕВ += 1
        try:
            функция()
        except AssertionError as ошибка:
            ПРОВАЛЫ.append(f"{имя}: {ошибка}")
        except Exception as ошибка:  # noqa: BLE001 — сбой самой проверки тоже провал
            ПРОВАЛЫ.append(f"{имя}: сбой проверки — {ошибка!r}")
        return функция

    return обёртка


def _git(корень: Path, *аргументы: str) -> subprocess.CompletedProcess[str]:
    """git во временном проекте: личность автора — из окружения, чужих настроек нет."""
    return subprocess.run(
        ["git", "-C", str(корень), *аргументы],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env={**os.environ, **ЛИЧНОСТЬ},
    )


def _manage(корень: Path | None, вывод: str, код: int = 0) -> None:
    """`manage.py`-заглушка: печатает заданный вывод `showmigrations` и выходит кодом.

    `корень=None` — заглушки нет вовсе (проект не Django).
    """
    if корень is None:
        return
    (корень / "manage.py").write_text(
        "import sys\n"
        f"ВЫВОД = {вывод!r}\n"
        "sys.stdout.write(ВЫВОД)\n"
        f"sys.exit({код})\n",
        encoding="utf-8",
    )


def проект(временная: Path, форма: str = "полная") -> Path:
    """Временный проект: инструменты комплекта, табло, заметка, журнал, git."""
    корень = временная / "проект"
    (корень / ".dsh" / "tools").mkdir(parents=True)
    (корень / ".reglament" / "hooks").mkdir(parents=True)
    (корень / "docs" / "vault" / "задачи").mkdir(parents=True)
    # Склад проверяльщика — заглушка: иначе инструмент полезет копировать настоящий.
    (корень / ".pre-commit-home" / "repo1").mkdir(parents=True)
    (корень / ".pre-commit-home" / "db.db").write_text("проба\n", encoding="utf-8")
    (корень / ".pre-commit-home" / "repo1" / "проба").write_text("", encoding="utf-8")

    shutil.copy2(КОРЕНЬ / "tools" / "close_task.py", корень / ".dsh" / "tools" / "close_task.py")
    shutil.copy2(
        КОРЕНЬ / "tools" / "pre_commit_cache.py",
        корень / ".dsh" / "tools" / "pre_commit_cache.py",
    )
    shutil.copy2(
        КОРЕНЬ / "hooks" / "close_task.py",
        корень / ".reglament" / "hooks" / "close_task.py",
    )
    (корень / ".reglament" / "hooks" / "validate_vault.py").write_text(
        ЗАГЛУШКА_ВАЛИДАТОРА, encoding="utf-8"
    )
    (корень / "docs" / "vault" / f"{ЗАМЕТКА}.md").write_text(
        ЗАГОЛОВОК_ЗАМЕТКИ, encoding="utf-8"
    )
    (корень / ЖУРНАЛ).write_text(
        "# Журнал мелких правок\n\n| Дата | Что сделано | Файлы | Коммит |\n|---|---|---|---|\n",
        encoding="utf-8",
    )
    табло = {
        "задача": ЗАМЕТКА,
        "заметка": f"docs/vault/{ЗАМЕТКА}.md",
        "форма": форма,
        "фаза": "тесты",
    }
    (корень / ".reglament" / "task-state.json").write_text(
        json.dumps(табло, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    _git(корень, "init", "-q")
    _git(корень, "config", "core.autocrlf", "false")
    _git(корень, "add", "-A")
    _git(корень, "commit", "-q", "-m", "начало")
    return корень


def _окружение(корень: Path, среда: dict | None = None) -> dict:
    """Окружение запуска инструмента: питон из PATH, корень проекта, личность git."""
    окружение = dict(os.environ, **ЛИЧНОСТЬ)
    окружение["PATH"] = str(Path(sys.executable).parent) + os.pathsep + окружение.get("PATH", "")
    окружение["REGLAMENT_PROJECT_DIR"] = str(корень)
    if среда:
        окружение.update(среда)
    return окружение


def _запустить(скрипт: Path, корень: Path, *аргументы: str, среда: dict | None = None):
    return subprocess.run(
        [sys.executable, "-X", "utf8", str(скрипт), *аргументы],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(корень),
        env=_окружение(корень, среда),
    )


def закрыть(корень: Path, *аргументы: str, среда: dict | None = None):
    """Закрытие инструментом ДСХ — так же, как его зовёт навык."""
    return _запустить(корень / ".dsh" / "tools" / "close_task.py", корень, *аргументы, среда=среда)


def закрыть_хуком(корень: Path, *аргументы: str, среда: dict | None = None):
    """Закрытие близнецом прежней среды."""
    return _запустить(
        корень / ".reglament" / "hooks" / "close_task.py", корень, *аргументы, среда=среда
    )


def текст(путь: Path) -> str:
    return путь.read_text(encoding="utf-8")


def коммитов(корень: Path) -> int:
    return int(_git(корень, "rev-list", "--count", "HEAD").stdout.strip())


def вывод(итог) -> str:
    return f"{итог.stdout or ''}{итог.stderr or ''}"


# ── случаи ────────────────────────────────────────────────────────────────


@случай("неприменённая миграция: отказ, состояние не тронуто")
def _():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as временная:
        корень = проект(Path(временная))
        _manage(корень, МИГРАЦИЯ_НЕ_ПРИМЕНЕНА)
        заметка = корень / "docs" / "vault" / f"{ЗАМЕТКА}.md"
        было = (текст(заметка), текст(корень / ".reglament" / "task-state.json"), коммитов(корень))
        итог = закрыть(корень)
        assert итог.returncode == 1, f"ждали отказ, код {итог.returncode}: {вывод(итог)}"
        assert "не применены миграции" in вывод(итог), вывод(итог)
        assert "works.0085_pp_plan_blocking" in вывод(итог), вывод(итог)
        assert "manage.py migrate" in вывод(итог), вывод(итог)
        стало = (текст(заметка), текст(корень / ".reglament" / "task-state.json"), коммитов(корень))
        assert стало == было, "отказ изменил заметку, табло или сделал коммит"


@случай("миграции применены: закрытие проходит")
def _():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as временная:
        корень = проект(Path(временная))
        _manage(корень, МИГРАЦИИ_ПРИМЕНЕНЫ)
        заметка = корень / "docs" / "vault" / f"{ЗАМЕТКА}.md"
        было_коммитов = коммитов(корень)
        итог = закрыть(корень)
        assert итог.returncode == 0, f"ждали закрытие, код {итог.returncode}: {вывод(итог)}"
        assert "статус: сделано" in текст(заметка), "статус заметки не переведён"
        assert "реализовано в коммите" in текст(заметка), "нет строки о коммите"
        assert json.loads(текст(корень / ".reglament" / "task-state.json")) == {}, "табло не очищено"
        assert коммитов(корень) == было_коммитов + 1, "закрывающего коммита нет"


@случай("сбой проверки: «неизвестно» не считается разрешением")
def _():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as временная:
        корень = проект(Path(временная))
        _manage(корень, "базы нет\n", код=1)
        заметка = корень / "docs" / "vault" / f"{ЗАМЕТКА}.md"
        было = текст(заметка)
        итог = закрыть(корень)
        assert итог.returncode == 1, f"ждали отказ, код {итог.returncode}: {вывод(итог)}"
        assert "остановлено" in вывод(итог), вывод(итог)
        assert текст(заметка) == было, "отказ при сбое проверки изменил заметку"


@случай("manage.py нет: проверка не выполнялась, но об этом сказано")
def _():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as временная:
        корень = проект(Path(временная))
        итог = закрыть(корень)
        assert итог.returncode == 0, f"ждали закрытие, код {итог.returncode}: {вывод(итог)}"
        assert "manage.py не найден — проверка не выполнялась" in вывод(итог), вывод(итог)


@случай("обход --allow-pending: закрытие проходит, причина остаётся следом")
def _():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as временная:
        корень = проект(Path(временная))
        _manage(корень, МИГРАЦИЯ_НЕ_ПРИМЕНЕНА)
        итог = закрыть(корень, "--allow-pending", "дев-база занята")
        assert итог.returncode == 0, f"ждали закрытие, код {итог.returncode}: {вывод(итог)}"
        заметка = текст(корень / "docs" / "vault" / f"{ЗАМЕТКА}.md")
        assert "закрытие с обходом: дев-база занята" in заметка, "причина обхода не осталась следом"


@случай("обход без причины не принимается")
def _():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as временная:
        корень = проект(Path(временная))
        _manage(корень, МИГРАЦИЯ_НЕ_ПРИМЕНЕНА)
        итог = закрыть(корень, "--allow-pending", "  ")
        assert итог.returncode == 1, f"ждали отказ, код {итог.returncode}: {вывод(итог)}"
        assert "требует причины" in вывод(итог), вывод(итог)


@случай("отказ валидатора: правка заметки откатана, коммита нет")
def _():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as временная:
        корень = проект(Path(временная))
        _manage(корень, МИГРАЦИИ_ПРИМЕНЕНЫ)
        (корень / ".reglament" / "hooks" / "ПРОВАЛ").write_text("", encoding="utf-8")
        заметка = корень / "docs" / "vault" / f"{ЗАМЕТКА}.md"
        было, было_коммитов = текст(заметка), коммитов(корень)
        итог = закрыть(корень)
        assert итог.returncode == 1, f"ждали отказ, код {итог.returncode}: {вывод(итог)}"
        assert "правка откатана" in вывод(итог), вывод(итог)
        assert текст(заметка) == было, "отказ валидатора не откатил заметку"
        assert коммитов(корень) == было_коммитов, "при отказе валидатора появился коммит"


@случай("малая форма: проверка та же, журнал при отказе не тронут")
def _():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as временная:
        корень = проект(Path(временная), форма="малая")
        _manage(корень, МИГРАЦИЯ_НЕ_ПРИМЕНЕНА)
        журнал = корень / ЖУРНАЛ
        было = текст(журнал)
        итог = закрыть(корень, "--desc", "проба", "--files", "apps/a.py")
        assert итог.returncode == 1, f"ждали отказ, код {итог.returncode}: {вывод(итог)}"
        assert текст(журнал) == было, "отказ изменил журнал мелких правок"


@случай("чужой корень в REGLAMENT_PROJECT_DIR: закрытие отклонено")
def _():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as временная:
        корень = проект(Path(временная))
        _manage(корень, МИГРАЦИИ_ПРИМЕНЕНЫ)
        итог = закрыть(корень, среда={"REGLAMENT_PROJECT_DIR": str(временная)})
        assert итог.returncode == 1, f"ждали отказ, код {итог.returncode}: {вывод(итог)}"
        assert "другой проект" in вывод(итог), вывод(итог)


@случай("близнец прежней среды: проверка миграций работает так же")
def _():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as временная:
        корень = проект(Path(временная))
        _manage(корень, МИГРАЦИЯ_НЕ_ПРИМЕНЕНА)
        итог = закрыть_хуком(корень)
        assert итог.returncode == 1, f"ждали отказ, код {итог.returncode}: {вывод(итог)}"
        assert "не применены миграции" in вывод(итог), вывод(итог)


# ── итог ──────────────────────────────────────────────────────────────────

print(f"пройдено случаев: {СЛУЧАЕВ - len(ПРОВАЛЫ)} из {СЛУЧАЕВ}")
if ПРОВАЛЫ:
    print(f"ПРОВАЛЕНО: {len(ПРОВАЛЫ)}")
    for провал in ПРОВАЛЫ:
        print(f"  - {провал}")
    sys.exit(1)
print("все случаи пройдены")
