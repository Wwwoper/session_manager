# Session Manager 🚀

**Умный трекер сессий работы с автоматическим сохранением контекста для разработчиков**

Session Manager — это инструмент для разработчиков, который не просто отслеживает время работы, но и **помогает быстро погрузиться обратно в проект** после перерыва. Он автоматически сохраняет контекст работы, интегрируется с вашими инструментами разработки и создаёт умный файл PROJECT.md с подсказками "что делать дальше".

## 🎯 Что делает этот инструмент особенным?

**Session Manager — это не просто трекер времени.** Это ваш помощник для:

✨ **Быстрого восстановления контекста**
- Автоматически сохраняет "что вы делали" и "что делать дальше"
- Создаёт файл PROJECT.md с актуальной информацией о проекте
- Показывает последнее действие при запуске новой сессии

🔗 **Глубокой интеграции с workflow**
- Git: текущая ветка, последний коммит, незакоммиченные изменения
- Pytest: автоматический запуск тестов и статус
- GitHub Issues: показывает открытые задачи через gh CLI

🛡️ **Работы везде**
- Работает с git-репозиториями И обычными папками
- Graceful degradation: все интеграции опциональны
- Нет внешних зависимостей (только Python 3.8+)

💾 **Полной приватности**
- Все данные хранятся локально в `~/.session-manager/`
- Никаких внешних сервисов или отправки данных
- Полный контроль над вашей информацией

## 📦 Установка

### Требования
- Python 3.8 или выше
- **Опционально** (для дополнительных возможностей):
  - Git (для git-интеграции)
  - pytest (для автоматического запуска тестов)
  - gh CLI (для интеграции с GitHub Issues)

### Установка из исходников

```bash
# Клонируйте репозиторий
git clone https://github.com/Wwwoper/session-manager.git
cd session-manager

# Установите в режиме разработки
pip install -e .

# Или установите с dev-зависимостями для разработки
pip install -e ".[dev]"
```

После установки команда `session` будет доступна глобально в вашей системе.

## 🚀 Быстрый старт

### 1. Добавьте свой первый проект

```bash
# Добавить текущую директорию как проект
session project add myapp . --alias ma

# Или указать путь к проекту
session project add myapp /path/to/myapp
```

### 2. Начните работу

```bash
session start myapp
```

Session Manager покажет:
- 📌 Последнее сохранённое действие (если есть)
- 🌿 Git статус (ветка, коммит, изменения)
- 📋 Открытые GitHub Issues (если доступен gh CLI)
- 🧪 Результаты запуска тестов (если доступен pytest)

### 3. Завершите сессию

```bash
session end
```

Session Manager попросит:
- Резюме сессии: что было сделано
- Следующее действие: что делать при возвращении
- Опционально: создать git-коммит если есть изменения

После этого будут созданы:
- Снимок контекста в `~/.session-manager/projects/myapp/snapshots/`
- Обновлённый файл `PROJECT.md` с актуальной информацией

### 4. Проверьте статус

```bash
session status
```

Показывает полную картину:
- Активная сессия (если есть)
- Последнее сохранённое действие
- Git информация
- Статус тестов

## 📚 Основные команды

### Управление проектами

```bash
# Добавить проект
session project add <name> <path> [--alias <alias>]

# Список всех проектов
session project list

# Информация о проекте
session project info <name>

# Удалить проект
session project remove <name>
```

### Работа с сессиями

```bash
# Начать новую сессию
session start [project] [description]

# Завершить активную сессию
session end [project]

# Показать текущий статус
session status [project]

# История сессий
session history [project] [--limit N]

# Статистика
session stats [project]
```

### Дополнительные команды

```bash
# Справка
session help

# Версия
session version
```

## 💡 Примеры использования

### Сценарий 1: Работа с git-репозиторием

```bash
# Добавляем проект
cd ~/projects/myapp
session project add myapp . --alias ma

# Начинаем работу
session start ma "Implement user authentication"

# Session Manager покажет:
# 📌 Next Action: Add password hashing function
# 🌿 Git Status
#    Branch: feature/auth
#    Last Commit: abc1234 Add login form
#    ✅ Working directory clean
# 🧪 Running Tests...
#    ✅ All 15 tests passed

# Работаете над кодом...

# Завершаем сессию
session end
# > Summary: Implemented bcrypt hashing and user model
# > Next action: Add authentication middleware
# > Create a commit? (y/N): y
# > Commit message: Add password hashing with bcrypt
```

### Сценарий 2: Работа без git (обычная папка)

