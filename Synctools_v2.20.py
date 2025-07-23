import bpy
import os
import re
from pathlib import Path
from bpy.types import Operator, AddonPreferences
import math
from . import project_info_io_c4d
import json
import glob
import string
import random

bl_info = {
    "name": "SyncTools Pro",
    "blender": (4, 2, 0),
    "category": "Import-Export",
    "version": (2, 2, 0),
    "author": "475519905",
    "description": "A unified plugin with Standard (FBX) and Bata (ABC) modes for import/export operations",
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
    
    # Mode selection - Add this at the top
    sync_mode: bpy.props.EnumProperty(
        name="Sync Mode",
        description="Choose sync mode",
        items=[
            ('STANDARD', "Standard (FBX)", "Use standard FBX-based sync with full features"),
            ('BATA', "Bata (ABC)", "Use experimental ABC-based sync for geometry transfer"),
        ],
        default='STANDARD',
        update=lambda self, context: self.update_sync_mode(context)
    )
    
    # Add language selection
    interface_language: bpy.props.EnumProperty(
        name="Language",
        description="Choose interface language",
        items=[
            ('en_US', "English", "Use English language"),
            ('zh_HANS', "中文", "使用中文"),
        ],
        default='en_US',
        update=lambda self, context: self.update_language(context)
    )

    def update_sync_mode(self, context):
        """Update sync mode and refresh UI"""
        # Force UI refresh when mode changes
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                for region in area.regions:
                    if region.type == 'UI':
                        region.tag_redraw()

    def update_language(self, context):
        """Update Blender's interface language"""
        prefs = context.preferences
        if self.interface_language == 'zh_HANS':
            prefs.view.language = 'zh_HANS'
            # Update UI strings to Chinese
            self.clipboard_keymap.name = "快捷键风格"
            self.clipboard_keymap.description = "选择快捷键触发方式"
            self.clipboard_keymap.items[0][2] = "使用标准键盘快捷键"
            self.clipboard_keymap.items[1][2] = "使用鼠标拖拽操作"
            
            # Update import/export preset strings
            self.import_export_preset.name = "预设"
            self.import_export_preset.description = "选择导入导出选项预设"
            self.import_export_preset.items[0][2] = "选择所有选项"
            self.import_export_preset.items[1][2] = "仅选择模型相关选项"
            self.import_export_preset.items[2][2] = "选择常用选项"
            
            # Update axis preset strings
            self.import_axis_preset.name = "导入轴向预设"
            self.export_axis_preset.name = "导出轴向预设"
            
            # Update property names
            self.import_lights.name = "导入灯光"
            self.export_lights.name = "导出灯光"
            self.import_cameras.name = "导入相机"
            self.export_cameras.name = "导出相机"
            self.import_materials.name = "导入材质"
            self.export_materials.name = "导出材质"
            self.import_meshes.name = "导入网格"
            self.export_meshes.name = "导出网格"
            self.import_armatures.name = "导入骨骼"
            self.export_armatures.name = "导出骨骼"
            self.import_bake_animation.name = "导入烘焙动画"
            self.export_bake_animation.name = "导出烘焙动画"
            
            # Update scale and rotation properties
            self.import_global_scale.name = "导入全局缩放"
            self.export_global_scale.name = "导出全局缩放"
            self.import_light_scale.name = "灯光缩放"
            self.export_light_scale.name = "灯光缩放"
            self.import_rotation_x.name = "X轴旋转"
            self.import_rotation_y.name = "Y轴旋转"
            self.import_rotation_z.name = "Z轴旋转"
            self.export_rotation_x.name = "X轴旋转"
            self.export_rotation_y.name = "Y轴旋转"
            self.export_rotation_z.name = "Z轴旋转"
            
            # Update sync options
            self.sync_pypreference_check2.name = "识别渲染器"
            self.sync_pypreference_check2.description = "识别渲染器设置"
            
            # Update project info sync options
            self.import_sync_resolution.name = "导入分辨率"
            self.export_sync_resolution.name = "导出分辨率"
            self.import_sync_frame_rate.name = "导入帧率"
            self.export_sync_frame_rate.name = "导出帧率"
            self.import_sync_frame_range.name = "导入帧范围"
            self.export_sync_frame_range.name = "导出帧范围"
            self.import_sync_output_path.name = "导入输出路径"
            self.export_sync_output_path.name = "导出输出路径"
            self.import_sync_file_format.name = "导入文件格式"
            self.export_sync_file_format.name = "导出文件格式"
            
        else:
            prefs.view.language = 'en_US'
            # Update UI strings to English
            self.clipboard_keymap.name = "Shortcut Style"
            self.clipboard_keymap.description = "Choose shortcut trigger method"
            self.clipboard_keymap.items[0][2] = "Use standard keyboard shortcut"
            self.clipboard_keymap.items[1][2] = "Use mouse drag operation"
            
            # Update import/export preset strings
            self.import_export_preset.name = "Preset"
            self.import_export_preset.description = "Choose preset for import/export options"
            self.import_export_preset.items[0][2] = "Select all options"
            self.import_export_preset.items[1][2] = "Select only model-related options"
            self.import_export_preset.items[2][2] = "Select commonly used options"
            
            # Update axis preset strings
            self.import_axis_preset.name = "Import Axis Preset"
            self.export_axis_preset.name = "Export Axis Preset"
            
            # Update property names
            self.import_lights.name = "Import Lights"
            self.export_lights.name = "Export Lights"
            self.import_cameras.name = "Import Cameras"
            self.export_cameras.name = "Export Cameras"
            self.import_materials.name = "Import Materials"
            self.export_materials.name = "Export Materials"
            self.import_meshes.name = "Import Meshes"
            self.export_meshes.name = "Export Meshes"
            self.import_armatures.name = "Import Armatures"
            self.export_armatures.name = "Export Armatures"
            self.import_bake_animation.name = "Import Baked Animation"
            self.export_bake_animation.name = "Export Baked Animation"
            
            # Update scale and rotation properties
            self.import_global_scale.name = "Import Global Scale"
            self.export_global_scale.name = "Export Global Scale"
            self.import_light_scale.name = "Light Scale"
            self.export_light_scale.name = "Light Scale"
            self.import_rotation_x.name = "Rotation X"
            self.import_rotation_y.name = "Rotation Y"
            self.import_rotation_z.name = "Rotation Z"
            self.export_rotation_x.name = "Rotation X"
            self.export_rotation_y.name = "Rotation Y"
            self.export_rotation_z.name = "Rotation Z"
            
            # Update sync options
            self.sync_pypreference_check2.name = "Identify Renderer"
            self.sync_pypreference_check2.description = "Identify renderer settings"
            
            # Update project info sync options
            self.import_sync_resolution.name = "Import Resolution"
            self.export_sync_resolution.name = "Export Resolution"
            self.import_sync_frame_rate.name = "Import Frame Rate"
            self.export_sync_frame_rate.name = "Export Frame Rate"
            self.import_sync_frame_range.name = "Import Frame Range"
            self.export_sync_frame_range.name = "Export Frame Range"
            self.import_sync_output_path.name = "Import Output Path"
            self.export_sync_output_path.name = "Export Output Path"
            self.import_sync_file_format.name = "Import File Format"
            self.export_sync_file_format.name = "Export File Format"

    # Add cache info properties
    cache_file_count: bpy.props.IntProperty(
        name="Cache Files",
        default=0,
        get=lambda self: self.get_cache_info()[0]
    )
    
    cache_size_mb: bpy.props.FloatProperty(
        name="Cache Size (MB)",
        default=0,
        get=lambda self: self.get_cache_info()[1] / 1024 / 1024
    )

    def get_cache_info(self):
        """Get current cache information"""
        documents_dir = os.path.join(os.path.expanduser("~"), "Documents")
        cache_dir = os.path.join(documents_dir, "cache")
        
        if not os.path.exists(cache_dir):
            return 0, 0
            
        # Get all FBX and image files
        fbx_files = glob.glob(os.path.join(cache_dir, "*.fbx"))
        image_files = []
        for ext in ['*.jpg', '*.jpeg', '*.png']:
            image_files.extend(glob.glob(os.path.join(cache_dir, ext)))
        
        all_files = fbx_files + image_files
        
        # Calculate total size
        total_size = sum(os.path.getsize(f) for f in all_files)
        
        return len(all_files), total_size

    # Add shortcut style selection
    clipboard_keymap: bpy.props.EnumProperty(
        items=[
            ('0', 'Standard Shortcut (Ctrl+Shift+V) / 标准快捷键', 'Use standard keyboard shortcut / 使用标准键盘快捷键'),
            ('1', 'Mouse Drag (Ctrl+Alt+Drag) / 鼠标拖拽', 'Use mouse drag operation / 使用鼠标拖拽操作')
        ],
        name="Shortcut Style / 快捷键风格",
        description="Choose shortcut trigger method / 选择快捷键触发方式",
        default='0',
        update=lambda self, context: update_keymaps(self)
    )

    # 新增灯光缩放属性
    import_light_scale: bpy.props.FloatProperty(
        name="Light Scale",
        description="Scale imported lights",
        default=1.0,
        min=0.00001,
        max=1000000.0,
    )

    export_light_scale: bpy.props.FloatProperty(
        name="Light Scale",
        description="Scale exported lights",
        default=0.01,
        min=0.00001,
        max=1000000.0,
    )

    # Add sync option
    sync_pypreference_check2: bpy.props.BoolProperty(
        name="Identify Renderer / 识别渲染器",
        description="Identify renderer settings / 识别渲染器设置",
        default=True,
        update=lambda self, context: self.sync_preference_file(),
    )

    # ABC-specific option (for Bata mode)
    randomize_names_before_export: bpy.props.BoolProperty(
        name="Data Compatibility / 数据兼容性",
        description="Randomize object and data block names before export for enhanced compatibility / 在导出前随机重命名所有对象和数据块以增强兼容性",
        default=True,
    )

    # 导入项目信息同步选项
    import_sync_resolution: bpy.props.BoolProperty(
        name="Import Resolution / 导入分辨率",
        description="Import resolution settings / 导入分辨率设置",
        default=True,
    )
    import_sync_frame_rate: bpy.props.BoolProperty(
        name="Import Frame Rate / 导入帧率",
        description="Import frame rate settings / 导入帧率设置",
        default=True,
    )
    import_sync_frame_range: bpy.props.BoolProperty(
        name="Import Frame Range / 导入帧范围",
        description="Import frame range settings / 导入帧范围设置",
        default=True,
    )
    import_sync_output_path: bpy.props.BoolProperty(
        name="Import Output Path / 导入输出路径",
        description="Import render output path / 导入渲染输出路径",
        default=True,
    )
    import_sync_file_format: bpy.props.BoolProperty(
        name="Import File Format / 导入文件格式",
        description="Import output file format / 导入输出文件格式",
        default=True,
    )

    # 导出项目信息同步选项
    export_sync_resolution: bpy.props.BoolProperty(
        name="Export Resolution / 导出分辨率",
        description="Export resolution settings / 导出分辨率设置",
        default=True,
    )
    export_sync_frame_rate: bpy.props.BoolProperty(
        name="Export Frame Rate / 导出帧率",
        description="Export frame rate settings / 导出帧率设置",
        default=True,
    )
    export_sync_frame_range: bpy.props.BoolProperty(
        name="Export Frame Range / 导出帧范围",
        description="Export frame range settings / 导出帧范围设置",
        default=True,
    )
    export_sync_output_path: bpy.props.BoolProperty(
        name="Export Output Path / 导出输出路径",
        description="Export render output path / 导出渲染输出路径",
        default=True,
    )
    export_sync_file_format: bpy.props.BoolProperty(
        name="Export File Format / 导出文件格式",
        description="Export output file format / 导出输出文件格式",
        default=True,
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
        name="Import Forward Axis / 导入前向轴",
        description="Forward axis for importing / 导入时的前向轴",
        items=[
            ('X', "X Forward", "X axis forward / X轴前向"),
            ('Y', "Y Forward", "Y axis forward / Y轴前向"),
            ('Z', "Z Forward", "Z axis forward / Z轴前向"),
            ('-X', "-X Forward", "-X axis forward / -X轴前向"),
            ('-Y', "-Y Forward", "-Y axis forward / -Y轴前向"),
            ('-Z', "-Z Forward", "-Z axis forward (Default) / -Z轴前向（默认）"),
        ],
        default='-Z',
    )
    
    import_axis_up: bpy.props.EnumProperty(
        name="Import Up Axis / 导入向上轴",
        description="Up axis for importing / 导入时的向上轴",
        items=[
            ('X', "X Up", "X axis up / X轴向上"),
            ('Y', "Y Up", "Y axis up (Default) / Y轴向上（默认）"),
            ('Z', "Z Up", "Z axis up / Z轴向上"),
            ('-X', "-X Up", "-X axis up / -X轴向上"),
            ('-Y', "-Y Up", "-Y axis up / -Y轴向上"),
            ('-Z', "-Z Up", "-Z axis up / -Z轴向上"),
        ],
        default='Y',
    )

    # 导出轴向设置
    export_axis_forward: bpy.props.EnumProperty(
        name="Export Forward Axis / 导出前向轴",
        description="Forward axis for exporting / 导出时的前向轴",
        items=[
            ('X', "X Forward", "X axis forward / X轴前向"),
            ('Y', "Y Forward", "Y axis forward / Y轴前向"),
            ('Z', "Z Forward", "Z axis forward / Z轴前向"),
            ('-X', "-X Forward", "-X axis forward / -X轴前向"),
            ('-Y', "-Y Forward", "-Y axis forward / -Y轴前向"),
            ('-Z', "-Z Forward", "-Z axis forward (Default) / -Z轴前向（默认）"),
        ],
        default='-Z',
    )
    
    export_axis_up: bpy.props.EnumProperty(
        name="Export Up Axis / 导出向上轴",
        description="Up axis for exporting / 导出时的向上轴",
        items=[
            ('X', "X Up", "X axis up / X轴向上"),
            ('Y', "Y Up", "Y axis up (Default) / Y轴向上（默认）"),
            ('Z', "Z Up", "Z axis up / Z轴向上"),
            ('-X', "-X Up", "-X axis up / -X轴向上"),
            ('-Y', "-Y Up", "-Y axis up / -Y轴向上"),
            ('-Z', "-Z Up", "-Z axis up / -Z轴向上"),
        ],
        default='Y',
    )

    # 添加独立的缩放比例滑块
    import_global_scale: bpy.props.FloatProperty(
        name="Import Global Scale / 导入全局缩放",
        description="Scale all imported data / 缩放所有导入的数据",
        default=1,
        min=0.00001,
        max=1000000.0,
    )

    export_global_scale: bpy.props.FloatProperty(
        name="Export Global Scale / 导出全局缩放",
        description="Scale all exported data / 缩放所有导出的数据",
        default=1,
        min=0.000001,
        max=1000000.0,
    )
    # Add shortcut key properties
    copy_key: bpy.props.StringProperty(
        name="Copy Shortcut / 复制快捷键", 
        description="Shortcut key for copying (importing), e.g. CTRL_SHIFT_C / 复制（导入）的快捷键，例如 CTRL_SHIFT_C",
        default="CTRL_SHIFT_V",
        update=lambda self, context: self.update_keymaps(),
    )
    paste_key: bpy.props.StringProperty(
        name="Paste Shortcut / 粘贴快捷键",
        description="Shortcut key for pasting (exporting), e.g. CTRL_SHIFT_V / 粘贴（导出）的快捷键，例如 CTRL_SHIFT_V", 
        default="CTRL_SHIFT_C",
        update=lambda self, context: self.update_keymaps(),
    )

    # Add extension download menu
    extension_download: bpy.props.EnumProperty(
        name="Get More Extensions",
        description="Download SyncTools extensions for other software",
        items=[
            ('C4D', "Cinema 4D", "Download SyncTools for Cinema 4D / 下载Cinema 4D版SyncTools"),
            ('MAYA', "Maya", "Download SyncTools for Maya / 下载Maya版SyncTools"),
            ('3DSMAX', "3ds Max", "Download SyncTools for 3ds Max / 下载3ds Max版SyncTools"),
            ('HOUDINI', "Houdini", "Download SyncTools for Houdini / 下载Houdini版SyncTools"), 
            ('ZBRUSH', "ZBrush", "Download SyncTools for ZBrush / 下载ZBrush版SyncTools"),
            ('SP', "Substance Painter", "Download SyncTools for Substance Painter / 下载SP版SyncTools"),
            ('UNITY', "Unity", "Download SyncTools for Unity / 下载Unity版SyncTools"),
            ('UE', "Unreal Engine", "Download SyncTools for UE / 下载虚幻引擎版SyncTools"),
            ('MD', "Marvelous Designer", "Download SyncTools for MD / 下载MD版SyncTools"),
            ('SKETCHUP', "SketchUp", "Download SyncTools for SketchUp / 下载SketchUp版SyncTools"),
        ],
        default='C4D'
    )

    # 添加导入导出选项预设
    import_export_preset: bpy.props.EnumProperty(
        name="Import Export Preset / 导入导出预设",
        description="Choose preset for import/export options / 选择导入导出选项预设",
        items=[
            ('ALL', "All / 全部", "Select all options / 选择所有选项"),
            ('FAST', "Fast (Models Only) / 快速（仅模型）", "Select only model-related options / 仅选择模型相关选项"),
            ('MEDIUM', "Medium / 中等", "Select commonly used options / 选择常用选项"),
        ],
        default='ALL',
        update=lambda self, context: self.update_import_export_preset()
    )

    # 导入选项
    def get_default_light_setting():
        # 获取 Blender 版本
        version = bpy.app.version

        # 如果是 4.3.0 版本返回 False，其他版本返回 True
        if version[0] == 4 and version[1] == 3 and version[2] == 0:
            return False
        return True

    import_lights: bpy.props.BoolProperty(
        name="Import Lights / 导入灯光",
        description="Import lights / 导入灯光",
        default=get_default_light_setting(),
    )
    import_cameras: bpy.props.BoolProperty(
        name="Import Cameras / 导入相机",
        description="Import cameras / 导入相机",
        default=True,
    )
    import_materials: bpy.props.BoolProperty(
        name="Import Materials / 导入材质",
        description="Import materials / 导入材质",
        default=True,
    )
    import_meshes: bpy.props.BoolProperty(
        name="Import Meshes / 导入网格",
        description="Import meshes / 导入网格",
        default=True,
    )
    import_armatures: bpy.props.BoolProperty(
        name="Import Armatures / 导入骨骼",
        description="Import armatures (skeletons) / 导入骨骼（骨架）",
        default=True,
    )
    import_bake_animation: bpy.props.BoolProperty(
        name="Import Baked Animation / 导入烘焙动画",
        description="Import baked keyframe animation / 导入烘焙关键帧动画",
        default=True,
    )

    # 导出选项
    export_lights: bpy.props.BoolProperty(
        name="Export Lights / 导出灯光",
        description="Export lights / 导出灯光",
        default=get_default_light_setting(),
    )
    export_cameras: bpy.props.BoolProperty(
        name="Export Cameras / 导出相机",
        description="Export cameras / 导出相机",
        default=True,
    )
    export_materials: bpy.props.BoolProperty(
        name="Export Materials / 导出材质",
        description="Export materials / 导出材质",
        default=True,
    )
    export_meshes: bpy.props.BoolProperty(
        name="Export Meshes / 导出网格",
        description="Export meshes / 导出网格",
        default=True,
    )
    export_armatures: bpy.props.BoolProperty(
        name="Export Armatures / 导出骨骼",
        description="Export armatures (skeletons) / 导出骨骼（骨架）",
        default=True,
    )
    export_bake_animation: bpy.props.BoolProperty(
        name="Export Baked Animation / 导出烘焙动画",
        description="Export baked keyframe animation / 导出烘焙关键帧动画",
        default=True,
    )

    # 添加旋转属性
    import_rotation_x: bpy.props.FloatProperty(
        name="Rotation X / X轴旋转",
        description="Import rotation around X axis in degrees / 导入时绕X轴旋转的角度",
        default=0,
        min=-360,
        max=360
    )
    import_rotation_y: bpy.props.FloatProperty(
        name="Rotation Y / Y轴旋转",
        description="Import rotation around Y axis in degrees / 导入时绕Y轴旋转的角度",
        default=0,
        min=-360,
        max=360
    )
    import_rotation_z: bpy.props.FloatProperty(
        name="Rotation Z / Z轴旋转",
        description="Import rotation around Z axis in degrees / 导入时绕Z轴旋转的角度",
        default=0,
        min=-360,
        max=360
    )

    export_rotation_x: bpy.props.FloatProperty(
        name="Rotation X / X轴旋转",
        description="Export rotation around X axis in degrees / 导出时绕X轴旋转的角度",
        default=0,
        min=-360,
        max=360
    )
    export_rotation_y: bpy.props.FloatProperty(
        name="Rotation Y / Y轴旋转",
        description="Export rotation around Y axis in degrees / 导出时绕Y轴旋转的角度",
        default=0,
        min=-360,
        max=360
    )
    export_rotation_z: bpy.props.FloatProperty(
        name="Rotation Z / Z轴旋转",
        description="Export rotation around Z axis in degrees / 导出时绕Z轴旋转的角度",
        default=0,
        min=-360,
        max=360
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
                'rotation_export': (0, 0, 0),   # 导出旋转角度
                'light_scale_import': 0.01,  # Cinema 4D 的灯光缩放
                'light_scale_export': 0.01
            },
            'BLENDER': {
                'forward': 'Z',
                'up': 'Y',
                'scale_import': 1.0,
                'scale_export': 1.0,
                'rotation_import': (0, 0, 0),
                'rotation_export': (0, 0, 0),
                'light_scale_import': 1.0,
                'light_scale_export': 1.0
            },
            '3DSMAX': {
                'forward': '-Y',
                'up': 'Z',
                'scale_import': 50.0,
                'scale_export': 0.01,
                'rotation_import': (0, 0, -90),
                'rotation_export': (0, 0, 0),
                'light_scale_import': 1.0,
                'light_scale_export': 1.0
            },
            'MAYA': {
                'forward': 'Z',
                'up': 'Y',
                'scale_import': 100.0,
                'scale_export': 0.01,
                'rotation_import': (0, 0, 0),
                'rotation_export': (0, 0, 0),
                'light_scale_import': 1.0,
                'light_scale_export': 1.0
            },
            'HOUDINI': {
                'forward': 'Z',
                'up': 'Y',
                'scale_import': 200.0,
                'scale_export': 0.005,
                'rotation_import': (0, 0, 0),
                'rotation_export': (0, 0, 0),
                'light_scale_import': 1.0,
                'light_scale_export': 1.0
            },
            'SP': {
                'forward': 'Z',
                'up': 'Y',
                'scale_import': 1.0,
                'scale_export': 1.0,
                'rotation_import': (0, 0, 0),
                'rotation_export': (0, 0, 0),
                'light_scale_import': 1.0,
                'light_scale_export': 1.0
            },
            'RHINO': {
                'forward': '-Z',
                'up': 'Y',
                'scale_import': 1.0,
                'scale_export': 1.0,
                'rotation_import': (0, 0, 0),
                'rotation_export': (0, 0, 0),
                'light_scale_import': 1.0,
                'light_scale_export': 1.0
            },
            'UE': {
                'forward': 'X',
                'up': 'Z',
                'scale_import': 1.0,
                'scale_export': 1.0,
                'rotation_import': (-90, 0, -90),
                'rotation_export': (-90, 0, -90),
                'light_scale_import': 1.0,
                'light_scale_export': 1.0
            },
            'UNITY': {
                'forward': 'Z',
                'up': 'Y',
                'scale_import': 1.0,
                'scale_export': 1.0,
                'rotation_import': (0, 0, 0),
                'rotation_export': (0, 0, 0),
                'light_scale_import': 1.0,
                'light_scale_export': 1.0
            },
            'MD': {
                'forward': 'Z',
                'up': 'Y',
                'scale_import': 1.0,
                'scale_export': 1.0,
                'rotation_import': (0, 0, 0),
                'rotation_export': (0, 0, 0),
                'light_scale_import': 1.0,
                'light_scale_export': 1.0
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
            self.import_light_scale = preset['light_scale_import']

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
            self.export_light_scale = preset['light_scale_export']

    def update_import_export_preset(self):
        if self.import_export_preset == 'ALL':
            # 全选所有选项
            self.import_lights = True
            self.export_lights = True
            self.import_cameras = True
            self.export_cameras = True
            self.import_materials = True
            self.export_materials = True
            self.import_meshes = True
            self.export_meshes = True
            self.import_armatures = True
            self.export_armatures = True
            self.import_bake_animation = True
            self.export_bake_animation = True
        elif self.import_export_preset == 'FAST':
            # 仅选择模型相关选项
            self.import_lights = False
            self.export_lights = False
            self.import_cameras = False
            self.export_cameras = False
            self.import_materials = True
            self.export_materials = True
            self.import_meshes = True
            self.export_meshes = True
            self.import_armatures = False
            self.export_armatures = False
            self.import_bake_animation = False
            self.export_bake_animation = False
        else:  # MEDIUM
            # 选择常用选项
            self.import_lights = False
            self.export_lights = False
            self.import_cameras = True
            self.export_cameras = True
            self.import_materials = True
            self.export_materials = True
            self.import_meshes = True
            self.export_meshes = True
            self.import_armatures = True
            self.export_armatures = True
            self.import_bake_animation = False
            self.export_bake_animation = False

    def draw(self, context):
        layout = self.layout
        is_chinese = self.interface_language == 'zh_HANS'

        # Language Selection
        box = layout.box()
        box.label(text="Language / 语言", icon='WORLD')
        box.prop(self, "interface_language", text="")
        
        layout.separator()

        # Sync Mode Selection
        box = layout.box()
        box.label(text="同步模式" if is_chinese else "Sync Mode", icon='SETTINGS')
        box.prop(self, "sync_mode", text="")
        
        # Show mode description
        if self.sync_mode == 'STANDARD':
            box.label(text="FBX模式：完整功能，支持材质、灯光、相机等" if is_chinese else "FBX Mode: Full features, supports materials, lights, cameras", icon='INFO')
        else:
            box.label(text="ABC模式：专注几何传输，更快速" if is_chinese else "ABC Mode: Geometry-focused, faster transfer", icon='EXPERIMENTAL')
        
        # Show mode-specific options
        if self.sync_mode == 'BATA':
            box.prop(self, "randomize_names_before_export")
        
        layout.separator()

        # Cache Management Section
        box = layout.box()
        box.label(text="缓存管理" if is_chinese else "Cache Management", icon='TEMP')
        row = box.row()
        row.label(text=f"{'缓存文件' if is_chinese else 'Cache Files'}: {self.cache_file_count}")
        row.label(text=f"{'总大小' if is_chinese else 'Total Size'}: {self.cache_size_mb:.2f} MB")
        row = box.row()
        row.operator("preferences.clear_cache", 
            text="清除缓存" if is_chinese else "Clear Cache", 
            icon='TRASH')
        
        layout.separator()

        # Original content
        row = layout.row()
        row.operator(
            "wm.url_open", 
            text="文档" if is_chinese else "Documentation",
            icon='HELP'
        ).url = "https://www.yuque.com/shouwangxingkong-0p4w3/ldvruc/qkb24gky94mkgbe4?singleDoc"
        row.operator(
            "wm.url_open",
            text="关于作者" if is_chinese else "About Author",
            icon='USER'
        ).url = "https://space.bilibili.com/34368968"

        # Second row buttons
        row = layout.row()
        row.operator(
            "wm.url_open",
            text="检查更新" if is_chinese else "Check Updates",
            icon='FILE_REFRESH'
        ).url = "https://www.yuque.com/shouwangxingkong-0p4w3/ldvruc/gmd4pud4fu2vz30z?singleDoc"
        row.operator(
            "wm.url_open", 
            text="加入QQ群" if is_chinese else "Join QQ Group",
            icon='COMMUNITY'
        ).url = "https://qm.qq.com/cgi-bin/qm/qr?k=9KgmVUQMfoGf7g_s-4tSe15oMJ6rbz6b&jump_from=webapi&authKey=hs9XWuCbT1jx9ytpzSsXbJuQCwUc2kXy0gRJfA+qMaVoXTbvhiOKz0dHOnP1+Cvt"

        # Third row button (single)
        row = layout.row()
        row.operator(
            "wm.url_open",
            text="购买专业版" if is_chinese else "Buy Pro Version",
            icon='FUND'
        ).url = "https://www.bilibili.com/video/BV1GT421k7fi"

        # Add dropdown menu and download button for getting more extensions
        box = layout.box()
        box.label(text="获取更多扩展:" if is_chinese else "Get More Extensions:", icon='DOWNARROW_HLT')
        row = box.row()
        row.prop(self, "extension_download", text="")
        row.operator("wm.url_open", 
            text="下载" if is_chinese else "Download", 
            icon='IMPORT').url = "https://www.yuque.com/shouwangxingkong-0p4w3/ldvruc/qkb24gky94mkgbe4?singleDoc"

        layout.separator()

        layout.label(text="首选项同步选项:" if is_chinese else "Preference Sync Options:")
        layout.prop(self, "sync_pypreference_check2")

        layout.separator()

        # Shortcut key settings
        layout.label(text="快捷键设置:" if is_chinese else "Shortcut Key Settings:")
        layout.prop(self, "clipboard_keymap")
        draw_keymap(self, context, layout)

        layout.separator()

        # Project info sync settings UI
        box = layout.box()
        box.label(text="项目信息同步设置:" if is_chinese else "Project Info Sync Settings:", icon='SCENE_DATA')
        
        # Create two-column layout
        row = box.row()
        
        # Import settings column
        col_import = row.column()
        col_import.label(text="导入设置:" if is_chinese else "Import Settings:", icon='IMPORT')
        col_import.prop(self, "import_sync_resolution")
        col_import.prop(self, "import_sync_frame_rate")
        col_import.prop(self, "import_sync_frame_range")
        col_import.prop(self, "import_sync_output_path")
        col_import.prop(self, "import_sync_file_format")
        
        # Add separator
        row.separator(factor=2.0)
        
        # Export settings column
        col_export = row.column()
        col_export.label(text="导出设置:" if is_chinese else "Export Settings:", icon='EXPORT')
        col_export.prop(self, "export_sync_resolution")
        col_export.prop(self, "export_sync_frame_rate")
        col_export.prop(self, "export_sync_frame_range")
        col_export.prop(self, "export_sync_output_path")
        col_export.prop(self, "export_sync_file_format")

        layout.separator()

        # Add import preset selection
        box = layout.box()
        box.label(text="导入轴向预设:" if is_chinese else "Import Axis Preset:")
        box.prop(self, "import_axis_preset")
        
        # Add export preset selection
        box = layout.box()
        box.label(text="导出轴向预设:" if is_chinese else "Export Axis Preset:")
        box.prop(self, "export_axis_preset")
        
        # Add explanation text
        if self.import_axis_preset != 'C4D' or self.export_axis_preset != 'C4D':
            box = layout.box()
            box.label(text="注意: 使用非Cinema 4D预设可能需要调整轴向" if is_chinese else "Note: Using non-Cinema 4D preset may require axis adjustment", icon='INFO')
            box.label(text=f"{'导入缩放' if is_chinese else 'Import Scale'}: {self.import_global_scale:.3f}", icon='IMPORT')
            box.label(text=f"{'导出缩放' if is_chinese else 'Export Scale'}: {self.export_global_scale:.3f}", icon='EXPORT')
        
        # Import axis and rotation settings
        box = layout.box()
        box.label(text="导入设置:" if is_chinese else "Import Settings:")
        row = box.row()
        row.prop(self, "import_axis_forward")
        row.prop(self, "import_axis_up")
        box.prop(self, "import_global_scale")
        
        # Import rotation settings
        row = box.row()
        row.prop(self, "import_rotation_x")
        row.prop(self, "import_rotation_y")
        row.prop(self, "import_rotation_z")
        
        # Export axis and rotation settings
        box = layout.box()
        box.label(text="导出设置:" if is_chinese else "Export Settings:")
        row = box.row()
        row.prop(self, "export_axis_forward")
        row.prop(self, "export_axis_up")
        box.prop(self, "export_global_scale")
        
        # Export rotation settings
        row = box.row()
        row.prop(self, "export_rotation_x")
        row.prop(self, "export_rotation_y")
        row.prop(self, "export_rotation_z")

        layout.separator()

        layout.label(text="导入导出选项:" if is_chinese else "Import & Export Options:")
        
        # Add preset selection
        box = layout.box()
        box.label(text="预设:" if is_chinese else "Preset:", icon='PRESET')
        box.prop(self, "import_export_preset", text="")
        
        # Original options
        row = layout.row()
        row.prop(self, "import_lights")
        row.prop(self, "export_lights")
        
        # Add light scale sliders
        if self.import_lights or self.export_lights:
            box = layout.box()
            row = box.row(align=True)
            if self.import_lights:
                row.prop(self, "import_light_scale")
            if self.export_lights:
                row.prop(self, "export_light_scale")
        
        row = layout.row()
        row.prop(self, "import_cameras")
        row.prop(self, "export_cameras")
        
        row = layout.row()
        row.prop(self, "import_materials")
        row.prop(self, "export_materials")
        
        row = layout.row()
        row.prop(self, "import_meshes")
        row.prop(self, "export_meshes")
        
        row = layout.row()
        row.prop(self, "import_armatures")
        row.prop(self, "export_armatures")
           
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

    # 根据预设选择导出逻辑
    if prefs.export_axis_preset == 'C4D':
        # --- 旧版 C4D 导出逻辑 ---
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
            axis_forward='-Z',  # C4D 默认轴向
            axis_up='Y',        # C4D 默认轴向
            global_scale=prefs.export_global_scale, # 使用预设的导出缩放
            use_selection=True,
            bake_anim=prefs.export_bake_animation,
            bake_anim_use_all_bones=False,
            bake_anim_force_startend_keying=True,
            bake_anim_step=1.0,
            bake_anim_simplify_factor=1.0,
            object_types=object_types
        )
        print(f"场景成功导出为 (C4D Preset): {fbx_filepath}")

    else:
        # --- 当前的导出逻辑 (非 C4D 预设) ---
        # 保存选中的对象
        selected_objects = bpy.context.selected_objects
        active_object = bpy.context.active_object

        # 为选中的对象创建临时副本并应用旋转和缩放
        temp_objects = []
        bpy.ops.object.select_all(action='DESELECT') # 取消选择所有对象以准备选择副本
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

            # 为灯光对象应用独立缩放
            if temp_obj.type == 'LIGHT' and prefs.export_lights:
                 # 注意：这里我们只应用缩放值，不在导出前应用变换
                 # 因为 FBX 导出器会处理 global_scale
                 # 如果需要对灯光应用特定的独立缩放，可能需要更复杂的处理
                 # 或者调整 C4D 端导入时的灯光缩放
                 pass # 暂时不直接应用灯光缩放，依赖 global_scale

            temp_objects.append(temp_obj)
            temp_obj.select_set(True) # 选中副本以供导出

        # 设置活动对象为副本中的第一个（如果存在）
        if temp_objects:
            bpy.context.view_layer.objects.active = temp_objects[0]
        else:
             bpy.context.view_layer.objects.active = None # 如果没有选中对象，则没有活动对象


        # 导出FBX (使用副本)
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
            axis_forward=prefs.export_axis_forward, # 使用预设轴向
            axis_up=prefs.export_axis_up,           # 使用预设轴向
            global_scale=prefs.export_global_scale, # 使用预设缩放
            use_selection=True, # 导出选中的副本
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
        bpy.ops.object.select_all(action='DESELECT') # 先取消所有选择
        for obj in selected_objects:
            obj.select_set(True)
        if active_object:
            bpy.context.view_layer.objects.active = active_object

        print(f"场景成功导出为 (Non-C4D Preset): {fbx_filepath}")


    # --- 通用部分：写入层级文件 ---
    txt_path = os.path.join(cache_dir, "hierarchy.txt")
    name_dict = {}
    # 确保我们引用的是原始选择的对象来写入层级
    original_selected_objects = bpy.context.selected_objects
    
    with open(txt_path, 'w', encoding='utf-8') as file: # 指定UTF-8编码
        # 只写入选中的对象的层级结构
        top_level_selected = [obj for obj in original_selected_objects if obj.parent is None or obj.parent not in original_selected_objects]
        for obj in top_level_selected:
            write_hierarchy_to_file(obj, file=file, name_dict=name_dict, selected_objects=set(original_selected_objects))


    print(f"层级结构已保存到: {txt_path}")


# 定义操作类
class OBJECT_OT_import_obj(bpy.types.Operator):
    """Import object via OBJ file format"""
    bl_idname = "idm.import_obj"
    bl_label = "Copy"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        prefs = context.preferences.addons[__name__].preferences
        
        if prefs.sync_mode == 'STANDARD':
            # Standard FBX mode
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

            # 导入项目信息
            cache_dir = os.path.join(documents_dir, "cache")
            json_path = os.path.join(cache_dir, "project_info.json")
            if os.path.exists(json_path):
                import_project_info_with_settings(json_path)
                print("已导入项目信息")

            # 执行import_latest_fbx()
            import_latest_fbx()

            # 如果SYNC_PREFERENCE_CHECK2为True，则执行importx
            if execute_importx:
                try:
                    bpy.ops.import_octane_material.importx()
                    print("SYNC_PREFERENCE_CHECK2为True，执行importx操作")
                except AttributeError:
                    print("未找到 'import_octane_material.importx' 操作。请确保相关插件已安装。")
        
        elif prefs.sync_mode == 'BATA':
            # Bata ABC mode
            import_abc_by_counter()
            print("执行ABC导入")

        return {'FINISHED'}


class OBJECT_OT_export_obj(bpy.types.Operator):
    """Export object via OBJ file format."""
    bl_idname = "idm.export_obj"
    bl_label = "Paste"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        prefs = context.preferences.addons[__name__].preferences
        
        if prefs.sync_mode == 'STANDARD':
            # Standard FBX mode
            # 导出项目信息
            documents_dir = os.path.join(os.path.expanduser("~"), "Documents")
            cache_dir = os.path.join(documents_dir, "cache")
            export_project_info_with_settings(cache_dir)
            print("已导出项目信息")

            # 执行FBX导出
            export_fbx_to_cache()
        
        elif prefs.sync_mode == 'BATA':
            # Bata ABC mode
            export_abc_to_cache()
            print("执行ABC导出")
            
        return {'FINISHED'}


# 定义面板类
class OBJECT_PT_fbx_import_export_panel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "SyncTools Pro"
    bl_idname = "OBJECT_PT_fbx_import_export"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "SyncTools"

    def draw(self, context):
        layout = self.layout
        prefs = context.preferences.addons[__name__].preferences
        is_chinese = prefs.interface_language == 'zh_HANS'
        
        # Mode selection
        box = layout.box()
        box.label(text="同步模式:" if is_chinese else "Sync Mode:", icon='SETTINGS')
        box.prop(prefs, "sync_mode", text="")
        
        # Show mode description
        if prefs.sync_mode == 'STANDARD':
            box.label(text="FBX模式：完整功能，支持项目信息同步" if is_chinese else "FBX Mode: Full features, project info sync", icon='INFO')
        else:
            box.label(text="ABC模式：快速几何传输，实验性功能" if is_chinese else "ABC Mode: Fast geometry transfer, experimental", icon='EXPERIMENTAL')
        
        # Show mode-specific options
        if prefs.sync_mode == 'BATA':
            box.prop(prefs, "randomize_names_before_export")
        
        layout.separator()
        
        # Adapt label based on mode
        if prefs.sync_mode == 'STANDARD':
            layout.label(text="复制/粘贴网格 (FBX):" if is_chinese else "Copy / paste meshes (FBX):")
        else:
            layout.label(text="复制/粘贴网格 (ABC):" if is_chinese else "Copy / paste meshes (ABC):")
            
        row = layout.row(align=True)
        row.operator("idm.export_obj", text=" 复制 " if is_chinese else " Copy ")
        row.operator("idm.import_obj", text=" 粘贴 " if is_chinese else " Paste ")


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


# ABC-specific functions (for Bata mode)
def generate_random_name(length=8):
    """生成随机的名称，包含字母和数字"""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length))

