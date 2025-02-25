import bpy
import os
import re
from pathlib import Path
from bpy.types import Operator, AddonPreferences
import math

bl_info = {
    "name": "SyncTools Pro",
    "blender": (4, 2, 0),
    "category": "Import-Export",
    "version": (2, 1, 2),
    "author": "475519905",
    "description": "A plugin to import (Copy) and export (Paste) OBJ files with customizable options",
    "doc_url": "https://space.bilibili.com/34368968",
    "location": "View3D > Sidebar > SyncTools",
    "warning": "",
    "support": "COMMUNITY",
}

# 导入快捷键管理模块
import rna_keymap_ui

addon_keymaps = []  # 全局变量，用于存储快捷键映射

def parse_shortcut(shortcut):
    """
    解析快捷键字符串，例如 'CTRL_SHIFT_C'，返回 type 和修饰键参数。
    """
    parts = shortcut.upper().split("_")
    modifiers = {"ctrl": False, "shift": False, "alt": False, "oskey": False}
    key = None

    for part in parts:
        if part == "CTRL":
            modifiers["ctrl"] = True
        elif part == "SHIFT":
            modifiers["shift"] = True
        elif part == "ALT":
            modifiers["alt"] = True
        elif part == "OSKEY":
            modifiers["oskey"] = True
        else:
            key = part  # 假设最后的部分是按键本身
    if key is None:
        raise ValueError(f"Invalid shortcut: {shortcut}")

    # 检查按键是否在允许的按键列表中
    allowed_keys = (
        'LEFTMOUSE', 'MIDDLEMOUSE', 'RIGHTMOUSE', 'BUTTON4MOUSE', 'BUTTON5MOUSE',
        'BUTTON6MOUSE', 'BUTTON7MOUSE', 'PEN', 'ERASER', 'MOUSEMOVE',
        'INBETWEEN_MOUSEMOVE', 'TRACKPADPAN', 'TRACKPADZOOM', 'MOUSEROTATE',
        'MOUSESMARTZOOM', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE', 'WHEELINMOUSE',
        'WHEELOUTMOUSE', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J',
        'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W',
        'X', 'Y', 'Z', 'ZERO', 'ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'SIX',
        'SEVEN', 'EIGHT', 'NINE', 'LEFT_CTRL', 'LEFT_ALT', 'LEFT_SHIFT',
        'RIGHT_ALT', 'RIGHT_CTRL', 'RIGHT_SHIFT', 'OSKEY', 'APP', 'GRLESS',
        'ESC', 'TAB', 'RET', 'SPACE', 'LINE_FEED', 'BACK_SPACE', 'DEL',
        'SEMI_COLON', 'PERIOD', 'COMMA', 'QUOTE', 'ACCENT_GRAVE', 'MINUS',
        'PLUS', 'SLASH', 'BACK_SLASH', 'EQUAL', 'LEFT_BRACKET', 'RIGHT_BRACKET',
        'LEFT_ARROW', 'DOWN_ARROW', 'RIGHT_ARROW', 'UP_ARROW',
        'NUMPAD_2', 'NUMPAD_4', 'NUMPAD_6', 'NUMPAD_8', 'NUMPAD_1', 'NUMPAD_3',
        'NUMPAD_5', 'NUMPAD_7', 'NUMPAD_9', 'NUMPAD_PERIOD', 'NUMPAD_SLASH',
        'NUMPAD_ASTERIX', 'NUMPAD_0', 'NUMPAD_MINUS', 'NUMPAD_ENTER',
        'NUMPAD_PLUS', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8',
        'F9', 'F10', 'F11', 'F12', 'F13', 'F14', 'F15', 'F16', 'F17',
        'F18', 'F19', 'F20', 'F21', 'F22', 'F23', 'F24', 'PAUSE', 'INSERT',
        'HOME', 'PAGE_UP', 'PAGE_DOWN', 'END', 'MEDIA_PLAY', 'MEDIA_STOP',
        'MEDIA_FIRST', 'MEDIA_LAST', 'TEXTINPUT', 'WINDOW_DEACTIVATE',
        'TIMER', 'TIMER0', 'TIMER1', 'TIMER2', 'TIMER_JOBS', 'TIMER_AUTOSAVE',
        'TIMER_REPORT', 'TIMERREGION', 'NDOF_MOTION', 'NDOF_BUTTON_MENU',
        'NDOF_BUTTON_FIT', 'NDOF_BUTTON_TOP', 'NDOF_BUTTON_BOTTOM',
        'NDOF_BUTTON_LEFT', 'NDOF_BUTTON_RIGHT', 'NDOF_BUTTON_FRONT',
        'NDOF_BUTTON_BACK', 'NDOF_BUTTON_ISO1', 'NDOF_BUTTON_ISO2',
        'NDOF_BUTTON_ROLL_CW', 'NDOF_BUTTON_ROLL_CCW', 'NDOF_BUTTON_SPIN_CW',
        'NDOF_BUTTON_SPIN_CCW', 'NDOF_BUTTON_TILT_CW', 'NDOF_BUTTON_TILT_CCW',
        'NDOF_BUTTON_ROTATE', 'NDOF_BUTTON_PANZOOM', 'NDOF_BUTTON_DOMINANT',
        'NDOF_BUTTON_PLUS', 'NDOF_BUTTON_MINUS', 'NDOF_BUTTON_V1',
        'NDOF_BUTTON_V2', 'NDOF_BUTTON_V3', 'NDOF_BUTTON_1',
        'NDOF_BUTTON_2', 'NDOF_BUTTON_3', 'NDOF_BUTTON_4',
        'NDOF_BUTTON_5', 'NDOF_BUTTON_6', 'NDOF_BUTTON_7',
        'NDOF_BUTTON_8', 'NDOF_BUTTON_9', 'NDOF_BUTTON_10', 'NDOF_BUTTON_A',
        'NDOF_BUTTON_B', 'NDOF_BUTTON_C', 'ACTIONZONE_AREA',
        'ACTIONZONE_REGION', 'ACTIONZONE_FULLSCREEN', 'XR_ACTION'
    )

    if key not in allowed_keys:
        raise ValueError(f"无效的按键类型: {key}")

    return key, modifiers


