import uuid

from app.shared.base_schema import BaseResponse, BaseSchema


class AiConfigCreate(BaseSchema):
    scope: str = "global"
    scope_id: uuid.UUID | None = None
    team_standard_prompt: str | None = None
    module_rules: dict | None = None
    output_preference: dict | None = None
    scope_preference: dict | None = None
    rag_config: dict | None = None
    custom_checklist: dict | None = None
    llm_model: str | None = None
    llm_temperature: float | None = None


class AiConfigUpdate(BaseSchema):
    team_standard_prompt: str | None = None
    module_rules: dict | None = None
    output_preference: dict | None = None
    scope_preference: dict | None = None
    rag_config: dict | None = None
    custom_checklist: dict | None = None
    llm_model: str | None = None
    llm_temperature: float | None = None


class AiConfigResponse(BaseResponse):
    scope: str
    scope_id: uuid.UUID | None
    system_rules_version: str
    team_standard_prompt: str | None
    module_rules: dict | None
    output_preference: dict | None
    scope_preference: dict | None
    rag_config: dict | None
    custom_checklist: dict | None
    llm_model: str | None
    llm_temperature: float | None
