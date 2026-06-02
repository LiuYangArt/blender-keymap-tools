from __future__ import annotations

import bpy
import rna_keymap_ui

from ..functions.keymap_scanner import find_keymap, get_user_keyconfig, scan_multi_hotkey_bindings


class KMTOOLS_AP_preferences(bpy.types.AddonPreferences):
    bl_idname = __package__.rsplit(".", 1)[0]

    def draw(self, context):
        layout = self.layout
        settings = context.window_manager.keymap_tools_settings

        layout.operator("keymap_tools.import_keymap_preset", icon="IMPORT")
        layout.operator("keymap_tools.remove_invalid_keymap_items", icon="TRASH")
        layout.operator("keymap_tools.scan_multi_hotkey_bindings", icon="VIEWZOOM")

        if not settings.show_multi_hotkey_results:
            return

        keyconfig = get_user_keyconfig()
        groups = scan_multi_hotkey_bindings(include_inactive=False)
        layout.label(text=f"Duplicate Hotkey Groups: {len(groups)}")

        if not groups:
            return

        for group in groups:
            keymap = find_keymap(group.key.keymap_name, keyconfig)
            box = layout.box()
            box.label(text=f"{group.label} - {group.key.keymap_name}")

            for ref in group.items:
                item = keymap.keymap_items.from_id(ref.item_id)
                if item is None:
                    continue
                row = box.split(factor=0.2)
                row.label(text=item.name)
                rna_keymap_ui.draw_kmi(["USER"], keyconfig, keymap, item, row, 0)