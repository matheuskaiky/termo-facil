import pytest

def test_listar_termos_empty(client, valid_token):
    response = client.get("/api/v1/termos", headers=valid_token)
    assert response.status_code == 200
    assert response.json() == []

# To test get by ID, we would need to mock an entire depoimento lifecycle in the database.
# For basic coverage, let's test fetching a non-existent ID.
def test_get_termo_not_found(client, valid_token):
    import uuid
    fake_id = str(uuid.uuid4())
    response = client.get(f"/api/v1/termos/{fake_id}", headers=valid_token)
    assert response.status_code == 404
