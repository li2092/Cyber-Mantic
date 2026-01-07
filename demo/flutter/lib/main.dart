import 'package:flutter/material.dart';
import 'theme/app_theme.dart';
import 'pages/home_page.dart';

void main() {
  runApp(const CyberManticApp());
}

/// 赛博玄数 Flutter Desktop Demo
class CyberManticApp extends StatelessWidget {
  const CyberManticApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: '赛博玄数 - Cyber Mantic',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.darkTheme,
      home: const HomePage(),
    );
  }
}
