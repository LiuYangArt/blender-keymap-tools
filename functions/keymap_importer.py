from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import bpy

from .keymap_scanner import iter_property_items, repr_keymap_property_value


@dataclass(frozen=True)
class KeymapImportItemKey:
    keymap_name: str
    is_modal: bool
    idname: str
    properties: tuple[tuple[str, str], ...]
    event_type: str
    value: str
    any: bool
    ctrl: int
    shift: int
    alt: int
    oskey: int
    hyper: int
    key_modifier: str
    direction: str
    repeat: bool


@dataclass(frozen=True)
class KeymapImportResult:
    keymaps_seen: int
    items_seen: int
    imported: int
    skipped_duplicates: int
    removed_invalid: int


@dataclass(frozen=True)
class InvalidKeymapCleanupResult:
    scanned: int
    removed: int


_KEYMAP_OPTION_KEYS = {"space_type", "region_type", "modal", "tool"}
_KEYMAP_DATA_KEYS = {"items"}
_EVENT_OPTION_KEYS = {"any", "shift", "ctrl", "alt", "oskey", "hyper", "key_modifier", "direction", "repeat"}
_NON_MODAL_EVENT_OPTION_KEYS = _EVENT_OPTION_KEYS | {"head"}
_ITEM_OPTION_KEYS = {"properties", "active"}


def import_keymap_preset(filepath: str) -> KeymapImportResult:
    keyconfig_data = load_keyconfig_data(filepath)
    existing_keys = collect_existing_import_keys()
    user_keyconfig = get_user_keyconfig()

    keymaps_seen = 0
    items_seen = 0
    imported = 0
    skipped_duplicates = 0

    for keymap_name, keymap_args, keymap_data in keyconfig_data:
        keymaps_seen += 1
        unknown_keymap_args = set(keymap_args) - _KEYMAP_OPTION_KEYS
        if unknown_keymap_args:
            raise RuntimeError(f"Unsupported keymap options for {keymap_name!r}: {sorted(unknown_keymap_args)}")
        unknown_keymap_data = set(keymap_data) - _KEYMAP_DATA_KEYS
        if unknown_keymap_data:
            raise RuntimeError(f"Unsupported keymap data for {keymap_name!r}: {sorted(unknown_keymap_data)}")

        is_modal = bool(keymap_args.get("modal", False))
        keymap = user_keyconfig.keymaps.new(
            keymap_name,
            space_type=keymap_args.get("space_type", "EMPTY"),
            region_type=keymap_args.get("region_type", "WINDOW"),
            modal=is_modal,
            tool=bool(keymap_args.get("tool", False)),
        )

        for idname, event_args, item_args in keymap_data.get("items", ()):  # Blender export format.
            items_seen += 1
            item_key = make_import_item_key(keymap_name, is_modal, idname, event_args, item_args)
            if item_key in existing_keys:
                skipped_duplicates += 1
                continue

            item = create_keymap_item(keymap, idname, event_args)
            apply_item_options(item, item_args, idname)
            existing_keys.add(item_key)
            imported += 1

    cleanup_result = remove_invalid_user_keymap_items()
    return KeymapImportResult(
        keymaps_seen=keymaps_seen,
        items_seen=items_seen,
        imported=imported,
        skipped_duplicates=skipped_duplicates,
        removed_invalid=cleanup_result.removed,
    )


def remove_invalid_user_keymap_items() -> InvalidKeymapCleanupResult:
    keyconfig = get_user_keyconfig()
    scanned = 0
    removed = 0

    for keymap in keyconfig.keymaps:
        if keymap.is_modal:
            continue
        for item in list(keymap.keymap_items):
            scanned += 1
            if operator_exists(item.idname):
                continue
            print(f"Keymap Tools removing invalid item: {keymap.name}: {item.idname} {item.to_string(compact=True)}")
            keymap.keymap_items.remove(item)
            removed += 1

    return InvalidKeymapCleanupResult(scanned=scanned, removed=removed)


def load_keyconfig_data(filepath: str) -> list[Any]:
    path = Path(filepath)
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except Exception as error:
        raise RuntimeError(f"Failed to read keymap preset: {path}") from error

    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if any(isinstance(target, ast.Name) and target.id == "keyconfig_data" for target in node.targets):
            try:
                return ast.literal_eval(node.value)
            except Exception as error:
                raise RuntimeError(f"Failed to parse keyconfig_data in: {path}") from error

    raise RuntimeError(f"No keyconfig_data assignment found in: {path}")


def get_user_keyconfig() -> bpy.types.KeyConfig:
    keyconfig = bpy.context.window_manager.keyconfigs.user
    if keyconfig is None:
        raise RuntimeError("No Blender user keyconfig is available")
    return keyconfig


def collect_existing_import_keys() -> set[KeymapImportItemKey]:
    window_manager = bpy.context.window_manager
    keys: set[KeymapImportItemKey] = set()
    for keyconfig in (window_manager.keyconfigs.active, window_manager.keyconfigs.user):
        if keyconfig is None:
            continue
        for keymap in keyconfig.keymaps:
            for item in keymap.keymap_items:
                keys.add(make_existing_item_key(keymap, item))
    return keys


