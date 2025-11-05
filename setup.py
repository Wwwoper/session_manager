#!/usr/bin/env python3
"""
Setup script for Session Manager
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_file = Path(__file__).parent / "README.md"
long_description = (
    readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""
)

# Read version from __init__.py
version = "0.1.0"
init_file = Path(__file__).parent / "session_manager" / "__init__.py"
if init_file.exists():
    for line in init_file.read_text(encoding="utf-8").splitlines():
        if line.startswith("__version__"):
            version = line.split("=")[1].strip().strip('"').strip("'")
            break

setup(
    name="session_manager",
    version=version,
    author="Wwwoper",
    author_email="rs.berenev@yandex.ru",
    description="Умный трекер сессий работы с сохранением контекста для разработчиков",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Wwwoper/session_manager.git",
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Version Control",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: Console",
    ],
    python_requires=">=3.8",
    install_requires=[
        # Нет жестких зависимостей - только стандартная библиотека!
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "session=session_manager.__main__:main",
        ],
    },
    keywords="session time-tracking context development workflow git productivity",
    project_urls={
        "Bug Reports": "https://github.com/Wwwoper/session_manager/issues",
        "Source": "https://github.com/Wwwoper/session_manager",
        "Documentation": "https://github.com/Wwwoper/session_manager#readme",
    },
    include_package_data=True,
    zip_safe=False,
)
