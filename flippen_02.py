bl_info = {
    'name': 'flippen',
    'author': 'Alexey Khlystov, tankshield',
    'version': (0, 2),
    'blender': (4, 4, 0),
    'location': '3D View > Object menu',
    'description': 'Automatically Flip Normals and Make Normals Consistent on multiple objects using neighbor consistency check',
    'category': 'Object'
}

import bpy
from bpy.props import EnumProperty

def log(text):
    addon_prefs = bpy.context.preferences.addons[__name__].preferences
    if getattr(addon_prefs, 'pref_log', False):
        print('flippen: ' + text)
    return {'FINISHED'}

class flippen_preferences(bpy.types.AddonPreferences):
    bl_idname = __name__
    pref_log: bpy.props.BoolProperty(
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
        self.layout.label(text="Report bugs or get help:")
        self.layout.operator("wm.url_open", text="flippen on GitHub").url = "https://github.com/tankshield/flippen"

class FLIPPEN_OT_persistent(bpy.types.Operator):
    bl_idname = 'object.flippen_persistent'
    bl_label = 'Persistent Flip'
    def execute(self, context):
        max_passes = context.window_manager.flippen_max_passes
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'WARNING'}, 'No active mesh object')
            return {'CANCELLED'}
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.reveal()
        bpy.ops.mesh.select_all(action='DESELECT')
        import bmesh
        bm = bmesh.from_edit_mesh(obj.data)
        bm.faces.ensure_lookup_table()
        total_flipped = 0
        for pass_num in range(max_passes):
            faces_to_flip = []
            for f in bm.faces:
                neighbor_normals = []
                for loop in f.loops:
                    edge = loop.edge
                    for linked_face in edge.link_faces:
                        if linked_face != f:
                            neighbor_normals.append(linked_face.normal.normalized())
                if not neighbor_normals:
                    continue
                dot_products = [f.normal.normalized().dot(n) for n in neighbor_normals]
                num_opposite = sum(1 for d in dot_products if d < 0)
                if num_opposite > len(neighbor_normals) / 2:
                    faces_to_flip.append(f)
            if not faces_to_flip:
                break
            for f in bm.faces:
                f.select = False
            for f in faces_to_flip:
                f.select = True
            bmesh.update_edit_mesh(obj.data, loop_triangles=False, destructive=False)
            bpy.ops.mesh.flip_normals()
            total_flipped += len(faces_to_flip)
        bpy.ops.object.mode_set(mode='OBJECT')
        self.report({'INFO'}, f'Persistent Flip: {total_flipped} faces flipped in up to {max_passes} passes')
        return {'FINISHED'}

class FLIPPEN_OT_manual_align_start(bpy.types.Operator):
    bl_idname = 'object.flippen_manual_align_start'
    bl_label = 'Start Manual Align'
    bl_description = 'Select a face in Edit Mode (Face Select), then click Run Manual Align'

    def execute(self, context):
        self.report({'INFO'}, 'Select a face in Edit Mode, then click Run Manual Align')
        return {'FINISHED'}

class FLIPPEN_OT_manual_align_run(bpy.types.Operator):
    bl_idname = 'object.flippen_manual_align_run'
    bl_label = 'Run Manual Align'
    bl_description = 'Propagate correct orientation from the selected face to all connected faces'

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'WARNING'}, 'No active mesh object')
            return {'CANCELLED'}
        import bmesh
        bm = bmesh.from_edit_mesh(obj.data)
        bm.faces.ensure_lookup_table()
        # Find the selected face
        seed_faces = [f for f in bm.faces if f.select]
        if not seed_faces:
            self.report({'WARNING'}, 'No face selected. Please select a face in Edit Mode (Face Select).')
            return {'CANCELLED'}
        seed_face = seed_faces[0]
        # Propagate orientation using BFS
        from collections import deque
        visited = set()
        queue = deque()
        queue.append((seed_face, seed_face.normal.copy()))
        while queue:
            face, ref_normal = queue.popleft()
            if face.index in visited:
                continue
            visited.add(face.index)
            # If the face normal is opposite to the reference, flip it
            if face.normal.dot(ref_normal) < 0:
                face.normal_flip()
            # Add neighbors
            for loop in face.loops:
                edge = loop.edge
                for linked_face in edge.link_faces:
                    if linked_face.index not in visited:
                        queue.append((linked_face, face.normal.copy()))
        bmesh.update_edit_mesh(obj.data, loop_triangles=False, destructive=False)
        self.report({'INFO'}, 'Manual align complete!')
        return {'FINISHED'}

