#!/usr/bin/env python3
"""
HTML生成模块 - 生成静态HTML页面
"""
from jinja2 import Template, Environment, FileSystemLoader
from typing import List, Dict
from datetime import datetime
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HTMLGenerator:
    """HTML页面生成器"""
    
    def __init__(self, template_dir: str = 'templates'):
        self.env = Environment(loader=FileSystemLoader(template_dir))
    
    def generate_index(self, items: List[Dict], output_path: str = 'docs/index.html'):
        """
        生成首页HTML
        
        Args:
            items: 优惠信息列表
            output_path: 输出文件路径
        """
        try:
            template = self.env.get_template('index.html')
            
            # 准备模板数据
            context = {
                'deals': items,
                'total_count': len(items),
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'categories': self._group_by_category(items)
            }
            
            # 渲染HTML
            html_content = template.render(**context)
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 写入文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"HTML生成成功: {output_path}")
            
        except Exception as e:
            logger.error(f"HTML生成失败: {str(e)}")
            raise
    
    def _group_by_category(self, items: List[Dict]) -> Dict:
        """按分类分组"""
        categories = {}
        for item in items:
            category = item.get('category', '未分类')
            if category not in categories:
                categories[category] = []
            categories[category].append(item)
        return categories