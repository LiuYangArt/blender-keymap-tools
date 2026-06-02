# 2026-06-02 Keymap Import Cleanup Failures

## Symptoms
- Importing full Blender keymap export could freeze or raise errors on nested macro properties.
- Running Remove Exact Duplicates after importing stale add-on keymaps raised `AttributeError: 'NoneType' object has no attribute 'keys'`.

## Root Cause
- Exported keymaps can contain nested macro operator properties such as `TRANSFORM_OT_edge_slide`.
- Stale or disabled add-on operators can expose keymap items with `item.properties is None`.
- Duplicate signatures assumed all keymap items have regular operator properties.

## Fix
- Import nested macro properties recursively.
- Build duplicate signatures recursively for nested properties.
- Treat `item.properties is None` as an empty property set.
- Normalize exported float property signatures to Blender's 32-bit representation.

## Regression Verification
- `python scripts/validate_addon.py`
- Blender 5.1.2 background import of `bl_keymap_custom_full.py`
- Duplicate scan and remove after import
- Invalid keymap cleanup after import