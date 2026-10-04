#!/usr/bin/env python3
"""Официальные курсы Национального Банка Казахстана → rates.json для сайта OPERELLE Logistics.
Запуск: python3 tools/nbk_rates.py rates.json
Файл переписывается, только если курсы или дата изменились. Если сайт Нацбанка не ответил, файл остаётся прежним.
Курс в файле: сколько тенге за одну единицу валюты."""
import json, sys, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

OUT = sys.argv[1] if len(sys.argv) > 1 else 'rates.json'
URL = 'https://nationalbank.kz/rss/get_rates.cfm?fdate=%s'
today = (datetime.now(timezone.utc) + timedelta(hours=5)).strftime('%d.%m.%Y')   # дата по времени Астаны


def fetch(date):
    req = urllib.request.Request(URL % date, headers={'User-Agent': 'Mozilla/5.0 (OPERELLE Logistics rates)'})
    with urllib.request.urlopen(req, timeout=40) as r:
        root = ET.fromstring(r.read())
    rates = {}
    for it in root.iter('item'):
        code, val, q = (it.findtext('title') or '').strip(), it.findtext('description'), it.findtext('quant') or '1'
        try:
            v = float(val) / float(q)
        except (TypeError, ValueError, ZeroDivisionError):
            continue
        if code and v > 0:
            rates[code] = round(v, 6)
    return (root.findtext('date') or date).strip(), rates


try:
    date, rates = fetch(today)
    if len(rates) < 10:
        raise ValueError('мало валют в ответе: %d' % len(rates))
except Exception as e:  # сайт недоступен или ответ пустой: оставляем прежний файл
    print('Нацбанк не ответил:', e)
    sys.exit(0)

try:
    old = json.load(open(OUT, encoding='utf-8'))
except Exception:
    old = {}
if old.get('date') == date and old.get('rates') == rates:
    print('без изменений:', date, len(rates), 'валют')
    sys.exit(0)
data = {'source': 'Национальный Банк Казахстана', 'url': 'https://nationalbank.kz/ru/exchangerates/ezhednevnye-oficialnye-rynochnye-kursy-valyut',
        'date': date, 'fetched': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'base': 'KZT', 'rates': rates}
json.dump(data, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('обновлено:', date, len(rates), 'валют, USD', rates.get('USD'))
