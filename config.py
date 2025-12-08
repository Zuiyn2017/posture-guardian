"""
配置文件 - 管理所有配置项
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ================= Doubao Vision 配置 =================
ARK_API_KEY = os.getenv("ARK_API_KEY", "")
ARK_MODEL_NAME = os.getenv("ARK_MODEL_NAME", "doubao-seed-1-6-vision-250815")
ARK_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"

# ================= 火山 TTS 配置 =================
TTS_API_KEY = os.getenv("TTS_API_KEY", "")
TTS_API_URL = "https://openspeech.bytedance.com/api/v3/tts/unidirectional"
TTS_RESOURCE_ID = "volc.service_type.10029"
TTS_SPEAKER = os.getenv("TTS_SPEAKER", "zh_male_beijingxiaoye_emo_v2_mars_bigtts")

# ================= 日志配置 =================
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")

# ================= 坐姿分析 Prompt =================
POSTURE_SYSTEM_PROMPT = """你是一位专业的儿童人体工程学专家。请分析上传图片中孩子的写字坐姿。

评分标准 (满分100分)：
1. 背部是否挺直 (不驼背) - 占 30 分
2. 眼睛离桌面/书本距离是否足够 (约一尺/33cm) - 占 25 分
3. 胸口离桌沿是否有一定距离 (约一拳) - 占 25 分
4. 头是否摆正 (不歪头) - 占 20 分

特殊情况处理：
- 如果图片中没有人，返回 status 为 "no_person"
- 如果人物明显不在写字状态（如离开座位、站立），返回 status 为 "not_writing"

请严格按照以下 JSON 格式返回结果，不要包含任何 Markdown 标记或额外文字：
{
    "status": "normal" | "no_person" | "not_writing",
    "score": 0-100 的整数,
    "is_qualified": true 或 false (score >= 80 为 true),
    "issues": ["问题1", "问题2"],
    "suggestion": "给孩子的温柔语音提醒，30字以内，语气像温柔的大姐姐，以鼓励为主。如果合格则为空字符串"
}"""

