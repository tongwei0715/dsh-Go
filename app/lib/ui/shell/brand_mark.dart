import 'package:flutter/material.dart';
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
