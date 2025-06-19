# Project directory: /Users/user/Downloads/flippen
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This is a fork of the original Flippist add-on by Alexey Khlystov.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA
#
# Copyright (C) 2016-2024 Alexey Khlystov and contributors

bl_info = {
    'name': 'flippen',
    'original author': 'Alexey Khlystov',
    'fork_by': 'tankshield',
    'version': (0, 1),
    'blender': (4, 4, 0),
    'location': '3D View > Sidebar > flippen tab and Object > flippen',
    'description': 'Automatically Flip Normals and Make Normals Consistent on multiple objects',
    'category': 'Object'
}

import bpy
from bpy.props import BoolProperty, EnumProperty

def log(text):
    addon_prefs = bpy.context.preferences.addons[__name__].preferences
    if getattr(addon_prefs, 'pref_log', False):
        print('flippen: ' + text)
    return {'FINISHED'}

class flippen_preferences(bpy.types.AddonPreferences):
    bl_idname = __name__
    pref_log: BoolProperty(
        name='Logging',
        description='Logging to the console',
        default=False)

    pref_def: EnumProperty(
        items=[('0', 'Flip Normals', 'Flip Normals'),
               ('1', 'Make Normals Consistent', 'Make Normals Consistent'),
               ('2', 'Make Normals Consistent next Flip Normals', 'Make Normals Consistent next Flip Normals')],
        name='Default behavior (after Blender reload)',
        description='Default behavior',
        default='0')

    def draw(self, context):
        self.layout.prop(self, 'pref_def')
        self.layout.prop(self, 'pref_log')

class flippen(bpy.types.Operator):
    bl_idname = 'object.flippen'
    bl_label = 'flippen'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'UNDO'}

    param: EnumProperty(
        items=[('0', 'Flip Normals', 'Flip Normals'),
               ('1', 'Make Normals Consistent', 'Make Normals Consistent'),
               ('2', 'Make Normals Consistent next Flip Normals', 'Make Normals Consistent next Flip Normals')],
        name='flippen options',
        default='0')

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'param')

    def invoke(self, context, event):
        # Set default from preferences
        addon_prefs = bpy.context.preferences.addons[__name__].preferences
        self.param = getattr(addon_prefs, 'pref_def', '0')
        return self.execute(context)

    def execute(self, context):
        objects = context.selected_objects
        if len(objects) == 0:
            log('no selected objects')
            return {'FINISHED'}

        wm = context.window_manager
        wm.progress_begin(0, len(objects))
        progress = 0

        for obj in objects:
            if obj.type != 'MESH':
                log(obj.name + ' is not a mesh object')
            else:
                context.view_layer.objects.active = obj
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.reveal()
                bpy.ops.mesh.select_all(action='DESELECT')
                import bmesh
                from mathutils import Vector
                bm = bmesh.from_edit_mesh(obj.data)
                bm.faces.ensure_lookup_table()
                if self.param == '0':
                    # Flip only wrongly oriented faces
                    avg_normal = sum((f.normal for f in bm.faces), Vector((0,0,0)))
                    if avg_normal.length == 0:
                        continue
                    avg_normal.normalize()
                    for f in bm.faces:
                        f.select = (f.normal.normalized().dot(avg_normal) < 0)
                    bmesh.update_edit_mesh(obj.data, loop_triangles=False, destructive=False)
                    bpy.ops.mesh.flip_normals()
                elif self.param == '1':
                    # This uses Blender's built-in 'Recalculate Outside' operator,
                    # which matches the Face Orientation overlay (blue = outside)
                    bpy.ops.mesh.select_all(action='SELECT')
                    bpy.ops.mesh.normals_make_consistent(inside=False)
                elif self.param == '2':
                    bpy.ops.mesh.select_all(action='SELECT')
                    bpy.ops.mesh.normals_make_consistent(inside=False)
                    bpy.ops.mesh.flip_normals()
                bpy.ops.object.mode_set(mode='OBJECT')
                log(obj.name + ' - operation complete!')

                # Select non-manifold faces after operation
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.mesh.select_mode(type='EDGE')
                bpy.ops.mesh.select_non_manifold()
                bpy.ops.object.mode_set(mode='OBJECT')

            progress += 1
            wm.progress_update(progress)

        wm.progress_end()
        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator(flippen.bl_idname, icon='MESH_CUBE')

def register():
    bpy.utils.register_class(flippen_preferences)
    bpy.utils.register_class(flippen)
    bpy.types.VIEW3D_MT_object.append(menu_func)

def unregister():
    bpy.types.VIEW3D_MT_object.remove(menu_func)
    bpy.utils.unregister_class(flippen)
    bpy.utils.unregister_class(flippen_preferences)

# This is the end of the file 
