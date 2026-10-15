import importlib
import os
import pkgutil

os.environ.setdefault("ANTHROPIC_API_KEY", "test")
os.environ.setdefault("GOOGLE_API_KEY", "test")

import app


def _iter_app_modules():
    mods = ["app"]
    for info in pkgutil.walk_packages(app.__path__, "app."):
        mods.append(info.name)
    return sorted(mods)


def test_all_app_modules_importable():
    failed = []
    for name in _iter_app_modules():
        try:
            importlib.import_module(name)
        except Exception as e:  # noqa: BLE001
            failed.append(f"{name}: {e!r}")
    assert not failed, "modules failed to import:\n" + "\n".join(failed)
