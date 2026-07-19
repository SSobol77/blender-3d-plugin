# troubleshooting.md

| Problem | Fix |
|---------|-----|
| `BLEN 288: No active object` | Ustaw aktywnego obiektu przed operacja |
| `export failed: no UV layers` | Dodaj UV unwrap przed eksportem |
| `FBX: missing armature` | Sprawdz czy骨骼 sa w Object Mode |
| `GLTF: image too large` | Zmniejsz texture do 1024 lub 512 |
| `Tri count exceeded` | Zastosuj Decimate ratio ponizej 0.3 |
| `socket timeout` | Zwieksz timeout wew. blender-mcp |
| `animation looks broken` | Bake constraints przed exportem |
| `Android build failed` | Uzyj GLB + metryk z manifest |
