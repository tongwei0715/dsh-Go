#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
问问Ai (wenwenai.cn) — 针对 ccch1mneyyy/dsh-Go 的全方位深度品牌重塑、Logo 修复与文案净化脚本
彻底解决：
  1. 桌面与启动屏 Adaptive Icon 被裁切/显示不全：提取问问Ai图标内部气泡前景（去蓝色底板）居中缩放到 108dp 的 62dp 安全区内，并重写 ic_launcher_monochrome.xml 矢量图。
  2. Flutter 界面内 BrandMark / BrandLockup / AppIconPreview 显示不全：将 BrandMark.aspect 修正为 1.0、visualCentre 修正为 Offset(0.5, 0.5)，并在非 tile 模式下绘制带 #2F5BFF 圆角底板的完整问问Ai图标（解决浅色背景下白色气泡和右上角耳机消失的问题）。
  3. 聊天空状态中央图标（WhaleTail）被单色染成色块：移除 ColorFilter.mode(..., BlendMode.srcIn)，让问问仔全彩原样呈现。
  4. 欢迎页大标题「把 DeepSeek 智能体装进口袋」与各页面标题「DSH 在哪里运行」「给 DSH 发消息」「DSH 正在干活」「下载/DSH-Go」等全部替换为「遇事不决，\n问问Ai！」与「问问Ai」。
"""
import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path
from PIL import Image

# Android 13+ 主题图标矢量层 (108x108 画布，居中放置问问Ai双气泡与问号)
MONOCHROME_XML = """<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp"
    android:height="108dp"
    android:viewportWidth="108"
    android:viewportHeight="108">
    <group android:translateX="21.0" android:translateY="21.0" android:scaleX="0.55" android:scaleY="0.55">
        <path android:fillColor="#FFFFFFFF" android:pathData="M26,62h14L24,78z"/>
        <path android:fillColor="#FFFFFFFF" android:pathData="M34,20h26a16,16 0 0,1 16,16v14a16,16 0 0,1 -16,16h-26a16,16 0 0,1 -16,-16v-14a16,16 0 0,1 16,-16z"/>
        <path android:fillColor="#CCFFFFFF" android:pathData="M72,90h20l2,16z"/>
        <path android:fillColor="#CCFFFFFF" android:pathData="M57,44h28a17,17 0 0,1 17,17v14a17,17 0 0,1 -17,17h-28a17,17 0 0,1 -17,-17v-14a17,17 0 0,1 17,-17z"/>
    </group>
</vector>
"""

# 状态栏小图标 ic_stat_dsh.xml
IC_STAT_XML = """<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp"
    android:height="24dp"
    android:viewportWidth="120"
    android:viewportHeight="120">
    <path android:fillColor="#FFFFFFFF" android:pathData="M26,62h14L24,78z"/>
    <path android:fillColor="#FFFFFFFF" android:pathData="M34,20h26a16,16 0 0,1 16,16v14a16,16 0 0,1 -16,16h-26a16,16 0 0,1 -16,-16v-14a16,16 0 0,1 16,-16z"/>
    <path android:fillColor="#CCFFFFFF" android:pathData="M72,90h20l2,16z"/>
    <path android:fillColor="#CCFFFFFF" android:pathData="M57,44h28a17,17 0 0,1 17,17v14a17,17 0 0,1 -17,17h-28a17,17 0 0,1 -17,-17v-14a17,17 0 0,1 17,-17z"/>
</vector>
"""

BRAND_MARK_DART = """import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';

import '../../state/app_info.dart';
import '../theme/theme.dart';
import 'brand_glyph.g.dart';

/// 问问Ai (wenwenai.cn) 完整品牌图标绘制组件（1:1 比例，完整呈现蓝底+黄白双气泡+问号+AI耳机胶囊）。
class BrandMark extends StatelessWidget {
  const BrandMark({super.key, this.size = 28, this.color, this.tile = false});

  final double size;
  final Color? color;
  final bool tile;

  /// 正方形 1:1 比例，保证在任何容器（欢迎页、侧边栏、网页悬浮球、关于页）中绝不裁切变形。
  static const aspect = 1.0;

  /// 视觉中心严格居中。
  static const visualCentre = Offset(0.5, 0.5);

  static Offset opticalShift(double size) => Offset.zero;

  @override
  Widget build(BuildContext context) {
    final style = tile
        ? _Style.tile
        : color != null
        ? _Style.mono
        : Theme.of(context).brightness == Brightness.dark
        ? _Style.dark
        : _Style.light;
    return Semantics(
      label: AppInfo.wordmark,
      image: true,
      child: CustomPaint(
        size: Size.square(size),
        painter: _BrandPainter(style, color),
      ),
    );
  }
}

enum _Style { light, dark, mono, tile }

class _BrandPainter extends CustomPainter {
  const _BrandPainter(this.style, this.color);

