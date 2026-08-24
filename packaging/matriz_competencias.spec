from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

spec_base = Path(SPECPATH).resolve()
root = spec_base.parent if spec_base.name.lower() == "packaging" else spec_base
backend = root / "backend"

hiddenimports = collect_submodules("uvicorn") + collect_submodules("alembic")

a = Analysis(
    [str(backend / "portable_entry.py")],
    pathex=[str(backend)],
    binaries=[],
    datas=[
        (str(root / "frontend" / "dist"), "frontend/dist"),
        (str(backend / "alembic"), "backend/alembic"),
        (str(backend / "alembic.ini"), "backend"),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "ruff"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="MatrizCompetencias",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name="MatrizCompetencias",
)
