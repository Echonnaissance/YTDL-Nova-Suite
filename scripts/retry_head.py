#!/usr/bin/env python3
"""retry_head.py

Non-interactive retry helper: HEAD-check media URLs from the API.
Tries id 44 first, then falls back to other recent records.
"""
import urllib.request
import urllib.parse
import urllib.error
import json
import sys

BASE = 'http://127.0.0.1:8000'
API = BASE + '/api/downloads/?limit=20'


def fetch_json(url):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def head_request(url):
    req = urllib.request.Request(
        url, method='HEAD', headers={'Range': 'bytes=0-1'})
    try:
        with urllib.request.urlopen(req) as r:
            print('HEAD status:', r.status)
            for k, v in r.getheaders():
                print(f'{k}: {v}')
            return 0
    except urllib.error.HTTPError as e:
        code = getattr(e, 'code', None)
        reason = getattr(e, 'reason', None)
        print('HEAD HTTPError:', code if code is not None else reason)
        return 1
    except urllib.error.URLError as e:
        print('HEAD URLError:', getattr(e, 'reason', str(e)))
        return 2


def resolve_media_url(media):
    if not media:
        return None
    media = media.strip()
    if media.startswith('http://') or media.startswith('https://'):
        return media
    if media.startswith('/'):
        return BASE + urllib.parse.quote(media, safe='/')
    # fallback: treat as path under /media
    enc = urllib.parse.quote(media.replace('\\', '/'), safe='/')
    if not enc.startswith('/media'):
        enc = '/media/' + enc.lstrip('/')
    return BASE + enc


def main():
    try:
        data = fetch_json(API)
    except Exception as e:
        print('Failed to fetch API:', e)
        sys.exit(3)

    # prefer id 44
    preferred = 44
    ordered = [d for d in data if d.get('id') == preferred]
    ordered += [d for d in data if d.get('id') != preferred]

    for d in ordered:
        mid = d.get('id')
        media = d.get('media_url')
        print(f"Checking id={mid} media_url={media}")
        url = resolve_media_url(media)
        if not url:
            print('No media_url to check')
            continue
        print('Resolved URL:', url)
        rc = head_request(url)
        if rc == 0:
            print('Successful HEAD for id', mid)
            return 0
        else:
            print('HEAD failed for id', mid, 'moving to next')

    print('All checks failed')
    return 1


if __name__ == '__main__':
    sys.exit(main())
