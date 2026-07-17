from pydantic import AliasChoices, BaseModel, Field, field_validator


class KnowledgeLevelUpdate(BaseModel):
    knowledge_level: int = Field(
        ge=0,
        le=5,
        validation_alias=AliasChoices("knowledge_level", "knowledgeLevel"),
    )

    @field_validator("knowledge_level", mode="before")
    @classmethod
    def reject_bool(cls, value):
        # Исторический контракт: true/false — не уровень (lax-режим иначе даёт 1/0).
        if isinstance(value, bool):
            raise ValueError("knowledge_level must be an integer from 0 to 5")
        return value
