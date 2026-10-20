"""验证 Agent 版本清单中的必填字段、文件路径与 SHA-256。"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


class ManifestValidationError(ValueError):
    """版本清单不完整或与仓库文件不一致。"""


def _sha256(path: Path) -> str:
    """分块计算文件摘要，避免把大文件一次性读入内存。"""

    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(64 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _require_mapping(value: object, field_name: str) -> dict[str, Any]:
    """把运行时类型检查集中在一个函数中，错误信息更容易定位。"""

    if not isinstance(value, dict):
        raise ManifestValidationError(f"{field_name} 必须是 JSON 对象")
    return value


def validate_manifest(manifest_path: Path, project_root: Path) -> dict[str, Any]:
    """读取并验证清单；成功时返回已经解析的 JSON 对象。

    校验分为三层：
    1. 必须存在服务、运行时和 Agent 组件版本；
    2. 被清单引用的文件必须位于项目根目录内且真实存在；
    3. 文件的实际 SHA-256 必须与清单记录一致。
    """

    try:
        raw_data: object = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestValidationError(f"无法读取版本清单：{exc}") from exc

    manifest = _require_mapping(raw_data, "清单根节点")
    for required_key in ("schema_version", "service", "runtime", "agent"):
        if required_key not in manifest:
            raise ManifestValidationError(f"缺少必填字段：{required_key}")

    agent = _require_mapping(manifest["agent"], "agent")
    required_components = (
        "prompt",
        "chat_model",
        "skills",
        "tools",
        "harness",
        "embedding",
        "knowledge_base",
        "index",
        "evaluation",
    )
    missing = [name for name in required_components if name not in agent]
    if missing:
        raise ManifestValidationError("agent 缺少组件版本：" + ", ".join(missing))

    # 只校验带 path + sha256 的文件型组件；模型和 Tool 版本可只记录标识。
    for component_name, component_value in agent.items():
        if not isinstance(component_value, dict) or "path" not in component_value:
            continue

        relative_path = component_value.get("path")
        expected_sha256 = component_value.get("sha256")
        if not isinstance(relative_path, str) or not isinstance(expected_sha256, str):
            raise ManifestValidationError(
                f"{component_name} 的 path 和 sha256 必须是字符串"
            )

        candidate = (project_root / relative_path).resolve()
        root = project_root.resolve()
        if not candidate.is_relative_to(root):
            raise ManifestValidationError(
                f"{component_name} 的路径越过了项目根目录：{relative_path}"
            )
        if not candidate.is_file():
            raise ManifestValidationError(
                f"{component_name} 引用的文件不存在：{relative_path}"
            )

        actual_sha256 = _sha256(candidate)
        if actual_sha256 != expected_sha256:
            raise ManifestValidationError(
                f"{component_name} 摘要不一致：请审核变更后更新版本和 SHA-256"
            )

    return manifest
