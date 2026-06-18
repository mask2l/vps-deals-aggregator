#!/usr/bin/env python3
"""
数据处理模块 - 过滤、排序、去重
"""
from typing import List, Dict
from datetime import datetime
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DealProcessor:
    """优惠信息处理器"""
    
    # 关键词匹配 - 中英文关键词
    DEAL_KEYWORDS = [
        # 中文关键词
        r'优惠', r'折扣', r'促销', r'特价', r'秒杀', r'限时', r'立减',
        r'优惠券', r'代金券', r'红包', r'满减', r'返现', r'赠品',
        
        # 英文基础关键词
        r'sale', r'discount', r'deal', r'offer', r'coupon', r'promo',
        r'promotion', r'bargain', r'cheap', r'cheap(er)', r'lowest',
        r'best price', r'hot deal', r'special offer', r'limited time',
        r'flash sale', r'clearance', r'save', r'saving', r'rebate',
        r'cashback', r'cash back', r'free', r'bonus', r'gift',
        
        # VPS/主机相关关键词
        r'vps', r'virtual private server', r'dedicated server', r'dedicated',
        r'cloud server', r'cloud hosting', r'web hosting', r'hosting',
        r'shared hosting', r'reseller hosting', r'wordpress hosting',
        r'minecraft hosting', r'game server', r'server', r'vpn',
        
        # 价格相关
        r'\$\d+', r'usd', r'euro', r'eur', r'gbp', r'price', r'cost',
        r'per month', r'/month', r'/mo', r'per year', r'/year', r'/yr',
        r'per year', r'annually', r'monthly', r'quarterly',
        r'percent off', r'% off', r'% off', r'\d+%',
        
        # 商户相关
        r'digitalocean', r'linode', r'vultr', r'aws', r'azure',
        r'google cloud', r'hetzner', r'ovh', r'scaleway', r'do',
        
        # 地域相关
        r'usa', r'us', r'uk', r'europe', r'asia', r'singapore',
        r'tokyo', r'hong kong', r'hk', r'germany', r'france',
        
        # 配置相关
        r'ram', r'cpu', r'ssd', r'nvme', r'bandwidth', r'traffic',
        r'ipv4', r'ipv6', r'cpu core', r'vcpu', r'thread',
        
        # 其他促销词汇
        r'bundle', r'package', r'plan', r'tier', r'upgrade',
        r'migration', r'transfer', r'new customer', r'new user',
        r'existing customer', r'renewal', r'extension', r'expiring',
        
        # 紧急程度
        r'ending soon', r'last chance', r'final', r'expires',
        r'deadline', r'available', r'stock', r'limited'
    ]
    
    def __init__(self):
        self.patterns = [re.compile(keyword, re.IGNORECASE) for keyword in self.DEAL_KEYWORDS]
    
    def filter_deals(self, items: List[Dict]) -> List[Dict]:
        """
        过滤出优惠相关内容
        
        Args:
            items: 原始文章列表
            
        Returns:
            过滤后的优惠信息列表
        """
        deal_items = []
        
        for item in items:
            title = item.get('title', '').lower()
            description = item.get('description', '').lower()
            combined_text = f"{title} {description}"
            
            # 检查是否包含优惠关键词
            is_deal = any(pattern.search(combined_text) for pattern in self.patterns)
            
            if is_deal:
                deal_items.append(item)
        
        logger.info(f"过滤后保留 {len(deal_items)} 条优惠信息")
        return deal_items
    
    def remove_duplicates(self, items: List[Dict]) -> List[Dict]:
        """
        去重（基于标题和链接）
        
        Args:
            items: 文章列表
            
        Returns:
            去重后的列表
        """
        seen = set()
        unique_items = []
        
        for item in items:
            # 使用标题和链接作为去重依据
            key = (item.get('title', ''), item.get('link', ''))
            if key not in seen:
                seen.add(key)
                unique_items.append(item)
        
        if len(items) != len(unique_items):
            logger.info(f"去重: {len(items)} -> {len(unique_items)}")
        
        return unique_items
    
    def sort_by_date(self, items: List[Dict]) -> List[Dict]:
        """
        按日期排序（最新的在前）
        
        Args:
            items: 文章列表
            
        Returns:
            排序后的列表
        """
        def parse_date(item):
            try:
                date_str = item.get('published', '')
                from dateutil import parser
                return parser.parse(date_str)
            except:
                return datetime.min
        
        sorted_items = sorted(items, key=parse_date, reverse=True)
        return sorted_items
    
    def truncate_description(self, item: Dict) -> Dict:
        """
        截取描述，特别是针对Reddit内容
        
        Args:
            item: 原始文章项
            
        Returns:
            处理后的文章项
        """
        description = item.get('description', '')
        source_name = item.get('source_name', '')
        
        # 对Reddit内容进行特殊处理
        if 'reddit' in source_name.lower():
            # 移除HTML标签
            clean_desc = re.sub(r'<[^>]+>', '', description)
            # 移除多余的空白
            clean_desc = re.sub(r'\s+', ' ', clean_desc).strip()
            # 截取到100字符
            if len(clean_desc) > 100:
                clean_desc = clean_desc[:97] + '...'
            item['description'] = clean_desc
        else:
            # 其他来源截取到150字符
            if len(description) > 150:
                clean_desc = re.sub(r'<[^>]+>', '', description)
                clean_desc = re.sub(r'\s+', ' ', clean_desc).strip()
                item['description'] = clean_desc[:147] + '...'
        
        return item
    
    def process(self, items: List[Dict]) -> List[Dict]:
        """
        完整处理流程：过滤 -> 截取描述 -> 去重 -> 排序
        
        Args:
            items: 原始文章列表
            
        Returns:
            处理后的优惠信息列表
        """
        # 过滤优惠信息
        deals = self.filter_deals(items)
        
        # 截取描述（特别是Reddit内容）
        deals = [self.truncate_description(deal) for deal in deals]
        
        # 去重
        unique_deals = self.remove_duplicates(deals)
        
        # 排序
        sorted_deals = self.sort_by_date(unique_deals)
        
        return sorted_deals