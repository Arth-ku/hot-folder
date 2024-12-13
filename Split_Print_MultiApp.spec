# Split_Print_v2.spec
# -*- mode: python ; coding: utf-8 -*-
block_cipher = None

a = Analysis(
    ['Split_Print_MultiApp.py'],
    pathex=['.'],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Split_Print_MultiApp.py',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Change to False to hide the console
    icon='C:\Split_print_multiapp/icon.ico',  # Specify path to your icon file if you have one
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Split_Print_MultiApp.py',
)
