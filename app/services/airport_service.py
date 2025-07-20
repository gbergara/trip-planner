import os
import json
import redis
import requests
import csv
from io import StringIO

OPENFLIGHTS_URL = 'https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat'
OPENFLIGHTS_REDIS_KEY = 'openflights:airports'

class AirportService:
    def __init__(self):
        self.redis = redis.Redis(host=os.environ.get('REDIS_HOST', 'redis'), port=6379, db=0, decode_responses=True)

    def _fetch_and_cache_openflights(self):
        resp = requests.get(OPENFLIGHTS_URL, timeout=10)
        resp.raise_for_status()
        csv_data = resp.text
        airports = []
        reader = csv.reader(StringIO(csv_data))
        for row in reader:
            # OpenFlights columns: ID,Name,City,Country,IATA,ICAO,Lat,Lon,Alt,Timezone,DST,Tz,Type,Source
            if len(row) < 5:
                continue
            airport = {
                'name': row[1],
                'city': row[2],
                'country': row[3],
                'iata': row[4],
                'icao': row[5] if len(row) > 5 else ''
            }
            if airport['iata'] and airport['iata'] != '\\N':
                airports.append(airport)
        self.redis.setex(OPENFLIGHTS_REDIS_KEY, 86400, json.dumps(airports))
        return airports

    def _get_airports(self):
        cached = self.redis.get(OPENFLIGHTS_REDIS_KEY)
        if cached:
            return json.loads(cached)
        return self._fetch_and_cache_openflights()

    def search_airports(self, query, limit=10):
        query = query.lower().strip()
        if not query:
            return []
        airports = self._get_airports()
        results = []
        for airport in airports:
            if (
                query in (airport.get('name') or '').lower() or
                query in (airport.get('city') or '').lower() or
                query in (airport.get('country') or '').lower() or
                query in (airport.get('iata') or '').lower() or
                query in (airport.get('icao') or '').lower()
            ):
                results.append(airport)
                if len(results) >= limit:
                    break
        return results
