# app/schemas/network.py
from pydantic import BaseModel, Field


class Network(BaseModel):
    ssid: str = Field(None, description="SSID of the Wi-Fi network")
    bssid: str = Field(None, description="BSSID of the Wi-Fi network")
    signal: int = Field(None, description="Signal strength of the Wi-Fi network")
    frequency: int = Field(None, description="Frequency of the Wi-Fi network")
    security: str = Field(None, description="Security type of the Wi-Fi network")
    auth_algorithm: str = Field(None, description="Authentication algorithm of the Wi-Fi network")
    network_type: str = Field(None, description="Type of the Wi-Fi network")
