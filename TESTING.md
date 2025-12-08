# 测试说明

## 服务状态

✅ 服务已成功启动并运行在 `http://localhost:8000`

## 测试步骤

### 1. 访问前端页面

打开浏览器访问：`http://localhost:8000`

### 2. 开始监测

1. 点击「开始监测」按钮
2. 允许浏览器访问摄像头权限
3. 系统会立即执行一次检测，之后每 30 秒自动检测一次

### 3. 验证日志记录

每次检测完成后，检查以下内容：

#### 3.1 检查日志目录

```bash
ls -lh logs/images/    # 查看保存的截图
ls -lh logs/results/   # 查看保存的API返回结果
```

#### 3.2 查看日志文件内容

选择一个最新的 JSON 文件查看：

```bash
cat logs/results/$(ls -t logs/results/ | head -1)
```

#### 3.3 验证日志内容

日志文件应包含以下结构：

```json
{
  "timestamp": "2025-12-08T16:50:00.123456",
  "time_str": "20251208_165000_123",
  "date": "2025-12-08",
  "image_filename": "20251208_165000_123.jpg",
  "api_response": {
    "parsed_result": {
      "status": "normal",
      "score": 75,
      "is_qualified": false,
      "issues": ["背部前倾"],
      "suggestion": "宝贝，背背要挺直哦"
    },
    "full_api_response": {
      "id": "...",
      "object": "...",
      "created_at": ...,
      "model": "...",
      "output": [
        {
          "id": "...",
          "type": "reasoning",
          "summary": [
            {
              "text": "思考过程内容...",
              "type": "summary_text"
            }
          ]
        },
        {
          "id": "...",
          "type": "output_text",
          "text": "{\"status\": \"normal\", ...}",
          "annotations": null
        }
      ],
      "usage": {...},
      ...
    }
  }
}
```

### 4. 验证思考过程

在 `full_api_response.output` 中查找 `type: "reasoning"` 的项，应包含：
- `summary`: 思考过程的摘要
- 其他推理相关的字段

### 5. 检查控制台日志

服务启动后，每次检测会在控制台输出：
- 思考过程的摘要（前200字符）
- 检测完成信息
- 日志保存状态

## 预期结果

✅ **截图保存**: `logs/images/` 目录下应有 JPG 文件  
✅ **完整响应保存**: `logs/results/` 目录下应有 JSON 文件  
✅ **思考过程包含**: JSON 文件中 `full_api_response.output` 包含 `reasoning` 类型的数据  
✅ **所有字段保留**: JSON 文件包含豆包 API 返回的所有字段

## 测试 API 接口

### 查看历史记录

```bash
curl http://localhost:8000/api/records?limit=10
```

### 查看指定日期的记录

```bash
curl http://localhost:8000/api/records?date=2025-12-08&limit=10
```

## 故障排查

### 如果日志文件没有生成

1. 检查 `logs/` 目录权限
2. 查看服务日志中的错误信息
3. 确认 API 调用是否成功

### 如果思考过程为空

1. 检查 `full_api_response.output` 是否包含 `reasoning` 类型
2. 查看服务日志中的思考过程摘要
3. 确认豆包 API 是否返回了 reasoning 数据

## 注意事项

- 日志文件会持续累积，建议定期清理或归档
- 每次检测都会生成两个文件（图片 + JSON），注意磁盘空间
- JSON 文件可能较大（包含完整响应），建议定期压缩归档

