# ANOMALY-PDA

Инструменты и будущий интерактивный КПК для **S.T.A.L.K.E.R. Anomaly**: карта Зоны, игровые графы, точки переходов, маршруты и навигация.

## Текущее состояние

Первый рабочий модуль — валидируемый парсер Game Graph — добавлен в `src/anomaly_pda/game_graph.py`. Он принимает **уже извлечённый payload чанка Game Graph**, а не целый X-Ray DB архив.

Подтверждённые результаты исследования текущих архивов:
- 5 345 вершин;
- 13 444 ребра;
- 764 226 Level Points;
- 34 уровня;
- Edge: 6 байт (`<Hf`);
- Level Point: 20 байт (`<fffIf`).

## Быстрый старт

Python 3.10+:

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
```

После извлечения Game Graph payload в отдельный файл:

```bash
anomaly-pda-graph /path/to/game_graph_payload.bin
```

Или:

```bash
python -m anomaly_pda.game_graph /path/to/game_graph_payload.bin
```

Парсер проверяет границы массивов, диапазоны рёбер и точек каждой вершины, ссылки на целевые вершины и соответствие сумм счётчиков заголовку.

## Структура

```
ANOMALY-PDA/
├── docs/FORMAT_RESEARCH.md
├── src/anomaly_pda/
│   ├── __init__.py
│   └── game_graph.py
├── tests/
│   ├── README.md
│   └── test_game_graph.py
├── pyproject.toml
├── STATUS.md
└── README.md
```

## Следующие этапы

- [x] Реализовать базовый Game Graph parser.
- [x] Добавить синтетические тесты форматов записей.
- [ ] Проверить новый парсер на полном payload из Anomaly.
- [ ] Разобрать Level Graph (`level.ai`).
- [ ] Найти и разобрать Cross Table.
- [ ] Связать глобальный Game Graph с локальными графами.
- [ ] Извлечь точки интереса и реализовать маршрутизацию.
- [ ] Создать интерфейс интерактивного КПК.

## Правила

Не добавлять игровые архивы и извлечённые игровые данные в Git. Непроверенные структуры помечать как гипотезы. См. [STATUS.md](STATUS.md) и [документ исследования форматов](docs/FORMAT_RESEARCH.md).
