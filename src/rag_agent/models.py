from dataclasses import dataclass
from pydantic import BaseModel

@dataclass
class Document:
    id : int
    title : str
    source : str

class DocumentModel(BaseModel):
    id : int
    title : str
    source : str


doc = Document(
    id=1,
    title="Mine Safety Guidelines",
    source="DGMS"
)

print(doc)
