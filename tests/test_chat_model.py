import os
import unittest

from api.routes import chat

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RETIRED = "llama-3.1-8b-instant"


class ChatModelTests(unittest.TestCase):
    def test_default_model_is_gpt_oss_20b(self):
        if "GROQ_MODEL" not in os.environ:
            self.assertEqual(chat.GROQ_MODEL, "openai/gpt-oss-20b")

    def test_default_literal_in_source(self):
        src = open(os.path.join(ROOT, "api", "routes", "chat.py"), encoding="utf-8").read()
        self.assertIn('os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b")', src)

    def test_retired_model_string_is_gone(self):
        for sub in ("api", os.path.join("frontend", "src")):
            for dirpath, dirs, files in os.walk(os.path.join(ROOT, sub)):
                dirs[:] = [d for d in dirs if d not in ("__pycache__", "node_modules")]
                for f in files:
                    if f.endswith((".pyc", ".png", ".jpg", ".svg", ".ico")):
                        continue
                    path = os.path.join(dirpath, f)
                    with open(path, encoding="utf-8", errors="ignore") as fh:
                        self.assertNotIn(RETIRED, fh.read(), path)


if __name__ == "__main__":
    unittest.main()
