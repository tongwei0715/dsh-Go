// The line under the DSH Remote card: who provides the service, with the
// upstream project as a link to its GitHub page.

import 'dart:async';
import 'dart:math' as math;
import 'dart:ui' as ui;

import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../l10n/l10n.dart';
import '../../state/app_info.dart';
import '../../state/star_prompt.dart' show starLinkOpenerProvider;
import '../settings/settings_widgets.dart';
import '../theme/app_icons.dart';

/// 「服务由 liguobao/ds-harness-remote 提供」. Only the project name and its
/// glyph open the project page, in the browser app as 给项目点 Star does
/// (signed in to GitHub there, a star is one tap away).
/// They take taps up to 48dp tall by reaching into the empty space above and
/// below their line: never into the card above, the next section or the rest
/// of the line.
///
/// The footer of a [SettingsSection] laid out with [sectionMargin]: the
/// credit carries the section's bottom margin itself, so the link can reach
/// into it while the page lays out exactly as with [kSettingsGroupMargin].
class RelayCredit extends ConsumerStatefulWidget {
  const RelayCredit({super.key, this.server});

  /// A self-hosted server, named after the credit.
  final String? server;

  /// The margin of the section this is the footer of.
  static final sectionMargin = kSettingsGroupMargin.copyWith(bottom: 0);

  @override
  ConsumerState<RelayCredit> createState() => _RelayCreditState();
}

class _RelayCreditState extends ConsumerState<RelayCredit> {
  late final _tap = TapGestureRecognizer()
    ..onTapDown = ((_) => _press(true))
    ..onTapCancel = (() => _press(false))
    ..onTap = () {
      _press(false);
      unawaited(_open());
    };
  bool _pressed = false;

  void _press(bool down) {
    if (mounted && _pressed != down) setState(() => _pressed = down);
  }

  /// No browser: the address goes to the clipboard and a line says so.
  Future<void> _open() async {
    final l10n = context.l10n;
    final messenger = ScaffoldMessenger.maybeOf(context);
    final url = Uri.parse(AppInfo.remoteProjectUrl);
    var opened = false;
    try {
      opened = await ref.read(starLinkOpenerProvider)(url);
    } catch (_) {
      // No browser: handled below.
    }
    if (opened) return;
    var copied = true;
    try {
      await Clipboard.setData(ClipboardData(text: url.toString()));
    } catch (_) {
      copied = false;
    }
    messenger?.showSnackBar(SnackBar(content: Text(copied ? l10n.shellBrowserUrlCopied : l10n.stateBrowserOpenFailed)));
  }

  @override
  void dispose() {
    _tap.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => const SizedBox.shrink();
}
