import tempfile
import unittest

from gpt5_generate_catalog_retrieval_summaries import (
    build_user_prompt,
    config_for_domain,
    default_output_for_domain,
    prompt_signature,
    system_prompt_for_domain,
)


class RetrievalSummaryDomainTest(unittest.TestCase):
    def test_domain_selects_hf_config_and_prompt_name(self):
        self.assertEqual(
            config_for_domain("Office_Products"),
            "Office_Products_catalog",
        )
        self.assertIn(
            "future user interests in the Office Products domain",
            system_prompt_for_domain("Office_Products"),
        )
        self.assertIn(
            "future user interests in the Industrial and Scientific domain",
            system_prompt_for_domain("Industrial_and_Scientific"),
        )
        self.assertIn("printer or device family", system_prompt_for_domain("Office_Products"))
        self.assertIn(
            "thread or connector type",
            system_prompt_for_domain("Industrial_and_Scientific"),
        )
        self.assertNotIn(
            "FOR A GAME OR GAME CONTENT",
            system_prompt_for_domain("Office_Products"),
        )
        self.assertIn(
            "FOR A GAME OR GAME CONTENT",
            system_prompt_for_domain("Video_Games"),
        )

    def test_default_outputs_do_not_collide_between_domains(self):
        with tempfile.TemporaryDirectory() as output_dir:
            office = default_output_for_domain("Office_Products", output_dir)
            industrial = default_output_for_domain(
                "Industrial_and_Scientific",
                output_dir,
            )
        self.assertNotEqual(office, industrial)
        self.assertTrue(office.endswith("Office_Products_catalog_with_retrieval_summary.jsonl"))

    def test_prompt_signatures_include_domain(self):
        office = prompt_signature("Office_Products", "gpt-5.4", "low")
        industrial = prompt_signature(
            "Industrial_and_Scientific",
            "gpt-5.4",
            "low",
        )
        self.assertNotEqual(office, industrial)

    def test_unsupported_domain_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unsupported catalog domain"):
            config_for_domain("Books")

    def test_video_only_quality_override_does_not_clear_other_domains(self):
        row = {
            "item_id": 3460,
            "title": "Industrial Component",
            "brand": "Example",
            "description": "A supported industrial source description.",
            "detailed_description": "Detailed supported specifications.",
        }
        office_prompt, _, _ = build_user_prompt(row, {})
        video_prompt, _, _ = build_user_prompt(row)
        self.assertIn("A supported industrial source description.", office_prompt)
        self.assertIn("Original descriptions: (not provided)", video_prompt)


if __name__ == "__main__":
    unittest.main()