def register_keymaps():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon

    if kc:
        prefs = bpy.context.preferences.addons[__name__].preferences

        # 根据用户选择的快捷键风格设置不同的快捷键
        for space_type in ['EMPTY', 'VIEW_3D', 'NODE_EDITOR']:
            km = kc.keymaps.new(name='Object Mode', space_type=space_type)
            
            if prefs.clipboard_keymap == '0':
                # 标准快捷键模式
                kmi_copy = km.keymap_items.new(
                    "idm.export_obj",
                    type='C',
                    value='PRESS',
                    ctrl=True,
                    shift=True
                )
                
                kmi_paste = km.keymap_items.new(
                    "idm.import_obj",
                    type='V',
                    value='PRESS',
                    ctrl=True,
                    shift=True
                )
                
                kmi_octane = km.keymap_items.new(
                    "idm.import_octane_material.importx",
                    type='M',
                    value='PRESS',
                    ctrl=True,
                    shift=True
                )
                
                # 添加sync_pypreference_check2的快捷键
                kmi_sync = km.keymap_items.new(
                    "preferences.sync_pypreference_toggle",  # 需要创建新的operator
                    type='R',  # 使用R键
                    value='PRESS',
                    ctrl=True,
                    shift=True
                )
            else:
                # 鼠标拖拽模式
                kmi_copy = km.keymap_items.new(
                    "idm.export_obj",
                    type='LEFTMOUSE',
                    value='CLICK_DRAG',
                    ctrl=True,
                    alt=True
                )
                
                kmi_paste = km.keymap_items.new(
                    "idm.import_obj",
                    type='LEFTMOUSE',
                    value='CLICK_DRAG',
                    ctrl=True,
                    shift=True
                )
                
                kmi_octane = km.keymap_items.new(
                    "idm.import_octane_material.importx",
                    type='LEFTMOUSE',
                    value='CLICK_DRAG',
                    ctrl=True,
                    shift=True,
                    alt=True
                )
                
                # 添加sync_pypreference_check2的快捷键（鼠标模式）
                kmi_sync = km.keymap_items.new(
                    "preferences.sync_pypreference_toggle",
                    type='RIGHTMOUSE',
                    value='CLICK',
                    ctrl=True,
                    shift=True,
                    alt=True
                )
            
            # 添加到快捷键列表
            addon_keymaps.append((km, kmi_copy))
            addon_keymaps.append((km, kmi_paste))
            addon_keymaps.append((km, kmi_octane))
            addon_keymaps.append((km, kmi_sync))


def unregister_keymaps():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        for km, kmi in addon_keymaps:
            km.keymap_items.remove(kmi)
    addon_keymaps.clear()


class IDToolsPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__
    # Add shortcut style selection
    clipboard_keymap: bpy.props.EnumProperty(
        items=[
            ('0', 'Standard Shortcut (Ctrl+Shift+V)', 'Use standard keyboard shortcut'),
            ('1', 'Mouse Drag (Ctrl+Alt+Drag)', 'Use mouse drag operation')
        ],
        name="Shortcut Style",
        description="Choose shortcut trigger method",
        default='0',
        update=lambda self, context: update_keymaps(self)
    )

    # 新增勾选项，映射到 PYPREFERENCE_CHECK2
    sync_pypreference_check2: bpy.props.BoolProperty(
        name="Identify Renderer",
        description="Identify renderer settings",
        default=True,
        update=lambda self, context: self.sync_preference_file(),
    )

    # 导入预设选择
    import_axis_preset: bpy.props.EnumProperty(
        name="Import Axis Preset",
        description="Common 3D software axis presets for importing",
        items=[
            ('C4D', "Cinema 4D", "Forward: -Z, Up: Y"),
            ('BLENDER', "Blender", "Forward: Z, Up: Y"),
            ('3DSMAX', "3ds Max", "Forward: -Y, Up: Z"),
            ('MAYA', "Maya", "Forward: Z, Up: Y"),
            ('HOUDINI', "Houdini", "Forward: Z, Up: Y"),
            ('SP', "Substance Painter", "Forward: Z, Up: Y"),
            ('RHINO', "Rhino", "Forward: -Z, Up: Y"),
            ('UE', "Unreal Engine", "Forward: X, Up: Z"),
            ('UNITY', "Unity", "Forward: Z, Up: Y"),
            ('MD', "Marvelous Designer", "Forward: Z, Up: Y"),
        ],
        default='C4D',
        update=lambda self, context: self.update_import_preset(context)
    )

    # 导出预设选择
    export_axis_preset: bpy.props.EnumProperty(
        name="Export Axis Preset",
        description="Common 3D software axis presets for exporting",
        items=[
            ('C4D', "Cinema 4D", "Forward: -Z, Up: Y"),
            ('BLENDER', "Blender", "Forward: Z, Up: Y"),
            ('3DSMAX', "3ds Max", "Forward: -Y, Up: Z"),
            ('MAYA', "Maya", "Forward: Z, Up: Y"),
            ('HOUDINI', "Houdini", "Forward: Z, Up: Y"),
            ('SP', "Substance Painter", "Forward: Z, Up: Y"),
            ('RHINO', "Rhino", "Forward: -Z, Up: Y"),
            ('UE', "Unreal Engine", "Forward: X, Up: Z"),
            ('UNITY', "Unity", "Forward: Z, Up: Y"),
            ('MD', "Marvelous Designer", "Forward: Z, Up: Y"),
        ],
        default='C4D',
        update=lambda self, context: self.update_export_preset(context)
    )

    # 导入轴向设置
    import_axis_forward: bpy.props.EnumProperty(
        name="Import Forward Axis",
        description="Forward axis for importing",
        items=[
            ('X', "X Forward", ""),
            ('Y', "Y Forward", ""),
            ('Z', "Z Forward", ""),
            ('-X', "-X Forward", ""),
            ('-Y', "-Y Forward", ""),
            ('-Z', "-Z Forward", "Default"),
        ],
        default='-Z',
    )
    
    import_axis_up: bpy.props.EnumProperty(
        name="Import Up Axis",
        description="Up axis for importing",
        items=[
            ('X', "X Up", ""),
            ('Y', "Y Up", "Default"),
            ('Z', "Z Up", ""),
            ('-X', "-X Up", ""),
            ('-Y', "-Y Up", ""),
            ('-Z', "-Z Up", ""),
        ],
        default='Y',
    )

    # 导出轴向设置
    export_axis_forward: bpy.props.EnumProperty(
        name="Export Forward Axis",
        description="Forward axis for exporting",
        items=[
            ('X', "X Forward", ""),
            ('Y', "Y Forward", ""),
            ('Z', "Z Forward", ""),
            ('-X', "-X Forward", ""),
            ('-Y', "-Y Forward", ""),
            ('-Z', "-Z Forward", "Default"),
        ],
        default='-Z',
    )
    
    export_axis_up: bpy.props.EnumProperty(
        name="Export Up Axis",
        description="Up axis for exporting",
        items=[
            ('X', "X Up", ""),
            ('Y', "Y Up", "Default"),
            ('Z', "Z Up", ""),
            ('-X', "-X Up", ""),
            ('-Y', "-Y Up", ""),
            ('-Z', "-Z Up", ""),
        ],
        default='Y',
    )

    # 添加独立的缩放比例滑块
    import_global_scale: bpy.props.FloatProperty(
        name="Import Global Scale",
        description="Scale all imported data",
        default=1,
        min=0.00001,
        max=1000000.0,
    )

    export_global_scale: bpy.props.FloatProperty(
        name="Export Global Scale",
        description="Scale all exported data",
        default=1,
        min=0.000001,
        max=1000000.0,
    )
    # Add shortcut key properties
    copy_key: bpy.props.StringProperty(
        name="Copy Shortcut", 
        description="Shortcut key for copying (importing), e.g. CTRL_SHIFT_C",
        default="CTRL_SHIFT_V",
        update=lambda self, context: self.update_keymaps(),
    )
    paste_key: bpy.props.StringProperty(
        name="Paste Shortcut",
        description="Shortcut key for pasting (exporting), e.g. CTRL_SHIFT_V", 
        default="CTRL_SHIFT_C",
        update=lambda self, context: self.update_keymaps(),
    )

    def sync_preference_file(self):
        # 更新 Preference.txt 中的 PYPREFERENCE_CHECK2
        documents_dir = os.path.join(os.path.expanduser("~"), "Documents")
        preference_file = os.path.join(documents_dir, "cache", "Preference.txt")

        if os.path.exists(preference_file):
            with open(preference_file, 'r') as file:
                data = file.readlines()

            # 修改 PYPREFERENCE_CHECK2 行
            for i, line in enumerate(data):
                if line.startswith("PYPREFERENCE_CHECK2"):
                    data[i] = f"PYPREFERENCE_CHECK2: {'True' if self.sync_pypreference_check2 else 'False'}\n"
                    break
            else:
                # 如果没有找到 PYPREFERENCE_CHECK2，则添加一行
                data.append(f"PYPREFERENCE_CHECK2: {'True' if self.sync_pypreference_check2 else 'False'}\n")

            # 写回文件
            with open(preference_file, 'w') as file:
                file.writelines(data)

    # 导入选项
    def get_default_light_setting():
        # 获取 Blender 版本
        version = bpy.app.version

        # 如果是 4.2.x 版本返回 True，4.3 及以上返回 False
        if version[0] == 4:
            if version[1] == 2:
                return True
            elif version[1] >= 3:
                return False
        return True  # 其他版本默认返回 True

    import_lights: bpy.props.BoolProperty(
        name="Import Lights",
        description="Import lights",
        default=get_default_light_setting(),
    )
    import_cameras: bpy.props.BoolProperty(
        name="Import Cameras",
        description="Import cameras",
        default=True,
    )
    import_materials: bpy.props.BoolProperty(
        name="Import Materials",
        description="Import materials",
        default=True,
    )
    import_meshes: bpy.props.BoolProperty(
        name="Import Meshes",
        description="Import meshes",
        default=True,
    )
    import_armatures: bpy.props.BoolProperty(
        name="Import Armatures",
        description="Import armatures (skeletons)",
        default=True,
    )
    import_bake_animation: bpy.props.BoolProperty(
        name="Import Baked Animation",
        description="Import baked keyframe animation",
        default=True,
    )

    # 导出选项
    export_lights: bpy.props.BoolProperty(
        name="Export Lights",
        description="Export lights",
        default=get_default_light_setting(),
    )
    export_cameras: bpy.props.BoolProperty(
        name="Export Cameras",
        description="Export cameras",
        default=True,
    )
    export_materials: bpy.props.BoolProperty(
        name="Export Materials",
        description="Export materials",
        default=True,
    )
    export_meshes: bpy.props.BoolProperty(
        name="Export Meshes",
        description="Export meshes",
        default=True,
    )
    export_armatures: bpy.props.BoolProperty(
        name="Export Armatures",
        description="Export armatures (skeletons)",
        default=True,
    )
    export_bake_animation: bpy.props.BoolProperty(
        name="Export Baked Animation",
        description="Export baked keyframe animation",
        default=True,
    )

    # 添加旋转属性
    import_rotation_x: bpy.props.FloatProperty(
        name="Rotation X",
        description="Import rotation around X axis in degrees",
        default=0,
        min=-360,
        max=360
    )
    import_rotation_y: bpy.props.FloatProperty(
        name="Rotation Y",
        description="Import rotation around Y axis in degrees",
        default=0,
        min=-360,
        max=360
    )
    import_rotation_z: bpy.props.FloatProperty(
        name="Rotation Z",
        description="Import rotation around Z axis in degrees",
        default=0,
        min=-360,
        max=360
    )

    export_rotation_x: bpy.props.FloatProperty(
        name="Rotation X",
        description="Export rotation around X axis in degrees",
        default=0,
        min=-360,
        max=360
    )
    export_rotation_y: bpy.props.FloatProperty(
        name="Rotation Y",
        description="Export rotation around Y axis in degrees",
        default=0,
        min=-360,
        max=360
    )
    export_rotation_z: bpy.props.FloatProperty(
        name="Rotation Z",
        description="Export rotation around Z axis in degrees",
        default=0,
        min=-360,
        max=360
    )

    def update_keymaps(self):
        # 注销现有快捷键
        unregister_keymaps()
        # 重新注册快捷键
        register_keymaps()

    def get_preset_settings(self, preset_name):
        """获取预设的设置"""
        presets = {
            'C4D': {
                'forward': '-Z',
                'up': 'Y',
                'scale_import': 1.0,
                'scale_export': 1.0,
                'rotation_import': (0, 0, 0),  # 导入旋转角度
                'rotation_export': (0, 0, 0)   # 导出旋转角度
            },
            'BLENDER': {
                'forward': 'Z',
                'up': 'Y',
                'scale_import': 1.0,
                'scale_export': 1.0,
                'rotation_import': (0, 0, 0),
                'rotation_export': (0, 0, 0)
            },
            '3DSMAX': {
                'forward': '-Y',
                'up': 'Z',
                'scale_import': 50.0,
                'scale_export': 0.01,
                'rotation_import': (0, 0, -90),  # 导入时需要绕X轴旋转-90度
                'rotation_export': (0, 0, 0)   # 导出时需要绕X轴旋转-90度
            },
            'MAYA': {
                'forward': 'Z',
                'up': 'Y',
                'scale_import': 100.0,
                'scale_export': 0.01,
                'rotation_import': (0, 0, 0),
                'rotation_export': (0, 0, 0)
            },
            'HOUDINI': {
                'forward': 'Z',
                'up': 'Y',
                'scale_import': 200.0,
                'scale_export': 0.005,
                'rotation_import': (0, 0, 0),
                'rotation_export': (0, 0, 0)
            },
            'SP': {
                'forward': 'Z',
                'up': 'Y',
                'scale_import': 1.0,
                'scale_export': 1.0,
                'rotation_import': (0, 0, 0),
                'rotation_export': (0, 0, 0)
            },
            'RHINO': {
                'forward': '-Z',
                'up': 'Y',
                'scale_import': 1.0,
                'scale_export': 1.0,
                'rotation_import': (0, 0, 0),
                'rotation_export': (0, 0, 0)
            },
            'UE': {
                'forward': 'X',
                'up': 'Z',
                'scale_import': 1.0,
                'scale_export': 1.0,
                'rotation_import': (-90, 0, -90),  # UE需要特殊的旋转
                'rotation_export': (-90, 0, -90)
            },
            'UNITY': {
                'forward': 'Z',
                'up': 'Y',
                'scale_import': 1.0,
                'scale_export': 1.0,
                'rotation_import': (0, 0, 0),
                'rotation_export': (0, 0, 0)
            },
            'MD': {
                'forward': 'Z',
                'up': 'Y',
                'scale_import': 1.0,
                'scale_export': 1.0,
                'rotation_import': (0, 0, 0),
                'rotation_export': (0, 0, 0)
            },
        }
        return presets.get(preset_name)

    def update_import_preset(self, context):
        """更新导入预设设置"""
        preset = self.get_preset_settings(self.import_axis_preset)
        if preset:
            self.import_axis_forward = preset['forward']
            self.import_axis_up = preset['up']
            self.import_global_scale = preset['scale_import']
            self.import_rotation_x = preset['rotation_import'][0]
            self.import_rotation_y = preset['rotation_import'][1]
            self.import_rotation_z = preset['rotation_import'][2]

    def update_export_preset(self, context):
        """更新导出预设设置"""
        preset = self.get_preset_settings(self.export_axis_preset)
        if preset:
            self.export_axis_forward = preset['forward']
            self.export_axis_up = preset['up']
            self.export_global_scale = preset['scale_export']
            self.export_rotation_x = preset['rotation_export'][0]
            self.export_rotation_y = preset['rotation_export'][1]
            self.export_rotation_z = preset['rotation_export'][2]

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.operator(
            "wm.url_open", 
            text="Documentation",
            icon='HELP'
        ).url = "https://www.yuque.com/shouwangxingkong-0p4w3/ldvruc/qkb24gky94mkgbe4?singleDoc"
        row.operator(
            "wm.url_open",
            text="About Author",
            icon='USER'
        ).url = "https://space.bilibili.com/34368968"

        # Second row buttons
        row = layout.row()
        row.operator(
            "wm.url_open",
            text="Check Updates",
            icon='FILE_REFRESH'
        ).url = "https://www.yuque.com/shouwangxingkong-0p4w3/ldvruc/gmd4pud4fu2vz30z?singleDoc"
        row.operator(
            "wm.url_open", 
            text="Join QQ Group",
            icon='COMMUNITY'
        ).url = "https://qm.qq.com/cgi-bin/qm/qr?k=9KgmVUQMfoGf7g_s-4tSe15oMJ6rbz6b&jump_from=webapi&authKey=hs9XWuCbT1jx9ytpzSsXbJuQCwUc2kXy0gRJfA+qMaVoXTbvhiOKz0dHOnP1+Cvt"

        # Third row button (single)
        row = layout.row()
        row.operator(
            "wm.url_open",
            text="Buy Pro Version",
            icon='FUND'
        ).url = "https://www.bilibili.com/video/BV1GT421k7fi"

        layout.separator()

        layout.label(text="Preference Sync Options:")
        layout.prop(self, "sync_pypreference_check2")

        layout.separator()

        # 快捷键设置 (移到这里)
        layout.label(text="快捷键设置:")
        layout.prop(self, "clipboard_keymap")
        draw_keymap(self, context, layout)

        layout.separator()

        # 添加导入预设选择
        box = layout.box()
        box.label(text="Import Axis Preset:")
        box.prop(self, "import_axis_preset")
        
        # 添加导出预设选择
        box = layout.box()
        box.label(text="Export Axis Preset:")
        box.prop(self, "export_axis_preset")
        
        # 添加说明文本
        if self.import_axis_preset != 'C4D' or self.export_axis_preset != 'C4D':
            box = layout.box()
            box.label(text="Note: Using non-Cinema 4D preset may require axis adjustment", icon='INFO')
            box.label(text=f"Import Scale: {self.import_global_scale:.3f}", icon='IMPORT')
            box.label(text=f"Export Scale: {self.export_global_scale:.3f}", icon='EXPORT')
        
        # 导入轴向和旋转设置
        box = layout.box()
        box.label(text="Import Settings:")
        row = box.row()
        row.prop(self, "import_axis_forward")
        row.prop(self, "import_axis_up")
        box.prop(self, "import_global_scale")
        
        
        # 导入旋转设置
        row = box.row()
        row.prop(self, "import_rotation_x")
        row.prop(self, "import_rotation_y")
        row.prop(self, "import_rotation_z")
        
        # 导出轴向和旋转设置
        box = layout.box()
        box.label(text="Export Settings:")
        row = box.row()
        row.prop(self, "export_axis_forward")
        row.prop(self, "export_axis_up")
        box.prop(self, "export_global_scale")
        
        # 导出旋转设置
        row = box.row()
        row.prop(self, "export_rotation_x")
        row.prop(self, "export_rotation_y")
        row.prop(self, "export_rotation_z")

        layout.separator()

        layout.label(text="Import & Export Options:")
 
        # Lights
        row = layout.row()
        row.prop(self, "import_lights")
        row.prop(self, "export_lights")
        
        # Cameras 
        row = layout.row()
        row.prop(self, "import_cameras")
        row.prop(self, "export_cameras")
        
        # Materials
        row = layout.row()
        row.prop(self, "import_materials")
        row.prop(self, "export_materials")
        
        # Meshes
        row = layout.row()
        row.prop(self, "import_meshes")
        row.prop(self, "export_meshes")
        
        # Armatures
        row = layout.row()
        row.prop(self, "import_armatures")
        row.prop(self, "export_armatures")
           
        # Export Animation (单独一行)
        row = layout.row()
        row.prop(self, "export_bake_animation")
        row.prop(self, "import_bake_animation")
        
        layout.separator()


