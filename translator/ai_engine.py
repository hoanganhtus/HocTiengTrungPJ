"""
AI Engine SDK cho ứng dụng học tiếng Trung
Cung cấp các chức năng AI thông minh với OpenAI API
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
from openai import OpenAI
from openai.types.chat import ChatCompletion


# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelType(Enum):
    """Các model AI hỗ trợ"""

    GPT4O = "gpt-4o"
    GPT4_TURBO = "gpt-4-turbo-preview"
    GPT35_TURBO = "gpt-3.5-turbo"


@dataclass
class AIConfig:
    """Cấu hình cho AI Engine"""

    api_key: Optional[str] = None
    model: str = ModelType.GPT4O.value
    temperature: float = 0.3
    max_tokens: int = 1000
    timeout: int = 30
    max_retries: int = 3

    def __post_init__(self):
        if not self.api_key:
            self.api_key = os.environ.get("OPENAI_API_KEY")


@dataclass
class VocabularyEntry:
    """Dữ liệu từ vựng"""

    chinese: str
    pinyin: str
    vietnamese: str
    example: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chinese": self.chinese,
            "pinyin": self.pinyin,
            "vietnamese": self.vietnamese,
            "example": self.example,
        }


class ChineseAIEngine:
    """
    SDK chính cho AI Engine học tiếng Trung

    Sử dụng:
        engine = ChineseAIEngine()
        result = engine.translate("你好")
    """

    def __init__(self, config: Optional[AIConfig] = None):
        """
        Khởi tạo AI Engine

        Args:
            config: Cấu hình tùy chỉnh (optional)
        """
        self.config = config or AIConfig()
        self._client: Optional[OpenAI] = None
        self._vocabulary_file = "tu_vung_trung_viet.txt"

        # System prompts
        self.system_prompt = """
        Bạn là Gia sư song ngữ Trung - Việt chuyên nghiệp.
        1. Nếu nhập Tiếng Trung: Hiện Pinyin -> Dịch Việt -> Lưu từ mới.
        2. Nếu nhập Tiếng Việt: Dịch Trung -> Hiện Pinyin -> Lưu từ Trung mới dịch được.
        Luôn ưu tiên gọi hàm 'luu_tu_vung' để lưu từ vựng.
        """

        # Tools schema
        self.tools_schema = [
            {
                "type": "function",
                "function": {
                    "name": "save_vocabulary",
                    "description": "Lưu từ vựng tiếng Trung, Pinyin và nghĩa tiếng Việt.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "chinese": {
                                "type": "string",
                                "description": "Từ vựng Tiếng Trung",
                            },
                            "pinyin": {
                                "type": "string",
                                "description": "Phiên âm Pinyin",
                            },
                            "vietnamese": {
                                "type": "string",
                                "description": "Nghĩa Tiếng Việt",
                            },
                        },
                        "required": ["chinese", "pinyin", "vietnamese"],
                    },
                },
            }
        ]

    @property
    def client(self) -> OpenAI:
        """Lazy initialization của OpenAI client"""
        if self._client is None:
            if not self.config.api_key:
                raise ValueError(
                    "API key không tồn tại. Vui lòng cấu hình OPENAI_API_KEY "
                    "trong biến môi trường hoặc truyền vào config."
                )

            try:
                self._client = OpenAI(
                    api_key=self.config.api_key,
                    timeout=self.config.timeout,
                    max_retries=self.config.max_retries,
                )
                logger.info("✓ OpenAI client initialized successfully")
            except Exception as e:
                logger.error(f"✗ Failed to initialize OpenAI client: {e}")
                raise

        return self._client

    def save_vocabulary(self, chinese: str, pinyin: str, vietnamese: str) -> str:
        """
        Lưu từ vựng vào file

        Args:
            chinese: Từ tiếng Trung
            pinyin: Phiên âm Pinyin
            vietnamese: Nghĩa tiếng Việt

        Returns:
            Thông báo kết quả
        """
        try:
            entry = VocabularyEntry(chinese, pinyin, vietnamese)
            content = f"{entry.chinese} ({entry.pinyin}) : {entry.vietnamese}\n"

            with open(self._vocabulary_file, "a", encoding="utf-8") as f:
                f.write(content)

            logger.info(f"✓ Saved vocabulary: {chinese}")
            return f"✓ Đã lưu: {chinese} ({pinyin})"

        except Exception as e:
            logger.error(f"✗ Failed to save vocabulary: {e}")
            return f"✗ Lỗi ghi file: {e}"

    def translate(self, text: str) -> str:
        """
        Dịch văn bản và lưu từ vựng tự động

        Args:
            text: Văn bản cần dịch (tiếng Trung hoặc tiếng Việt)

        Returns:
            Kết quả dịch và giải thích
        """
        try:
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": text},
            ]

            logger.info(f"→ Translating: {text}")

            # Gọi AI lần 1
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                tools=self.tools_schema,
                tool_choice="auto",
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )

            message = response.choices[0].message

            # Xử lý tool calls
            if message.tool_calls:
                messages.append(message)

                for tool_call in message.tool_calls:
                    try:
                        args = json.loads(tool_call.function.arguments)

                        # Gọi function tương ứng
                        if tool_call.function.name == "save_vocabulary":
                            result = self.save_vocabulary(
                                args["chinese"], args["pinyin"], args["vietnamese"]
                            )
                        else:
                            result = f"Unknown function: {tool_call.function.name}"

                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": result,
                            }
                        )

                    except Exception as e:
                        logger.error(f"✗ Tool execution error: {e}")
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": f"Error: {str(e)}",
                            }
                        )

                # Gọi AI lần 2 để tổng hợp kết quả
                final_response = self.client.chat.completions.create(
                    model=self.config.model,
                    messages=messages,
                    temperature=self.config.temperature,
                )

                result = final_response.choices[0].message.content
                logger.info(f"✓ Translation completed")
                return result

            # Không có tool call, trả về response trực tiếp
            result = message.content or "Không có kết quả"
            logger.info(f"✓ Direct response")
            return result

        except Exception as e:
            logger.error(f"✗ Translation error: {e}")
            return f"✗ Lỗi kết nối OpenAI: {str(e)}"


# Backward compatibility với code cũ
client = None


def get_openai_client():
    """[Deprecated] Sử dụng ChineseAIEngine thay thế"""
    global client
    if client is None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            try:
                client = OpenAI(api_key=api_key)
            except Exception as e:
                logger.error(f"Lỗi khởi tạo OpenAI client: {e}")
                client = None
    return client


def luu_tu_vung(tu_moi, pinyin, nghia):
    """[Deprecated] Sử dụng ChineseAIEngine.save_vocabulary thay thế"""
    engine = ChineseAIEngine()
    return engine.save_vocabulary(tu_moi, pinyin, nghia)


def chay_gia_su(cau_hoi):
    """[Deprecated] Sử dụng ChineseAIEngine.translate thay thế"""
    engine = ChineseAIEngine()
    return engine.translate(cau_hoi)
