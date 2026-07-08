# tests/test_smoke.py
async def test_smoke(client):
    response = await client.get("/docs")
    assert response.status_code == 200
