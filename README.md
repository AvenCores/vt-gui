

<div align="center">
    <a href="https://www.youtube.com/@avencores/" target="_blank">
      <img src="https://github.com/user-attachments/assets/338bcd74-e3c3-4700-87ab-7985058bd17e" alt="YouTube" height="40">
    </a>
    <a href="https://t.me/avencoresyt" target="_blank">
      <img src="https://github.com/user-attachments/assets/939f8beb-a49a-48cf-89b9-d610ee5c4b26" alt="Telegram" height="40">
    </a>
    <a href="https://vk.ru/avencoresreuploads" target="_blank">
      <img src="https://github.com/user-attachments/assets/dc109dda-9045-4a06-95a5-3399f0e21dc4" alt="VK" height="40">
    </a>
    <a href="https://dzen.ru/avencores" target="_blank">
      <img src="https://github.com/user-attachments/assets/bd55f5cf-963c-4eb8-9029-7b80c8c11411" alt="Dzen" height="40">
    </a>
</div>

# 🦠 VT GUI
<p align="center">
  <a href="https://github.com/AvenCores/vt-gui"><img src="https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54" alt="Python"></a>
  <a href="./LICENSE"><img src="https://img.shields.io/badge/License-GPL--3.0-blue?style=for-the-badge" alt="GPL-3.0 License"></a>
  <a href="https://github.com/AvenCores/vt-gui/releases/latest"><img src="https://img.shields.io/github/v/release/AvenCores/vt-gui?style=for-the-badge" alt="Latest release"></a>
  <a href="https://github.com/AvenCores/vt-gui/stargazers"><img src="https://img.shields.io/github/stars/AvenCores/vt-gui?style=for-the-badge" alt="GitHub stars"></a>
  <img src="https://img.shields.io/github/forks/AvenCores/vt-gui?style=for-the-badge" alt="GitHub forks">
  <a href="https://github.com/AvenCores/vt-gui/watchers">
  <img src="https://img.shields.io/github/watchers/AvenCores/vt-gui?style=for-the-badge" alt="GitHub Watchers"></a>
  <a href="https://github.com/AvenCores/vt-gui/releases"><img src="https://img.shields.io/github/downloads/AvenCores/vt-gui/total?style=for-the-badge" alt="Downloads"></a>
  <a href="https://github.com/AvenCores/vt-gui/pulls"><img src="https://img.shields.io/github/issues-pr/AvenCores/vt-gui?style=for-the-badge" alt="GitHub pull requests"></a>
  <a href="https://github.com/AvenCores/vt-gui/issues"><img src="https://img.shields.io/github/issues/AvenCores/vt-gui?style=for-the-badge" alt="GitHub issues"></a>
</p>

**VT GUI** — это современное кроссплатформенное графическое приложение (GUI) для сервиса **VirusTotal**, написанное на Python с использованием фреймворка **Flet** (на базе Flutter).

Приложение представляет собой удобную графическую оболочку над официальной утилитой командной строки VirusTotal (`vt-cli`), интегрируя её с прямыми HTTP-запросами к VirusTotal API v3 для максимального быстродействия и удобства работы.

