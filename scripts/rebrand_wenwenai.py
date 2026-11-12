#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
问问Ai (wenwenai.cn) — 针对 ccch1mneyyy/dsh-Go 的幂等品牌重塑、像素桌宠精灵表生成与更新源绑定脚本
"""
import argparse
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from PIL import Image


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
    """将 256x256 的问问仔像素图按整数/最近邻缩放居中放入 (cell_w, cell_h) 帧格内，带 dy 呼吸位移。"""
    cell = Image.new("RGBA", (cell_w, cell_h), (0, 0, 0, 0))
    # 留出上下 4px 呼吸空间
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
    """按照 pack.json 中每个动画的精确 frameW, frameH, cols 与原图尺寸重新生成多帧像素精灵表。"""
    pack_file = pack_dir / "pack.json"
    if not pack_file.is_file():
        return 0
    pack = json.loads(pack_file.read_text(encoding="utf-8"))
    pack["name"] = new_name
    pack["author"] = "wenwenai.cn"
    pack["license"] = "问问Ai (wenwenai.cn) 原创像素桌宠"
    pack["source"] = "wenwenai.cn"
    pack_file.write_text(json.dumps(pack, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # 收集每个 sheet 对应的 (frameW, frameH, cols)
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
                    # 轻微上下像素律动 (-1, 0, +1, 0)
                    dy = (-1, 0, 1, 0)[idx % 4]
                    cell = render_cell(pet_img, fw, fh, dy=dy)
                    new_sheet.alpha_composite(cell, (c * fw, r * fh))
                    idx += 1
            new_sheet.save(sheet_path, format="PNG", optimize=True)
            count += 1
    return count


def rebuild_whale_and_widgets(repo_root: Path, pet_src_dir: Path) -> None:
    """替换 app/assets/whale/whale_1..4.png、star_whale.webp 与 Android 桌面小组件贴图。"""
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
            src_png = pet_src_dir / ("pet_sleeping.png" if level["level"] == 1 else "pet_working.png")
            with Image.open(src_png).convert("RGBA") as pet_img:
                sheet = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
                rows = max(1, sh // fh)
                for r in range(rows):
                    for c in range(min(cols, sw // fw)):
                        dy = (-1, 0, 1, 0)[(r * cols + c) % 4]
                        cell = render_cell(pet_img, fw, fh, dy=dy)
                        sheet.alpha_composite(cell, (c * fw, r * fh))
                sheet.save(img_path, format="PNG", optimize=True)

    # 替换 star_whale.webp
    star_webp = repo_root / "app" / "assets" / "star" / "star_whale.webp"
    if star_webp.is_file():
        with Image.open(pet_src_dir / "pet_completed.png").convert("RGBA") as img:
            img.save(star_webp, format="WEBP", lossless=True)

    # 替换 Android 小组件贴图 companion_widget_*.png (240x240)
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
    """将全套 mipmap 图标（含默认、night、frost、ink 四套别名）统一替换为问问Ai蓝黄图标。"""
    res_dir = repo_root / "app" / "android" / "app" / "src" / "main" / "res"
    src_res = assets_dir / "android_res"
    for density in ["mipmap-mdpi", "mipmap-hdpi", "mipmap-xhdpi", "mipmap-xxhdpi", "mipmap-xxxhdpi"]:
        sdir = src_res / density
        ddir = res_dir / density
        if not sdir.is_dir() or not ddir.is_dir():
            continue
        ic_main = sdir / "ic_launcher.png"
        ic_round = sdir / "ic_launcher_round.png"
        ic_fg = sdir / "ic_launcher_foreground.png"
        for variant in ["", "_night", "_frost", "_ink"]:
            if ic_main.is_file():
                shutil.copy2(ic_main, ddir / f"ic_launcher{variant}.png")
            if ic_round.is_file():
                shutil.copy2(ic_round, ddir / f"ic_launcher{variant}_round.png")
            if ic_fg.is_file():
                shutil.copy2(ic_fg, ddir / f"ic_launcher{variant}_foreground.png")

    # 统一自适应图标背景色为 #2F5BFF（暗夜版 #14213D）
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


def patch_brand_mark_dart(repo_root: Path) -> None:
    """将 Flutter 内的 BrandMark 绘制逻辑替换为问问Ai双色对话气泡矢量绘制。"""
    bm_path = repo_root / "app" / "lib" / "ui" / "shell" / "brand_mark.dart"
    if not bm_path.is_file():
        return
    txt = bm_path.read_text(encoding="utf-8")
    old_paint_start = txt.index("  @override\n  void paint(Canvas canvas, Size size) {")
    old_paint_end = txt.index("  @override\n  bool shouldRepaint")
    new_paint = """  @override
  void paint(Canvas canvas, Size size) {
    canvas.save();
    // 问问Ai 120x120 矢量网格绘制
    final scaleX = size.width / 120.0;
    final scaleY = size.height / 120.0;
    canvas.scale(scaleX, scaleY);

    if (style == _Style.tile) {
      final bgPaint = Paint()..color = const Color(0xFF2F5BFF);
      canvas.drawRRect(RRect.fromRectAndRadius(const Rect.fromLTWH(0, 0, 120, 120), const Radius.circular(28)), bgPaint);
    }

    final Color leftColor = style == _Style.mono ? color! : const Color(0xFFFFC93C);
    final Color rightColor = style == _Style.mono
        ? color!.withValues(alpha: 0.85)
        : (style == _Style.light && ! (style == _Style.tile) ? const Color(0xFF2F5BFF) : const Color(0xFFFFFFFF));
    final Color qColor = style == _Style.mono
        ? const Color(0xFF000000)
        : (rightColor == const Color(0xFFFFFFFF) ? const Color(0xFF2F5BFF) : const Color(0xFFFFFFFF));

    // 左上黄色气泡
    final pLeft = Paint()..color = leftColor;
    canvas.drawRRect(RRect.fromRectAndRadius(const Rect.fromLTWH(18, 20, 58, 46), const Radius.circular(16)), pLeft);
    final tailLeft = Path()..moveTo(26, 62)..lineTo(40, 62)..lineTo(24, 78)..close();
    canvas.drawPath(tailLeft, pLeft);

    // 右下气泡
    final pRight = Paint()..color = rightColor;
    canvas.drawRRect(RRect.fromRectAndRadius(const Rect.fromLTWH(40, 44, 62, 48), const Radius.circular(17)), pRight);
    final tailRight = Path()..moveTo(72, 90)..lineTo(92, 90)..lineTo(94, 106)..close();
    canvas.drawPath(tailRight, pRight);

    // 问号与圆点
    final qPaint = Paint()
      ..color = qColor
      ..style = PaintingStyle.stroke
      ..strokeWidth = 5.5
      ..strokeCap = StrokeCap.round;
    final qPath = Path()
      ..moveTo(62, 62)
      ..cubicTo(62, 54, 80, 54, 80, 63)
      ..cubicTo(80, 70, 71, 70, 71, 76);
    canvas.drawPath(qPath, qPaint);
    canvas.drawCircle(const Offset(71, 85), 3.4, Paint()..color = qColor);

    // 右上角 AI 胶囊徽章
    if (style != _Style.mono) {
      canvas.drawRRect(RRect.fromRectAndRadius(const Rect.fromLTWH(74, 12, 36, 22), const Radius.circular(11)), Paint()..color = const Color(0xFF14213D));
      canvas.drawCircle(const Offset(99.5, 14.8), 1.8, Paint()..color = const Color(0xFFFFC93C));
    }
    canvas.restore();
  }

