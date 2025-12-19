# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for UMD (Universal Media Downloader) CLI tool

a = Analysis(
    ['YTMP3urlConverter.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config.example.json', '.'),  # Include config template
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='UMD',  # Executable name
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compress executable (smaller size)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # IMPORTANT: Show console for CLI tool
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