def rename_objects_and_data_blocks():
    """随机重命名所有物体及其数据块，包括动画数据块"""
    print("开始随机重命名对象和数据块...")
    renamed_count = 0
    # 重命名物体及其数据块
    for obj in bpy.data.objects:
        try:
            random_name = generate_random_name()
            obj.name = random_name
            renamed_count += 1
            if obj.data:
                obj.data.name = generate_random_name()
                renamed_count += 1
        except Exception as e:
            print(f"Error renaming object or its data {obj.name}: {e}")

    # 重命名材质
    for material in bpy.data.materials:
        try:
            material.name = generate_random_name()
            renamed_count += 1
        except Exception as e:
            print(f"Error renaming material {material.name}: {e}")

    # 重命名纹理
    for texture in bpy.data.textures:
        try:
            texture.name = generate_random_name()
            renamed_count += 1
        except Exception as e:
            print(f"Error renaming texture {texture.name}: {e}")

    print(f"已完成重命名 {renamed_count} 个对象和数据块")

def get_abc_counter(counter_file):
    """获取当前的ABC导出计数器值"""
    if os.path.exists(counter_file):
        with open(counter_file, 'r') as file:
            try:
                return int(file.read().strip())
            except ValueError:
                return 1
    return 1

def increment_abc_counter(counter_file):
    """递增ABC导出计数器值并返回新的计数器值"""
    counter = get_abc_counter(counter_file)
    with open(counter_file, 'w') as file:
        counter += 1
        file.write(str(counter))
    return counter

