import bpy

from ..functions.keymap_importer import import_keymap_preset, remove_invalid_user_keymap_items


class KMTOOLS_OT_import_keymap_preset(bpy.types.Operator):
    """Import a Blender keymap preset without adding duplicate bindings."""

    bl_idname = "keymap_tools.import_keymap_preset"
    bl_label = "Import Keymap"
    bl_description = "Import a Blender keymap preset and skip bindings that already exist"
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