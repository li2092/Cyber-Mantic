import 'package:flutter/material.dart';

/// 赛博玄数主题配置
class AppTheme {
  // 主色调 - 玄青色系
  static const Color primary = Color(0xFF6366F1);
  static const Color primaryLight = Color(0xFF818CF8);
  static const Color primaryDark = Color(0xFF4F46E5);

  // 强调色 - 丹朱色系
  static const Color accent = Color(0xFFF59E0B);
  static const Color accentLight = Color(0xFFFBBF24);

  // 状态色
  static const Color success = Color(0xFF10B981);
  static const Color warning = Color(0xFFF59E0B);
  static const Color danger = Color(0xFFEF4444);

  // 背景色
  static const Color bgPrimary = Color(0xFF0F0F1A);
  static const Color bgSecondary = Color(0xFF1A1A2E);
  static const Color bgTertiary = Color(0xFF252542);
  static const Color bgCard = Color(0x991E1E32); // 60% opacity

  // 文字色
  static const Color textPrimary = Color(0xFFF1F5F9);
  static const Color textSecondary = Color(0xFF94A3B8);
  static const Color textMuted = Color(0xFF64748B);

  // 边框
  static const Color border = Color(0x14FFFFFF); // 8% white
  static const Color borderLight = Color(0x1FFFFFFF); // 12% white

  // 玻璃效果
  static const Color glassBg = Color(0x08FFFFFF); // 3% white
  static const Color glassBorder = Color(0x14FFFFFF); // 8% white

  // 渐变
  static const LinearGradient primaryGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [primary, primaryDark],
  );

  static const LinearGradient accentGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [accent, accentLight],
  );

  static const LinearGradient welcomeGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [
      Color(0x33636FF1), // primary 20%
      Color(0x1AF59E0B), // accent 10%
      Color(0x1A10B981), // success 10%
    ],
  );

  // 阴影
  static List<BoxShadow> cardShadow = [
    BoxShadow(
      color: Colors.black.withOpacity(0.3),
      blurRadius: 20,
      offset: const Offset(0, 4),
    ),
  ];

  static List<BoxShadow> glowShadow = [
    BoxShadow(
      color: primary.withOpacity(0.3),
      blurRadius: 30,
      spreadRadius: -5,
    ),
  ];

  // 圆角
  static const double radiusSm = 8.0;
  static const double radiusMd = 12.0;
  static const double radiusLg = 16.0;
  static const double radiusXl = 24.0;

  // 间距
  static const double spacingXs = 4.0;
  static const double spacingSm = 8.0;
  static const double spacingMd = 12.0;
  static const double spacingLg = 16.0;
  static const double spacingXl = 24.0;
  static const double spacingXxl = 32.0;

  // 动画时长
  static const Duration durationFast = Duration(milliseconds: 150);
  static const Duration durationNormal = Duration(milliseconds: 250);
  static const Duration durationSlow = Duration(milliseconds: 400);

  // 主题数据
  static ThemeData get darkTheme {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: bgPrimary,
      primaryColor: primary,
      colorScheme: const ColorScheme.dark(
        primary: primary,
        secondary: accent,
        surface: bgSecondary,
        error: danger,
      ),
      textTheme: const TextTheme(
        displayLarge: TextStyle(
          fontSize: 32,
          fontWeight: FontWeight.bold,
          color: textPrimary,
        ),
        displayMedium: TextStyle(
          fontSize: 24,
          fontWeight: FontWeight.w600,
          color: textPrimary,
        ),
        titleLarge: TextStyle(
          fontSize: 20,
          fontWeight: FontWeight.w600,
          color: textPrimary,
        ),
        titleMedium: TextStyle(
          fontSize: 16,
          fontWeight: FontWeight.w500,
          color: textPrimary,
        ),
        bodyLarge: TextStyle(
          fontSize: 16,
          color: textPrimary,
        ),
        bodyMedium: TextStyle(
          fontSize: 14,
          color: textSecondary,
        ),
        bodySmall: TextStyle(
          fontSize: 12,
          color: textMuted,
        ),
        labelSmall: TextStyle(
          fontSize: 10,
          letterSpacing: 1.5,
          color: textMuted,
        ),
      ),
      iconTheme: const IconThemeData(
        color: textSecondary,
        size: 24,
      ),
      dividerColor: border,
      cardTheme: CardTheme(
        color: bgCard,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(radiusLg),
          side: const BorderSide(color: glassBorder),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: bgTertiary,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(radiusMd),
          borderSide: const BorderSide(color: border),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(radiusMd),
          borderSide: const BorderSide(color: border),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(radiusMd),
          borderSide: const BorderSide(color: primary, width: 2),
        ),
        hintStyle: const TextStyle(color: textMuted),
        contentPadding: const EdgeInsets.symmetric(
          horizontal: spacingLg,
          vertical: spacingMd,
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: primary,
          foregroundColor: Colors.white,
          padding: const EdgeInsets.symmetric(
            horizontal: spacingXl,
            vertical: spacingMd,
          ),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(radiusMd),
          ),
        ),
      ),
      scrollbarTheme: ScrollbarThemeData(
        radius: const Radius.circular(4),
        thumbColor: WidgetStateProperty.all(bgTertiary),
        trackColor: WidgetStateProperty.all(bgSecondary),
      ),
    );
  }
}

// 五行颜色
class WuXingColors {
  static const Color wood = Color(0xFF22C55E);  // 木 - 绿
  static const Color fire = Color(0xFFEF4444);  // 火 - 红
  static const Color earth = Color(0xFFF59E0B); // 土 - 黄
  static const Color metal = Color(0xFFE2E8F0); // 金 - 白
  static const Color water = Color(0xFF3B82F6); // 水 - 蓝

  static Color getColor(String element) {
    switch (element) {
      case '木': return wood;
      case '火': return fire;
      case '土': return earth;
      case '金': return metal;
      case '水': return water;
      default: return AppTheme.textPrimary;
    }
  }

  static Color getBgColor(String element) {
    return getColor(element).withOpacity(0.2);
  }
}
