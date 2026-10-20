# 可复现工程与 CI 实验项目

本项目是 `Day01_可复现工程与CI.md` 的配套最小案例。它使用一个 uv workspace 管理：

- 根项目 `employee-agent-service`：最小 FastAPI 服务；
- workspace 成员 `release-guard`：Agent 版本清单校验库；
- 一份共享 `uv.lock`：固定两个项目的完整依赖解析结果。

## 本地运行

```bash
uv sync --locked --all-groups
uv run python scripts/validate_version_manifest.py
uv run ruff check .
uv run ruff format --check .
uv run mypy src packages/release_guard/src
uv run pytest --cov
uv build --all-packages --out-dir dist
uv run uvicorn employee_agent_service.app:app --reload
```

访问：

- `http://127.0.0.1:8000/api/health`
- `http://127.0.0.1:8000/api/version`

## 更新 Agent 文件后的正确流程

修改 Prompt、知识库、索引清单或评测集后：

1. 人工审查文件内容和影响范围；
2. 更新对应组件的 `version`；
3. 执行 `uv run python scripts/update_manifest_hashes.py`；
4. 执行 `uv run python scripts/validate_version_manifest.py`；
5. 运行完整质量门禁后再提交。

摘要脚本只是生成证据，不能替代人工审核。版本清单不得保存 API Key、Token、密码、完整用户问题或隐私数据。

> 本目录在课程资料库中是一个嵌套项目。练习 GitHub Actions 时，应把本目录复制为独立 Git 仓库的根目录，使 `.github/workflows/ci.yml` 位于仓库根目录下；嵌套在课程资料库中时，GitHub 不会把它识别为该仓库的 Workflow。
