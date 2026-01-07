import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

/// 聊天消息模型
class ChatMessage {
  final String content;
  final bool isUser;
  final DateTime time;

  ChatMessage({
    required this.content,
    required this.isUser,
    DateTime? time,
  }) : time = time ?? DateTime.now();
}

/// 聊天气泡组件
class ChatBubble extends StatelessWidget {
  final ChatMessage message;

  const ChatBubble({
    super.key,
    required this.message,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: AppTheme.spacingSm),
      child: Row(
        mainAxisAlignment:
            message.isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (!message.isUser) _buildAvatar(false),
          if (!message.isUser) const SizedBox(width: AppTheme.spacingMd),
          Flexible(
            child: Column(
              crossAxisAlignment: message.isUser
                  ? CrossAxisAlignment.end
                  : CrossAxisAlignment.start,
              children: [
                Container(
                  constraints: const BoxConstraints(maxWidth: 400),
                  padding: const EdgeInsets.symmetric(
                    horizontal: AppTheme.spacingLg,
                    vertical: AppTheme.spacingMd,
                  ),
                  decoration: BoxDecoration(
                    gradient: message.isUser ? AppTheme.primaryGradient : null,
                    color: message.isUser ? null : AppTheme.bgTertiary,
                    borderRadius: BorderRadius.only(
                      topLeft: const Radius.circular(AppTheme.radiusLg),
                      topRight: const Radius.circular(AppTheme.radiusLg),
                      bottomLeft: Radius.circular(
                        message.isUser ? AppTheme.radiusLg : 4,
                      ),
                      bottomRight: Radius.circular(
                        message.isUser ? 4 : AppTheme.radiusLg,
                      ),
                    ),
                  ),
                  child: Text(
                    message.content,
                    style: TextStyle(
                      fontSize: 14,
                      height: 1.5,
                      color: message.isUser ? Colors.white : AppTheme.textPrimary,
                    ),
                  ),
                ),
                const SizedBox(height: AppTheme.spacingXs),
                Text(
                  _formatTime(message.time),
                  style: const TextStyle(
                    fontSize: 10,
                    color: AppTheme.textMuted,
                  ),
                ),
              ],
            ),
          ),
          if (message.isUser) const SizedBox(width: AppTheme.spacingMd),
          if (message.isUser) _buildAvatar(true),
        ],
      ),
    );
  }

  Widget _buildAvatar(bool isUser) {
    return Container(
      width: 36,
      height: 36,
      decoration: BoxDecoration(
        gradient: isUser ? AppTheme.accentGradient : AppTheme.primaryGradient,
        shape: BoxShape.circle,
      ),
      child: Center(
        child: Text(
          isUser ? '李' : '☯',
          style: const TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w600,
            color: Colors.white,
          ),
        ),
      ),
    );
  }

  String _formatTime(DateTime time) {
    return '${time.hour.toString().padLeft(2, '0')}:${time.minute.toString().padLeft(2, '0')}';
  }
}

/// 打字指示器
class TypingIndicator extends StatefulWidget {
  const TypingIndicator({super.key});

  @override
  State<TypingIndicator> createState() => _TypingIndicatorState();
}

