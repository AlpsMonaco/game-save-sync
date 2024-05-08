# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ["mainwindow.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

dll_set = (
    "libcrypto-1_1.dll",
    "libffi-7.dll",
    "libssl-1_1.dll",
    "MSVCP140_1.dll",
    "MSVCP140_2.dll",
    "qwindows.dll",
    "qmodernwindowsstyle.dll",
    "pyside6.abi3.dll",
    "Qt6Core.dll",
    "Qt6Gui.dll",
    "Qt6Widgets.dll",
    "python310.dll",
    "MSVCP140.dll",
    "shiboken6.abi3.dll",
    "VCRUNTIME140_1.dll",
    "VCRUNTIME140.dll",
)

binaries = []
for binary in a.binaries:
    binary_path = binary[0]
    if binary_path.lower().rfind('dll') != -1:
        if binary[0].find('PySide6') != -1:
            if  os.path.basename(binary[0]) not in dll_set:
                continue
    binaries.append(binary)
a.binaries = binaries

datas = []
for data in a.datas:
    if data[0].find('translations') != -1:
        continue
    datas.append(data)
a.datas = datas

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="game-save-sync",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