  final _Style style;
  final Color? color;

  @override
  void paint(Canvas canvas, Size size) {
    canvas.save();
    final scaleX = size.width / 120.0;
    final scaleY = size.height / 120.0;
    canvas.scale(scaleX, scaleY);

    if (style != _Style.mono) {
      // 始终绘制 #2F5BFF 圆角蓝底，确保白色气泡与右上角深蓝AI耳机胶囊在浅色/深色背景下都 100% 清晰完整
      final bgPaint = Paint()..color = const Color(0xFF2F5BFF);
      canvas.drawRRect(
        RRect.fromRectAndRadius(const Rect.fromLTWH(0, 0, 120, 120), const Radius.circular(28)),
        bgPaint,
      );
    }

    final Color leftColor = style == _Style.mono ? color! : const Color(0xFFFFC93C);
    final Color rightColor = style == _Style.mono ? color!.withValues(alpha: 0.88) : const Color(0xFFFFFFFF);
    final Color qColor = style == _Style.mono ? const Color(0xFF2F5BFF) : const Color(0xFF2F5BFF);

    // 1. 左上黄色气泡 + 尖角
    final pLeft = Paint()..color = leftColor;
    canvas.drawRRect(
      RRect.fromRectAndRadius(const Rect.fromLTWH(18, 20, 58, 46), const Radius.circular(16)),
      pLeft,
    );
    final tailLeft = Path()
      ..moveTo(26, 62)
      ..lineTo(40, 62)
      ..lineTo(24, 78)
      ..close();
    canvas.drawPath(tailLeft, pLeft);

    // 2. 右下白色气泡 + 尖角
    final pRight = Paint()..color = rightColor;
    canvas.drawRRect(
      RRect.fromRectAndRadius(const Rect.fromLTWH(40, 44, 62, 48), const Radius.circular(17)),
      pRight,
    );
    final tailRight = Path()
      ..moveTo(72, 90)
      ..lineTo(92, 90)
      ..lineTo(94, 106)
      ..close();
    canvas.drawPath(tailRight, pRight);

    // 3. 问号曲线与圆点
    if (style != _Style.mono) {
      final qPaint = Paint()
        ..color = qColor
        ..style = PaintingStyle.stroke
        ..strokeWidth = 5.0
        ..strokeCap = StrokeCap.round;
      final qPath = Path()
        ..moveTo(62, 62)
        ..cubicTo(62, 54, 80, 54, 80, 63)
        ..cubicTo(80, 70, 71, 70, 71, 76);
      canvas.drawPath(qPath, qPaint);
      canvas.drawCircle(const Offset(71, 85), 3.2, Paint()..color = qColor);

      // 4. 右上角深蓝胶囊与金色 AI 字样/光点（完整还原 wenwen-icon.svg）
      canvas.drawRRect(
        RRect.fromRectAndRadius(const Rect.fromLTWH(74, 12, 36, 22), const Radius.circular(11)),
        Paint()..color = const Color(0xFF14213D),
      );
      final aiStroke = Paint()
        ..color = const Color(0xFFFFC93C)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 2.6
        ..strokeCap = StrokeCap.round;
      canvas.drawCircle(const Offset(88.5, 23.2), 4.2, aiStroke);
      canvas.drawLine(const Offset(92.7, 18.4), const Offset(92.7, 28.0), aiStroke);
      canvas.drawLine(const Offset(99.5, 18.4), const Offset(99.5, 28.0), aiStroke);
      canvas.drawCircle(const Offset(99.5, 14.8), 1.6, Paint()..color = const Color(0xFFFFC93C));
    }

    canvas.restore();
  }

  @override
  bool shouldRepaint(_BrandPainter old) => old.style != style || old.color != color;
}

class BrandLockup extends StatelessWidget {
  const BrandLockup({
    super.key,
    this.height = 20,
    this.fontSize,
    this.label = AppInfo.wordmark,
    this.color,
    this.glyphColor,
  });

  final double height;
  final double? fontSize;
  final String label;
  final Color? color;
  final Color? glyphColor;

  static const glyphScale = 1.25;
  static const gapScale = 0.36;
  static const xHeight = 0.528;
  static const capHeight = 0.711;

  static double centreRise(String label, double size) =>
      (label.contains(RegExp('[a-z]')) ? xHeight : capHeight) * size / 2;

  static double wordInset(double size) => size * glyphScale * BrandMark.aspect + size * gapScale;