def get_latest_fbx_file(cache_dir):
    fbx_files = list(Path(cache_dir).glob("*.fbx"))
    if not fbx_files:
        return None

    latest_fbx = max(fbx_files, key=os.path.getmtime)
    return latest_fbx


def import_latest_fbx():
    documents_dir = os.path.join(os.path.expanduser("~"), "Documents")
    cache_dir = os.path.join(documents_dir, "cache")

    if not os.path.exists(cache_dir):
        print(f"文件夹不存在: {cache_dir}")
        return

    latest_fbx = get_latest_fbx_file(cache_dir)

    if latest_fbx is None:
        return

    # 获取用户设置
    prefs = bpy.context.preferences.addons[__name__].preferences

    # 记录导入前的对象列表
    pre_import_objects = set(bpy.context.scene.objects)

    # 导入FBX
    bpy.ops.import_scene.fbx(
        filepath=str(latest_fbx),
        axis_forward=prefs.import_axis_forward,
        axis_up=prefs.import_axis_up,
        global_scale=prefs.import_global_scale
    )

    # 获取新导入的对象
    new_objects = set(bpy.context.scene.objects) - pre_import_objects

    # 应用旋转设置到新导入的对象
    for obj in new_objects:
        # 转换角度为弧度
        rotation_x = math.radians(prefs.import_rotation_x)
        rotation_y = math.radians(prefs.import_rotation_y)
        rotation_z = math.radians(prefs.import_rotation_z)
        
        # 设置旋转
        obj.rotation_euler.x += rotation_x
        obj.rotation_euler.y += rotation_y
        obj.rotation_euler.z += rotation_z
        
        # 应用旋转
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
        obj.select_set(False)

    # 删除不需要的物体类型和动画数据
    for obj in new_objects:  # 只处理新导入的对象
        if (obj.type == 'LIGHT' and not prefs.import_lights) or \
           (obj.type == 'CAMERA' and not prefs.import_cameras) or \
           (obj.type == 'MESH' and not prefs.import_meshes) or \
           (obj.type == 'ARMATURE' and not prefs.import_armatures):
            bpy.data.objects.remove(obj, do_unlink=True)
        elif obj.type in {'MATERIAL', 'MESH'} and not prefs.import_materials:
            for mat in obj.data.materials:
                bpy.data.materials.remove(mat, do_unlink=True)
        
        # 如果禁用了动画导入，只删除新导入对象的动画数据
        if not prefs.import_bake_animation:
            if obj.animation_data:
                obj.animation_data_clear()
            # 如果是骨骼，只清除新导入骨骼的姿势动画
            if obj.type == 'ARMATURE':
                for pbone in obj.pose.bones:
                    if pbone.animation_data:
                        pbone.animation_data_clear()

    # 根据 import_global_scale 按比例缩放新导入的摄像机裁剪起始值
    if prefs.import_cameras:
        for obj in new_objects:
            if obj.type == 'CAMERA':
                base_clip_start = 0.1
                obj.data.clip_start = base_clip_start / prefs.import_global_scale
                print(f"设置摄像机 {obj.name} 的裁剪起始为 {obj.data.clip_start} 米")

    try:
        os.remove(str(latest_fbx))
        print(f"已删除文件: {latest_fbx}")
    except Exception as e:
        print(f"删除文件失败: {e}")


