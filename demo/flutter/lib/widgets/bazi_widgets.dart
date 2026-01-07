import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

/// 八字柱位组件
class BaZiPillar extends StatelessWidget {
  final String label;
  final String gan;
  final String zhi;

  const BaZiPillar({
    super.key,
    required this.label,
    required this.gan,
    required this.zhi,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(AppTheme.spacingLg),
      decoration: BoxDecoration(
        color: AppTheme.bgTertiary,
        borderRadius: BorderRadius.circular(AppTheme.radiusMd),
        border: Border.all(color: AppTheme.border),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            label,
            style: const TextStyle(
              fontSize: 11,
              color: AppTheme.textMuted,
            ),
          ),
          const SizedBox(height: AppTheme.spacingSm),
          Text(
            gan,
            style: const TextStyle(
              fontFamily: 'NotoSerifSC',
              fontSize: 28,
              fontWeight: FontWeight.w600,
              color: AppTheme.primaryLight,
            ),
          ),
          const SizedBox(height: AppTheme.spacingXs),
          Text(
            zhi,
            style: const TextStyle(
              fontFamily: 'NotoSerifSC',
              fontSize: 28,
              fontWeight: FontWeight.w600,
              color: AppTheme.accent,
            ),
          ),
        ],
      ),
    );
  }
}

/// 八字四柱显示
class BaZiFourPillars extends StatelessWidget {
  final List<Map<String, String>> pillars;

  const BaZiFourPillars({
    super.key,
    this.pillars = const [
      {'label': '年柱', 'gan': '甲', 'zhi': '子'},
      {'label': '月柱', 'gan': '丙', 'zhi': '寅'},
      {'label': '日柱', 'gan': '戊', 'zhi': '辰'},
      {'label': '时柱', 'gan': '庚', 'zhi': '午'},
    ],
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: pillars.map((pillar) {
        return Expanded(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 4),
            child: BaZiPillar(
              label: pillar['label']!,
              gan: pillar['gan']!,
              zhi: pillar['zhi']!,
            ),
          ),
        );
      }).toList(),
    );
  }
}

/// 五行指示器
class WuXingIndicator extends StatelessWidget {
  final String element;
  final int count;

  const WuXingIndicator({
    super.key,
    required this.element,
    required this.count,
  });

  @override
  Widget build(BuildContext context) {
    final color = WuXingColors.getColor(element);
    final bgColor = WuXingColors.getBgColor(element);

    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Stack(
          clipBehavior: Clip.none,
          children: [
            Container(
              width: 48,
              height: 48,
              decoration: BoxDecoration(
                color: bgColor,
                shape: BoxShape.circle,
              ),
              child: Center(
                child: Text(
                  element,
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w500,
                    color: color,
                  ),
                ),
              ),
            ),
            Positioned(
              right: -4,
              bottom: -4,
              child: Container(
                width: 20,
                height: 20,
                decoration: BoxDecoration(
                  color: AppTheme.bgPrimary,
                  shape: BoxShape.circle,
                  border: Border.all(color: color, width: 2),
                ),
                child: Center(
                  child: Text(
                    count.toString(),
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w600,
                      color: color,
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: AppTheme.spacingSm),
        Text(
          element,
          style: const TextStyle(
            fontSize: 12,
            color: AppTheme.textSecondary,
          ),
        ),
      ],
    );
  }
}

/// 五行分布图
class WuXingDistribution extends StatelessWidget {
  final Map<String, int> distribution;

  const WuXingDistribution({
    super.key,
    this.distribution = const {
      '木': 2,
      '火': 3,
      '土': 2,
      '金': 1,
      '水': 0,
    },
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceAround,
      children: distribution.entries.map((entry) {
        return WuXingIndicator(
          element: entry.key,
          count: entry.value,
        );
      }).toList(),
    );
  }
}
