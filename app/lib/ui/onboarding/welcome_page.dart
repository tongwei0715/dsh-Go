import 'package:flutter/material.dart';

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
              color: colors.textSecondary,
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
