import os
import json
from openai import OpenAI


def translate_with_google(text, source_lang="auto", target_lang="vi"):
    """
    Dịch văn bản sử dụng deep-translator (giống Google Translate)
    """
    try:
        from deep_translator import GoogleTranslator

        translator = GoogleTranslator(source=source_lang, target=target_lang)
        result = translator.translate(text)
        return {"success": True, "translated": result}
    except ImportError:
        # Nếu chưa cài deep-translator, thử googletrans
        try:
            from googletrans import Translator

            translator = Translator()
            result = translator.translate(text, src=source_lang, dest=target_lang)
            return {"success": True, "translated": result.text}
        except Exception as e:
            return {"success": False, "error": f"Lỗi dịch: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Lỗi dịch: {str(e)}"}


def get_ai_vocabulary_info(chinese=None, vietnamese=None):
    """
    Sử dụng OpenAI để tự động điền thông tin từ vựng
    Nếu có tiếng Trung -> tìm nghĩa tiếng Việt, pinyin, ví dụ
    Nếu có tiếng Việt -> tìm chữ Hán, pinyin, ví dụ

    FALLBACK: Nếu AI không hoạt động, sử dụng Google Translate
    """
    api_key = os.environ.get("OPENAI_API_KEY")

    # Nếu không có API key, dùng Google Translate làm dự phòng
    if not api_key:
        return use_google_translate_fallback(chinese, vietnamese)

    try:
        client = OpenAI(api_key=api_key)

        # Tạo prompt dựa trên input
        if chinese:
            prompt = f"""Bạn là trợ lý dạy tiếng Trung. Hãy cung cấp thông tin về từ tiếng Trung: "{chinese}"

Trả về JSON với format chính xác sau:
{{
    "chinese": "从",
    "pinyin": "cóng",
    "vietnamese": "từ, theo",
    "example": "我从学校来。(Wǒ cóng xuéxiào lái.) - Tôi đến từ trường học."
}}

Lưu ý:
- chinese: giữ nguyên từ gốc
- pinyin: phiên âm đầy đủ có dấu thanh
- vietnamese: nghĩa tiếng Việt ngắn gọn
- example: 1 câu ví dụ tiếng Trung + pinyin + nghĩa tiếng Việt

Chỉ trả về JSON, không thêm text nào khác."""

        else:  # vietnamese
            prompt = f"""Bạn là trợ lý dạy tiếng Trung. Hãy tìm từ tiếng Trung tương ứng với nghĩa tiếng Việt: "{vietnamese}"

Trả về JSON với format chính xác sau:
{{
    "chinese": "从",
    "pinyin": "cóng",
    "vietnamese": "từ, theo",
    "example": "我从学校来。(Wǒ cóng xuéxiào lái.) - Tôi đến từ trường học."
}}

Lưu ý:
- chinese: chữ Hán tương ứng (nếu có nhiều từ, chọn từ phổ biến nhất)
- pinyin: phiên âm đầy đủ có dấu thanh
- vietnamese: nghĩa tiếng Việt chính xác
- example: 1 câu ví dụ tiếng Trung + pinyin + nghĩa tiếng Việt

Chỉ trả về JSON, không thêm text nào khác."""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "Bạn là trợ lý dạy tiếng Trung chuyên nghiệp. Luôn trả về JSON đúng format.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=500,
        )

        result_text = response.choices[0].message.content.strip()

        # Loại bỏ markdown code blocks nếu có
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]
            result_text = result_text.strip()

        # Parse JSON
        vocab_info = json.loads(result_text)

        return {
            "success": True,
            "method": "AI (OpenAI)",
            "data": {
                "chinese": vocab_info.get("chinese", chinese or ""),
                "pinyin": vocab_info.get("pinyin", ""),
                "vietnamese": vocab_info.get("vietnamese", vietnamese or ""),
                "example_sentence": vocab_info.get("example", ""),
            },
        }

    except json.JSONDecodeError as e:
        # Nếu AI lỗi, dùng Google Translate
        print(f"AI JSON error, fallback to Google Translate: {str(e)}")
        return use_google_translate_fallback(chinese, vietnamese)

    except Exception as e:
        # Nếu AI lỗi, dùng Google Translate
        print(f"AI error, fallback to Google Translate: {str(e)}")
        return use_google_translate_fallback(chinese, vietnamese)


def use_google_translate_fallback(chinese=None, vietnamese=None):
    """
    Dự phòng: Sử dụng Google Translate khi AI không hoạt động
    """
    try:
        if chinese:
            # Dịch từ tiếng Trung sang tiếng Việt
            result = translate_with_google(
                chinese, source_lang="zh-CN", target_lang="vi"
            )

            if result["success"]:
                return {
                    "success": True,
                    "method": "Google Translate (Dự phòng)",
                    "data": {
                        "chinese": chinese,
                        "pinyin": "",  # Google Translate không cung cấp pinyin
                        "vietnamese": result["translated"],
                        "example_sentence": f'{chinese} - {result["translated"]}',
                    },
                }

        elif vietnamese:
            # Dịch từ tiếng Việt sang tiếng Trung
            result = translate_with_google(
                vietnamese, source_lang="vi", target_lang="zh-CN"
            )

            if result["success"]:
                return {
                    "success": True,
                    "method": "Google Translate (Dự phòng)",
                    "data": {
                        "chinese": result["translated"],
                        "pinyin": "",  # Google Translate không cung cấp pinyin
                        "vietnamese": vietnamese,
                        "example_sentence": f'{result["translated"]} - {vietnamese}',
                    },
                }

        return {"success": False, "error": "Không thể dịch với Google Translate"}

    except Exception as e:
        return {"success": False, "error": f"Lỗi Google Translate: {str(e)}"}
