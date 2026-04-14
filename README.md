# AI Browser Agent Prototype

一个最小可运行的 AI 浏览器代理原型（FastAPI + Playwright + Chrome/Edge 扩展）。

## 功能
- 接收自然语言任务：`POST /api/tasks/run`
- 基于 LLM 的逐步规划（含安全校验 + fallback）
- Playwright 执行动作并保存截图
- 技能系统（generic_web / github / google / bilibili）
- 本地记忆（`artifacts/memory/tasks.json`）
- 调试追踪（`artifacts/logs/{task_id}.json`）
- MV3 侧边栏扩展，可采集当前标签页上下文并调用后端

## 环境要求
- Python 3.11+
- Node/Chrome/Edge（用于加载扩展）

## 快速启动
### 1) 安装依赖
```bash
pip install -r requirements.txt
playwright install chromium
```

### 2) 启动后端
```bash
./start.sh
```
或：
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3) 运行测试
```bash
pytest -q
```

## API 示例
```bash
curl -X POST http://localhost:8000/api/tasks/run \
  -H 'Content-Type: application/json' \
  -d '{
    "task": "总结当前页面并截图",
    "debug": true,
    "current_page": {
      "url": "https://example.com",
      "title": "Example Domain",
      "buttons": [],
      "links": [{"text":"More information","href":"https://www.iana.org/domains/example"}],
      "inputs": [],
      "summary": "Example Domain..."
    }
  }'
```

## 扩展加载（Chrome/Edge）
详细步骤见：`extension/README.md`
