# Android APK

Первые Android-сборки ANOMALY-PDA выполняются автоматически через GitHub Actions.

## Сборка
- Workflow: `.github/workflows/android-apk.yml`
- Android application module: `app`
- Package: `ru.anomalypda`
- Min SDK: 23 (Android 6.0)
- Target SDK: 35
- Версия: 0.1.0 (debug)

Внутри APK веб-карта из папки `web/` упаковывается в assets, а справочные JSON-данные — из `data/reference/`. Для запуска не требуется интернет или локальный сервер.

## Получить APK
1. Открой вкладку **Actions** в репозитории GitHub.
2. Выбери workflow **Android APK**.
3. Открой успешный запуск.
4. В разделе Artifacts скачай `ANOMALY-PDA-debug-apk`.
5. Распакуй архив artifact и установи `app-debug.apk` на Android.

Это первая оболочка APK для проверки на телефоне. Визуальный тест на реальном Android-устройстве пока не выполнен.