class FLIPPEN_OT_exhe(bpy.types.Operator):
    bl_idname = 'object.flippen_exhe'
    bl_label = 'Exterior Heuristic Flip'
    bl_description = 'Exterior Exposure Heuristic: Orient boundary faces based on exposure to empty space (works for rooms and exteriors)'

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'WARNING'}, 'No active mesh object')
            return {'CANCELLED'}
        if obj.mode != 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')
        import bmesh
        from mathutils import Vector
        bm = bmesh.from_edit_mesh(obj.data)
        bm.faces.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.verts.ensure_lookup_table()
        # Find boundary faces (faces with at least one boundary edge)
        boundary_faces = set()
        for e in bm.edges:
            if len(e.link_faces) == 1:
                boundary_faces.add(e.link_faces[0])
        # Use ray_cast to check exposure
        depsgraph = context.evaluated_depsgraph_get()
        obj_eval = obj.evaluated_get(depsgraph)
        mesh_eval = obj_eval.to_mesh()
        flipped_count = 0
        for f in boundary_faces:
            face_center = f.calc_center_median()
            normal = f.normal.normalized()
            # Cast a ray from just outside the face along the normal
            ray_origin = obj.matrix_world @ (face_center + normal * 0.001)
            ray_dir = obj.matrix_world.to_3x3() @ normal
            hit, loc, norm, idx, obj_, mat = context.scene.ray_cast(
                depsgraph, ray_origin, ray_dir, distance=0.5)
            # Cast in the opposite direction as well
            ray_origin_back = obj.matrix_world @ (face_center - normal * 0.001)
            ray_dir_back = obj.matrix_world.to_3x3() @ (-normal)
            hit_back, loc_back, norm_back, idx_back, obj_back, mat_back = context.scene.ray_cast(
                depsgraph, ray_origin_back, ray_dir_back, distance=0.5)
            # If the ray in the normal direction does NOT hit, it's exposed
            if not hit:
                # If the normal is pointing inward (into the mesh), flip it
                if normal.dot(f.normal) < 0.0:
                    f.normal_flip()
                    flipped_count += 1
            # If the ray in the opposite direction does NOT hit, it's interior (room)
            elif not hit_back:
                # If the normal is pointing outward (into the wall), flip it
                if normal.dot(f.normal) > 0.0:
                    f.normal_flip()
                    flipped_count += 1
        bmesh.update_edit_mesh(obj.data, loop_triangles=False, destructive=False)
        obj_eval.to_mesh_clear()
        self.report({'INFO'}, f'Exterior Heuristic Flip: {flipped_count} faces flipped')
        return {'FINISHED'}

class FLIPPEN_OT_flood_flip(bpy.types.Operator):
    bl_idname = 'object.flippen_flood_flip'
    bl_label = 'Flood Flip'
    bl_description = 'Flood fill from outside: propagate correct orientation from outside the mesh'

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'WARNING'}, 'No active mesh object')
            return {'CANCELLED'}
        if obj.mode != 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')
        import bmesh
        from mathutils import Vector
        bm = bmesh.from_edit_mesh(obj.data)
        bm.faces.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.verts.ensure_lookup_table()
        # Find a point outside the mesh (min bounding box corner)
        min_corner = Vector((min(v.co.x for v in bm.verts), min(v.co.y for v in bm.verts), min(v.co.z for v in bm.verts)))
        # Find the closest face to the min_corner
        seed_face = min(bm.faces, key=lambda f: (f.calc_center_median() - min_corner).length)
        # Flood fill from the seed face
        from collections import deque
        visited = set()
        queue = deque()
        queue.append((seed_face, seed_face.normal.copy()))
        flipped_count = 0
        while queue:
            face, ref_normal = queue.popleft()
            if face.index in visited:
                continue
            visited.add(face.index)
            # If the face normal is opposite to the reference, flip it
            if face.normal.dot(ref_normal) < 0:
                face.normal_flip()
                flipped_count += 1
            # Add neighbors
            for loop in face.loops:
                edge = loop.edge
                for linked_face in edge.link_faces:
                    if linked_face.index not in visited:
                        queue.append((linked_face, face.normal.copy()))
        bmesh.update_edit_mesh(obj.data, loop_triangles=False, destructive=False)
        self.report({'INFO'}, f'Flood Flip: {flipped_count} faces flipped')
        return {'FINISHED'}

