from __future__ import annotations

import bpy
import rna_keymap_ui

from ..functions.keymap_scanner import (
    find_keymap_for_ref,
    format_hotkey_ref,
    get_user_keyconfig,
    scan_hotkey_conflicts,
    scan_multi_hotkey_bindings,
)


class KMTOOLS_AP_preferences(bpy.types.AddonPreferences):
    bl_idname = __package__.rsplit(".", 1)[0]

    def draw(self, context):
        layout = self.layout
        settings = context.window_manager.keymap_tools_settings

        layout.operator("keymap_tools.import_keymap_preset", icon="IMPORT")
        layout.operator("keymap_tools.remove_invalid_keymap_items", icon="TRASH")
        layout.operator("keymap_tools.scan_multi_hotkey_bindings", icon="VIEWZOOM")
        layout.operator("keymap_tools.scan_hotkey_conflicts", icon="ERROR")

        keyconfig = get_user_keyconfig()
        if settings.show_multi_hotkey_results:
            groups = scan_multi_hotkey_bindings(include_inactive=False)
            self.draw_result_header(
                layout,
                settings,
                "expand_multi_hotkey_results",
                f"Multi-Bound Action Groups: {len(groups)}",
                "MULTI_BOUND",
            )
            if settings.expand_multi_hotkey_results:
                for group in groups:
                    box = layout.box()
                    box.label(text=f"{group.label} - {group.key.keymap_name}")
                    self.draw_keymap_items(keyconfig, group.items, box)

        if settings.show_hotkey_conflict_results:
            groups = scan_hotkey_conflicts(include_inactive=True)
            self.draw_result_header(
                layout,
                settings,
                "expand_hotkey_conflict_results",
                f"Hotkey Conflict Groups: {len(groups)}",
                "CONFLICTS",
            )
            if settings.expand_hotkey_conflict_results:
                for group in groups:
                    box = layout.box()
                    box.label(text=f"{format_hotkey_ref(group.items[0])} - {group.key.keymap_name}")
                    self.draw_keymap_items(keyconfig, group.items, box)

    def draw_result_header(self, layout, settings, prop_name: str, text: str, result_type: str):
        icon = "TRIA_DOWN" if getattr(settings, prop_name) else "TRIA_RIGHT"
        row = layout.row(align=True)
        row.prop(settings, prop_name, text="", icon=icon, emboss=False)
        row.label(text=text)
        row.operator("keymap_tools.clear_results", text="", icon="X").result_type = result_type

    def draw_keymap_items(self, keyconfig, refs, layout):
        for ref in refs:
            keymap = find_keymap_for_ref(ref, keyconfig)
            item = keymap.keymap_items.from_id(ref.item_id)
            if item is None:
                continue
            rna_keymap_ui.draw_kmi(["USER"], keyconfig, keymap, item, layout, 0)
