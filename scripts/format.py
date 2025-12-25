#!/usr/bin/env python3
"""Скрипт для автоматического форматирования кода."""
import subprocess
import sys

print("Форматирование кода...")

commands = [
    "isort app/ tests/",
    "black app/ tests/",
    "echo 'Форматирование завершено'"
]

for cmd in commands:
    subprocess.run(cmd, shell=True)

sys.exit(0)
