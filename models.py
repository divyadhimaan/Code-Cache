from pydantic import BaseModel, Field
from typing import Optional, List

class Question(BaseModel):
    question_id: int
    question_title: str
    topic: str
    difficulty: str
    revision: Optional[bool] = 0
    link: str
    notes: Optional[str] = None  # This will store the content of the .md file
    additional_tags: List[str]
    
    class Config:
        # Allows the model to be used with MongoDB, where the data might have an extra _id field
        arbitrary_types_allowed = True
