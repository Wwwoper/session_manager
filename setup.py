#!/usr/bin/env python3
"""
Setup configuration for Session Manager
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="session-manager",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Smart session manager for developers - track time, save context, and integrate with your workflow",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Wwwoper/session-manager",
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
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
        # Только стандартная библиотека для MVP
        # Никаких внешних зависимостей
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
    keywords="session manager time tracking context git productivity development",
    project_urls={
        "Bug Reports": "https://github.com/Wwwoper/session-manager/issues",
        "Source": "https://github.com/Wwwoper/session-manager",
    },
)