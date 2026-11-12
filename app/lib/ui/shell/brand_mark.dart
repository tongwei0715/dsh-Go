import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';

import '../../state/app_info.dart';
import '../theme/theme.dart';
import 'brand_glyph.g.dart';

/// The dsh-go mark: a fish tail with its bubble.
///
/// Vector paths generated from the brand masters in `assets/brand/`
/// (`brand_glyph.g.dart`, by `tool/make_brand_mark.py`), in the launcher icon's
/// 108 grid, so the mark and the themed launcher layer
/// (`android/app/src/main/res/drawable/ic_launcher_monochrome.xml`) never drift
/// apart.
///
/// - By default the colour glyph: soft blue and lilac glass, one tuning for light
///   pages and one for dark, picked by the theme.
/// - [color]: one flat tint (a quiet footer, white on the poster card).
/// - [tile]: the launcher tile, the glyph on the icon's gradient rounded square.
class BrandMark extends StatelessWidget {
  const BrandMark({super.key, this.size = 28, this.color, this.tile = false});

  /// Height of the glyph (its width is [aspect] × this), or the side of the tile when
  /// [tile] is true.
  final double size;

  /// A flat tint instead of the colour glyph. Ignored on a tile.
  final Color? color;

  /// Draw the launcher tile (splash, about, update).
  final bool tile;

  /// Width / height of the glyph.
  static const aspect = BrandGlyph.aspect;

  /// The glyph's visual centre, the area centroid of its ink, as fractions of its
  /// width and height from the top left. A little below the box's centre: the body
  /// carries the weight.
  static final visualCentre = Offset(
    (BrandGlyph.centroid.dx - BrandGlyph.box.left) / BrandGlyph.box.width,
    (BrandGlyph.centroid.dy - BrandGlyph.box.top) / BrandGlyph.box.height,
  );

  /// How far to move a glyph of height [size] so its visual centre, not its box,
  /// sits on the centre of the space it is centred in.
  static Offset opticalShift(double size) =>
      Offset((0.5 - visualCentre.dx) * size * aspect, (0.5 - visualCentre.dy) * size);

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
        size: tile ? Size.square(size) : Size(size * aspect, size),
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

  @override
  bool shouldRepaint(_BrandPainter old) => old.style != style || old.color != color;
}

/// The glyph and a wordmark on one line.
///
/// Everything follows the word's size (0.95 × [height] by default, times the app's
/// text scale):
/// - the glyph is [glyphScale] × the word's size tall;
/// - its visual centre ([BrandMark.visualCentre]) sits on the centre of the word's
///   main band: the x-height for a lowercase word (「dsh-go」), the cap height for
///   capitals (「DSH」);
/// - [gapScale] × the word's size separates the glyph's ink from the word.
class BrandLockup extends StatelessWidget {
  const BrandLockup({
    super.key,
    this.height = 20,
    this.fontSize,
    this.label = AppInfo.wordmark,
    this.color,
    this.glyphColor,
  });

  /// The lockup's size; the word is set at 0.95 × this unless [fontSize] is given.
  final double height;

  /// The word's size, overriding the one derived from [height].
  final double? fontSize;

  final String label;

  /// The word's colour (default: onSurface).
  final Color? color;

  /// A flat glyph tint instead of the colour glyph.
  final Color? glyphColor;

  /// Glyph height / word size.
  static const glyphScale = 1.25;

  /// Gap between the glyph and the word / word size.
  static const gapScale = 0.36;

  /// x-height and cap height of the system sans, in ems (Roboto: 1082 and 1456 of
  /// 2048 units).
  static const xHeight = 0.528;
  static const capHeight = 0.711;

  /// Height above the baseline of the line the glyph centres on, for [label] set at
  /// [size].
  static double centreRise(String label, double size) =>
      (label.contains(RegExp('[a-z]')) ? xHeight : capHeight) * size / 2;

  /// Where the word starts, from the lockup's left edge, for a word drawn at [size]
  /// (after text scaling): glyph width + gap.
  static double wordInset(double size) => size * glyphScale * BrandMark.aspect + size * gapScale;

  double get _size => fontSize ?? height * 0.95;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    // The word's drawn size: the glyph and the gap scale with the text.
    final drawn = MediaQuery.textScalerOf(context).scale(_size);
    final glyph = drawn * glyphScale;
    return Row(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.baseline,
      textBaseline: TextBaseline.alphabetic,
      children: [
        _GlyphBaseline(
          // A baseline this far below the glyph's top puts its visual centre on the
          // word's x-height (or cap-height) centre when the row aligns baselines.
          baseline: glyph * BrandMark.visualCentre.dy + centreRise(label, drawn),
          child: BrandMark(size: glyph, color: glyphColor),
        ),
        SizedBox(width: drawn * gapScale),
        Text(
          label,
          style: AppType.wordmark(size: _size, color: color ?? scheme.onSurface),
        ),
      ],
    );
  }
}

/// Reports [baseline] as its child's alphabetic baseline.
class _GlyphBaseline extends SingleChildRenderObjectWidget {
  const _GlyphBaseline({required this.baseline, required super.child});

  final double baseline;

  @override
  RenderObject createRenderObject(BuildContext context) => _RenderGlyphBaseline(baseline);

  @override
  void updateRenderObject(BuildContext context, _RenderGlyphBaseline renderObject) {
    renderObject.baseline = baseline;
  }
}

class _RenderGlyphBaseline extends RenderProxyBox {
  _RenderGlyphBaseline(this._baseline);

  double _baseline;

  set baseline(double value) {
    if (value == _baseline) return;
    _baseline = value;
    markNeedsLayout();
  }

  @override
  double? computeDistanceToActualBaseline(TextBaseline baseline) => _baseline;

  @override
  double? computeDryBaseline(BoxConstraints constraints, TextBaseline baseline) => _baseline;
}
