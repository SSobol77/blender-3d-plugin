#!/usr/bin/env python3
"""Validate exported mobile asset manifests and blend files."""

import argparse
import json
import os
import sys


def validate_manifest(manifest_path, limits):
    if not os.path.exists(manifest_path):
        return [f"manifest missing: {manifest_path}"]

    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    issues = []
    tri = data.get("triangles", 0)
    tex = data.get("max_texture", 0)
    bones = data.get("bones", 0)
    materials = data.get("materials", 0)

    if limits.get("tri_limit") and tri > limits["tri_limit"]:
        issues.append(f"triangles {tri} > limit {limits['tri_limit']}")
    if limits.get("tex_max") and tex > limits["tex_max"]:
        issues.append(f"max_texture {tex} > limit {limits['tex_max']}")
    if limits.get("bone_limit") and bones > limits["bone_limit"]:
        issues.append(f"bones {bones} > limit {limits['bone_limit']}")
    if limits.get("material_limit") and materials > limits["material_limit"]:
        issues.append(f"materials {materials} > limit {limits['material_limit']}")

    return issues


def find_workflow_files(root="workflows"):
    files = []
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            if name.endswith(".json"):
                files.append(os.path.join(dirpath, name))
    return files


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="/home/astra/blender-3d-plugin")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    issues = []
    limit_map = {
        "godot_mobile.json": {"tri_limit": 120, "tex_max": 512, "material_limit": 4},
        "unity_mobile.json": {"tri_limit": 200, "tex_max": 512, "material_limit": 4},
        "ue5_mobile.json": {"tri_limit": 300, "tex_max": 1024, "material_limit": 6},
        "flutter_mobile.json": {"tri_limit": 80, "tex_max": 1024, "material_limit": 3},
        "kotlin_mobile.json": {"tri_limit": 120, "tex_max": 512, "material_limit": 4},
    }

    for path in find_workflow_files(os.path.join(args.root, "workflows")):
        name = os.path.basename(path)
        limits = limit_map.get(name, {"tri_limit": 300, "tex_max": 1024, "material_limit": 6})
        issues.extend(validate_manifest(path, limits))

    if issues:
        print(f"ISSUES: {len(issues)}")
        for i in issues:
            print(" - " + i)
        sys.exit(1)
    print("PASS: workflow manifest validation passed")
    sys.exit(0)


if __name__ == "__main__":
    main()
