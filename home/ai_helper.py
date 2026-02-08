"""
AI Helper SDK cho chức năng từ vựng học tiếng Trung
Cung cấp dịch thuật và tự động điền thông tin từ vựng với AI
"""

import os
import json
import logging
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
from openai import OpenAI


# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TranslationMethod(Enum):
    """Phương thức dịch"""
    OPENAI = "AI (OpenAI)"
    GOOGLE = "Google Translate"
    FALLBACK = "Google Translate (Dự phòng)"


@dataclass
class VocabularyData:
    """Dữ liệu từ vựng chuẩn"""
    chinese: str = ""
    pinyin: str = ""
    vietnamese: str = ""
    example_sentence: str = ""
    
    def to_dict(self) -> Dict[str, str]:
        return asdict(self)


@dataclass
class TranslationResult:
    """Kết quả dịch"""
    success: bool
    method: str
    data: Optional[VocabularyData] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "success": self.success,
            "method": self.method
        }
        if self.data:
            result["data"] = self.data.to_dict()
        if self.error:
            result["error"] = self.error
        return result


class GoogleTranslator:
    """Wrapper cho Google Translate với fallback strategy"""
    
    @staticmethod
    def translate(text: str, source_lang: str = "auto", target_lang: str = "vi") -> Dict[str, Any]:
        """
        Dịch văn bản sử dụng Google Translate
        
        Args:
            text: Văn bản cần dịch
            source_lang: Ngôn ngữ nguồn (mặc định: auto)
            target_lang: Ngôn ngữ đích (mặc định: vi)
            
        Returns:
            Dict chứa kết quả dịch
        """
        # Thử deep-translator trước
        try:
            from deep_translator import GoogleTranslator as DeepGoogleTranslator
            
            translator = DeepGoogleTranslator(source=source_lang, target=target_lang)
            result = translator.translate(text)
            logger.info(f"✓ Translated with deep-translator: {text[:30]}...")
            return {"success": True, "translated": result}
            
        except ImportError:
            logger.warning("deep-translator not installed, trying googletrans...")
            
        # Fallback sang googletrans
        try:
            from googletrans import Translator
            
            translator = Translator()
            result = translator.translate(text, src=source_lang, dest=target_lang)
            logger.info(f"✓ Translated with googletrans: {text[:30]}...")
            return {"success": True, "translated": result.text}
            
        except Exception as e:
            logger.error(f"✗ Translation failed: {e}")
            return {"success": False, "error": f"Lỗi dịch: {str(e)}"}