def delete_oldest_abc(cache_dir):
    """删除最旧的ABC文件以保持文件数量在限制内"""
    abc_files = list(Path(cache_dir).glob("*.abc"))
    if len(abc_files) >= 10:
        oldest_abc = min(abc_files, key=os.path.getmtime)
        os.remove(oldest_abc)
        print(f"删除最旧的ABC文件: {oldest_abc}")

def export_abc_to_cache():
    """导出选中对象为ABC文件到cache文件夹"""
    documents_dir = os.path.join(os.path.expanduser("~"), "Documents")
    cache_dir = os.path.join(documents_dir, "cache")

    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

    counter_file = os.path.join(cache_dir, "abc_counter.txt")
    counter = increment_abc_counter(counter_file)
    abc_filepath = os.path.join(cache_dir, f"export_{counter}.abc")

    # 在导出前删除最旧的ABC文件
    delete_oldest_abc(cache_dir)

    prefs = bpy.context.preferences.addons[__name__].preferences

    # 如果启用了随机命名，先执行重命名
    if prefs.randomize_names_before_export:
        rename_objects_and_data_blocks()

    selected_objects = bpy.context.selected_objects

    if not selected_objects:
        print("没有选中的对象")
        return

    # 导出为ABC
    bpy.ops.wm.alembic_export(
        filepath=abc_filepath,
        selected=True,
        global_scale=prefs.export_global_scale
    )

    print(f"ABC文件已导出到: {abc_filepath}")

    # 写入层级文件
    txt_path = os.path.join(cache_dir, "hierarchy.txt")
    name_dict = {}
    
    with open(txt_path, 'w', encoding='utf-8') as file:
        top_level_selected = [obj for obj in selected_objects if obj.parent is None or obj.parent not in selected_objects]
        for obj in top_level_selected:
            write_hierarchy_to_file(obj, file=file, name_dict=name_dict, selected_objects=set(selected_objects))

    print(f"层级结构已保存到: {txt_path}")

