"""CI 入口：校验 Agent 版本清单并给出稳定退出码。"""

from pathlib import Path

from release_guard import ManifestValidationError, validate_manifest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = PROJECT_ROOT / "release" / "agent_versions.json"


def main() -> int:
    """返回 0 表示允许继续构建，返回 1 表示发布证据不可信。"""

    try:
        manifest = validate_manifest(MANIFEST_PATH, PROJECT_ROOT)
    except ManifestValidationError as exc:
        print(f"版本清单校验失败：{exc}")
        return 1

    service = manifest["service"]
    print(f"版本清单校验通过：{service['name']} {service['version']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