def get_unique_name(name, name_dict):
    """获取唯一的名称，如果重复则添加编号"""
    base_name = re.sub(r'\.\d+$', '', name)
    if base_name not in name_dict:
        name_dict[base_name] = 1
        return base_name
    else:
        unique_name = f"{base_name}.{name_dict[base_name]:03d}"
        name_dict[base_name] += 1
        return unique_name


def write_hierarchy_to_file(obj, level=0, file=None, name_dict=None, selected_objects=None):
    """递归写入选中对象的层级结构到文件并编号"""
    if obj is None or (selected_objects and obj not in selected_objects):
        return

    unique_name = get_unique_name(obj.name, name_dict)
    file.write(' ' * level * 4 + f"{unique_name}\n")

    for child in obj.children:
        write_hierarchy_to_file(child, level + 1, file, name_dict, selected_objects)


def get_export_counter(counter_file):
    """获取当前的导出计数器值"""
    if os.path.exists(counter_file):
        with open(counter_file, 'r') as file:
            try:
                return int(file.read().strip())
            except ValueError:
                return 1
    return 1


def increment_export_counter(counter_file):
    """递增导出计数器值并返回新的计数器值"""
    counter = get_export_counter(counter_file)
    with open(counter_file, 'w') as file:
        counter += 1
        file.write(str(counter))
    return counter


