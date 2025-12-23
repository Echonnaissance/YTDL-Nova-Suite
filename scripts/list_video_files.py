#!/usr/bin/env python3
import os
p = os.path.join('Downloads', 'Video')
if not os.path.exists(p):
    print('no path', p)
    raise SystemExit(0)
for f in os.listdir(p):
    print(repr(f))
