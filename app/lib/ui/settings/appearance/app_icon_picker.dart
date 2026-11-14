// Picks the launcher icon (桌面图标), for the appearance page. The icons
// themselves: android/app/src/main/res (ic_launcher_*).

import 'dart:async';
import 'dart:math' as math;
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../l10n/l10n.dart';
import '../../../state/app_icon_state.dart';
import '../../common/pressable.dart';
import '../../shell/brand_glyph.g.dart';
import '../../theme/theme.dart';
import '../../common/brief_notice.dart';

/// The four launcher icons in a row, drawn as the launcher draws them (the
/// system's icon mask), the one on the phone ringed in the accent:
///
/// ```
///   ╭───╮      ╭───╮      ╭───╮      ╭───╮
///  ( ◖● )     │ ◖● │     │ ◖● │     │ ◖● │    a ring [ringGap] off the chosen
///   ╰───╯      ╰───╯      ╰───╯      ╰───╯    icon, in the icon's own shape
///   雾蓝        夜幕        霜白         墨
/// ```
///
/// Equal columns [gap] apart, [padding] on every side; each icon is centred in
/// a square of [extent] (icon + ring room on every side), so choosing moves
/// nothing. Sits in a card (`SettingsSection`) or straight on a page.
class AppIconPicker extends ConsumerWidget {
  const AppIconPicker({super.key, this.padding = const EdgeInsets.all(16)});

  final EdgeInsetsGeometry padding;

  static const gap = 12.0;

  /// The ring round the chosen icon, and the space between it and the icon.
  static const ring = 2.0;
  static const ringGap = 3.0;

  /// Icons are at most this big (a launcher's own size), smaller in narrow columns.
  static const maxIcon = 56.0;

  /// Icon square to label.
  static const labelGap = 8.0;

  /// The icon's side in a column [width] wide.
  static double iconFor(double width) => math.min(maxIcon, width - 2 * (ring + ringGap));

  /// The square an icon of [icon] sits in, ring included.
  static double extent(double icon) => icon + 2 * (ring + ringGap);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(appIconProvider).value;
    return Padding(
      padding: padding,
      child: LayoutBuilder(
        builder: (context, constraints) {
          final column = (constraints.maxWidth - gap * (AppIcon.values.length - 1)) / AppIcon.values.length;
          final icon = iconFor(column);
          return Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              for (final (i, choice) in AppIcon.values.indexed) ...[
                if (i > 0) const SizedBox(width: gap),
                Expanded(
                  child: _Option(
                    icon: choice,
                    size: icon,
                    mask: state?.mask,
                    selected: state?.current == choice,
                    onTap: state == null || state.current == choice
                        ? null
                        : () => unawaited(_select(context, ref, choice)),
                  ),
                ),
              ],
            ],
          );
        },
      ),
    );
  }

  Future<void> _select(BuildContext context, WidgetRef ref, AppIcon icon) async {
    final l10n = context.l10n;
    final messenger = ScaffoldMessenger.maybeOf(context);
    final ok = await ref.read(appIconProvider.notifier).select(icon);
    if (ok) {
      messenger?.showBriefNotice(l10n.pluginsIconChanged);
    } else {
      messenger
        ?..hideCurrentSnackBar()
        ..showSnackBar(SnackBar(content: Text(l10n.pluginsIconChangeFailed)));
    }
  }
}

class _Option extends StatelessWidget {
  const _Option({
    required this.icon,
    required this.size,
    required this.mask,
    required this.selected,
    required this.onTap,
  });

  final AppIcon icon;
  final double size;
  final List<double>? mask;
  final bool selected;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;
    final duration = AppMotion.of(context, AppMotion.quick);
    return Semantics(
      selected: selected,
      inMutuallyExclusiveGroup: true,
      child: Pressable(
        // Even the chosen one gives feedback; it just has nothing to do.
        onTap: onTap ?? () {},
        haptic: onTap != null,
        semanticLabel: icon.label,
        child: Column(
          children: [
            TweenAnimationBuilder<double>(
              tween: Tween(end: selected ? 1 : 0),
              duration: duration,
              curve: AppMotion.std,
              builder: (context, t, child) => CustomPaint(
                key: ValueKey('app-icon-${icon.name}'),
                painter: _RingPainter(
                  mask: mask,
                  icon: size,
                  color: scheme.primary.withValues(alpha: t),
                ),
                child: child,
              ),
              child: SizedBox.square(
                dimension: AppIconPicker.extent(size),
                child: Center(
                  child: AppIconPreview(icon, size: size, mask: mask),
                ),
              ),
            ),
            const SizedBox(height: AppIconPicker.labelGap),
            AnimatedDefaultTextStyle(
              duration: duration,
              style: theme.textTheme.labelMedium!.copyWith(
                color: selected ? scheme.primary : scheme.onSurfaceVariant,
                fontWeight: selected ? FontWeight.w600 : FontWeight.w500,
              ),
              child: Text(icon.label, textAlign: TextAlign.center, maxLines: 1, overflow: TextOverflow.ellipsis),
            ),
          ],
        ),
      ),
    );
  }
}

