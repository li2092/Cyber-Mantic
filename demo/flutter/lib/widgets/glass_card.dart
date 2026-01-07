import 'dart:ui';
import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

/// 玻璃拟态卡片组件
class GlassCard extends StatefulWidget {
  final Widget child;
  final String? title;
  final Widget? titleWidget;
  final Widget? trailing;
  final EdgeInsetsGeometry? padding;
  final EdgeInsetsGeometry? margin;
  final double? width;
  final double? height;
  final bool enableHover;
  final VoidCallback? onTap;

  const GlassCard({
    super.key,
    required this.child,
    this.title,
    this.titleWidget,
    this.trailing,
    this.padding,
    this.margin,
    this.width,
    this.height,
    this.enableHover = true,
    this.onTap,
  });

  @override
  State<GlassCard> createState() => _GlassCardState();
}

class _GlassCardState extends State<GlassCard> {
  bool _isHovered = false;

  @override
  Widget build(BuildContext context) {
    return MouseRegion(
      onEnter: widget.enableHover ? (_) => setState(() => _isHovered = true) : null,
      onExit: widget.enableHover ? (_) => setState(() => _isHovered = false) : null,
      child: GestureDetector(
        onTap: widget.onTap,
        child: AnimatedContainer(
          duration: AppTheme.durationNormal,
          curve: Curves.easeOut,
          width: widget.width,
          height: widget.height,
          margin: widget.margin,
          transform: _isHovered
              ? (Matrix4.identity()..translate(0.0, -4.0))
              : Matrix4.identity(),
          decoration: BoxDecoration(
            color: AppTheme.bgCard,
            borderRadius: BorderRadius.circular(AppTheme.radiusLg),
            border: Border.all(
              color: _isHovered ? AppTheme.primary.withOpacity(0.3) : AppTheme.glassBorder,
              width: 1,
            ),
            boxShadow: _isHovered ? AppTheme.cardShadow : null,
          ),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(AppTheme.radiusLg),
            child: BackdropFilter(
              filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  if (widget.title != null || widget.titleWidget != null)
                    _buildHeader(),
                  Flexible(
                    child: Padding(
                      padding: widget.padding ?? const EdgeInsets.all(AppTheme.spacingXl),
                      child: widget.child,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppTheme.spacingXl,
        vertical: AppTheme.spacingLg,
      ),
      decoration: const BoxDecoration(
        border: Border(
          bottom: BorderSide(color: AppTheme.border),
        ),
      ),
      child: Row(
        children: [
          if (widget.titleWidget != null)
            widget.titleWidget!
          else
            Text(
              widget.title!,
              style: const TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w500,
                color: AppTheme.textPrimary,
              ),
            ),
          const Spacer(),
          if (widget.trailing != null) widget.trailing!,
        ],
      ),
    );
  }
}

/// 统计卡片组件
class StatCard extends StatefulWidget {
  final String icon;
  final String value;
  final String label;
  final String? trend;
  final bool trendUp;
  final Color? iconBgColor;
  final Color? iconColor;

  const StatCard({
    super.key,
    required this.icon,
    required this.value,
    required this.label,
    this.trend,
    this.trendUp = true,
    this.iconBgColor,
    this.iconColor,
  });

  @override
  State<StatCard> createState() => _StatCardState();
}

class _StatCardState extends State<StatCard> {
  bool _isHovered = false;

  @override
  Widget build(BuildContext context) {
    return MouseRegion(
      onEnter: (_) => setState(() => _isHovered = true),
      onExit: (_) => setState(() => _isHovered = false),
      cursor: SystemMouseCursors.click,
      child: AnimatedContainer(
        duration: AppTheme.durationNormal,
        curve: Curves.easeOut,
        padding: const EdgeInsets.all(AppTheme.spacingXl),
        transform: _isHovered
            ? (Matrix4.identity()..translate(0.0, -4.0))
            : Matrix4.identity(),
        decoration: BoxDecoration(
          color: _isHovered ? AppTheme.bgTertiary.withOpacity(0.8) : AppTheme.bgCard,
          borderRadius: BorderRadius.circular(AppTheme.radiusLg),
          border: Border.all(
            color: _isHovered ? AppTheme.primary : AppTheme.glassBorder,
            width: 1,
          ),
          boxShadow: _isHovered ? AppTheme.cardShadow : null,
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 头部：图标和趋势
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Container(
                  width: 48,
                  height: 48,
                  decoration: BoxDecoration(
                    color: widget.iconBgColor ?? AppTheme.primary.withOpacity(0.15),
                    borderRadius: BorderRadius.circular(AppTheme.radiusMd),
                  ),
                  child: Center(
                    child: Text(
                      widget.icon,
                      style: TextStyle(
                        fontSize: 24,
                        color: widget.iconColor ?? AppTheme.primaryLight,
                      ),
                    ),
                  ),
                ),
                if (widget.trend != null)
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 10,
                      vertical: 4,
                    ),
                    decoration: BoxDecoration(
                      color: widget.trendUp
                          ? AppTheme.success.withOpacity(0.15)
                          : AppTheme.danger.withOpacity(0.15),
                      borderRadius: BorderRadius.circular(AppTheme.radiusSm),
                    ),
                    child: Text(
                      widget.trend!,
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w500,
                        color: widget.trendUp ? AppTheme.success : AppTheme.danger,
                      ),
                    ),
                  ),
              ],
            ),
            const SizedBox(height: AppTheme.spacingLg),
            // 数值
            Text(
              widget.value,
              style: const TextStyle(
                fontSize: 32,
                fontWeight: FontWeight.bold,
                color: AppTheme.textPrimary,
              ),
            ),
            const SizedBox(height: AppTheme.spacingXs),
            // 标签
            Text(
              widget.label,
              style: const TextStyle(
                fontSize: 13,
                color: AppTheme.textMuted,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
