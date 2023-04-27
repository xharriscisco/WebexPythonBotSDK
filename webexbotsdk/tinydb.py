from tinydb import *
from dataclasses import dataclass, asdict

__all__ = ["BotDoc", "dataclass"]

@dataclass
class BotDoc():
  doc_id: int = None
  dict = asdict