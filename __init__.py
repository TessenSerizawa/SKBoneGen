import bpy

from .op_bone_gen import SKBONEGEN_OT_bone_gen
from .panel import VIEW3D_PT_SkBoneGenPanel, menu_func

ADDON_NAME = "SK Bone Generator"

# 拡張機能(blender_manifest.toml)として入れる場合、bl_info は無視される。
# 4.1以前のレガシーアドオンとしても入れられるように残してある。
bl_info = {
    "name": ADDON_NAME,
    "author": "Re7U6",
    "version": (1, 1, 0),
    "blender": (3, 6, 0),
    "location": "View 3D > Sidebar > Edit Tab / Edit Mode Context Menu",
    "description": "スカートのボーンの生成を楽にするアドオン",
    "support": "COMMUNITY",
    "category": "Rigging",
}

classes = (
    SKBONEGEN_OT_bone_gen,
    VIEW3D_PT_SkBoneGenPanel,
)


def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.VIEW3D_MT_edit_mesh_context_menu.append(menu_func)
    print(f"アドオン『{ADDON_NAME}』が有効化されました")


def unregister():
    bpy.types.VIEW3D_MT_edit_mesh_context_menu.remove(menu_func)
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
    print(f"アドオン『{ADDON_NAME}』が無効化されました")


if __name__ == "__main__":
    register()
