from typing import Dict

from fastapi import Request


def parse_device(request: Request, default_type: str = "web") -> Dict:
    headers = request.headers
    return {
        "userAgent": headers.get("user-agent"),
        "os": headers.get("x-device-os"),
        "osVersion": headers.get("x-device-os-version"),
        "deviceType": headers.get("x-device-type", default_type),
        "appVersion": headers.get("x-app-version"),
        "deviceModel": headers.get("x-device-model"),
        "locale": headers.get("accept-language"),
        "ip": request.client.host if request.client else None,
    }
