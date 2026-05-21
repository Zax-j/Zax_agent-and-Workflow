from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from pydantic import BaseModel
import asyncio
from io import BytesIO
import pandas as pd
import json
import re
from urllib.parse import quote
import logging
import time
import uuid
from typing import Optional, Dict, Any
from collections import defaultdict

# 导入你原生所有核心函数
from pages.Zax_agent import (
    zax_agent_core,
    read_pdf,
    read_word,
    build_rag,
    ocr,
    encode_image_to_base64
)

app = FastAPI(title="Zax Agent 生产级API", version="1.0")


# ===================== 【新增】结构化日志配置 =====================
# 配置日志格式（结构化：时间、请求ID、级别、接口、耗时、信息）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | request_id=%(request_id)s | path=%(path)s | method=%(method)s | cost=%(cost).2fms | msg=%(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log", encoding="utf-8")
    ]
)

logger = logging.getLogger(__name__)


# 全局中间件：自动记录所有接口请求日志
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    path = request.url.path
    method = request.method

    # 日志上下文（会被format中的%(xxx)s自动读取）
    log_extra = {
        "request_id": request_id,
        "path": path,
        "method": method,
        "cost": 0
    }

    try:
        # 记录请求开始
        logger.info("接口请求开始", extra=log_extra)

        # 处理请求
        response = await call_next(request)

        # 计算耗时
        cost_time = (time.time() - start_time) * 1000
        log_extra["cost"] = cost_time

        # 记录请求成功
        logger.info(
            f"接口请求成功 | 状态码={response.status_code}",
            extra=log_extra
        )
        return response

    except Exception as e:
        cost_time = (time.time() - start_time) * 1000
        log_extra["cost"] = cost_time
        logger.error(f"接口请求失败 | 错误={str(e)}", extra=log_extra)
        raise

# ===================== 日志配置结束 =====================

# ===================== 【新增】服务监控模块 =====================
from collections import defaultdict
import asyncio
from fastapi.responses import HTMLResponse

monitor_data: dict = defaultdict(lambda: {
    "total": 0,
    "success": 0,
    "fail": 0,
    "total_time": 0.0,
    "max_time": 0.0,
    "min_time": float('inf')
})

@app.middleware("http")
async def monitor_middleware(request: Request, call_next):
    path = request.url.path
    # 跳过监控本身和文档页面的统计
    if path in ["/monitor", "/metrics", "/docs", "/openapi.json", "/favicon.ico"]:
        return await call_next(request)

    start_time = time.time()
    monitor_data[path]["total"] += 1
    try:
        response = await call_next(request)
        if 200 <= response.status_code < 400:
            monitor_data[path]["success"] += 1
        else:
            monitor_data[path]["fail"] += 1
        return response
    except Exception:
        monitor_data[path]["fail"] += 1
        raise
    finally:
        cost = (time.time() - start_time) * 1000
        monitor_data[path]["total_time"] += cost
        if cost > monitor_data[path]["max_time"]:
            monitor_data[path]["max_time"] = cost
        if cost < monitor_data[path]["min_time"]:
            monitor_data[path]["min_time"] = cost

@app.get("/metrics")
async def get_metrics():
    result = {}
    for path, data in monitor_data.items():
        avg_time = data["total_time"] / data["total"] if data["total"] > 0 else 0
        result[path] = {
            "调用次数": data["total"],
            "成功次数": data["success"],
            "失败次数": data["fail"],
            "成功率": round(data["success"] / data["total"] * 100, 2) if data["total"] > 0 else 0,
            "平均耗时(ms)": round(avg_time, 2),
            "最大耗时(ms)": round(data["max_time"], 2),
            "最小耗时(ms)": round(data["min_time"], 2)
        }
    return result

