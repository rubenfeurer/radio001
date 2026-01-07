"""
WiFi Data Models

Pydantic models for WiFi API requests and responses.
"""

from typing import Optional

from pydantic import BaseModel, Field


class WiFiNetworkModel(BaseModel):
    """WiFi network model for API responses"""

    ssid: str
    signal: Optional[int] = None
    encryption: str = "Unknown"
    frequency: Optional[str] = None


class WiFiCredentials(BaseModel):
    """WiFi connection credentials"""

    ssid: str = Field(..., min_length=1, max_length=32, description="Network SSID")
    password: str = Field(
        default="",
        max_length=63,
        description="Network password (empty for open networks)",
    )


class WiFiStatusModel(BaseModel):
    """WiFi connection status model"""

    mode: str  # "client" or "host"
    connected: bool
    ssid: Optional[str] = None
    ip_address: Optional[str] = None
    signal_strength: Optional[int] = None
