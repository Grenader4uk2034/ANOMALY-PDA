# ANOMALY-PDA

Инструменты и будущий интерактивный КПК для **S.T.A.L.K.E.R. Anomaly**: карта Зоны, игровые графы, точки переходов, маршруты и навигация.

## Реализовано в коде

- Парсер Game Graph: глобальные вершины, рёбра и Level Points.
- Чтение встроенных в Game Graph Cross Tables.
- Парсер `level.ai` версий 10 и 13.
- Декодирование четырёх соседних ссылок каждой AI-вершины.
- Преобразование координат AI-узлов в мировые координаты.
- Экономное чтение крупных Level Graph: вершины декодируются по запросу, без создания миллионов Python-объектов.
- A* для перемещения внутри уровня и Dijkstra для межуровневого Game Graph.
- Сборка маршрута в локальные участки и переходы между уровнями.
- Сверка GUID и количества вершин между Level Graph и Cross Table.

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

Парсеры принимают извлечённые бинарные данные; чтение внешних X-Ray DB архивов будет отдельным слоем.

## Подтверждённые размеры файлов Anomaly

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
│   ├── level_graph.py
│   └── routing.py
├── tests/
│   ├── README.md
│   └── test_game_graph.py
├── pyproject.toml
├── STATUS.md
└── README.md
```

## Следующий этап

1. Запустить тесты и парсеры на реальных игровых файлах в Termux.
2. Сверить GUID и число ячеек Cross Table с `level.ai` каждой локации.
3. Проверить маршруты на реальных уровнях и переходах.
4. Добавить загрузчик X-Ray DB архивов.
5. Экспортировать карту/графы для интерфейса КПК.

См. [статус](STATUS.md) и [исследование форматов](docs/FORMAT_RESEARCH.md).
