from pathlib import Path
import pytest
from starlette.testclient import TestClient
from main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_codebase_rag_endpoints_lifecycle(client: TestClient, tmp_path: Path):
    proj_dir = tmp_path / 'test_sample_service'
    src_dir = proj_dir / 'src'
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / 'service.py').write_text('class PaymentGateway:\n    """Payment processor service."""\n    async def process_payment(self, amount: float) -> bool:\n        """Execute charge."""\n        return True\n', encoding='utf-8')
    build_payload = {'project_root': str(proj_dir), 'index_name': 'payment_service_v1', 'include_dirs': ['src']}
    res_build = client.post('/api/rag/codebase/build', json=build_payload)
    assert res_build.status_code == 200
    data_build = res_build.json()
    assert data_build['status'] == 'success'
    assert data_build['result']['index_name'] == 'payment_service_v1'
    assert data_build['result']['total_chunks'] >= 1
    res_list = client.get('/api/rag/codebase/indexes')
    assert res_list.status_code == 200
    data_list = res_list.json()
    assert data_list['status'] == 'success'
    assert any((idx['name'] == 'payment_service_v1' for idx in data_list['indexes']))
    res_sym = client.post('/api/rag/codebase/symbols', json={'symbol': 'PaymentGateway', 'index_name': 'payment_service_v1'})
    assert res_sym.status_code == 200
    data_sym = res_sym.json()
    assert data_sym['success'] is True
    assert data_sym['count'] >= 1
    assert data_sym['results'][0]['symbol'] == 'PaymentGateway'
    res_search = client.post('/api/rag/codebase/search', json={'query': 'Execute charge', 'index_name': 'payment_service_v1', 'top_k': 3})
    assert res_search.status_code == 200
    data_search = res_search.json()
    assert data_search['success'] is True
    assert data_search['count'] >= 1
    res_del = client.delete('/api/rag/codebase/indexes/payment_service_v1')
    assert res_del.status_code == 200
    assert res_del.json()['success'] is True