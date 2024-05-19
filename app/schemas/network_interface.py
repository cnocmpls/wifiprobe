# app/schemas/network_interface.py
from typing import List, Optional

from pydantic import BaseModel, Field, IPvAnyAddress


class IPDetail(BaseModel):
    address: IPvAnyAddress
    netmask: Optional[str] = None
    broadcast: Optional[str] = None


class NetworkInterfaceDetails(BaseModel):
    name: str = Field(default="Unknown")
    index: int = Field(default=0)
    mac_address: Optional[str] = Field(default="Unknown")
    ipv4: List[IPDetail] = Field(default_factory=list)
    ipv6: List[IPDetail] = Field(default_factory=list)
    is_up: bool = False
    speed: Optional[int] = None
    duplex: Optional[str] = None
    mtu: Optional[int] = None
    is_wifi: Optional[bool] = False
    status: Optional[str] = None


class AllNetworkInterfaces(BaseModel):
    interfaces: dict[str, NetworkInterfaceDetails]

    class Config:
        validate_assignment = True
