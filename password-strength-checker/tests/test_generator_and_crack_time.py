import string
import unittest

from psc import analyze, crack_time, generator


class GeneratorTests(unittest.TestCase):
    def test_length_and_groups(self):
        for _ in range(50):
            pw = generator.generate_password(12)
            self.assertEqual(len(pw), 12)
            self.assertTrue(any(c in string.ascii_lowercase for c in pw))
            self.assertTrue(any(c in string.ascii_uppercase for c in pw))
            self.assertTrue(any(c in string.digits for c in pw))
            self.assertTrue(any(c in generator.SYMBOLS for c in pw))

    def test_options(self):
        pw = generator.generate_password(30, symbols=False, upper=False)
        self.assertTrue(all(c in string.ascii_lowercase + string.digits for c in pw))
        pw = generator.generate_password(200, avoid_ambiguous=True)
        self.assertFalse(set(pw) & generator.AMBIGUOUS)

    def test_invalid_arguments(self):
        with self.assertRaises(ValueError):
            generator.generate_password(2)
        with self.assertRaises(ValueError):
            generator.generate_password(10, lower=False, upper=False, digits=False, symbols=False)
        with self.assertRaises(ValueError):
            generator.generate_password(10_000)

    def test_passwords_are_unique(self):
        self.assertEqual(len({generator.generate_password(16) for _ in range(200)}), 200)

    def test_generated_passwords_score_well(self):
        self.assertTrue(all(analyze(generator.generate_password(18)).score >= 85 for _ in range(30)))

    def test_passphrase(self):
        phrase = generator.generate_passphrase(5, "-")
        self.assertEqual(len(phrase.split("-")), 5)
        self.assertTrue(all(w in generator.passphrase_words() for w in phrase.split("-")))
        self.assertEqual(len(generator.passphrase_words()), 2048)
        self.assertAlmostEqual(generator.passphrase_entropy_bits(6), 66.0)
        self.assertTrue(generator.generate_passphrase(4, "", capitalize=True)[0].isupper())
        with self.assertRaises(ValueError):
            generator.generate_passphrase(1)


class CrackTimeTests(unittest.TestCase):
    def test_humanize(self):
        h = crack_time.humanize
        self.assertEqual(h(0.2), "instantly")
        self.assertEqual(h(1), "1 second")
        self.assertEqual(h(90), "2 minutes")
        self.assertEqual(h(3600 * 5), "5 hours")
        self.assertEqual(h(86400 * 3), "3 days")
        self.assertIn("year", h(86400 * 365 * 40))
        self.assertIn("thousand years", h(86400 * 365 * 5000))
        self.assertIn("billion years", h(86400 * 365 * 3e9))
        self.assertEqual(h(1e40), "practically forever")

    def test_more_bits_take_longer(self):
        a = crack_time.seconds_to_crack(30, 1e4)
        b = crack_time.seconds_to_crack(60, 1e4)
        self.assertGreater(b, a)

    def test_huge_entropy_does_not_overflow(self):
        self.assertTrue(crack_time.estimate_all(1e9))

    def test_four_scenarios(self):
        self.assertEqual(len(crack_time.estimate_all(40)), 4)


if __name__ == "__main__":
    unittest.main()
