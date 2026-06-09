#!/usr/bin/env python3
"""
优化的HTTP客户端模块 - 参考反爬虫技术
支持User-Agent轮换、请求头伪装、代理、重试机制等
"""
import requests
import random
import time
from typing import Optional, Dict, List
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedHTTPClient:
    """增强的HTTP客户端，模拟真实浏览器行为"""
    
    # 真实的浏览器User-Agent列表
    USER_AGENTS = [
        # Chrome
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        # Firefox
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
        # Safari
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
        # Edge
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
        # Opera
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0'
    ]
    
    # 延迟策略枚举
    DELAY_STRATEGIES = ['fixed', 'random', 'linear', 'exponential', 'adaptive']
    
    # 真实的浏览器请求头模板
    BASE_HEADERS = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0'
    }
    
    def __init__(
        self,
        proxy_list: Optional[List[str]] = None,
        use_proxy: bool = False,
        max_retries: int = 3,
        timeout: int = 30,
        delay_range: tuple = (1, 3),
        delay_strategy: str = 'random',
        enabled: bool = True,
        adaptive_delay_config: Optional[Dict] = None
    ):
        """
        初始化增强HTTP客户端
        
        Args:
            proxy_list: 代理服务器列表
            use_proxy: 是否使用代理
            max_retries: 最大重试次数
            timeout: 请求超时时间
            delay_range: 请求延迟范围（秒）
            delay_strategy: 延迟策略 (fixed, random, linear, exponential, adaptive)
            enabled: 是否启用增强功能
            adaptive_delay_config: 自适应延迟配置
        """
        self.enabled = enabled
        self.proxy_list = proxy_list or []
        self.use_proxy = use_proxy if enabled else False
        self.max_retries = max_retries if enabled else 0
        self.timeout = timeout
        self.delay_range = delay_range if enabled else (0, 0)
        self.delay_strategy = delay_strategy if enabled else 'none'
        
        # 验证延迟策略
        if self.delay_strategy not in self.DELAY_STRATEGIES and self.delay_strategy != 'none':
            logger.warning(f"未知的延迟策略: {delay_strategy}, 使用默认策略 random")
            self.delay_strategy = 'random'
        
        # 自适应延迟配置
        self.adaptive_config = adaptive_delay_config or {
            'base_delay': 1.0,
            'max_delay': 10.0,
            'increase_factor': 1.5,
            'decrease_factor': 0.8,
            'error_threshold': 3
        }
        
        # 延迟状态跟踪
        self.request_count = 0
        self.error_count = 0
        self.current_delay = self.adaptive_config['base_delay']
        self.last_response_time = 0
        
        # 域名特定的延迟记录
        self.domain_delays = {}
        self.domain_last_request = {}
        
        # 创建会话
        self.session = self._create_session()
        
        # 存储cookies
        self.cookies = {}
    
    def _create_session(self) -> requests.Session:
        """创建带有重试机制的会话"""
        session = requests.Session()
        
        # 配置重试策略
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _get_random_user_agent(self) -> str:
        """获取随机User-Agent"""
        return random.choice(self.USER_AGENTS)
    
    def _get_random_proxy(self) -> Optional[Dict]:
        """获取随机代理"""
        if not self.use_proxy or not self.proxy_list:
            return None
        
        proxy_url = random.choice(self.proxy_list)
        return {
            'http': proxy_url,
            'https': proxy_url
        }
    
    def _build_headers(self, custom_headers: Optional[Dict] = None) -> Dict:
        """构建请求头"""
        headers = self.BASE_HEADERS.copy()
        headers['User-Agent'] = self._get_random_user_agent()
        
        # 添加自定义请求头
        if custom_headers:
            headers.update(custom_headers)
        
        return headers
    
    def _extract_domain(self, url: str) -> str:
        """提取URL的域名"""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc
        except:
            return url
    
    def _get_domain_delay(self, url: str) -> float:
        """
        获取基于域名的延迟
        
        Args:
            url: 请求URL
            
        Returns:
            域名特定的延迟时间
        """
        domain = self._extract_domain(url)
        current_time = time.time()
        
        # 检查域名是否在延迟记录中
        if domain in self.domain_last_request:
            last_request_time = self.domain_last_request[domain]
            time_since_last = current_time - last_request_time
            
            # 如果距离上次请求时间很短，增加额外延迟
            if time_since_last < 2.0:
                return 2.0  # 额外2秒延迟
        
        # 更新域名最后请求时间
        self.domain_last_request[domain] = current_time
        
        return 0
    
    def _add_delay(self, url: str = "", response_status: Optional[int] = None):
        """
        添加延迟 - 支持多种延迟策略
        
        Args:
            url: 请求URL（用于域名特定延迟）
            response_status: 上一次请求的响应状态码，用于自适应延迟
        """
        if not self.enabled or self.delay_strategy == 'none':
            return
        
        # 基于域名的延迟
        domain_delay = self._get_domain_delay(url) if url else 0
        
        # 策略延迟
        strategy_delay = self._calculate_delay(response_status)
        
        # 总延迟
        total_delay = domain_delay + strategy_delay
        
        if total_delay > 0:
            logger.debug(f"应用延迟: {total_delay:.2f}秒 (域名: {domain_delay:.2f}s, 策略: {strategy_delay:.2f}s)")
            time.sleep(total_delay)
    
    def _calculate_delay(self, response_status: Optional[int] = None) -> float:
        """
        计算延迟时间
        
        Args:
            response_status: 响应状态码
            
        Returns:
            延迟时间（秒）
        """
        self.request_count += 1
        
        if self.delay_strategy == 'fixed':
            return self._fixed_delay()
        elif self.delay_strategy == 'random':
            return self._random_delay()
        elif self.delay_strategy == 'linear':
            return self._linear_delay()
        elif self.delay_strategy == 'exponential':
            return self._exponential_delay()
        elif self.delay_strategy == 'adaptive':
            return self._adaptive_delay(response_status)
        else:
            return 0
    
    def _fixed_delay(self) -> float:
        """固定延迟"""
        if self.delay_range:
            return (self.delay_range[0] + self.delay_range[1]) / 2
        return 1.0
    
    def _random_delay(self) -> float:
        """随机延迟"""
        if self.delay_range:
            return random.uniform(*self.delay_range)
        return random.uniform(1, 3)
    
    def _linear_delay(self) -> float:
        """线性增长延迟"""
        if self.delay_range:
            base, max_delay = self.delay_range
            delay = base + (self.request_count * 0.1)
            return min(delay, max_delay)
        return min(1.0 + (self.request_count * 0.1), 5.0)
    
    def _exponential_delay(self) -> float:
        """指数增长延迟"""
        if self.delay_range:
            base, max_delay = self.delay_range
            delay = base * (1.5 ** (self.request_count // 10))
            return min(delay, max_delay)
        return min(1.0 * (1.5 ** (self.request_count // 10)), 10.0)
    
    def _adaptive_delay(self, response_status: Optional[int] = None) -> float:
        """
        自适应延迟 - 根据响应状态动态调整
        
        Args:
            response_status: HTTP响应状态码
            
        Returns:
            延迟时间（秒）
        """
        config = self.adaptive_config
        
        # 基于响应状态调整
        if response_status:
            if response_status >= 500:  # 服务器错误，增加延迟
                self.error_count += 1
                self.current_delay = min(
                    self.current_delay * config['increase_factor'],
                    config['max_delay']
                )
            elif response_status >= 400:  # 客户端错误，适度增加延迟
                self.error_count += 1
                self.current_delay = min(
                    self.current_delay * 1.2,
                    config['max_delay']
                )
            elif response_status == 200:  # 成功，减少延迟
                self.error_count = max(0, self.error_count - 1)
                self.current_delay = max(
                    self.current_delay * config['decrease_factor'],
                    config['base_delay']
                )
        
        # 基于错误率调整
        if self.request_count > 0:
            error_rate = self.error_count / self.request_count
            if error_rate > 0.3:  # 错误率超过30%，显著增加延迟
                self.current_delay = min(self.current_delay * 2, config['max_delay'])
        
        # 添加随机性
        random_factor = random.uniform(0.8, 1.2)
        final_delay = self.current_delay * random_factor
        
        # 确保在配置范围内
        return min(max(final_delay, config['base_delay']), config['max_delay'])
    
    def get(
        self,
        url: str,
        headers: Optional[Dict] = None,
        params: Optional[Dict] = None,
        custom_delay: bool = True
    ) -> requests.Response:
        """
        发送GET请求
        
        Args:
            url: 请求URL
            headers: 自定义请求头
            params: 查询参数
            custom_delay: 是否添加延迟
            
        Returns:
            Response对象
        """
        # 添加延迟
        if custom_delay:
            self._add_delay(url=url)
        
        # 构建请求头
        request_headers = self._build_headers(headers)
        
        # 获取代理
        proxies = self._get_random_proxy()
        
        try:
            logger.info(f"请求: {url}")
            if proxies:
                logger.info(f"使用代理: {proxies}")
            
            response = self.session.get(
                url,
                headers=request_headers,
                params=params,
                proxies=proxies,
                timeout=self.timeout,
                allow_redirects=True
            )
            
            # 保存cookies
            for cookie in response.cookies:
                self.cookies[cookie.name] = cookie.value
            
            logger.info(f"响应状态: {response.status_code}")
            return response
            
        except Exception as e:
            logger.error(f"请求失败: {url}, 错误: {str(e)}")
            # 请求失败也增加延迟
            if custom_delay:
                self._add_delay(url=url, response_status=500)
            raise
    
    def post(
        self,
        url: str,
        data: Optional[Dict] = None,
        json: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        custom_delay: bool = True
    ) -> requests.Response:
        """
        发送POST请求
        
        Args:
            url: 请求URL
            data: 表单数据
            json: JSON数据
            headers: 自定义请求头
            custom_delay: 是否添加延迟
            
        Returns:
            Response对象
        """
        # 添加延迟
        if custom_delay:
            self._add_delay(url=url)
        
        # 构建请求头
        request_headers = self._build_headers(headers)
        if json:
            request_headers['Content-Type'] = 'application/json'
        
        # 获取代理
        proxies = self._get_random_proxy()
        
        try:
            logger.info(f"POST请求: {url}")
            
            response = self.session.post(
                url,
                data=data,
                json=json,
                headers=request_headers,
                proxies=proxies,
                timeout=self.timeout,
                allow_redirects=True
            )
            
            # 保存cookies
            for cookie in response.cookies:
                self.cookies[cookie.name] = cookie.value
            
            logger.info(f"响应状态: {response.status_code}")
            return response
            
        except Exception as e:
            logger.error(f"POST请求失败: {url}, 错误: {str(e)}")
            # 请求失败也增加延迟
            if custom_delay:
                self._add_delay(url=url, response_status=500)
            raise
    
    def add_cookies(self, cookies: Dict):
        """添加cookies"""
        self.cookies.update(cookies)
        self.session.cookies.update(cookies)
    
    def clear_cookies(self):
        """清除cookies"""
        self.cookies.clear()
        self.session.cookies.clear()
    
    def close(self):
        """关闭会话"""
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class RotatingProxyClient(EnhancedHTTPClient):
    """支持代理轮换的HTTP客户端"""
    
    def __init__(self, proxy_list: List[str], **kwargs):
        """
        初始化代理轮换客户端
        
        Args:
            proxy_list: 代理服务器列表
            **kwargs: 其他参数传递给父类
        """
        super().__init__(proxy_list=proxy_list, use_proxy=True, **kwargs)
        self.current_proxy_index = 0
    
    def _get_random_proxy(self) -> Optional[Dict]:
        """轮换获取代理"""
        if not self.proxy_list:
            return None
        
        # 轮换代理
        proxy_url = self.proxy_list[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_list)
        
        return {
            'http': proxy_url,
            'https': proxy_url
        }


# 工具函数：创建常用代理列表（示例）
def create_default_proxy_list() -> List[str]:
    """创建默认代理列表（示例）"""
    # 注意：这些是示例代理，实际使用时需要替换为有效的代理
    return [
        # "http://proxy1.example.com:8080",
        # "http://proxy2.example.com:8080",
        # "socks5://proxy3.example.com:1080"
    ]


# 工具函数：创建HTTP客户端
def create_client(use_proxy: bool = False, proxy_list: Optional[List[str]] = None) -> EnhancedHTTPClient:
    """
    创建HTTP客户端
    
    Args:
        use_proxy: 是否使用代理
        proxy_list: 代理列表
        
    Returns:
        EnhancedHTTPClient实例
    """
    if use_proxy and proxy_list:
        return RotatingProxyClient(proxy_list=proxy_list)
    else:
        return EnhancedHTTPClient()