# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['wav_to_ale_with_bext_xml_v2_plusUCS-Parsing.py'],
    pathex=[],
    binaries=[],
    datas=[('data/UCS_v8.2.1_Full_List.csv', 'data')],
    hiddenimports=['tkinter', 'tkinter.ttk', 'tkinter.filedialog', 'tkinter.messagebox', 'tkinter.font', 'tkinter.scrolledtext'],
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
    [],
    exclude_binaries=True,
    name='WAVsToALE',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icons/mac/WAVsToALE.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='WAVsToALE',
)
app = BUNDLE(
    coll,
    name='WAVsToALE.app',
    icon='icons/mac/WAVsToALE.icns',
    bundle_identifier='com.editcandy.wavstoale',
    info_plist={
        'CFBundleName': 'WAVsToALE',
        'CFBundleDisplayName': 'WAVsToALE',
        'CFBundleShortVersionString': '1.0.1',
        'CFBundleVersion': '1.0.1',
        'NSHighResolutionCapable': True,
    },
)
