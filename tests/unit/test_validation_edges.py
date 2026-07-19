from __future__ import annotations

import pytest

from blender_mobile_3d.core.validation import ValidationEngine


@pytest.mark.parametrize(
    "limits,metrics,expected_codes",
    [
        ({"material_limit": 10, "tri_limit": 120, "tex_max": 512, "bone_limit": 60}, {"triangle_count": 10, "texture_max": 128, "bone_count": 5}, []),
        ({"material_limit": 1, "tri_limit": 5}, {"triangle_count": 500, "texture_max": 2000, "bone_count": 1000}, ["TRIANGLE_OVERAGE", "TEXTURE_SIZE_OVERAGE", "BONE_BUDGET_OVERAGE"]),
    ],
)
def test_parameterized_validation(limits, metrics, expected_codes):
    engine = ValidationEngine(limits)
    issues = engine.validate_metrics(metrics)
    codes = [i["code"] for i in issues]
    for expected in expected_codes:
        assert expected in codes, codes
