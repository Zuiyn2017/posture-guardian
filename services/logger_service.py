"""
日志记录服务 - 保存截图和API返回结果
"""
import os
import json
import base64
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class LoggerService:
    """日志记录服务，用于保存检测记录"""
    
    def __init__(self, log_dir: str = "logs"):
        """
        初始化日志服务
        
        Args:
            log_dir: 日志目录路径
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建子目录
        self.images_dir = self.log_dir / "images"
        self.images_dir.mkdir(exist_ok=True)
        
        self.results_dir = self.log_dir / "results"
        self.results_dir.mkdir(exist_ok=True)
        
        logger.info(f"日志服务初始化完成，日志目录: {self.log_dir.absolute()}")
    
    def save_detection_record(self, image_base64: str, api_response: dict, timestamp: datetime = None):
        """
        保存检测记录（截图和API返回结果）
        
        Args:
            image_base64: Base64编码的图片数据
            api_response: API返回的完整结果
            timestamp: 时间戳，如果为None则使用当前时间
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # 格式化时间戳
        time_str = timestamp.strftime("%Y%m%d_%H%M%S_%f")[:-3]  # 精确到毫秒
        date_str = timestamp.strftime("%Y-%m-%d")
        
        try:
            # 1. 保存图片
            image_filename = f"{time_str}.jpg"
            image_path = self.images_dir / image_filename
            
            # 解码并保存图片
            image_data = base64.b64decode(image_base64)
            with open(image_path, 'wb') as f:
                f.write(image_data)
            
            # 2. 保存API返回结果（JSON格式）
            result_filename = f"{time_str}.json"
            result_path = self.results_dir / result_filename
            
            # 构建完整的记录
            record = {
                "timestamp": timestamp.isoformat(),
                "time_str": time_str,
                "date": date_str,
                "image_filename": image_filename,
                "api_response": api_response
            }
            
            with open(result_path, 'w', encoding='utf-8') as f:
                json.dump(record, f, ensure_ascii=False, indent=2)
            
            logger.info(f"检测记录已保存: {time_str} - 图片: {image_filename}, 结果: {result_filename}")
            
            return {
                "success": True,
                "image_path": str(image_path),
                "result_path": str(result_path),
                "timestamp": timestamp.isoformat()
            }
            
        except Exception as e:
            logger.error(f"保存检测记录失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_detection_records(self, date: str = None, limit: int = 100):
        """
        获取检测记录列表
        
        Args:
            date: 日期字符串 (YYYY-MM-DD)，如果为None则返回所有记录
            limit: 返回记录数量限制
        
        Returns:
            记录列表
        """
        records = []
        
        try:
            if date:
                # 按日期筛选
                pattern = f"{date}_*.json"
            else:
                pattern = "*.json"
            
            result_files = sorted(self.results_dir.glob(pattern), reverse=True)[:limit]
            
            for result_file in result_files:
                try:
                    with open(result_file, 'r', encoding='utf-8') as f:
                        record = json.load(f)
                        records.append(record)
                except Exception as e:
                    logger.warning(f"读取记录文件失败 {result_file}: {e}")
            
            return records
            
        except Exception as e:
            logger.error(f"获取检测记录失败: {e}")
            return []

