from __future__ import annotations

import bpy

from ..functions.keymap_scanner import (
    find_hotkey_matches,
    format_item_ref,
    list_available_key_summary,
    remove_exact_duplicates,
    scan_exact_duplicates,
)


class KMTOOLS_OT_scan_exact_duplicates(bpy.types.Operator):
    """Scan active keyconfig for exactly duplicated keymap items."""

    bl_idname = "keymap_tools.scan_exact_duplicates"
    bl_label = "Scan Exact Duplicates"
    bl_description = "Find exactly duplicated keymap items in the active keyconfig"
    bl_options = {"REGISTER"}

    def execute(self, context):
        settings = context.window_manager.keymap_tools_settings
        duplicates = scan_exact_duplicates(include_inactive=settings.include_inactive)
        for refs in duplicates.values():
            print("Keymap Tools duplicate group:")
            for ref in refs:
                print("  " + format_item_ref(ref))
        self.report({"INFO"}, f"Found {len(duplicates)} duplicate groups")
        return {"FINISHED"}


class KMTOOLS_OT_remove_exact_duplicates(bpy.types.Operator):
    """Remove exactly duplicated keymap items, keeping the first item in each group."""

    bl_idname = "keymap_tools.remove_exact_duplicates"
    bl_label = "Remove Exact Duplicates"
    bl_description = "Remove exact duplicate keymap items from the active keyconfig"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = context.window_manager.keymap_tools_settings
        removed = remove_exact_duplicates(include_inactive=settings.include_inactive)
        self.report({"INFO"}, f"Removed {removed} duplicate keymap items")
        return {"FINISHED"}


class KMTOOLS_OT_check_hotkey_conflict(bpy.types.Operator):
    """Check which keymap items match the configured hotkey."""

    bl_idname = "keymap_tools.check_hotkey_conflict"
    bl_label = "Check Hotkey Conflict"
    bl_description = "List keymap items matching the configured key and modifiers"
    bl_options = {"REGISTER"}

    def execute(self, context):
        settings = context.window_manager.keymap_tools_settings
        try:
            matches = find_hotkey_matches(
                keymap_name=settings.keymap_name,
                event_type=settings.event_type.strip().upper(),
                event_value=settings.event_value,
                ctrl=settings.ctrl,
                shift=settings.shift,
                alt=settings.alt,
                oskey=settings.oskey,
                include_inactive=settings.include_inactive,
            )
        except KeyError as error:
            raise RuntimeError(f"Failed to check hotkey in keymap {settings.keymap_name!r}") from error

        print(f"Keymap Tools hotkey matches: {settings.keymap_name}")
        for ref in matches:
            print("  " + format_item_ref(ref))
        self.report({"INFO"}, f"Found {len(matches)} matching keymap items")
        return {"FINISHED"}


class KMTOOLS_OT_list_available_keys(bpy.types.Operator):
    """Summarize common free key combinations in the configured keymap."""

    bl_idname = "keymap_tools.list_available_keys"
    bl_label = "List Available Keys"
    bl_description = "Summarize occupied and available common key combinations"
    bl_options = {"REGISTER"}

    def execute(self, context):
        settings = context.window_manager.keymap_tools_settings
        try:
            free_count, occupied_count = list_available_key_summary(
                settings.keymap_name,
                include_inactive=settings.include_inactive,
            )
        except KeyError as error:
            raise RuntimeError(f"Failed to list available keys in keymap {settings.keymap_name!r}") from error

        print(
            "Keymap Tools availability: "
            f"keymap={settings.keymap_name!r}, free={free_count}, occupied={occupied_count}"
        )
        self.report({"INFO"}, f"Free: {free_count}, occupied: {occupied_count}")
        return {"FINISHED"}