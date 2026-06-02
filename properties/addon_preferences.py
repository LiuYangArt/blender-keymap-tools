from __future__ import annotations

import bpy


class KMTOOLS_AP_preferences(bpy.types.AddonPreferences):
    bl_idname = __package__.rsplit(".", 1)[0]

    def draw(self, context):
        layout = self.layout
        layout.operator("keymap_tools.import_keymap_preset", icon="IMPORT")
        layout.operator("keymap_tools.remove_invalid_keymap_items", icon="TRASH")