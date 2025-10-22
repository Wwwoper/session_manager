"""
Session Manager - Умное отслеживание сессий с сохранением контекста
Инструмент для разработчиков, объединяющий учёт времени, сохранение контекста,
и глубокую интеграцию с вашим рабочим процессом разработки.
Возможности:
- Отслеживание рабочих сессий с автоматическим подсчётом времени
- Сохранение и восстановление контекста проекта (что вы делали, что дальше)
- Интеграция с Git (ветка, коммиты, несохранённые изменения)
- Отслеживание статуса тестов (интеграция с pytest)
- Интеграция с GitHub Issues (gh CLI)
- Работает с Git или без него - корректная деградация функциональности
- Локальное хранилище для полной конфиденциальности
Использование:
    session project add myproject /path/to/project
    session start
    session end
    session status
"""
__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"
__license__ = "MIT"
# Core components will be imported here as they're developed
# from .core.session import SessionManager
# from .core.config import GlobalConfig
# from .core.project import Project
