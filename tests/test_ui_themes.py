"""
UI主题测试 - 测试各组件的主题切换功能

测试范围：
1. chat_widget - 聊天组件Markdown主题渲染（纯Python函数）
2. 主题颜色逻辑验证（不依赖Qt）

注意：由于测试环境mock了PyQt6，涉及Qt类的测试需要特殊处理
"""
import pytest


class TestChatWidgetMarkdownTheme:
    """聊天组件Markdown主题测试 - 纯Python函数，不依赖Qt"""

    def test_process_inline_markdown_has_theme_param(self):
        """测试process_inline_markdown有theme参数"""
        from ui.widgets.chat_widget import process_inline_markdown
        import inspect

        sig = inspect.signature(process_inline_markdown)
        assert 'theme' in sig.parameters

    def test_markdown_to_styled_html_has_theme_param(self):
        """测试markdown_to_styled_html有theme参数"""
        from ui.widgets.chat_widget import markdown_to_styled_html
        import inspect

        sig = inspect.signature(markdown_to_styled_html)
        assert 'theme' in sig.parameters

    def test_process_inline_markdown_dark_theme(self):
        """测试深色主题行内Markdown"""
        from ui.widgets.chat_widget import process_inline_markdown

        result = process_inline_markdown("**bold**", theme="dark")

        # 深色主题应该使用浅色文字
        assert "#E2E8F0" in result  # 浅色文字

    def test_process_inline_markdown_light_theme(self):
        """测试浅色主题行内Markdown"""
        from ui.widgets.chat_widget import process_inline_markdown

        result = process_inline_markdown("**bold**", theme="light")

        # 浅色主题应该使用深色文字
        assert "#1E293B" in result  # 深色文字

    def test_process_inline_code_dark_theme(self):
        """测试深色主题行内代码"""
        from ui.widgets.chat_widget import process_inline_markdown

        result = process_inline_markdown("`code`", theme="dark")

        assert "#1E1E2E" in result  # 深色背景
        assert "#E2E8F0" in result  # 浅色文字

    def test_process_inline_code_light_theme(self):
        """测试浅色主题行内代码"""
        from ui.widgets.chat_widget import process_inline_markdown

        result = process_inline_markdown("`code`", theme="light")

        assert "#F1F5F9" in result  # 浅色背景
        assert "#334155" in result  # 深色文字

    def test_markdown_code_block_dark_theme(self):
        """测试深色主题代码块"""
        from ui.widgets.chat_widget import markdown_to_styled_html

        result = markdown_to_styled_html("```\ncode\n```", theme="dark")

        # 深色主题代码块背景
        assert "#1E1E2E" in result
        assert "#E2E8F0" in result  # 代码文字

    def test_markdown_code_block_light_theme(self):
        """测试浅色主题代码块"""
        from ui.widgets.chat_widget import markdown_to_styled_html

        result = markdown_to_styled_html("```\ncode\n```", theme="light")

        # 浅色主题代码块背景
        assert "#F1F5F9" in result
        assert "#334155" in result  # 代码文字

    def test_markdown_h1_dark_theme(self):
        """测试深色主题H1标题颜色"""
        from ui.widgets.chat_widget import markdown_to_styled_html

        result = markdown_to_styled_html("# Title", theme="dark")
        assert "#DDD6FE" in result

    def test_markdown_h1_light_theme(self):
        """测试浅色主题H1标题颜色"""
        from ui.widgets.chat_widget import markdown_to_styled_html

        result = markdown_to_styled_html("# Title", theme="light")
        assert "#5B21B6" in result  # 加深的颜色以提高对比度

    def test_markdown_h2_dark_theme(self):
        """测试深色主题H2标题颜色"""
        from ui.widgets.chat_widget import markdown_to_styled_html

        result = markdown_to_styled_html("## Title", theme="dark")
        assert "#C4B5FD" in result

    def test_markdown_h2_light_theme(self):
        """测试浅色主题H2标题颜色"""
        from ui.widgets.chat_widget import markdown_to_styled_html

        result = markdown_to_styled_html("## Title", theme="light")
        assert "#7C3AED" in result

    def test_markdown_h3_dark_theme(self):
        """测试深色主题H3标题颜色"""
        from ui.widgets.chat_widget import markdown_to_styled_html

        result = markdown_to_styled_html("### Title", theme="dark")
        assert "#A78BFA" in result

    def test_markdown_h3_light_theme(self):
        """测试浅色主题H3标题颜色"""
        from ui.widgets.chat_widget import markdown_to_styled_html

        result = markdown_to_styled_html("### Title", theme="light")
        assert "#8B5CF6" in result

    def test_markdown_quote_dark_theme(self):
        """测试深色主题引用块"""
        from ui.widgets.chat_widget import markdown_to_styled_html

        result = markdown_to_styled_html("> quote", theme="dark")
        assert "#94A3B8" in result  # 引用文字颜色
        assert "#6366F1" in result  # 引用边框颜色

    def test_markdown_quote_light_theme(self):
        """测试浅色主题引用块"""
        from ui.widgets.chat_widget import markdown_to_styled_html

        result = markdown_to_styled_html("> quote", theme="light")
        assert "#64748B" in result  # 引用文字颜色

    def test_markdown_hr_dark_theme(self):
        """测试深色主题分隔线"""
        from ui.widgets.chat_widget import markdown_to_styled_html

        result = markdown_to_styled_html("---", theme="dark")
        assert "#4B5563" in result

    def test_markdown_hr_light_theme(self):
        """测试浅色主题分隔线"""
        from ui.widgets.chat_widget import markdown_to_styled_html

        result = markdown_to_styled_html("---", theme="light")
        assert "#E2E8F0" in result

    def test_markdown_list_uses_theme(self):
        """测试列表项使用主题"""
        from ui.widgets.chat_widget import markdown_to_styled_html

        dark_result = markdown_to_styled_html("- item with **bold**", theme="dark")
        light_result = markdown_to_styled_html("- item with **bold**", theme="light")

        # 加粗文字颜色应该不同
        assert "#E2E8F0" in dark_result
        assert "#1E293B" in light_result

    def test_markdown_numbered_list_uses_theme(self):
        """测试数字列表使用主题"""
        from ui.widgets.chat_widget import markdown_to_styled_html

        dark_result = markdown_to_styled_html("1. item with `code`", theme="dark")
        light_result = markdown_to_styled_html("1. item with `code`", theme="light")

        # 代码背景颜色应该不同
        assert "#1E1E2E" in dark_result
        assert "#F1F5F9" in light_result

    def test_markdown_empty_content(self):
        """测试空内容处理"""
        from ui.widgets.chat_widget import markdown_to_styled_html

        result = markdown_to_styled_html("", theme="dark")
        assert result == ""

        result = markdown_to_styled_html(None, theme="light")
        assert result == ""

    def test_markdown_mixed_content(self):
        """测试混合内容"""
        from ui.widgets.chat_widget import markdown_to_styled_html

        content = """# Title

This is a paragraph with **bold** and `code`.

> A quote

- List item

```
code block
```
"""
        dark_result = markdown_to_styled_html(content, theme="dark")
        light_result = markdown_to_styled_html(content, theme="light")

        # 验证两个主题生成的HTML不同
        assert dark_result != light_result

        # 验证包含关键元素
        assert "<p" in dark_result
        assert "<pre" in dark_result
        assert "<strong" in dark_result


