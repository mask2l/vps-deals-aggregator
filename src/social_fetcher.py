#!/usr/bin/env python3
"""
社交媒体数据抓取模块 - 使用增强HTTP客户端
"""
from typing import List, Dict, Optional
from datetime import datetime
import logging
import os
from enhanced_client import create_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SocialFetcher:
    """社交媒体数据抓取器"""
    
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
    
    def fetch_twitter_search(self, query: str, max_items: int = 20, api_key: Optional[str] = None) -> List[Dict]:
        """
        搜索Twitter相关推文
        
        Args:
            query: 搜索查询
            max_items: 最多抓取条数
            api_key: Twitter API密钥（可选，不提供则使用公开RSS）
            
        Returns:
            包含推文信息的字典列表
        """
        try:
            logger.info(f"正在搜索Twitter: {query}")
            
            # 使用Twitter的公开RSS搜索功能
            # 注意：这种方式可能有限制，生产环境建议使用官方API
            import urllib.parse
            encoded_query = urllib.parse.quote(query)
            rss_url = f"https://nitter.net/search?q={encoded_query}&f=tweets&rss"
            
            try:
                import feedparser
                feed = feedparser.parse(rss_url)
                
                if feed.bozo:
                    logger.warning(f"Twitter RSS可能有问题，错误: {feed.bozo}")
                
                items = []
                for entry in feed.entries[:max_items]:
                    try:
                        # 提取作者信息
                        author = entry.get('author', 'Unknown')
                        
                        # 提取推文内容
                        content = entry.get('description', entry.get('summary', ''))
                        
                        # 清理HTML标签
                        import re
                        content = re.sub(r'<[^>]+>', '', content)
                        
                        item = {
                            'title': f"@{author}: {content[:100]}",
                            'link': entry.get('link', ''),
                            'description': content[:300],
                            'published': self._parse_twitter_date(entry.get('published')),
                            'source': 'Twitter',
                            'source_url': rss_url,
                            'author': author,
                            'social_platform': 'twitter'
                        }
                        
                        items.append(item)
                        
                    except Exception as e:
                        logger.warning(f"解析Twitter推文失败: {str(e)}")
                        continue
                
                logger.info(f"成功抓取 {len(items)} 条Twitter数据")
                return items
                
            except ImportError:
                logger.warning("feedparser未安装，使用备用方法")
                return self._fetch_twitter_fallback(query, max_items)
            
        except Exception as e:
            logger.error(f"搜索Twitter失败: {str(e)}")
            return []
    
    def _fetch_twitter_fallback(self, query: str, max_items: int = 20) -> List[Dict]:
        """
        Twitter备用抓取方法（使用Nitter公开实例）
        
        Args:
            query: 搜索查询
            max_items: 最多抓取条数
            
        Returns:
            包含推文信息的字典列表
        """
        try:
            # 使用Nitter公开实例
            nitter_instances = [
                'https://nitter.net',
                'https://nitter.poast.org',
                'https://nitter.privacydev.net'
            ]
            
            for instance in nitter_instances:
                try:
                    import urllib.parse
                    encoded_query = urllib.parse.quote(query)
                    url = f"{instance}/search?q={encoded_query}&f=tweets"
                    
                    html_content = self._get_response(url)
                    if not html_content:
                        continue
                    
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    items = []
                    tweets = soup.select('div.timeline-item')[:max_items]
                    
                    for tweet in tweets:
                        try:
                            # 提取推文内容
                            content_elem = tweet.select_one('div.tweet-content')
                            content = content_elem.get_text(strip=True) if content_elem else ""
                            
                            # 提取作者
                            author_elem = tweet.select_one('a.username')
                            author = author_elem.get_text(strip=True) if author_elem else "Unknown"
                            
                            # 提取时间
                            time_elem = tweet.select_one('span.tweet-date')
                            date_str = time_elem.get_text(strip=True) if time_elem else ""
                            
                            # 提取链接
                            link_elem = tweet.select_one('a.tweet-link')
                            link = link_elem.get('href') if link_elem else ""
                            if link and not link.startswith('http'):
                                link = f"{instance}{link}"
                            
                            item = {
                                'title': f"@{author}: {content[:100]}",
                                'link': link,
                                'description': content[:300],
                                'published': self._parse_twitter_date(date_str),
                                'source': 'Twitter (Nitter)',
                                'source_url': url,
                                'author': author,
                                'social_platform': 'twitter'
                            }
                            
                            items.append(item)
                            
                        except Exception as e:
                            logger.warning(f"解析推文失败: {str(e)}")
                            continue
                    
                    if items:
                        logger.info(f"成功抓取 {len(items)} 条Twitter数据")
                        return items
                        
                except Exception as e:
                    logger.warning(f"Nitter实例 {instance} 失败: {str(e)}")
                    continue
            
            logger.warning("所有Nitter实例都失败")
            return []
            
        except Exception as e:
            logger.error(f"Twitter备用抓取失败: {str(e)}")
            return []
    
    def fetch_reddit(self, subreddit: str, max_items: int = 20) -> List[Dict]:
        """
        抓取Reddit子版块
        
        Args:
            subreddit: 子版块名称（如VPSDeals）
            max_items: 最多抓取条数
            
        Returns:
            包含帖子信息的字典列表
        """
        try:
            logger.info(f"正在抓取Reddit: r/{subreddit}")
            
            rss_url = f"https://www.reddit.com/r/{subreddit}/.rss"
            
            try:
                import feedparser
                feed = feedparser.parse(rss_url)
                
                if feed.bozo:
                    logger.warning(f"Reddit RSS可能有问题，错误: {feed.bozo}")
                
                items = []
                for entry in feed.entries[:max_items]:
                    try:
                        # 清理HTML标签
                        import re
                        description = entry.get('description', '')
                        description = re.sub(r'<[^>]+>', '', description)
                        
                        item = {
                            'title': entry.get('title', ''),
                            'link': entry.get('link', ''),
                            'description': description[:300],
                            'published': self._parse_reddit_date(entry.get('published')),
                            'source': f'Reddit r/{subreddit}',
                            'source_url': rss_url,
                            'author': entry.get('author', 'Unknown'),
                            'social_platform': 'reddit'
                        }
                        
                        items.append(item)
                        
                    except Exception as e:
                        logger.warning(f"解析Reddit帖子失败: {str(e)}")
                        continue
                
                logger.info(f"成功抓取 {len(items)} 条Reddit数据")
                return items
                
            except ImportError:
                logger.error("feedparser未安装")
                return []
            
        except Exception as e:
            logger.error(f"抓取Reddit失败: {str(e)}")
            return []
    
    def _parse_twitter_date(self, date_str: str) -> str:
        """解析Twitter日期字符串"""
        if not date_str:
            return datetime.now().strftime('%Y-%m-%d %H:%M')
        
        try:
            from dateutil import parser
            dt = parser.parse(date_str)
            return dt.strftime('%Y-%m-%d %H:%M')
        except:
            return date_str
    
    def _parse_reddit_date(self, date_str: str) -> str:
        """解析Reddit日期字符串"""
        if not date_str:
            return datetime.now().strftime('%Y-%m-%d %H:%M')
        
        try:
            from dateutil import parser
            dt = parser.parse(date_str)
            return dt.strftime('%Y-%m-%d %H:%M')
        except:
            return date_str
    
    def fetch_multiple_social(self, sources: List[Dict], max_items: int = 20) -> List[Dict]:
        """
        批量抓取多个社交媒体源
        
        Args:
            sources: 社交媒体源配置列表
            max_items: 每个源最多抓取条数
            
        Returns:
            所有内容的合并列表
        """
        all_items = []
        
        for source in sources:
            platform = source.get('platform', '').lower()
            name = source.get('name', platform)
            category = source.get('category', '社交媒体')
            
            if platform == 'twitter':
                query = source.get('query', '')
                items = self.fetch_twitter_search(query, max_items)
            elif platform == 'reddit':
                subreddit = source.get('subreddit', source.get('query', ''))
                items = self.fetch_reddit(subreddit, max_items)
            else:
                logger.warning(f"不支持的社交媒体平台: {platform}")
                continue
            
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