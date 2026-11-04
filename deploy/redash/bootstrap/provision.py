"""Provision the local football dashboard using the existing local admin account."""
import os
import sys
import time
import requests
# The official image keeps Redash source in /app without installing it as a package.
# Running this mounted script otherwise puts only /bootstrap on Python's search path.
sys.path.insert(0, '/app')
from redash import create_app
from redash.models import User

app = create_app()
with app.app_context():
    admin = next((u for u in User.query.order_by(User.id).all() if u.has_permission('admin')), None)
    if admin is None:
        raise SystemExit('Complete the initial Redash admin setup at http://localhost:5000/setup first.')
    key = admin.api_key

session = requests.Session()
session.headers['Authorization'] = 'Key ' + key
base = 'http://server:5000/api/'

def api(method, path, payload=None):
    response = session.request(method, base + path, json=payload, timeout=60)
    if not response.ok:
        raise RuntimeError(f'{method} {path}: HTTP {response.status_code}: {response.text[:500]}')
    return response.json()

for attempt in range(60):
    try:
        sources = api('GET', 'data_sources')
        break
    except requests.RequestException:
        time.sleep(2)
else:
    raise SystemExit('Redash server did not become ready.')

source_name = 'World Cup PostgreSQL'
source = next((s for s in sources if s['name'] == source_name), None)
if source is None:
    source = api('POST', 'data_sources', {
        'name': source_name, 'type': 'pg', 'options': {
            'host': 'analytics', 'port': 5432, 'dbname': 'world_cup_analytics',
            'user': 'redash_reader', 'password': os.environ['ANALYTICS_READER_PASSWORD'],
            'sslmode': 'disable',
        },
    })

definitions = [
    ('Dataset overview', "SELECT COUNT(*) AS matches, COUNT(DISTINCT tournament) AS tournaments, MIN(date) AS first_match, MAX(date) AS last_match, ROUND(AVG(total_goals),2) AS avg_goals FROM bi_match_facts", None, None, None),
    ('Matches through time', 'SELECT year, matches, cumulative_matches FROM bi_year_trends ORDER BY year', 'year', 'matches', 'line'),
    ('Goals through time', 'SELECT year, avg_goals FROM bi_year_trends ORDER BY year', 'year', 'avg_goals', 'line'),
    ('Top teams by wins', 'SELECT team, SUM(matches) AS matches, SUM(wins) AS wins, ROUND(100.0*SUM(wins)/NULLIF(SUM(matches),0),2) AS win_rate_pct FROM bi_team_year GROUP BY team HAVING SUM(matches)>=100 ORDER BY wins DESC,team LIMIT 15', 'team', 'wins', 'column'),
    ('Tournament volumes', 'SELECT tournament, COUNT(*) AS matches FROM bi_match_facts GROUP BY tournament ORDER BY matches DESC,tournament LIMIT 10', 'tournament', 'matches', 'column'),
    ('Home advantage', "SELECT CASE WHEN neutral IS TRUE THEN 'Neutral' ELSE 'Non-neutral' END AS venue, COUNT(*) AS matches, ROUND(100.0*COUNT(*) FILTER (WHERE result='Home win')/COUNT(*),2) AS home_win_pct, ROUND(100.0*COUNT(*) FILTER (WHERE result='Draw')/COUNT(*),2) AS draw_pct, ROUND(100.0*COUNT(*) FILTER (WHERE result='Away win')/COUNT(*),2) AS away_win_pct FROM bi_match_facts WHERE neutral IS NOT NULL GROUP BY neutral ORDER BY neutral", None, None, None),
]

dashboard_name = 'World Cup 2026 Analytics'
dashboards = api('GET', 'dashboards?page_size=100')['results']
dashboard = next((d for d in dashboards if d['name'] == dashboard_name), None)
if dashboard is None:
    dashboard = api('POST', 'dashboards', {'name': dashboard_name})
dashboard = api('GET', f"dashboards/{dashboard['id']}")
widgets = dashboard.get('widgets', [])
layout = []
for index, (title, sql, x, y, kind) in enumerate(definitions):
    name = 'World Cup | ' + title
    candidates = api('GET', 'queries?page_size=100&q=' + requests.utils.quote(name))['results']
    query = next((q for q in candidates if q['name'] == name), None)
    if query is None:
        query = api('POST', 'queries', {'name': name, 'query': sql, 'data_source_id': source['id'], 'options': {'parameters': []}, 'description': 'Historical international men football results. Source: martj42/international_results. Home advantage is descriptive, not causal.'})
    query = api('POST', f"queries/{query['id']}", {'is_draft': False})
    result = api('POST', f"queries/{query['id']}/results", {'max_age': 0, 'parameters': {}})
    if 'job' in result:
        job = result['job']
        for _ in range(90):
            job = api('GET', 'jobs/' + str(job['id']))['job']
            if job['status'] == 3:
                break
            if job['status'] in (4, 5):
                raise RuntimeError(f"Query {title} failed: {job.get('error')}")
            time.sleep(1)
        else:
            raise RuntimeError(f'Query {title} timed out')
    query = api('GET', f"queries/{query['id']}")
    vis_name = 'Dashboard chart' if kind else 'Dashboard table'
    visualization = next((v for v in query.get('visualizations', []) if v['name'] == vis_name), None)
    if visualization is None:
        options = {} if not kind else {
            'globalSeriesType': kind, 'columnMapping': {x: 'x', y: 'y'},
            'sortX': False, 'legend': {'enabled': False},
            'xAxis': {'type': 'category' if kind == 'column' else 'linear'},
            'yAxis': [{'type': 'linear'}, {'type': 'linear'}],
            'seriesOptions': {},
        }
        visualization = api('POST', 'visualizations', {'query_id': query['id'], 'name': vis_name, 'type': 'CHART' if kind else 'TABLE', 'options': options, 'description': title})
    widget = next((w for w in widgets if (w.get('visualization') or {}).get('id') == visualization['id']), None)
    if widget is None:
        widget = api('POST', 'widgets', {'dashboard_id': dashboard['id'], 'visualization_id': visualization['id'], 'text': '', 'width': 1, 'options': {'position': {'col': (index % 2)*6, 'row': (index//2)*7, 'sizeX': 6, 'sizeY': 7}, 'parameterMappings': {}}})
    if index % 2 == 0:
        layout.append([])
    layout[-1].append(widget['id'])
    print('Verified query:', title, flush=True)

latest = api('GET', f"dashboards/{dashboard['id']}")
api('POST', f"dashboards/{dashboard['id']}", {'is_draft': False, 'layout': layout, 'version': latest['version']})
print('Dashboard ready: http://localhost:5000/dashboards/' + str(dashboard['id']), flush=True)
