import bpy


class KMTOOLS_PG_settings(bpy.types.PropertyGroup):
    keymap_name: bpy.props.StringProperty(
        name="Keymap",
        description="Blender keymap name to inspect",
        default="3D View",
    )
    event_type: bpy.props.StringProperty(
        name="Key",
        description="Event type, for example A, SPACE, F1, LEFTMOUSE",
        default="A",
    )
    event_value: bpy.props.EnumProperty(
        name="Value",
        description="Key event value",
        items=(
            ("PRESS", "Press", "Key press"),
            ("RELEASE", "Release", "Key release"),
            ("CLICK", "Click", "Mouse click"),
            ("DOUBLE_CLICK", "Double Click", "Mouse double click"),
        ),
        default="PRESS",
    )
    ctrl: bpy.props.BoolProperty(name="Ctrl", default=False)
    shift: bpy.props.BoolProperty(name="Shift", default=False)
    alt: bpy.props.BoolProperty(name="Alt", default=False)
    oskey: bpy.props.BoolProperty(name="OS Key", default=False)
    include_inactive: bpy.props.BoolProperty(
        name="Include Inactive",
        description="Include disabled keymap items in scans",
        default=True,
    )
    show_multi_hotkey_results: bpy.props.BoolProperty(default=False)
    multi_hotkey_result_count: bpy.props.IntProperty(default=0)


def register():
    bpy.types.WindowManager.keymap_tools_settings = bpy.props.PointerProperty(type=KMTOOLS_PG_settings)


def unregister():
    del bpy.types.WindowManager.keymap_tools_settings