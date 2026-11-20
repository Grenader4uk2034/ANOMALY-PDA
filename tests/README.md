# Tests

Запуск:

```bash
python -m unittest discover -s tests -v
```

Текущие синтетические проверки покрывают:
- Game Graph header, level table and vertex decoding;
- Game Graph edge target validation;
- embedded Cross Table header/cells and lookup;
- Level Graph versions 10 and 13;
- packed neighbor links and world-coordinate decoding;
- truncated binary payload rejection;
- local A* route on a small test graph.

Эти тесты проверяют реализацию на искусственных бинарных примерах. Они не заменяют обязательную проверку на полном наборе Anomaly.

Реальные игровые архивы и извлечённые данные не добавлять в репозиторий.
