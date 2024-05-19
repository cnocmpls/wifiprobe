from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.routers.captive_router import router as captive_router
from app.routers.network_router import router as network_router
from app.routers.network_interface_router import router as network_interface_router

app = FastAPI()
app.include_router(captive_router)
app.include_router(network_router)
app.include_router(network_interface_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": f"An unexpected error occurred.{str(exc)}"}
    )
