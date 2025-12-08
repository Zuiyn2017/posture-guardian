"""
智能坐姿守护助手 (Posture Guardian)
主入口文件 - FastAPI 应用
"""
import logging
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from config import ARK_API_KEY, ARK_MODEL_NAME, TTS_API_KEY, TTS_SPEAKER
from services.vision_service import VisionService
from services.tts_service import TTSService
from services.logger_service import LoggerService

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI(
    title="Posture Guardian",
    description="智能坐姿守护助手 API",
    version="1.0.0"
)

# 确保 static 目录存在
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# 初始化服务
vision_service = VisionService()
tts_service = TTSService()
logger_service = LoggerService()


# ================= 路由 =================

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """返回前端页面"""
    index_path = static_dir / "index.html"
    if index_path.exists():
        return HTMLResponse(content=index_path.read_text(encoding="utf-8"))
    else:
        return HTMLResponse(content="<h1>请创建 static/index.html 文件</h1>", status_code=404)


@app.post("/check")
async def check_posture(request: Request):
    """
    检测坐姿
    
    请求体:
        {
            "image": "data:image/jpeg;base64,..."
        }
    
    响应:
        {
            "status": "normal",
            "score": 75,
            "is_qualified": false,
            "issues": ["背部前倾", "眼睛离书本太近"],
            "suggestion": "...",
            "audio": "base64音频数据..."
        }
    """
    try:
        data = await request.json()
    except Exception as e:
        logger.error(f"请求体解析失败: {e}")
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)
    
    image_data = data.get("image")
    
    if not image_data:
        return JSONResponse({"error": "No image provided"}, status_code=400)

    # 移除 base64 头部 (data:image/jpeg;base64,...)
    if "," in image_data:
        image_base64 = image_data.split(",")[1]
    else:
        image_base64 = image_data

    # 记录时间戳
    timestamp = datetime.now()

    # 调用视觉模型分析（返回解析结果和完整响应）
    parsed_result, full_response = vision_service.analyze_posture(image_base64)
    
    if not parsed_result:
        return JSONResponse({
            "error": "AI Analysis failed",
            "score": 0,
            "is_qualified": False,
            "issues": ["分析服务暂时不可用"],
            "audio": None
        }, status_code=500)

    # 保存检测记录（截图和完整的API返回结果，包括思考过程）
    # 构建完整的记录，包含解析结果和完整响应
    complete_response = {
        "parsed_result": parsed_result,  # 解析后的结果
        "full_api_response": full_response  # 完整的API响应，包括思考过程等所有字段
    }
    
    save_result = logger_service.save_detection_record(
        image_base64=image_base64,
        api_response=complete_response,
        timestamp=timestamp
    )
    
    if save_result.get("success"):
        logger.info(f"检测记录已保存: {save_result.get('timestamp')}")
    else:
        logger.warning(f"检测记录保存失败: {save_result.get('error')}")

    # 构建响应数据
    response_data = {
        "status": parsed_result.get("status", "normal"),
        "score": parsed_result.get("score", 0),
        "is_qualified": parsed_result.get("is_qualified", False),
        "issues": parsed_result.get("issues", []),
        "suggestion": parsed_result.get("suggestion", ""),
        "audio": None,
        "raw_result": parsed_result  # 包含完整的原始结果供前端显示
    }

    # 如果不合格且状态为 normal，调用 TTS 生成语音
    status = response_data["status"]
    suggestion = response_data["suggestion"]
    if status == "normal" and not response_data["is_qualified"] and suggestion:
        audio_base64 = tts_service.synthesize(suggestion)
        response_data["audio"] = audio_base64

    logger.info(f"检测完成: status={status}, 得分={response_data['score']}, 合格={response_data['is_qualified']}")
    
    # 在日志中输出完整响应的关键信息（思考过程）
    if full_response and isinstance(full_response, dict):
        if "output" in full_response:
            output = full_response["output"]
            if isinstance(output, list):
                for item in output:
                    if isinstance(item, dict) and item.get("type") == "reasoning":
                        reasoning_summary = item.get("summary", [])
                        if reasoning_summary:
                            logger.info(f"思考过程: {reasoning_summary[0].get('text', '')[:200]}...")
    
    return JSONResponse(response_data)


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "ok", "service": "Posture Guardian"}


@app.get("/api/records")
async def get_records(date: str = None, limit: int = 100):
    """
    获取检测记录列表
    
    Args:
        date: 日期字符串 (YYYY-MM-DD)，可选
        limit: 返回记录数量限制，默认100
    """
    records = logger_service.get_detection_records(date=date, limit=limit)
    return JSONResponse({
        "count": len(records),
        "records": records
    })


if __name__ == "__main__":
    import uvicorn
    
    # 检查配置
    if not ARK_API_KEY:
        logger.warning("⚠️  ARK_API_KEY 未配置，视觉分析功能将不可用")
    else:
        logger.info(f"✅ 视觉模型已配置: {ARK_MODEL_NAME}")
    
    if not TTS_API_KEY:
        logger.warning("⚠️  TTS_API_KEY 未配置，语音合成功能将不可用")
    else:
        logger.info(f"✅ 语音模型已配置: {TTS_SPEAKER}")
    
    logger.info("🚀 启动 Posture Guardian 服务...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