def get_latest_abc_file(cache_dir):
    """获取缓存目录中最新的ABC文件"""
    abc_files = list(Path(cache_dir).glob("*.abc"))
    if not abc_files:
        return None

    latest_abc = max(abc_files, key=os.path.getmtime)
    return latest_abc

def import_abc_by_counter():
    """根据计数器导入最新的ABC文件"""
    documents_dir = os.path.join(os.path.expanduser("~"), "Documents")
    cache_dir = os.path.join(documents_dir, "cache")

    if not os.path.exists(cache_dir):
        print(f"缓存目录不存在: {cache_dir}")
        return

    latest_abc = get_latest_abc_file(cache_dir)

    if latest_abc is None:
        print("缓存目录中没有找到ABC文件")
        return

    prefs = bpy.context.preferences.addons[__name__].preferences

    # 导入ABC文件
    bpy.ops.wm.alembic_import(
        filepath=str(latest_abc),
        as_background_job=False,
        scale=prefs.import_global_scale
    )

    print(f"已导入ABC文件: {latest_abc}")

    try:
        os.remove(str(latest_abc))
        print(f"已删除文件: {latest_abc}")
    except Exception as e:
        print(f"删除文件失败: {e}")


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
        prefs = context.preferences.addons[__name__].preferences
        is_chinese = prefs.interface_language == 'zh_HANS'
        
        layout.operator("idm.export_obj", 
            text="复制" if is_chinese else "Copy", 
            icon='COPYDOWN')
        layout.operator("idm.import_obj", 
            text="粘贴" if is_chinese else "Paste", 
            icon='PASTEDOWN')
        layout.separator()
        layout.operator("preferences.sync_pypreference_toggle", 
            text="切换同步" if is_chinese else "Toggle Sync", 
            icon='FILE_REFRESH')
        layout.operator("preferences.clear_cache", 
            text="清除缓存" if is_chinese else "Clear Cache", 
            icon='TRASH')
        layout.separator()
        layout.operator("preferences.addon_show", 
            text="首选项" if is_chinese else "Preference", 
            icon='PREFERENCES').module = __name__
        layout.operator("wm.url_open", 
            text="文档" if is_chinese else "Documentation", 
            icon='HELP').url = "https://www.yuque.com/shouwangxingkong-0p4w3/ldvruc/qkb24gky94mkgbe4?singleDoc"

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
    bpy.utils.register_class(PREFERENCES_OT_clear_cache)  # 注册清理缓存操作符

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
    bpy.utils.unregister_class(PREFERENCES_OT_clear_cache)  # 注销清理缓存操作符
    bpy.utils.unregister_class(IDToolsPreferences)
    bpy.utils.unregister_class(OBJECT_PT_fbx_import_export_panel)
    bpy.utils.unregister_class(OBJECT_OT_import_obj)
    bpy.utils.unregister_class(OBJECT_OT_export_obj)


