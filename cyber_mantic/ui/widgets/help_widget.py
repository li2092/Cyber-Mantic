"""
帮助系统组件
提供应用使用指南、FAQ、快捷键说明等帮助内容

设计参考：docs/design/08_文档输出计划.md
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QFrame, QTextBrowser, QStackedWidget,
    QListWidget, QListWidgetItem, QSplitter, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from utils.logger import get_logger


class HelpWidget(QWidget):
    """帮助系统组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # 搜索栏
        search_layout = QHBoxLayout()
        search_icon = QLabel("🔍")
        search_layout.addWidget(search_icon)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("搜索帮助...")
        self._search_input.textChanged.connect(self._on_search)
        self._search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 15px;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #1976d2;
            }
        """)
        search_layout.addWidget(self._search_input)
        layout.addLayout(search_layout)

        # 主内容区：目录 + 内容
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧目录
        self._topic_list = QListWidget()
        self._topic_list.setMaximumWidth(200)
        self._topic_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: #fafafa;
            }
            QListWidget::item {
                padding: 10px 15px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
        """)
        self._topic_list.currentRowChanged.connect(self._on_topic_changed)
        splitter.addWidget(self._topic_list)

        # 右侧内容
        self._content_browser = QTextBrowser()
        self._content_browser.setOpenExternalLinks(True)
        self._content_browser.setStyleSheet("""
            QTextBrowser {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 15px;
                background-color: #fff;
                font-size: 14px;
                line-height: 1.6;
            }
        """)
        splitter.addWidget(self._content_browser)

        splitter.setSizes([200, 500])
        layout.addWidget(splitter)

        # 底部链接
        links_layout = QHBoxLayout()
        links_layout.addStretch()

        feedback_btn = QPushButton("📧 反馈问题")
        feedback_btn.clicked.connect(self._on_feedback)
        feedback_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                border: 1px solid #ccc;
                border-radius: 5px;
                background-color: #fff;
            }
            QPushButton:hover {
                background-color: #f5f5f5;
            }
        """)
        links_layout.addWidget(feedback_btn)

        layout.addLayout(links_layout)

        # 加载帮助内容
        self._load_help_topics()

    def _load_help_topics(self):
        """加载帮助主题"""
        topics = [
            ("📖 快速入门", self._get_quickstart_content()),
            ("💬 问道使用指南", self._get_wendao_guide()),
            ("🔮 推演使用指南", self._get_tuiyan_guide()),
            ("📚 典籍使用指南", self._get_library_guide()),
            ("📊 洞察使用指南", self._get_insight_guide()),
            ("🔧 AI接口配置", self._get_api_config_guide()),
            ("❓ 常见问题 (FAQ)", self._get_faq_content()),
            ("📋 术数理论简介", self._get_theory_intro()),
            ("⌨️ 快捷键一览", self._get_shortcuts_content()),
        ]

        self._help_contents = []
        for title, content in topics:
            item = QListWidgetItem(title)
            self._topic_list.addItem(item)
            self._help_contents.append(content)

        # 默认选中第一项
        if self._topic_list.count() > 0:
            self._topic_list.setCurrentRow(0)

    def _on_topic_changed(self, row: int):
        """主题切换"""
        if 0 <= row < len(self._help_contents):
            self._content_browser.setHtml(self._help_contents[row])

    def _on_search(self, text: str):
        """搜索帮助内容"""
        if not text:
            # 显示所有主题
            for i in range(self._topic_list.count()):
                self._topic_list.item(i).setHidden(False)
            return

        text_lower = text.lower()
        for i in range(self._topic_list.count()):
            item = self._topic_list.item(i)
            title = item.text().lower()
            content = self._help_contents[i].lower()
            # 匹配标题或内容
            match = text_lower in title or text_lower in content
            item.setHidden(not match)

    def _on_feedback(self):
        """打开反馈"""
        import webbrowser
        webbrowser.open("https://github.com/your-repo/issues")

    # ==================== 帮助内容 ====================

    def _get_quickstart_content(self) -> str:
        """快速入门内容"""
        return """
        <h2>快速入门</h2>
        <p>欢迎使用 <b>赛博玄数</b>！这是一款基于多AI引擎的中国传统术数智能分析系统。</p>

        <h3>第一步：配置 AI 接口</h3>
        <p>在「设置」页面配置至少一个 AI API 密钥（推荐 Claude 或 Deepseek）。</p>

        <h3>第二步：选择功能模块</h3>
        <ul>
            <li><b>问道</b>：对话式渐进分析，适合深度咨询</li>
            <li><b>推演</b>：快速排盘分析，输入信息即可获得报告</li>
            <li><b>典籍</b>：学习术数知识，阅读经典文献</li>
            <li><b>洞察</b>：查看个人使用画像和状态</li>
        </ul>

        <h3>第三步：开始使用</h3>
        <p><b>问道模式</b>：描述您的问题 + 三个随机数字（0-9），AI将引导您完成5个阶段的分析。</p>
        <p><b>推演模式</b>：填写出生信息、问题类型，选择理论后点击「开始分析」。</p>

        <h3>提示</h3>
        <ul>
            <li>首次使用建议先阅读「免责声明」</li>
            <li>提供更完整的信息可获得更准确的分析</li>
            <li>分析结果仅供参考，重大决策请咨询专业人士</li>
        </ul>
        """

    def _get_wendao_guide(self) -> str:
        """问道使用指南"""
        return """
        <h2>问道使用指南</h2>
        <p>问道模块采用对话式渐进分析，通过5个阶段逐步深入了解您的问题。</p>

        <h3>5阶段流程</h3>
        <ol>
            <li><b>破冰阶段</b>：描述问题 + 三个随机数字，系统使用小六壬起卦初判</li>
            <li><b>基础信息</b>：提供出生年月日、性别、MBTI（可选），解锁八字等理论</li>
            <li><b>深度补充</b>：推断时辰（通过兄弟姐妹、脸型等），补充六爻/梅花占卜</li>
            <li><b>结果确认</b>：回溯过去3-5年关键事件，验证分析准确性</li>
            <li><b>完整报告</b>：生成综合分析报告，支持后续问答</li>
        </ol>

        <h3>输入格式示例</h3>
        <p>「我想问问最近的工作运势，随机数字：3、7、2」</p>

        <h3>支持的理论</h3>
        <ul>
            <li>小六壬（快速初判）</li>
            <li>八字命理（需出生信息）</li>
            <li>紫微斗数（需出生信息）</li>
            <li>六爻占卜（需随机数）</li>
            <li>梅花易数（需随机数/测字）</li>
            <li>奇门遁甲、大六壬等</li>
        </ul>

        <h3>对话管理</h3>
        <ul>
            <li>支持保存和导出对话记录</li>
            <li>可查看对话摘要和统计</li>
            <li>报告支持 Markdown/PDF 导出</li>
        </ul>
        """

    def _get_tuiyan_guide(self) -> str:
        """推演使用指南"""
        return """
        <h2>推演使用指南</h2>
        <p>推演模块提供快速排盘分析，填写信息后一键生成报告。</p>

        <h3>使用步骤</h3>
        <ol>
            <li>选择问题类型（事业、感情、财运等）</li>
            <li>填写问题描述</li>
            <li>提供出生信息（可选但推荐）</li>
            <li>输入随机数字或测字（可选）</li>
            <li>点击「开始分析」</li>
        </ol>

        <h3>出生信息说明</h3>
        <ul>
            <li><b>时辰确定性</b>：选择「确定」「不确定」或「不知道」</li>
            <li><b>历法类型</b>：选择公历或农历</li>
            <li><b>真太阳时</b>：可配置高德API自动计算</li>
        </ul>

        <h3>理论选择</h3>
        <p>系统会根据您提供的信息自动推荐可用理论，也可手动选择。</p>

        <h3>报告功能</h3>
        <ul>
            <li>查看详细排盘结果</li>
            <li>AI综合解读和建议</li>
            <li>导出为多种格式</li>
            <li>保存到历史记录</li>
        </ul>
        """

    def _get_library_guide(self) -> str:
        """典籍使用指南"""
        return """
        <h2>典籍使用指南</h2>
        <p>典籍模块是术数知识学习平台，收录经典文献和现代解读。</p>

        <h3>功能介绍</h3>
        <ul>
            <li><b>文档浏览</b>：阅读系统内置的术数经典</li>
            <li><b>笔记摘抄</b>：选中文本添加个人笔记</li>
            <li><b>标签管理</b>：为笔记添加标签分类</li>
            <li><b>导入文档</b>：添加自己的学习材料</li>
        </ul>

        <h3>内置典籍</h3>
        <ul>
            <li>八字入门与进阶</li>
            <li>紫微斗数基础</li>
            <li>六爻占卜指南</li>
            <li>梅花易数精要</li>
            <li>奇门遁甲入门</li>
            <li>更多内容持续更新中...</li>
        </ul>

        <h3>笔记功能</h3>
        <ol>
            <li>选中文档中的文本</li>
            <li>点击「添加笔记」按钮</li>
            <li>输入个人理解和标签</li>
            <li>笔记支持搜索和导出</li>
        </ol>
        """

    def _get_insight_guide(self) -> str:
        """洞察使用指南"""
        return """
        <h2>洞察使用指南</h2>
        <p>洞察模块展示您的个人使用画像，帮助了解自己的关注点和状态。</p>

        <h3>数据展示</h3>
        <ul>
            <li><b>问题类型分布</b>：您最常咨询的问题领域</li>
            <li><b>使用时段分布</b>：您的使用时间习惯</li>
            <li><b>理论偏好</b>：您最常使用的分析理论</li>
            <li><b>关键词云</b>：高频出现的关键词</li>
        </ul>

        <h3>数据来源</h3>
        <p>数据来自您在「问道」和「推演」模块的使用记录，完全本地存储。</p>

        <h3>隐私说明</h3>
        <ul>
            <li>所有数据仅存储在本地</li>
            <li>不会上传到任何服务器</li>
            <li>可随时清除使用记录</li>
        </ul>

        <h3>温馨关怀</h3>
        <p>如果系统检测到您可能需要休息或帮助，会温和地提示您。这是关怀而非惩罚。</p>
        """

    def _get_api_config_guide(self) -> str:
        """AI接口配置指南"""
        return """
        <h2>AI接口配置教程</h2>
        <p>本应用支持多个 AI 服务商，至少需要配置一个 API 密钥。</p>

        <h3>推荐配置</h3>
        <ul>
            <li><b>主力</b>：Claude 或 Deepseek（分析质量最佳）</li>
            <li><b>备用</b>：配置多个作为故障转移</li>
            <li><b>可选</b>：高德地图（真太阳时计算）</li>
        </ul>

        <h3>API 密钥获取</h3>

        <h4>1. Claude API</h4>
        <p>官网：<a href="https://console.anthropic.com/">console.anthropic.com</a></p>
        <ul>
            <li>注册账号并登录</li>
            <li>进入 API Keys 页面</li>
            <li>点击 Create Key 创建密钥</li>
        </ul>

        <h4>2. Deepseek API</h4>
        <p>官网：<a href="https://platform.deepseek.com/">platform.deepseek.com</a></p>
        <ul>
            <li>注册并实名认证</li>
            <li>进入「API密钥」页面创建</li>
            <li>性价比高，中文能力强</li>
        </ul>

        <h4>3. Google Gemini API</h4>
        <p>官网：<a href="https://makersuite.google.com/app/apikey">makersuite.google.com</a></p>
        <ul>
            <li>使用 Google 账号登录</li>
            <li>点击 Get API Key</li>
        </ul>

        <h4>4. Kimi API</h4>
        <p>官网：<a href="https://platform.moonshot.cn/">platform.moonshot.cn</a></p>
        <ul>
            <li>注册 Moonshot 账号</li>
            <li>在控制台创建 API 密钥</li>
        </ul>

        <h4>5. 高德地图 API（可选）</h4>
        <p>官网：<a href="https://console.amap.com/dev/key/app">console.amap.com</a></p>
        <ul>
            <li>用于出生地点查询</li>
            <li>计算真太阳时</li>
            <li>选择「Web服务」类型</li>
        </ul>
        """

    def _get_faq_content(self) -> str:
        """常见问题"""
        return """
        <h2>常见问题 (FAQ)</h2>

        <h3>Q: 分析结果准确吗？</h3>
        <p>A: 本应用提供的分析基于传统术数理论和现代AI技术，仅供参考和文化探索。
        重大人生决策请咨询专业人士，不要完全依赖分析结果。</p>

        <h3>Q: 为什么需要出生信息？</h3>
        <p>A: 八字、紫微等理论需要精确的出生时间来排盘。
        如果不确定时辰，可以选择「不确定」或「不知道」，系统会使用其他不需要时辰的理论。</p>

        <h3>Q: 随机数字有什么用？</h3>
        <p>A: 随机数字用于六爻、梅花等占卜理论的起卦。
        建议使用真正随机的数字（如随意想到的），而非刻意选择的数字。</p>

        <h3>Q: 数据安全吗？</h3>
        <p>A: 所有数据都存储在您的本地电脑上，不会上传到任何服务器。
        API调用仅发送问题内容给AI服务商，不包含您的个人信息。</p>

        <h3>Q: 支持哪些术数理论？</h3>
        <p>A: 目前支持：八字命理、紫微斗数、六爻占卜、梅花易数、
        小六壬、奇门遁甲、大六壬、测字等。更多理论持续开发中。</p>

        <h3>Q: 为什么分析很慢？</h3>
        <p>A: 分析速度取决于所选AI服务商的响应速度和网络状况。
        Claude和Gemini通常较快，如果超时可尝试切换其他API。</p>

        <h3>Q: 可以离线使用吗？</h3>
        <p>A: 核心排盘计算可以离线进行，但AI分析和解读需要网络连接。</p>

        <h3>Q: 如何清除历史记录？</h3>
        <p>A: 在「洞察」页面可以查看和管理使用记录。
        也可以直接删除 ~/.cyber_mantic 目录下的数据库文件。</p>
        """

    def _get_theory_intro(self) -> str:
        """术数理论简介"""
        return """
        <h2>术数理论简介</h2>
        <p>中国传统术数是一套基于阴阳五行、天干地支等概念的推演系统。</p>

        <h3>八字命理</h3>
        <p>又称四柱预测，以出生年月日时的天干地支组成「八字」，
        分析人的性格特点、运势起伏、人生轨迹。是最广泛使用的命理学说。</p>

        <h3>紫微斗数</h3>
        <p>以出生时间排出命盘，通过十二宫位和百余颗星曜的组合，
        详细分析人生各方面的吉凶。被誉为「帝王之学」。</p>

        <h3>六爻占卜</h3>
        <p>源于《周易》，通过摇卦得到六个爻组成卦象，
        结合日月、世应、用神等分析具体事情的吉凶。灵活性强。</p>

        <h3>梅花易数</h3>
        <p>由宋代邵雍创立，可以通过数字、时间、汉字等多种方式起卦，
        快速判断事情的吉凶趋势。简便灵活。</p>

        <h3>小六壬</h3>
        <p>简单快速的占卜方法，只需三个数字即可起卦。
        结果分为大安、留连、速喜、赤口、小吉、空亡六种。</p>

        <h3>奇门遁甲</h3>
        <p>古代用于军事决策的术数，以时空为基础排局，
        分析事情的方位、时机、人事关系等。结构复杂但信息丰富。</p>

        <h3>大六壬</h3>
        <p>以日辰为基础排课，通过十二天将、贵人等分析人事吉凶。
        尤其擅长占问人事、出行、疾病等。</p>

        <h3>测字</h3>
        <p>通过分析汉字的形、音、义来推断吉凶。
        汉字是象形文字，蕴含丰富的信息可供解读。</p>
        """

    def _get_shortcuts_content(self) -> str:
        """快捷键一览"""
        return """
        <h2>快捷键一览</h2>

        <h3>全局快捷键</h3>
        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
            <tr style="background-color: #f5f5f5;">
                <th>快捷键</th>
                <th>功能</th>
            </tr>
            <tr>
                <td><code>Ctrl + 1</code></td>
                <td>切换到「问道」标签页</td>
            </tr>
            <tr>
                <td><code>Ctrl + 2</code></td>
                <td>切换到「推演」标签页</td>
            </tr>
            <tr>
                <td><code>Ctrl + 3</code></td>
                <td>切换到「典籍」标签页</td>
            </tr>
            <tr>
                <td><code>Ctrl + 4</code></td>
                <td>切换到「洞察」标签页</td>
            </tr>
            <tr>
                <td><code>Ctrl + 5</code></td>
                <td>切换到「历史」标签页</td>
            </tr>
            <tr>
                <td><code>Ctrl + 6</code></td>
                <td>切换到「设置」标签页</td>
            </tr>
            <tr>
                <td><code>Ctrl + S</code></td>
                <td>保存当前内容</td>
            </tr>
            <tr>
                <td><code>Ctrl + E</code></td>
                <td>导出报告</td>
            </tr>
        </table>

        <h3>问道模块</h3>
        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
            <tr style="background-color: #f5f5f5;">
                <th>快捷键</th>
                <th>功能</th>
            </tr>
            <tr>
                <td><code>Enter</code></td>
                <td>发送消息</td>
            </tr>
            <tr>
                <td><code>Shift + Enter</code></td>
                <td>换行</td>
            </tr>
        </table>

        <h3>推演模块</h3>
        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
            <tr style="background-color: #f5f5f5;">
                <th>快捷键</th>
                <th>功能</th>
            </tr>
            <tr>
                <td><code>F5</code></td>
                <td>开始分析</td>
            </tr>
        </table>

        <h3>典籍模块</h3>
        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
            <tr style="background-color: #f5f5f5;">
                <th>快捷键</th>
                <th>功能</th>
            </tr>
            <tr>
                <td><code>Ctrl + F</code></td>
                <td>搜索文档内容</td>
            </tr>
            <tr>
                <td><code>Ctrl + N</code></td>
                <td>添加笔记</td>
            </tr>
        </table>
        """
