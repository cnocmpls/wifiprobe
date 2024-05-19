from pydantic import BaseModel


class MobileNumber(BaseModel):
    mobile_number: str


class OTPVerification(BaseModel):
    otp: str