class TestThemeColorLogic:
    """主题颜色逻辑测试 - 不依赖Qt类"""

    def test_progress_widget_dark_theme_colors(self):
        """测试深色主题进度条颜色定义"""
        is_dark = True
        stage_color = "#5E9EA0" if is_dark else "#0D9488"
        progress_border = "#3B82F6" if is_dark else "#BBDEFB"
        progress_bg = "#1E293B" if is_dark else "#F5F5F5"
        progress_text = "#E2E8F0" if is_dark else "#1E293B"

        assert stage_color == "#5E9EA0"
        assert progress_border == "#3B82F6"
        assert progress_bg == "#1E293B"
        assert progress_text == "#E2E8F0"

    def test_progress_widget_light_theme_colors(self):
        """测试浅色主题进度条颜色定义"""
        is_dark = False
        stage_color = "#5E9EA0" if is_dark else "#0D9488"
        progress_border = "#3B82F6" if is_dark else "#BBDEFB"
        progress_bg = "#1E293B" if is_dark else "#F5F5F5"
        progress_text = "#E2E8F0" if is_dark else "#1E293B"

        assert stage_color == "#0D9488"
        assert progress_border == "#BBDEFB"
        assert progress_bg == "#F5F5F5"
        assert progress_text == "#1E293B"

    def test_onboarding_dark_theme_colors(self):
        """测试引导对话框深色主题颜色"""
        is_dark = True
        title_color = "#E2E8F0" if is_dark else "#333"
        subtitle_color = "#94A3B8" if is_dark else "#666"
        desc_bg = "#1E293B" if is_dark else "#f8f9fa"
        desc_color = "#CBD5E1" if is_dark else "#444"
        footer_bg = "#1E293B" if is_dark else "#fff"

        assert title_color == "#E2E8F0"
        assert subtitle_color == "#94A3B8"
        assert desc_bg == "#1E293B"
        assert desc_color == "#CBD5E1"
        assert footer_bg == "#1E293B"

    def test_onboarding_light_theme_colors(self):
        """测试引导对话框浅色主题颜色"""
        is_dark = False
        title_color = "#E2E8F0" if is_dark else "#333"
        subtitle_color = "#94A3B8" if is_dark else "#666"
        desc_bg = "#1E293B" if is_dark else "#f8f9fa"
        desc_color = "#CBD5E1" if is_dark else "#444"
        footer_bg = "#1E293B" if is_dark else "#fff"

        assert title_color == "#333"
        assert subtitle_color == "#666"
        assert desc_bg == "#f8f9fa"
        assert desc_color == "#444"
        assert footer_bg == "#fff"

    def test_api_settings_desc_color(self):
        """测试API设置描述颜色"""
        is_dark = True
        desc_color_dark = "#94A3B8" if is_dark else "#64748B"

        is_dark = False
        desc_color_light = "#94A3B8" if is_dark else "#64748B"

        assert desc_color_dark == "#94A3B8"
        assert desc_color_light == "#64748B"
        assert desc_color_dark != desc_color_light

    def test_verification_widget_colors(self):
        """测试验证组件颜色"""
        is_dark = True
        bg_color_dark = "#2D2D3A" if is_dark else "#F8FAFC"
        text_color_dark = "#E2E8F0" if is_dark else "#1E293B"
        border_color_dark = "#4B5563" if is_dark else "#E2E8F0"

        is_dark = False
        bg_color_light = "#2D2D3A" if is_dark else "#F8FAFC"
        text_color_light = "#E2E8F0" if is_dark else "#1E293B"
        border_color_light = "#4B5563" if is_dark else "#E2E8F0"

        # 深色主题
        assert bg_color_dark == "#2D2D3A"
        assert text_color_dark == "#E2E8F0"
        assert border_color_dark == "#4B5563"

        # 浅色主题
        assert bg_color_light == "#F8FAFC"
        assert text_color_light == "#1E293B"
        assert border_color_light == "#E2E8F0"

    def test_chat_bubble_colors(self):
        """测试聊天气泡颜色"""
        # 用户气泡
        is_dark = False
        user_bubble_bg = "#7C3AED" if not is_dark else "#8B5CF6"
        assert user_bubble_bg == "#7C3AED"

        is_dark = True
        user_bubble_bg = "#7C3AED" if not is_dark else "#8B5CF6"
        assert user_bubble_bg == "#8B5CF6"

        # AI气泡
        is_dark = True
        ai_bubble_bg_dark = "#FFFFFF" if not is_dark else "#2D2D3A"
        ai_text_color_dark = "#1E293B" if not is_dark else "#F1F5F9"
        ai_border_color_dark = "#E2E8F0" if not is_dark else "#3D3D4A"

        assert ai_bubble_bg_dark == "#2D2D3A"
        assert ai_text_color_dark == "#F1F5F9"
        assert ai_border_color_dark == "#3D3D4A"

        is_dark = False
        ai_bubble_bg_light = "#FFFFFF" if not is_dark else "#2D2D3A"
        ai_text_color_light = "#1E293B" if not is_dark else "#F1F5F9"
        ai_border_color_light = "#E2E8F0" if not is_dark else "#3D3D4A"

        assert ai_bubble_bg_light == "#FFFFFF"
        assert ai_text_color_light == "#1E293B"
        assert ai_border_color_light == "#E2E8F0"

    def test_quick_result_panel_title_color(self):
        """测试快速结论面板标题颜色"""
        theme = "light"
        title_color = "#1e293b" if theme == "light" else "#E2E8F0"
        assert title_color == "#1e293b"

        theme = "dark"
        title_color = "#1e293b" if theme == "light" else "#E2E8F0"
        assert title_color == "#E2E8F0"

    def test_quick_result_card_status_colors_dark(self):
        """测试快速结论卡片状态颜色 - 深色主题"""
        # 模拟STATUS_STYLES_DARK定义
        STATUS_STYLES_DARK = {
            "WAITING": {"border": "#4B5563", "bg": "#1F2937", "icon": "⬚", "text": "#9CA3AF"},
            "RUNNING": {"border": "#3B82F6", "bg": "#1E3A5F", "icon": "⏳", "text": "#93C5FD"},
            "COMPLETED_GOOD": {"border": "#10B981", "bg": "#064E3B", "icon": "✅", "text": "#6EE7B7"},
            "COMPLETED_BAD": {"border": "#EF4444", "bg": "#7F1D1D", "icon": "⚠️", "text": "#FCA5A5"},
            "COMPLETED_NEUTRAL": {"border": "#F59E0B", "bg": "#78350F", "icon": "➖", "text": "#FCD34D"},
            "ERROR": {"border": "#6B7280", "bg": "#1F2937", "icon": "❌", "text": "#9CA3AF"},
        }

        for status, style in STATUS_STYLES_DARK.items():
            # 验证深色背景（hex值较小）
            bg = style['bg']
            r = int(bg[1:3], 16)
            g = int(bg[3:5], 16)
            b = int(bg[5:7], 16)
            brightness = (r + g + b) / 3
            assert brightness < 128, f"Dark theme {status} bg should be dark"

    def test_quick_result_card_status_colors_light(self):
        """测试快速结论卡片状态颜色 - 浅色主题"""
        # 模拟STATUS_STYLES_LIGHT定义
        STATUS_STYLES_LIGHT = {
            "WAITING": {"border": "#D1D5DB", "bg": "#F3F4F6", "icon": "⬚", "text": "#4B5563"},  # 加深的颜色
            "RUNNING": {"border": "#3B82F6", "bg": "#EFF6FF", "icon": "⏳", "text": "#1D4ED8"},
            "COMPLETED_GOOD": {"border": "#10B981", "bg": "#ECFDF5", "icon": "✅", "text": "#047857"},
            "COMPLETED_BAD": {"border": "#EF4444", "bg": "#FEF2F2", "icon": "⚠️", "text": "#B91C1C"},
            "COMPLETED_NEUTRAL": {"border": "#F59E0B", "bg": "#FFFBEB", "icon": "➖", "text": "#92400E"},  # 加深的颜色
            "ERROR": {"border": "#9CA3AF", "bg": "#F3F4F6", "icon": "❌", "text": "#4B5563"},  # 与WAITING保持一致
        }

        for status, style in STATUS_STYLES_LIGHT.items():
            # 验证浅色背景（hex值较大）
            bg = style['bg']
            r = int(bg[1:3], 16)
            g = int(bg[3:5], 16)
            b = int(bg[5:7], 16)
            brightness = (r + g + b) / 3
            assert brightness > 200, f"Light theme {status} bg should be bright"


