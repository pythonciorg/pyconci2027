from pydantic import BaseModel


class TranslationCreate(BaseModel):
    entity_type: str
    entity_id: int
    language: str
    field: str
    value: str


class TranslationUpdate(BaseModel):
    value: str


class Translation(TranslationCreate):
    id: int

    class Config:
        from_attributes = True