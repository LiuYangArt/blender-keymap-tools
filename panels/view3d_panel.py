from __future__ import annotations

import bpy


class KMTOOLS_PT_main_panel(bpy.types.Panel):
    bl_idname = "KMTOOLS_PT_main_panel"
    bl_label = "Keymap Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Keymap Tools"

    def draw(self, context):
        layout = self.layout
        settings = context.window_manager.keymap_tools_settings

        duplicate_box = layout.box()
        duplicate_box.label(text="Cleanup")
        duplicate_box.prop(settings, "include_inactive")
        duplicate_box.operator("keymap_tools.scan_exact_duplicates", icon="VIEWZOOM")
        duplicate_box.operator("keymap_tools.remove_exact_duplicates", icon="TRASH")

        conflict_box = layout.box()
        conflict_box.label(text="Hotkey Check")
        conflict_box.prop(settings, "keymap_name")
        conflict_box.prop(settings, "event_type")
        conflict_box.prop(settings, "event_value")

        row = conflict_box.row(align=True)
        row.prop(settings, "ctrl", toggle=True)
        row.prop(settings, "shift", toggle=True)
        row.prop(settings, "alt", toggle=True)
        row.prop(settings, "oskey", toggle=True)

        conflict_box.operator("keymap_tools.check_hotkey_conflict", icon="ERROR")
        conflict_box.operator("keymap_tools.list_available_keys", icon="KEYINGSET")