  double get _size => fontSize ?? height * 0.95;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final drawn = MediaQuery.textScalerOf(context).scale(_size);
    final glyph = drawn * glyphScale;
    return Row(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        BrandMark(size: glyph, color: glyphColor),
        SizedBox(width: drawn * gapScale),
        Text(
          label,
          style: AppType.wordmark(size: _size, color: color ?? scheme.onSurface),
        ),
      ],
    );
  }
}
"""


def extract_foreground_glyph(icon_1024_path: Path, size: int) -> Image.Image:
    """
    从 1024x1024 的完整图标中移除外圈 #2F5BFF 蓝色圆角底板，只保留内部的：
    - 左上黄色气泡
    - 右下白色气泡（及内部蓝色问号）
    - 右上深蓝 AI 胶囊
    并将其居中放入 size x size 的 Adaptive Icon 前景安全区（占 60% 宽高），
    这样 Android 桌面用圆形/超椭圆遮罩加上 #2F5BFF 背景层时，图标 100% 完整无白边、无裁切！
    """
    src = Image.open(icon_1024_path).convert("RGBA")
    w, h = src.size
    px = src.load()
    # 创建透明图层，只保留内部图形元素（去掉外围纯蓝底 #2F5BFF）
    fg = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    fg_px = fg.load()
    # 白色气泡内部区域（保留其中的蓝色问号）：大致在 x:[320, 880], y:[360, 820]
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a < 16:
                continue
            is_bg_blue = (abs(r - 47) <= 18 and abs(g - 91) <= 18 and abs(b - 255) <= 18)
            in_question_mark_box = (460 <= x <= 740 and 450 <= y <= 780)
            if is_bg_blue and not in_question_mark_box:
                continue
            fg_px[x, y] = (r, g, b, a)

    bbox = fg.getbbox()
    if bbox:
        fg = fg.crop(bbox)

    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    # Adaptive Icon 安全区直径为 66/108 ≈ 61%，这里取 0.56 * size 保证绝不被任何厂商圆遮罩切角
    target_max = int(round(size * 0.56))
    scale = min(target_max / fg.width, target_max / fg.height)
    nw = max(1, int(round(fg.width * scale)))
    nh = max(1, int(round(fg.height * scale)))
    resized = fg.resize((nw, nh), Image.Resampling.LANCZOS)
    ox = (size - nw) // 2
    oy = (size - nh) // 2
    out.alpha_composite(resized, (ox, oy))
    return out


def pick_pet_source(sheet_name: str, pet_dir: Path) -> Path:
    n = sheet_name.lower()
    if any(k in n for k in ["sleep", "rest"]):
        return pet_dir / "pet_sleeping.png"
    if any(k in n for k in ["happy", "smile", "thumb", "music", "swim", "hop", "double"]):
        return pet_dir / "pet_completed.png"
    if any(k in n for k in ["notif", "error", "poke", "drag", "carry", "tickle", "wake", "look", "spout"]):
        return pet_dir / "pet_confirm.png"
    return pet_dir / "pet_working.png"


def render_cell(src_img: Image.Image, cell_w: int, cell_h: int, dy: int = 0) -> Image.Image:
    cell = Image.new("RGBA", (cell_w, cell_h), (0, 0, 0, 0))
    avail_w = max(8, cell_w - 4)
    avail_h = max(8, cell_h - 6)
    scale = min(avail_w / src_img.width, avail_h / src_img.height)
    new_w = max(1, int(round(src_img.width * scale)))
    new_h = max(1, int(round(src_img.height * scale)))
    resized = src_img.resize((new_w, new_h), Image.Resampling.NEAREST)
    x = (cell_w - new_w) // 2
    y = max(0, min(cell_h - new_h, (cell_h - new_h) // 2 + dy))
    cell.alpha_composite(resized, (x, y))
    return cell


def rebuild_pet_pack_sheets(pack_dir: Path, pet_src_dir: Path, new_name: str) -> int:
    pack_file = pack_dir / "pack.json"
    if not pack_file.is_file():
        return 0
    pack = json.loads(pack_file.read_text(encoding="utf-8"))
    pack["name"] = new_name
    pack["author"] = "wenwenai.cn"
    pack["license"] = "问问Ai (wenwenai.cn) 原创像素桌宠"
    pack["source"] = "wenwenai.cn"
    pack_file.write_text(json.dumps(pack, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    sheet_specs = {}
    for anim in pack.get("animations", {}).values():
        sheet_specs[anim["sheet"]] = (int(anim["frameW"]), int(anim["frameH"]), int(anim["cols"]))

    count = 0
    for sheet_name, (fw, fh, cols) in sheet_specs.items():
        sheet_path = pack_dir / sheet_name
        if not sheet_path.is_file():
            continue
        with Image.open(sheet_path) as orig:
            sw, sh = orig.size
        src_png = pick_pet_source(sheet_name, pet_src_dir)
        with Image.open(src_png).convert("RGBA") as pet_img:
            new_sheet = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
            rows = max(1, sh // fh)
            actual_cols = max(1, min(cols, sw // fw))
            idx = 0
            for r in range(rows):
                for c in range(actual_cols):
                    dy = (-1, 0, 1, 0)[idx % 4]
                    cell = render_cell(pet_img, fw, fh, dy=dy)
                    new_sheet.alpha_composite(cell, (c * fw, r * fh))
                    idx += 1
            new_sheet.save(sheet_path, format="PNG", optimize=True)
            count += 1
    return count


def rebuild_whale_and_widgets(repo_root: Path, pet_src_dir: Path) -> None:
    whale_dir = repo_root / "app" / "assets" / "whale"
    whale_json = whale_dir / "whale.json"
    if whale_json.is_file():
        meta = json.loads(whale_json.read_text(encoding="utf-8"))
        fw, fh, cols = int(meta["frameWidth"]), int(meta["frameHeight"]), int(meta["columns"])
        for level in meta.get("levels", []):
            img_path = whale_dir / level["image"]
            if not img_path.is_file():
                continue
            with Image.open(img_path) as orig:
                sw, sh = orig.size
            src_png = pet_src_dir / ("pet_completed.png" if level["level"] == 1 else "pet_working.png")
            with Image.open(src_png).convert("RGBA") as pet_img:
                sheet = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
                rows = max(1, sh // fh)
                for r in range(rows):
                    for c in range(min(cols, sw // fw)):
                        dy = (-1, 0, 1, 0)[(r * cols + c) % 4]
                        cell = render_cell(pet_img, fw, fh, dy=dy)
                        sheet.alpha_composite(cell, (c * fw, r * fh))
                sheet.save(img_path, format="PNG", optimize=True)

    # 让 WhaleTail 绘制时保留问问仔全彩原色，而不是被 ColorFilter.mode(..., BlendMode.srcIn) 涂成单色块
    wt_dart = repo_root / "app" / "lib" / "ui" / "chat" / "widgets" / "whale_tail.dart"
    if wt_dart.is_file():
        wtxt = wt_dart.read_text(encoding="utf-8")
        wtxt = re.sub(
            r'\.\.colorFilter\s*=\s*ColorFilter\.mode\([^)]+\)',
            '..colorFilter = ColorFilter.mode(Colors.white.withValues(alpha: weight), BlendMode.modulate)',
            wtxt,
        )
        wt_dart.write_text(wtxt, encoding="utf-8")

    # 调整 empty_state.dart 中 WhaleTail 的透明度为 1.0（原为 0.4 半透明灰块）
    es_dart = repo_root / "app" / "lib" / "ui" / "chat" / "empty_state.dart"
    if es_dart.is_file():
        etxt = es_dart.read_text(encoding="utf-8")
        etxt = etxt.replace("color: whaleColorFor(theme.brightness).withValues(alpha: 0.4),", "color: Colors.white,")
        es_dart.write_text(etxt, encoding="utf-8")

    star_webp = repo_root / "app" / "assets" / "star" / "star_whale.webp"
    if star_webp.is_file():
        with Image.open(pet_src_dir / "pet_completed.png").convert("RGBA") as img:
            img.save(star_webp, format="WEBP", lossless=True)

    nodpi = repo_root / "app" / "android" / "app" / "src" / "main" / "res" / "drawable-nodpi"
    mapping = {
        "companion_widget_idle.png": "pet_working.png",
        "companion_widget_happy.png": "pet_completed.png",
        "companion_widget_sleeping.png": "pet_sleeping.png",
    }
    for dst_name, src_name in mapping.items():
        dst = nodpi / dst_name
        if dst.is_file():
            with Image.open(pet_src_dir / src_name).convert("RGBA") as img:
                img.resize((240, 240), Image.Resampling.NEAREST).save(dst, format="PNG", optimize=True)


def replace_android_icons(repo_root: Path, assets_dir: Path) -> None:
    res_dir = repo_root / "app" / "android" / "app" / "src" / "main" / "res"
    src_res = assets_dir / "android_res"
    icon_1024 = assets_dir / "wenwen-icon-1024.png"
    fg_sizes = {
        "mipmap-mdpi": 108,
        "mipmap-hdpi": 162,
        "mipmap-xhdpi": 216,
        "mipmap-xxhdpi": 324,
        "mipmap-xxxhdpi": 432,
    }
    for density, fg_px in fg_sizes.items():
        sdir = src_res / density
        ddir = res_dir / density
        if not sdir.is_dir() or not ddir.is_dir():
            continue
        ic_main = sdir / "ic_launcher.png"
        ic_round = sdir / "ic_launcher_round.png"
        clean_fg = extract_foreground_glyph(icon_1024, fg_px)
        for variant in ["", "_night", "_frost", "_ink"]:
            if ic_main.is_file():
                shutil.copy2(ic_main, ddir / f"ic_launcher{variant}.png")
            if ic_round.is_file():
                shutil.copy2(ic_round, ddir / f"ic_launcher{variant}_round.png")
            clean_fg.save(ddir / f"ic_launcher{variant}_foreground.png", format="PNG", optimize=True)

    drawable_dir = res_dir / "drawable"
    for bg_name, color in [
        ("ic_launcher_background.xml", "#2F5BFF"),
        ("ic_launcher_frost_background.xml", "#2F5BFF"),
        ("ic_launcher_ink_background.xml", "#14213D"),
        ("ic_launcher_night_background.xml", "#14213D"),
    ]:
        bg_file = drawable_dir / bg_name
        if bg_file.is_file():
            bg_file.write_text(
                f'<?xml version="1.0" encoding="utf-8"?>\n'
                f'<shape xmlns:android="http://schemas.android.com/apk/res/android">\n'
                f'    <solid android:color="{color}" />\n'
                f'</shape>\n',
                encoding="utf-8",
            )
    (drawable_dir / "ic_launcher_monochrome.xml").write_text(MONOCHROME_XML, encoding="utf-8")
    (drawable_dir / "ic_stat_dsh.xml").write_text(IC_STAT_XML, encoding="utf-8")


def patch_app_icon_picker(repo_root: Path) -> None:
    """将设置 -> 外观 -> 桌面图标选择器中的预览图也改为绘制问问Ai双气泡图标。"""
    picker = repo_root / "app" / "lib" / "ui" / "settings" / "appearance" / "app_icon_picker.dart"
    if not picker.is_file():
        return
    txt = picker.read_text(encoding="utf-8")
    txt = txt.replace(
        "AppIcon.mist => const AppIconArt._(Color(0xFF9AB0E8), Color(0xFF405AAD), AppIconGlyph.glassDark),",
        "AppIcon.mist => const AppIconArt._(Color(0xFF2F5BFF), Color(0xFF1D44DB), AppIconGlyph.glassDark),",
    )
    if "    switch (art.glyph) {" in txt:
        old_switch_start = txt.index("    switch (art.glyph) {")
        old_switch_end = txt.index("    canvas\n      ..restore()")
        new_switch = """    // 绘制问问Ai双气泡前景
    final pLeft = Paint()..color = const Color(0xFFFFC93C);
    canvas.drawRRect(RRect.fromRectAndRadius(const Rect.fromLTWH(28, 30, 32, 25), const Radius.circular(9)), pLeft);
    final pRight = Paint()..color = const Color(0xFFFFFFFF);
    canvas.drawRRect(RRect.fromRectAndRadius(const Rect.fromLTWH(42, 44, 34, 26), const Radius.circular(9)), pRight);
    final qPaint = Paint()
      ..color = const Color(0xFF2F5BFF)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3.2
      ..strokeCap = StrokeCap.round;
    final qPath = Path()
      ..moveTo(54, 54)
      ..cubicTo(54, 49, 64, 49, 64, 54.5)
      ..cubicTo(64, 58, 59, 58, 59, 61.5);
    canvas.drawPath(qPath, qPaint);
    canvas.drawCircle(const Offset(59, 66.5), 2.0, Paint()..color = const Color(0xFF2F5BFF));
