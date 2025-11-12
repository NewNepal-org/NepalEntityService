"""Tests for translate CLI command.

Following TDD approach: Write failing tests first (Red phase).
These tests define the expected behavior of the translate CLI command.

The translate CLI should:
- Translate text from English to Nepali
- Translate text from Nepali (Devanagari) to English
- Translate text from Nepali (Romanized) to English
- Auto-detect source language when not specified
- Handle transliteration for Nepali names
- Support stdin input
"""

from unittest.mock import AsyncMock, patch

import pytest
from click.testing import CliRunner


class TestTranslateCLIBasicFunctionality:
    """Test basic translate CLI functionality."""

    def test_translate_command_exists(self):
        """Test that translate command is registered."""
        from nes.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["translate", "--help"])

        assert result.exit_code == 0
        assert "translate" in result.output.lower()

    def test_translate_english_to_nepali(self):
        """Test translating English text to Nepali."""
        from nes.cli import cli

        runner = CliRunner()

        # Mock the translation service
        with patch("nes.cli.translate.get_translation_service") as mock_service:
            mock_translator = AsyncMock()
            mock_translator.translate.return_value = {
                "translated_text": "राम चन्द्र पौडेल",
                "source_language": "en",
                "target_language": "ne",
            }
            mock_service.return_value = mock_translator

            result = runner.invoke(
                cli, ["translate", "--to", "ne", "Ram Chandra Poudel"]
            )

            assert result.exit_code == 0
            assert "राम चन्द्र पौडेल" in result.output

    def test_translate_nepali_to_english(self):
        """Test translating Nepali (Devanagari) text to English."""
        from nes.cli import cli

        runner = CliRunner()

        with patch("nes.cli.translate.get_translation_service") as mock_service:
            mock_translator = AsyncMock()
            mock_translator.translate.return_value = {
                "translated_text": "Ram Chandra Poudel",
                "source_language": "ne",
                "target_language": "en",
            }
            mock_service.return_value = mock_translator

            result = runner.invoke(cli, ["translate", "--to", "en", "राम चन्द्र पौडेल"])

            assert result.exit_code == 0
            assert "Ram Chandra Poudel" in result.output

    def test_translate_romanized_nepali_name_to_english(self):
        """Test translating Romanized Nepali name to English."""
        from nes.cli import cli

        runner = CliRunner()

        with patch("nes.cli.translate.get_translation_service") as mock_service:
            mock_translator = AsyncMock()
            mock_translator.translate.return_value = {
                "translated_text": "Ram Chandra Poudel",
                "source_language": "ne",
                "target_language": "en",
            }
            mock_service.return_value = mock_translator

            result = runner.invoke(
                cli, ["translate", "--to", "en", "Ram Chandra Paudel"]
            )

            assert result.exit_code == 0
            assert "Ram Chandra Poudel" in result.output

    def test_translate_romanized_nepali_sentence_to_english(self):
        """Test translating Romanized Nepali sentence to English."""
        from nes.cli import cli

        runner = CliRunner()

        with patch("nes.cli.translate.get_translation_service") as mock_service:
            mock_translator = AsyncMock()
            mock_translator.translate.return_value = {
                "translated_text": "I eat rice.",
                "source_language": "ne",
                "target_language": "en",
            }
            mock_service.return_value = mock_translator

            result = runner.invoke(cli, ["translate", "--to", "en", "Ma bhat khanchu."])

            assert result.exit_code == 0
            assert "I eat rice" in result.output

    def test_translate_romanized_nepali_to_devanagari(self):
        """Test translating Romanized Nepali to Devanagari."""
        from nes.cli import cli

        runner = CliRunner()

        with patch("nes.cli.translate.get_translation_service") as mock_service:
            mock_translator = AsyncMock()
            mock_translator.translate.return_value = {
                "translated_text": "म भात खान्छु।",
                "source_language": "ne",
                "target_language": "ne",
            }
            mock_service.return_value = mock_translator

            result = runner.invoke(cli, ["translate", "--to", "ne", "Ma bhat khanchu."])

            assert result.exit_code == 0
            assert "म भात खान्छु" in result.output

    def test_translate_mixed_romanized_input(self):
        """Test translating mixed English and Romanized Nepali text."""
        from nes.cli import cli

        runner = CliRunner()

        with patch("nes.cli.translate.get_translation_service") as mock_service:
            mock_translator = AsyncMock()
            mock_translator.translate.return_value = {
                "translated_text": "Ram Chandra Poudel is the President of Nepal.",
                "source_language": "ne",
                "target_language": "en",
            }
            mock_service.return_value = mock_translator

            # Mixed input: name in romanized Nepali + English words
            result = runner.invoke(
                cli,
                [
                    "translate",
                    "--to",
                    "en",
                    "Ram Chandra Paudel Nepal ko rashtrapati hun.",
                ],
            )

            assert result.exit_code == 0
            assert "Ram Chandra Poudel" in result.output
            assert "President" in result.output or "Nepal" in result.output


