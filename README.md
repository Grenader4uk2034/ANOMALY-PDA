# ANOMALY-PDA

Инструменты и будущий интерактивный КПК для **S.T.A.L.K.E.R. Anomaly**: карта Зоны, игровые графы, точки переходов, маршруты и навигация.

## Реализовано

- Парсер Game Graph: глобальные вершины, рёбра и Level Points.
- Чтение встроенных в Game Graph Cross Tables.
- Парсер `level.ai` версий 10 и 13.
- Декодирование четырёх соседних ссылок каждой AI-вершины.
- Преобразование координат AI-узлов в мировые координаты.
- Синтетические unit-тесты бинарных форматов.

## Быстрый старт

Требуется Python 3.10+.

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
```

После извлечения Game Graph payload (chunk type 4):

```bash
anomaly-pda-graph /path/to/game_graph_payload.bin
```

Для отдельного файла уровня:

```bash
anomaly-pda-level-graph /path/to/level.ai
anomaly-pda-level-graph /path/to/level.ai --vertex 100
```

Оба CLI работают с уже извлечёнными бинарными payload. Чтение внешних X-Ray DB архивов будет отдельным слоем.

## Проверенные данные текущей Anomaly установки

- Game Graph: 5 345 вершин, 13 444 ребра, 764 226 Level Points, 34 уровня.
- `fake_start/level.ai`: 631 вершина (56 + 631 × 23 = 14 569 байт).
- `zaton/level.ai`: 1 851 251 вершина (56 + 1 851 251 × 23 = 42 578 829 байт).
- Cross Table хранит отображение локальной вершины в глобальную вершину Game Graph и может быть встроена в Game Graph.

## Структура

```
ANOMALY-PDA/
├── docs/FORMAT_RESEARCH.md
├── src/anomaly_pda/
│   ├── __init__.py
│   ├── game_graph.py
│   └── level_graph.py
├── tests/
│   ├── README.md
│   └── test_game_graph.py
├── pyproject.toml
├── STATUS.md
└── README.md
```

## Дальнейшая работа

1. Запустить тесты и парсеры на реальных игровых файлах в Termux.
2. Сверить GUID и число записей Cross Table с Level Graph каждой локации.
3. Собрать объединённую модель графов и проверить маршруты.
4. Экспортировать данные карты для будущего интерфейса КПК.

См. [статус](STATUS.md) и [исследование форматов](docs/FORMAT_RESEARCH.md).
