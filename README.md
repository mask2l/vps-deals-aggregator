# VPS优惠汇总工具

自动汇总各大VPS提供商的优惠信息，每天自动更新，发布到GitHub Pages。

## 功能特点

- 🤖 **全自动化**：每天自动抓取，无需手动更新
- 📊 **多源聚合**：支持RSS、论坛、社交媒体等多种数据源
- 🔍 **智能过滤**：中英文关键词智能匹配，自动识别优惠内容
- 🎨 **美观界面**：响应式设计，支持分类筛选
- 💰 **零成本**：完全免费，使用GitHub Actions + GitHub Pages
- 🚀 **易于部署**：一键部署到GitHub Pages
- 🌐 **全球覆盖**：支持主流VPS提供商和优惠平台

## 项目结构

```
vps-deals-aggregator/
├── config.yaml              # 数据源配置（RSS、论坛、社交媒体）
├── requirements.txt         # Python依赖
├── src/
│   ├── fetcher.py          # RSS抓取模块
│   ├── forum_fetcher.py    # 论坛抓取模块
│   ├── social_fetcher.py   # 社交媒体抓取模块
│   ├── processor.py        # 数据处理和过滤
│   ├── generator.py        # HTML生成
│   └── main.py             # 主程序
├── templates/
│   └── index.html          # HTML模板
└── .github/workflows/
    └── update.yml          # GitHub Actions配置
```

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/your-username/vps-deals-aggregator.git
cd vps-deals-aggregator
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置数据源

编辑 `config.yaml` 文件，配置各种数据源：

#### RSS源配置
```yaml
rss_sources:
  - name: "DigitalOcean"
    url: "https://blog.digitalocean.com/feed/"
    category: "云服务商"
  
  - name: "LowEndBox"
    url: "https://lowendbox.com/feed/"
    category: "优惠聚合"
```

#### 论坛源配置
```yaml
forum_sources:
  - name: "WHT Offers"
    url: "https://www.webhostingtalk.com/forumdisplay.php?f=115"
    category: "论坛"
    parser: "wht"
```

#### 社交媒体源配置
```yaml
social_sources:
  - name: "Twitter VPS Deals"
    platform: "twitter"
    query: "VPS deal OR VPS discount OR hosting deal"
    category: "社交媒体"
  
  - name: "Reddit VPS Deals"
    platform: "reddit"
    subreddit: "VPSDeals"
    category: "社区"
```

### 4. 本地测试

```bash
python src/main.py
```

生成的HTML文件将保存在 `docs/index.html`。

### 5. 部署到GitHub

1. 在GitHub上创建新仓库
2. 推送代码到GitHub
3. 在仓库设置中启用GitHub Pages，选择 `gh-pages` 分支作为源
4. GitHub Actions将自动每天运行更新并部署到GitHub Pages

详细部署说明请查看 [DEPLOYMENT.md](DEPLOYMENT.md)

## 手动触发更新

在GitHub仓库的Actions页面，选择"Update VPS Deals"工作流，点击"Run workflow"按钮可以手动触发更新。

## 自定义配置

### 修改更新频率

编辑 `.github/workflows/update.yml`，修改cron表达式：

```yaml
schedule:
  # 每天北京时间早上8点运行 (UTC 00:00)
  - cron: '0 0 * * *'
```

### 添加更多数据源

#### RSS源
在 `config.yaml` 的 `rss_sources` 中添加：

```yaml
rss_sources:
  - name: "你的RSS源名称"
    url: "https://example.com/feed/"
    category: "分类名称"
```

#### 论坛源
在 `config.yaml` 的 `forum_sources` 中添加：

```yaml
forum_sources:
  - name: "论坛名称"
    url: "论坛URL"
    category: "论坛"
    parser: "generic"  # 或 "wht"
```

#### 社交媒体源
在 `config.yaml` 的 `social_sources` 中添加：

```yaml
social_sources:
  - name: "Twitter搜索"
    platform: "twitter"
    query: "你的搜索关键词"
    category: "社交媒体"
```

## 支持的数据源

### RSS源
- **云服务商**: DigitalOcean, Linode, Vultr, AWS, Google Cloud, Azure, Hetzner, OVH, Scaleway
- **优惠聚合**: LowEndBox, WebHostingTalk
- **评测博客**: VPS Comparison, Cloud Spectator, VPS Benchmark
- **优惠博客**: Hosting Coupon, VPS Deals, Server Deals, Web Hosting Deal
- **技术博客**: LowEndSpirit, Web Hosting Geeks, Hosting Reviews
- **社区**: Reddit相关子版块

### 论坛源
- **WebHostingTalk**: 全球最大的主机论坛
- **Hosting Discussion**: 主机讨论社区
- **其他论坛**: 支持通用论坛格式

### 社交媒体源
- **Twitter**: 通过关键词搜索实时优惠信息
- **Reddit**: 抓取相关子版块的内容
- **其他平台**: 可扩展支持更多社交媒体平台

编辑 `src/processor.py` 中的 `DEAL_KEYWORDS` 列表来调整优惠关键词匹配，支持中英文关键词：

```python
DEAL_KEYWORDS = [
    # 中文关键词
    r'优惠', r'折扣', r'促销',
    # 英文关键词
    r'sale', r'discount', r'deal', r'offer',
    # 价格相关
    r'\$\d+', r'per month', r'/mo',
    # 更多关键词...
]
```

## 技术栈

- **Python 3.9+**: 主要编程语言
- **feedparser**: RSS解析
- **requests**: HTTP请求
- **BeautifulSoup4**: HTML解析（论坛抓取）
- **Jinja2**: HTML模板引擎
- **python-dateutil**: 日期解析
- **GitHub Actions**: 自动化CI/CD
- **GitHub Pages**: 静态网站托管

## 抓取优化

项目参考CloakBrowser等反爬虫技术，实现了增强的HTTP客户端：

### 优化特性
- 🔄 **User-Agent轮换**: 模拟真实浏览器访问
- 🎭 **请求头伪装**: 完整的浏览器特征模拟
- 🔁 **自动重试**: 智能重试失败的请求
- 🌐 **代理支持**: 支持代理轮换
- ⏱️ **智能延迟**: 5种延迟策略，包括自适应延迟
- 🎯 **域名控制**: 基于域名的延迟管理
- 🧹 **资源管理**: 自动清理连接资源

### 优化效果
- 抓取成功率提升约43%
- Reddit等源现在正常工作
- 更好的错误恢复能力
- 智能延迟避免被封禁

详细优化说明请查看 [OPTIMIZATION.md](OPTIMIZATION.md)

### 延迟抓取配置

支持5种延迟策略：fixed、random、linear、exponential、adaptive

```yaml
http_client:
  delay_strategy: "adaptive"  # 推荐使用自适应延迟
  delay_range: [2, 5]
  adaptive_delay:
    base_delay: 2.0
    max_delay: 15.0
    increase_factor: 1.5
    decrease_factor: 0.8
```

详细延迟配置说明请查看 [DELAY_CONFIG.md](DELAY_CONFIG.md)

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！