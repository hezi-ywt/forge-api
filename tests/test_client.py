import base64
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from forge_api import ADetailerConfig, ForgeClient, ForgeConfig, IPAUnit


class FakeClient(ForgeClient):
    def __init__(self):
        super().__init__(url="127.0.0.1:7860", timeout=5)
        self.calls = []

    def _request(self, path, payload=None):
        self.calls.append((path, payload))
        if path.endswith("txt2img"):
            return {"images": [base64.b64encode(b"png").decode()], "info": '{"seed": 42}'}
        return {"progress": 0.0, "state": {}}


class ClientTests(unittest.TestCase):
    def test_config_normalizes_host(self):
        self.assertEqual(ForgeConfig("127.0.0.1:7860").normalized_url(), "http://127.0.0.1:7860")

    def test_txt2img_builds_typed_scripts(self):
        client = FakeClient()
        result = client.txt2img(
            prompt="test", controlnet=[IPAUnit(model="ipa", image="abc")],
            adetailer=ADetailerConfig.face_repair(prompt="face"),
            enable_hr=True, hr_additional_modules=[],
        )
        payload = client.calls[0][1]
        self.assertEqual(payload["hr_additional_modules"], [])
        self.assertIn("ControlNet", payload["alwayson_scripts"])
        self.assertIn("ADetailer", payload["alwayson_scripts"])
        self.assertEqual(result.seed, 42)

    def test_read_only_methods_use_expected_paths(self):
        client = FakeClient()
        client.progress(); client.options(); client.samplers(); client.loras(); client.checkpoints(); client.vaes()
        self.assertEqual([p for p, _ in client.calls], [
            "/sdapi/v1/progress", "/sdapi/v1/options", "/sdapi/v1/samplers",
            "/sdapi/v1/loras", "/sdapi/v1/sd-models", "/sdapi/v1/sd-vae",
        ])


if __name__ == "__main__":
    unittest.main()