class VocabularyAIHelper:
    """
    SDK chính cho AI Helper - Tự động điền thông tin từ vựng
    
    Sử dụng:
        helper = VocabularyAIHelper()
        result = helper.get_vocabulary_info(chinese="你好")
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        """
        Khởi tạo AI Helper
        
        Args:
            api_key: OpenAI API key (optional, mặc định lấy từ env)
            model: Model AI sử dụng (mặc định: gpt-3.5-turbo)
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model
        self._client: Optional[OpenAI] = None
        self.google_translator = GoogleTranslator()
        
    @property
    def client(self) -> Optional[OpenAI]:
        """Lazy initialization của OpenAI client"""
        if self._client is None and self.api_key:
            try:
                self._client = OpenAI(api_key=self.api_key)
                logger.info("✓ OpenAI client initialized")
            except Exception as e:
                logger.error(f"✗ Failed to initialize OpenAI client: {e}")
        return self._client
    
    def get_vocabulary_info(
        self, 
        chinese: Optional[str] = None, 
        vietnamese: Optional[str] = None
    ) -> Dict[str, Any]:
    def get_vocabulary_info(
        self, 
        chinese: Optional[str] = None, 
        vietnamese: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Tự động điền thông tin từ vựng bằng AI
        
        Args:
            chinese: Từ tiếng Trung (nếu có)
            vietnamese: Nghĩa tiếng Việt (nếu có)
            
        Returns:
            Dict chứa kết quả với data từ vựng
            
        Examples:
            >>> helper = VocabularyAIHelper()
            >>> result = helper.get_vocabulary_info(chinese="你好")
            >>> print(result['data']['vietnamese'])
            'xin chào'
        """
        # Nếu không có API key hoặc client, dùng Google Translate
        if not self.client:
            logger.warning("OpenAI not available, using Google Translate")
            return self._use_google_fallback(chinese, vietnamese)
        
        try:
            # Tạo prompt dựa trên input
            prompt = self._build_prompt(chinese, vietnamese)
            
            logger.info(f"→ Getting vocabulary info for: {chinese or vietnamese}")
            
            # Gọi OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Bạn là trợ lý dạy tiếng Trung chuyên nghiệp. Luôn trả về JSON đúng format."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            # Parse kết quả
            result_text = response.choices[0].message.content.strip()
            vocab_info = self._parse_ai_response(result_text)
            
            # Xây dựng kết quả
            result = TranslationResult(
                success=True,
                method=TranslationMethod.OPENAI.value,
                data=VocabularyData(
                    chinese=vocab_info.get("chinese", chinese or ""),
                    pinyin=vocab_info.get("pinyin", ""),
                    vietnamese=vocab_info.get("vietnamese", vietnamese or ""),
                    example_sentence=vocab_info.get("example", "")
                )
            )
            
            logger.info(f"✓ AI vocabulary info retrieved successfully")
            return result.to_dict()
            
        except json.JSONDecodeError as e:
            logger.error(f"✗ AI JSON parsing error, fallback to Google: {e}")
            return self._use_google_fallback(chinese, vietnamese)
            
        except Exception as e:
            logger.error(f"✗ AI error, fallback to Google: {e}")
            return self._use_google_fallback(chinese, vietnamese)
    
    def _build_prompt(self, chinese: Optional[str], vietnamese: Optional[str]) -> str:
        """Xây dựng prompt cho AI"""
        base_format = """
Trả về JSON với format chính xác sau:
{
    "chinese": "从",
    "pinyin": "cóng",
    "vietnamese": "từ, theo",
    "example": "我从学校来。(Wǒ cóng xuéxiào lái.) - Tôi đến từ trường học."
}

Lưu ý:
- chinese: chữ Hán (giữ nguyên hoặc tìm từ phổ biến nhất)
- pinyin: phiên âm đầy đủ có dấu thanh
- vietnamese: nghĩa tiếng Việt ngắn gọn, chính xác
- example: 1 câu ví dụ tiếng Trung + pinyin + nghĩa tiếng Việt

Chỉ trả về JSON, không thêm text nào khác.
"""
        
        if chinese:
            return f"""Bạn là trợ lý dạy tiếng Trung. Hãy cung cấp thông tin về từ tiếng Trung: "{chinese}"
{base_format}"""
        else:
            return f"""Bạn là trợ lý dạy tiếng Trung. Hãy tìm từ tiếng Trung tương ứng với nghĩa tiếng Việt: "{vietnamese}"
{base_format}"""
    
    def _parse_ai_response(self, text: str) -> Dict[str, str]:
        """Parse response từ AI, xử lý markdown code blocks"""
        # Loại bỏ markdown code blocks nếu có
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()
        
        # Parse JSON
        return json.loads(text)
    
    def _use_google_fallback(
        self, 
        chinese: Optional[str], 
        vietnamese: Optional[str]
    ) -> Dict[str, Any]:
        """
        Fallback sử dụng Google Translate khi AI không hoạt động
        
        Args:
            chinese: Từ tiếng Trung
            vietnamese: Nghĩa tiếng Việt
            
        Returns:
            Dict chứa kết quả dịch từ Google
        """
        try:
            if chinese:
                # Dịch từ tiếng Trung sang tiếng Việt
                result = self.google_translator.translate(
                    chinese, source_lang="zh-CN", target_lang="vi"
                )
                
                if result["success"]:
                    return TranslationResult(
                        success=True,
                        method=TranslationMethod.FALLBACK.value,
                        data=VocabularyData(
                            chinese=chinese,
                            pinyin="",  # Google không cung cấp pinyin
                            vietnamese=result["translated"],
                            example_sentence=f'{chinese} - {result["translated"]}'
                        )
                    ).to_dict()
            
            elif vietnamese:
                # Dịch từ tiếng Việt sang tiếng Trung
                result = self.google_translator.translate(
                    vietnamese, source_lang="vi", target_lang="zh-CN"
                )
                
                if result["success"]:
                    return TranslationResult(
                        success=True,
                        method=TranslationMethod.FALLBACK.value,
                        data=VocabularyData(
                            chinese=result["translated"],
                            pinyin="",  # Google không cung cấp pinyin
                            vietnamese=vietnamese,
                            example_sentence=f'{result["translated"]} - {vietnamese}'
                        )
                    ).to_dict()
            
            # Nếu không thành công
            return TranslationResult(
                success=False,
                method=TranslationMethod.GOOGLE.value,
                error="Không thể dịch với Google Translate"
            ).to_dict()
            
        except Exception as e:
            logger.error(f"✗ Google Translate error: {e}")
            return TranslationResult(
                success=False,
                method=TranslationMethod.GOOGLE.value,
                error=f"Lỗi Google Translate: {str(e)}"
            ).to_dict()


# ============================================
# Backward compatibility với code cũ
# ============================================

def translate_with_google(text, source_lang="auto", target_lang="vi"):
    """[Deprecated] Sử dụng GoogleTranslator.translate thay thế"""
    translator = GoogleTranslator()
    return translator.translate(text, source_lang, target_lang)


def get_ai_vocabulary_info(chinese=None, vietnamese=None):
    """[Deprecated] Sử dụng VocabularyAIHelper.get_vocabulary_info thay thế"""
    helper = VocabularyAIHelper()
    return helper.get_vocabulary_info(chinese, vietnamese)


def use_google_translate_fallback(chinese=None, vietnamese=None):
    """[Deprecated] Sử dụng VocabularyAIHelper._use_google_fallback thay thế"""
    helper = VocabularyAIHelper()
    return helper._use_google_fallback(chinese, vietnamese)
