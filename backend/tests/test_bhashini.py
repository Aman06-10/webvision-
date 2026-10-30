"""Checks our request building and response parsing against the documented Bhashini shapes with a fake
server. This is NOT a live test: no Bhashini credentials were available."""
import asyncio

from app import config, voice

CONFIG_REPLY = {
    "pipelineInferenceAPIEndPoint": {"callbackUrl": "https://dhruva.example/compute",
                                     "inferenceApiKey": {"name": "Authorization", "value": "tok"}},
    "pipelineResponseConfig": [{"taskType": "asr", "config": [{"serviceId": "asr-svc"}]},
                               {"taskType": "translation", "config": [{"serviceId": "nmt-svc"}]}],
}
COMPUTE_REPLY = {"pipelineResponse": [
    {"taskType": "asr", "output": [{"source": "சாலை"}]},
    {"taskType": "translation", "output": [{"source": "சாலை", "target": "road"}]}]}


class FakeResp:
    def __init__(self, data):
        self.data = data
    def raise_for_status(self): pass
    def json(self): return self.data


def fake_client(calls):
    class C:
        def __init__(self, *a, **k): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *a): pass
        async def post(self, url, headers=None, json=None):
            calls.append((url, headers, json))
            return FakeResp(CONFIG_REPLY if "getModelsPipeline" in url else COMPUTE_REPLY)
    return C


def test_asr_plus_translation_flow(monkeypatch):
    calls = []
    monkeypatch.setattr(config, "BHASHINI_USER_ID", "u")
    monkeypatch.setattr(config, "BHASHINI_ULCA_API_KEY", "k")
    monkeypatch.setattr(voice.httpx, "AsyncClient", fake_client(calls))
    out = asyncio.run(voice.transcribe_and_translate(b"RIFFxxxx", "ta", "en"))
    assert out["translated"] == "road" and out["engine"].startswith("bhashini")
    cfg_url, cfg_headers, cfg_body = calls[0]
    assert cfg_headers == {"userID": "u", "ulcaApiKey": "k"}
    assert [t["taskType"] for t in cfg_body["pipelineTasks"]] == ["asr", "translation"]
    assert cfg_body["pipelineRequestConfig"]["pipelineId"] == config.BHASHINI_PIPELINE_ID
    comp_url, comp_headers, comp_body = calls[1]
    assert comp_url == "https://dhruva.example/compute" and comp_headers == {"Authorization": "tok"}
    assert comp_body["pipelineTasks"][0]["config"]["serviceId"] == "asr-svc"
    assert "audioContent" in comp_body["inputData"]["audio"][0]


def test_not_used_without_credentials(monkeypatch):
    monkeypatch.setattr(config, "BHASHINI_USER_ID", "")
    assert not voice.bhashini_configured()
