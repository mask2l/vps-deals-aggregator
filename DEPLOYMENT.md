# GitHub Pages 部署指南

## 自动部署配置

项目已经配置了完整的GitHub Actions自动部署流程，包括自动抓取和GitHub Pages部署。

## 部署架构

```
GitHub Actions → 抓取数据 → 更新docs/ → 提交到仓库 → 部署到GitHub Pages
```

## 功能特性

### 1. 自动定时更新
- 每天北京时间早上8点自动运行
- 抓取最新VPS优惠信息
- 更新静态HTML页面

### 2. 手动触发
- 在GitHub Actions页面手动触发更新
- 用于紧急更新或测试

### 3. 自动部署
- 检测到docs/目录变化时自动部署
- 使用GitHub Actions直接部署到GitHub Pages
- 自动创建更新标签

### 4. 智能变更检测
- 只在有实际内容更新时才提交
- 避免无意义的空提交
- 减少部署次数

## 部署步骤

### 1. 创建GitHub仓库

```bash
# 如果还没有GitHub仓库，先创建一个
git init
git add .
git commit -m "Initial commit"

# 添加GitHub远程仓库
git remote add origin https://github.com/your-username/vps-deals-aggregator.git

# 推送到GitHub
git branch -M main
git push -u origin main
```

### 2. 启用GitHub Pages

1. 进入GitHub仓库页面
2. 点击 `Settings` 标签
3. 在左侧菜单找到 `Pages`
4. 配置如下：
   - **Source**: `Deploy from a branch`
   - **Branch**: `gh-pages`
   - **Folder**: `/root`
   - 点击 `Save`

### 3. 启用GitHub Actions

1. 进入仓库的 `Actions` 标签
2. 确认 `Update VPS Deals and Deploy to GitHub Pages` 工作流已启用
3. 可以在 `I understand my workflows, go ahead and enable them` 页面确认

### 4. 验证部署

1. 等待几分钟让Actions完成首次运行
2. 访问 `https://your-username.github.io/vps-deals-aggregator/`
3. 检查页面是否正常显示

## 工作流配置说明

### 定时触发

```yaml
schedule:
  # 每天北京时间早上8点运行 (UTC 00:00)
  - cron: '0 0 * * *'
```

修改定时规则：
- `0 */6 * * *`: 每6小时运行一次
- `0 */12 * * *`: 每12小时运行一次
- `0 0 * * 1`: 每周一运行一次
- `0 0 1 * *`: 每月1号运行一次

### 手动触发

在GitHub Actions页面：
1. 选择 `Update VPS Deals and Deploy to GitHub Pages` 工作流
2. 点击 `Run workflow` 按钮
3. 选择分支（通常是main）
4. 点击 `Run workflow` 绿色按钮

### 自动触发配置

工作流会在以下情况自动触发：
- 定时任务执行
- 手动触发
- 推送代码到main分支（当源代码文件变化时）

触发文件包括：
- `src/**` - 源代码
- `config.yaml` - 配置文件
- `requirements.txt` - 依赖文件
- `templates/**` - 模板文件
- `.github/workflows/update.yml` - 工作流配置

## GitHub Pages配置详情

### 部署配置

```yaml
- name: 部署到GitHub Pages
  uses: peaceiris/actions-gh-pages@v3
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    publish_dir: ./docs
    publish_branch: gh-pages
    force_orphan: true
```

**参数说明**:
- `github_token`: GitHub提供的认证令牌（自动配置）
- `publish_dir`: 要发布的目录（docs/）
- `publish_branch`: 发布分支（gh-pages）
- `force_orphan`: 创建独立的发布分支，保持主分支干净

### 权限配置

```yaml
permissions:
  contents: write
```

这是必需的，允许Actions写入仓库内容。

## 域名配置（可选）

### 使用自定义域名

1. 在仓库根目录创建 `CNAME` 文件
2. 写入你的域名，例如：
   ```
   vps-deals.yourdomain.com
   ```

3. 在你的域名DNS提供商处配置：
   - **CNAME记录**: `vps-deals` → `your-username.github.io`
   - 或使用A记录指向GitHub Pages IP

4. 在GitHub Pages设置中设置自定义域名