def delete_previous_exports(cache_dir):
    """删除之前的所有导出文件"""
    for filename in os.listdir(cache_dir):
        if filename.startswith("export") and filename.endswith(".fbx"):
            os.remove(os.path.join(cache_dir, filename))
    print("之前的所有导出文件已删除")


def export_fbx_to_cache():
    """导出当前场景为 FBX 文件到 cache 文件夹，并处理计数器和层级文件"""
    documents_dir = os.path.join(os.path.expanduser("~"), "Documents")
    cache_dir = os.path.join(documents_dir, "cache")

    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

    counter_file = os.path.join(cache_dir, "export_counter.txt")
    counter = get_export_counter(counter_file)

    if counter >= 10:
        delete_previous_exports(cache_dir)
        counter = 1

    counter = increment_export_counter(counter_file)
    fbx_filepath = os.path.join(cache_dir, f"export_{counter}.fbx")

    prefs = bpy.context.preferences.addons[__name__].preferences

    # 保存选中的对象
    selected_objects = bpy.context.selected_objects
    active_object = bpy.context.active_object

    # 为选中的对象创建临时副本并应用旋转
    temp_objects = []
    for obj in selected_objects:
        # 创建对象的副本
        temp_obj = obj.copy()
        if obj.data:
            temp_obj.data = obj.data.copy()
        bpy.context.scene.collection.objects.link(temp_obj)
        
        # 应用导出旋转
        rotation_x = math.radians(prefs.export_rotation_x)
        rotation_y = math.radians(prefs.export_rotation_y)
        rotation_z = math.radians(prefs.export_rotation_z)
        
        temp_obj.rotation_euler.x += rotation_x
        temp_obj.rotation_euler.y += rotation_y
        temp_obj.rotation_euler.z += rotation_z
        
        temp_objects.append(temp_obj)
        temp_obj.select_set(True)

    # 取消选择原始对象
    for obj in selected_objects:
        obj.select_set(False)

    # 设置活动对象
    if temp_objects:
        bpy.context.view_layer.objects.active = temp_objects[0]

    # 导出FBX
    object_types = {'EMPTY'}
    if prefs.export_lights:
        object_types.add('LIGHT')
    if prefs.export_cameras:
        object_types.add('CAMERA')
    if prefs.export_meshes:
        object_types.add('MESH')
    if prefs.export_armatures:
        object_types.add('ARMATURE')

    bpy.ops.export_scene.fbx(
        filepath=fbx_filepath,
        axis_forward=prefs.export_axis_forward,
        axis_up=prefs.export_axis_up,
        global_scale=prefs.export_global_scale,
        use_selection=True,
        bake_anim=prefs.export_bake_animation,
        bake_anim_use_all_bones=False,
        bake_anim_force_startend_keying=True,
        bake_anim_step=1.0,
        bake_anim_simplify_factor=1.0,
        object_types=object_types
    )

    # 清理：删除临时对象
    for temp_obj in temp_objects:
        bpy.data.objects.remove(temp_obj, do_unlink=True)

    # 恢复原始选择
    for obj in selected_objects:
        obj.select_set(True)
    if active_object:
        bpy.context.view_layer.objects.active = active_object

    print(f"场景成功导出为: {fbx_filepath}")

    txt_path = os.path.join(cache_dir, "hierarchy.txt")
    name_dict = {}
    selected_objects = bpy.context.selected_objects

    with open(txt_path, 'w') as file:
        for obj in bpy.context.scene.objects:
            write_hierarchy_to_file(obj, file=file, name_dict=name_dict, selected_objects=selected_objects)

    print(f"层级结构已保存到: {txt_path}")


