# -*- mode: python ; coding: utf-8 -*-


import os

# Helper function to collect all files in a directory recursively for datas
def collect_all_files(directory):
    data_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            full_path = os.path.join(root, file)
            relative_path = os.path.relpath(root, directory)
            target_path = os.path.join('vectorstore', relative_path)
            data_files.append((full_path, target_path))
    return data_files

datas = [
    ('users.txt', '.'),
    ('medicines.csv', '.'),
]

# Manually collect all files from vectorstore directory recursively
vectorstore_datas = collect_all_files('vectorstore')
datas.extend(vectorstore_datas)

a = Analysis(
    ['app_tkinter.py'],
    pathex=[os.path.abspath('.')],  # Add current working directory to pathex
    binaries=[],
    datas=datas,
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
    name='app_tkinter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
