import 'dart:ui' as ui;
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
