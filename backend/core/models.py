"""
Radio system data models.

This module defines the Pydantic models used throughout the radio system:
- RadioStation: Individual radio station with metadata
- SystemStatus: Current system state (volume, playback, etc.)
- VolumeUpdate: Volume change requests
- StationRequest: Station creation/update requests
- PlaybackStatus: Current playback information
"""

from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, validator, HttpUrl
from enum import Enum


class PlaybackState(str, Enum):
    """Current playback state"""
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"
    CONNECTING = "connecting"
    ERROR = "error"


class RadioStation(BaseModel):
    """Radio station model with all metadata"""

    name: str = Field(..., min_length=1, max_length=100, description="Station name")
    url: str = Field(..., description="Stream URL")
    slot: Optional[int] = Field(None, ge=1, le=3, description="Station slot (1-3)")
    country: Optional[str] = Field(None, max_length=50, description="Country of origin")
    location: Optional[str] = Field(None, max_length=100, description="City/location")
    genre: Optional[str] = Field(None, max_length=50, description="Music genre")
    bitrate: Optional[str] = Field(None, max_length=20, description="Stream bitrate")
    language: Optional[str] = Field(None, max_length=30, description="Broadcast language")

    @validator('url')
    def validate_url(cls, v):
        """Ensure URL is valid for streaming"""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v

    class Config:
        schema_extra = {
            "example": {
                "name": "Jazz FM",
                "url": "https://jazz-icy.streamguys1.com/live",
                "slot": 1,
                "country": "United Kingdom",
                "location": "London",
                "genre": "Jazz",
                "bitrate": "128k",
                "language": "English"
            }
        }


class SystemStatus(BaseModel):
    """Current system status"""

    current_station: Optional[int] = Field(None, ge=1, le=3, description="Currently playing station slot")
    volume: int = Field(50, ge=0, le=100, description="Current volume level (0-100)")
    is_playing: bool = Field(False, description="Whether audio is currently playing")
    playback_state: PlaybackState = Field(PlaybackState.STOPPED, description="Detailed playback state")
    current_station_info: Optional[RadioStation] = Field(None, description="Info about currently playing station")
    uptime: Optional[int] = Field(None, description="System uptime in seconds")

    class Config:
        schema_extra = {
            "example": {
                "current_station": 1,
                "volume": 75,
                "is_playing": True,
                "playback_state": "playing",
                "current_station_info": {
                    "name": "Jazz FM",
                    "url": "https://jazz-icy.streamguys1.com/live",
                    "slot": 1
                },
                "uptime": 3600
            }
        }


class VolumeUpdate(BaseModel):
    """Volume change request"""

    volume: int = Field(..., ge=0, le=100, description="New volume level (0-100)")

    class Config:
        schema_extra = {
            "example": {
                "volume": 75
            }
        }


class StationRequest(BaseModel):
    """Request to create or update a station"""

    name: str = Field(..., min_length=1, max_length=100, description="Station name")
    url: str = Field(..., description="Stream URL")
    country: Optional[str] = Field(None, max_length=50, description="Country of origin")
    location: Optional[str] = Field(None, max_length=100, description="City/location")
    genre: Optional[str] = Field(None, max_length=50, description="Music genre")
    bitrate: Optional[str] = Field(None, max_length=20, description="Stream bitrate")
    language: Optional[str] = Field(None, max_length=30, description="Broadcast language")

    @validator('url')
    def validate_url(cls, v):
        """Ensure URL is valid for streaming"""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


class PlaybackStatus(BaseModel):
    """Detailed playback status information"""

    state: PlaybackState = Field(PlaybackState.STOPPED, description="Current playback state")
    station_slot: Optional[int] = Field(None, ge=1, le=3, description="Playing station slot")
    station_name: Optional[str] = Field(None, description="Playing station name")
    volume: int = Field(50, ge=0, le=100, description="Current volume")
    duration: Optional[int] = Field(None, description="Stream duration if available")
    position: Optional[int] = Field(None, description="Current position if available")
    error_message: Optional[str] = Field(None, description="Error message if in error state")

    class Config:
        schema_extra = {
            "example": {
                "state": "playing",
                "station_slot": 2,
                "station_name": "Classical Radio",
                "volume": 65,
                "duration": None,
                "position": None,
                "error_message": None
            }
        }


class StationsResponse(BaseModel):
    """Response containing all configured stations"""

    stations: Dict[int, Optional[RadioStation]] = Field(
        ...,
        description="Dictionary mapping slot numbers (1-3) to station objects or None"
    )
    total_configured: int = Field(0, ge=0, le=3, description="Number of configured stations")

    class Config:
        schema_extra = {
            "example": {
                "stations": {
                    1: {
                        "name": "Jazz FM",
                        "url": "https://jazz-icy.streamguys1.com/live",
                        "slot": 1,
                        "country": "UK",
                        "genre": "Jazz"
                    },
                    2: None,
                    3: {
                        "name": "Classical Radio",
                        "url": "https://classical.stream.com/live",
                        "slot": 3,
                        "genre": "Classical"
                    }
                },
                "total_configured": 2
            }
        }


class ApiResponse(BaseModel):
    """Standard API response wrapper"""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Human-readable message")
    data: Optional[Any] = Field(None, description="Response data if applicable")

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Station saved successfully",
                "data": {
                    "slot": 1,
                    "name": "Jazz FM"
                }
            }
        }


class HardwareStatus(BaseModel):
    """Hardware component status (for debugging/monitoring)"""

    gpio_available: bool = Field(False, description="Whether GPIO hardware is available")
    audio_available: bool = Field(False, description="Whether audio system is available")
    mock_mode: bool = Field(True, description="Whether running in mock/development mode")
    button_states: Dict[int, bool] = Field(default_factory=dict, description="Current button states")
    last_volume_change: Optional[float] = Field(None, description="Timestamp of last volume change")

    class Config:
        schema_extra = {
            "example": {
                "gpio_available": True,
                "audio_available": True,
                "mock_mode": False,
                "button_states": {
                    17: False,
                    16: False,
                    26: False
                },
                "last_volume_change": 1703123456.789
            }
        }


# WebSocket message types
class WSMessage(BaseModel):
    """WebSocket message base structure"""

    type: str = Field(..., description="Message type identifier")
    data: Optional[Dict[str, Any]] = Field(None, description="Message data payload")
    timestamp: Optional[float] = Field(None, description="Message timestamp")

    class Config:
        schema_extra = {
            "example": {
                "type": "volume_update",
                "data": {
                    "volume": 75,
                    "station_slot": 1
                },
                "timestamp": 1703123456.789
            }
        }


class WSVolumeUpdate(WSMessage):
    """WebSocket volume update message"""
    type: Literal["volume_update"] = "volume_update"


class WSStationChange(WSMessage):
    """WebSocket station change message"""
    type: Literal["station_change"] = "station_change"


class WSPlaybackStatus(WSMessage):
    """WebSocket playback status message"""
    type: Literal["playback_status"] = "playback_status"


class WSSystemStatus(WSMessage):
    """WebSocket system status message"""
    type: Literal["system_status"] = "system_status"
