import json
import time
import unittest

from psc import analyze


class AnalyzerTests(unittest.TestCase):
    def test_empty_password(self):
        r = analyze("")
        self.assertEqual((r.score, r.label), (0, "Empty"))

    def test_common_passwords_are_very_weak(self):
        for pw in ("password", "123456", "qwerty", "letmein", "P@ssw0rd"):
            with self.subTest(pw=pw):
                r = analyze(pw)
                self.assertEqual(r.label, "Very Weak")
                self.assertFalse(r.checks["not_common"])

    def test_random_password_is_very_strong(self):
        r = analyze("xK9#mP2$vL5!qR8@")
        self.assertEqual(r.label, "Very Strong")
        self.assertGreaterEqual(r.score, 90)
        self.assertEqual(r.findings, [])

    def test_repeats_detected(self):
        r = analyze("aaaaaaaaaaaa")
        self.assertIn("repeat", [f["kind"] for f in r.findings])
        self.assertLess(r.effective_bits, 15)
        self.assertFalse(r.checks["no_patterns"])

    def test_repeated_block_detected(self):
        r = analyze("Qx7!Qx7!Qx7!")
        self.assertIn("repeat", [f["kind"] for f in r.findings])

    def test_sequences_detected(self):
        for pw in ("abcdefgh", "ZYXWVUTS", "pq#456789zz"):
            with self.subTest(pw=pw):
                self.assertIn("sequence", [f["kind"] for f in analyze(pw).findings])

    def test_keyboard_walk_detected(self):
        self.assertIn("keyboard", [f["kind"] for f in analyze("plokijuhyg").findings])

    def test_year_and_date_detected(self):
        self.assertIn("year", [f["kind"] for f in analyze("Vq#8Lm2024xZ").findings])
        self.assertIn("date", [f["kind"] for f in analyze("Vq#25/12/1999xZ").findings])

    def test_leetspeak_dictionary_word(self):
        r = analyze("Tr0ub4dor")  # not a word, should not be flagged
        self.assertTrue(r.checks["no_dictionary"])
        r = analyze("D1nn3rT1me")  # dinner + time with substitutions
        self.assertFalse(r.checks["no_dictionary"])

    def test_short_passwords_are_capped(self):
        r = analyze("xK9#mP2")
        self.assertEqual(r.label, "Weak")
        self.assertFalse(r.checks["length_8"])

    def test_longer_is_stronger(self):
        self.assertGreater(analyze("correct horse battery staple").effective_bits,
                           analyze("correct horse").effective_bits)

    def test_effective_never_exceeds_naive(self):
        for pw in ("hello", "Summer2024!", "xK9#mP2$vL5!qR8@", "a b c d"):
            r = analyze(pw)
            self.assertLessEqual(r.effective_bits, r.naive_bits + 1e-9)

    def test_breach_override(self):
        r = analyze("xK9#mP2$vL5!qR8@", breach_count=12345)
        self.assertEqual(r.label, "Compromised")
        self.assertLessEqual(r.score, 10)
        self.assertIn("12,345", r.suggestions[0])

    def test_score_is_in_range(self):
        for pw in ("", "a", "password", "xK9#mP2$vL5!qR8@" * 10):
            self.assertTrue(0 <= analyze(pw).score <= 100)

    def test_unicode_does_not_crash(self):
        r = analyze("пароль密码🔐İstanbul")
        self.assertIn("other/unicode", r.charsets)

    def test_very_long_input_is_fast(self):
        start = time.time()
        analyze("aB3$" * 1500)
        self.assertLess(time.time() - start, 5)

    def test_json_output_does_not_leak_password_fragments(self):
        r = analyze("Summer2024!")
        text = json.dumps(r.to_dict())
        self.assertNotIn("Summer", text)
        self.assertNotIn("2024", text)
        self.assertIn("Summer", json.dumps(r.to_dict(include_tokens=True)))


if __name__ == "__main__":
    unittest.main()
