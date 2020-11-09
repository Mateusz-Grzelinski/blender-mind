import bpy

bl_info = {
    "name": "blender_mind",
    "author": "Mateusz Grzelinski, Piotr Swedrak",
    "description": "Predict your next operation",
    "blender": (2, 80, 0),
    "version": (0, 0, 1),
    "location": "",
    "warning": "In development",
    "category": "Generic"
}

from . import auto_load

auto_load.init()

addon_keymaps = []


def register():
    auto_load.register()

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new("wm.predict_operator", type='F', value='PRESS', shift=True)
        addon_keymaps.append((km, kmi))


def unregister():
    auto_load.unregister()

    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