```bash
# Добавляем обычную папку
session project add notes ~/Documents/notes

# Начинаем работу
session start notes

# Session Manager работает без проблем:
# 📌 Next Action: Review chapter 3 notes
# (Нет git-информации, но всё остальное работает)

# Завершаем сессию
session end
# > Summary: Completed review of chapter 3
# > Next action: Start writing chapter 4 summary
```

### Сценарий 3: Множественные проекты

```bash
# Добавляем несколько проектов
session project add webapp ~/projects/webapp --alias web
session project add mobile ~/projects/mobile-app --alias mob
session project add docs ~/projects/documentation

# Список проектов (отсортирован по последнему использованию)
session project list

# Переключаемся между проектами
session start web
session end
session start mob
```

### Сценарий 4: Автоопределение проекта

```bash
# Если вы в директории зарегистрированного проекта,
# можно не указывать имя проекта
cd ~/projects/myapp
session start    # Автоматически определит проект myapp
session status
session end
```

## 🗂️ Структура данных

Session Manager хранит все данные локально в `~/.session-manager/`:

```
~/.session-manager/
├── config.json                      # Глобальная конфигурация
└── projects/
    └── myapp/
        ├── sessions.json            # История сессий
        ├── PROJECT.md               # Актуальный контекст проекта
        └── snapshots/               # Снимки контекста
            ├── 20250122_143000.md
            └── 20250122_183000.md
```

### PROJECT.md — ваш главный помощник

После каждой сессии Session Manager обновляет файл `PROJECT.md`:

```markdown
# Project Context

**Last Updated:** 2025-01-22 18:30  
**Session Duration:** 2h 15m

## 🎯 Next Action

Add authentication middleware to Express routes

## 📝 Last Session Summary

Implemented bcrypt password hashing and created User model
with validation. All tests passing.

---

## Session Information

- **Started:** 2025-01-22 16:15
- **Ended:** 2025-01-22 18:30
- **Branch:** feature/auth
- **Last Commit:** abc1234 Add password hashing
```

## 🔧 Интеграции

### Git Integration (опционально)

Если проект — git-репозиторий, Session Manager автоматически:
- Показывает текущую ветку
- Отображает последний коммит
- Предупреждает о незакоммиченных изменениях
- Предлагает создать коммит при завершении сессии

**Работает без git:** Если git недоступен, все остальные функции работают нормально.

### Pytest Integration (опционально)

Если pytest установлен, Session Manager:
- Автоматически запускает тесты при старте сессии
- Показывает статус тестов (passed/failed)
- Включает статус в снимки контекста

**Работает без pytest:** Если pytest недоступен, секция тестов просто не показывается.

### GitHub Issues Integration (опционально)

Если gh CLI установлен и проект подключён к GitHub:
- Показывает список открытых issues
- Отображает issues, назначенные на вас
- Помогает быстро сориентироваться в задачах

**Работает без gh CLI:** Если gh недоступен, секция issues не показывается.

## 🧪 Разработка и тестирование

### Установка для разработки

```bash
# Клонировать репозиторий
git clone https://github.com/yourusername/session-manager.git
cd session-manager

# Установить с dev-зависимостями
pip install -e ".[dev]"
```

### Запуск тестов

```bash
# Запустить все тесты
pytest

# С покрытием кода
pytest --cov=session_manager --cov-report=html

# Только unit-тесты
pytest tests/test_core/

# Только интеграционные тесты
pytest tests/test_integrations/
```

### Проверка качества кода

```bash
# Форматирование с black
black session_manager/

# Проверка стиля с flake8
flake8 session_manager/

# Проверка типов с mypy
mypy session_manager/
```

## 🤝 Вклад в проект

Мы приветствуем вклад в проект! Вот несколько способов помочь:

1. 🐛 **Сообщить о баге** через Issues
2. 💡 **Предложить новую функцию** через Issues
3. 📝 **Улучшить документацию** через Pull Request
4. 🔧 **Исправить баг** через Pull Request

### Гайдлайны

- Код должен следовать PEP 8
- Все новые функции должны иметь тесты
- Покрытие кода тестами должно быть >70%
- Документируйте публичные API в docstrings
- Пишите понятные commit-сообщения

## 📄 Лицензия

MIT License - см. файл [LICENSE](LICENSE)

## 🙏 Благодарности

Session Manager создан для разработчиков, разработчиками. Спасибо всем контрибьюторам!

---

**Вопросы?** Создайте issue на GitHub!  
**Хотите помочь?** Pull requests приветствуются!

**Made with ❤️ for developers who care about context**