import os
import tempfile

# import addon_utils

script = """
import bpy
import addon_utils

# bpy.utils.script_paths()
addon_utils.enable(module_name='blender_mind', default_set=True)
bpy.ops.debug.connect_debugger_pycharm()
"""

with tempfile.NamedTemporaryFile('w') as file:
    file.write(script)
    command = f'blender --python {file.name} start.blend'
    print(command)
    os.system(command)
