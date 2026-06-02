from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from struct import pack, unpack
from typing import Iterable

import bpy


def round_float_32(value: float) -> float:
    return unpack("f", pack("f", value))[0]


def repr_float_32(value: float) -> str:
    rounded_value = round_float_32(value)
    value_repr = repr(value)
    fraction = value_repr.partition(".")[2]
    if not fraction:
        return value_repr
    for precision in range(1, len(fraction)):
        rounded_test = round(value, precision)
        if round_float_32(rounded_test) == rounded_value:
            return f"{rounded_test:.{precision}f}"
    return value_repr


def repr_keymap_property_value(value: object) -> str:
    if isinstance(value, float):
        return repr_float_32(value)
    return repr(value)


@dataclass(frozen=True)
class KeymapItemSignature:
    keymap_name: str
    is_modal: bool
    idname: str
    properties: tuple[tuple[str, str], ...]
    map_type: str
    event_type: str
    value: str
    ctrl: int
    shift: int
    alt: int
    oskey: int
    key_modifier: str
    direction: str
    repeat: bool


@dataclass(frozen=True)
class KeymapFunctionKey:
    keymap_name: str
    idname: str
    properties: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class KeymapItemRef:
    keymap_name: str
    item_id: int
    idname: str
    label: str
    active: bool
    signature: KeymapItemSignature


@dataclass(frozen=True)
class MultiHotkeyGroup:
    key: KeymapFunctionKey
    label: str
    items: tuple[KeymapItemRef, ...]


def get_active_keyconfig() -> bpy.types.KeyConfig:
    keyconfig = bpy.context.window_manager.keyconfigs.active
    if keyconfig is None:
        raise RuntimeError("No active Blender keyconfig is available")
    return keyconfig


def get_user_keyconfig() -> bpy.types.KeyConfig:
    keyconfig = bpy.context.window_manager.keyconfigs.user
    if keyconfig is None:
        raise RuntimeError("No Blender user keyconfig is available")
    return keyconfig


def get_default_keyconfig() -> bpy.types.KeyConfig | None:
    return bpy.context.window_manager.keyconfigs.default


def iter_keymaps(keyconfig: bpy.types.KeyConfig | None = None) -> Iterable[bpy.types.KeyMap]:
    source = keyconfig or get_active_keyconfig()
    yield from source.keymaps


def find_keymap(name: str, keyconfig: bpy.types.KeyConfig | None = None) -> bpy.types.KeyMap:
    normalized = name.strip().casefold()
    for keymap in iter_keymaps(keyconfig):
        if keymap.name.casefold() == normalized:
            return keymap
    raise KeyError(f"Keymap not found: {name}")


def keymap_item_signature(keymap: bpy.types.KeyMap, item: bpy.types.KeyMapItem) -> KeymapItemSignature:
    return KeymapItemSignature(
        keymap_name=keymap.name,
        is_modal=keymap.is_modal,
        idname=item.idname,
        properties=tuple(sorted(iter_property_items(item))),
        map_type=item.map_type,
        event_type=item.type,
        value=item.value,
        ctrl=item.ctrl,
        shift=item.shift,
        alt=item.alt,
        oskey=item.oskey,
        key_modifier=item.key_modifier,
        direction=item.direction,
        repeat=item.repeat,
    )


def keymap_function_key(keymap: bpy.types.KeyMap, item: bpy.types.KeyMapItem) -> KeymapFunctionKey:
    return KeymapFunctionKey(
        keymap_name=keymap.name,
        idname=item.idname,
        properties=tuple(sorted(iter_property_items(item))),
    )


def iter_property_items(item: bpy.types.KeyMapItem) -> Iterable[tuple[str, str]]:
    yield from iter_operator_property_items(item.properties)


def iter_operator_property_items(
    properties: bpy.types.OperatorProperties | None,
    prefix: str = "",
) -> Iterable[tuple[str, str]]:
    if properties is None:
        return
    for name in properties.keys():
        path = f"{prefix}.{name}" if prefix else name
        try:
            value = getattr(properties, name)
        except AttributeError:
            value = properties[name]
        if isinstance(value, bpy.types.OperatorProperties):
            yield from iter_operator_property_items(value, path)
            continue
        if isinstance(value, bpy.types.bpy_struct):
            continue
        yield path, repr_keymap_property_value(value)


def make_item_ref(keymap: bpy.types.KeyMap, item: bpy.types.KeyMapItem) -> KeymapItemRef:
    return KeymapItemRef(
        keymap_name=keymap.name,
        item_id=item.id,
        idname=item.idname,
        label=item.name,
        active=item.active,
        signature=keymap_item_signature(keymap, item),
    )


