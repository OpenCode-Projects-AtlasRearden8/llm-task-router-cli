import unittest

from llm_task_router.classifier import DEEP, QUICK, classify


class ClassifyQuickTests(unittest.TestCase):
    def test_short_typo_task_is_quick(self):
        result = classify("Fix the typo in my email subject line")
        self.assertEqual(result.category, QUICK)

    def test_translate_is_quick(self):
        result = classify("Translate this paragraph to German")
        self.assertEqual(result.category, QUICK)

    def test_summarize_bullets_is_quick(self):
        result = classify("Quick summarize the meeting in three bullets")
        self.assertEqual(result.category, QUICK)

    def test_name_ideas_is_quick(self):
        result = classify("Give me ten name ideas for a chess app")
        self.assertEqual(result.category, QUICK)

    def test_tie_defaults_to_quick(self):
        result = classify("Potato")
        self.assertEqual(result.category, QUICK)
        self.assertTrue(any("tie" in reason or "defaulted" in reason for reason in result.reasons))


class ClassifyDeepTests(unittest.TestCase):
    def test_analyze_is_deep(self):
        result = classify("Analyze why my eBay listings stopped converting")
        self.assertEqual(result.category, DEEP)

    def test_design_workflow_is_deep(self):
        result = classify("Design a comprehensive agent workflow for processing invoices")
        self.assertEqual(result.category, DEEP)

    def test_compare_and_contrast_is_deep(self):
        result = classify("Compare and contrast Kubernetes vs plain Docker for my home lab")
        self.assertEqual(result.category, DEEP)

    def test_word_think_through_is_deep(self):
        result = classify("Think through my migration strategy for the notes database")
        self.assertEqual(result.category, DEEP)


class ClassifyResultShapeTests(unittest.TestCase):
    def test_result_fields(self):
        result = classify("  Translate this list   ")
        self.assertEqual(result.task, "Translate this list")
        self.assertIn("category", dir(result))
        self.assertTrue(0.0 <= result.confidence <= 1.0)
        self.assertIsInstance(result.reasons, list)

    def test_confidence_grows_with_signal(self):
        weak = classify("Fix the typo")
        strong = classify("Analyze and compare and contrast my whole migration strategy")
        self.assertGreaterEqual(strong.confidence, weak.confidence)


if __name__ == "__main__":
    unittest.main()