# 定义操作类
class OBJECT_OT_import_obj(bpy.types.Operator):
    """Import object via OBJ file format"""
    bl_idname = "idm.import_obj"
    bl_label = "Copy"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # 获取Preference.txt文件路径
        documents_dir = os.path.join(os.path.expanduser("~"), "Documents")
        preference_file = os.path.join(documents_dir, "cache", "Preference.txt")

        # 检查 Preference.txt 文件是否存在，如果不存在则创建它
        if not os.path.exists(preference_file):
            # 创建包含默认内容的 Preference.txt 文件
            os.makedirs(os.path.dirname(preference_file), exist_ok=True)  # 确保目录存在
            with open(preference_file, 'w', encoding='utf-8') as file:
                file.write("Preference Container Data:\n")
                file.write("SYNC_PREFERENCE_CHECK: True\n")
                file.write("SYNC_PREFERENCE_NUMBER: 10\n")
                file.write("SYNC_PREFERENCE_CHECK2: True\n")
            print(f"已创建文件: {preference_file}，并写入默认内容。")

        # 检查文件是否存在并读取SYNC_PREFERENCE_CHECK2的值
        execute_importx = False
        if os.path.exists(preference_file):
            with open(preference_file, 'r') as file:
                for line in file:
                    if line.startswith("SYNC_PREFERENCE_CHECK2"):
                        # 设置标志，如果值为True，则标志为True
                        execute_importx = "True" in line
                        break
        else:
            print(f"未找到文件: {preference_file}")

        # 执行import_latest_fbx()
        import_latest_fbx()

        # 如果SYNC_PREFERENCE_CHECK2为True，则执行importx
        if execute_importx:
            try:
                bpy.ops.import_octane_material.importx()
                print("SYNC_PREFERENCE_CHECK2为True，执行importx操作")
            except AttributeError:
                print("未找到 'import_octane_material.importx' 操作。请确保相关插件已安装。")

        return {'FINISHED'}


