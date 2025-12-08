"""
视觉分析服务 - 调用 Doubao Vision API
"""
import json
import logging
from openai import OpenAI
from config import ARK_API_KEY, ARK_MODEL_NAME, ARK_BASE_URL, POSTURE_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class VisionService:
    """视觉分析服务"""
    
    def __init__(self):
        """初始化视觉分析服务"""
        self.client = None
        if ARK_API_KEY:
            self.client = OpenAI(
                base_url=ARK_BASE_URL,
                api_key=ARK_API_KEY,
            )
            logger.info(f"视觉分析服务初始化完成，模型: {ARK_MODEL_NAME}")
        else:
            logger.warning("ARK_API_KEY 未配置，视觉分析功能将不可用")
    
    def analyze_posture(self, image_base64: str) -> tuple:
        """
        分析坐姿
        
        Args:
            image_base64: Base64 编码的图片数据 (不含 data:image/xxx;base64, 前缀)
        
        Returns:
            (parsed_result, full_response_dict) 元组：
            - parsed_result: 解析后的结果字典，包含 score, is_qualified, issues, suggestion 等字段
            - full_response_dict: 完整的响应对象（转换为字典），包含所有字段和思考过程
        """
        if not self.client:
            logger.error("视觉分析服务未初始化")
            return None, None

        # 构建提示词
        prompt_text = f"""{POSTURE_SYSTEM_PROMPT}

请评估这张图片中的坐姿。"""

        try:
            logger.info("正在调用 Doubao Vision API...")
            
            # 调用 API
            response = self.client.responses.create(
                model=ARK_MODEL_NAME,
                input=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_image",
                                "image_url": f"data:image/jpeg;base64,{image_base64}"
                            },
                            {
                                "type": "input_text",
                                "text": prompt_text
                            },
                        ],
                    }
                ]
            )
            
            # 先提取返回内容用于解析（在转换前）
            content = self._extract_content(response)
            
            if not content:
                logger.error("无法从响应中提取内容")
                logger.error(f"响应类型: {type(response)}")
                logger.error(f"响应属性: {dir(response)}")
                if hasattr(response, 'output'):
                    logger.error(f"output内容: {response.output}")
                # 即使提取失败，也尝试转换完整响应
                full_response_dict = self._response_to_dict(response)
                return None, full_response_dict
            
            # 将完整响应对象转换为字典（包含所有字段和思考过程）
            full_response_dict = self._response_to_dict(response)
            
            # 清理并解析 JSON
            content = self._clean_json_content(content)
            parsed_result = json.loads(content)
            
            logger.info(f"视觉分析完成: status={parsed_result.get('status')}, score={parsed_result.get('score')}")
            
            return parsed_result, full_response_dict
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败: {e}, 原始内容: {content[:200]}")
            # 即使解析失败，也返回完整的响应对象
            full_response_dict = self._response_to_dict(response) if 'response' in locals() else None
            return None, full_response_dict
        except Exception as e:
            logger.error(f"视觉分析失败: {e}")
            return None, None
    
    def _response_to_dict(self, response) -> dict:
        """
        将响应对象转换为字典，保留所有字段包括思考过程
        
        Args:
            response: API 响应对象
        
        Returns:
            完整的响应字典
        """
        try:
            # 使用 Pydantic 模型的 dict() 方法或 model_dump()
            if hasattr(response, 'model_dump'):
                return response.model_dump()
            elif hasattr(response, 'dict'):
                return response.dict()
            elif hasattr(response, '__dict__'):
                # 手动转换
                result = {}
                for key, value in response.__dict__.items():
                    if key.startswith('_'):
                        continue
                    result[key] = self._convert_value(value)
                return result
            else:
                # 尝试转换为字符串再解析
                return {"raw_response": str(response)}
        except Exception as e:
            logger.warning(f"转换响应对象失败: {e}")
            return {"error": str(e), "raw_response": str(response)}
    
    def _convert_value(self, value):
        """
        递归转换值，处理嵌套对象
        
        Args:
            value: 要转换的值
        
        Returns:
            转换后的值
        """
        if hasattr(value, 'model_dump'):
            return value.model_dump()
        elif hasattr(value, 'dict'):
            return value.dict()
        elif isinstance(value, list):
            return [self._convert_value(item) for item in value]
        elif isinstance(value, dict):
            return {k: self._convert_value(v) for k, v in value.items()}
        elif hasattr(value, '__dict__'):
            return {k: self._convert_value(v) for k, v in value.__dict__.items() if not k.startswith('_')}
        else:
            return value
    
    def _extract_content(self, response) -> str:
        """
        从响应中提取文本内容
        
        Args:
            response: API 响应对象
        
        Returns:
            提取的文本内容
        """
        content = None
        
        # 尝试不同的响应结构
        if hasattr(response, 'output'):
            output = response.output
            
            if isinstance(output, list):
                # output 是列表，遍历提取文本
                for item in output:
                    item_type = getattr(item, 'type', None)
                    
                    # 处理 ResponseOutputMessage 类型 (type='message')
                    if item_type == 'message':
                        if hasattr(item, 'content') and isinstance(item.content, list):
                            # content 也是列表，查找 text 字段
                            for content_item in item.content:
                                if hasattr(content_item, 'text'):
                                    content = content_item.text
                                    break
                            if content:
                                break
                    
                    # 处理 output_text 类型
                    if item_type == 'output_text':
                        content = getattr(item, 'text', str(item))
                        break
                    elif hasattr(item, 'text'):
                        content = item.text
                        break
                    elif isinstance(item, dict):
                        if item.get('type') == 'output_text':
                            content = item.get('text', '')
                            break
                        content = item.get('text') or item.get('content')
                        if content:
                            break
            elif hasattr(output, 'content'):
                content = output.content
            elif hasattr(output, 'text'):
                content = output.text
            else:
                content = str(output)
        elif hasattr(response, 'choices') and len(response.choices) > 0:
            # OpenAI 标准格式
            content = response.choices[0].message.content
        else:
            content = str(response)
        
        # 如果 content 仍然是列表，继续提取
        if isinstance(content, list):
            for item in content:
                item_type = getattr(item, 'type', None)
                if item_type == 'output_text':
                    content = getattr(item, 'text', str(item))
                    break
                elif hasattr(item, 'text'):
                    content = item.text
                    break
        
        return str(content) if content else None
    
    def _clean_json_content(self, content: str) -> str:
        """
        清理 JSON 内容，移除 Markdown 标记
        
        Args:
            content: 原始内容
        
        Returns:
            清理后的内容
        """
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        return content.strip()

