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

addon_keymaps = []

from . import predict_operator


def register():
    predict_operator.register()

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new("wm.predict_operator", type='F', value='PRESS', shift=True)
        addon_keymaps.append((km, kmi))


def unregister():
    predict_operator.unregister()

    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