class FLIPPEN_OT_hybrid_flip(bpy.types.Operator):
    bl_idname = 'object.flippen_hybrid_flip'
    bl_label = 'Hybrid Flip'
    bl_description = 'Persistent Flip followed by Recalculate Outside'

    def execute(self, context):
        max_passes = context.window_manager.flippen_max_passes
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'WARNING'}, 'No active mesh object')
            return {'CANCELLED'}
        if obj.mode != 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')
        import bmesh
        bm = bmesh.from_edit_mesh(obj.data)
        bm.faces.ensure_lookup_table()
        total_flipped = 0
        for pass_num in range(max_passes):
            faces_to_flip = []
            for f in bm.faces:
                neighbor_normals = []
                for loop in f.loops:
                    edge = loop.edge
                    for linked_face in edge.link_faces:
                        if linked_face != f:
                            neighbor_normals.append(linked_face.normal.normalized())
                if not neighbor_normals:
                    continue
                dot_products = [f.normal.normalized().dot(n) for n in neighbor_normals]
                num_opposite = sum(1 for d in dot_products if d < 0)
                if num_opposite > len(neighbor_normals) / 2:
                    faces_to_flip.append(f)
            if not faces_to_flip:
                break
            for f in bm.faces:
                f.select = False
            for f in faces_to_flip:
                f.select = True
            bmesh.update_edit_mesh(obj.data, loop_triangles=False, destructive=False)
            bpy.ops.mesh.flip_normals()
            total_flipped += len(faces_to_flip)
        # Now recalculate outside
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.object.mode_set(mode='OBJECT')
        self.report({'INFO'}, f'Hybrid Flip: {total_flipped} faces flipped, then recalculated outside')
        return {'FINISHED'}

class FLIPPEN_OT_ao_flip(bpy.types.Operator):
    bl_idname = 'object.flippen_ao_flip'
    bl_label = 'AO Flip'
    bl_description = 'Flip faces with low ambient occlusion (likely inward)'

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'WARNING'}, 'No active mesh object')
            return {'CANCELLED'}
        if obj.mode != 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')
        import bmesh
        bm = bmesh.from_edit_mesh(obj.data)
        bm.faces.ensure_lookup_table()
        # Use AO: For each face, sample AO by casting rays from the face center along the normal
        from mathutils import Vector
        depsgraph = context.evaluated_depsgraph_get()
        obj_eval = obj.evaluated_get(depsgraph)
        threshold = 0.1  # AO threshold (tweak as needed)
        flipped_count = 0
        for f in bm.faces:
            face_center = f.calc_center_median()
            normal = f.normal.normalized()
            ray_origin = obj.matrix_world @ (face_center + normal * 0.001)
            ray_dir = obj.matrix_world.to_3x3() @ normal
            hit, loc, norm, idx, obj_, mat = context.scene.ray_cast(
                depsgraph, ray_origin, ray_dir, distance=0.5)
            if hit:
                # If the ray hits something very close, it's likely occluded (inward)
                if (loc - ray_origin).length < threshold:
                    f.normal_flip()
                    flipped_count += 1
        bmesh.update_edit_mesh(obj.data, loop_triangles=False, destructive=False)
        bpy.ops.object.mode_set(mode='OBJECT')
        self.report({'INFO'}, f'AO Flip: {flipped_count} faces flipped (low AO)')
        return {'FINISHED'}

class FLIPPEN_PT_panel(bpy.types.Panel):
    bl_label = 'flippen Tools'
    bl_idname = 'FLIPPEN_PT_panel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'flippen'

    def draw(self, context):
        layout = self.layout
        layout.prop(context.window_manager, 'flippen_param')
        layout.operator('object.flippen', text='Flip', icon='MODIFIER')
        layout.prop(context.window_manager, 'flippen_max_passes')
        layout.operator('object.flippen_persistent', text='Persistent Flip', icon='LOOP_FORWARDS')
        layout.separator()
        layout.label(text='Hybrid:')
        layout.operator('object.flippen_hybrid_flip', text='Hybrid Flip', icon='MODIFIER')
        layout.separator()
        layout.label(text='AO Analysis:')
        layout.operator('object.flippen_ao_flip', text='AO Flip', icon='SHADING_RENDERED')
        layout.separator()
        layout.label(text='Exterior Heuristic:')
        layout.operator('object.flippen_exhe', text='Exterior Heuristic Flip', icon='SNAP_FACE')
        layout.separator()
        layout.label(text='Flood Fill:')
        layout.operator('object.flippen_flood_flip', text='Flood Flip', icon='FACESEL')
        layout.separator()
        layout.label(text='Manual Align:')
        layout.operator('object.flippen_manual_align_run', text='Run Manual Align', icon='CHECKMARK')
        layout.label(text='1. Enter Edit Mode (Face Select)')
        layout.label(text='2. Select an outside face')
        layout.label(text='3. Click Run Manual Align')

