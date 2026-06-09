# 延迟抓取配置说明

## 概述

VPS优惠汇总工具现在支持多种延迟抓取策略，可以有效避免被封禁，提高抓取稳定性。

## 延迟策略

### 1. 固定延迟 (fixed)

每次请求使用固定的延迟时间。

**配置示例**:
```yaml
delay_strategy: "fixed"
delay_range: [3, 3]  # 固定3秒
```

**适用场景**:
- 需要严格控制抓取频率
- 目标网站对抓取频率敏感
- 测试和调试阶段

### 2. 随机延迟 (random)

在指定范围内随机选择延迟时间，模拟人类行为。

**配置示例**:
```yaml
delay_strategy: "random"
delay_range: [2, 5]  # 随机2-5秒
```

**适用场景**:
- 一般情况下的推荐策略
- 模拟真实用户访问模式
- 平衡抓取速度和安全性

### 3. 线性增长延迟 (linear)

延迟时间随请求次数线性增长。

**配置示例**:
```yaml
delay_strategy: "linear"
delay_range: [1, 10]  # 基础1秒，最大10秒
```

**适用场景**:
- 长时间运行的抓取任务
- 需要逐渐减慢抓取速度
- 避免长期运行被封禁

### 4. 指数增长延迟 (exponential)

延迟时间随请求次数指数增长，快速达到最大延迟。

**配置示例**:
```yaml
delay_strategy: "exponential"
delay_range: [1, 15]  # 基础1秒，最大15秒
```

**适用场景**:
- 对反爬虫严格的网站
- 需要快速增加延迟的情况
- 遇到频繁限制时

### 5. 自适应延迟 (adaptive) ⭐推荐

根据响应状态和错误率动态调整延迟时间。

**配置示例**:
```yaml
delay_strategy: "adaptive"
delay_range: [2, 5]
adaptive_delay:
  base_delay: 2.0          # 基础延迟时间
  max_delay: 15.0          # 最大延迟时间
  increase_factor: 1.5     # 错误时延迟增长因子
  decrease_factor: 0.8     # 成功时延迟减少因子
  error_threshold: 3       # 连续错误阈值
```

**工作原理**:
- 成功请求 (200): 延迟逐渐减少
- 客户端错误 (4xx): 适度增加延迟
- 服务器错误 (5xx): 显著增加延迟
- 错误率高: 自动增加整体延迟水平
- 同域名快速请求: 额外增加2秒延迟

**适用场景**:
- 生产环境推荐使用
- 需要智能调节抓取速度
- 对稳定性要求高的场景

## 域名特定延迟

系统自动跟踪每个域名的请求时间，如果对同一域名的请求间隔太短（<2秒），会自动增加额外延迟。

**特性**:
- 自动管理，无需配置
- 防止对同一域名过于频繁的请求
- 提高抓取成功率

## 完整配置示例

### 保守配置 (最安全)
```yaml
http_client:
  enabled: true
  delay_strategy: "adaptive"
  delay_range: [5, 10]
  adaptive_delay:
    base_delay: 5.0
    max_delay: 30.0
    increase_factor: 2.0
    decrease_factor: 0.7
    error_threshold: 2
```

### 平衡配置 (推荐)
```yaml
http_client:
  enabled: true
  delay_strategy: "adaptive"
  delay_range: [2, 5]
  adaptive_delay:
    base_delay: 2.0
    max_delay: 15.0
    increase_factor: 1.5
    decrease_factor: 0.8
    error_threshold: 3
```

### 激进配置 (快速)
```yaml
http_client:
  enabled: true
  delay_strategy: "random"
  delay_range: [1, 3]
```

### 测试配置 (无延迟)
```yaml
http_client:
  enabled: false  # 禁用增强客户端，无延迟
```

## 监控和调试

### 查看延迟日志

设置日志级别为DEBUG可以看到详细的延迟信息：

```yaml
logging:
  level: "DEBUG"
```

**输出示例**:
```
DEBUG:enhanced_client:应用延迟: 3.45秒 (域名: 0.00s, 策略: 3.45s)
DEBUG:enhanced_client:应用延迟: 5.12秒 (域名: 2.00s, 策略: 3.12s)
```

### 性能监控

关注以下指标：
- 总抓取时间
- 成功率变化
- 延迟触发频率

## 最佳实践

1. **从保守配置开始**: 首次使用建议使用保守配置
2. **根据响应调整**: 观察目标网站的响应，逐步调整参数
3. **遵守robots.txt**: 尊重网站的抓取规则
4. **设置合理上限**: 避免延迟过长影响整体效率
5. **定期评估**: 根据抓取效果定期调整配置
6. **错误率监控**: 如果错误率持续升高，考虑增加延迟

## 故障排查

### 问题: 抓取速度太慢

**解决方案**:
- 减小delay_range范围
- 切换到random或fixed策略
- 降低adaptive_delay的base_delay

### 问题: 频繁被封禁

**解决方案**:
- 增大delay_range范围
- 切换到adaptive或exponential策略
- 启用代理轮换
- 增加adaptive_delay的max_delay

### 问题: 延迟不生效

**检查项目**:
- 确认http_client.enabled为true
- 检查delay_strategy设置
- 查看日志确认延迟配置加载正确

## 技术细节

### 延迟计算公式

**固定延迟**: `delay = (min + max) / 2`

**随机延迟**: `delay = random(min, max)`

**线性延迟**: `delay = min(request_count * 0.1, max)`

**指数延迟**: `delay = min(base * (1.5^(request_count/10)), max)`

**自适应延迟**: 
```
if response >= 500:
    current_delay = min(current * increase_factor, max)
elif response >= 400:
    current_delay = min(current * 1.2, max)
elif response == 200:
    current_delay = max(current * decrease_factor, base)

final_delay = current * random(0.8, 1.2)
final_delay = min(max(final, base), max)
```

### 域名延迟

```
if (current_time - last_request_time[domain]) < 2.0:
    domain_delay = 2.0
else:
    domain_delay = 0.0

total_delay = domain_delay + strategy_delay
```

## 总结

选择合适的延迟策略对于爬虫的稳定性和效率至关重要：

- **安全性优先**: adaptive + 保守参数
- **效率优先**: random + 较小延迟
- **平衡选择**: adaptive + 推荐参数

建议根据目标网站的特点和实际抓取需求，选择最适合的配置。