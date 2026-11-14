#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
问问Ai (wenwenai.cn) — 针对 ccch1mneyyy/dsh-Go 的全方位品牌重塑、方案 C 四款高定图标与全量深度优化脚本
"""
import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw

# Android 13+ 主题图标矢量层 (方案 C：左上带横线提问气泡 + 右下带问号解答气泡)
MONOCHROME_XML = """<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp"
    android:height="108dp"
    android:viewportWidth="120"
    android:viewportHeight="120">
    <group android:translateX="15.6" android:translateY="15.6" android:scaleX="0.74" android:scaleY="0.74">
        <path android:fillColor="#FFFFFFFF" android:pathData="M24,37C24,29.82 29.82,24 37,24H61C68.18,24 74,29.82 74,37V49C74,56.18 68.18,62 61,62H37L26.5,70C25.2,71 24,70 24,68.4V37Z"/>
        <path android:fillColor="#CCFFFFFF" android:pathData="M46,56C46,48.82 51.82,43 59,43H83C90.18,43 96,48.82 96,56V70C96,77.18 90.18,83 83,83H82L91,91.5C92.2,92.6 90.5,94.2 89,93.4L74,83H59C51.82,83 46,77.18 46,70V56Z"/>
    </group>
</vector>
"""

IC_STAT_XML = """<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp"
    android:height="24dp"
    android:viewportWidth="120"
    android:viewportHeight="120">
    <path android:fillColor="#FFFFFFFF" android:pathData="M24,37C24,29.82 29.82,24 37,24H61C68.18,24 74,29.82 74,37V49C74,56.18 68.18,62 61,62H37L26.5,70C25.2,71 24,70 24,68.4V37Z"/>
    <path android:fillColor="#CCFFFFFF" android:pathData="M46,56C46,48.82 51.82,43 59,43H83C90.18,43 96,48.82 96,56V70C96,77.18 90.18,83 83,83H82L91,91.5C92.2,92.6 90.5,94.2 89,93.4L74,83H59C51.82,83 46,77.18 46,70V56Z"/>
</vector>
"""

# Flutter 内部 BrandMark 绘制器（方案 C：一问一答·对称叙事版，1:1 比例）
BRAND_MARK_DART = """import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';

import '../../state/app_info.dart';
import '../theme/theme.dart';
import 'brand_glyph.g.dart';

/// 问问Ai (wenwenai.cn) 方案 C 品牌图标组件（一问一答·对称叙事版，1:1 比例）。
class BrandMark extends StatelessWidget {
  const BrandMark({super.key, this.size = 28, this.color, this.tile = false});

  final double size;
  final Color? color;
  final bool tile;