/// The ring: the icon's own outline grown by [AppIconPicker.ringGap], centred
/// on the square the icon sits in.
class _RingPainter extends CustomPainter {
  const _RingPainter({required this.mask, required this.icon, required this.color});

  final List<double>? mask;
  final double icon;
  final Color color;

  @override
  void paint(Canvas canvas, Size size) {
    if (color.a == 0) return;
    final side = icon + 2 * AppIconPicker.ringGap + AppIconPicker.ring;
    final inset = (size.width - side) / 2;
    canvas.drawPath(
      launcherMaskPath(mask, side).shift(Offset(inset, (size.height - side) / 2)),
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = AppIconPicker.ring
        ..color = color,
    );
  }

  @override
  bool shouldRepaint(_RingPainter old) => old.color != color || old.icon != icon || old.mask != mask;
}

/// How each launcher icon is drawn: the gradient of its background layer
/// (`res/drawable/ic_launcher[_<name>]_background.xml`, the same diagonal for
/// all four) and its glyph.
class AppIconArt {
  const AppIconArt._(this.from, this.to, this.glyph, [this.mono]);

  /// Top-left and bottom-right of the background gradient.
  final Color from;
  final Color to;
  final AppIconGlyph glyph;

  /// The flat glyph colour, for [AppIconGlyph.mono].
  final Color? mono;

  /// The gradient's ends in the launcher's 108 grid (ic_launcher_background.xml).
  static const start = Offset(7.57, -5.87);
  static const end = Offset(100.43, 113.87);

  static AppIconArt of(AppIcon icon) => switch (icon) {
    // The default icon; on the phone its glyph is the original art, here the
    // brand master's glass (the same fit).
    AppIcon.mist => const AppIconArt._(Color(0xFF3B66FF), Color(0xFF1E40AF), AppIconGlyph.glassDark), Color(0xFF1D44DB), AppIconGlyph.glassDark),
    AppIcon.night => const AppIconArt._(Color(0xFF2C3D6C), Color(0xFF0C122D), AppIconGlyph.glassDark),
    AppIcon.frost => const AppIconArt._(Color(0xFFFCFDFF), Color(0xFFDDE5F8), AppIconGlyph.glassLight),
    AppIcon.ink => const AppIconArt._(Color(0xFF292B30), Color(0xFF0D0E11), AppIconGlyph.mono, Color(0xFFF5F7FB)),
  };
}

/// The brand glyph's three renderings (`assets/brand/glyph-*.svg`).
enum AppIconGlyph { glassDark, glassLight, mono }

/// [icon] as the launcher shows it: [size] square, cut to [mask] (an outline
/// in 0…1, see [AppIconState.mask]; a rounded square when null), with a
/// hairline inside its edge so the light icon keeps its shape on a light card.
class AppIconPreview extends StatelessWidget {
  const AppIconPreview(this.icon, {super.key, this.size = AppIconPicker.maxIcon, this.mask});

  final AppIcon icon;
  final double size;
  final List<double>? mask;

  @override
  Widget build(BuildContext context) => CustomPaint(
    size: Size.square(size),
    painter: _IconPainter(icon, mask, Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.08)),
  );
}

class _IconPainter extends CustomPainter {
  const _IconPainter(this.icon, this.mask, this.edge);

  final AppIcon icon;
  final List<double>? mask;
  final Color edge;

  @override
  void paint(Canvas canvas, Size size) {
    final art = AppIconArt.of(icon);
    final clip = launcherMaskPath(mask, size.width);
    canvas
      ..save()
      ..clipPath(clip)
      ..save()
      // The visible 72 of the 108 grid, as on the launcher.
      ..scale(size.width / 72)
      ..translate(-18, -18)
      ..drawRect(
        const Rect.fromLTWH(0, 0, 108, 108),
        Paint()..shader = ui.Gradient.linear(AppIconArt.start, AppIconArt.end, [art.from, art.to]),
      );
    // 绘制方案 C 的 4 款差异化桌面图标皮肤预览
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
    canvas
      ..restore()
      // Half of it falls outside the clip: a 1 px line just inside the edge.
      ..drawPath(
        clip,
        Paint()
          ..style = PaintingStyle.stroke
          ..strokeWidth = 2
          ..color = edge,
      )
      ..restore();
  }

  @override
  bool shouldRepaint(_IconPainter old) => old.icon != icon || old.mask != mask || old.edge != edge;
}

/// The launcher's icon shape at [side] × [side]: [mask] (a closed outline in
/// 0…1 from the system) or, without one, a rounded square.
Path launcherMaskPath(List<double>? mask, double side) {
  if (mask == null || mask.length < 6) {
    return RoundedSuperellipseBorder(borderRadius: BorderRadius.circular(side * 0.32))
        .getOuterPath(Rect.fromLTWH(0, 0, side, side));
  }
  final path = Path()..moveTo(mask[0] * side, mask[1] * side);
  for (var i = 2; i + 1 < mask.length; i += 2) {
    path.lineTo(mask[i] * side, mask[i + 1] * side);
  }
  return path..close();
}