if __name__ == "__main__":
    register()

def export_project_info_with_settings(cache_dir):
    """根据用户设置导出项目信息"""
    prefs = bpy.context.preferences.addons[__name__].preferences
    scene = bpy.context.scene
    render = scene.render
    image_settings = render.image_settings

    data = {}
    
    # 分辨率设置
    if prefs.export_sync_resolution:
        data.update({
            "resolution_x": render.resolution_x,
            "resolution_y": render.resolution_y,
        })
    else:
        data.update({
            "resolution_x": "none",
            "resolution_y": "none",
        })
    
    # 帧率设置
    if prefs.export_sync_frame_rate:
        data.update({
            "frame_rate": render.fps,
            "frame_rate_base": render.fps_base,
            "fps_final": render.fps / render.fps_base,
        })
    else:
        data.update({
            "frame_rate": "none",
            "frame_rate_base": "none",
            "fps_final": "none",
        })
    
    # 帧范围设置
    if prefs.export_sync_frame_range:
        data.update({
            "frame_start": scene.frame_start,
            "frame_end": scene.frame_end,
            "frame_current": scene.frame_current,
            "frame_step": scene.frame_step,
        })
    else:
        data.update({
            "frame_start": "none",
            "frame_end": "none",
            "frame_current": "none",
            "frame_step": "none",
        })
    
    # 输出路径设置
    if prefs.export_sync_output_path:
        data.update({
            "output_path": bpy.path.abspath(render.filepath),
        })
    else:
        data.update({
            "output_path": "none",
        })
    
    # 文件格式设置
    if prefs.export_sync_file_format:
        data.update({
            "file_format": image_settings.file_format,
        })
    else:
        data.update({
            "file_format": "none",
        })

    # 添加文件名信息（如果有）
    data["blend_file"] = bpy.path.basename(bpy.data.filepath) if bpy.data.filepath else "Unsaved"

    os.makedirs(cache_dir, exist_ok=True)
    save_path = os.path.join(cache_dir, "project_info.json")

    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

    print(f"已导出项目信息到: {save_path}")