def make_existing_item_key(keymap: bpy.types.KeyMap, item: bpy.types.KeyMapItem) -> KeymapImportItemKey:
    idname = item.propvalue if keymap.is_modal else item.idname
    return KeymapImportItemKey(
        keymap_name=keymap.name,
        is_modal=keymap.is_modal,
        idname=idname,
        properties=tuple(sorted(iter_property_items(item))) if not keymap.is_modal else (),
        event_type=item.type,
        value=item.value,
        any=bool(item.any),
        ctrl=item.ctrl,
        shift=item.shift,
        alt=item.alt,
        oskey=item.oskey,
        hyper=item.hyper,
        key_modifier=item.key_modifier,
        direction=item.direction,
        repeat=item.repeat,
    )


def make_import_item_key(
    keymap_name: str,
    is_modal: bool,
    idname: str,
    event_args: dict[str, Any],
    item_args: dict[str, Any] | None,
) -> KeymapImportItemKey:
    any_modifier = bool(event_args.get("any", False))
    return KeymapImportItemKey(
        keymap_name=keymap_name,
        is_modal=is_modal,
        idname=idname,
        properties=extract_import_properties(item_args) if not is_modal else (),
        event_type=event_args["type"],
        value=event_args["value"],
        any=any_modifier,
        ctrl=normalize_modifier(event_args, "ctrl", any_modifier),
        shift=normalize_modifier(event_args, "shift", any_modifier),
        alt=normalize_modifier(event_args, "alt", any_modifier),
        oskey=normalize_modifier(event_args, "oskey", any_modifier),
        hyper=normalize_modifier(event_args, "hyper", any_modifier),
        key_modifier=event_args.get("key_modifier", "NONE"),
        direction=event_args.get("direction", "ANY"),
        repeat=bool(event_args.get("repeat", False)),
    )


def normalize_modifier(event_args: dict[str, Any], name: str, any_modifier: bool) -> int:
    if any_modifier and name not in event_args:
        return -1
    return int(event_args.get(name, False))


def extract_import_properties(item_args: dict[str, Any] | None) -> tuple[tuple[str, str], ...]:
    if not item_args:
        return ()
    return tuple(sorted(iter_import_property_items(item_args.get("properties", ()))))


def iter_import_property_items(properties: Iterable[tuple[str, Any]], prefix: str = "") -> Iterable[tuple[str, str]]:
    for name, value in properties:
        path = f"{prefix}.{name}" if prefix else name
        if isinstance(value, list):
            yield from iter_import_property_items(value, path)
        else:
            yield path, repr_keymap_property_value(value)


def create_keymap_item(keymap: bpy.types.KeyMap, idname: str, event_args: dict[str, Any]) -> bpy.types.KeyMapItem:
    option_keys = _EVENT_OPTION_KEYS if keymap.is_modal else _NON_MODAL_EVENT_OPTION_KEYS
    unknown_keys = set(event_args) - option_keys - {"type", "value"}
    if unknown_keys:
        raise RuntimeError(f"Unsupported keymap event options for {idname!r}: {sorted(unknown_keys)}")

    options = {name: event_args[name] for name in option_keys if name in event_args}
    if keymap.is_modal:
        return keymap.keymap_items.new_modal(idname, event_args["type"], event_args["value"], **options)
    return keymap.keymap_items.new(idname, event_args["type"], event_args["value"], **options)


def apply_item_options(item: bpy.types.KeyMapItem, item_args: dict[str, Any] | None, idname: str) -> None:
    if not item_args:
        return

    unknown_keys = set(item_args) - _ITEM_OPTION_KEYS
    if unknown_keys:
        raise RuntimeError(f"Unsupported keymap item options for {idname!r}: {sorted(unknown_keys)}")

    apply_properties(item.properties, item_args.get("properties", ()), idname)

    if "active" in item_args:
        item.active = bool(item_args["active"])


def apply_properties(
    base_properties: bpy.types.OperatorProperties,
    properties: Iterable[tuple[str, Any]],
    idname: str,
) -> None:
    for name, value in properties:
        if isinstance(value, list):
            try:
                base_properties.property_unset(name)
                nested_properties = getattr(base_properties, name)
            except AttributeError as error:
                raise RuntimeError(f"Failed to find nested keymap property {name!r} on {idname!r}") from error
            apply_properties(nested_properties, value, idname)
            continue

        try:
            setattr(base_properties, name, value)
        except AttributeError:
            try:
                base_properties[name] = value
            except Exception as error:
                raise RuntimeError(f"Failed to store keymap property {name!r} on {idname!r}") from error
        except Exception as error:
            raise RuntimeError(f"Failed to set keymap property {name!r} on {idname!r}") from error


def operator_exists(idname: str) -> bool:
    if "." not in idname:
        return False
    module_name, operator_name = idname.split(".", 1)
    try:
        operator = getattr(getattr(bpy.ops, module_name), operator_name)
        return operator.get_rna_type() is not None
    except (AttributeError, KeyError, RuntimeError, TypeError):
        return False