class OBJECT_OT_export_obj(bpy.types.Operator):
    """Export object via OBJ file format."""
    bl_idname = "idm.export_obj"
    bl_label = "Paste"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        export_fbx_to_cache()
        return {'FINISHED'}


# 定义面板类
class OBJECT_PT_fbx_import_export_panel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Object Operations"
    bl_idname = "OBJECT_PT_fbx_import_export"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "SyncTools"

    def draw(self, context):
        layout = self.layout
        layout.label(text="Copy / paste meshes:")  # 在按钮上方添加说明文字
        row = layout.row(align=True)
        row.operator("idm.export_obj", text=" Copy ")
        row.operator("idm.import_obj", text=" Paste ")


# 定义快捷键绘制函数
def draw_keymap(self, context, layout):
    col = layout.box().column()
    col.label(text="Keymap", icon="KEYINGSET")
    km = None
    wm = context.window_manager
    kc = wm.keyconfigs.user

    old_km_name = ""
    get_kmi_l = []

    for km_add, kmi_add in addon_keymaps:
        for km_con in kc.keymaps:
            if km_add.name == km_con.name:
                km = km_con
                break

        for kmi_con in km.keymap_items:
            if kmi_add.idname == kmi_con.idname and kmi_add.name == kmi_con.name:
                get_kmi_l.append((km, kmi_con))

    get_kmi_l = sorted(set(get_kmi_l), key=get_kmi_l.index)

    for km, kmi in get_kmi_l:
        if not km.name == old_km_name:
            col.label(text=str(km.name), icon="DOT")

        col.context_pointer_set("keymap", km)
        rna_keymap_ui.draw_kmi([], kc, km, kmi, col, 0)

        old_km_name = km.name


class PREFERENCES_OT_sync_pypreference_toggle(bpy.types.Operator):
    """Toggle sync_pypreference_check2 setting"""
    bl_idname = "preferences.sync_pypreference_toggle"
    bl_label = "Toggle Sync Preference"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        prefs = context.preferences.addons[__name__].preferences
        # 切换设置
        prefs.sync_pypreference_check2 = not prefs.sync_pypreference_check2
        # 显示当前状态的消息
        self.report({'INFO'}, f"Sync Preference is now {'enabled' if prefs.sync_pypreference_check2 else 'disabled'}")
        return {'FINISHED'}


# 添加顶部菜单类
class VIEW3D_MT_synctools_menu(bpy.types.Menu):
    bl_label = "SyncTools"
    bl_idname = "VIEW3D_MT_synctools_menu"

    def draw(self, context):
        layout = self.layout
        layout.operator("idm.export_obj", text="Copy", icon='COPYDOWN')
        layout.operator("idm.import_obj", text="Paste", icon='PASTEDOWN')
        layout.separator()
        layout.operator("preferences.sync_pypreference_toggle", text="Toggle Sync", icon='FILE_REFRESH')
        layout.separator()
        # 添加打开首选项的选项
        layout.operator("preferences.addon_show", text="Preference", icon='PREFERENCES').module = __name__
        layout.operator("wm.url_open", text="Documentation", icon='HELP').url = "https://www.yuque.com/shouwangxingkong-0p4w3/ldvruc/qkb24gky94mkgbe4?singleDoc"

# 添加菜单到顶部菜单栏的函数
def menu_func(self, context):
    self.layout.menu(VIEW3D_MT_synctools_menu.bl_idname)


# 注册和注销
def register():
    bpy.utils.register_class(IDToolsPreferences)
    bpy.utils.register_class(OBJECT_PT_fbx_import_export_panel)
    bpy.utils.register_class(OBJECT_OT_import_obj)
    bpy.utils.register_class(OBJECT_OT_export_obj)
    bpy.utils.register_class(PREFERENCES_OT_sync_pypreference_toggle)
    bpy.utils.register_class(VIEW3D_MT_synctools_menu)  # 注册菜单类

    # 将菜单添加到顶部菜单栏
    bpy.types.TOPBAR_MT_editor_menus.append(menu_func)

    # 注册快捷键
    register_keymaps()


def unregister():
    # 注销快捷键
    unregister_keymaps()

    # 移除顶部菜单
    bpy.types.TOPBAR_MT_editor_menus.remove(menu_func)

    bpy.utils.unregister_class(VIEW3D_MT_synctools_menu)  # 注销菜单类
    bpy.utils.unregister_class(PREFERENCES_OT_sync_pypreference_toggle)
    bpy.utils.unregister_class(IDToolsPreferences)
    bpy.utils.unregister_class(OBJECT_PT_fbx_import_export_panel)
    bpy.utils.unregister_class(OBJECT_OT_import_obj)
    bpy.utils.unregister_class(OBJECT_OT_export_obj)


if __name__ == "__main__":
    register()
