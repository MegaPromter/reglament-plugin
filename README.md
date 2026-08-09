# Reglament — система управления разработкой для работы с ИИ

*Development management system for AI-assisted coding. The wizard's
dialogue and generated files are in Russian — see English summary
below.*

## Что это

Плагин для [Claude Code](https://claude.com/claude-code) с навыком
`reglament-setup` — пошаговым мастером, который разворачивает в новом
проекте файловую систему памяти для работы с ИИ-ассистентом:

- **Устав** (`CLAUDE.md`) — короткие жёсткие правила, которые
  ассистент видит автоматически в каждой сессии;
- **Документация-vault** (`docs/vault/`) — регламент работы, заметка
  на каждую задачу, журнал решений с привязкой к коммитам;
- **Память ИИ** — конспекты ассистента и файл текущего статуса для
  преемственности сессий;
- **Проектный навык `/reglament`** — процедура ведения задачи:
  заметка → согласование → код → тесты → коммит → закрытие.

Зачем: у ИИ-ассистента ограниченное контекстное окно и нет памяти
между сессиями. Эта система выносит память в файлы — новая сессия
восстанавливает контекст за минуту, решения не теряются, каждая
задача согласуется словами до кода.

Особенности мастера:

- каждый принцип и каждый файл согласуется с пользователем по
  очереди — ничего не создаётся без подтверждения;
- каждый вопрос сопровождается пояснением: что это, зачем
  спрашивается, куда пойдёт ответ (подходит непрофессионалам);
- предохранитель: к уже настроенному проекту мастер не применяется;
- ничего не выдумывает о проекте — только ответы пользователя.

## Установка

### Способ 1 — терминальный Claude Code (две команды)

```
/plugin marketplace add MegaPromter/reglament-plugin
/plugin install reglament@megapromter-plugins
```

Вызов мастера после установки: `/reglament:reglament-setup`

### Способ 2 — десктоп-приложение Claude Code

Вариант А — через меню: кнопка **«+»** рядом с полем ввода →
**Plugins** → **Add plugin** → найти каталог/плагин.

Вариант Б — одним сообщением ассистенту. Скопируйте и отправьте
своему Claude:

> Подключи мне плагин reglament: в файл `~/.claude/settings.json`
> добавь в `extraKnownMarketplaces` запись
> `"megapromter-plugins": {"source": {"source": "github", "repo":
> "MegaPromter/reglament-plugin"}}`, а в массив `enabledPlugins` —
> элемент `{"marketplace": "megapromter-plugins", "plugin":
> "reglament"}`. Существующие настройки не затирай. Потом скажи
> мне перезапустить приложение.

После перезапуска мастер доступен как `/reglament:reglament-setup`.

### Способ 3 — вручную папкой (работает везде, без плагинов)

1. Скачайте этот репозиторий (Code → Download ZIP).
2. Скопируйте папку `plugins/reglament/skills/reglament-setup` в
   личную папку навыков:
   - Windows: `C:\Users\<имя>\.claude\skills\`
   - Mac/Linux: `~/.claude/skills/`
3. Перезапустите Claude Code.

Вызов мастера: `/reglament-setup`

## Использование

В папке нового проекта вызовите мастер и отвечайте на вопросы.
Мастер проведёт по шагам: обзор системы → опрос о проекте → устав →
принципы регламента (по одному) → структура документации → память
ИИ → проектный навык задач → вопрос об автоматизации (хук) → итог.

Дальнейшие задачи в настроенном проекте начинаются командой
`/reglament` — она ведёт задачу по процедуре до коммита.

## English summary

A Claude Code plugin with a `reglament-setup` skill — a step-by-step
wizard that bootstraps a file-based memory system for AI-assisted
development in a new project: a project charter (`CLAUDE.md`), a
documentation vault with a workflow reglament and per-task notes
linked to commits, AI memory files for session continuity, and a
per-task procedure skill (`/reglament`). Every principle and file is
confirmed with the user one by one; a safety check prevents running
the wizard on an already-configured project. **The wizard dialogue
and generated files are currently in Russian.**

Install: `/plugin marketplace add MegaPromter/reglament-plugin`,
then `/plugin install reglament@megapromter-plugins`, run
`/reglament:reglament-setup` in a new project folder. Manual
install: copy `plugins/reglament/skills/reglament-setup` into
`~/.claude/skills/` and run `/reglament-setup`.

## Лицензия

MIT — см. [LICENSE](LICENSE).