"""
    txt = txt[:old_paint_start] + new_paint + txt[old_paint_end:]
    bm_path.write_text(txt, encoding="utf-8")


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

    # 1. 修改 Gradle applicationId 与 AndroidManifest.xml / Android strings
    gradle_kts = root / "app" / "android" / "app" / "build.gradle.kts"
    if gradle_kts.is_file():
        gtxt = gradle_kts.read_text(encoding="utf-8")
        gtxt = re.sub(r'applicationId\s*=\s*"[^"]+"', f'applicationId = "{args.app_id}"', gtxt)
        gradle_kts.write_text(gtxt, encoding="utf-8")
        print(f"[1/6] 已更新 build.gradle.kts applicationId = {args.app_id}")

    manifest_xml = root / "app" / "android" / "app" / "src" / "main" / "AndroidManifest.xml"
    if manifest_xml.is_file():
        mtxt = manifest_xml.read_text(encoding="utf-8")
        mtxt = re.sub(r'android:label="[^"]+"', f'android:label="{args.app_name}"', mtxt, count=1)
        manifest_xml.write_text(mtxt, encoding="utf-8")

    res_dir = root / "app" / "android" / "app" / "src" / "main" / "res"
    for xml_f in res_dir.rglob("*.xml"):
        if xml_f.parent.name.startswith("values"):
            xtxt = xml_f.read_text(encoding="utf-8")
            rep = args.app_name if "zh" in xml_f.parent.name else args.app_name_en
            new_xtxt = xtxt.replace("DSH Go", rep)
            if new_xtxt != xtxt:
                xml_f.write_text(new_xtxt, encoding="utf-8")

    # 2. 替换 Android 启动图标与生成问问仔多帧像素精灵表
    replace_android_icons(root, assets)
    c1 = rebuild_pet_pack_sheets(root / "app" / "assets" / "pets" / "deepy-whale", pet_dir, "问问仔")
    c2 = rebuild_pet_pack_sheets(root / "app" / "assets" / "pets" / "whale-girl", pet_dir, "问问灵")
    rebuild_whale_and_widgets(root, pet_dir)
    print(f"[2/6] 已重绘问问仔多帧像素精灵表 (deepy-whale: {c1} 张, whale-girl: {c2} 张) 与全套 Android 图标")

    # 3. 更新 AppInfo、BrandMark 与自动更新配置 update_config.dart / release.dart / release_assets.py
    app_info = root / "app" / "lib" / "state" / "app_info.dart"
    if app_info.is_file():
        itxt = app_info.read_text(encoding="utf-8")
        itxt = re.sub(r"static const name = '[^']+';", f"static const name = '{args.app_name}';", itxt)
        itxt = re.sub(r"static const wordmark = '[^']+';", f"static const wordmark = '{args.app_name}';", itxt)
        app_info.write_text(itxt, encoding="utf-8")

    patch_brand_mark_dart(root)

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
    print(f"[3/6] 已更新 AppInfo、BrandMark 矢量绘制与更新源 ({args.github_repo} + https://{args.domain})")

    # 4. 更新双语 ARB 词条并运行 l10n_merge.py
    parts_dir = root / "app" / "lib" / "l10n" / "parts"
    for arb_path in sorted(parts_dir.glob("*.arb")):
        is_zh = arb_path.name.endswith("_zh.arb")
        data = json.loads(arb_path.read_text(encoding="utf-8"))
        changed = False
        for k, v in list(data.items()):
            if k.startswith("@") or not isinstance(v, str):
                continue
            orig_v = v
            if k == "appSlogan":
                v = args.slogan if is_zh else args.slogan_en
            elif k == "stateAppDisclaimer":
                v = f"{args.slogan}（官方网站 https://{args.domain}）· 基于 DeepSeek Harness 构建" if is_zh else f"{args.slogan_en} (https://{args.domain}) · Built on DeepSeek Harness"
            elif k == "hubAboutAuthor":
                # 保留原作者致谢条目清晰度
                v = "dsh-Go 上游原作者" if is_zh else "Original upstream author of dsh-Go"
            elif k == "botsPetDeepy":
                v = "问问仔" if is_zh else "WenWen Bot"
            elif k == "botsPetWhaleGirl":
                v = "问问灵" if is_zh else "WenWen Pixel"
            else:
                v = v.replace("DSH Go", args.app_name if is_zh else args.app_name_en)
                if is_zh:
                    v = v.replace("Deepy 小鲸鱼", "问问仔").replace("Deepy", "问问仔").replace("鲸娘", "问问灵").replace("本鱼", "问问仔")
                else:
                    v = v.replace("Deepy", "WenWen Bot").replace("little whale", "WenWen Bot")
            if v != orig_v:
                data[k] = v
                changed = True
        if changed:
            arb_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # 运行 l10n_merge.py --no-gen 合并 ARB，并同步更新 gen/app_localizations*.dart
    subprocess.run(["python3", str(root / "app" / "tool" / "l10n_merge.py"), "--no-gen"], check=True)
    for gen_dart in (root / "app" / "lib" / "l10n" / "gen").glob("app_localizations_*.dart"):
        is_zh = gen_dart.name.endswith("_zh.dart")
        gtxt = gen_dart.read_text(encoding="utf-8")
        if is_zh:
            gtxt = gtxt.replace("随时随刻，想go就Go！", args.slogan)
            gtxt = gtxt.replace("基于 DeepSeek Harness 构建 · 非 DeepSeek 官方应用", f"{args.slogan}（官方网站 https://{args.domain}）· 基于 DeepSeek Harness 构建")
            gtxt = gtxt.replace("DSH Go 原作者", "dsh-Go 上游原作者")
            gtxt = gtxt.replace("DSH Go", args.app_name).replace("Deepy 小鲸鱼", "问问仔").replace("Deepy", "问问仔").replace("鲸娘", "问问灵").replace("本鱼", "问问仔")
        else:
            gtxt = gtxt.replace("Anytime, anywhere. Just Go!", args.slogan_en)
            gtxt = gtxt.replace("Built on DeepSeek Harness · Unofficial DeepSeek app", f"{args.slogan_en} (https://{args.domain}) · Built on DeepSeek Harness")
            gtxt = gtxt.replace("Original author of DSH Go", "Original upstream author of dsh-Go")
            gtxt = gtxt.replace("DSH Go", args.app_name_en).replace("Deepy", "WenWen Bot")
        gen_dart.write_text(gtxt, encoding="utf-8")
    subprocess.run(["python3", str(root / "app" / "tool" / "l10n_merge.py"), "--check"], check=True)
    print("[4/6] 已更新中英文 ARB 词条与 app_localizations*.dart 并通过 l10n_merge.py --check 校验")

    # 5. 更新用户指南 docs/guide/ 并运行 guide_sync.py
    guide_dir = root / "docs" / "guide"
    if guide_dir.is_dir():
        for md in guide_dir.rglob("*.md"):
            is_zh = "zh" in md.parts
            mtxt = md.read_text(encoding="utf-8")
            new_mtxt = mtxt.replace("DSH Go", args.app_name if is_zh else args.app_name_en)
            if is_zh:
                new_mtxt = new_mtxt.replace("Deepy 小鲸鱼", "问问仔").replace("问问仔 小鲸鱼", "问问仔").replace("Deepy", "问问仔").replace("鲸娘", "问问灵")
            else:
                new_mtxt = new_mtxt.replace("Deepy", "WenWen Bot")
            if new_mtxt != mtxt:
                md.write_text(new_mtxt, encoding="utf-8")
        subprocess.run(["python3", str(root / "app" / "tool" / "guide_sync.py")], check=True)
        subprocess.run(["python3", str(root / "app" / "tool" / "guide_sync.py"), "--check"], check=True)
        print("[5/6] 已同步更新内置用户指南并通过 guide_sync.py --check 校验")

    # 6. 写入 AGPL-3.0 合规衍生声明 NOTICE_DERIVATIVE.md
    (root / "NOTICE_DERIVATIVE.md").write_text(
        f"# {args.app_name} ({args.domain}) — {args.slogan}\n\n"
        f"- **官方网站**：https://{args.domain}\n"
        f"- **衍生版开源仓库**：https://github.com/{args.github_repo}\n"
        f"- **上游项目**：https://github.com/ccch1mneyyy/dsh-Go（原作者：ccch1mneyyy）\n"
        f"- **开源协议**：GNU AGPL-3.0\n\n"
        f"本版本遵照上游 AGPL-3.0 协议与 ASSETS.md 要求，已将原版受限的品牌标识与 Deepy/鲸娘吉祥物素材全面替换为「{args.app_name}」与「问问仔」原创资产，并完整公开衍生源码与自动化构建脚本。\n",
        encoding="utf-8",
    )
    print("[6/6] 已生成 AGPL-3.0 合规声明文件 NOTICE_DERIVATIVE.md")


if __name__ == "__main__":
    main()
