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

![maxresdefault](https://i.ibb.co/8nB79Cn2/chrome-Go-WZgprng-Z.png)

# 🎦 Видео гайд по установке и решению проблем

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
* **Мультивыбор файлов:** Поддержка одновременного сканирования нескольких файлов с распределением по отдельным вкладкам результатов.
* **Drag-and-Drop & Буфер обмена:** Файлы можно перетаскивать прямо в окно приложения или просто нажать `Ctrl + V` для вставки путей к файлам из буфера обмена.
* **Контекстное меню ОС:** Приложение поддерживает запуск с аргументами командной строки, что позволяет интегрировать его в контекстное меню операционной системы «Отправить в VT GUI».

### 🌐 Threat Intelligence (Аналитика угроз)
* **Анализ URL:** Проверка интернет-ссылок на вредоносную активность.
* **Анализ доменов:** Получение информации о репутации домена, его регистраторе и вердиктах антивирусных движков.
* **Анализ IP-адресов:** Проверка репутации IP-адресов.
* **Полнотекстовый поиск:** Поиск файлов и отчетов в базе VirusTotal по сложным запросам с возможностью скачивания образцов (требуется Premium-ключ API).

### 📜 История сканирований
* **Автоматическое сохранение:** Все сканирования файлов и проверки URL/доменов/IP автоматически сохраняются в историю.
* **Повторный анализ:** Одним кликом можно повторить сканирование файла или вернуться к результатам проверки.
* **Управление записями:** Удаление отдельных записей или полная очистка истории с подтверждением.
* **Веб-отчёт:** Быстрый переход к полному отчёту на VirusTotal для любой записи из истории.

### 🛠️ Безопасность и автоматизация CLI
* **Автоматическая установка:** Приложение само определяет операционную систему, разрядность процессора и скачивает официальный релиз `vt-cli` с GitHub.
* **Контроль хэш-сумм:** Безопасность превыше всего. Все скачанные бинарные файлы проверяются по встроенному списку SHA-256 хэшей официальных версий.
* **Пользовательский CLI:** Вы можете вручную загрузить свой бинарный файл `vt`/`vt.exe`, и приложение сохранит его хэш-сумму как доверенную после вашего подтверждения.
* **Переустановка CLI:** Кнопка переустановки VirusTotal CLI прямо из настроек приложения.
* **Проверка API ключа:** Встроенная проверка работоспособности API ключа с мгновенной обратной связью.
* **Синхронизация конфигурации:** API-ключ автоматически синхронизируется с официальным файлом конфигурации `~/.vt.toml`.

### 🌍 Локализация и Дизайн
* **Интерфейс «из коробки»:** Премиальный темно-синий неоновый дизайн с плавными анимациями, интерактивными карточками результатов и подробными сводками антивирусного ПО.
* **12 языков:** Автоматическое определение языка системы с возможностью переключения в шапке программы. Поддерживаются английский, русский, испанский, немецкий, французский, португальский, турецкий, украинский, китайский, японский, корейский и арабский языки.
* **Проверка обновлений:** Кнопка в нижней панели для проверки наличия новой версии приложения через GitHub Releases. При доступном обновлении — одна кнопка для перехода к скачиванию.

---

## 📂 Структура проекта

* [main.py](file:///C:/Users/avencores/Desktop/vt-gui/source/main.py) — Главный файл приложения, точка входа, конфигурация окна Flet, обработка аргументов командной строки и переключение основных экранов.
* **`app/`** — Основной модуль логики приложения:
  * [app/config.py](file:///C:/Users/avencores/Desktop/vt-gui/source/app/config.py) — Настройки окружения (чтение/запись `.env` и `~/.vt.toml`), автоматическое определение языка системы, база официальных хэшей `vt-cli` и инициализация строк локализации.
  * [app/cli_manager.py](file:///C:/Users/avencores/Desktop/vt-gui/source/app/cli_manager.py) — Менеджер для работы с бинарным файлом `vt` (проверка наличия, хэширование, скачивание ZIP-архивов релизов с GitHub и распаковка в изолированную директорию).
  * [app/vt_api.py](file:///C:/Users/avencores/Desktop/vt-gui/source/app/vt_api.py) — Прямые запросы к HTTP API VirusTotal v3 для быстрого поиска хэша перед загрузкой.
  * [app/history_manager.py](file:///C:/Users/avencores/Desktop/vt-gui/source/app/history_manager.py) — Менеджер истории сканирований (загрузка, сохранение, добавление и удаление записей из JSON).
  * [app/strings.json](file:///C:/Users/avencores/Desktop/vt-gui/source/app/strings.json) — Файл локализации со всеми текстовыми строками интерфейса.
  * **`services/`** — Сервисный слой бизнес-логики:
    * [scan_service.py](file:///C:/Users/avencores/Desktop/vt-gui/source/app/services/scan_service.py) — Многопоточный пайплайн сканирования файлов (вычисление хэша -> поиск в VT -> загрузка через CLI -> ожидание анализа -> вывод отчета).
  * **`ui/`** — Элементы интерфейса и графические представления:
    * [ui/theme.py](file:///C:/Users/avencores/Desktop/vt-gui/source/app/ui/theme.py) — Кастомные графические компоненты (карточки статистики, виджеты результатов движков с семантической подсветкой угроз).
    * [ui/scanner_view.py](file:///C:/Users/avencores/Desktop/vt-gui/source/app/ui/scanner_view.py) — Экран приветствия с кнопкой выбора файла / зоной Drag-and-Drop и статусом валидации CLI.
    * [ui/scanning_view.py](file:///C:/Users/avencores/Desktop/vt-gui/source/app/ui/scanning_view.py) — Экран прогресса текущего сканирования.
    * [ui/results_view.py](file:///C:/Users/avencores/Desktop/vt-gui/source/app/ui/results_view.py) — Панель результатов с диаграммой вердикта, сводкой детектов и раскрывающимся полным списком антивирусов.
    * [ui/intelligence_view.py](file:///C:/Users/avencores/Desktop/vt-gui/source/app/ui/intelligence_view.py) — Логика и верстка вкладок для поиска по URL, IP, доменам и текстовым запросам.
    * [ui/history_view.py](file:///C:/Users/avencores/Desktop/vt-gui/source/app/ui/history_view.py) — Экран истории сканирований с карточками записей и управлением.
    * [ui/install_view.py](file:///C:/Users/avencores/Desktop/vt-gui/source/app/ui/install_view.py) — Экран мастера установки `vt-cli` (автоматическая загрузка или ручной выбор файла).
    * [ui/settings_dialog.py](file:///C:/Users/avencores/Desktop/vt-gui/source/app/ui/settings_dialog.py) — Модальное окно настроек для смены API-ключа, проверки ключа и переустановки CLI.
    * [ui/api_key_dialog.py](file:///C:/Users/avencores/Desktop/vt-gui/source/app/ui/api_key_dialog.py) — Диалог ввода API-ключа, блокирующий работу до момента его настройки при первом запуске.
    * [ui/footer.py](file:///C:/Users/avencores/Desktop/vt-gui/source/app/ui/footer.py) — Нижняя панель приложения со ссылками на социальные сети автора, кнопкой проверки обновлений и диалогом «О программе».

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

Проект собирается в один независимый исполняемый файл с помощью **PyInstaller**. В репозитории уже настроен процесс автоматической компиляции для GitHub Actions ([.github/workflows/build.yml](file:///C:/Users/avencores/Desktop/vt-gui/.github/workflows/build.yml)), поддерживающий сборки для Windows (x64/ARM64), Linux (x64/ARM64) и macOS (ARM64).

Если вы хотите собрать приложение локально, выполните следующие шаги:

### Windows
```bash
cd source
pyinstaller --onefile --noconsole --icon=assets/icon.ico --add-data="assets;assets" --add-data="app/strings.json;app" --name="VirusTotal_File_Scanner_Windows_x64" --noupx --clean --version-file=version.txt main.py
```

### Linux
```bash
cd source
pyinstaller --onefile --icon=assets/icon.ico --add-data="assets:assets" --add-data="app/strings.json:app" --name="VirusTotal_File_Scanner_Linux_x64" --clean main.py
```

### macOS
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


