import os
import json

# 自动检测当前软件环境
try:
    import bpy
    CURRENT_SOFTWARE = "BLENDER"
except ImportError:
    try:
        import c4d
        CURRENT_SOFTWARE = "C4D"
    except ImportError:
        CURRENT_SOFTWARE = None

# C4D文件格式映射表
C4D_FORMAT_MAPPING = {
    "TIF": 1100,
    "PNG": 1023671,
    "JPG": 1016606,
    "JPEG": 1016606,
    "EXR": 1104
}

def export_project_info(save_dir):
    """导出当前项目基本信息到 JSON"""
    if CURRENT_SOFTWARE == "BLENDER":
        scene = bpy.context.scene
        render = scene.render
        image_settings = render.image_settings

        data = {
            "resolution_x": render.resolution_x,
            "resolution_y": render.resolution_y,
            "frame_start": scene.frame_start,
            "frame_end": scene.frame_end,
            "frame_current": scene.frame_current,
            "frame_rate": render.fps,
            "frame_rate_base": render.fps_base,
            "fps_final": render.fps / render.fps_base,
            "frame_step": scene.frame_step,
            "blend_file": bpy.path.basename(bpy.data.filepath) if bpy.data.filepath else "Unsaved",
            "output_path": bpy.path.abspath(render.filepath),
            "file_format": image_settings.file_format
        }

    elif CURRENT_SOFTWARE == "C4D":
        doc = c4d.documents.GetActiveDocument()
        renderData = doc.GetActiveRenderData()
        bd = renderData.GetDataInstance()

        def get_frame_from_basetime(basetime):
            return basetime.GetFrame(doc.GetFps())

        min_time = doc[c4d.DOCUMENT_MINTIME]
        max_time = doc[c4d.DOCUMENT_MAXTIME]

        frame_start = get_frame_from_basetime(min_time)
        frame_end = get_frame_from_basetime(max_time)
        frame_current = doc.GetTime().GetFrame(doc.GetFps())

        data = {
            "resolution_x": int(bd[c4d.RDATA_XRES]),
            "resolution_y": int(bd[c4d.RDATA_YRES]),
            "frame_start": frame_start,
            "frame_end": frame_end,
            "frame_current": frame_current,
            "frame_rate": int(doc.GetFps()),
            "frame_rate_base": 1.0,
            "fps_final": float(doc.GetFps()),
            "frame_step": 1,
            "blend_file": "Unsaved",  # C4D不直接提供
            "output_path": bd[c4d.RDATA_PATH],
            "file_format": "PNG"  # 这里可以更细处理
        }

    else:
        raise RuntimeError("未检测到支持的软件环境（Blender或C4D）")

    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, "project_info.json")

    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

    print(f"[{CURRENT_SOFTWARE}] 项目信息已导出到: {save_path}")

def import_project_info(json_path):
    """从 JSON 文件读取并应用项目信息"""
    if not os.path.exists(json_path):
        print(f"未找到文件: {json_path}")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if CURRENT_SOFTWARE == "BLENDER":
        scene = bpy.context.scene
        render = scene.render
        image_settings = render.image_settings

        render.resolution_x = data.get("resolution_x", render.resolution_x)
        render.resolution_y = data.get("resolution_y", render.resolution_y)
        scene.frame_start = data.get("frame_start", scene.frame_start)
        scene.frame_end = data.get("frame_end", scene.frame_end)
        scene.frame_current = data.get("frame_current", scene.frame_current)
        render.fps = data.get("frame_rate", render.fps)
        render.fps_base = data.get("frame_rate_base", render.fps_base)
        scene.frame_step = data.get("frame_step", scene.frame_step)
        render.filepath = bpy.path.relpath(data.get("output_path", render.filepath))
        image_settings.file_format = data.get("file_format", image_settings.file_format)

    elif CURRENT_SOFTWARE == "C4D":
        doc = c4d.documents.GetActiveDocument()
        renderData = doc.GetActiveRenderData()
        bd = renderData.GetDataInstance()

        bd[c4d.RDATA_XRES] = float(data.get("resolution_x", bd[c4d.RDATA_XRES]))
        bd[c4d.RDATA_YRES] = float(data.get("resolution_y", bd[c4d.RDATA_YRES]))

        fps = int(data.get("frame_rate", doc.GetFps()))
        doc.SetFps(fps)

        def set_frame_to_basetime(frame, fps):
            return c4d.BaseTime(frame, fps)

        frame_start = int(data.get("frame_start", 0))
        frame_end = int(data.get("frame_end", 90))
        frame_current = int(data.get("frame_current", frame_start))

        doc.SetMinTime(set_frame_to_basetime(frame_start, fps))
        doc.SetMaxTime(set_frame_to_basetime(frame_end, fps))
        doc.SetLoopMinTime(set_frame_to_basetime(frame_start, fps))
        doc.SetLoopMaxTime(set_frame_to_basetime(frame_end, fps))
        doc.SetTime(set_frame_to_basetime(frame_current, fps))

        output_path = data.get("output_path")
        if output_path:
            bd[c4d.RDATA_PATH] = str(output_path)

        file_format = data.get("file_format")
        if file_format:
            format_id = C4D_FORMAT_MAPPING.get(file_format.upper())
            if format_id:
                bd[c4d.RDATA_FORMAT] = format_id
            else:
                print(f"警告：未识别的文件格式 '{file_format}'，保持原样。")

        c4d.EventAdd()

    else:
        raise RuntimeError("未检测到支持的软件环境（Blender或C4D）")

    print(f"[{CURRENT_SOFTWARE}] 成功从 {json_path} 导入并应用项目设置")
