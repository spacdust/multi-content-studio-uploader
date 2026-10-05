import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from src.server import app, fetch_available_models

class TestSettingsModels(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_fetch_empty_base_url(self):
        result = fetch_available_models("", "")
        self.assertEqual(result, [])

    @patch("openai.OpenAI")
    def test_fetch_models_via_openai_sdk(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_model_1 = MagicMock()
        mock_model_1.id = "gemini-2.5-flash"
        mock_model_2 = MagicMock()
        mock_model_2.id = "gpt-4o"
        mock_client.models.list.return_value = [mock_model_1, mock_model_2]
        mock_openai_cls.return_value = mock_client

        res = fetch_available_models("http://dummy-url/v1", "sk-test")
        self.assertIn("gemini-2.5-flash", res)
        self.assertIn("gpt-4o", res)

    @patch("openai.OpenAI", side_effect=Exception("SDK error"))
    @patch("requests.get")
    def test_fetch_models_fallback_http_gemini_format(self, mock_get, mock_openai_cls):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "models": [
                {"name": "models/gemini-2.5-flash"},
                {"name": "models/gemini-2.5-pro"}
            ]
        }
        mock_get.return_value = mock_resp

        res = fetch_available_models("http://dummy-gemini/v1beta", "key-test")
        self.assertEqual(res, ["gemini-2.5-flash", "gemini-2.5-pro"])

    @patch("openai.OpenAI", side_effect=Exception("SDK error"))
    @patch("requests.get")
    def test_fetch_models_fallback_http_standard_format(self, mock_get, mock_openai_cls):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "data": [
                {"id": "meta-llama/llama-3-70b-instruct"},
                {"id": "mistralai/mistral-large"}
            ]
        }
        mock_get.return_value = mock_resp

        res = fetch_available_models("http://dummy-proxy/v1", "key-test")
        self.assertEqual(res, ["meta-llama/llama-3-70b-instruct", "mistralai/mistral-large"])

    @patch("src.server.fetch_available_models")
    def test_api_get_models_endpoint(self, mock_fetch):
        mock_fetch.return_value = ["model-a", "model-b"]
        response = self.client.get("/api/settings/models?base_url=http://mock/v1&api_key=sk-123")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["count"], 2)
        self.assertEqual(data["models"], ["model-a", "model-b"])

    @patch("src.server.fetch_available_models")
    def test_api_post_models_endpoint(self, mock_fetch):
        mock_fetch.return_value = ["model-x", "model-y"]
        response = self.client.post("/api/settings/models", json={
            "llm_base_url": "http://mock/v1",
            "llm_api_key": "sk-test"
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["count"], 2)
        self.assertEqual(data["models"], ["model-x", "model-y"])

if __name__ == "__main__":
    unittest.main()
