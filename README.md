# Reglament — система управления разработкой для работы с ИИ

*Development management system for AI-assisted coding. The wizard
asks for your preferred language at the start and runs the whole
dialogue — and generates all files — in it. English summary below.*

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

- в начале спрашивает язык — весь диалог и все создаваемые файлы
  ведутся на языке пользователя;
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

**Через встроенный каталог (окно Directory → Plugins) этот плагин
найти НЕЛЬЗЯ**: там показываются только плагины Anthropic и
партнёров. Сторонние каталоги подключаются правкой файла настроек.

Скопируйте и отправьте своему Claude:

> Подключи мне плагин reglament. В файле `~/.claude/settings.json`
> (Windows: `C:\Users\<имя>\.claude\settings.json`) добавь, не
> затирая существующие настройки:
>
> ```json
> "extraKnownMarketplaces": {
>   "megapromter-plugins": {
>     "source": { "source": "github", "repo": "MegaPromter/reglament-plugin" }
>   }
> },
> "enabledPlugins": {
>   "reglament@megapromter-plugins": true
> }
> ```
>
> Потом скажи мне перезапустить приложение.

**Обязательно перезапустите Claude Code** — плагин подхватывается
при старте. После перезапуска мастер доступен как
`/reglament:reglament-setup`.

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
the wizard on an already-configured project. The wizard asks for
your preferred language at the start and conducts the dialogue and
all generated files in it.

Install: `/plugin marketplace add MegaPromter/reglament-plugin`,
then `/plugin install reglament@megapromter-plugins`, run
`/reglament:reglament-setup` in a new project folder. Manual
install: copy `plugins/reglament/skills/reglament-setup` into
`~/.claude/skills/` and run `/reglament-setup`.

## Лицензия

MIT — см. [LICENSE](LICENSE).
