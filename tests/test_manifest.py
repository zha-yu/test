import hashlib
import json
from pathlib import Path

import pytest
from release_guard import ManifestValidationError, validate_manifest

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def minimal_manifest(prompt: object) -> dict[str, object]:
    """构造只包含必填组件的测试清单，便于聚焦单个失败原因。"""

    return {
        "schema_version": "1.0",
        "service": {},
        "runtime": {},
        "agent": {
            "prompt": prompt,
            "chat_model": {},
            "skills": {},
            "tools": {},
            "harness": {},
            "embedding": {},
            "knowledge_base": {},
            "index": {},
            "evaluation": {},
        },
    }


def write_manifest(path: Path, content: object) -> None:
    path.write_text(json.dumps(content), encoding="utf-8")


def test_repository_manifest_is_valid() -> None:
    manifest = validate_manifest(
        PROJECT_ROOT / "release" / "agent_versions.json",
        PROJECT_ROOT,
    )

    assert manifest["agent"]["index"]["version"] == "index-1.0.0"


def test_changed_file_without_hash_update_is_rejected(tmp_path: Path) -> None:
    prompt_path = tmp_path / "prompt.md"
    prompt_path.write_text("安全版本", encoding="utf-8")
    manifest_path = tmp_path / "manifest.json"
    manifest = minimal_manifest(
        {
            "version": "prompt-1.0.0",
            "path": "prompt.md",
            "sha256": "0" * 64,
        }
    )
    write_manifest(manifest_path, manifest)

    with pytest.raises(ManifestValidationError, match="摘要不一致"):
        validate_manifest(manifest_path, tmp_path)


def test_path_cannot_escape_project_root(tmp_path: Path) -> None:
    outside_file = tmp_path.parent / "outside.txt"
    outside_file.write_text("不可读取", encoding="utf-8")
    manifest = minimal_manifest(
        {
            "version": "prompt-1.0.0",
            "path": "../outside.txt",
            "sha256": "0" * 64,
        }
    )
    manifest_path = tmp_path / "manifest.json"
    write_manifest(manifest_path, manifest)

    with pytest.raises(ManifestValidationError, match="越过了项目根目录"):
        validate_manifest(manifest_path, tmp_path)


@pytest.mark.parametrize("content", ["not-json", "["])
def test_invalid_json_is_rejected(tmp_path: Path, content: str) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(content, encoding="utf-8")

    with pytest.raises(ManifestValidationError, match="无法读取版本清单"):
        validate_manifest(manifest_path, tmp_path)


def test_missing_manifest_file_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ManifestValidationError, match="无法读取版本清单"):
        validate_manifest(tmp_path / "missing.json", tmp_path)


def test_manifest_root_must_be_object(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    write_manifest(manifest_path, [])

    with pytest.raises(ManifestValidationError, match="清单根节点 必须是 JSON 对象"):
        validate_manifest(manifest_path, tmp_path)


def test_required_top_level_field_cannot_be_missing(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    write_manifest(manifest_path, {"schema_version": "1.0"})

    with pytest.raises(ManifestValidationError, match="缺少必填字段：service"):
        validate_manifest(manifest_path, tmp_path)


def test_agent_must_be_object(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest = minimal_manifest({})
    manifest["agent"] = []
    write_manifest(manifest_path, manifest)

    with pytest.raises(ManifestValidationError, match="agent 必须是 JSON 对象"):
        validate_manifest(manifest_path, tmp_path)


def test_all_agent_components_are_required(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest = minimal_manifest({})
    del manifest["agent"]["evaluation"]  # type: ignore[index]
    write_manifest(manifest_path, manifest)

    with pytest.raises(ManifestValidationError, match="evaluation"):
        validate_manifest(manifest_path, tmp_path)


def test_path_and_hash_must_be_strings(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    write_manifest(
        manifest_path,
        minimal_manifest({"version": "prompt-1.0.0", "path": 123, "sha256": None}),
    )

    with pytest.raises(ManifestValidationError, match="必须是字符串"):
        validate_manifest(manifest_path, tmp_path)


def test_referenced_file_must_exist(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    write_manifest(
        manifest_path,
        minimal_manifest(
            {"version": "prompt-1.0.0", "path": "missing.md", "sha256": "0" * 64}
        ),
    )

    with pytest.raises(ManifestValidationError, match="文件不存在"):
        validate_manifest(manifest_path, tmp_path)


def test_matching_hash_is_accepted(tmp_path: Path) -> None:
    prompt_path = tmp_path / "prompt.md"
    content = "已审核的 Prompt"
    prompt_path.write_text(content, encoding="utf-8")
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    manifest_path = tmp_path / "manifest.json"
    write_manifest(
        manifest_path,
        minimal_manifest(
            {"version": "prompt-1.0.0", "path": "prompt.md", "sha256": digest}
        ),
    )

    manifest = validate_manifest(manifest_path, tmp_path)

    assert manifest["agent"]["prompt"]["version"] == "prompt-1.0.0"  # type: ignore[index]