class TestTranslateCLIAutoDetection:
    """Test automatic language detection."""

    def test_auto_detect_nepali_devanagari(self):
        """Test auto-detection of Nepali Devanagari script."""
        from nes.cli import cli

        runner = CliRunner()

        with patch("nes.cli.translate.get_translation_service") as mock_service:
            mock_translator = AsyncMock()
            mock_translator.translate.return_value = {
                "translated_text": "Ram Chandra Poudel",
                "source_language": "ne",
                "target_language": "en",
                "detected_language": "ne",
            }
            mock_service.return_value = mock_translator

            # No --from specified, should auto-detect
            result = runner.invoke(cli, ["translate", "--to", "en", "राम चन्द्र पौडेल"])

            assert result.exit_code == 0
            assert "Detected" in result.output or "Nepali" in result.output

    def test_auto_detect_english(self):
        """Test auto-detection of English text."""
        from nes.cli import cli

        runner = CliRunner()

        with patch("nes.cli.translate.get_translation_service") as mock_service:
            mock_translator = AsyncMock()
            mock_translator.translate.return_value = {
                "translated_text": "राम चन्द्र पौडेल",
                "source_language": "en",
                "target_language": "ne",
                "detected_language": "en",
            }
            mock_service.return_value = mock_translator

            # No --from specified, should auto-detect
            result = runner.invoke(
                cli, ["translate", "--to", "ne", "Ram Chandra Poudel"]
            )

            assert result.exit_code == 0
            assert "राम चन्द्र पौडेल" in result.output


class TestTranslateCLIOptions:
    """Test CLI options and flags."""

    def test_explicit_source_language(self):
        """Test specifying source language explicitly."""
        from nes.cli import cli

        runner = CliRunner()

        with patch("nes.cli.translate.get_translation_service") as mock_service:
            mock_translator = AsyncMock()
            mock_translator.translate.return_value = {
                "translated_text": "राम चन्द्र पौडेल",
                "source_language": "en",
                "target_language": "ne",
            }
            mock_service.return_value = mock_translator

            result = runner.invoke(
                cli, ["translate", "--from", "en", "--to", "ne", "Ram Chandra Poudel"]
            )

            assert result.exit_code == 0
            assert "राम चन्द्र पौडेल" in result.output

    def test_specify_provider_aws_explicitly(self):
        """Test specifying AWS provider explicitly."""
        from nes.cli import cli

        runner = CliRunner()

        with patch("nes.cli.translate.get_translation_service") as mock_service:
            mock_translator = AsyncMock()
            mock_translator.translate.return_value = {
                "translated_text": "राम चन्द्र पौडेल",
                "source_language": "en",
                "target_language": "ne",
            }
            mock_service.return_value = mock_translator

            result = runner.invoke(
                cli,
                ["translate", "--provider", "aws", "--to", "ne", "Ram Chandra Poudel"],
            )

            assert result.exit_code == 0
            assert "राम चन्द्र पौडेल" in result.output
            # Verify the service was called with correct provider (None for defaults)
            mock_service.assert_called_once_with(
                provider_name="aws", model_id=None, region_name=None
            )

    def test_default_provider_is_aws(self):
        """Test that AWS is the default provider."""
        from nes.cli import cli

        runner = CliRunner()

        with patch("nes.cli.translate.get_translation_service") as mock_service:
            mock_translator = AsyncMock()
            mock_translator.translate.return_value = {
                "translated_text": "राम चन्द्र पौडेल",
                "source_language": "en",
                "target_language": "ne",
            }
            mock_service.return_value = mock_translator

            # Don't specify provider, should default to aws
            result = runner.invoke(
                cli, ["translate", "--to", "ne", "Ram Chandra Poudel"]
            )

            assert result.exit_code == 0
            # Verify the service was called with aws as default (None for defaults)
            mock_service.assert_called_once_with(
                provider_name="aws", model_id=None, region_name=None
            )

    def test_specify_model_id(self):
        """Test specifying a specific model ID."""
        from nes.cli import cli

        runner = CliRunner()

        with patch("nes.cli.translate.get_translation_service") as mock_service:
            mock_translator = AsyncMock()
            mock_translator.translate.return_value = {
                "translated_text": "राम चन्द्र पौडेल",
                "source_language": "en",
                "target_language": "ne",
            }
            mock_service.return_value = mock_translator

            result = runner.invoke(
                cli,
                [
                    "translate",
                    "--provider",
                    "aws",
                    "--model",
                    "global.anthropic.claude-sonnet-4-5-20250929-v1:0",
                    "--to",
                    "ne",
                    "Ram Chandra Poudel",
                ],
            )

            assert result.exit_code == 0
            assert "राम चन्द्र पौडेल" in result.output
            # Verify the service was called with correct model
            mock_service.assert_called_once_with(
                provider_name="aws",
                model_id="global.anthropic.claude-sonnet-4-5-20250929-v1:0",
                region_name=None,
            )

    def test_show_transliteration(self):
        """Test showing transliteration in output."""
        from nes.cli import cli

        runner = CliRunner()

        with patch("nes.cli.translate.get_translation_service") as mock_service:
            mock_translator = AsyncMock()
            mock_translator.translate.return_value = {
                "translated_text": "Ram Chandra Poudel",
                "source_language": "ne",
                "target_language": "en",
                "transliteration": "Ram Chandra Paudel",
            }
            mock_service.return_value = mock_translator

            result = runner.invoke(cli, ["translate", "--to", "en", "राम चन्द्र पौडेल"])

            assert result.exit_code == 0
            # Should show transliteration when available
            assert "Transliteration" in result.output
            assert "Ram Chandra Paudel" in result.output


