# Исследование форматов Anomaly

Документ фиксирует результаты исследования игровых архивов и сверку бинарных структур с реализацией X-Ray. Непроверенные предположения явно отмечаются.

## 1. Game Graph

Источник: `db/configs/spawns.db0` → chunk типа 4 (Game Graph).

Размер извлечённого чанка: 86 177 339 байт.

| Поле | Значение |
|---|---:|
| Version | 10 |
| Vertex count | 5 345 |
| Edge count | 13 444 |
| Level Point count | 764 226 |
| Level count | 34 |
| Vertex offset | 1 715 |
| Edges offset | 226 205 |
| Points offset | 306 869 |
| GUID | `defae07743cab24b9c71f4729f54e866` |

### Структуры

| Структура | Формат | Размер |
|---|---|---:|
| Header | `<BHII16sB` | 28 байт |
| Vertex | `<ffffffBBBBBBBBIIBB` | 42 байта |
| Edge | `<Hf` | 6 байт |
| Level Point | `<fffIf` | 20 байт |

Запись уровня содержит null-terminated имя, три float координаты, однобайтовый ID, null-terminated section и 16-байтовый GUID.

В записи вершины:
- первые 6 float — локальная и глобальная координаты;
- первый byte — ID уровня;
- следующие 3 byte — 24-битный `level_vertex_id`;
- следующие 4 byte — `vertex_types`;
- далее два uint32 byte-offset и два byte-счётчика.

`edge_offset` и `point_offset` — байтовые смещения относительно начала массива вершин, а не индексы. Парсер учитывает это при проверке диапазонов.

### Embedded Cross Tables

После массива Level Points в Game Graph располагаются блоки Cross Table для уровней, отсортированные по ID уровня. Перед каждым блоком записан uint32 размер блока, включающий само поле размера.

Внутренний заголовок Cross Table занимает 44 байта:
- uint32 version;
- uint32 level_vertex_count;
- uint32 game_vertex_count;
- 16-byte level GUID;
- 16-byte Game Graph GUID.

После заголовка идут `level_vertex_count` ячеек по 6 байт: `<Hf` — Game Graph vertex ID и distance. Таблица сопоставляет индекс вершины `level.ai` с глобальной вершиной Game Graph.

Отдельный файл `.gct` не обязателен: таблицы могут быть встроены в общий Game Graph. Это объясняет, почему поиск файла `.gct` в архиве отдельной локации мог ничего не показать.

### Реализация и память

`src/anomaly_pda/game_graph.py` читает заголовок, уровни, вершины, рёбра, Level Points и embedded Cross Tables. Level Points выдаются итератором, ячейки Cross Table читаются по индексу через memoryview. Это позволяет не создавать сотни тысяч Python-объектов.

## 2. Level Graph — level.ai

Подтверждён заголовок длиной 56 байт:

| Смещение | Тип | Поле |
|---:|---|---|
| 0 | uint32 | version |
| 4 | uint32 | vertex_count |
| 8 | float32 | cell_size |
| 12 | float32 | factor_y |
| 16 | 6 × float32 | bounding box min/max |
| 40 | 2 × uint64 | GUID |

Поддерживаемые форматы узла:
- версия 10: 23 байта на вершину;
- версия 13: 25 байт на вершину.

Узел содержит четыре соседних link ID, cover high/low, packed plane normal и упакованную позицию. Для v10 четыре ссылки упакованы в 92 бита (4 × 23), для v13 — в 104 бита (4 × 26). Позиция v10 занимает 5 байт: 24-bit XZ grid key и uint16 Y. В v13 XZ key занимает 4 байта.

Размеры файлов из Anomaly совпадают с формулой:

| Файл | Размер | Вычисление | Число вершин |
|---|---:|---:|---:|
| `fake_start/level.ai` | 14 569 | 56 + 631 × 23 | 631 |
| `zaton/level.ai` | 42 578 829 | 56 + 1 851 251 × 23 | 1 851 251 |

Это сильная независимая проверка длины заголовка и записи. Новый парсер ещё должен быть прогнан по полным файлам в Termux.

Позиция узла декодируется через bounding box, cell_size, row_length и factor_y. Модуль `src/anomaly_pda/level_graph.py` поддерживает v10/v13, декодирует четыре ссылки и преобразует индекс узла в мировые координаты. Для крупных карт вершины декодируются по запросу: в памяти остаётся исходный бинарный буфер, а не миллионы Python-объектов.

## 3. Связка графов и маршрутизация

Cross Table позволяет преобразовать локальный `level_vertex_id` в глобальный `game_vertex_id`.

Модуль `src/anomaly_pda/routing.py` содержит:
- A* внутри одного Level Graph по четырём соседним ссылкам;
- Dijkstra между глобальными вершинами Game Graph;
- сборку маршрута в локальные сегменты, разделённые переходами между уровнями;
- проверку соответствия GUID и количества ячеек Cross Table перед использованием уровня.

Это первая рабочая архитектура маршрута, но её корректность на реальных маршрутах ещё должна быть подтверждена прогоном в Termux.

## 4. Архивы уровней

Найдены 34 архива уровней и отдельный `levels.db0`.

Примеры:
- `levels/fake_start/level.ai` в `levels.db0`, 14 569 байт.
- `levels/zaton/level.ai` в `level_zaton.db0`, 42 578 829 байт.

В архиве Zaton также присутствуют `level.cform`, `level.details`, `level.game`, `level.geom`, `level.geomx`, `level.hom`, `level.ltx` и `level.spawn`.

## 5. Источники сверки

Структуры Level Graph и Cross Table сверены с открытым парсером X-Ray форматов: [Voxura/xray-anomaly — ai_graph.rs](https://github.com/Voxura/xray-anomaly/blob/cecc598c855ed2f57703c61884e2123387dc12fd/crates/xray-formats/src/ai_graph.rs). Он описывает `level.ai` v10/v13, 56-байтовый заголовок, 23/25-байтовые узлы, 44-байтовый Cross Table header и embedded Cross Tables в Game Graph.

Для чтения X-Ray DB архивов используется `DBReader.XRReader` из stalker-tools:

```python
from DBReader import XRReader
reader = XRReader("/path/to/archive.db0", "xdb")
```

Игровые архивы и извлечённые данные не добавлять в Git.
