# World Cup 2026 Analytics

Historical international football analytics with a reproducible CSV → Python ETL → PostgreSQL → SQL views → Redash workflow.

## Посмотреть результат без установки

Проект отвечает на вопросы: как менялся объём международных матчей, какие команды лидируют по историческим победам и как различаются результаты на нейтральных и домашних полях.

Реализованы подготовка и валидация данных на Python, загрузка в PostgreSQL, три аналитические SQL-витрины и дашборд Redash с шестью запросами. В Redash используется отдельный пользователь базы с правами чтения.

Ниже — реальные графики, экспортированные из работающего локального Redash. Для просмотра этих результатов Docker не требуется.

| Матчи по годам | Среднее число голов |
| --- | --- |
| ![Число матчей по годам в Redash](docs/images/redash-matches.png) | ![Среднее число голов по годам в Redash](docs/images/redash-goals.png) |
| **Команды по числу побед** | **Турниры по числу матчей** |
| ![Исторический рейтинг команд в Redash](docs/images/redash-teams.png) | ![Число матчей по турнирам в Redash](docs/images/redash-tournaments.png) |

Дашборд показывает 49 520 матчей, 201 турнир и среднее 2,94 гола за матч. В 36 364 матчах на ненейтральном поле доля побед хозяев составляет 50,75%, гостей — 26,40%. Это описание выборки, а не доказательство причинного эффекта домашнего поля. Последний год представлен только по 19 июля 2026 года, поэтому его объём не следует сравнивать с полными годами без поправки.

### Что посмотреть в коде

- [Python ETL и загрузка в базу](src/world_cup_analytics/cli.py).
- [Таблица матчей и ограничения качества](sql/ddl/001_create_matches.sql).
- [Три BI-витрины с CTE, агрегатами и оконными функциями](sql/ddl/002_create_bi_marts.sql).
- [Шесть запросов, создание визуализаций и дашборда](deploy/redash/bootstrap/provision.py).
- [SQL-проверки расчётов на контрольной выборке](tests/bi_marts_assertions.sql).
- [Воспроизводимая конфигурация Docker Compose](deploy/redash/compose.yaml).

Далее приведены данные и инструкция самостоятельного запуска. Публичный сервер не развёрнут; адрес localhost открывается только после локального запуска. Видео демонстрации пока не записано.

## Dataset

49,520 international men's matches, from 1872-11-30 through 2026-07-19; 337 teams and 201 tournaments.
Original source: [martj42/international_results](https://github.com/martj42/international_results).
The prepared snapshot is `data/interim/matches_standardized.csv`.

## Run Redash on Windows

Start Docker Desktop (Linux containers), then run in PowerShell:

```powershell
& .\deploy\redash\start-redash.cmd
```

On a new installation, complete the administrator form at http://localhost:5000/setup and run the script again.
On subsequent runs, the existing account, queries and database volumes are reused.
The script downloads pinned Redash 26.9.0, PostgreSQL 17 and Redis 7 images, loads the snapshot,
creates the SQL views and read-only data source, executes six SQL queries, and creates the dashboard.
The web service is available only at http://localhost:5000.

The local configuration is generated in `deploy/redash/.env`. Keep it out of Git.
Redash metadata and the analytics dataset use separate PostgreSQL services and persistent Docker volumes.
The analytics service is named `analytics`; Redash connects to it with `redash_reader`, who has SELECT permissions.

## Dashboard

- Dataset overview and date coverage.
- Match counts and goals per year.
- Top teams by wins, with a minimum of 100 matches.
- Tournament volumes.
- Home, draw and away win shares on neutral versus non-neutral fields.

These metrics describe historical associations; they do not establish a causal effect of venue.
Friendlies dominate the sample, so aggregated rankings are not rankings of current team strength.

## Data model

- `matches`: validated match records and source metadata.
- `bi_match_facts`: one row per match, result and goals.
- `bi_team_year`: one row per team and year, wins/draws/losses, goals, win rate, DENSE_RANK.
- `bi_year_trends`: one row per year, match volume, goals, draw rate and cumulative matches.

Team statistics count one observation for each team participating in a match.
Home advantage excludes unknown venue status; neutral and non-neutral samples are shown separately.
The source CSV is loaded once when the analytics volume is created. Later changes to CSV files are not automatically imported.

## Python ETL and research

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .[dev]
wca-validate-data data/raw/results.csv
wca-profile-data data/raw/results.csv
wca-transform-data data/raw/results.csv --mapping config/column_mapping.toml --output data/interim/matches_standardized.csv
```

For an existing PostgreSQL installation, fill `.env` using `.env.example` and run:

```powershell
wca-load-postgres data/interim/matches_standardized.csv
psql -d world_cup_analytics -f sql/ddl/002_create_bi_marts.sql
```

Exploratory analysis remains in `notebooks/world_cup_analysis.ipynb`; SQL investigations are in `sql/analysis`.

## Validation

```powershell
python -m pytest -q
docker compose -f deploy/redash/compose.yaml config --quiet
```

The startup workflow checks the 49,520-row snapshot and executes every dashboard query through the Redash worker.
`tests/bi_marts_assertions.sql` checks view grain, win rates, tied ranks, unknown venue status and cumulative matches in a disposable PostgreSQL database.

## Troubleshooting and shutdown

```powershell
docker compose -f deploy/redash/compose.yaml ps
docker compose -f deploy/redash/compose.yaml logs --tail 80 server worker analytics
docker compose -f deploy/redash/compose.yaml stop
```

If Docker Hub downloads report a refused connection to a local proxy, check Docker Desktop's proxy settings and the VPN/proxy application.
Stopping containers preserves data. Do not remove volumes unless you intend to erase that deployment's stored data.
