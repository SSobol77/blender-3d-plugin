import pytest


@pytest.mark.parametrize("preset_name", ["low_poly", "environment", "character", "ui_3d", "fx"])
def test_available_presets(preset_name):
    from blender_mobile_3d.config.loader import available_presets

    assert preset_name in available_presets()
