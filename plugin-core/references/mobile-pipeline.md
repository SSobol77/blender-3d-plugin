# mobile-pipeline.md

## Cel

Przygotowac assety 3D ready-to-use w grach mobilnych.
Plugin produkcyjny, nie eksperymentalny.
Wszystkie profile ograniczaja zuzycie zasobow dla urzadzen mobilnych.

## Kolejnosc

1. Przygotowanie sceny stagingowej
   - reset obiektow
   - ustaw jednostki w cm
   - ustaw renderer Eevee Next
2. Import mesh
3. Czystka geometrii
   - usun duplikaty
   - usun unused verts/edges/faces
4. Zastosuj profil mobile (low_poly / character / environment / ui_3d / fx)
5. LOD chain
6. PBR materials
7. Eksport
8. Manifest + validation

## Scorecard

| Check | Wartosc |
|-------|---------|
| triangle count <= profile limit | Yes | 
| texture size <= profile max | Yes |
| material count <= 4 | Yes |
| UV map exists | Yes |
| lod chain exists dla character/env | Yes |
| export file istnieje | Yes |
| manifest.json generated | Yes |
