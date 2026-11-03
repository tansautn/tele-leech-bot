"""Tests for bot.core.config_manager.Config — type conversion and value processing."""

import pytest

from bot.core.config_manager import Config


class TestConvert:
    def test_bool_true_values(self):
        for val in ["true", "True", "1", "yes"]:
            assert Config._convert("AS_DOCUMENT", val) is True

    def test_bool_false_values(self):
        for val in ["false", "0", "no", ""]:
            assert Config._convert("AS_DOCUMENT", val) is False

    def test_int_from_string(self):
        assert Config._convert("OWNER_ID", "12345") == 12345

    def test_int_from_int(self):
        assert Config._convert("OWNER_ID", 99) == 99

    def test_str_passthrough(self):
        assert Config._convert("BOT_TOKEN", "abc:123") == "abc:123"

    def test_list_from_string(self):
        result = Config._convert("SEARCH_PLUGINS", '["a", "b"]')
        assert result == ["a", "b"]

    def test_list_empty_string(self):
        assert Config._convert("SEARCH_PLUGINS", "") == []

    def test_dict_from_string(self):
        result = Config._convert("FFMPEG_CMDS", '{"key": "val"}')
        assert result == {"key": "val"}

    def test_dict_empty_string(self):
        assert Config._convert("FFMPEG_CMDS", "") == {}

    def test_none_returns_none(self):
        assert Config._convert("BOT_TOKEN", None) is None

    def test_invalid_key_raises(self):
        with pytest.raises(KeyError):
            Config._convert("NONEXISTENT_KEY", "val")

    def test_invalid_list_string_raises(self):
        with pytest.raises(TypeError):
            Config._convert("SEARCH_PLUGINS", "not a list")

    def test_invalid_int_raises(self):
        with pytest.raises(TypeError):
            Config._convert("OWNER_ID", "not_a_number")


class TestSetGet:
    def setup_method(self):
        self._original = Config.CMD_SUFFIX

    def teardown_method(self):
        Config.CMD_SUFFIX = self._original

    def test_set_and_get(self):
        Config.set("CMD_SUFFIX", "test")
        assert Config.get("CMD_SUFFIX") == "test"

    def test_set_invalid_key_raises(self):
        with pytest.raises(KeyError):
            Config.set("INVALID_KEY_XYZ", "val")

    def test_get_missing_returns_none(self):
        assert Config.get("NONEXISTENT") is None


class TestProcessConfigValue:
    def test_default_upload_non_gd(self):
        assert Config._process_config_value("DEFAULT_UPLOAD", "tg") == "rc"

    def test_default_upload_gd(self):
        assert Config._process_config_value("DEFAULT_UPLOAD", "gd") == "gd"

    def test_base_url_strips_trailing_slash(self):
        result = Config._process_config_value("BASE_URL", "https://example.com/")
        assert result == "https://example.com"

    def test_empty_value_returns_none(self):
        assert Config._process_config_value("BOT_TOKEN", "") is None
