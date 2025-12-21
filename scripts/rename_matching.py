#!/usr/bin/env python3
import os
import sys
import argparse


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--dir', required=True)
    p.add_argument('--match', required=True)
    p.add_argument('--suffix', default=' (1)')
    args = p.parse_args()
    d = args.dir
    if not os.path.isdir(d):
        print('dir-not-found')
        sys.exit(2)
    files = [f for f in os.listdir(d) if args.match in f]
    if not files:
        print('notfound')
        sys.exit(1)
    f = files[0]
    base, ext = os.path.splitext(f)
    new = base + args.suffix + ext
    oldp = os.path.join(d, f)
    newp = os.path.join(d, new)
    try:
        os.rename(oldp, newp)
        print(f"renamed: {oldp} -> {new}")
        sys.exit(0)
    except Exception as e:
        print('error', e)
        sys.exit(3)


if __name__ == '__main__':
    main()