class TestTranslateCLIErrorHandling:
    """Test error handling in translate CLI."""

    def test_missing_target_language(self):
        """Test error when target language is not specified."""
        from nes.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["translate", "some text"])

        # Should fail because --to is required
        assert result.exit_code != 0

    def test_invalid_target_language_code(self):
        """Test error handling for invalid target language codes."""
        from nes.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["translate", "--to", "invalid", "some text"])

        # Should show error for invalid language
        assert result.exit_code != 0

    def test_invalid_source_language_code(self):
        """Test error handling for invalid source language codes."""
        from nes.cli import cli

        runner = CliRunner()
        result = runner.invoke(
            cli, ["translate", "--from", "invalid", "--to", "en", "some text"]
        )

        # Should show error for invalid language
        assert result.exit_code != 0

    def test_empty_text_input(self):
        """Test handling of empty text input."""
        from nes.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["translate", "--to", "ne", ""])

        # Should handle empty input gracefully
        assert result.exit_code != 0

    def test_translation_service_error(self):
        """Test handling of translation service errors."""
        from nes.cli import cli

        runner = CliRunner()

        with patch("nes.cli.translate.get_translation_service") as mock_service:
            mock_translator = AsyncMock()
            mock_translator.translate.side_effect = Exception("Translation failed")
            mock_service.return_value = mock_translator

            result = runner.invoke(
                cli, ["translate", "--to", "ne", "Ram Chandra Poudel"]
            )

            assert result.exit_code != 0
            assert "error" in result.output.lower() or "failed" in result.output.lower()


class TestTranslateCLIStdinInput:
    """Test reading input from stdin."""

    def test_translate_from_stdin(self):
        """Test translating text piped from stdin."""
        from nes.cli import cli

        runner = CliRunner()

        with patch("nes.cli.translate.get_translation_service") as mock_service:
            mock_translator = AsyncMock()
            mock_translator.translate.return_value = {
                "translated_text": "राम चन्द्र पौडेल",
                "source_language": "en",
                "target_language": "ne",
            }
            mock_service.return_value = mock_translator

            # Simulate piped input
            result = runner.invoke(
                cli,
                ["translate", "--to", "ne"],
                input="Ram Chandra Poudel",
            )

            assert result.exit_code == 0
            assert "राम चन्द्र पौडेल" in result.output