  static const aspect = 1.0;
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
      final bgPaint = Paint()
        ..shader = ui.Gradient.linear(
          const Offset(0, 0),
          const Offset(120, 120),
          const [Color(0xFF3B66FF), Color(0xFF1E40AF)],
        );
      canvas.drawRRect(
        RRect.fromRectAndRadius(const Rect.fromLTWH(0, 0, 120, 120), const Radius.circular(28)),
        bgPaint,
      );
    }

    final Paint pLeft = style == _Style.mono
        ? (Paint()..color = color!)
        : (Paint()
          ..shader = ui.Gradient.linear(
            const Offset(24, 24),
            const Offset(74, 62),
            const [Color(0xFFFFD859), Color(0xFFF5B118)],
          ));
    final Paint pRight = Paint()
      ..color = style == _Style.mono ? color!.withValues(alpha: 0.88) : const Color(0xFFFFFFFF);

    // 1. 左上暖阳金提问气泡 + 圆润尾巴
    canvas.drawRRect(
      RRect.fromRectAndRadius(const Rect.fromLTWH(24, 24, 50, 38), const Radius.circular(13)),
      pLeft,
    );
    final tailLeft = Path()
      ..moveTo(24, 50)
      ..lineTo(39, 61)
      ..lineTo(25.5, 70)
      ..close();
    canvas.drawPath(tailLeft, pLeft);

    if (style != _Style.mono) {
      final linePaint = Paint()
        ..color = const Color(0xFF14213D)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 4.5
        ..strokeCap = StrokeCap.round;
      canvas.drawLine(const Offset(36, 39), const Offset(60, 39), linePaint);
      canvas.drawLine(const Offset(36, 48.5), const Offset(50, 48.5), linePaint);
    }

    // 2. 右下纯白解答气泡 + 圆润尾巴
    canvas.drawRRect(
      RRect.fromRectAndRadius(const Rect.fromLTWH(46, 43, 50, 40), const Radius.circular(13)),
      pRight,
    );
    final tailRight = Path()
      ..moveTo(74, 82)
      ..lineTo(85, 82)
      ..lineTo(90.5, 92.5)
      ..close();
    canvas.drawPath(tailRight, pRight);

    // 3. 右下气泡内居中电光蓝问号
    if (style != _Style.mono) {
      final qPaint = Paint()
        ..color = const Color(0xFF2F5BFF)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 5.0
        ..strokeCap = StrokeCap.round;
      final qPath = Path()
        ..moveTo(64.5, 57.5)
        ..cubicTo(64.5, 51.5, 77.5, 51.5, 77.5, 58.5)
        ..cubicTo(77.5, 63.2, 71.0, 63.5, 71.0, 68.5);
      canvas.drawPath(qPath, qPaint);
      canvas.drawCircle(const Offset(71.0, 75.8), 3.1, Paint()..color = const Color(0xFF2F5BFF));
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

CLEAN_WELCOME_PAGE_DART = """import 'package:flutter/material.dart';

import '../../l10n/l10n.dart';
import '../common/fade_in.dart';
import '../shell/brand_mark.dart';
import '../theme/theme.dart';
import 'onboarding_scaffold.dart';

/// 极简大厂风欢迎页：78dp 立体阴影图标 + 主副两行黄金层级标题 + 纯净底部主按钮（无重复口号、无统计开关杂音）。
class WelcomePage extends StatelessWidget {
  const WelcomePage({super.key, required this.onStart});

  final VoidCallback onStart;

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    final theme = Theme.of(context);
    final colors = DshColors.of(context);
    final isZh = Localizations.localeOf(context).languageCode.startsWith('zh');
    final subtitle = isZh ? '万物皆插件 · 住在你手机里的全能智能体' : 'Everything is a plugin · Your on-device AI agent';

    return OnboardingScaffold(
      children: [
        const Spacer(flex: 5),
        const Center(child: _BrandArrival()),
        const SizedBox(height: 30),
        FadeSlideIn(
          delay: const Duration(milliseconds: 180),
          child: Text(
            l10n.shellWelcomeMessage,
            textAlign: TextAlign.center,
            style: theme.textTheme.displaySmall?.copyWith(
              fontSize: 28,
              fontWeight: FontWeight.w700,
              letterSpacing: -0.4,
              height: 1.25,
            ),
          ),
        ),
        const SizedBox(height: 12),
        FadeSlideIn(
          delay: const Duration(milliseconds: 230),
          child: Text(
            subtitle,
            textAlign: TextAlign.center,
            style: theme.textTheme.bodyMedium?.copyWith(
              fontSize: 14.5,
              color: colors.textTertiary,
              height: 1.45,
            ),
          ),
        ),
        const Spacer(flex: 6),
        FadeSlideIn(
          delay: const Duration(milliseconds: 300),
          child: FilledButton(
            onPressed: onStart,
            child: Text(l10n.shellGetStarted),
          ),
        ),
        const SizedBox(height: 20),
      ],
    );
  }
}

class _BrandArrival extends StatefulWidget {
  const _BrandArrival();

  @override
  State<_BrandArrival> createState() => _BrandArrivalState();
}

class _BrandArrivalState extends State<_BrandArrival> with SingleTickerProviderStateMixin {
  late final AnimationController _arrive = AnimationController(vsync: this, duration: AppMotion.slow);
  late final Animation<double> _curve = CurvedAnimation(parent: _arrive, curve: AppMotion.enter);

  static const _mark = 78.0;
  static const _glow = 240.0;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (AppMotion.reduced(context)) {
      _arrive.value = 1;
    } else if (_arrive.isDismissed) {
      _arrive.forward();
    }
  }

  @override
  void dispose() {
    _arrive.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final dark = scheme.brightness == Brightness.dark;
    return SizedBox(
      width: _mark * BrandMark.aspect,
      height: _mark,
      child: AnimatedBuilder(
        animation: _curve,
        builder: (context, child) => Opacity(
          opacity: _curve.value,
          child: Transform.scale(scale: 0.92 + 0.08 * _curve.value, child: child),
        ),
        child: Stack(
          clipBehavior: Clip.none,
          alignment: Alignment.center,
          children: [
            Positioned.fill(
              child: OverflowBox(
                maxWidth: _glow,
                maxHeight: _glow,
                child: IgnorePointer(
                  child: SizedBox.square(
                    dimension: _glow,
                    child: DecoratedBox(
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        gradient: RadialGradient(
                          colors: [
                            scheme.primary.withValues(alpha: dark ? 0.24 : 0.16),
                            scheme.primary.withValues(alpha: 0),
                          ],
                        ),
                      ),
                    ),
                  ),
                ),
              ),
            ),
            DecoratedBox(
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(18),
                boxShadow: const [
                  BoxShadow(
                    color: Color(0x382F5BFF),
                    blurRadius: 28,
                    offset: Offset(0, 12),
                  ),
                ],
              ),
              child: const BrandMark(size: _mark, tile: true),
            ),
          ],
        ),
      ),
    );
  }
}
"""

CLEAN_ABOUT_PAGE_DART = """import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../l10n/l10n.dart';
import '../../state/app_info.dart';
import '../../state/star_prompt.dart' show starLinkOpenerProvider;
import '../../state/update_state.dart';
import '../shell/brand_mark.dart';
import '../shell/page_frame.dart';
import '../theme/app_icons.dart';
import '../theme/theme.dart';
import '../update/update_tiles.dart';
import 'settings_widgets.dart';

String installedVersionLabel(WidgetRef ref) {
  final installed = ref.watch(appUpdateProvider.select((s) => s.current));
  return installed.build == null ? installed.name : '${installed.name} (${installed.build})';
}

class AboutPage extends ConsumerWidget {
  const AboutPage({super.key});

  static final Uri _officialSite = Uri.parse('https://wenwenai.cn');

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = context.l10n;
    final theme = Theme.of(context);
    final colors = DshColors.of(context);
    final version = installedVersionLabel(ref);
    return AppPage.list(
      title: l10n.hubAbout,
      children: [
        SettingsSection(
          children: [
            SettingsTile(
              spot: Spots.version,
              value: Text(version, style: AppType.tabular(theme.textTheme.bodyMedium!)),
            ),
            const AppUpdateTiles(),
            SettingsTile(
              key: const ValueKey('about-official-website'),
              title: '官方网站',
              subtitle: 'https://wenwenai.cn',
              trailing: Icon(AppIcons.openExternal, size: 18, color: colors.textTertiary),
              onTap: () => unawaited(_openOfficialSite(context, ref)),
            ),
            SettingsTile(
              spot: Spots.licenses,
              onTap: () => showLicensePage(
                context: context,
                applicationName: AppInfo.name,
                applicationVersion: version,
                applicationIcon: const Padding(padding: EdgeInsets.all(12), child: BrandMark(size: 56, tile: true)),
                applicationLegalese: AppInfo.disclaimer,
              ),
            ),
          ],
        ),
        Padding(
          padding: const EdgeInsets.fromLTRB(24, 16, 24, 0),
          child: Column(
            children: [
              const BrandMark(size: 32, tile: true),
              const SizedBox(height: 12),
              Text(
                AppInfo.slogan,
                textAlign: TextAlign.center,
                style: theme.textTheme.labelSmall?.copyWith(color: colors.textTertiary),
              ),
              const SizedBox(height: 8),
              Text(
                AppInfo.disclaimer,
                textAlign: TextAlign.center,
                style: theme.textTheme.labelSmall?.copyWith(color: colors.textTertiary),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Future<void> _openOfficialSite(BuildContext context, WidgetRef ref) async {
    final l10n = context.l10n;
    final messenger = ScaffoldMessenger.maybeOf(context);
    try {
      if (await ref.read(starLinkOpenerProvider)(_officialSite)) return;
    } catch (_) {}
    var copied = true;
    try {
      await Clipboard.setData(ClipboardData(text: _officialSite.toString()));
    } catch (_) {
      copied = false;
    }
    if (messenger?.mounted ?? false) {
      messenger!.showSnackBar(
        SnackBar(content: Text(copied ? l10n.shellBrowserUrlCopied : _officialSite.toString())),
      );
    }
  }
}
"""

CLEAN_COMMUNITY_JSON = """{
  "schema": 1,
  "revision": 2,
  "updatedAt": "2026-11-14T00:00:00Z",
  "tagline": "遇事不决，问问Ai · 官方网站 wenwenai.cn",
  "plugins": [
    { "name": "@liustack/modsearch", "note": "免费的联网搜索" },
    { "name": "@liustack/modlens", "note": "让纯文本模型看懂图片" },
    { "name": "dsh-context", "note": "看清并管理上下文用量" },
    { "name": "@xmanrui/dsh-im", "note": "把飞书、微信、QQ 机器人接进 问问Ai" },
    { "name": "dsh-univer-office", "note": "表格和文档的办公环境" }
  ],
  "prompts": [
    {
      "title": "整理周报",
      "summary": "按提交记录写一份周报",
      "icon": "doc",
      "prompt": "看看工作区里最近一周的 Git 提交，按项目整理成一份周报：完成了什么、遇到的问题、下周计划。用 Markdown 输出。"
    },
    {
      "title": "读懂报错",
      "summary": "原因、修法和验证",
      "icon": "bug",
      "prompt": "我贴一段报错信息，帮我解释原因，给出最可能的修复办法，并说明怎么确认修好了。报错如下：\\n\\n"
    },
    {
      "title": "数据做成图表",
      "summary": "表格、合计和一张图",
      "icon": "chart",
      "prompt": "把我接下来给的数据整理成表格，算出合计和环比，再画一张合适的图表。数据如下：\\n\\n"
    },
    {
      "title": "两周入门一门语言",
      "summary": "按天的计划和练习",
      "icon": "school",
      "prompt": "我想在两周内入门 Rust。给我一份按天的学习计划，每天一个小练习，现在就带我做第一天的练习。"
    },
    {
      "title": "给项目写 README",
      "summary": "介绍、安装和用法",
      "icon": "code",
      "prompt": "读一下工作区里的项目，写一份 README：一句话介绍、功能、安装、使用示例和目录结构。"
    },
    {
      "title": "规划一次旅行",
      "summary": "三天行程和预算",
      "icon": "travel",
      "prompt": "帮我规划一次三天的杭州旅行：每天的路线、交通、吃什么，再估一份预算。我喜欢人少的地方。"
    }
  ],
  "groups": [],
  "updates": []
}
"""


def draw_round_line(draw, p1, p2, width, color):
    draw.line([p1, p2], fill=color, width=width)
    r = width / 2.0
    for x, y in (p1, p2):
        draw.ellipse([x - r, y - r, x + r, y + r], fill=color)


def cubic_bezier(p0, p1, p2, p3, steps=80):
    pts = []
    for i in range(steps + 1):
        t = i / steps
        mt = 1.0 - t
        x = (mt**3)*p0[0] + 3*(mt**2)*t*p1[0] + 3*mt*(t**2)*p2[0] + (t**3)*p3[0]
        y = (mt**3)*p0[1] + 3*(mt**2)*t*p1[1] + 3*mt*(t**2)*p2[1] + (t**3)*p3[1]
        pts.append((x, y))
    return pts


def draw_thick_curve(draw, pts, width, color):
    r = width / 2.0
    for i in range(len(pts) - 1):
        draw.line([pts[i], pts[i+1]], fill=color, width=int(round(width)))
    for x, y in pts:
        draw.ellipse([x - r, y - r, x + r, y + r], fill=color)


# 4 款高定桌面图标皮肤配色表 (mist=经典问问蓝, night=暗夜流金, frost=凝霜白玉, ink=水墨丹青)
ICON_VARIANTS = {
    "": {
        "bg1": (59, 102, 255),
        "bg2": (30, 64, 175),
        "left_bubble": (255, 204, 64, 255),
        "left_line": (20, 33, 61, 255),
        "right_bubble": (255, 255, 255, 255),
        "q_mark": (47, 91, 255, 255),
    },
    "_night": {
        "bg1": (23, 35, 68),
        "bg2": (10, 15, 32),
        "left_bubble": (255, 204, 64, 255),
        "left_line": (15, 23, 42, 255),
        "right_bubble": (232, 240, 255, 255),
        "q_mark": (47, 91, 255, 255),
    },
    "_frost": {
        "bg1": (250, 252, 255),
        "bg2": (219, 230, 250),
        "left_bubble": (47, 91, 255, 255),
        "left_line": (255, 255, 255, 255),
        "right_bubble": (255, 204, 64, 255),
        "q_mark": (20, 33, 61, 255),
    },
    "_ink": {
        "bg1": (39, 41, 48),
        "bg2": (14, 15, 19),
        "left_bubble": (255, 204, 64, 255),
        "left_line": (18, 19, 24, 255),
        "right_bubble": (245, 247, 251, 255),
        "q_mark": (24, 26, 32, 255),
    },
}


def render_scheme_c(size: int, with_bg: bool = True, circle_mask: bool = False, variant: str = "") -> Image.Image:
    """4x 超采样渲染方案 C 图标（支持 4 款差异化桌面图标皮肤）。"""
    pal = ICON_VARIANTS.get(variant, ICON_VARIANTS[""])
    SS = 4
    W = size * SS
    if not with_bg:
        scale = (W * 0.72) / 120.0
        ox = (W - 120.0 * scale) / 2.0
        oy = (W - 120.0 * scale) / 2.0
    else:
        scale = W / 120.0
        ox = 0.0
        oy = 0.0

    def tx(x): return ox + x * scale
    def ty(y): return oy + y * scale
    def tr(v): return v * scale

    img = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    if with_bg:
        c1_rgb, c2_rgb = pal["bg1"], pal["bg2"]
        bg = Image.new("RGBA", (W, W), (0, 0, 0, 0))
        bg_px = bg.load()
        for y in range(W):
            for x in range(W):
                t = (x + y) / (2.0 * W)
                r = int(round(c1_rgb[0] * (1 - t) + c2_rgb[0] * t))
                g = int(round(c1_rgb[1] * (1 - t) + c2_rgb[1] * t))
                b = int(round(c1_rgb[2] * (1 - t) + c2_rgb[2] * t))
                bg_px[x, y] = (r, g, b, 255)
        mask = Image.new("L", (W, W), 0)
        mdraw = ImageDraw.Draw(mask)
        if circle_mask:
            mdraw.ellipse([0, 0, W - 1, W - 1], fill=255)
        else:
            mdraw.rounded_rectangle([0, 0, W - 1, W - 1], radius=int(round(tr(26))), fill=255)
        img.paste(bg, (0, 0), mask)
        draw = ImageDraw.Draw(img)

    left_b = pal["left_bubble"]
    draw.rounded_rectangle([tx(24), ty(24), tx(74), ty(62)], radius=int(round(tr(13))), fill=left_b)
    draw.polygon([(tx(24), ty(50)), (tx(39), ty(61)), (tx(25), ty(70))], fill=left_b)
    draw.ellipse([tx(24), ty(67), tx(28), ty(71)], fill=left_b)

    line_c = pal["left_line"]
    lw = int(round(tr(4.6)))
    draw_round_line(draw, (tx(36), ty(39)), (tx(60), ty(39)), lw, line_c)
    draw_round_line(draw, (tx(36), ty(48.5)), (tx(50), ty(48.5)), lw, line_c)

    right_b = pal["right_bubble"]
    draw.rounded_rectangle([tx(46), ty(43), tx(96), ty(83)], radius=int(round(tr(13))), fill=right_b)
    draw.polygon([(tx(74), ty(82)), (tx(85), ty(82)), (tx(91), ty(92.5))], fill=right_b)
    draw.ellipse([tx(88), ty(90), tx(92.5), ty(94.5)], fill=right_b)

    qm_c = pal["q_mark"]
    qw = tr(5.0)
    c1 = cubic_bezier((tx(64.5), ty(57.5)), (tx(64.5), ty(51.5)), (tx(77.5), ty(51.5)), (tx(77.5), ty(58.5)))
    c2 = cubic_bezier((tx(77.5), ty(58.5)), (tx(77.5), ty(63.2)), (tx(71.0), ty(63.5)), (tx(71.0), ty(68.5)))
    draw_thick_curve(draw, c1 + c2, qw, qm_c)
    dr = tr(3.2)
    draw.ellipse([tx(71) - dr, ty(75.8) - dr, tx(71) + dr, ty(75.8) + dr], fill=qm_c)

    return img.resize((size, size), Image.Resampling.LANCZOS)


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

    wt_dart = repo_root / "app" / "lib" / "ui" / "chat" / "widgets" / "whale_tail.dart"
    if wt_dart.is_file():
        wtxt = wt_dart.read_text(encoding="utf-8")
        wtxt = re.sub(
            r'\.\.(?:colorFilter|color)\s*=[^\n]+',
            '..color = Color.fromRGBO(255, 255, 255, weight),',
            wtxt,
        )
        wt_dart.write_text(wtxt, encoding="utf-8")

    # 2️⃣ 新对话首页正中央的「问问仔」放大到 68dp 且全彩 100% 不透明
    es_dart = repo_root / "app" / "lib" / "ui" / "chat" / "empty_state.dart"
    if es_dart.is_file():
        etxt = es_dart.read_text(encoding="utf-8")
        etxt = etxt.replace("color: whaleColorFor(theme.brightness).withValues(alpha: 0.4),", "color: const Color(0xFFFFFFFF),")
        etxt = etxt.replace("color: Colors.white,", "color: const Color(0xFFFFFFFF),")
        etxt = re.sub(
            r"WhaleTail\(\s*still:\s*true,\s*height:\s*\d+(?:\.\d+)?,",
            "WhaleTail(\n                        still: true,\n                        height: 68,",
            etxt,
        )
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


def replace_android_icons(repo_root: Path) -> None:
    """3️⃣ 生成 4 款真正不同配色的桌面图标（经典问问蓝、暗夜流金、凝霜白玉、水墨丹青）。"""
    res_dir = repo_root / "app" / "android" / "app" / "src" / "main" / "res"
    densities = {
        "mipmap-mdpi": (48, 108),
        "mipmap-hdpi": (72, 162),
        "mipmap-xhdpi": (96, 216),
        "mipmap-xxhdpi": (144, 324),
        "mipmap-xxxhdpi": (192, 432),
    }
    for density, (launcher_px, fg_px) in densities.items():
        ddir = res_dir / density
        if not ddir.is_dir():
            continue
        for variant in ["", "_night", "_frost", "_ink"]:
            ic_main = render_scheme_c(launcher_px, with_bg=True, circle_mask=False, variant=variant)
            ic_round = render_scheme_c(launcher_px, with_bg=True, circle_mask=True, variant=variant)
            ic_fg = render_scheme_c(fg_px, with_bg=False, variant=variant)
            ic_main.save(ddir / f"ic_launcher{variant}.png", format="PNG", optimize=True)
            ic_round.save(ddir / f"ic_launcher{variant}_round.png", format="PNG", optimize=True)
            ic_fg.save(ddir / f"ic_launcher{variant}_foreground.png", format="PNG", optimize=True)

    drawable_dir = res_dir / "drawable"
    for bg_name, color in [
        ("ic_launcher_background.xml", "#2F5BFF"),
        ("ic_launcher_night_background.xml", "#141E3C"),
        ("ic_launcher_frost_background.xml", "#EEF4FF"),
        ("ic_launcher_ink_background.xml", "#16171C"),
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
    """将设置 -> 外观 -> 桌面图标选择器中的预览图同步支持 4 款差异化配色。"""
    picker = repo_root / "app" / "lib" / "ui" / "settings" / "appearance" / "app_icon_picker.dart"
    if not picker.is_file():
        return
    txt = picker.read_text(encoding="utf-8")
    txt = re.sub(
        r"AppIcon\.mist => const AppIconArt\._\([^)]+\),",
        "AppIcon.mist => const AppIconArt._(Color(0xFF3B66FF), Color(0xFF1E40AF), AppIconGlyph.glassDark),",
        txt,
    )
    new_painter_block = """    // 绘制方案 C 的 4 款差异化桌面图标皮肤预览
    final isFrost = icon == AppIcon.frost;
    final isInk = icon == AppIcon.ink;
    final leftColor = isFrost ? const Color(0xFF2F5BFF) : const Color(0xFFFFCC40);
    final lineColor = isFrost ? const Color(0xFFFFFFFF) : const Color(0xFF14213D);
    final rightColor = isFrost ? const Color(0xFFFFCC40) : const Color(0xFFFFFFFF);
    final qColor = isFrost
        ? const Color(0xFF14213D)
        : isInk
        ? const Color(0xFF181A20)
        : const Color(0xFF2F5BFF);
    final pLeft = Paint()..color = leftColor;
    canvas.drawRRect(RRect.fromRectAndRadius(const Rect.fromLTWH(28, 28, 30, 23), const Radius.circular(8)), pLeft);
    final lineP = Paint()..color = lineColor..style = PaintingStyle.stroke..strokeWidth = 2.8..strokeCap = StrokeCap.round;
    canvas.drawLine(const Offset(35, 37), const Offset(50, 37), lineP);
    canvas.drawLine(const Offset(35, 43), const Offset(44, 43), lineP);
    final pRight = Paint()..color = rightColor;
    canvas.drawRRect(RRect.fromRectAndRadius(const Rect.fromLTWH(44, 42, 32, 25), const Radius.circular(8)), pRight);
    final qPaint = Paint()..color = qColor..style = PaintingStyle.stroke..strokeWidth = 3.0..strokeCap = StrokeCap.round;
    final qPath = Path()..moveTo(56, 51)..cubicTo(56, 47, 64, 47, 64, 51.5)..cubicTo(64, 54.5, 60, 55, 60, 58);
    canvas.drawPath(qPath, qPaint);
    canvas.drawCircle(const Offset(60, 62.5), 1.9, Paint()..color = qColor);
"""
    txt = re.sub(
        r"    (?:switch \(art\.glyph\) \{|// 绘制).*?(?=    canvas\n      \.\.restore\(\))",
        new_painter_block,
        txt,
        flags=re.DOTALL,
    )
    picker.write_text(txt, encoding="utf-8")


def apply_deep_cleanups_and_1_to_6_enhancements(root: Path, args) -> None:
    """落实欢迎页重构、原作者净化 + 1～6 项深水区体验升级。"""
    # 0️⃣ 极简欢迎页 WelcomePage 与纯净 AboutPage
    (root / "app/lib/ui/onboarding/welcome_page.dart").write_text(CLEAN_WELCOME_PAGE_DART, encoding="utf-8")
    (root / "app/lib/ui/settings/about_page.dart").write_text(CLEAN_ABOUT_PAGE_DART, encoding="utf-8")

    # 1️⃣ 【视觉统一】将默认主题色 mist 升级为鲜亮明快的「问问蓝 (#2F5BFF)」
    acc_dart = root / "app/lib/ui/theme/accent.dart"
    if acc_dart.is_file():
        atxt = acc_dart.read_text(encoding="utf-8")
        new_mist = """  static const mist = AppAccent(
    id: 'mist',
    seed: Color(0xFF2F5BFF),
    pressed: Color(0xFF1E44D8),
    container: Color(0xFFDCE5FF),
    onContainer: Color(0xFF142868),
    bubble: Color(0xFFD8E3FF),
    glow: Color(0xFF9BB6FF),
    seedDark: Color(0xFF7B9CFF),
    pressedDark: Color(0xFF6488F5),
    onSeedDark: Color(0xFF0C1838),
    containerDark: Color(0xFF24366E),
    onContainerDark: Color(0xFFDCE5FF),
    bubbleDark: Color(0xFF222C4A),
    glowDark: Color(0xFF4262B8),
    tintHue: NeutralTones.baseHue,
    tintChroma: 1.05,
    haze: Color(0xFFFFEAB3),
    hazeDark: Color(0xFF4A412A),
  );"""
        atxt = re.sub(
            r"  static const mist = AppAccent\(.*?\n  \);",
            new_mist,
            atxt,
            flags=re.DOTALL,
        )
        acc_dart.write_text(atxt, encoding="utf-8")

    # 2️⃣ 永久关闭半小时求 Star 弹窗 & 净社区页 & 分享二维码指向官网 & 隐藏第三方署名
    sp_dart = root / "app/lib/state/star_prompt.dart"
    if sp_dart.is_file():
        stxt = sp_dart.read_text(encoding="utf-8")
        stxt = re.sub(
            r"final starPromptGateProvider = Provider<bool>\(\(ref\) => [^)]+\);",
            "final starPromptGateProvider = Provider<bool>((ref) => false);",
            stxt,
        )
        stxt = re.sub(
            r"final starProjectPage = Uri\.https\([^)]+\);",
            f"final starProjectPage = Uri.https('{args.domain}', '/');",
            stxt,
        )
        sp_dart.write_text(stxt, encoding="utf-8")

    fc_dart = root / "app/lib/ui/features/feature_catalog.dart"
    if fc_dart.is_file():
        ftxt = fc_dart.read_text(encoding="utf-8")
        ftxt = re.sub(
            r"Widget communityPage\(\) =>\s*\n?\s*Builder\([^\n]+;",
            "Widget communityPage() => const CommunityPage();",
            ftxt,
        )
        fc_dart.write_text(ftxt, encoding="utf-8")

    cs_dart = root / "app/lib/state/community_state.dart"
    if cs_dart.is_file():
        ctxt = cs_dart.read_text(encoding="utf-8")
        ctxt = re.sub(
            r"List<CommunitySource> defaultCommunitySources\(\) => \[[^\]]+\];",
            "List<CommunitySource> defaultCommunitySources() => const [];",
            ctxt,
            flags=re.DOTALL,
        )
        cs_dart.write_text(ctxt, encoding="utf-8")

    (root / "app/assets/community/community.json").write_text(CLEAN_COMMUNITY_JSON, encoding="utf-8")

    sc_dart = root / "app/lib/ui/share/share_content.dart"
    if sc_dart.is_file():
        sctxt = sc_dart.read_text(encoding="utf-8")
        sctxt = re.sub(
            r"const dshGoProjectUrl = '[^']+';",
            f"const dshGoProjectUrl = 'https://{args.domain}';",
            sctxt,
        )
        sc_dart.write_text(sctxt, encoding="utf-8")

    rv_dart = root / "app/lib/share_code/replay_viewer.g.dart"
    if rv_dart.is_file():
        rvtxt = rv_dart.read_text(encoding="utf-8")
        rvtxt = rvtxt.replace("https://github.com/ccch1mneyyy/dsh-go/releases/latest", f"https://{args.domain}")
        rv_dart.write_text(rvtxt, encoding="utf-8")

    fp_kt = root / "app/android/app/src/main/kotlin/io/github/ccch1mneyyy/dsh_app/files/FilesPlugin.kt"
    if fp_kt.is_file():
        fptxt = fp_kt.read_text(encoding="utf-8")
        fptxt = fptxt.replace('private const val SUBDIR = "DSH-Go"', 'private const val SUBDIR = "WenWenAi"')
        fp_kt.write_text(fptxt, encoding="utf-8")

    mp_kt = root / "app/android/app/src/main/kotlin/io/github/ccch1mneyyy/dsh_app/media/MediaPlugin.kt"
    if mp_kt.is_file():
        mptxt = mp_kt.read_text(encoding="utf-8")
        mptxt = mptxt.replace('"DSH_${System.currentTimeMillis()}', '"WenWen_${System.currentTimeMillis()}')
        mp_kt.write_text(mptxt, encoding="utf-8")

    art_dart = root / "app/lib/state/artifacts.dart"
    if art_dart.is_file():
        atxt = art_dart.read_text(encoding="utf-8")
        atxt = atxt.replace("Download/DSH-Go", "Download/WenWenAi")
        art_dart.write_text(atxt, encoding="utf-8")

    rc_dart = root / "app/lib/ui/remote/relay_credit.dart"
    if rc_dart.is_file():
        rctxt = rc_dart.read_text(encoding="utf-8")
        rctxt = re.sub(
            r"@override\s+Widget build\(BuildContext context\)\s*\{.*",
            "@override\n  Widget build(BuildContext context) => const SizedBox.shrink();\n}\n",
            rctxt,
            flags=re.DOTALL,
        )
        rc_dart.write_text(rctxt, encoding="utf-8")

    # 4️⃣ 【分享与唤醒协议】导出后缀改为 .wenwen，同时支持 wenwen:// 与 dshgo:// 唤醒协议
    sn_kt = root / "app/android/app/src/main/kotlin/io/github/ccch1mneyyy/dsh_app/share/ShareNames.kt"
    if sn_kt.is_file():
        sntxt = sn_kt.read_text(encoding="utf-8")
        sntxt = sntxt.replace('const val SHARE_CODE_EXTENSION = "dshgo"', 'const val SHARE_CODE_EXTENSION = "wenwen"')
        sn_kt.write_text(sntxt, encoding="utf-8")

    sc_codec = root / "app/lib/share_code/share_codec.dart"
    if sc_codec.is_file():
        codectxt = sc_codec.read_text(encoding="utf-8")
        codectxt = codectxt.replace("const shareFileExtension = 'dshgo';", "const shareFileExtension = 'wenwen';")
        sc_codec.write_text(codectxt, encoding="utf-8")

    so_dart = root / "app/lib/ui/share_code/share_out.dart"
    if so_dart.is_file():
        sotxt = so_dart.read_text(encoding="utf-8")
        sotxt = sotxt.replace("dsh-go-profile-", "wenwen-profile-").replace("dsh-go-plugin-", "wenwen-plugin-")
        so_dart.write_text(sotxt, encoding="utf-8")

    si_dart = root / "app/lib/links/share_intake.dart"
    if si_dart.is_file():
        sitxt = si_dart.read_text(encoding="utf-8")
        sitxt = sitxt.replace(
            "name.toLowerCase().endsWith('.$shareFileExtension')",
            "(name.toLowerCase().endsWith('.$shareFileExtension') || name.toLowerCase().endsWith('.dshgo'))",
        )
        si_dart.write_text(sitxt, encoding="utf-8")

    sch_dart = root / "app/lib/ui/share_code/share_code_host.dart"
    if sch_dart.is_file():
        schtxt = sch_dart.read_text(encoding="utf-8")
        if "registerFileHandler('dshgo'" not in schtxt:
            schtxt = schtxt.replace(
                "..add(router.registerFileHandler(shareFileExtension, _file));",
                "..add(router.registerFileHandler(shareFileExtension, _file))\n      ..add(router.registerFileHandler('dshgo', _file));",
            )
            sch_dart.write_text(schtxt, encoding="utf-8")

    lp_kt = root / "app/android/app/src/main/kotlin/io/github/ccch1mneyyy/dsh_app/links/LinksPlugin.kt"
    if lp_kt.is_file():
        lptxt = lp_kt.read_text(encoding="utf-8")
        lptxt = lptxt.replace(
            'SCHEME, "https", "http" -> deliver(mapOf("uri" to data.toString()))',
            'SCHEME, "wenwen", "https", "http" -> deliver(mapOf("uri" to data.toString().replaceFirst(Regex("^wenwen://"), "dshgo://")))',
        )
        lp_kt.write_text(lptxt, encoding="utf-8")

    manifest_xml = root / "app/android/app/src/main/AndroidManifest.xml"
    if manifest_xml.is_file():
        mtxt = manifest_xml.read_text(encoding="utf-8")
        if '<data android:scheme="wenwen" />' not in mtxt:
            mtxt = mtxt.replace(
                '<data android:scheme="dshgo" />',
                '<data android:scheme="dshgo" />\n                <data android:scheme="wenwen" />',
            )
            manifest_xml.write_text(mtxt, encoding="utf-8")

    # 5️⃣ 【内置终端体验】首次打开内置终端时打印彩色欢迎横幅
    ts_dart = root / "app/lib/state/terminal_state.dart"
    if ts_dart.is_file():
        tstxt = ts_dart.read_text(encoding="utf-8")
        old_emu = "    if (screen != null && screen.isNotEmpty) terminal.write(screen);"
        new_emu = (
            "    if (screen != null && screen.isNotEmpty) {\n"
            "      terminal.write(screen);\n"
            "    } else {\n"
            "      terminal.write('\\x1b[1;34m⚡ 问问Ai Linux Workstation\\x1b[0m \\x1b[33m(Ubuntu 24.04 · Node.js 24)\\x1b[0m — \\x1b[4;36mhttps://wenwenai.cn\\x1b[0m\\r\\n');\n"
            "    }"
        )
        if "问问Ai Linux Workstation" not in tstxt:
            tstxt = tstxt.replace(old_emu, new_emu)
            ts_dart.write_text(tstxt, encoding="utf-8")

    # 6️⃣ 【精简首次开机引导】跳过繁琐的「选外观」步骤，直接使用精心调校的问问蓝主题进入权限与连接步骤
    rg_dart = root / "app/lib/ui/shell/root_gate.dart"
    if rg_dart.is_file():
        rgtxt = rg_dart.read_text(encoding="utf-8")
        rgtxt = rgtxt.replace(
            "unawaited(_prefs.setSetupStep(SetupStep.appearance));\n    _startUnpack();\n    _goTo(OnboardingStep.appearance);",
            "unawaited(_prefs.setSetupStep(SetupStep.access));\n    _startUnpack();\n    _goTo(OnboardingStep.access);",
        )
        rg_dart.write_text(rgtxt, encoding="utf-8")

    ob_dart = root / "app/lib/ui/onboarding/onboarding_flow.dart"
    if ob_dart.is_file():
        obtxt = ob_dart.read_text(encoding="utf-8")
        obtxt = obtxt.replace(
            "? const [OnboardingStep.runtime, OnboardingStep.appearance, OnboardingStep.access, OnboardingStep.apiKey]",
            "? const [OnboardingStep.runtime, OnboardingStep.access, OnboardingStep.apiKey]",
        )
        ob_dart.write_text(obtxt, encoding="utf-8")


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

    # 2. 生成方案 C 的 4 款差异化桌面图标与问问仔精灵表 (68dp 首页高度)
    replace_android_icons(root)
    c1 = rebuild_pet_pack_sheets(root / "app" / "assets" / "pets" / "deepy-whale", pet_dir, "问问仔 · 活力版")
    c2 = rebuild_pet_pack_sheets(root / "app" / "assets" / "pets" / "whale-girl", pet_dir, "问问仔 · 乖巧版")
    rebuild_whale_and_widgets(root, pet_dir)
    print(f"[2/6] 已生成 4 款差异化方案 C 桌面图标皮肤并重绘 68dp 问问仔精灵表 ({c1}+{c2} 张)")

    # 3. 更新 AppInfo、BrandMark、AppIconPreview 与 1～6 项深水区升级
    app_info = root / "app" / "lib" / "state" / "app_info.dart"
    if app_info.is_file():
        itxt = app_info.read_text(encoding="utf-8")
        itxt = re.sub(r"static const name = '[^']+';", f"static const name = '{args.app_name}';", itxt)
        itxt = re.sub(r"static const wordmark = '[^']+';", f"static const wordmark = '{args.app_name}';", itxt)
        itxt = re.sub(r"static const author = '[^']+';", f"static const author = '{args.domain}';", itxt)
        itxt = re.sub(r"static const authorGithubUrl = '[^']+';", f"static const authorGithubUrl = 'https://{args.domain}';", itxt)
        app_info.write_text(itxt, encoding="utf-8")

    (root / "app" / "lib" / "ui" / "shell" / "brand_mark.dart").write_text(BRAND_MARK_DART, encoding="utf-8")
    patch_app_icon_picker(root)
    apply_deep_cleanups_and_1_to_6_enhancements(root, args)

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
    print("[3/6] 已完成鲜亮问问蓝主题、.wenwen 分享协议、终端欢迎栏与精简引导流")

    # 4. 全面替换中英文 ARB 词条（含 4 款图标皮肤命名与主题色命名）
    zh_exact_overrides = {
        "shellWelcomeMessage": "遇事不决，问问Ai",
        "appSlogan": args.slogan,
        "stateAppDisclaimer": f"{args.slogan}（官方网站 https://{args.domain}）",
        "hubAboutAuthor": "官方网站",
        "phoneAccentMist": "问问蓝",
        "pluginsIconMist": "问问蓝",
        "pluginsIconNight": "暗夜金",
        "pluginsIconFrost": "凝霜白",
        "pluginsIconInk": "水墨黑",
        "viewEmptySubtitle": "遇事不决，随时吩咐问问仔替你干活",
        "botsPetDeepy": "问问仔",
        "botsPetWhaleGirl": "问问灵",
        "botsPetSource": "问问Ai 原创伴侣",
        "botsOpenSource": f"官方网站 https://{args.domain}",
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
        "shellWelcomeMessage": "When in doubt, ask Wenwen.ai",
        "appSlogan": args.slogan_en,
        "stateAppDisclaimer": f"{args.slogan_en} (https://{args.domain})",
        "hubAboutAuthor": "Official Website",
        "phoneAccentMist": "WenWen Blue",
        "pluginsIconMist": "WenWen Blue",
        "pluginsIconNight": "Night Gold",
        "pluginsIconFrost": "Frost White",
        "pluginsIconInk": "Obsidian Ink",
        "viewEmptySubtitle": "When in doubt, let WenWen handle it for you",
        "botsPetDeepy": "WenWen Bot",
        "botsPetWhaleGirl": "WenWen Pixel",
        "botsPetSource": "Wenwen.ai Companion",
        "botsOpenSource": f"Official Website https://{args.domain}",
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
                v = (
                    v.replace("下载/DSH-Go", "下载/WenWenAi")
                    .replace("Download/DSH-Go", "Download/WenWenAi")
                    .replace(".dshgo", ".wenwen")
                    .replace("DSH Go", target_brand)
                    .replace("DSH-Go", target_brand)
                )
                if is_zh:
                    v = (
                        v.replace("把 DeepSeek 智能体\n装进口袋", "遇事不决，问问Ai")
                        .replace("把 DeepSeek 装进口袋", "遇事不决，问问Ai！")
                        .replace("Deepy 小鲸鱼", "问问仔")
                        .replace("Deepy", "问问仔")
                        .replace("小鲸鱼", "问问仔")
                        .replace("鲸娘", "问问灵")
                        .replace("本鱼", "问问仔")
                    )
                    v = re.sub(r'(?<![A-Za-z0-9_$/-])DSH(?!\s*Remote)(?![A-Za-z0-9_/-])', target_brand, v)
                else:
                    v = (
                        v.replace("The DeepSeek agent,\nin your pocket", "When in doubt, ask Wenwen.ai")
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
    print("[4/6] 已更新全部 65 个 ARB 分片并通过 l10n_merge.py --check 校验")

    # 5. 更新用户指南 docs/guide/ 并运行 guide_sync.py
    guide_dir = root / "docs" / "guide"
    if guide_dir.is_dir():
        for md in guide_dir.rglob("*.md"):
            is_zh = "zh" in md.parts
            mtxt = md.read_text(encoding="utf-8")
            target_brand = args.app_name if is_zh else args.app_name_en
            new_mtxt = (
                mtxt.replace("下载/DSH-Go", "下载/WenWenAi")
                .replace("Download/DSH-Go", "Download/WenWenAi")
                .replace("DSH Go", target_brand)
                .replace("DSH-Go", target_brand)
            )
            if is_zh:
                new_mtxt = (
                    new_mtxt.replace("Deepy 小鲸鱼", "问问仔")
                    .replace("问问仔 小鲸鱼", "问问仔")
                    .replace("Deepy", "问问仔")
                    .replace("鲸娘", "问问灵")
                    .replace("**雾蓝**", "**问问蓝**")
                )
                new_mtxt = re.sub(r'(?<![A-Za-z0-9_$/-])DSH(?!\s*Remote)(?![A-Za-z0-9_/-])', target_brand, new_mtxt)
            else:
                new_mtxt = new_mtxt.replace("Deepy", "WenWen Bot").replace("**Mist**", "**WenWen Blue**")
                new_mtxt = re.sub(r'(?<![A-Za-z0-9_$/-])DSH(?!\s*Remote)(?![A-Za-z0-9_/-])', target_brand, new_mtxt)
            if new_mtxt != mtxt:
                md.write_text(new_mtxt, encoding="utf-8")
        subprocess.run(["python3", str(root / "app" / "tool" / "guide_sync.py")], check=True)
        subprocess.run(["python3", str(root / "app" / "tool" / "guide_sync.py"), "--check"], check=True)
        print("[5/6] 已同步更新内置用户指南并通过 guide_sync.py --check 校验")

    # 5b. 网页工作台 DOM 巡检补丁
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

    # 6. 写入 NOTICE_DERIVATIVE.md
    (root / "NOTICE_DERIVATIVE.md").write_text(
        f"# {args.app_name} ({args.domain}) — {args.slogan}\n\n"
        f"- **官方网站**：https://{args.domain}\n"
        f"- **发布仓库**：https://github.com/{args.github_repo}\n",
        encoding="utf-8",
    )
    print("[6/6] 1～6 项深水区升级全部执行完毕！")


if __name__ == "__main__":
    main()
