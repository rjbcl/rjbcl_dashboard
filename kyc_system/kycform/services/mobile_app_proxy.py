import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen

from django.conf import settings


class MobileAppProxyError(Exception):
    def __init__(self, detail, status_code=502):
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


class MobileAppProxyService:
    @staticmethod
    def _build_url(path, params=None):
        base_url = (getattr(settings, "MOBILE_APP_API_BASE_URL", "") or "").strip()
        if not base_url:
            raise MobileAppProxyError(
                "MOBILE_APP_API_BASE_URL is not configured.",
                status_code=503,
            )

        url = urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
        query = urlencode({k: v for k, v in (params or {}).items() if v not in (None, "")})
        if query:
            url = f"{url}?{query}"
        return url

    @classmethod
    def fetch_json(cls, path, params=None):
        url = cls._build_url(path, params=params)
        request = Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "rjbcl-dashboard/1.0",
            },
        )

        try:
            with urlopen(request, timeout=getattr(settings, "MOBILE_APP_API_TIMEOUT", 15)) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                payload = response.read().decode(charset)
        except HTTPError as exc:
            detail = cls._extract_error_detail(exc)
            raise MobileAppProxyError(detail, status_code=exc.code) from exc
        except URLError as exc:
            raise MobileAppProxyError(
                f"Unable to reach mobile app service: {exc.reason}",
                status_code=502,
            ) from exc
        except TimeoutError as exc:
            raise MobileAppProxyError(
                "Mobile app service request timed out.",
                status_code=504,
            ) from exc

        try:
            return json.loads(payload)
        except json.JSONDecodeError as exc:
            raise MobileAppProxyError(
                "Mobile app service returned invalid JSON.",
                status_code=502,
            ) from exc

    @staticmethod
    def _extract_error_detail(exc):
        try:
            payload = exc.read().decode("utf-8")
            data = json.loads(payload)
            return data.get("detail") or data.get("message") or payload or "Mobile app service request failed."
        except Exception:
            return f"Mobile app service request failed with status {exc.code}."