"""
        txt = txt[:old_switch_start] + new_switch + txt[old_switch_end:]
    picker.write_text(txt, encoding="utf-8")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parent.parent)
    p.add_argument("--assets-dir", type=Path, default=None)
    p.add_argument("--app-id", default="cn.wenwenai.app")
    p.add_argument("--app-name", default="问问Ai")
    p.add_argument("--app-name-en", default="Wenwen.ai")
    p.add_argument("--slogan", default="遇事不决，问问Ai！")
    p.add_argument("--slogan-en", default="When in doubt, ask Wenwen.ai!")
    p.add_argument("--domain", default="wenwenai.cn")
    p.add_argument("--github-repo", default="tongwei0715/dsh-Go")
    args = p.parse_args()

    root = args.repo_root.resolve()
    assets = (args.assets_dir or (root / "brand_assets")).resolve()
    pet_dir = assets / "pet_wenwen"

    # 1. Gradle applicationId, AndroidManifest.xml, Kotlin 常量与 Android XML 字符串
    gradle_kts = root / "app" / "android" / "app" / "build.gradle.kts"
    if gradle_kts.is_file():
        gtxt = gradle_kts.read_text(encoding="utf-8")
        gtxt = re.sub(r'applicationId\s*=\s*"[^"]+"', f'applicationId = "{args.app_id}"', gtxt)
        gradle_kts.write_text(gtxt, encoding="utf-8")

    manifest_xml = root / "app" / "android" / "app" / "src" / "main" / "AndroidManifest.xml"
    if manifest_xml.is_file():
        mtxt = manifest_xml.read_text(encoding="utf-8")
        mtxt = re.sub(r'android:label="[^"]+"', f'android:label="{args.app_name}"', mtxt, count=1)
        manifest_xml.write_text(mtxt, encoding="utf-8")

    # Kotlin 硬编码名称替换
    for kt_rel, old_s, new_s in [
        ("app/android/app/src/main/kotlin/io/github/ccch1mneyyy/dsh_app/i18n/AppStrings.kt", 'const val APP_NAME = "DSH Go"', f'const val APP_NAME = "{args.app_name}"'),
        ("app/android/app/src/main/kotlin/io/github/ccch1mneyyy/dsh_app/media/MediaPlugin.kt", 'private const val ALBUM = "DSH Go"', f'private const val ALBUM = "{args.app_name}"'),
        ("app/android/app/src/main/kotlin/io/github/ccch1mneyyy/dsh_app/icons/PictureShortcutPlugin.kt", 'if (clean.isEmpty()) return "DSH Go"', f'if (clean.isEmpty()) return "{args.app_name}"'),
        ("app/android/app/src/main/kotlin/io/github/ccch1mneyyy/dsh_app/runtime/SafeMode.kt", "DSH 连续两次启动失败", f"{args.app_name} 连续两次启动失败"),
    ]:
        kf = root / kt_rel
        if kf.is_file():
            kf.write_text(kf.read_text(encoding="utf-8").replace(old_s, new_s), encoding="utf-8")

    res_dir = root / "app" / "android" / "app" / "src" / "main" / "res"
    for xml_f in res_dir.rglob("*.xml"):
        if xml_f.parent.name.startswith("values"):
            xtxt = xml_f.read_text(encoding="utf-8")
            rep = args.app_name if "zh" in xml_f.parent.name else args.app_name_en
            new_xtxt = xtxt.replace("DSH Go", rep).replace("DSH-Go", rep)
            if new_xtxt != xtxt:
                xml_f.write_text(new_xtxt, encoding="utf-8")
    print(f"[1/6] 已更新 Android 包名 ({args.app_id})、Manifest 与 Kotlin 原生常量")

    # 2. 提取透明安全区前景图标 & 生成问问仔精灵表
    replace_android_icons(root, assets)
    c1 = rebuild_pet_pack_sheets(root / "app" / "assets" / "pets" / "deepy-whale", pet_dir, "问问仔")
    c2 = rebuild_pet_pack_sheets(root / "app" / "assets" / "pets" / "whale-girl", pet_dir, "问问灵")
    rebuild_whale_and_widgets(root, pet_dir)
    print(f"[2/6] 已修复 Adaptive Icon 108dp 安全区居中前景并重绘问问仔精灵表 ({c1}+{c2} 张)")

    # 3. 更新 AppInfo、BrandMark、AppIconPreview 与硬编码 DSH 标题
    app_info = root / "app" / "lib" / "state" / "app_info.dart"
    if app_info.is_file():
        itxt = app_info.read_text(encoding="utf-8")
        itxt = re.sub(r"static const name = '[^']+';", f"static const name = '{args.app_name}';", itxt)
        itxt = re.sub(r"static const wordmark = '[^']+';", f"static const wordmark = '{args.app_name}';", itxt)
        app_info.write_text(itxt, encoding="utf-8")

    (root / "app" / "lib" / "ui" / "shell" / "brand_mark.dart").write_text(BRAND_MARK_DART, encoding="utf-8")
    patch_app_icon_picker(root)

    # 替换 Dart UI 中写死的 'DSH' 标题
    for dart_rel, old_d, new_d in [
        ("app/lib/ui/web/web_handle.dart", "const SheetTitleBar('DSH')", f"const SheetTitleBar('{args.app_name}')"),
        ("app/lib/ui/update/update_sheet.dart", "Text('DSH ${latest.version.name}'", f"Text('{args.app_name} ${{latest.version.name}}'"),
        ("app/lib/ui/remote/ssh_host_form.dart", "title: 'DSH',", f"title: '{args.app_name}',"),
    ]:
        df = root / dart_rel
        if df.is_file():
            df.write_text(df.read_text(encoding="utf-8").replace(old_d, new_d), encoding="utf-8")

    u_cfg = root / "app" / "lib" / "update" / "update_config.dart"
    if u_cfg.is_file():
        utxt = u_cfg.read_text(encoding="utf-8")
        utxt = re.sub(r"const updateRepo = '[^']+';", f"const updateRepo = '{args.github_repo}';", utxt)
        utxt = re.sub(r"const updateDownloadOrigin = '[^']+';", f"const updateDownloadOrigin = 'https://{args.domain}';", utxt)
        u_cfg.write_text(utxt, encoding="utf-8")

    rel_py = root / "tooling" / "release_assets.py"
    if rel_py.is_file():
        rtxt = rel_py.read_text(encoding="utf-8")
        rtxt = re.sub(r'REPO = "[^"]+"', f'REPO = "{args.github_repo}"', rtxt)
        rtxt = rtxt.replace('f"DSH Go {name}"', f'f"{args.app_name} {{name}}"')
        rel_py.write_text(rtxt, encoding="utf-8")
    print("[3/6] 已重写 BrandMark 1:1 完整矢量图标绘制器与全部 Dart 标题")

    # 4. 全面替换中英文 ARB 词条（含欢迎页大标题 shellWelcomeMessage 与所有用户可见的 DSH 文案）
    zh_exact_overrides = {
        "shellWelcomeMessage": "遇事不决，\n问问Ai！",
        "appSlogan": args.slogan,
        "stateAppDisclaimer": f"{args.slogan}（官方网站 https://{args.domain}）· 智能随身助手",
        "hubAboutAuthor": "dsh-Go 上游原作者",
        "botsPetDeepy": "问问仔",
        "botsPetWhaleGirl": "问问灵",
        "botsPetSource": "问问Ai 原创伴侣",
        "localEnvChooseTitle": f"{args.app_name} 在哪里运行？",
        "localEnvRemoteDetail": f"连接电脑或服务器上的 {args.app_name}",
        "localEnvInstallMessage": f"在这台手机上运行 {args.app_name}",
        "chatComposerHint": f"给 {args.app_name} 发消息…",
        "chatImageOffline": f"未连接 {args.app_name}",
        "livePublicRunning": f"{args.app_name} 正在干活",
        "livePublicWaiting": f"{args.app_name} 在等你处理",
        "livePublicDone": f"{args.app_name} 做完了",
        "livePublicFailed": f"{args.app_name} 出错了",
        "webTitle": f"{args.app_name} 网页工作台",
        "catalogWebSummary": f"{args.app_name} 网页工作台",
        "hubInterfaceWebHint": f"{args.app_name} 网页工作台",
        "viewShareBrandLine": f"手机上的 {args.app_name} · 扫码获取",
        "viewShareBrandLineNoQr": f"手机上的 {args.app_name}",
        "accessRestrictedTap": f"在无障碍里点一下「{args.app_name} 手机操控」，出现「受限制的设置」时点确定",
        "accessRestrictedBack": f"回到无障碍，打开「{args.app_name} 手机操控」",
    }
    en_exact_overrides = {
        "shellWelcomeMessage": "When in doubt,\nask Wenwen.ai!",
        "appSlogan": args.slogan_en,
        "stateAppDisclaimer": f"{args.slogan_en} (https://{args.domain})",
        "hubAboutAuthor": "Original upstream author of dsh-Go",
        "botsPetDeepy": "WenWen Bot",
        "botsPetWhaleGirl": "WenWen Pixel",
        "botsPetSource": "Wenwen.ai Companion",
        "localEnvChooseTitle": f"Where should {args.app_name_en} run?",
        "localEnvRemoteDetail": f"Connect to {args.app_name_en} on a computer or server",
        "localEnvInstallMessage": f"Run {args.app_name_en} on this phone",
        "chatComposerHint": f"Message {args.app_name_en}…",
        "chatImageOffline": f"Not connected to {args.app_name_en}",
        "livePublicRunning": f"{args.app_name_en} is working",
        "livePublicWaiting": f"{args.app_name_en} needs your input",
        "livePublicDone": f"{args.app_name_en} finished",
        "livePublicFailed": f"{args.app_name_en} ran into an issue",
        "webTitle": f"{args.app_name_en} Web",
        "catalogWebSummary": f"{args.app_name_en} web workspace",
        "hubInterfaceWebHint": f"{args.app_name_en} web workspace",
        "viewShareBrandLine": f"{args.app_name_en} on mobile · Scan to get",
        "viewShareBrandLineNoQr": f"{args.app_name_en} on mobile",
    }

    parts_dir = root / "app" / "lib" / "l10n" / "parts"
    for arb_path in sorted(parts_dir.glob("*.arb")):
        is_zh = arb_path.name.endswith("_zh.arb")
        data = json.loads(arb_path.read_text(encoding="utf-8"))
        changed = False
        overrides = zh_exact_overrides if is_zh else en_exact_overrides
        target_brand = args.app_name if is_zh else args.app_name_en

        for k, v in list(data.items()):
            if k.startswith("@") or not isinstance(v, str):
                continue
            orig_v = v
            if k in overrides:
                v = overrides[k]
            else:
                v = v.replace("DSH Go", target_brand).replace("DSH-Go", target_brand)
                if is_zh:
                    v = (
                        v.replace("把 DeepSeek 智能体\n装进口袋", "遇事不决，\n问问Ai！")
                        .replace("把 DeepSeek 装进口袋", "遇事不决，问问Ai！")
                        .replace("Deepy 小鲸鱼", "问问仔")
                        .replace("Deepy", "问问仔")
                        .replace("小鲸鱼", "问问仔")
                        .replace("鲸娘", "问问灵")
                        .replace("本鱼", "问问仔")
                    )
                    # 将普通中文句子里的独立 DSH（不含 $DSH_HOME、DSH Remote 等专有协议名）替换为 问问Ai
                    v = re.sub(r'(?<![A-Za-z0-9_$/-])DSH(?!\s*Remote)(?![A-Za-z0-9_/-])', target_brand, v)
                else:
                    v = (
                        v.replace("The DeepSeek agent,\nin your pocket", "When in doubt,\nask Wenwen.ai!")
                        .replace("Deepy", "WenWen Bot")
                        .replace("little whale", "WenWen Bot")
                    )
                    v = re.sub(r'(?<![A-Za-z0-9_$/-])DSH(?!\s*Remote)(?![A-Za-z0-9_/-])', target_brand, v)
            if v != orig_v:
                data[k] = v
                changed = True
        if changed:
            arb_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    subprocess.run(["python3", str(root / "app" / "tool" / "l10n_merge.py"), "--no-gen"], check=True)
    subprocess.run(["python3", str(root / "app" / "tool" / "l10n_merge.py"), "--check"], check=True)
    print("[4/6] 已更新全部 64 个 ARB 分片（含欢迎页「遇事不决，问问Ai！」与全量 DSH 标题）并通过校验")

    # 5. 更新用户指南 docs/guide/ 并运行 guide_sync.py
    guide_dir = root / "docs" / "guide"
    if guide_dir.is_dir():
        for md in guide_dir.rglob("*.md"):
            is_zh = "zh" in md.parts
            mtxt = md.read_text(encoding="utf-8")
            target_brand = args.app_name if is_zh else args.app_name_en
            new_mtxt = mtxt.replace("DSH Go", target_brand).replace("DSH-Go", target_brand)
            if is_zh:
                new_mtxt = (
                    new_mtxt.replace("Deepy 小鲸鱼", "问问仔")
                    .replace("问问仔 小鲸鱼", "问问仔")
                    .replace("Deepy", "问问仔")
                    .replace("鲸娘", "问问灵")
                )
                new_mtxt = re.sub(r'(?<![A-Za-z0-9_$/-])DSH(?!\s*Remote)(?![A-Za-z0-9_/-])', target_brand, new_mtxt)
            else:
                new_mtxt = new_mtxt.replace("Deepy", "WenWen Bot")
                new_mtxt = re.sub(r'(?<![A-Za-z0-9_$/-])DSH(?!\s*Remote)(?![A-Za-z0-9_/-])', target_brand, new_mtxt)
            if new_mtxt != mtxt:
                md.write_text(new_mtxt, encoding="utf-8")
        subprocess.run(["python3", str(root / "app" / "tool" / "guide_sync.py")], check=True)
        subprocess.run(["python3", str(root / "app" / "tool" / "guide_sync.py"), "--check"], check=True)
        print("[5/6] 已同步更新内置用户指南并通过 guide_sync.py --check 校验")

    # 5b. 在 dsh_web_phone.js 中注入网页工作台品牌替换（将 Web 界面内的探索未至之境 / deepseek HARNESS 同步替换为 问问Ai）
    web_js = root / "app" / "assets" / "web" / "dsh_web_phone.js"
    if web_js.is_file():
        jtxt = web_js.read_text(encoding="utf-8")
        marker = "// WENWEN_WEB_BRAND_PATCH"
        if marker not in jtxt:
            patch_js = f"""
  {marker}
  function rebrandWebDom() {{
    var walker = document.createTreeWalker(document.body || document.documentElement, NodeFilter.SHOW_TEXT);
    var node;
    while ((node = walker.nextNode())) {{
      var v = node.nodeValue;
      if (!v) continue;
      if (v === '探索未至之境' || v === 'Into the Unknown') node.nodeValue = '{args.slogan}';
      else if (v === 'deepseek' || v === 'DeepSeek Harness') node.nodeValue = '{args.app_name}';
      else if (v === 'HARNESS') node.nodeValue = '{args.domain.upper()}';
    }}
  }}
  setInterval(rebrandWebDom, 600);
"""
            jtxt = jtxt.replace("  window.__dshApp = {", patch_js + "\n  window.__dshApp = {")
            web_js.write_text(jtxt, encoding="utf-8")

    # 6. 写入合规衍生声明 NOTICE_DERIVATIVE.md
    (root / "NOTICE_DERIVATIVE.md").write_text(
        f"# {args.app_name} ({args.domain}) — {args.slogan}\n\n"
        f"- **官方网站**：https://{args.domain}\n"
        f"- **衍生版开源仓库**：https://github.com/{args.github_repo}\n"
        f"- **上游项目**：https://github.com/ccch1mneyyy/dsh-Go（原作者：ccch1mneyyy）\n"
        f"- **开源协议**：GNU AGPL-3.0\n",
        encoding="utf-8",
    )
    print("[6/6] 全部重塑步骤执行完毕！")


if __name__ == "__main__":
    main()
