#!/usr/bin/env python3
"""
Simplified test suite for html_utils module focusing on the main HTML entity issue.
"""

import unittest
from html_utils import clean_html_content, clean_html_content_with_linebreaks


class TestHtmlUtilsSimple(unittest.TestCase):
    """Simplified test cases for HTML utility functions."""

    def test_main_issue_em_dash_decoding(self):
        """Test the main issue: em dash entity decoding."""
        # This is the exact case from the original issue
        input_text = "Art. 241 &#8211; B &#8211; Posse ou armazenamento de pornografia infantil"
        expected = "Art. 241 – B – Posse ou armazenamento de pornografia infantil"
        result = clean_html_content(input_text)
        self.assertEqual(result, expected)

    def test_em_dash_with_html_tags(self):
        """Test em dash decoding with HTML tags."""
        input_text = "<p>Art. 241 &#8211; B &#8211; Content</p>"
        expected = "Art. 241 – B – Content"
        result = clean_html_content(input_text)
        self.assertEqual(result, expected)

    def test_multiple_em_dashes(self):
        """Test multiple em dash entities."""
        input_text = "First &#8211; Second &#8211; Third &#8211; Fourth"
        expected = "First – Second – Third – Fourth"
        result = clean_html_content(input_text)
        self.assertEqual(result, expected)

    def test_em_dash_with_portuguese_text(self):
        """Test em dash with Portuguese accented characters."""
        input_text = "Educação &#8211; formação"
        expected = "Educação – formação"
        result = clean_html_content(input_text)
        self.assertEqual(result, expected)

    def test_ampersand_entity(self):
        """Test ampersand entity decoding."""
        input_text = "Tom &#38; Jerry"
        expected = "Tom & Jerry"
        result = clean_html_content(input_text)
        self.assertEqual(result, expected)

    def test_en_dash_entity(self):
        """Test en dash entity decoding."""
        input_text = "Text &#8212; with en dash"
        expected = "Text — with en dash"
        result = clean_html_content(input_text)
        self.assertEqual(result, expected)

    def test_basic_html_tag_removal(self):
        """Test basic HTML tag removal."""
        input_text = "<p>Simple paragraph</p>"
        expected = "Simple paragraph"
        result = clean_html_content(input_text)
        self.assertEqual(result, expected)

    def test_nested_html_tags_with_entities(self):
        """Test nested HTML tags with entities."""
        input_text = "<div><p>Content &#8211; with dash</p></div>"
        expected = "Content – with dash"
        result = clean_html_content(input_text)
        self.assertEqual(result, expected)

    def test_whitespace_normalization(self):
        """Test whitespace normalization."""
        input_text = "Text   with    spaces &#8211; more"
        expected = "Text with spaces – more"
        result = clean_html_content(input_text)
        self.assertEqual(result, expected)

    def test_linebreaks_function_basic(self):
        """Test basic functionality of clean_html_content_with_linebreaks."""
        input_text = "<p>First &#8211; paragraph</p><p>Second paragraph</p>"
        result = clean_html_content_with_linebreaks(input_text)
        
        # Should preserve line breaks and decode entities
        self.assertIn("–", result)  # Em dash should be decoded
        self.assertIn("\n", result)  # Should have line breaks
        self.assertIn("First", result)
        self.assertIn("Second", result)

    def test_linebreaks_with_br_tags(self):
        """Test <br> tag handling in clean_html_content_with_linebreaks."""
        input_text = "Line 1<br>Line 2 &#8211; content<br>Line 3"
        result = clean_html_content_with_linebreaks(input_text)
        
        lines = result.split('\n')
        self.assertTrue(len(lines) >= 3)  # Should have multiple lines
        self.assertIn("–", result)  # Em dash should be decoded

    def test_empty_string(self):
        """Test empty string handling."""
        result = clean_html_content("")
        self.assertEqual(result, "")

    def test_only_html_tags(self):
        """Test string with only HTML tags."""
        input_text = "<p></p><div></div>"
        result = clean_html_content(input_text)
        self.assertEqual(result, "")

    def test_special_characters_preservation(self):
        """Test that allowed special characters are preserved."""
        input_text = "Text with: periods. commas, exclamation! question? dash-hyphen &#8211; em-dash"
        result = clean_html_content(input_text)
        
        # These should be preserved
        self.assertIn(".", result)
        self.assertIn(",", result)
        self.assertIn("!", result)
        self.assertIn("?", result)
        self.assertIn("-", result)  # Regular hyphen
        self.assertIn("–", result)  # Em dash from entity

    def test_parentheses_and_slashes_preservation(self):
        """Test that parentheses and slashes are preserved - the new reported issue."""
        input_text = "A Lei Antifeminicídio (Lei n. 14.994/2024) e os efeitos da condenação no Direito Penal Militar"
        expected = "A Lei Antifeminicídio (Lei n. 14.994/2024) e os efeitos da condenação no Direito Penal Militar"
        result = clean_html_content(input_text)
        self.assertEqual(result, expected)
        
        # Test with HTML tags too
        input_with_tags = "<p>A Lei Antifeminicídio (Lei n. 14.994/2024) e os efeitos</p>"
        expected_with_tags = "A Lei Antifeminicídio (Lei n. 14.994/2024) e os efeitos"
        result_with_tags = clean_html_content(input_with_tags)
        self.assertEqual(result_with_tags, expected_with_tags)

    def test_various_punctuation_preservation(self):
        """Test that various punctuation marks are preserved."""
        input_text = "Test (parentheses) [brackets] {braces} /slash/ \\backslash\\ @symbol #hash %percent"
        result = clean_html_content(input_text)
        
        # All these should be preserved
        self.assertIn("(", result)
        self.assertIn(")", result)
        self.assertIn("[", result)
        self.assertIn("]", result)
        self.assertIn("{", result)
        self.assertIn("}", result)
        self.assertIn("/", result)
        self.assertIn("\\", result)
        self.assertIn("@", result)
        self.assertIn("#", result)
        self.assertIn("%", result)

    def test_real_world_wordpress_example(self):
        """Test with the exact real-world WordPress example from the issue."""
        wordpress_content = """
        <p>Este artigo trata sobre crimes digitais &#8211; especificamente:</p>
        <ul>
            <li>Posse de material &#8211; Art. 241-B</li>
            <li>Armazenamento &#38; distribuição</li>
        </ul>
        <p>Mais informações em: www.exemplo.com</p>
        """
        
        result = clean_html_content_with_linebreaks(wordpress_content)
        
        # Check that entities are properly decoded
        self.assertIn("–", result)  # Em dash
        self.assertIn("&", result)  # Ampersand
        
        # Check that structure is preserved
        self.assertIn("Este artigo", result)
        self.assertIn("Posse de material", result)
        self.assertIn("www.exemplo.com", result)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)