# Testing

`app.test_client()` sends requests to your app without starting a server. It keeps cookies between requests, so sessions work.

```python
from app import app

def test_home():
    client = app.test_client()
    resp = client.get("/")
    assert resp.status == 200
    assert "Welcome" in resp.text

def test_form():
    client = app.test_client()
    resp = client.post("/contact", data={"name": "Ann"})
    assert "Thanks Ann" in resp.text

def test_api():
    client = app.test_client()
    resp = client.post("/api/items", json_data={"name": "pen"})
    assert resp.status == 201
    assert resp.json["id"] == 42
```

| Client method | |
|---|---|
| `get(path, headers=None)` | GET request (`path` may contain `?query`) |
| `post(path, data=None, json_data=None, body=b"", headers=None)` | POST with form data, JSON or raw body |
| `put(...)`, `delete(...)` | other methods |
| `request(method, path, ...)` | any method |
| `client.cookies` | cookies stored by the client |

| Response attribute | |
|---|---|
| `status` | status code (`200`) |
| `text` / `data` | body as `str` / `bytes` |
| `json` | decoded JSON body |
| `headers`, `get_header(name)`, `content_type` | headers |

Run your tests with [pytest](https://pytest.org): `pip install pytest && pytest`.
