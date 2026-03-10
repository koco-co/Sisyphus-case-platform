"""B-AICONF-07 — AiConfigService 单元测试"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

# ── Helpers ──────────────────────────────────────────────────────────


def _make_config(
    scope: str = "global",
    scope_id: uuid.UUID | None = None,
    llm_model: str | None = None,
    llm_temperature: float | None = None,
    team_standard_prompt: str | None = None,
    module_rules: dict | None = None,
    output_preference: dict | None = None,
):
    cfg = MagicMock()
    cfg.id = uuid.uuid4()
    cfg.scope = scope
    cfg.scope_id = scope_id
    cfg.llm_model = llm_model
    cfg.llm_temperature = llm_temperature
    cfg.team_standard_prompt = team_standard_prompt
    cfg.module_rules = module_rules
    cfg.output_preference = output_preference
    cfg.scope_preference = None
    cfg.rag_config = None
    cfg.custom_checklist = None
    cfg.system_rules_version = "v1"
    cfg.deleted_at = None
    return cfg


def _make_service(session: AsyncMock):
    from app.modules.ai_config.service import AiConfigService

    return AiConfigService(session)


# ── Tests ────────────────────────────────────────────────────────────


class TestInheritanceChain:
    """测试 AI 配置的继承链：iteration > product > global > default"""

    async def test_inheritance_chain_global_only(self):
        """只有 global 配置时应返回 global 配置。"""
        global_cfg = _make_config(
            scope="global",
            llm_model="glm-4-flash",
            llm_temperature=0.7,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = global_cfg

        session = AsyncMock()
        session.execute = AsyncMock(return_value=mock_result)

        svc = _make_service(session)
        result = await svc.get_by_scope("global")

        assert result == global_cfg
        assert result.llm_model == "glm-4-flash"

    async def test_inheritance_chain_product_scope(self):
        """product 级别配置应存在并独立查询。"""
        product_id = uuid.uuid4()
        product_cfg = _make_config(
            scope="product",
            scope_id=product_id,
            llm_model="qwen-max",
            llm_temperature=0.5,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = product_cfg

        session = AsyncMock()
        session.execute = AsyncMock(return_value=mock_result)

        svc = _make_service(session)
        result = await svc.get_by_scope("product", product_id)

        assert result.scope == "product"
        assert result.scope_id == product_id
        assert result.llm_model == "qwen-max"


class TestOverridePriority:
    """测试配置覆盖优先级。"""

    async def test_override_priority(self):
        """get_effective_config 应按 iteration > product > global 合并。"""
        global_cfg = _make_config(
            scope="global",
            llm_model="glm-4-flash",
            llm_temperature=0.7,
            team_standard_prompt="global prompt",
            module_rules={"diagnosis": "global rule"},
        )
        product_cfg = _make_config(
            scope="product",
            llm_model="qwen-max",
            llm_temperature=None,
            team_standard_prompt=None,
            module_rules={"generation": "product rule"},
        )
        iter_cfg = _make_config(
            scope="iteration",
            llm_model=None,
            llm_temperature=0.3,
            team_standard_prompt="iter prompt",
            module_rules=None,
        )

        # Mock get_by_scope to return different configs for different scopes
        scope_map = {
            "global": global_cfg,
            "product": product_cfg,
            "iteration": iter_cfg,
        }

        async def mock_get_by_scope(scope, scope_id=None):
            return scope_map.get(scope)

        session = AsyncMock()
        svc = _make_service(session)

        with patch.object(svc, "get_by_scope", side_effect=mock_get_by_scope):
            product_id = uuid.uuid4()
            iteration_id = uuid.uuid4()
            result = await svc.get_effective_config(product_id, iteration_id)

        # iteration 配置覆盖优先级最高
        assert result["llm_temperature"] == 0.3
        assert result["team_standard_prompt"] == "iter prompt"
        # product 配置次之
        assert result["llm_model"] == "qwen-max"

    async def test_override_no_iteration(self):
        """无 iteration 配置时应合并 global + product。"""
        global_cfg = _make_config(
            scope="global",
            llm_model="glm-4-flash",
            llm_temperature=0.7,
        )
        product_cfg = _make_config(
            scope="product",
            llm_model="qwen-max",
            llm_temperature=0.5,
        )

        scope_map = {
            "global": global_cfg,
            "product": product_cfg,
            "iteration": None,
        }

        async def mock_get_by_scope(scope, scope_id=None):
            return scope_map.get(scope)

        session = AsyncMock()
        svc = _make_service(session)

        with patch.object(svc, "get_by_scope", side_effect=mock_get_by_scope):
            result = await svc.get_effective_config(uuid.uuid4(), None)

        assert result["llm_model"] == "qwen-max"
        assert result["llm_temperature"] == 0.5
