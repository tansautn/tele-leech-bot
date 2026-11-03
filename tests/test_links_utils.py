"""Tests for bot.helper.ext_utils.links_utils — pure regex functions."""

import pytest

from bot.helper.ext_utils.links_utils import (
    is_magnet,
    is_url,
    is_gdrive_link,
    is_telegram_link,
    is_share_link,
    is_rclone_path,
    is_gdrive_id,
)


class TestIsMagnet:
    def test_valid_btih(self):
        assert is_magnet(
            "magnet:?xt=urn:btih:c12fe1c06bba254a9dc9f519b335aa7c1367a88a&dn=test"
        )

    def test_valid_btmh(self):
        assert is_magnet(
            "magnet:?xt=urn:btmh:1220caf1e1c30e81cb361b9ee167c4aa64228a7fa4fa9f6105232b28ad099f3a302e"
        )

    def test_invalid_no_xt(self):
        assert not is_magnet("magnet:?dn=test")

    def test_invalid_http(self):
        assert not is_magnet("https://example.com")

    def test_empty(self):
        assert not is_magnet("")


class TestIsUrl:
    def test_https(self):
        assert is_url("https://example.com/path")

    def test_http(self):
        assert is_url("http://example.com")

    def test_ftp(self):
        assert is_url("ftp://files.example.com/file.zip")

    def test_bare_domain(self):
        assert is_url("example.com")

    def test_with_port(self):
        assert is_url("https://example.com:8080/path")

    def test_empty(self):
        assert not is_url("")

    def test_magnet_is_not_url(self):
        assert not is_url("magnet:?xt=urn:btih:abc123")


class TestIsGdriveLink:
    def test_drive_google(self):
        assert is_gdrive_link("https://drive.google.com/file/d/abc123/view")

    def test_drive_usercontent(self):
        assert is_gdrive_link(
            "https://drive.usercontent.google.com/download?id=abc"
        )

    def test_docs_google(self):
        assert is_gdrive_link("https://docs.google.com/spreadsheets/d/abc")

    def test_not_gdrive(self):
        assert not is_gdrive_link("https://example.com/file")


class TestIsTelegramLink:
    def test_t_me(self):
        assert is_telegram_link("https://t.me/channel/123")

    def test_tg_protocol(self):
        assert is_telegram_link("tg://openmessage?user_id=123")

    def test_not_telegram(self):
        assert not is_telegram_link("https://example.com")


class TestIsRclonePath:
    def test_valid_remote(self):
        assert is_rclone_path("gdrive:path/to/folder")

    def test_rcl_shortcut(self):
        assert is_rclone_path("rcl")

    def test_mrcc_prefix(self):
        assert is_rclone_path("mrcc:remote:path")

    def test_magnet_not_rclone(self):
        assert not is_rclone_path("magnet:?xt=urn:btih:abc")

    def test_mtp_not_rclone(self):
        assert not is_rclone_path("mtp:path")


class TestIsGdriveId:
    def test_valid_33char(self):
        assert is_gdrive_id("1BxNKmMoc0YwfTzFGqKxJFpG6eMi1Rgt0")

    def test_valid_19char(self):
        assert is_gdrive_id("0B1234567890abcdefg")

    def test_gdl_shortcut(self):
        assert is_gdrive_id("gdl")

    def test_root(self):
        assert is_gdrive_id("root")

    def test_sa_prefix(self):
        assert is_gdrive_id("sa:1BxNKmMoc0YwfTzFGqKxJFpG6eMi1Rgt0")

    def test_invalid(self):
        assert not is_gdrive_id("short")
