"""审核文件变更后，显式重算版本清单中的 SHA-256。"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = PROJECT_ROOT / "release" / "agent_versions.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(64 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    manifest: dict[str, Any] = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    for component in manifest["agent"].values():
        if not isinstance(component, dict) or "path" not in component:
            continue
        path = PROJECT_ROOT / component["path"]
        if not path.is_file():
            print(f"无法更新摘要，文件不存在：{path}")
            return 1
        component["sha256"] = sha256(path)

    # ensure_ascii=False 保留中文；末尾换行便于 Git diff 与文本工具处理。
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("已更新版本清单摘要；提交前仍需人工审核版本号和变更原因。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