class flippen(bpy.types.Operator):
    bl_idname = 'object.flippen'
    bl_label = 'flippen'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        param = context.window_manager.flippen_param
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
                if param == '0':
                    # Neighbor Consistency Check: Flip only faces whose normal is opposite to the majority of their neighbors
                    import bmesh
                    bm = bmesh.from_edit_mesh(obj.data)
                    bm.faces.ensure_lookup_table()
                    faces_to_flip = []
                    for f in bm.faces:
                        neighbor_normals = []
                        for loop in f.loops:
                            edge = loop.edge
                            for linked_face in edge.link_faces:
                                if linked_face != f:
                                    neighbor_normals.append(linked_face.normal.normalized())
                        if not neighbor_normals:
                            continue
                        dot_products = [f.normal.normalized().dot(n) for n in neighbor_normals]
                        num_opposite = sum(1 for d in dot_products if d < 0)
                        if num_opposite > len(neighbor_normals) / 2:
                            faces_to_flip.append(f)
                    bpy.ops.mesh.select_all(action='DESELECT')
                    for f in bm.faces:
                        f.select = False
                    for f in faces_to_flip:
                        f.select = True
                    bmesh.update_edit_mesh(obj.data, loop_triangles=False, destructive=False)
                    bpy.ops.mesh.flip_normals()
                elif param == '1':
                    bpy.ops.mesh.select_all(action='SELECT')
                    bpy.ops.mesh.normals_make_consistent(inside=False)
                elif param == '2':
                    bpy.ops.mesh.select_all(action='SELECT')
                    bpy.ops.mesh.normals_make_consistent(inside=False)
                    bpy.ops.mesh.flip_normals()
                bpy.ops.object.mode_set(mode='OBJECT')
                log(obj.name + ' - operation complete!')
            progress += 1
            wm.progress_update(progress)
        wm.progress_end()
        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator(flippen.bl_idname, icon='MESH_CUBE')

def register():
    bpy.utils.register_class(flippen_preferences)
    bpy.utils.register_class(flippen)
    bpy.utils.register_class(FLIPPEN_OT_persistent)
    bpy.utils.register_class(FLIPPEN_OT_manual_align_run)
    bpy.utils.register_class(FLIPPEN_OT_exhe)
    bpy.utils.register_class(FLIPPEN_OT_flood_flip)
    bpy.utils.register_class(FLIPPEN_OT_hybrid_flip)
    bpy.utils.register_class(FLIPPEN_OT_ao_flip)
    bpy.utils.register_class(FLIPPEN_PT_panel)
    bpy.types.VIEW3D_MT_object.append(menu_func)
    bpy.types.WindowManager.flippen_param = bpy.props.EnumProperty(
        items=[('0', 'Flip Normals', 'Flip Normals'),
               ('1', 'Make Normals Consistent', 'Make Normals Consistent'),
               ('2', 'Make Normals Consistent next Flip Normals', 'Make Normals Consistent next Flip Normals')],
        name='Mode',
        default='0'
    )
    bpy.types.WindowManager.flippen_max_passes = bpy.props.IntProperty(
        name='Max Passes',
        description='Maximum number of passes for Persistent Flip',
        default=5, min=1, max=20
    )

def unregister():
    bpy.types.VIEW3D_MT_object.remove(menu_func)
    bpy.utils.unregister_class(flippen)
    bpy.utils.unregister_class(flippen_preferences)
    bpy.utils.unregister_class(FLIPPEN_OT_persistent)
    bpy.utils.unregister_class(FLIPPEN_OT_manual_align_run)
    bpy.utils.unregister_class(FLIPPEN_OT_exhe)
    bpy.utils.unregister_class(FLIPPEN_OT_flood_flip)
    bpy.utils.unregister_class(FLIPPEN_OT_hybrid_flip)
    bpy.utils.unregister_class(FLIPPEN_OT_ao_flip)
    bpy.utils.unregister_class(FLIPPEN_PT_panel)
    del bpy.types.WindowManager.flippen_param
    del bpy.types.WindowManager.flippen_max_passes 