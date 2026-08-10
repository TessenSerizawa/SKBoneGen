import bpy

from .op_bone_gen import SKBONEGEN_OT_bone_gen


class VIEW3D_PT_SkBoneGenPanel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_SkBoneGenPanel"
    bl_label = "SKBoneGen"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Edit'

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == 'MESH' and context.mode == 'EDIT_MESH'

    def draw(self, context):
        layout = self.layout
        layout.operator(SKBONEGEN_OT_bone_gen.bl_idname, text="Gen", icon='BONE_DATA')


def menu_func(self, context):
    self.layout.separator()
    self.layout.operator(SKBONEGEN_OT_bone_gen.bl_idname, text="SKBoneGen", icon='BONE_DATA')
