# app/routers/network_router.py
from typing import List

from fastapi import APIRouter, HTTPException, Query

from app.schemas.network import Network
from app.services.logger import setup_logger
from app.services.wifi_service import scan_wifi_networks

# Configure logger
logger = setup_logger(__name__)

router = APIRouter()


@router.get("/scan-networks/", response_model=List[Network])
async def scan_networks(interface_index: int = Query(0, description="Index of the network interface to scan")):
    logger.debug("Received request to scan Wi-Fi networks.")
    try:
        return scan_wifi_networks(interface_index)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
