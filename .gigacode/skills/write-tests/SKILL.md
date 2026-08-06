---
name: write-tests
description: Пишет и правит автотесты (API и UI) по правилам проекта.
  Используй, когда нужно написать новый тест, исправить упавший или
  покрыть изменения после обновления DTO.
---

## Правила проекта

- Тесты лежат в папке `tests/`, структура зеркалит `src/`
- Именование: `test_<имя_функции>_<сценарий>`
- Используем pytest + httpx для API, playwright для UI

## Инструкция

1. Изучи существующие тесты рядом с целевым модулем.
2. Напиши тест в том же стиле.
3. Проверь, что тест запускается без ошибок.# Write Tests Skill

## Overview
This skill provides automated test creation capabilities.

## Capabilities
- Generate unit tests for functions and classes
- Create integration tests for API endpoints
- Write component tests for React components
- Generate test fixtures and mocks

## Usage
Invoke with `/write-tests` command followed by file path or code snippet.

## Supported Testing Frameworks
- **Python**: pytest
- **Java**: JUnit 5 + MockMvc
- **JavaScript/TypeScript**: Vitest + React Testing Library
