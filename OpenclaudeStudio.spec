# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

project_root = Path.cwd()

a = Analysis(
    ['main.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        ('README.md', '.'),
        ('assets\\openclaude_studio.svg', 'assets'),
        ('assets\\github-hero.svg', 'assets'),
        ('languages\\pt_br.xml', 'languages'),
        ('languages\\en.US.xml', 'languages'),
        ('languages\\Russian.xml', 'languages'),
    ],
    hiddenimports=[
        'qtawesome',
        'markdown_it',
    ],
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
    name='OpenclaudeStudio',
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
    icon='assets\\openclaude_studio.ico',
    version='assets\\windows_version_info.txt',
)
