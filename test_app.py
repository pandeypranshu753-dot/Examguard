import importlib.util

spec = importlib.util.spec_from_file_location("github_app", "app.py/app.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_index_has_github_link():
    client = module.app.test_client()
    response = client.get("/")
    assert response.status_code == 200
    assert b"Connect with GitHub" in response.data
