from fastapi import APIRouter, HTTPException

from app.schemas.network_interface import AllNetworkInterfaces
from app.services.network_service import fetch_network_details, fetch_wifi_interfaces

router = APIRouter()


@router.get("/interfaces/", response_model=AllNetworkInterfaces)
async def list_interfaces():
    try:
        interfaces = fetch_network_details()
        return interfaces
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/interfaces/{interface_name}")
async def get_interface(interface_name: str):
    try:
        interfaces = fetch_network_details()
        return interfaces.interfaces.get(interface_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/wifi-interfaces/", response_model=AllNetworkInterfaces)
async def list_wifi_interfaces():
    try:
        interfaces = fetch_wifi_interfaces()
        return interfaces
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
