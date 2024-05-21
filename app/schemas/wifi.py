from pydantic import BaseModel

class WiFiTest(BaseModel):
    interface_index: int = 1
    ssid: str
    password: str = None
    mobile_number: str
