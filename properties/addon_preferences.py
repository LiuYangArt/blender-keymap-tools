from __future__ import annotations

import bpy


class KMTOOLS_AP_preferences(bpy.types.AddonPreferences):
    bl_idname = __package__.rsplit(".", 1)[0]

    def draw(self, context):
        layout = self.layout
        settings = context.window_manager.keymap_tools_settings

        layout.operator("keymap_tools.import_keymap_preset", icon="IMPORT")
        layout.operator("keymap_tools.remove_invalid_keymap_items", icon="TRASH")
        layout.operator("keymap_tools.scan_multi_hotkey_bindings", icon="VIEWZOOM")

        if not settings.multi_hotkey_report:
            return

        report_box = layout.box()
        for line in settings.multi_hotkey_report.splitlines():
            report_box.label(text=line)