def import_project_info_with_settings(json_path):
    """根据用户设置导入项目信息"""
    if not os.path.exists(json_path):
        print(f"未找到文件: {json_path}")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    prefs = bpy.context.preferences.addons[__name__].preferences
    scene = bpy.context.scene
    render = scene.render
    image_settings = render.image_settings

    # 分辨率设置
    if prefs.import_sync_resolution and "resolution_x" in data:
        if data["resolution_x"] != "none" and data["resolution_y"] != "none":
            render.resolution_x = data["resolution_x"]
            render.resolution_y = data["resolution_y"]
    
    # 帧率设置
    if prefs.import_sync_frame_rate and "frame_rate" in data:
        if data["frame_rate"] != "none":
            render.fps = data["frame_rate"]
            if "frame_rate_base" in data and data["frame_rate_base"] != "none":
                render.fps_base = data["frame_rate_base"]
    
    # 帧范围设置
    if prefs.import_sync_frame_range:
        if "frame_start" in data and data["frame_start"] != "none":
            scene.frame_start = data["frame_start"]
        if "frame_end" in data and data["frame_end"] != "none":
            scene.frame_end = data["frame_end"]
        if "frame_current" in data and data["frame_current"] != "none":
            scene.frame_current = data["frame_current"]
        if "frame_step" in data and data["frame_step"] != "none":
            scene.frame_step = data["frame_step"]
    
    # 输出路径设置
    if prefs.import_sync_output_path and "output_path" in data:
        if data["output_path"] != "none":
            render.filepath = bpy.path.relpath(data["output_path"])
    
    # 文件格式设置
    if prefs.import_sync_file_format and "file_format" in data:
        if data["file_format"] != "none":
            image_settings.file_format = data["file_format"]

    print("已根据设置导入项目信息")

