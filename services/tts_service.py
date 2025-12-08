"""
语音合成服务 - 调用火山引擎 TTS API
"""
import json
import base64
import logging
import requests
from config import TTS_API_KEY, TTS_API_URL, TTS_RESOURCE_ID, TTS_SPEAKER

logger = logging.getLogger(__name__)


class TTSService:
    """语音合成服务"""
    
    def __init__(self):
        """初始化 TTS 服务"""
        if TTS_API_KEY:
            logger.info(f"TTS 服务初始化完成，音色: {TTS_SPEAKER}")
        else:
            logger.warning("TTS_API_KEY 未配置，语音合成功能将不可用")
    
    def synthesize(self, text: str) -> str:
        """
        生成语音
        
        Args:
            text: 要合成的文本内容
        
        Returns:
            Base64 编码的 MP3 音频数据，失败返回 None
        """
        if not TTS_API_KEY:
            logger.error("TTS_API_KEY 未配置")
            return None

        if not text or len(text.strip()) == 0:
            return None

        headers = {
            "Content-Type": "application/json",
            "x-api-key": TTS_API_KEY,
            "X-Api-Resource-Id": TTS_RESOURCE_ID,
            "Connection": "keep-alive"
        }

        # TTS v3 API 请求格式
        payload = {
            "req_params": {
                "text": text,
                "speaker": TTS_SPEAKER,
                "additions": json.dumps({
                    "disable_markdown_filter": True,
                    "enable_language_detector": True,
                    "enable_latex_tn": True,
                    "disable_default_bit_rate": True,
                    "max_length_to_filter_parenthesis": 0,
                    "cache_config": {
                        "text_type": 1,
                        "use_cache": True
                    }
                }),
                "audio_params": {
                    "format": "mp3",
                    "sample_rate": 24000
                }
            }
        }

        try:
            logger.info(f"正在调用 TTS API，文本: {text}")
            response = requests.post(TTS_API_URL, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            # v3 API 直接返回音频二进制数据
            if response.status_code == 200:
                audio_base64 = base64.b64encode(response.content).decode('utf-8')
                logger.info(f"TTS 合成成功，音频大小: {len(response.content)} bytes")
                return audio_base64
            else:
                logger.error(f"TTS API 响应异常: {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error("TTS API 请求超时")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"TTS API 请求失败: {e}")
            return None

