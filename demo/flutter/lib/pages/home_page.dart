import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../widgets/widgets.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  int _selectedNavIndex = 0;
  final List<ChatMessage> _messages = [
    ChatMessage(
      content: '您好！我是赛博玄数智能助手。请问今天您想咨询什么事项？我可以为您提供八字、紫微斗数、奇门遁甲等多种术数分析。',
      isUser: false,
    ),
    ChatMessage(
      content: '我想问一下2025年的事业运势如何',
      isUser: true,
    ),
    ChatMessage(
      content: '好的，为了给您更准确的分析，我需要了解一些基本信息。请问您的出生年月日和时辰是？另外，如果方便的话，可以给我3个随机数字（1-9），用于辅助分析。',
      isUser: false,
    ),
  ];
  bool _isTyping = false;

  final List<Map<String, dynamic>> _navItems = [
    {'icon': '💬', 'label': '问道', 'badge': null},
    {'icon': '🔮', 'label': '推演', 'badge': 'New'},
    {'icon': '📚', 'label': '典籍', 'badge': null},
    {'icon': '💡', 'label': '洞察', 'badge': null},
    {'icon': '📜', 'label': '历史记录', 'badge': null},
    {'icon': '⚙️', 'label': '设置', 'badge': null},
    {'icon': '❓', 'label': '帮助', 'badge': null},
  ];

  void _handleSendMessage(String text) {
    setState(() {
      _messages.add(ChatMessage(content: text, isUser: true));
      _isTyping = true;
    });

    // 模拟AI回复
    Future.delayed(const Duration(milliseconds: 1500), () {
      if (mounted) {
        setState(() {
          _isTyping = false;
          _messages.add(ChatMessage(
            content: '根据您提供的信息，我正在为您进行多维度分析。从八字来看，您的命局呈现出较好的发展态势...',
            isUser: false,
          ));
        });
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.bgPrimary,
      body: Stack(
        children: [
          // 背景装饰
          _buildBackgroundDecoration(),
          // 主布局
          Row(
            children: [
              // 侧边栏
              _buildSidebar(),
              // 主内容
              Expanded(child: _buildMainContent()),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildBackgroundDecoration() {
    return Positioned.fill(
      child: Container(
        decoration: BoxDecoration(
          gradient: RadialGradient(
            center: const Alignment(-0.5, -0.5),
            radius: 1.5,
            colors: [
              AppTheme.primary.withOpacity(0.1),
              Colors.transparent,
            ],
          ),
        ),
        child: Stack(
          children: [
            // 八卦装饰
            Positioned(
              top: 80,
              right: 50,
              child: Text(
                '☯',
                style: TextStyle(
                  fontSize: 120,
                  color: AppTheme.textPrimary.withOpacity(0.03),
                ),
              ),
            ),
            Positioned(
              bottom: 100,
              left: 30,
              child: Text(
                '☰',
                style: TextStyle(
                  fontSize: 100,
                  color: AppTheme.textPrimary.withOpacity(0.02),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSidebar() {
    return Container(
      width: 260,
      decoration: BoxDecoration(
        color: AppTheme.glassBg,
        border: const Border(
          right: BorderSide(color: AppTheme.glassBorder),
        ),
      ),
      child: Column(
        children: [
          // Logo
          _buildLogo(),
          // 导航菜单
          Expanded(child: _buildNavMenu()),
          // 用户卡片
          _buildUserCard(),
        ],
      ),
    );
  }

  Widget _buildLogo() {
    return Container(
      padding: const EdgeInsets.all(AppTheme.spacingXl),
      decoration: const BoxDecoration(
        border: Border(
          bottom: BorderSide(color: AppTheme.border),
        ),
      ),
      child: Row(
        children: [
          Container(
            width: 48,
            height: 48,
            decoration: BoxDecoration(
              gradient: AppTheme.primaryGradient,
              borderRadius: BorderRadius.circular(AppTheme.radiusMd),
              boxShadow: AppTheme.glowShadow,
            ),
            child: const Center(
              child: Text(
                '☯',
                style: TextStyle(fontSize: 24, color: Colors.white),
              ),
            ),
          ),
          const SizedBox(width: AppTheme.spacingMd),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              ShaderMask(
                shaderCallback: (bounds) => const LinearGradient(
                  colors: [AppTheme.textPrimary, AppTheme.primaryLight],
                ).createShader(bounds),
                child: const Text(
                  '赛博玄数',
                  style: TextStyle(
                    fontFamily: 'NotoSerifSC',
                    fontSize: 20,
                    fontWeight: FontWeight.w600,
                    color: Colors.white,
                  ),
                ),
              ),
              const Text(
                'CYBER MANTIC',
                style: TextStyle(
                  fontSize: 10,
                  letterSpacing: 2,
                  color: AppTheme.textMuted,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildNavMenu() {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(
        horizontal: AppTheme.spacingMd,
        vertical: AppTheme.spacingLg,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const NavSectionTitle(title: '核心功能'),
          ...List.generate(3, (index) {
            final item = _navItems[index];
            return NavButton(
              icon: item['icon'],
              label: item['label'],
              badge: item['badge'],
              isActive: _selectedNavIndex == index,
              onTap: () => setState(() => _selectedNavIndex = index),
            );
          }),
          const SizedBox(height: AppTheme.spacingLg),
          const NavSectionTitle(title: '个人中心'),
          ...List.generate(2, (index) {
            final item = _navItems[index + 3];
            return NavButton(
              icon: item['icon'],
              label: item['label'],
              isActive: _selectedNavIndex == index + 3,
              onTap: () => setState(() => _selectedNavIndex = index + 3),
            );
          }),
          const SizedBox(height: AppTheme.spacingLg),
          const NavSectionTitle(title: '系统'),
          ...List.generate(2, (index) {
            final item = _navItems[index + 5];
            return NavButton(
              icon: item['icon'],
              label: item['label'],
              isActive: _selectedNavIndex == index + 5,
              onTap: () => setState(() => _selectedNavIndex = index + 5),
            );
          }),
        ],
      ),
    );
  }

  Widget _buildUserCard() {
    return Container(
      margin: const EdgeInsets.all(AppTheme.spacingMd),
      padding: const EdgeInsets.all(AppTheme.spacingMd),
      decoration: BoxDecoration(
        color: AppTheme.glassBg,
        borderRadius: BorderRadius.circular(AppTheme.radiusMd),
        border: Border.all(color: AppTheme.glassBorder),
      ),
      child: Row(
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: const BoxDecoration(
              gradient: AppTheme.accentGradient,
              shape: BoxShape.circle,
            ),
            child: const Center(
              child: Text(
                '李',
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  color: Colors.white,
                ),
              ),
            ),
          ),
          const SizedBox(width: AppTheme.spacingMd),
          const Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '李明',
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w500,
                    color: AppTheme.textPrimary,
                  ),
                ),
                SizedBox(height: 2),
                Row(
                  children: [
                    Icon(
                      Icons.circle,
                      size: 6,
                      color: AppTheme.success,
                    ),
                    SizedBox(width: 4),
                    Text(
                      'API 已连接',
                      style: TextStyle(
                        fontSize: 12,
                        color: AppTheme.success,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMainContent() {
    return Column(
      children: [
        // 顶部栏
        _buildTopBar(),
        // 内容区
        Expanded(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(AppTheme.spacingXxl),
            child: Column(
              children: [
                // 欢迎横幅
                _buildWelcomeBanner(),
                const SizedBox(height: AppTheme.spacingXl),
                // 统计卡片
                _buildStatsRow(),
                const SizedBox(height: AppTheme.spacingXl),
                // 主内容网格
                _buildMainGrid(),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildTopBar() {
    return Container(
      height: 64,
      padding: const EdgeInsets.symmetric(horizontal: AppTheme.spacingXl),
      decoration: BoxDecoration(
        color: AppTheme.glassBg,
        border: const Border(
          bottom: BorderSide(color: AppTheme.glassBorder),
        ),
      ),
      child: Row(
        children: [
          const Text(
            '💬',
            style: TextStyle(fontSize: 24),
          ),
          const SizedBox(width: AppTheme.spacingMd),
          const Text(
            '问道 · 智能对话',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w500,
              color: AppTheme.textPrimary,
            ),
          ),
          const Spacer(),
          // 搜索框
          Container(
            width: 240,
            height: 40,
            decoration: BoxDecoration(
              color: AppTheme.bgTertiary,
              borderRadius: BorderRadius.circular(AppTheme.radiusMd),
              border: Border.all(color: AppTheme.border),
            ),
            child: const Row(
              children: [
                SizedBox(width: AppTheme.spacingMd),
                Icon(Icons.search, size: 18, color: AppTheme.textMuted),
                SizedBox(width: AppTheme.spacingSm),
                Expanded(
                  child: TextField(
                    decoration: InputDecoration(
                      hintText: '搜索历史记录...',
                      hintStyle: TextStyle(
                        fontSize: 13,
                        color: AppTheme.textMuted,
                      ),
                      border: InputBorder.none,
                      isDense: true,
                      contentPadding: EdgeInsets.zero,
                    ),
                    style: TextStyle(
                      fontSize: 13,
                      color: AppTheme.textPrimary,
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: AppTheme.spacingMd),
          _buildIconButton(Icons.notifications_outlined, badge: 3),
          const SizedBox(width: AppTheme.spacingSm),
          _buildIconButton(Icons.dark_mode_outlined),
        ],
      ),
    );
  }

  Widget _buildIconButton(IconData icon, {int? badge}) {
    return Stack(
      clipBehavior: Clip.none,
      children: [
        Container(
          width: 40,
          height: 40,
          decoration: BoxDecoration(
            color: AppTheme.glassBg,
            borderRadius: BorderRadius.circular(AppTheme.radiusMd),
            border: Border.all(color: AppTheme.glassBorder),
          ),
          child: Icon(icon, size: 20, color: AppTheme.textSecondary),
        ),
        if (badge != null)
          Positioned(
            top: -4,
            right: -4,
            child: Container(
              width: 18,
              height: 18,
              decoration: const BoxDecoration(
                color: AppTheme.danger,
                shape: BoxShape.circle,
              ),
              child: Center(
                child: Text(
                  badge.toString(),
                  style: const TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.w600,
                    color: Colors.white,
                  ),
                ),
              ),
            ),
          ),
      ],
    );
  }

  Widget _buildWelcomeBanner() {
    return Container(
      padding: const EdgeInsets.all(AppTheme.spacingXxl),
      decoration: BoxDecoration(
        gradient: AppTheme.welcomeGradient,
        borderRadius: BorderRadius.circular(AppTheme.radiusXl),
        border: Border.all(color: AppTheme.glassBorder),
      ),
      child: Stack(
        children: [
          // 装饰
          Positioned(
            right: 32,
            top: 0,
            bottom: 0,
            child: Center(
              child: Text(
                '☯',
                style: TextStyle(
                  fontSize: 100,
                  color: AppTheme.textPrimary.withOpacity(0.1),
                ),
              ),
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                '欢迎回来，李明',
                style: TextStyle(
                  fontFamily: 'NotoSerifSC',
                  fontSize: 24,
                  fontWeight: FontWeight.w600,
                  color: AppTheme.textPrimary,
                ),
              ),
              const SizedBox(height: AppTheme.spacingSm),
              const Text(
                '今日宜：问事、出行、签约 | 紫气东来，万事可期',
                style: TextStyle(
                  fontSize: 14,
                  color: AppTheme.textSecondary,
                ),
              ),
              const SizedBox(height: AppTheme.spacingXl),
              Row(
                children: [
                  _buildPrimaryButton('✨  开始新对话'),
                  const SizedBox(width: AppTheme.spacingMd),
                  _buildSecondaryButton('📊  查看今日运势'),
                ],
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildPrimaryButton(String text) {
    return MouseRegion(
      cursor: SystemMouseCursors.click,
      child: Container(
        padding: const EdgeInsets.symmetric(
          horizontal: AppTheme.spacingXl,
          vertical: AppTheme.spacingMd,
        ),
        decoration: BoxDecoration(
          gradient: AppTheme.primaryGradient,
          borderRadius: BorderRadius.circular(AppTheme.radiusMd),
          boxShadow: [
            ...AppTheme.cardShadow,
            BoxShadow(
              color: AppTheme.primary.withOpacity(0.3),
              blurRadius: 20,
              spreadRadius: -5,
            ),
          ],
        ),
        child: Text(
          text,
          style: const TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w500,
            color: Colors.white,
          ),
        ),
      ),
    );
  }

  Widget _buildSecondaryButton(String text) {
    return MouseRegion(
      cursor: SystemMouseCursors.click,
      child: Container(
        padding: const EdgeInsets.symmetric(
          horizontal: AppTheme.spacingXl,
          vertical: AppTheme.spacingMd,
        ),
        decoration: BoxDecoration(
          color: AppTheme.glassBg,
          borderRadius: BorderRadius.circular(AppTheme.radiusMd),
          border: Border.all(color: AppTheme.glassBorder),
        ),
        child: Text(
          text,
          style: const TextStyle(
            fontSize: 14,
            color: AppTheme.textPrimary,
          ),
        ),
      ),
    );
  }

  Widget _buildStatsRow() {
    return Row(
      children: const [
        Expanded(
          child: StatCard(
            icon: '📊',
            value: '128',
            label: '本月分析次数',
            trend: '↑ 12%',
            trendUp: true,
          ),
        ),
        SizedBox(width: AppTheme.spacingXl),
        Expanded(
          child: StatCard(
            icon: '⏱️',
            value: '24.5h',
            label: '学习总时长',
            trend: '↑ 8%',
            trendUp: true,
            iconBgColor: Color(0x26F59E0B),
            iconColor: AppTheme.accent,
          ),
        ),
        SizedBox(width: AppTheme.spacingXl),
        Expanded(
          child: StatCard(
            icon: '📝',
            value: '56',
            label: '笔记数量',
            trend: '↑ 5%',
            trendUp: true,
            iconBgColor: Color(0x2610B981),
            iconColor: AppTheme.success,
          ),
        ),
        SizedBox(width: AppTheme.spacingXl),
        Expanded(
          child: StatCard(
            icon: '🎯',
            value: '87%',
            label: '分析准确率',
            trend: '↓ 3%',
            trendUp: false,
            iconBgColor: Color(0x26EF4444),
            iconColor: AppTheme.danger,
          ),
        ),
      ],
    );
  }

  Widget _buildMainGrid() {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // 左侧：对话区
        Expanded(
          flex: 2,
          child: _buildChatSection(),
        ),
        const SizedBox(width: AppTheme.spacingXl),
        // 右侧：信息面板
        Expanded(
          child: _buildRightPanel(),
        ),
      ],
    );
  }

  Widget _buildChatSection() {
    return GlassCard(
      title: '💬  智能问答',
      trailing: _buildSecondaryButton('🔄  新对话'),
      padding: EdgeInsets.zero,
      child: SizedBox(
        height: 450,
        child: Column(
          children: [
            // 消息列表
            Expanded(
              child: ListView.builder(
                padding: const EdgeInsets.all(AppTheme.spacingLg),
                itemCount: _messages.length + (_isTyping ? 1 : 0),
                itemBuilder: (context, index) {
                  if (_isTyping && index == _messages.length) {
                    return const TypingIndicator();
                  }
                  return ChatBubble(message: _messages[index]);
                },
              ),
            ),
            // 输入框
            ChatInputField(onSend: _handleSendMessage),
          ],
        ),
      ),
    );
  }

  Widget _buildRightPanel() {
    return Column(
      children: [
        // 八字命盘
        GlassCard(
          title: '🎴  八字命盘',
          child: Column(
            children: const [
              BaZiFourPillars(),
              SizedBox(height: AppTheme.spacingXl),
              WuXingDistribution(),
            ],
          ),
        ),
        const SizedBox(height: AppTheme.spacingXl),
        // 快捷操作
        GlassCard(
          title: '⚡  快捷操作',
          child: GridView.count(
            shrinkWrap: true,
            crossAxisCount: 2,
            mainAxisSpacing: AppTheme.spacingMd,
            crossAxisSpacing: AppTheme.spacingMd,
            childAspectRatio: 1.2,
            physics: const NeverScrollableScrollPhysics(),
            children: const [
              QuickActionButton(icon: '🎲', label: '小六壬'),
              QuickActionButton(icon: '✍️', label: '测字'),
              QuickActionButton(icon: '🌸', label: '梅花易数'),
              QuickActionButton(icon: '⚔️', label: '六爻'),
            ],
          ),
        ),
        const SizedBox(height: AppTheme.spacingXl),
        // 最近历史
        GlassCard(
          title: '📜  最近分析',
          padding: const EdgeInsets.all(AppTheme.spacingMd),
          child: Column(
            children: const [
              HistoryItem(
                title: '2025年事业运势分析',
                meta: '八字 · 2小时前',
                dotColor: AppTheme.success,
              ),
              HistoryItem(
                title: '感情姻缘咨询',
                meta: '紫微斗数 · 昨天',
                dotColor: AppTheme.primary,
              ),
              HistoryItem(
                title: '投资决策分析',
                meta: '奇门遁甲 · 3天前',
                dotColor: AppTheme.warning,
              ),
            ],
          ),
        ),
      ],
    );
  }
}
