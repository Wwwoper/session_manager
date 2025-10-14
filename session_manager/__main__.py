#!/usr/bin/env python3
"""
Session Manager - Main entry point
"""

import sys
from typing import List


def main(args: List[str] = None) -> int:
    """
    Main entry point for Session Manager CLI
    
    Args:
        args: Command line arguments (defaults to sys.argv[1:])
        
    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    if args is None:
        args = sys.argv[1:]
    
    # Временная заглушка - показываем что команда работает
    print("🚀 Session Manager v0.1.0")
    print()
    
    if not args:
        print("Использование: session <command> [options]")
        print()
        print("Доступные команды:")
        print("  project add <n> <path>    Добавить проект")
        print("  project list              Список проектов")
        print("  project remove <n>        Удалить проект")
        print("  project info <n>          Информация о проекте")
        print()
        print("  start [project]           Начать сессию")
        print("  end [project]             Завершить сессию")
        print("  status [project]          Показать статус")
        print("  history [project]         История сессий")
        print()
        print("  version                   Показать версию")
        print("  help                      Показать эту справку")
        print()
        print("⚠️  Функциональность пока не реализована (MVP в разработке)")
        return 0
    
    command = args[0].lower()
    
    if command in ("version", "-v", "--version"):
        print("Session Manager version 0.1.0")
        print("Python:", sys.version.split()[0])
        return 0
    
    if command in ("help", "-h", "--help"):
        main([])  # Показываем справку
        return 0
    
    # Пока что все остальные команды не реализованы
    print(f"❌ Команда '{command}' пока не реализована")
    print("   MVP находится в разработке")
    print()
    print("Запустите 'session help' для списка команд")
    return 1


if __name__ == "__main__":
    sys.exit(main())