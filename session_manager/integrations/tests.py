"""
Интеграция с Pytest для Session Manager

Предоставляет информацию о запуске тестов и статусе с корректной деградацией.
"""

import subprocess
from pathlib import Path
from typing import Optional, Dict


class TestsIntegration:
    """
    Интеграция с тестовым фреймворком pytest.

    Предоставляет выполнение тестов и информацию о статусе.
    Все методы корректно обрабатывают отсутствие pytest.
    """

    def __init__(self, project_path: Path):
        """
        Инициализировать интеграцию с тестами для проекта.

        Args:
            project_path: Путь к каталогу проекта
        """
        self.project_path = Path(project_path).resolve()
        self._pytest_available = None

    def is_pytest_available(self) -> bool:
        """
        Проверить, установлен ли и доступен ли pytest.

        Returns:
            True, если pytest доступен
        """
        if self._pytest_available is not None:
            return self._pytest_available

        try:
            result = subprocess.run(
                ["pytest", "--version"],
                capture_output=True,
                timeout=2,
            )
            self._pytest_available = result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError, OSError):
            self._pytest_available = False

        return self._pytest_available

    def has_tests(self) -> bool:
        """
        Проверить, есть ли файлы тестов в проекте.

        Ищет распространенные каталоги и файлы тестов.

        Returns:
            True, если найдены файлы тестов
        """
        # Распространенные шаблоны тестов
        test_patterns = [
            "test_*.py",
            "*_test.py",
        ]

        # Распространенные каталоги тестов
        test_dirs = [
            self.project_path / "tests",
            self.project_path / "test",
            self.project_path,
        ]

        for test_dir in test_dirs:
            if not test_dir.exists():
                continue

            for pattern in test_patterns:
                if list(test_dir.rglob(pattern)):
                    return True

        return False

    def run_tests(self, timeout: int = 30, verbose: bool = False) -> Dict:
        """
        Запустить тесты pytest.

        Args:
            timeout: Максимальное время ожидания тестов (секунды)
            verbose: Если True, включить подробный вывод

        Returns:
            Словарь с результатами тестов:
            - success: bool - успешно ли запущены тесты
            - passed: int - количество пройденных тестов
            - failed: int - количество неудачных тестов
            - output: str - вывод тестов (если подробно)
            - summary: str - краткое резюме
        """
        if not self.is_pytest_available():
            return {
                "success": False,
                "error": "pytest недоступен",
                "passed": 0,
                "failed": 0,
                "summary": "pytest не установлен",
            }

        try:
            args = ["pytest", "-v" if verbose else "-q", "--tb=short"]

            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.project_path,
            )

            output = result.stdout + result.stderr

            # Разбор вывода для подсчета тестов
            passed, failed = self._parse_test_output(output)

            return {
                "success": result.returncode == 0,
                "passed": passed,
                "failed": failed,
                "output": output if verbose else None,
                "summary": self._generate_summary(passed, failed),
                "exit_code": result.returncode,
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "тайм-аут",
                "passed": 0,
                "failed": 0,
                "summary": f"Тесты завершились по тайм-ауту после {timeout}с",
            }
        except (subprocess.SubprocessError, OSError) as e:
            return {
                "success": False,
                "error": str(e),
                "passed": 0,
                "failed": 0,
                "summary": "Не удалось запустить тесты",
            }

    def collect_tests(self) -> Optional[str]:
        """
        Собрать информацию о доступных тестах без их запуска.

        Returns:
            Строка с информацией о сборке тестов или None, если недоступно
        """
        if not self.is_pytest_available():
            return None

        try:
            result = subprocess.run(
                ["pytest", "--collect-only", "-q"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=self.project_path,
            )

            if result.returncode == 0 or result.returncode == 5:  # 5 = не собраны тесты
                return result.stdout.strip()

        except (subprocess.SubprocessError, OSError):
            pass

        return None

    def get_test_summary(self) -> Optional[str]:
        """
        Получить краткое резюме тестов без их запуска.

        Returns:
            Строка резюме или None, если недоступно
        """
        if not self.is_pytest_available():
            return None

        collection = self.collect_tests()
        if collection:
            # Извлечь количество тестов из сборки
            lines = collection.split("\n")
            for line in lines:
                if "test" in line.lower() and any(c.isdigit() for c in line):
                    return line.strip()

        return "Тесты доступны"

    def _parse_test_output(self, output: str) -> tuple[int, int]:
        """
        Разобрать вывод pytest для извлечения количества тестов.

        Args:
            output: Текст вывода pytest

        Returns:
            Кортеж (пройдено, неудачно) количества
        """
        passed = 0
        failed = 0

        # Искать шаблоны вроде "5 пройдено" или "3 неудачно"
        import re

        passed_match = re.search(r"(\d+)\s+passed", output)
        if passed_match:
            passed = int(passed_match.group(1))

        failed_match = re.search(r"(\d+)\s+failed", output)
        if failed_match:
            failed = int(failed_match.group(1))

        return passed, failed

    def _generate_summary(self, passed: int, failed: int) -> str:
        """
        Сгенерировать краткое резюме результатов тестов.

        Args:
            passed: Количество пройденных тестов
            failed: Количество неудачных тестов

        Returns:
            Строка резюме
        """
        total = passed + failed

        if total == 0:
            return "Тесты не найдены"

        if failed == 0:
            return f"✅ Все {passed} тестов пройдены"
        elif passed == 0:
            return f"❌ Все {failed} тестов не пройдены"
        else:
            return f"⚠️  {passed} пройдено, {failed} не пройдено"

    def get_coverage_info(self) -> Optional[Dict]:
        """
        Получить информацию о покрытии тестов (требуется pytest-cov).

        Returns:
            Словарь с информацией о покрытии или None, если недоступно
        """
        if not self.is_pytest_available():
            return None

        try:
            result = subprocess.run(
                ["pytest", "--cov", "--cov-report=term-missing", "-q"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.project_path,
            )

            # Попытка разбора процента покрытия
            import re

            match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", result.stdout)

            if match:
                return {
                    "available": True,
                    "percentage": int(match.group(1)),
                    "output": result.stdout,
                }

        except (subprocess.SubprocessError, OSError):
            pass

        return {"available": False}

    def get_test_info(self) -> Dict:
        """
        Получить всю информацию о тестах за один вызов.

        Returns:
            Словарь с информацией о тестах
        """
        return {
            "pytest_available": self.is_pytest_available(),
            "has_tests": self.has_tests(),
            "summary": self.get_test_summary(),
        }
