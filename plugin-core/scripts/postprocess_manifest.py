# postprocess_manifest.py
# Generuje konfiguracje docelowe dla danego stacku

import json, os
from datetime import datetime

TEMPLATES = {
    "godot": """[resource]
type = "PackedScene"
load_steps = 1
format = 3
uid = "uid://placeholder"
path = "res://assets/3d/{asset_id}.glb"
""",
    "unity": """
%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
--- !u!4 &{asset_id}
GameObject:
  m_Name: {asset_id}
""",
    "flutter": """
class Asset3D_{asset_id_pascal} {{
  static const String path = "assets/3d/{asset_id}.glb";
}}
""",
    "kotlin": """
data class Asset3D_{asset_id_pascal}(
    val path: String = "assets/3d/{asset_id}.glb",
    val triCount: Int = {tri_count},
    val texMax: Int = {tex_max}
)
""",
}

def generate_stub(stack, asset_id, tri_count=120, tex_max=512, out_dir="/tmp"):
    asset_id_snake = asset_id.lower().replace(" ", "_").replace("-", "_")
    asset_id_pascal = "".join(x.title() for x in asset_id_snake.split("_"))

    if stack not in TEMPLATES:
        raise ValueError(f"Brak szablonu dla stacku: {stack}")

    content = TEMPLATES[stack].format(
        asset_id=asset_id_snake,
        asset_id_pascal=asset_id_pascal,
        tri_count=tri_count,
        tex_max=tex_max,
    )

    ext = {
        "godot": "trescn",
        "unity": "meta",
        "flutter": "dart",
        "kotlin": "kt",
    }.get(stack, "txt")

    out_path = os.path.join(out_dir, f"{asset_id_snake}_mobile.{ext}")
    with open(out_path, "w") as f:
        f.write(content)
    return out_path

if __name__ == "__main__":
    path = generate_stub("kotlin", "char_hero")
    print("Wygenerowano:", path)