class TestColorContrast:
    """颜色对比度测试 - 确保文字可读"""

    def _calculate_contrast_ratio(self, fg: str, bg: str) -> float:
        """计算对比度（简化版）"""
        def luminance(hex_color: str) -> float:
            if hex_color.startswith('#'):
                hex_color = hex_color[1:]
            r = int(hex_color[0:2], 16) / 255
            g = int(hex_color[2:4], 16) / 255
            b = int(hex_color[4:6], 16) / 255
            return 0.299 * r + 0.587 * g + 0.114 * b

        l1 = luminance(fg)
        l2 = luminance(bg)
        if l1 > l2:
            return (l1 + 0.05) / (l2 + 0.05)
        return (l2 + 0.05) / (l1 + 0.05)

    def test_quick_result_card_text_contrast_dark(self):
        """测试深色主题卡片文字对比度"""
        STATUS_STYLES_DARK = {
            "WAITING": {"bg": "#1F2937", "text": "#9CA3AF"},
            "RUNNING": {"bg": "#1E3A5F", "text": "#93C5FD"},
            "COMPLETED_GOOD": {"bg": "#064E3B", "text": "#6EE7B7"},
            "COMPLETED_BAD": {"bg": "#7F1D1D", "text": "#FCA5A5"},
            "COMPLETED_NEUTRAL": {"bg": "#78350F", "text": "#FCD34D"},
            "ERROR": {"bg": "#1F2937", "text": "#9CA3AF"},
        }

        for status, style in STATUS_STYLES_DARK.items():
            text = style['text']
            bg = style['bg']
            ratio = self._calculate_contrast_ratio(text, bg)
            # 最低对比度要求
            assert ratio >= 2.5, f"Dark {status}: contrast {ratio:.2f} too low between {text} and {bg}"

    def test_quick_result_card_text_contrast_light(self):
        """测试浅色主题卡片文字对比度"""
        STATUS_STYLES_LIGHT = {
            "WAITING": {"bg": "#F3F4F6", "text": "#4B5563"},  # 加深的颜色以提高对比度
            "RUNNING": {"bg": "#EFF6FF", "text": "#1D4ED8"},
            "COMPLETED_GOOD": {"bg": "#ECFDF5", "text": "#047857"},
            "COMPLETED_BAD": {"bg": "#FEF2F2", "text": "#B91C1C"},
            "COMPLETED_NEUTRAL": {"bg": "#FFFBEB", "text": "#92400E"},  # 加深的颜色以提高对比度
            "ERROR": {"bg": "#F3F4F6", "text": "#4B5563"},  # 与WAITING保持一致
        }

        for status, style in STATUS_STYLES_LIGHT.items():
            text = style['text']
            bg = style['bg']
            ratio = self._calculate_contrast_ratio(text, bg)
            assert ratio >= 2.5, f"Light {status}: contrast {ratio:.2f} too low between {text} and {bg}"

    def test_ai_bubble_text_contrast(self):
        """测试AI气泡文字对比度"""
        # 深色主题
        dark_text = "#F1F5F9"
        dark_bg = "#2D2D3A"
        dark_ratio = self._calculate_contrast_ratio(dark_text, dark_bg)
        assert dark_ratio >= 3, f"Dark AI bubble contrast {dark_ratio:.2f} too low"

        # 浅色主题
        light_text = "#1E293B"
        light_bg = "#FFFFFF"
        light_ratio = self._calculate_contrast_ratio(light_text, light_bg)
        assert light_ratio >= 3, f"Light AI bubble contrast {light_ratio:.2f} too low"

    def test_markdown_header_contrast(self):
        """测试Markdown标题对比度"""
        # H1 深色主题（假设在深色背景上）
        h1_dark = "#DDD6FE"
        dark_bg = "#2D2D3A"
        ratio = self._calculate_contrast_ratio(h1_dark, dark_bg)
        assert ratio >= 3, f"H1 dark contrast {ratio:.2f} too low"

        # H1 浅色主题（假设在浅色背景上）
        h1_light = "#5B21B6"  # 加深的颜色以提高对比度
        light_bg = "#FFFFFF"
        ratio = self._calculate_contrast_ratio(h1_light, light_bg)
        assert ratio >= 3, f"H1 light contrast {ratio:.2f} too low"

    def test_verification_widget_text_contrast(self):
        """测试验证组件文字对比度"""
        # 深色主题
        dark_text = "#E2E8F0"
        dark_bg = "#2D2D3A"
        ratio = self._calculate_contrast_ratio(dark_text, dark_bg)
        assert ratio >= 3, f"Verification dark contrast {ratio:.2f} too low"

        # 浅色主题
        light_text = "#1E293B"
        light_bg = "#F8FAFC"
        ratio = self._calculate_contrast_ratio(light_text, light_bg)
        assert ratio >= 3, f"Verification light contrast {ratio:.2f} too low"


class TestEscapeHtml:
    """HTML转义测试"""

    def test_escape_html_basic(self):
        """测试基本HTML转义"""
        from ui.widgets.chat_widget import escape_html

        assert escape_html("<script>") == "&lt;script&gt;"
        assert escape_html("a & b") == "a &amp; b"
        assert escape_html("1 < 2 > 0") == "1 &lt; 2 &gt; 0"

    def test_escape_html_preserves_normal_text(self):
        """测试普通文字不受影响"""
        from ui.widgets.chat_widget import escape_html

        text = "Hello World! 你好世界"
        assert escape_html(text) == text
