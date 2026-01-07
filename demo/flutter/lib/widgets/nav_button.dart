import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

/// 侧边栏导航按钮
class NavButton extends StatefulWidget {
  final String icon;
  final String label;
  final bool isActive;
  final String? badge;
  final VoidCallback? onTap;

  const NavButton({
    super.key,
    required this.icon,
    required this.label,
    this.isActive = false,
    this.badge,
    this.onTap,
  });

  @override
  State<NavButton> createState() => _NavButtonState();
}

class _NavButtonState extends State<NavButton> {
  bool _isHovered = false;

  @override
  Widget build(BuildContext context) {
    final isHighlighted = widget.isActive || _isHovered;

    return MouseRegion(
      onEnter: (_) => setState(() => _isHovered = true),
      onExit: (_) => setState(() => _isHovered = false),
      cursor: SystemMouseCursors.click,
      child: GestureDetector(
        onTap: widget.onTap,
        child: AnimatedContainer(
          duration: AppTheme.durationFast,
          height: 44,
          decoration: BoxDecoration(
            color: isHighlighted
                ? AppTheme.primary.withOpacity(widget.isActive ? 0.15 : 0.1)
                : Colors.transparent,
            borderRadius: BorderRadius.circular(AppTheme.radiusMd),
            border: widget.isActive
                ? const Border(
                    left: BorderSide(color: AppTheme.primary, width: 3),
                  )
                : null,
          ),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: AppTheme.spacingLg),
            child: Row(
              children: [
                Text(
                  widget.icon,
                  style: const TextStyle(fontSize: 20),
                ),
                const SizedBox(width: AppTheme.spacingMd),
                Expanded(
                  child: Text(
                    widget.label,
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: widget.isActive ? FontWeight.w500 : FontWeight.normal,
                      color: widget.isActive
                          ? AppTheme.primaryLight
                          : (isHighlighted ? AppTheme.textPrimary : AppTheme.textSecondary),
                    ),
                  ),
                ),
                if (widget.badge != null)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(
                      color: AppTheme.primary,
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Text(
                      widget.badge!,
                      style: const TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.w500,
                        color: Colors.white,
                      ),
                    ),
                  ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

/// 导航分组标题
class NavSectionTitle extends StatelessWidget {
  final String title;

  const NavSectionTitle({
    super.key,
    required this.title,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(
        AppTheme.spacingLg,
        AppTheme.spacingLg,
        AppTheme.spacingLg,
        AppTheme.spacingSm,
      ),
      child: Text(
        title.toUpperCase(),
        style: const TextStyle(
          fontSize: 10,
          fontWeight: FontWeight.w500,
          letterSpacing: 1.5,
          color: AppTheme.textMuted,
        ),
      ),
    );
  }
}
