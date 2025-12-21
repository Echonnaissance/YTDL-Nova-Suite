#!/usr/bin/env python3
"""Test HTTP range requests for a download's media URL.

Prints the download JSON, the resolved media URL, HEAD headers, and GET status.
"""
import json
import urllib.request
import urllib.parse
import sys

API = 'http://127.0.0.1:8000/api/downloads/9'
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


def get_request(url):
    req = urllib.request.Request(url, headers={'Range': 'bytes=0-1'})
    try:
        with urllib.request.urlopen(req) as r:
            print('GET status:', r.status)
            data = r.read()
            print('GET bytes read:', len(data))
    except urllib.error.HTTPError as e:
        print('GET HTTPError:', e.code)


def main():
    print('Fetching', API)
    d = fetch_json(API)
    print('Download JSON:')
    print(json.dumps(d, indent=2, ensure_ascii=False))

    media = d.get('media_url') or d.get('file_path')
    if not media:
        print('No media/url found in record')
        sys.exit(1)

    # If media is a filesystem path, try to convert back to /media/ path if possible
    if media.startswith('/'):
        enc = urllib.parse.quote(media, safe='/')
        url = BASE + enc
    else:
        # assume already relative under /media
        enc = urllib.parse.quote(media.replace('\\', '/'), safe='/')
        if not enc.startswith('/media'):
            enc = '/media/' + enc.lstrip('/')
        url = BASE + enc

    print('Resolved media URL:', url)
    print('\n---HEAD---')
    head_request(url)
    print('\n---GET---')
    get_request(url)


if __name__ == '__main__':
    main()
