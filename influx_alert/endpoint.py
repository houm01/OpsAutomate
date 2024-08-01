
from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from .client import BaseClient


class Endpoint:
    
    def __init__(self, parent: "BaseClient") -> None:
        self.parent = parent
    


    
    