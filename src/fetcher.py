#!/usr/bin/env python3
"""
RSS数据抓取模块 - 使用增强HTTP客户端
"""
import feedparser
import requests
from datetime import datetime
from typing import List, Dict, Optional
import logging
from enhanced_client import create_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RSSFetcher:
    """RSS源数据抓取器"""
    
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
    
    def fetch_feed(self, url: str, max_items: int = 20) -> List[Dict]:
        """
        抓取RSS源数据
        
        Args:
            url: RSS源URL
            max_items: 最多抓取条数
            
        Returns:
            包含文章信息的字典列表
        """
        try:
            logger.info(f"正在抓取RSS源: {url}")
            
            if self.use_enhanced_client and self.client:
                # 使用增强客户端获取RSS内容
                try:
                    response = self.client.get(url)
                    rss_content = response.text
                    # 使用feedparser解析内容
                    feed = feedparser.parse(rss_content)
                except Exception as e:
                    logger.warning(f"增强客户端抓取失败，回退到直接解析: {str(e)}")
                    feed = feedparser.parse(url)
            else:
                # 使用传统方式
                feed = feedparser.parse(url)
            
            if feed.bozo:
                logger.warning(f"RSS源可能有问题: {url}, 错误: {feed.bozo}")
            
            items = []
            for entry in feed.entries[:max_items]:
                item = {
                    'title': entry.get('title', ''),
                    'link': entry.get('link', ''),
                    'description': entry.get('description', ''),
                    'published': self._parse_date(entry.get('published')),
                    'source': feed.feed.get('title', url),
                    'source_url': url
                }
                items.append(item)
            
            logger.info(f"成功抓取 {len(items)} 条数据")
            return items
            
        except Exception as e:
            logger.error(f"抓取RSS源失败 {url}: {str(e)}")
            return []
    
    def close(self):
        """关闭客户端连接"""
        if self.client:
            self.client.close()
        elif self.session:
            self.session.close()
    
    def _parse_date(self, date_str: Optional[str]) -> str:
        """解析日期字符串"""
        if not date_str:
            return datetime.now().strftime('%Y-%m-%d %H:%M')
        
        try:
            from dateutil import parser
            dt = parser.parse(date_str)
            return dt.strftime('%Y-%m-%d %H:%M')
        except:
            return date_str
    
    def fetch_multiple_sources(self, sources: List[Dict], max_items: int = 20) -> List[Dict]:
        """
        批量抓取多个RSS源
        
        Args:
            sources: RSS源配置列表，每个包含name和url
            max_items: 每个源最多抓取条数
            
        Returns:
            所有文章的合并列表
        """
        all_items = []
        
        for source in sources:
            url = source.get('url')
            name = source.get('name', url)
            category = source.get('category', '未分类')
            
            items = self.fetch_feed(url, max_items)
            
            # 添加分类信息
            for item in items:
                item['source_name'] = name
                item['category'] = category
            
            all_items.extend(items)
        
        return all_items
    
    def _parse_date(self, date_str: Optional[str]) -> str:
        """解析日期字符串"""
        if not date_str:
            return datetime.now().strftime('%Y-%m-%d %H:%M')
        
        try:
            from dateutil import parser
            dt = parser.parse(date_str)
            return dt.strftime('%Y-%m-%d %H:%M')
        except:
            return date_str
    
    def fetch_multiple_sources(self, sources: List[Dict], max_items: int = 20) -> List[Dict]:
        """
        批量抓取多个RSS源
        
        Args:
            sources: RSS源配置列表，每个包含name和url
            max_items: 每个源最多抓取条数
            
        Returns:
            所有文章的合并列表
        """
        all_items = []
        
        for source in sources:
            url = source.get('url')
            name = source.get('name', url)
            category = source.get('category', '未分类')
            
            items = self.fetch_feed(url, max_items)
            
            # 添加分类信息
            for item in items:
                item['source_name'] = name
                item['category'] = category
            
            all_items.extend(items)
        
        return all_items