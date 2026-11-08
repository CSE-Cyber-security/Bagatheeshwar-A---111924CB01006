import contextlib
import io
import json
import os
import tempfile
import unittest
import urllib.error

from psc import breach
from psc.cli import main


class FakeResponse:
    def __init__(self, body):
        self._body = body.encode()

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class BreachTests(unittest.TestCase):
    def test_hash_split_matches_known_sha1(self):
        # SHA-1("password") = 5BAA61E4C9B93F3F0682250B6CF8331B7EE68FD8
        prefix, suffix = breach.sha1_prefix_suffix("password")
        self.assertEqual(prefix, "5BAA6")
        self.assertEqual(suffix, "1E4C9B93F3F0682250B6CF8331B7EE68FD8")

    def test_found_and_not_found(self):
        body = "0018A45C4D1DEF81644B54AB7F969B88D65:3\r\n1E4C9B93F3F0682250B6CF8331B7EE68FD8:9545824\r\n"
        self.assertEqual(breach.check_pwned("password", opener=lambda *a, **k: FakeResponse(body)),
                         9545824)
        self.assertEqual(breach.check_pwned("password", opener=lambda *a, **k: FakeResponse("AAAA:1")), 0)

    def test_only_prefix_is_sent(self):
        seen = []

        def opener(request, timeout=None):
            seen.append(request.full_url)
            return FakeResponse("")

        breach.check_pwned("password", opener=opener)
        self.assertEqual(seen, [breach.API_URL + "5BAA6"])

    def test_network_failure_returns_none(self):
        def boom(*a, **k):
            raise urllib.error.URLError("offline")

        self.assertIsNone(breach.check_pwned("password", opener=boom))


def run_cli(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(list(argv))
    return code, out.getvalue(), err.getvalue()


class CliTests(unittest.TestCase):
    def test_check_report(self):
        code, out, _ = run_cli("check", "password")
        self.assertEqual(code, 0)
        self.assertIn("Very Weak", out)

    def test_check_json_and_min_score(self):
        code, out, _ = run_cli("check", "password", "--json", "--min-score", "50")
        self.assertEqual(code, 1)
        data = json.loads(out)
        self.assertEqual(data["label"], "Very Weak")
        self.assertNotIn('"token"', out)  # password fragments are not included

    def test_generate_and_passphrase(self):
        code, out, _ = run_cli("generate", "-l", "20", "-n", "3")
        self.assertEqual((code, len(out.strip().splitlines())), (0, 3))
        self.assertEqual(run_cli("generate", "-l", "1")[0], 2)
        code, out, _ = run_cli("passphrase", "-w", "5")
        self.assertEqual(code, 0)
        self.assertIn("bits of true entropy", out)

    def test_batch_never_prints_passwords(self):
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt", encoding="utf-8") as fh:
            fh.write("hunter2secret\nxK9#mP2$vL5!qR8@\n\n")
            path = fh.name
        try:
            code, out, _ = run_cli("batch", path)
            self.assertEqual(code, 1)  # first one is below the default minimum score
            self.assertNotIn("hunter2secret", out)
            self.assertNotIn("xK9", out)
            self.assertIn("2 passwords checked", out)
            code, out, _ = run_cli("batch", path, "--json")
            self.assertEqual(len(json.loads(out)), 2)
        finally:
            os.unlink(path)

    def test_batch_missing_file(self):
        self.assertEqual(run_cli("batch", "/no/such/file.txt")[0], 2)


if __name__ == "__main__":
    unittest.main()