class _TypingIndicatorState extends State<TypingIndicator>
    with TickerProviderStateMixin {
  late List<AnimationController> _controllers;
  late List<Animation<double>> _animations;

  @override
  void initState() {
    super.initState();
    _controllers = List.generate(
      3,
      (index) => AnimationController(
        duration: const Duration(milliseconds: 600),
        vsync: this,
      ),
    );

    _animations = _controllers.map((controller) {
      return Tween<double>(begin: 0, end: 1).animate(
        CurvedAnimation(parent: controller, curve: Curves.easeInOut),
      );
    }).toList();

    // 延迟启动动画
    for (int i = 0; i < 3; i++) {
      Future.delayed(Duration(milliseconds: i * 200), () {
        if (mounted) {
          _controllers[i].repeat(reverse: true);
        }
      });
    }
  }

  @override
  void dispose() {
    for (var controller in _controllers) {
      controller.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: AppTheme.spacingSm),
      child: Row(
        children: [
          Container(
            width: 36,
            height: 36,
            decoration: const BoxDecoration(
              gradient: AppTheme.primaryGradient,
              shape: BoxShape.circle,
            ),
            child: const Center(
              child: Text(
                '☯',
                style: TextStyle(
                  fontSize: 14,
                  color: Colors.white,
                ),
              ),
            ),
          ),
          const SizedBox(width: AppTheme.spacingMd),
          Container(
            padding: const EdgeInsets.symmetric(
              horizontal: AppTheme.spacingLg,
              vertical: AppTheme.spacingMd,
            ),
            decoration: BoxDecoration(
              color: AppTheme.bgTertiary,
              borderRadius: BorderRadius.circular(AppTheme.radiusLg),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: List.generate(3, (index) {
                return AnimatedBuilder(
                  animation: _animations[index],
                  builder: (context, child) {
                    return Container(
                      margin: EdgeInsets.only(
                        right: index < 2 ? 4 : 0,
                      ),
                      child: Transform.translate(
                        offset: Offset(0, -4 * _animations[index].value),
                        child: Container(
                          width: 8,
                          height: 8,
                          decoration: BoxDecoration(
                            color: AppTheme.textMuted.withOpacity(
                              0.5 + 0.5 * _animations[index].value,
                            ),
                            shape: BoxShape.circle,
                          ),
                        ),
                      ),
                    );
                  },
                );
              }),
            ),
          ),
        ],
      ),
    );
  }
}

/// 聊天输入框
class ChatInputField extends StatefulWidget {
  final Function(String) onSend;

  const ChatInputField({
    super.key,
    required this.onSend,
  });

  @override
  State<ChatInputField> createState() => _ChatInputFieldState();
}

class _ChatInputFieldState extends State<ChatInputField> {
  final _controller = TextEditingController();
  bool _hasText = false;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _handleSend() {
    final text = _controller.text.trim();
    if (text.isNotEmpty) {
      widget.onSend(text);
      _controller.clear();
      setState(() => _hasText = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(AppTheme.spacingLg),
      decoration: const BoxDecoration(
        border: Border(
          top: BorderSide(color: AppTheme.border),
        ),
      ),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: _controller,
              onChanged: (value) {
                setState(() => _hasText = value.trim().isNotEmpty);
              },
              onSubmitted: (_) => _handleSend(),
              decoration: InputDecoration(
                hintText: '输入您的问题...',
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(AppTheme.radiusMd),
                  borderSide: const BorderSide(color: AppTheme.border),
                ),
                contentPadding: const EdgeInsets.symmetric(
                  horizontal: AppTheme.spacingLg,
                  vertical: AppTheme.spacingMd,
                ),
              ),
              style: const TextStyle(fontSize: 14),
            ),
          ),
          const SizedBox(width: AppTheme.spacingMd),
          _buildSendButton(),
        ],
      ),
    );
  }

  Widget _buildSendButton() {
    return MouseRegion(
      cursor: SystemMouseCursors.click,
      child: GestureDetector(
        onTap: _handleSend,
        child: AnimatedContainer(
          duration: AppTheme.durationFast,
          width: 48,
          height: 48,
          decoration: BoxDecoration(
            gradient: _hasText ? AppTheme.primaryGradient : null,
            color: _hasText ? null : AppTheme.bgTertiary,
            borderRadius: BorderRadius.circular(AppTheme.radiusMd),
            boxShadow: _hasText ? AppTheme.glowShadow : null,
          ),
          child: Icon(
            Icons.send_rounded,
            color: _hasText ? Colors.white : AppTheme.textMuted,
            size: 20,
          ),
        ),
      ),
    );
  }
}
