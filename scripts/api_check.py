#!/usr/bin/env python3
"""Fetch recent downloads from the API and test range support for the first media_url found."""
import json
import urllib.request
import urllib.parse
import urllib.error
import sys

API = 'http://127.0.0.1:8000/api/downloads?limit=20'
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
        code = getattr(e, 'code', None)
        reason = getattr(e, 'reason', None)
        print('HEAD HTTPError:', code if code is not None else reason)
        headers = getattr(e, 'headers', None)
        if headers:
            # headers may be a mapping or an email.message.Message; try common access patterns
            try:
                for k, v in headers.items():
                    print(f'{k}: {v}')
            except Exception:
                try:
                    for k in headers:
                        print(f'{k}: {headers[k]}')
                except Exception:
                    print('HEAD HTTPError: headers present but could not be iterated')
    except urllib.error.URLError as e:
        print('HEAD URLError:', getattr(e, 'reason', str(e)))


def main():
    print('Fetching', API)
    data = fetch_json(API)
    print(f'Got {len(data)} records')

    found = None
    for d in data:
        print('id=', d.get('id'), 'status=', d.get(
            'status'), 'media_url=', d.get('media_url'))
        if not found and d.get('media_url'):
            found = d

    if not found:
        print('No media_url found in recent records')
        sys.exit(0)

    media = found.get('media_url')
    print('\nTesting media for id', found.get('id'))
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
