#!/usr/bin/env python3
"""Mirror pinned browser assets and rewrite the upstream image at build time."""
import hashlib
import json
import pathlib
import re
import urllib.parse
import urllib.request

PUBLIC = pathlib.Path('/src/public')
manifest = json.loads(pathlib.Path('/tmp/mirotalk-vendor/manifest.json').read_text())
replacements = {}
for url, expected in manifest.items():
    if not expected:
        raise ValueError(f'missing digest: {url}')
    parsed = urllib.parse.urlsplit(url)
    local = '/vendor/' + parsed.netloc + parsed.path
    # Bare jsDelivr package URLs return JavaScript but Express needs an extension.
    if not pathlib.PurePosixPath(local).suffix or url.endswith('/sweetalert2@11.4.8'):
        local += '.js'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=60) as response:
        data = response.read()
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError(f'asset changed since manifest generation: {url}')
    target = PUBLIC / local.lstrip('/')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    replacements[url] = local

for path in PUBLIC.rglob('*'):
    if not path.is_file() or path.suffix not in ('.html', '.js', '.css') or '/vendor/' in str(path):
        continue
    text = path.read_text(encoding='utf-8', errors='strict')
    original = text
    text = text.replace('https://cdn.jsdelivr.net/npm/@mediapipe/selfie_segmentation/${file}', '/vendor/cdn.jsdelivr.net/npm/@mediapipe/selfie_segmentation@0.1.1675465747/${file}')
    for url, local in sorted(replacements.items(), key=lambda x: -len(x[0])):
        text = text.replace(url, local)
    # Use system fonts rather than sending browser requests to Google Fonts.
    text = re.sub(r'@import\s+url\(["\']?https://fonts\.googleapis\.com/[^)]*\)\s*;', '', text)
    text = re.sub(r'<link\b[^>]*href=["\']https://fonts\.googleapis\.com/[^>]*>', '', text, flags=re.I)
    text = text.replace('https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@${MEDIAPIPE_VERSION}', '/vendor/cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@${MEDIAPIPE_VERSION}')
    text = text.replace('https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task', '/vendor/storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task')
    text = re.sub(r'<script\b[^>]*src=["\']https://buttons\.github\.io/buttons\.js["\'][^>]*></script>', '', text, flags=re.I)
    if path.name == 'RoomClient.js':
        text = re.sub(r'genGravatar\(email, size = false\)\s*\{.*?\n    \}', 'genGravatar(email, size = false) {\n        return this.genAvatarSvg(email, size || 256);\n    }', text, count=1, flags=re.S)
    # Original SRI applies to unmodified CDN files; local files are hash-verified above.
    text = re.sub(r'\s+integrity=["\'][^"\']+["\']', '', text)
    if text != original:
        path.write_text(text, encoding='utf-8')
print('Mirrored', len(manifest), 'SHA-256 verified assets')
