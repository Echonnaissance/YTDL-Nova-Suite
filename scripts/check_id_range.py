#!/usr/bin/env python3
"""check_id_range.py - interactive helper to inspect a single download id and HEAD its media URL

No CLI args required; you'll be prompted for an id (default 51).
"""
import urllib.parse
import urllib.request
import urllib.error
import json
import sys


def fetch_json(url):
    with urllib.request.urlopen(url) as r:
        return json.load(r)


def head_request(url):
    req = urllib.request.Request(
        url, method='HEAD', headers={'Range': 'bytes=0-1'})
    try:
        with urllib.request.urlopen(req) as r:
            print('HEAD status:', r.status)
            for k, v in r.getheaders():
                print(f'{k}: {v}')
    except urllib.error.HTTPError as e:
        code = getattr(e, 'code', None)
        print('HEAD HTTPError:', code)
        headers = getattr(e, 'headers', None)
        if headers:
            try:
                for k, v in headers.items():
                    print(f'{k}: {v}')
            except Exception:
                pass
    except urllib.error.URLError as e:
        print('HEAD URLError:', getattr(e, 'reason', str(e)))


def main():
    default_id = '51'
    id_in = input(f'Enter download id [{default_id}]: ').strip() or default_id
    API = f'http://127.0.0.1:8000/api/downloads/{id_in}'
    BASE = 'http://127.0.0.1:8000'
    print('Fetching', API)
    try:
        d = fetch_json(API)
    except Exception as e:
        print('Failed to fetch:', e)
        sys.exit(2)
    print(json.dumps(d, indent=2, ensure_ascii=False))
    media = d.get('media_url')
    if not media:
        print('No media_url for id', id_in)
        return
    if media.startswith('/'):
        enc = urllib.parse.quote(media, safe='/')
        url = BASE + enc
    else:
        enc = urllib.parse.quote(media.replace('\\', '/'), safe='/')
        if not enc.startswith('/media'):
            enc = '/media/' + enc.lstrip('/')
        url = BASE + enc
    print('Resolved URL:', url)
    print('\n---HEAD---')
    head_request(url)


if __name__ == '__main__':
    main()
