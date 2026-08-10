import bmesh
import bpy
from mathutils import Vector

# 長さがこれ未満のボーンはBlenderに自動削除されるため生成しない
MIN_BONE_LENGTH = 1e-5


class SKBONEGEN_OT_bone_gen(bpy.types.Operator):
    bl_idname = "bone.skbonegen"
    bl_label = "頂点に沿ってボーンを生成"
    bl_description = "選択した頂点に沿ってボーンを生成します（クリックした順番が使われます）"
    bl_options = {'REGISTER', 'UNDO'}

    bone_name: bpy.props.StringProperty(
        name="BoneName",
        description="ボーンの名前",
        default="SK_bone",
    )

    bone_num: bpy.props.IntProperty(
        name="BoneNum",
        description="ボーンの番号",
        default=1,
        min=0,
    )

    use_connect: bpy.props.BoolProperty(
        name="接続",
        description="ボーンを親子接続する",
        default=True,
    )

    align_roll: bpy.props.BoolProperty(
        name="ロールを法線に合わせる",
        description="頂点法線を使ってボーンのロールを揃える",
        default=True,
    )

    use_world_space: bpy.props.BoolProperty(
        name="トランスフォームを考慮",
        description="メッシュのトランスフォームを適用していなくても位置がズレないようにする",
        default=True,
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == 'MESH' and obj.mode == 'EDIT'

    # ------------------------------------------------------------------
    # 頂点の取得
    # ------------------------------------------------------------------
    def _gather_verts(self, obj):
        """選択履歴の順に (座標, 法線) を返す。bmeshはfree()しないこと。"""
        bm = bmesh.from_edit_mesh(obj.data)
        bm.verts.ensure_lookup_table()

        if self.use_world_space:
            mat = obj.matrix_world
            # 法線用の行列（非一様スケール対策）
            nmat = mat.to_3x3().inverted_safe().transposed()
        else:
            mat = None
            nmat = None

        coords = []
        normals = []
        for elem in bm.select_history:
            if not isinstance(elem, bmesh.types.BMVert) or not elem.select:
                continue
            co = elem.co.copy()
            no = elem.normal.copy()
            if mat is not None:
                co = mat @ co
                no = (nmat @ no).normalized()
            coords.append(co)
            normals.append(no)

        # bm.free() はしない（from_edit_mesh のbmeshはBlenderの所有物）
        return coords, normals

    # ------------------------------------------------------------------
    def execute(self, context):
        obj = context.active_object

        coords, normals = self._gather_verts(obj)

        if len(coords) < 2:
            self.report(
                {'ERROR'},
                "頂点の選択履歴が2つ未満です。頂点選択モードで、生成したい順に1つずつクリックしてください",
            )
            return {'CANCELLED'}

        view_layer = context.view_layer
        prev_active = view_layer.objects.active
        prev_selected = list(context.selected_objects)
        prev_mode = obj.mode

        # 一度オブジェクトモードへ（編集モード中にアクティブを切り替えない）
        bpy.ops.object.mode_set(mode='OBJECT')

        # ------------------------------ アーマチュア生成
        armature = bpy.data.armatures.new(name="BoneGen")
        armature_obj = bpy.data.objects.new("BoneGen", armature)
        context.collection.objects.link(armature_obj)

        if not self.use_world_space:
            # ローカル座標で作った場合はメッシュと同じ変換を持たせる
            armature_obj.matrix_world = obj.matrix_world.copy()

        for o in context.selected_objects:
            o.select_set(False)
        armature_obj.select_set(True)
        view_layer.objects.active = armature_obj

        bpy.ops.object.mode_set(mode='EDIT')

        edit_bones = armature.edit_bones
        prev_bone = None
        created = 0
        skipped = 0

        for i in range(len(coords) - 1):
            head = coords[i]
            tail = coords[i + 1]

            if (tail - head).length < MIN_BONE_LENGTH:
                skipped += 1
                continue

            bone = edit_bones.new(f"{self.bone_name}_{self.bone_num}_{i + 1}")
            bone.head = head
            bone.tail = tail

            if self.align_roll:
                # ボーン方向と平行な法線ではalign_rollが不定になるため除外
                axis = (tail - head).normalized()
                roll_vec = normals[i] - axis * normals[i].dot(axis)
                if roll_vec.length > 1e-6:
                    bone.align_roll(roll_vec.normalized())

            if prev_bone is not None:
                bone.parent = prev_bone
                bone.use_connect = self.use_connect

            prev_bone = bone
            created += 1

        bpy.ops.object.mode_set(mode='OBJECT')

        # ------------------------------ 元の状態に復帰
        armature_obj.select_set(False)
        for o in prev_selected:
            if o.name in view_layer.objects:
                o.select_set(True)
        if prev_active is not None and prev_active.name in view_layer.objects:
            view_layer.objects.active = prev_active
            if prev_mode == 'EDIT':
                bpy.ops.object.mode_set(mode='EDIT')

        if created == 0:
            self.report({'ERROR'}, "有効なボーンを生成できませんでした（頂点が重複しています）")
            return {'CANCELLED'}

        if skipped:
            self.report({'WARNING'}, f"{created}本のボーンを生成しました（{skipped}本は長さ0のためスキップ）")
        else:
            self.report({'INFO'}, f"{created}本のボーンを生成しました")

        return {'FINISHED'}


# 旧クラス名でも参照できるようにエイリアスを残す
SkBoneGenOperator = SKBONEGEN_OT_bone_gen
