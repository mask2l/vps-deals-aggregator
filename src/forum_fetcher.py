#!/usr/bin/env python3
"""
论坛数据抓取模块 - 使用增强HTTP客户端
"""
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime
import logging
import re
from enhanced_client import create_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ForumFetcher:
    """论坛数据抓取器"""
    
    def __init__(self, timeout: int = 30, use_enhanced_client: bool = True):
        self.timeout = timeout
        self.use_enhanced_client = use_enhanced_client
        
        if use_enhanced_client:
            # 使用增强HTTP客户端
            self.client = create_client(use_proxy=False)
            self.session = None
        else:
            # 使用传统requests
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            self.client = None
    
    def _get_response(self, url: str) -> Optional[str]:
        """
        获取HTTP响应内容
        
        Args:
            url: 请求URL
            
        Returns:
            响应内容文本
        """
        try:
            if self.use_enhanced_client and self.client:
                response = self.client.get(url)
                return response.text
            elif self.session:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response.text
            else:
                return None
        except Exception as e:
            logger.error(f"HTTP请求失败: {url}, 错误: {str(e)}")
            return None
    
    def fetch_wht_offers(self, url: str, max_items: int = 20) -> List[Dict]:
        """
        抓取WebHostingTalk优惠板块
        
        Args:
            url: 论坛URL
            max_items: 最多抓取条数
            
        Returns:
            包含优惠信息的字典列表
        """
        try:
            logger.info(f"正在抓取WHT论坛: {url}")
            
            html_content = self._get_response(url)
            if not html_content:
                return []
            
            soup = BeautifulSoup(html_content, 'html.parser')
            items = []
            
            # WHT论坛的帖子结构解析
            thread_rows = soup.select('tr.threadbit')
            
            for row in thread_rows[:max_items]:
                try:
                    # 提取标题和链接
                    title_elem = row.select_one('a.title')
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    link = title_elem.get('href')
                    if link and not link.startswith('http'):
                        link = f"https://www.webhostingtalk.com/{link}"
                    
                    # 提取作者
                    author_elem = row.select_one('a.username')
                    author = author_elem.get_text(strip=True) if author_elem else "Unknown"
                    
                    # 提取回复数
                    replies_elem = row.select_one('td.replies')
                    replies = replies_elem.get_text(strip=True) if replies_elem else "0"
                    
                    # 提取最后回复时间
                    date_elem = row.select_one('td.lastpost')
                    date_str = date_elem.get_text(strip=True) if date_elem else ""
                    
                    item = {
                        'title': title,
                        'link': link,
                        'description': f"作者: {author} | 回复: {replies}",
                        'published': self._parse_forum_date(date_str),
                        'source': 'WebHostingTalk',
                        'source_url': url,
                        'author': author,
                        'replies': replies
                    }
                    
                    items.append(item)
                    
                except Exception as e:
                    logger.warning(f"解析WHT帖子失败: {str(e)}")
                    continue
            
            logger.info(f"成功抓取 {len(items)} 条WHT数据")
            return items
            
        except Exception as e:
            logger.error(f"抓取WHT论坛失败: {str(e)}")
            return []
    
    def fetch_generic_forum(self, url: str, max_items: int = 20) -> List[Dict]:
        """
        通用论坛抓取方法
        
        Args:
            url: 论坛URL
            max_items: 最多抓取条数
            
        Returns:
            包含优惠信息的字典列表
        """
        try:
            logger.info(f"正在抓取通用论坛: {url}")
            
            html_content = self._get_response(url)
            if not html_content:
                return []
            
            soup = BeautifulSoup(html_content, 'html.parser')
            items = []
            
            # 通用论坛通常使用相似的HTML结构
            # 尝试匹配常见的帖子选择器
            selectors = [
                'tr.thread-row',
                'div.thread',
                'article.post',
                'div.topic',
                'li.thread'
            ]
            
            posts = []
            for selector in selectors:
                posts = soup.select(selector)
                if posts:
                    break
            
            for post in posts[:max_items]:
                try:
                    # 尝试提取标题和链接
                    title_elem = post.select_one('a[title], a.thread-title, h3 a, h2 a')
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    link = title_elem.get('href')
                    if link and not link.startswith('http'):
                        base_url = re.match(r'https?://[^/]+', url).group()
                        link = f"{base_url}{link}"
                    
                    # 提取描述
                    desc_elem = post.select_one('div.content, p.description, div.excerpt')
                    description = desc_elem.get_text(strip=True) if desc_elem else ""
                    
                    # 提取时间
                    time_elem = post.select_one('time, span.date, span.time')
                    date_str = time_elem.get_text(strip=True) if time_elem else ""
                    
                    item = {
                        'title': title,
                        'link': link,
                        'description': description[:200],
                        'published': self._parse_forum_date(date_str),
                        'source': self._extract_domain(url),
                        'source_url': url
                    }
                    
                    items.append(item)
                    
                except Exception as e:
                    logger.warning(f"解析论坛帖子失败: {str(e)}")
                    continue
            
            logger.info(f"成功抓取 {len(items)} 条通用论坛数据")
            return items
            
        except Exception as e:
            logger.error(f"抓取通用论坛失败: {str(e)}")
            return []
    
    def _parse_forum_date(self, date_str: str) -> str:
        """解析论坛日期字符串"""
        if not date_str:
            return datetime.now().strftime('%Y-%m-%d %H:%M')
        
        # 常见的论坛日期格式
        try:
            from dateutil import parser
            dt = parser.parse(date_str)
            return dt.strftime('%Y-%m-%d %H:%M')
        except:
            return date_str
    
    def _extract_domain(self, url: str) -> str:
        """提取域名作为源名称"""
        match = re.match(r'https?://(?:www\.)?([^/]+)', url)
        return match.group(1) if match else url
    
    def fetch_multiple_forums(self, sources: List[Dict], max_items: int = 20) -> List[Dict]:
        """
        批量抓取多个论坛
        
        Args:
            sources: 论坛源配置列表
            max_items: 每个源最多抓取条数
            
        Returns:
            所有帖子的合并列表
        """
        all_items = []
        
        for source in sources:
            url = source.get('url')
            name = source.get('name', url)
            category = source.get('category', '论坛')
            parser_type = source.get('parser', 'generic')
            
            if parser_type == 'wht':
                items = self.fetch_wht_offers(url, max_items)
            else:
                items = self.fetch_generic_forum(url, max_items)
            
            # 添加分类信息
            for item in items:
                item['source_name'] = name
                item['category'] = category
            
            all_items.extend(items)
        
        return all_items
    
    def close(self):
        """关闭客户端连接"""
        if self.client:
            self.client.close()
        elif self.session:
            self.session.close()