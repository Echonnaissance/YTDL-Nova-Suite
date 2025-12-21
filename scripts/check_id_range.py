#!/usr/bin/env python3
"""Check HEAD range support for a specific download ID."""
import sys
import json
import urllib.request
import urllib.parse

ID = sys.argv[1] if len(sys.argv) > 1 else '51'
API = f'http://127.0.0.1:8000/api/downloads/{ID}'
BASE = 'http://127.0.0.1:8000'


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
        print('HEAD HTTPError:', e.code)
        for k, v in e.headers.items():
            print(f'{k}: {v}')


def main():
    print('Fetching', API)
    d = fetch_json(API)
    print(json.dumps(d, indent=2, ensure_ascii=False))
    media = d.get('media_url')
    if not media:
        print('No media_url for id', ID)
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