def scan_exact_duplicates(include_inactive: bool = True) -> dict[KeymapItemSignature, list[KeymapItemRef]]:
    groups: dict[KeymapItemSignature, list[KeymapItemRef]] = defaultdict(list)
    for keymap in iter_keymaps():
        for item in keymap.keymap_items:
            if include_inactive or item.active:
                groups[keymap_item_signature(keymap, item)].append(make_item_ref(keymap, item))
    return {signature: refs for signature, refs in groups.items() if len(refs) > 1}


def remove_exact_duplicates(include_inactive: bool = True) -> int:
    removed = 0
    for signature, refs in scan_exact_duplicates(include_inactive=include_inactive).items():
        keymap = find_keymap(signature.keymap_name)
        keep_id = refs[0].item_id
        for ref in refs[1:]:
            if ref.item_id == keep_id:
                continue
            item = keymap.keymap_items.from_id(ref.item_id)
            if item is not None:
                keymap.keymap_items.remove(item)
                removed += 1
    return removed


def collect_default_signatures(include_inactive: bool = False) -> set[KeymapItemSignature]:
    keyconfig = get_default_keyconfig()
    if keyconfig is None:
        return set()

    signatures = set()
    for keymap in iter_keymaps(keyconfig):
        if keymap.is_modal:
            continue
        for item in keymap.keymap_items:
            if include_inactive or item.active:
                signatures.add(keymap_item_signature(keymap, item))
    return signatures

def find_hotkey_matches(
    keymap_name: str,
    event_type: str,
    event_value: str,
    ctrl: bool,
    shift: bool,
    alt: bool,
    oskey: bool,
    include_inactive: bool = True,
) -> list[KeymapItemRef]:
    keymap = find_keymap(keymap_name)
    matches: list[KeymapItemRef] = []
    for item in keymap.keymap_items:
        if not include_inactive and not item.active:
            continue
        if item.type != event_type:
            continue
        if item.value != event_value:
            continue
        if bool(item.ctrl) != ctrl or bool(item.shift) != shift:
            continue
        if bool(item.alt) != alt or bool(item.oskey) != oskey:
            continue
        matches.append(make_item_ref(keymap, item))
    return matches


def scan_multi_hotkey_bindings(include_inactive: bool = False) -> list[MultiHotkeyGroup]:
    default_signatures = collect_default_signatures(include_inactive=include_inactive)
    groups: dict[KeymapFunctionKey, list[KeymapItemRef]] = defaultdict(list)
    for keymap in iter_keymaps(get_user_keyconfig()):
        if keymap.is_modal:
            continue
        for item in keymap.keymap_items:
            if not include_inactive and not item.active:
                continue
            if not item.idname:
                continue
            if keymap_item_signature(keymap, item) in default_signatures:
                continue
            groups[keymap_function_key(keymap, item)].append(make_item_ref(keymap, item))

    result = []
    for key, refs in groups.items():
        hotkeys = {format_hotkey_ref(ref) for ref in refs}
        if len(hotkeys) <= 1:
            continue
        label = next((ref.label for ref in refs if ref.label), key.idname)
        result.append(MultiHotkeyGroup(key=key, label=label, items=tuple(refs)))
    return sorted(result, key=lambda group: (group.key.keymap_name.casefold(), group.label.casefold(), group.key.idname))


def format_hotkey_ref(ref: KeymapItemRef) -> str:
    sig = ref.signature
    modifiers = [
        name
        for name, enabled in (("Ctrl", sig.ctrl), ("Shift", sig.shift), ("Alt", sig.alt), ("OS", sig.oskey))
        if enabled
    ]
    if sig.key_modifier and sig.key_modifier != "NONE":
        modifiers.append(sig.key_modifier)
    hotkey = "+".join([*modifiers, sig.event_type]) if modifiers else sig.event_type
    return f"{hotkey} {sig.value}"


def format_item_ref(ref: KeymapItemRef) -> str:
    state = "active" if ref.active else "inactive"
    hotkey = format_hotkey_ref(ref)
    return f"[{state}] {ref.keymap_name}: {hotkey} -> {ref.idname} ({ref.label})"


def list_available_key_summary(keymap_name: str, include_inactive: bool = True) -> tuple[int, int]:
    keymap = find_keymap(keymap_name)
    occupied = set()
    for item in keymap.keymap_items:
        if include_inactive or item.active:
            occupied.add((item.type, bool(item.ctrl), bool(item.shift), bool(item.alt), bool(item.oskey)))

    candidates = [chr(code) for code in range(ord("A"), ord("Z") + 1)]
    candidates.extend(str(number) for number in range(10))
    candidates.extend(f"F{number}" for number in range(1, 13))
    modifiers = [
        (False, False, False, False),
        (True, False, False, False),
        (False, True, False, False),
        (False, False, True, False),
        (True, True, False, False),
        (True, False, True, False),
    ]

    total = len(candidates) * len(modifiers)
    used = sum(1 for key in candidates for mods in modifiers if (key, *mods) in occupied)
    return total - used, used