class PREFERENCES_OT_clear_cache(bpy.types.Operator):
    """Clear cache files (FBX and images)"""
    bl_idname = "preferences.clear_cache"
    bl_label = "Clear Cache"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        documents_dir = os.path.join(os.path.expanduser("~"), "Documents")
        cache_dir = os.path.join(documents_dir, "cache")
        
        if not os.path.exists(cache_dir):
            self.report({'WARNING'}, 
                "缓存目录不存在" if context.preferences.addons[__name__].preferences.interface_language == 'zh_HANS'
                else "Cache directory does not exist")
            return {'CANCELLED'}
            
        num_files, total_size = self.get_cache_info()
        
        fbx_files = glob.glob(os.path.join(cache_dir, "*.fbx"))
        image_files = []
        for ext in ['*.jpg', '*.jpeg', '*.png']:
            image_files.extend(glob.glob(os.path.join(cache_dir, ext)))
            
        for file in fbx_files + image_files:
            try:
                os.remove(file)
            except Exception as e:
                print(f"{'删除文件出错' if context.preferences.addons[__name__].preferences.interface_language == 'zh_HANS' else 'Error deleting'} {file}: {e}")
                
        self.report({'INFO'}, 
            f"已清除 {num_files} 个文件 ({total_size/1024/1024:.2f} MB)" if context.preferences.addons[__name__].preferences.interface_language == 'zh_HANS'
            else f"Cleared {num_files} files ({total_size/1024/1024:.2f} MB)")
        return {'FINISHED'}

    def get_cache_info(self):
        """Get current cache information"""
        documents_dir = os.path.join(os.path.expanduser("~"), "Documents")
        cache_dir = os.path.join(documents_dir, "cache")
        
        if not os.path.exists(cache_dir):
            return 0, 0
            
        # Get all FBX and image files
        fbx_files = glob.glob(os.path.join(cache_dir, "*.fbx"))
        image_files = []
        for ext in ['*.jpg', '*.jpeg', '*.png']:
            image_files.extend(glob.glob(os.path.join(cache_dir, ext)))
        
        all_files = fbx_files + image_files
        
        # Calculate total size
        total_size = sum(os.path.getsize(f) for f in all_files)
        
        return len(all_files), total_size
