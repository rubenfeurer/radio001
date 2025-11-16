from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict

class Station(BaseModel):
    """Base station model"""

    name: str
    url: str
    slot: Optional[int] = None

class RadioStation(Station):
    """Extended station model with additional fields"""

    id: Optional[int] = None
    country: Optional[str] = None
    location: Optional[str] = None

class SystemStatus(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    current_station: Optional[int] = None
    volume: int = 70
    is_playing: bool = False