### HTTPS配置

GitHub Pages自动提供SSL证书，配置自定义域名后：
1. 在GitHub Pages设置中勾选 `Enforce HTTPS`
2. 等待证书生成（可能需要几分钟到几小时）

## 监控和维护

### 查看部署状态

1. 进入仓库的 `Actions` 标签
2. 查看最新工作流运行状态
3. 点击具体运行查看详细日志

### 常见问题

#### 问题1: Actions失败

**排查步骤**:
1. 检查工作流日志
2. 确认Python版本和依赖安装
3. 检查网络连接和RSS源可用性
4. 查看是否有语法错误

#### 问题2: GitHub Pages不更新

**排查步骤**:
1. 确认gh-pages分支有更新
2. 检查GitHub Pages设置是否正确
3. 查看Actions是否成功部署
4. 清除浏览器缓存

#### 问题3: 定时任务不运行

**可能原因**:
- GitHub Actions可能延迟（正常）
- 仓库在一段时间内没有活动
- 工作流配置有误

**解决方案**:
- 手动触发一次工作流激活定时任务
- 检查cron表达式是否正确

### 性能优化

#### 减少部署频率

修改工作流配置，只在真正需要时部署：

```yaml
# 只在文档目录有实质变化时才部署
- name: 检查是否有更改
  id: check_changes
  run: |
    if git diff --quiet docs/; then
      echo "has_changes=false" >> $GITHUB_OUTPUT
    else
      echo "has_changes=true" >> $GITHUB_OUTPUT
    fi

- name: 部署到GitHub Pages
  if: steps.check_changes.outputs.has_changes == 'true'
  uses: peaceiris/actions-gh-pages@v3
```

#### 优化抓取效率

1. 减少RSS源数量
2. 调整延迟配置
3. 过滤低质量数据源
4. 使用缓存机制

## 成本说明

GitHub Actions和GitHub Pages都是**免费**的：

- **GitHub Actions**: 
  - 公开仓库：无限免费分钟数
  - 私人仓库：每月2000分钟免费

- **GitHub Pages**:
  - 公开仓库：无限免费
  - 私人仓库：每月100GB带宽免费

## 安全建议

1. **不要在配置中暴露敏感信息**
   - RSS源URL通常可以公开
   - 如需使用API密钥，使用GitHub Secrets

2. **使用GitHub Secrets存储敏感数据**
   ```yaml
   env:
     API_KEY: ${{ secrets.MY_API_KEY }}
   ```

3. **定期更新依赖**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

4. **监控异常活动**
   - 定期检查Actions运行日志
   - 关注异常的访问模式

## 故障恢复

### 回滚部署

如果新部署有问题，可以快速回滚：

```bash
# 查看gh-pages分支历史
git checkout gh-pages
git log --oneline

# 回滚到特定版本
git checkout <commit-hash>
git push origin gh-pages --force
```

### 重新部署

强制重新部署：

1. 在GitHub Pages设置中禁用再启用
2. 或手动触发Actions工作流
3. 或提交一个空提交：
   ```bash
   git commit --allow-empty -m "触发部署"
   git push
   ```

## 高级配置

### 多环境部署

可以为不同环境配置不同的工作流：

```yaml
# .github/workflows/staging.yml
name: Update Staging
# 配置开发环境

# .github/workflows/production.yml  
name: Update Production
# 配置生产环境
```

### 通知配置

添加部署成功/失败通知：

```yaml
- name: 发送通知
  if: failure()
  uses: actions/github-script@v6
  with:
    script: |
      github.rest.issues.create({
        owner: context.repo.owner,
        repo: context.repo.repo,
        title: '部署失败',
        body: '工作流运行失败，请检查日志。'
      })
```

## 总结

项目已经配置了完整的自动化部署流程：

✅ **自动定时更新**: 每天自动抓取最新优惠信息
✅ **自动部署**: 变更自动部署到GitHub Pages
✅ **手动触发**: 支持手动触发更新
✅ **智能检测**: 只在有变更时才部署
✅ **完全免费**: 使用GitHub免费服务

按照上述步骤操作，即可实现完全自动化的VPS优惠信息更新和部署！