# materials.md

## Mobile PBR Constraints

- Max 1024x1024 textures, prefer 512
- Base color in sRGB, roughness/metalness/normal in linear
- No alpha blending for opaque meshes
- Alpha test only for foliage / UI
- Single material per mesh preferred

## Shading

- Eevee Next / mobile optimized
- No volumetrics / SSS
- Simple baked indirect lighting allowed
- Limit texture samplers to 4
