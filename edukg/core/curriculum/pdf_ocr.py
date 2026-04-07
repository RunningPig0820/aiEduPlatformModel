"""
百度 OCR 服务

使用百度 OCR API 识别 PDF 文件中的文字
注意: 百度 OCR 是收费服务，按次计费
"""
import base64
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF
import httpx

from .config import settings


@dataclass
class OCRResult:
    """OCR 识别结果"""
    pdf_path: str
    total_pages: int
    pages: list[dict]
    processed_at: str


class BaiduOCRService:
    """
    百度 OCR 服务

    使用百度 OCR API 进行文字识别
    注意: 这是收费服务，按次计费

    文档: https://cloud.baidu.com/doc/OCR/s/1k3h7y3db
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
    ):
        """
        初始化百度 OCR 服务

        Args:
            api_key: 百度 OCR API Key，默认从环境变量读取
            secret_key: 百度 OCR Secret Key，默认从环境变量读取
        """
        self.api_key = api_key or settings.BAIDU_OCR_API_KEY
        self.secret_key = secret_key or settings.BAIDU_OCR_SECRET_KEY

        # 检查是否为空或仅空白字符
        if not self.api_key or not self.api_key.strip():
            raise ValueError(
                "百度 OCR API Key 未配置，请设置 BAIDU_OCR_API_KEY 环境变量"
            )
        if not self.secret_key or not self.secret_key.strip():
            raise ValueError(
                "百度 OCR Secret Key 未配置，请设置 BAIDU_OCR_SECRET_KEY 环境变量"
            )

        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0

    def _get_access_token(self) -> str:
        """
        获取百度 API Access Token

        Token 有效期 30 天，这里缓存起来
        """
        # 如果 token 还有 1 小时以上有效期，直接返回
        if self._access_token and time.time() < self._token_expires_at - 3600:
            return self._access_token

        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.secret_key,
        }

        response = httpx.post(url, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()
        self._access_token = data["access_token"]
        # Token 有效期（秒）
        expires_in = data.get("expires_in", 2592000)  # 默认 30 天
        self._token_expires_at = time.time() + expires_in

        return self._access_token

    def _ocr_image(self, image_path: str, retry: int = 3) -> str:
        """
        调用百度 OCR API 识别单张图片

        Args:
            image_path: 图片路径
            retry: 重试次数

        Returns:
            识别出的文字
        """
        url = "https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic"

        # 读取图片并转为 base64
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()

        params = {
            "image": image_data,
            "language_type": "CHN_ENG",  # 中英文混合
            "detect_direction": "true",   # 检测文字方向
            "detect_language": "true",    # 检测语言
        }

        for attempt in range(retry):
            try:
                access_token = self._get_access_token()
                response = httpx.post(
                    url,
                    params={"access_token": access_token},
                    data=params,
                    timeout=60,
                )
                response.raise_for_status()

                result = response.json()

                # 检查错误
                if "error_code" in result:
                    error_code = result["error_code"]
                    error_msg = result.get("error_msg", "Unknown error")

                    # QPS 限制错误，等待后重试
                    if error_code == 18:
                        wait_time = 2 ** attempt
                        print(f"QPS 限制，等待 {wait_time} 秒后重试...")
                        time.sleep(wait_time)
                        continue

                    raise OCRAPIError(f"OCR API 错误: {error_code} - {error_msg}")

                # 提取文字
                words_result = result.get("words_result", [])
                text = "\n".join([item["words"] for item in words_result])
                return text

            except httpx.HTTPError as e:
                if attempt < retry - 1:
                    wait_time = 2 ** attempt
                    print(f"HTTP 错误: {e}，等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    raise OCRAPIError(f"OCR API 调用失败: {e}")

        raise OCRAPIError("OCR API 调用失败: 超过最大重试次数")

    def extract_text(
        self,
        pdf_path: str,
        start_page: Optional[int] = None,
        end_page: Optional[int] = None,
        dpi: int = 200,
        verbose: bool = True,
    ) -> OCRResult:
        """
        从 PDF 文件提取文字

        Args:
            pdf_path: PDF 文件路径
            start_page: 起始页码（从 1 开始）
            end_page: 结束页码
            dpi: 图片分辨率，越高越清晰但处理越慢
            verbose: 是否显示进度

        Returns:
            OCRResult: OCR 识别结果
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF 文件不存在: {pdf_path}")

        if verbose:
            print(f"正在处理 PDF: {pdf_path.name}")

        # 使用 PyMuPDF 打开 PDF
        doc = fitz.open(str(pdf_path))
        total_pages = len(doc)

        # 确定页码范围
        start = max(0, (start_page or 1) - 1)  # PyMuPDF 从 0 开始，用户从 1 开始
        end = min(end_page or total_pages, total_pages)

        if verbose:
            print(f"PDF 共 {total_pages} 页，处理第 {start+1}-{end} 页")

        # OCR 识别每一页
        pages = []
        processed_count = 0
        pages_to_process = end - start

        for page_num in range(start, end):
            processed_count += 1
            if verbose:
                progress = processed_count / pages_to_process * 100
                print(f"正在识别第 {page_num + 1}/{total_pages} 页 ({progress:.1f}%)...")

            # 获取页面
            page = doc[page_num]

            # 将页面渲染为图片
            mat = fitz.Matrix(dpi / 72, dpi / 72)  # 缩放矩阵
            pix = page.get_pixmap(matrix=mat)

            # 转换为 PNG 字节
            img_bytes = pix.tobytes("png")

            # 保存临时图片
            temp_image_path = f"/tmp/pdf_page_{page_num + 1}.png"
            with open(temp_image_path, "wb") as f:
                f.write(img_bytes)

            # OCR 识别
            text = self._ocr_image(temp_image_path)

            pages.append({
                "page_num": page_num + 1,
                "text": text,
            })

            # 删除临时图片
            Path(temp_image_path).unlink(missing_ok=True)

            # QPS 限制：每秒最多 2 次请求
            time.sleep(0.5)

        doc.close()

        result = OCRResult(
            pdf_path=str(pdf_path),
            total_pages=pages_to_process,
            pages=pages,
            processed_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )

        if verbose:
            print(f"OCR 识别完成，共处理 {pages_to_process} 页")

        return result

    def save_ocr_result(self, result: OCRResult, output_path: str) -> None:
        """
        保存 OCR 结果到 JSON 文件

        Args:
            result: OCR 识别结果
            output_path: 输出文件路径
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "pdf_path": result.pdf_path,
            "total_pages": result.total_pages,
            "processed_at": result.processed_at,
            "pages": result.pages,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"OCR 结果已保存到: {output_path}")


class OCRAPIError(Exception):
    """OCR API 错误"""
    pass


# 命令行入口
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="PDF OCR 识别")
    parser.add_argument("--pdf-path", required=True, help="PDF 文件路径")
    parser.add_argument("--output", default="ocr_result.json", help="输出文件路径")
    parser.add_argument("--start-page", type=int, help="起始页码")
    parser.add_argument("--end-page", type=int, help="结束页码")
    parser.add_argument("--debug", action="store_true", help="调试模式")

    args = parser.parse_args()

    service = BaiduOCRService()
    result = service.extract_text(
        pdf_path=args.pdf_path,
        start_page=args.start_page,
        end_page=args.end_page,
        verbose=True,
    )
    service.save_ocr_result(result, args.output)