#!/usr/bin/env python3
"""
Session Manager - Точка входа
"""

import sys

from .core.config import GlobalConfig, ConfigError
from .core.project_registry import ProjectRegistry
from .cli.commands import CLI
from .utils.formatters import print_error, print_warning


def main(args: list = None) -> int:
    """
    Основная точка входа для CLI Session Manager

    Аргументы:
        args: Аргументы командной строки (по умолчанию sys.argv[1:])

    Возвращает:
        Код выхода (0 — успех, ненулевое — ошибка)
    """
    if args is None:
        args = sys.argv[1:]

    try:
        # Инициализация конфигурации
        config = GlobalConfig()
        config.load()

        # Инициализация реестра проектов
        registry = ProjectRegistry(config)

        # Инициализация CLI
        cli = CLI(config, registry)

        # Выполнение команды
        return cli.run(args)

    except ConfigError as e:
        print_error(f"Ошибка конфигурации: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n")
        print_warning("Прервано пользователем")
        return 130
    except Exception as e:
        print_error(f"Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())