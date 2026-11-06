"""Daily entry point. Optional normalized evidence feed remains private."""
import json
import os
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from .providers import ROOT, favorite_watchlist, refresh
from .update import build


def main():
    refresh()
    inputs = None
    endpoint = os.environ.get('SPORTS_INPUT_URL')
    if endpoint:
        if urlsplit(endpoint).scheme != 'https': raise ValueError('HTTPS input feed required')
        headers = {'Accept': 'application/json'}
        if os.environ.get('SPORTS_INPUT_TOKEN'): headers['Authorization'] = 'Bearer ' + os.environ['SPORTS_INPUT_TOKEN']
        try:
            with urlopen(Request(endpoint, headers=headers), timeout=60) as response:
                raw = response.read(5_000_001)
                if len(raw) > 5_000_000: raise ValueError('Input feed too large')
                inputs = json.loads(raw)
        except Exception as error:
            # Retain history, publish unavailable state, never print authenticated URL.
            print('Normalized input refresh failed: ' + type(error).__name__)
    # Show fresh native market coverage even when no independent model is ready.
    # Never substitute these prices for the normalized evidence contract.
    inputs = inputs or {}
    cache = ROOT / 'data/sports/odds.json'
    try:
        inputs['market_watchlist'] = favorite_watchlist(json.loads(cache.read_text())) if cache.exists() else []
    except (ValueError, OSError):
        inputs['market_watchlist'] = []
    print(json.dumps(build(inputs), indent=2))


if __name__ == '__main__': main()
