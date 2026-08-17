import json


async def app(scope, receive, send):
    assert scope["type"] == "http"
    payload = json.dumps({
        "path": scope.get("path"),
        "raw_path": scope.get("raw_path").decode(errors="replace") if scope.get("raw_path") else None,
        "method": scope.get("method"),
        "query_string": scope.get("query_string", b"").decode(errors="replace"),
        "root_path": scope.get("root_path"),
        "headers": {k.decode(errors="replace"): v.decode(errors="replace") for k, v in scope.get("headers", [])},
    }).encode()
    await send({"type": "http.response.start", "status": 200, "headers": [[b"content-type", b"application/json"]]})
    await send({"type": "http.response.body", "body": payload})
