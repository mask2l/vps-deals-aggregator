#!/usr/bin/env python3
"""
主程序 - 协调各个模块
"""
import yaml
import sys
import os
from fetcher import RSSFetcher
from forum_fetcher import ForumFetcher
from social_fetcher import SocialFetcher
from processor import DealProcessor
from generator import HTMLGenerator
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config(config_path: str = 'config.yaml') -> dict:
    """加载配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        logger.info(f"配置文件加载成功: {config_path}")
        return config
    except Exception as e:
        logger.error(f"配置文件加载失败: {str(e)}")
        raise

def setup_logging(config: dict):
    """配置日志"""
    logging_config = config.get('logging', {})
    log_level = logging_config.get('level', 'INFO')
    log_format = logging_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format
    )
    
def get_http_client_config(config: dict) -> dict:
    """获取HTTP客户端配置"""
    http_config = config.get('http_client', {})
    return {
        'enabled': http_config.get('enabled', True),
        'use_proxy': http_config.get('use_proxy', False),
        'proxy_list': http_config.get('proxy_list', []),
        'max_retries': http_config.get('max_retries', 3),
        'timeout': http_config.get('timeout', 30),
        'delay_range': tuple(http_config.get('delay_range', [2, 5])),
        'delay_strategy': http_config.get('delay_strategy', 'random'),
        'adaptive_delay_config': http_config.get('adaptive_delay', {})
    }


def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("VPS优惠汇总工具启动")
    logger.info("=" * 50)
    
    # 切换到项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)
    
    try:
        # 加载配置
        config = load_config()
        
        # 配置日志
        setup_logging(config)
        
        # 获取HTTP客户端配置
        http_config = get_http_client_config(config)
        
        rss_sources = config.get('rss_sources', [])
        forum_sources = config.get('forum_sources', [])
        social_sources = config.get('social_sources', [])
        settings = config.get('settings', {})
        max_items = settings.get('max_items_per_source', 20)
        output_dir = settings.get('output_dir', 'docs')
        
        all_items = []
        
        # 抓取RSS数据
        fetcher = None
        if rss_sources:
            logger.info(f"RSS源数量: {len(rss_sources)}")
            logger.info(f"每个源最多抓取: {max_items} 条")
            logger.info(f"延迟策略: {http_config['delay_strategy']}")
            
            fetcher = RSSFetcher(
                timeout=http_config['timeout'],
                use_enhanced_client=http_config['enabled']
            )
            # 如果启用了增强客户端，设置延迟配置
            if fetcher.client:
                fetcher.client.delay_strategy = http_config['delay_strategy']
                fetcher.client.delay_range = http_config['delay_range']
                fetcher.client.adaptive_config = http_config['adaptive_delay_config']
                
            logger.info("开始抓取RSS数据...")
            rss_items = fetcher.fetch_multiple_sources(rss_sources, max_items)
            all_items.extend(rss_items)
            logger.info(f"RSS抓取到 {len(rss_items)} 条数据")
        
        # 抓取论坛数据
        forum_fetcher = None
        if forum_sources:
            logger.info(f"论坛源数量: {len(forum_sources)}")
            
            forum_fetcher = ForumFetcher(
                timeout=http_config['timeout'],
                use_enhanced_client=http_config['enabled']
            )
            # 如果启用了增强客户端，设置延迟配置
            if forum_fetcher.client:
                forum_fetcher.client.delay_strategy = http_config['delay_strategy']
                forum_fetcher.client.delay_range = http_config['delay_range']
                forum_fetcher.client.adaptive_config = http_config['adaptive_delay_config']
                
            logger.info("开始抓取论坛数据...")
            forum_items = forum_fetcher.fetch_multiple_forums(forum_sources, max_items)
            all_items.extend(forum_items)
            logger.info(f"论坛抓取到 {len(forum_items)} 条数据")
        
        # 抓取社交媒体数据
        social_fetcher = None
        if social_sources:
            logger.info(f"社交媒体源数量: {len(social_sources)}")
            
            social_fetcher = SocialFetcher(
                timeout=http_config['timeout'],
                use_enhanced_client=http_config['enabled']
            )
            # 如果启用了增强客户端，设置延迟配置
            if social_fetcher.client:
                social_fetcher.client.delay_strategy = http_config['delay_strategy']
                social_fetcher.client.delay_range = http_config['delay_range']
                social_fetcher.client.adaptive_config = http_config['adaptive_delay_config']
                
            logger.info("开始抓取社交媒体数据...")
            social_items = social_fetcher.fetch_multiple_social(social_sources, max_items)
            all_items.extend(social_items)
            logger.info(f"社交媒体抓取到 {len(social_items)} 条数据")
        
        logger.info(f"总共抓取到 {len(all_items)} 条数据")
        
        # 处理数据
        processor = DealProcessor()
        logger.info("开始处理数据...")
        deal_items = processor.process(all_items)
        logger.info(f"处理后保留 {len(deal_items)} 条优惠信息")
        
        # 生成HTML
        generator = HTMLGenerator()
        output_path = os.path.join(output_dir, 'index.html')
        logger.info("开始生成HTML...")
        generator.generate_index(deal_items, output_path)
        
        logger.info("=" * 50)
        logger.info("VPS优惠汇总工具运行完成")
        logger.info(f"输出文件: {output_path}")
        logger.info("=" * 50)
        
        # 清理资源
        if fetcher:
            fetcher.close()
        if forum_fetcher:
            forum_fetcher.close()
        if social_fetcher:
            social_fetcher.close()
        
    except Exception as e:
        logger.error(f"程序运行出错: {str(e)}")
        
        # 确保在出错时也清理资源
        if fetcher:
            try:
                fetcher.close()
            except:
                pass
        if forum_fetcher:
            try:
                forum_fetcher.close()
            except:
                pass
        if social_fetcher:
            try:
                social_fetcher.close()
            except:
                pass
        
        sys.exit(1)


if __name__ == '__main__':
    main()