![maxresdefault](https://i.ibb.co/Z7S6T6d/flet-Ft-Fc-Lgjb-V9.png)

# 🎦 Видео гайд по установке и использованию программы

![maxresdefault](https://i.ibb.co/39YVYSWV/1.png)

<div align="center">

[**Смотреть на YouTube**](https://www.youtube.com/watch?v=KNdZoy6Ixxo)

[**Смотреть на Dzen**](https://dzen.ru/video/watch/6a5b77343ceaa4017d1d50f6)

[**Смотреть на Rutube**](https://rutube.ru/video/private/c402084c77dabec7cbf4e2152c7187ec/?p=ODGgUgedy78Lfdc2b74mew)

[**Смотреть в VK Video**](https://vkvideo.ru/video-234234162_456239099)

[**Смотреть в Telegram**](https://t.me/avencoreschat/558446)

</div>

---

## ✨ Основные возможности

### 🔎 Проверка файлов (File Scanner)
* **Быстрое сканирование хэша:** Вычисляет хэш SHA-256 локального файла и мгновенно проверяет его через API. Если файл уже проверялся ранее на VirusTotal, отчет загружается без необходимости повторной отправки файла.
* **Загрузка и отправка файлов:** Если файла нет в базе VirusTotal, приложение отправляет его с использованием официального CLI и запускает отслеживание анализа в реальном времени.
* **Мультивыбор и сканирование папок:** Поддержка одновременного сканирования нескольких файлов или всей директории с распределением результатов по отдельным вкладкам.
* **Drag-and-Drop & Буфер обмена:** Файлы можно перетаскивать прямо в окно приложения или нажать `Ctrl + V` для вставки путей из буфера обмена.
* **Контекстное меню ОС:** Поддержка запуска с аргументами командной строки для интеграции в системное контекстное меню «Отправить в VT GUI».
* **Повторный анализ:** Возможность отправить файл на повторную перепроверку в VirusTotal.
* **Экспорт отчетов:** Сохранение подробного отчета анализа в JSON через системное диалоговое окно или в папку «Загрузки».

### 🌐 Threat Intelligence (Аналитика угроз)
* **Анализ URL:** Проверка интернет-ссылок на вредоносность и отправка неизвестных URL на сканирование.
* **Анализ доменов:** Информация о репутации домена, регистраторе, дате создания, связанных субдоменах и DNS-разрешениях.
* **Анализ IP-адресов:** Проверка репутации IP, владельца AS и страны регистрации.
* **Полнотекстовый поиск:** Поиск файлов, хэшей и отчетов по базе VirusTotal с возможностью скачивания образцов (при наличии Premium API ключа).
* **Экспорт и переанализ:** Быстрый запрос повторного анализа и экспорт результатов в JSON.

### 🛠️ Инструменты VirusTotal (VT Tools)
* **Сравнение файлов (`vt diff`):** Наглядное сравнение двух хэшей SHA-256 с выводом структурных и поведенческих различий между ними.
* **YARA-правила (Livehunt):** Просмотр и проверка списка активных наборов правил YARA для мониторинга угроз.

### 📜 История сканирований
* **Автоматическое сохранение:** Все сканирования файлов и проверки URL/доменов/IP автоматически сохраняются в локальную историю (`history.json`).
* **Поиск и фильтрация:** Быстрый поиск по историческим записям.
* **Повторный анализ и веб-отчет:** Переход к сохраненным результатам, повторное сканирование в один клик и открытие отчета на сайте VirusTotal.
* **Управление записями:** Удаление отдельных записей или полная очистка истории.

### 🔐 Безопасность и автоматизация CLI
* **Автоматическая установка:** Определение ОС (Windows, Linux, macOS) и архитектуры (x64, ARM64, x86, ARM) с автоматической загрузкой официального `vt-cli` с GitHub.
* **Контроль хэш-сумм:** Сравнение скачанных бинарных файлов и ZIP-архивов с официальным списком SHA-256 хэшей релиза.
* **Пользовательский CLI:** Возможность указать собственный бинарный файл `vt`/`vt.exe` с сохранением его хэша после подтверждения.
* **Переустановка CLI:** Кнопка быстрого обновления/переустановки CLI прямо из настроек.
* **Валидация API-ключа:** Проверка работоспособности ключа при вводе и синхронизация с `~/.vt.toml` и `.env`.

### 🌍 Локализация и Дизайн
* **Современный интерфейс:** Премиальный темно-синий неоновый дизайн, адаптивные шрифты (Segoe UI, SF Pro), анимация переходов и индикаторы вердиктов антивирусов.
* **12 языков:** Поддержка английского, русского, испанского, немецкого, французского, португальского, турецкого, украинского, китайского, японского, корейского и арабского языков с автоматическим определением языка системы.
* **Проверка обновлений:** Встроенный инструмент проверки новых версий приложения через GitHub Releases.

---

## 📂 Структура проекта

* [source/main.py](source/main.py) — Главный файл приложения, точка входа, конфигурация окна Flet, обработка аргументов командной строки и маршрутизация между экранами.
* **`source/app/`** — Основной модуль логики приложения:
  * [source/app/config.py](source/app/config.py) — Настройки окружения (синхронизация `.env` и `~/.vt.toml`), автоопределение языка, база хэшей `vt-cli` и строки локализации.
  * [source/app/cli_manager.py](source/app/cli_manager.py) — Менеджер работы с бинарником `vt` (проверка, вычисление SHA-256, скачивание и распаковка релизов GitHub в изолированный каталог).
  * [source/app/clipboard_utils.py](source/app/clipboard_utils.py) — Утилиты для безопасной работы с буфером обмена (включая Win32 fallback для стабильности).
  * [source/app/vt_api.py](source/app/vt_api.py) — Взаимодействие с VirusTotal v3 REST API (поиск хэшей, сканирование URL, домены, IP, поиск, субдомены, DNS, diff файлов).
  * [source/app/exporter.py](source/app/exporter.py) — Экспорт отчетов сканирований и аналитики в файлы JSON через нативный системный диалог файла или в папку «Загрузки».
  * [source/app/history_manager.py](source/app/history_manager.py) — Менеджер истории сканирований и поисковых запросов (`history.json`).
  * [source/app/strings.json](source/app/strings.json) — Файл локализации со всеми текстовыми строками интерфейса.
  * **`services/`** — Сервисный слой бизнес-логики:
    * [source/app/services/scan_service.py](source/app/services/scan_service.py) — Пайплайн многопоточного сканирования файлов (хэширование -> VT API -> отправка CLI -> отслеживание).
  * **`ui/`** — Графический интерфейс и компоненты:
    * [source/app/ui/theme.py](source/app/ui/theme.py) — Дизайн-система (стили, карточки статистики, список антивирусных вердиктов).
    * [source/app/ui/scanner_view.py](source/app/ui/scanner_view.py) — Стартовый экран выбора файла/папки и зоны Drag-and-Drop.
    * [source/app/ui/scanning_view.py](source/app/ui/scanning_view.py) — Экран прогресса сканирования.
    * [source/app/ui/results_view.py](source/app/ui/results_view.py) — Панель результатов с вердиктом, сводкой детектов, антивирусами и экспортом.
    * [source/app/ui/intelligence_view.py](source/app/ui/intelligence_view.py) — Экраны проверки URL, доменов, IP-адресов и поисковых запросов.
    * [source/app/ui/tools_view.py](source/app/ui/tools_view.py) — Дополнительный инструментарий: сравнение файлов (`vt diff`) и наборы YARA-правил (`Livehunt`).
    * [source/app/ui/history_view.py](source/app/ui/history_view.py) — Экран истории сканирований с поиском, повторным анализом и очисткой.
    * [source/app/ui/install_view.py](source/app/ui/install_view.py) — Мастер установки `vt-cli` (автоматическая загрузка или ручной выбор).
    * [source/app/ui/settings_dialog.py](source/app/ui/settings_dialog.py) — Диалог настроек (управление API-ключом, переустановка CLI).
    * [source/app/ui/api_key_dialog.py](source/app/ui/api_key_dialog.py) — Диалог ввода API-ключа при первом запуске.
    * [source/app/ui/footer.py](source/app/ui/footer.py) — Нижняя панель с социальными сетями, проверкой обновлений и диалогом «О программе».

---

## 🚀 Установка и запуск из исходников

Для работы проекта требуется установленный **Python 3.8+**.

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/AvenCores/vt-gui.git
   cd vt-gui
   ```

2. Установите зависимости:
   ```bash
   pip install -r source/requirements.txt
   ```

3. Запустите приложение:
   ```bash
   python source/main.py
   ```
   *Или с помощью CLI утилиты Flet:*
   ```bash
   flet run source/main.py
   ```

При первом запуске приложение попросит ввести ваш персональный API-ключ VirusTotal (его можно бесплатно получить на официальном сайте). Ключ сохранится локально и будет использоваться для всех последующих сессий.

---

## 📦 Сборка в исполняемый файл

Проект собирается в один независимый исполняемый файл с помощью **PyInstaller**. В репозитории настроен процесс автоматической компиляции для GitHub Actions ([.github/workflows/build.yml](.github/workflows/build.yml)), поддерживающий сборки для Windows (x64/ARM64), Linux (x64/ARM64) и macOS (ARM64).

Если вы хотите собрать приложение локально, выполните следующие шаги из папки `source`:

### Windows (x64 / ARM64)
```bash
cd source
pyinstaller --onefile --noconsole --icon=assets/icon.ico --add-data="assets;assets" --add-data="app/strings.json;app" --name="VirusTotal_File_Scanner_Windows_x64" --noupx --clean --version-file=version.txt main.py
```

### Linux (x64 / ARM64)
```bash
cd source
pyinstaller --onefile --icon=assets/icon.ico --add-data="assets:assets" --add-data="app/strings.json:app" --name="VirusTotal_File_Scanner_Linux_x64" --clean main.py
```

### macOS (ARM64)
Используется специальный spec-файл для исключения конфликтов nested-библиотек Flet:
```bash
cd source
pyinstaller --clean VirusTotal_File_Scanner_macOS.spec
```

---

## 📜 Лицензия

Проект распространяется под лицензией GPL-3.0. Полный текст лицензии содержится в файле [`LICENSE`](LICENSE).

---

## 💰 Поддержать автора
* **SBER**: `2202 2050 1464 4675`