@app.get("/monitor", response_class=HTMLResponse)
async def monitor_page():
    metrics = await get_metrics()
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Zax Agent 服务监控面板</title>
        <style>
            body {font-family: Arial; background:#1e1e2e; color:#fff; padding:20px;}
            table {width:100%; border-collapse:collapse; margin-top:20px;}
            th,td {padding:12px; text-align:left; border-bottom:1px solid #444;}
            th {background:#313244;}
            tr:hover {background:#2d2f3f;}
            h1 {color:#fff;}
        </style>
    </head>
    <body>
        <h1>📊 Zax Agent 服务监控面板</h1>
        <table>
            <tr>
                <th>接口路径</th>
                <th>调用次数</th>
                <th>成功</th>
                <th>失败</th>
                <th>成功率 %</th>
                <th>平均耗时 ms</th>
                <th>最大耗时 ms</th>
                <th>最小耗时 ms</th>
            </tr>
    """

    for path, stat in metrics.items():
        html += f"""
            <tr>
                <td>{path}</td>
                <td>{stat['调用次数']}</td>
                <td>{stat['成功次数']}</td>
                <td>{stat['失败次数']}</td>
                <td>{stat['成功率']}</td>
                <td>{stat['平均耗时(ms)']}</td>
                <td>{stat['最大耗时(ms)']}</td>
                <td>{stat['最小耗时(ms)']}</td>
            </tr>
        """

    html += """
        </table>
        <br>
        <button onclick="window.location.reload()">🔄 刷新数据</button>
    </body>
    </html>
    """
    return html
# ===================== 监控模块结束 =====================

# 全局存储
global_vector_db = None
global_ocr_raw_text = ""
global_ocr_edit_text = ""
global_vl_image_bytes = None

# ------------------- 请求体模型 -------------------
class ChatRequest(BaseModel):
    message: str
    enable_rag: bool = True
    enable_neo4j: bool = False
    enable_ocr: bool = True
    enable_web: bool = False
    enable_vl: bool = False
    model_choice: str = "DeepSeek-V4"
    timeout_seconds: int = 100

class ChatResponse(BaseModel):
    code: int
    msg: str
    data: dict

class EditOcrText(BaseModel):
    new_text: str

# ------------------- 重置接口 -------------------
@app.post("/v1/reset_all")
async def reset_all():
    global global_vector_db, global_ocr_raw_text, global_ocr_edit_text, global_vl_image_bytes
    global_vector_db = None
    global_ocr_raw_text = ""
    global_ocr_edit_text = ""
    global_vl_image_bytes = None
    # 记录日志
    logger.info("全局变量已重置", extra={"request_id": "system", "path": "/v1/reset_all", "method": "POST", "cost": 0})
    return {"code":200, "msg":"所有全局变量已重置"}

# ------------------- 1. 文档上传RAG -------------------
@app.post("/v1/upload_doc")
async def upload_document(file: UploadFile = File(...)):
    global global_vector_db
    try:
        support_suffix = (".pdf", ".docx")
        if not file.filename.endswith(support_suffix):
            raise HTTPException(status_code=400, detail="仅支持 PDF / Word 文档")

        file_content = await file.read()
        file_like = BytesIO(file_content)
        doc_text = read_pdf(file_like) if file.filename.endswith(".pdf") else read_word(file_like)
        global_vector_db = build_rag(doc_text)
        return {"code": 200, "msg": "文档上传成功，知识库已构建完成", "filename": file.filename}
    except Exception as e:
        logger.error(f"文档上传失败：{str(e)}", extra={"request_id": "system", "path": "/v1/upload_doc", "method": "POST", "cost": 0})
        raise HTTPException(status_code=500, detail=f"文档上传失败：{str(e)}")

# ------------------- 2. 核心聊天 -------------------
@app.post("/v1/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    global global_vector_db, global_vl_image_bytes
    try:
        if req.model_choice == "DeepSeek-V4":
            global_vl_image_bytes = None

        vl_image_to_pass = global_vl_image_bytes if req.enable_vl else None

        result = await asyncio.wait_for(
            asyncio.to_thread(
                zax_agent_core,
                prompt=req.message,
                enable_rag=req.enable_rag,
                enable_neo4j=req.enable_neo4j,
                enable_ocr=req.enable_ocr,
                enable_web=req.enable_web,
                enable_vl=req.enable_vl,
                vector_db=global_vector_db,
                edited_ocr_text=global_ocr_edit_text,
                vl_image=vl_image_to_pass,
                model_choice=req.model_choice
            ),
            timeout=req.timeout_seconds
        )

        if any(word in req.message for word in ["表格", "excel", "导出表格"]):
            match = re.search(r'\{.*"headers".*"rows".*\}', result, re.DOTALL)
            if not match:
                raise HTTPException(status_code=500, detail="未生成标准表格格式")

            data = json.loads(match.group())
            df = pd.DataFrame(data["rows"], columns=data["headers"])
            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, index=False)
            output.seek(0)

            filename = "OCR表格导出.xlsx"
            encoded_filename = quote(filename)
            headers = {"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
            return StreamingResponse(
                output,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers=headers
            )

        return ChatResponse(
            code=200,
            msg="请求成功",
            data={"answer": result, "use_model": req.model_choice}
        )

    except asyncio.TimeoutError:
        logger.error("请求超时", extra={"request_id": "system", "path": "/v1/chat", "method": "POST", "cost": 0})
        raise HTTPException(status_code=504, detail=f"请求超时，最大限制{req.timeout_seconds}秒")
    except Exception as e:
        logger.error(f"服务内部错误：{str(e)}", extra={"request_id": "system", "path": "/v1/chat", "method": "POST", "cost": 0})
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"服务内部错误：{str(e)}")

# ------------------- 3. 图片OCR识别 -------------------
@app.post("/v1/ocr_image")
async def ocr_image(file: UploadFile = File(...)):
    global global_ocr_raw_text, global_ocr_edit_text, global_vl_image_bytes
    try:
        global_vl_image_bytes = None
        from PIL import Image
        import numpy as np

        file_content = await file.read()
        img = Image.open(BytesIO(file_content)).convert("RGB")
        ocr_res = ocr.readtext(np.array(img), detail=0)
        raw_text = " ".join(ocr_res)
        global_ocr_raw_text = raw_text
        global_ocr_edit_text = raw_text
        return {"code": 200, "msg": "OCR识别完成", "ocr_text": raw_text}
    except Exception as e:
        logger.error(f"OCR识别失败：{str(e)}", extra={"request_id": "system", "path": "/v1/ocr_image", "method": "POST", "cost": 0})
        raise HTTPException(status_code=500, detail=f"图片识别失败：{str(e)}")

# ------------------- 4. OCR文本编辑 -------------------
@app.post("/v1/edit_ocr_text")
async def edit_ocr_text(body: EditOcrText):
    global global_ocr_edit_text
    global_ocr_edit_text = body.new_text
    return {"code":200, "msg":"OCR文本已修改，可生成表格"}

# ------------------- 5. 图像理解图片上传 -------------------
@app.post("/v1/upload_vl_image")
async def upload_vl_image(file: UploadFile = File(...)):
    global global_vl_image_bytes, global_ocr_raw_text, global_ocr_edit_text
    try:
        global_ocr_raw_text = ""
        global_ocr_edit_text = ""

        support_suffix = (".jpg", ".jpeg", ".png")
        if not file.filename.endswith(support_suffix):
            raise HTTPException(status_code=400, detail="仅支持 JPG / PNG 图片")

        file_content = await file.read()
        global_vl_image_bytes = BytesIO(file_content)
        return {"code": 200, "msg": "图片上传成功，可进行图像理解", "filename": file.filename}
    except Exception as e:
        logger.error(f"VL图片上传失败：{str(e)}", extra={"request_id": "system", "path": "/v1/upload_vl_image", "method": "POST", "cost": 0})
        raise HTTPException(status_code=500, detail=f"图片上传失败：{str(e)}")