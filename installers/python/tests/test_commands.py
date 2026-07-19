from __future__ import annotations

from blender_mobile_3d_installer.commands import main


def test_main_help_returns_zero():
    assert main(["help"]) == 0


def test_main_version_returns_zero():
    assert main(["version"]) == 0


def test_main_doctor_json_returns_zero():
    assert main(["doctor", "--json"]) == 0


def test_main_doctor_text_returns_zero():
    assert main(["doctor"]) == 0


def test_main_unknown_command_returns_two():
    assert main(["unknown"]) == 2


def test_main_no_args_returns_zero():
    assert main([]) == 0
