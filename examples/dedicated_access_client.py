"""Website BACKEND example; no pricing, payment verification or auto-retries.

Store one operation UUID with the website's own order/entitlement before calling
grant/revoke. Token must never be sent to a browser. Python standard library only.
"""
import json
from urllib.error import HTTPError
from urllib.parse import quote, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from uuid import UUID


class PanelAPIError(RuntimeError):
    def __init__(self, status, code):
        self.status, self.code = status, code
        super().__init__(f"Panel API {status}: {code}")


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None  # Never forward an administrator bearer to a redirect host.


class DedicatedAccessClient:
    def __init__(self, panel_url, token, timeout=30, *, allow_loopback_http=False):
        parsed = urlsplit(panel_url)
        local_http = (allow_loopback_http and parsed.scheme == "http"
                      and parsed.hostname in {"127.0.0.1", "localhost", "::1"})
        if ((parsed.scheme != "https" and not local_http) or not parsed.hostname
                or parsed.username or parsed.password or parsed.query or parsed.fragment
                or parsed.path.rstrip("/") not in {"", "/api"}):
            raise ValueError("Use a fixed HTTPS panel origin (optionally ending in /api)")
        if not token or "\r" in token or "\n" in token:
            raise ValueError("A server-side administrator token is required")
        self.base = panel_url.rstrip("/")
        if not self.base.endswith("/api"):
            self.base += "/api"
        self.token, self.timeout = token, timeout
        self.opener = build_opener(_NoRedirect())

    def _request(self, method, path, body=None):
        request = Request(self.base + path, method=method,
            headers={"Authorization": "Bearer " + self.token, "Content-Type": "application/json"},
            data=json.dumps(body).encode() if body is not None else None)
        try:
            with self.opener.open(request, timeout=self.timeout) as response:
                return {"http_status": response.status, **json.load(response)}
        except HTTPError as exc:
            try:
                payload = json.load(exc)
                detail = payload.get("detail", {})
                code = detail.get("code", "REQUEST_REJECTED") if isinstance(detail, dict) else "REQUEST_REJECTED"
            except (ValueError, AttributeError):
                code = "INVALID_RESPONSE"
            finally:
                exc.close()
            raise PanelAPIError(exc.code, code) from None

    def catalog(self):
        return self._request("GET", "/dedicated-nodes")

    def user_access(self, username):
        return self._request("GET", f"/user/{quote(username, safe='')}/dedicated-nodes")

    def receipt(self, operation_id):
        return self._request("GET", "/dedicated-node-operations/" + str(UUID(operation_id)))

    def _change(self, method, username, node_id, operation_id, external_reference=None):
        if isinstance(node_id, bool) or not isinstance(node_id, int) or node_id < 1:
            raise ValueError("Use a positive catalog Node ID")
        body = {"operation_id": str(UUID(operation_id))}
        if external_reference is not None:
            body["external_reference"] = external_reference
        return self._request(method, f"/user/{quote(username, safe='')}/dedicated-nodes/{node_id}", body)

    def grant(self, username, node_id, operation_id, external_reference=None):
        return self._change("PUT", username, node_id, operation_id, external_reference)

    def revoke(self, username, node_id, operation_id, external_reference=None):
        return self._change("DELETE", username, node_id, operation_id, external_reference)
