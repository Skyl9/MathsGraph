from __future__ import annotations  # Activer les annotations différées (Python 3.7+)

from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel



class History(BaseModel):
    id:int
    concept_id:int
    modified_by:int
    modified_at:datetime
    field_modified:str
    old_value:Any
    new_value:Any
    version_number:int
    global_version:int
    is_rollback:bool
    note:Optional[str]