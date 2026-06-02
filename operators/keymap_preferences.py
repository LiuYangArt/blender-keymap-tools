import bpy

from ..functions.keymap_importer import import_keymap_preset, remove_invalid_user_keymap_items
from ..functions.keymap_scanner import scan_hotkey_conflicts, scan_multi_hotkey_bindings


class KMTOOLS_OT_import_keymap_preset(bpy.types.Operator):
    """Import a Blender keymap preset without adding duplicate bindings."""

    bl_idname = "keymap_tools.import_keymap_preset"
    bl_label = "Import Keymap"
    bl_description = "Import a Blender keymap preset, skip duplicates, and remove invalid bindings"
    bl_options = {"REGISTER", "UNDO"}

    filepath: bpy.props.StringProperty(name="File Path", subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(default="*.py", options={"HIDDEN"})
    filter_python: bpy.props.BoolProperty(default=True, options={"HIDDEN"})

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        result = import_keymap_preset(self.filepath)
        print(
            "Keymap Tools import: "
            f"keymaps={result.keymaps_seen}, items={result.items_seen}, "
            f"imported={result.imported}, skipped_duplicates={result.skipped_duplicates}, "
            f"removed_invalid={result.removed_invalid}"
        )
        self.report(
            {"INFO"},
            f"Imported {result.imported}; skipped {result.skipped_duplicates}; removed invalid {result.removed_invalid}",
        )
        return {"FINISHED"}


class KMTOOLS_OT_remove_invalid_keymap_items(bpy.types.Operator):
    """Remove user keymap items whose operators are no longer registered."""

    bl_idname = "keymap_tools.remove_invalid_keymap_items"
    bl_label = "Remove Invalid Keymaps"
    bl_description = "Remove user keymap items for missing or disabled operators"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        result = remove_invalid_user_keymap_items()
        self.report({"INFO"}, f"Removed {result.removed} invalid keymap items")
        print(f"Keymap Tools invalid cleanup: scanned={result.scanned}, removed={result.removed}")
        return {"FINISHED"}


class KMTOOLS_OT_scan_multi_hotkey_bindings(bpy.types.Operator):
    """Find same-context operator/property bindings with more than one active hotkey."""

    bl_idname = "keymap_tools.scan_multi_hotkey_bindings"
    bl_label = "Scan Multi-Bound Actions"
    bl_description = "List same-context actions that are bound to multiple different hotkeys"
    bl_options = {"REGISTER"}

    def execute(self, context):
        groups = scan_multi_hotkey_bindings(include_inactive=False)
        settings = context.window_manager.keymap_tools_settings
        settings.show_multi_hotkey_results = True
        settings.expand_multi_hotkey_results = True
        settings.multi_hotkey_result_count = len(groups)
        print(f"Keymap Tools multi-bound action scan: groups={len(groups)}")
        self.report({"INFO"}, f"Found {len(groups)} multi-bound action groups")
        return {"FINISHED"}


class KMTOOLS_OT_scan_hotkey_conflicts(bpy.types.Operator):
    """Find same-context hotkeys that trigger multiple actions."""

    bl_idname = "keymap_tools.scan_hotkey_conflicts"
    bl_label = "Scan Hotkey Conflicts"
    bl_description = "List same-context hotkeys that are assigned to multiple actions"
    bl_options = {"REGISTER"}

    def execute(self, context):
        groups = scan_hotkey_conflicts(include_inactive=False)
        settings = context.window_manager.keymap_tools_settings
        settings.show_hotkey_conflict_results = True
        settings.expand_hotkey_conflict_results = True
        settings.hotkey_conflict_result_count = len(groups)
        print(f"Keymap Tools hotkey conflict scan: groups={len(groups)}")
        self.report({"INFO"}, f"Found {len(groups)} hotkey conflict groups")
        return {"FINISHED"}


class KMTOOLS_OT_clear_keymap_tool_results(bpy.types.Operator):
    """Clear displayed keymap scan results."""

    bl_idname = "keymap_tools.clear_results"
    bl_label = "Clear Results"
    bl_description = "Clear displayed keymap scan results"
    bl_options = {"REGISTER"}

    result_type: bpy.props.EnumProperty(
        items=(
            ("MULTI_BOUND", "Multi-Bound Actions", "Clear multi-bound action results"),
            ("CONFLICTS", "Hotkey Conflicts", "Clear hotkey conflict results"),
        ),
        default="MULTI_BOUND",
    )

    def execute(self, context):
        settings = context.window_manager.keymap_tools_settings
        if self.result_type == "MULTI_BOUND":
            settings.show_multi_hotkey_results = False
            settings.multi_hotkey_result_count = 0
        elif self.result_type == "CONFLICTS":
            settings.show_hotkey_conflict_results = False
            settings.hotkey_conflict_result_count = 0
        else:
            raise RuntimeError(f"Unknown keymap result type: {self.result_type}")
        return {"FINISHED"}
