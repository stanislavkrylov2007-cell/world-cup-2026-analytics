# Database Setup

## Goal

Этот этап нужен для первого полноценного SQL-слоя проекта: создать таблицу `matches`, загрузить в неё стандартизированные матчи и запускать базовые аналитические запросы.

## Install PostgreSQL

1. Установи PostgreSQL локально с официального установщика для Windows, macOS или Linux.
2. Убедись, что сервер PostgreSQL запущен.
3. Запомни:
   - host;
   - port;
   - database name;
   - username;
   - password.

## Create a Local Database

Пример через `psql`:

```sql
CREATE DATABASE world_cup_analytics;
```

Если база уже существует, создавать её повторно не нужно.

## Fill `.env`

Создай `.env` на основе `.env.example` и укажи свои значения:

```env
APP_ENV=dev
DB_HOST=localhost
DB_PORT=5432
DB_NAME=world_cup_analytics
DB_USER=postgres
DB_PASSWORD=your_password_here
```

Не добавляй `.env` в Git.

## Check the Connection

Проверь загрузку конфигурации:

```bash
wca-check-config
```

Команда не должна выводить пароль.

## Create the Table and Load the CSV

Сначала убедись, что у тебя уже есть стандартизированный файл:

```text
data/interim/matches_standardized.csv
```

Затем выполни:

```bash
wca-load-postgres data/interim/matches_standardized.csv
```

Команда:

- создаст таблицу `matches`, если её ещё нет;
- загрузит строки в транзакции;
- покажет количество загруженных строк;
- проверит количество строк в таблице для текущего `source_file`.

## Reload the Same Source File

Если строки с тем же `source_file` уже есть, обычная загрузка завершится ошибкой, чтобы защитить от случайного дублирования.

Для повторной загрузки именно этого файла используй:

```bash
wca-load-postgres data/interim/matches_standardized.csv --replace
```

`--replace` удаляет только строки с тем же `source_file`, а не всю таблицу.

## Run SQL Files

Примеры запуска запросов через `psql`:

```bash
psql -d world_cup_analytics -f sql/queries/01_dataset_overview.sql
psql -d world_cup_analytics -f sql/queries/05_home_advantage.sql
```

## Common Connection Errors

- `Required environment variable 'DB_HOST' is not set.`
  - Значит, не заполнен `.env` или переменные окружения не экспортированы.
- `connection refused`
  - PostgreSQL не запущен или указан неверный `host`/`port`.
- `password authentication failed`
  - Неверный логин или пароль.
- `database does not exist`
  - База не создана или указано неверное имя.

## Why Secrets Are Not Stored in Git

- Пароли и другие секреты не должны попадать в репозиторий.
- Один и тот же проект может использоваться на разных машинах и с разными локальными настройками PostgreSQL.
- `.env` подходит для локальной разработки и не должен публиковаться.
