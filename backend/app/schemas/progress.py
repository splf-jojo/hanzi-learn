from pydantic import AliasChoices, BaseModel, Field


class KnowledgeLevelUpdate(BaseModel):
    knowledge_level: int = Field(
        ge=0,
        le=5,
        validation_alias=AliasChoices("knowledge_level", "knowledgeLevel"),
    )
