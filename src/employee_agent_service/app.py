"""最小 FastAPI 服务：暴露健康状态与可审计的组件版本。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from release_guard import validate_manifest


def create_app(project_root: Path | None = None) -> FastAPI:
    """创建应用，并在启动前验证 Agent 版本清单。

    project_root 可由测试传入临时目录，避免测试依赖开发者的启动位置。
    正常运行时使用当前工作目录，因此应在项目根目录启动服务。
    """

    root = (project_root or Path.cwd()).resolve()
    manifest_path = root / "release" / "agent_versions.json"
    manifest = validate_manifest(manifest_path, root)

    app = FastAPI(title="Employee Agent Service", version="0.1.0")
    # 只把已经校验、且不含密钥的版本信息放进应用状态。
    app.state.version_manifest = manifest

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/version")
    def version(request: Request) -> dict[str, Any]:
        stored: dict[str, Any] = request.app.state.version_manifest
        agent: dict[str, Any] = stored["agent"]
        # 接口只返回排障需要的标识，不返回 Prompt 正文、密钥或业务数据。
        return {
            "schema_version": stored["schema_version"],
            "service": stored["service"],
            "runtime": stored["runtime"],
            "components": {
                name: value.get("version", value.get("model_id", "recorded"))
                if isinstance(value, dict)
                else value
                for name, value in agent.items()
            },
        }

    return app


app = create_app()
