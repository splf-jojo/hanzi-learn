from pydantic import BaseModel


class PhotoOut(BaseModel):
    id: int
    slug: str
    filename: str
    content_type: str
    alt: str
    source: str
    url: str
