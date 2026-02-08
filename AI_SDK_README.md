# AI SDK Documentation - Học Tiếng Trung

## 📚 Tổng quan

Dự án cung cấp 2 SDK chính để xử lý AI cho ứng dụng học tiếng Trung:

1. **ChineseAIEngine** (`translator/ai_engine.py`) - Dịch thuật và lưu từ vựng tự động
2. **VocabularyAIHelper** (`home/ai_helper.py`) - Tự động điền thông tin từ vựng

## 🚀 Cài đặt

### Yêu cầu

```bash
pip install openai deep-translator googletrans==4.0.0rc1
```

### Cấu hình API Key

Đặt OpenAI API key trong biến môi trường:

```bash
# Windows
set OPENAI_API_KEY=sk-your-api-key-here

# Linux/Mac
export OPENAI_API_KEY=sk-your-api-key-here
```

## 📖 Hướng dẫn sử dụng

### 1. ChineseAIEngine - Dịch thuật thông minh

#### Sử dụng cơ bản

```python
from translator.ai_engine import ChineseAIEngine

# Khởi tạo engine
engine = ChineseAIEngine()

# Dịch từ tiếng Trung sang tiếng Việt (tự động lưu từ vựng)
result = engine.translate("你好")
print(result)
# Output: 
# "你好" (nǐ hǎo) có nghĩa là "xin chào" trong tiếng Việt.
# ✓ Đã lưu: 你好 (nǐ hǎo)

# Dịch từ tiếng Việt sang tiếng Trung
result = engine.translate("Tôi yêu học tiếng Trung")
print(result)
```

#### Cấu hình nâng cao

```python
from translator.ai_engine import ChineseAIEngine, AIConfig, ModelType

# Tùy chỉnh cấu hình
config = AIConfig(
    api_key="sk-your-key",
    model=ModelType.GPT4O.value,
    temperature=0.5,
    max_tokens=1500,
    max_retries=3
)

engine = ChineseAIEngine(config=config)
```

#### Lưu từ vựng thủ công

```python
# Lưu từ vựng trực tiếp
result = engine.save_vocabulary(
    chinese="学习",
    pinyin="xuéxí",
    vietnamese="học tập"
)
print(result)  # ✓ Đã lưu: 学习 (xuéxí)
```

### 2. VocabularyAIHelper - Tự động điền từ vựng

#### Từ tiếng Trung → Thông tin đầy đủ

```python
from home.ai_helper import VocabularyAIHelper

# Khởi tạo helper
helper = VocabularyAIHelper()

# Lấy thông tin từ vựng từ chữ Trung
result = helper.get_vocabulary_info(chinese="学习")
print(result)

# Output:
# {
#     "success": True,
#     "method": "AI (OpenAI)",
#     "data": {
#         "chinese": "学习",
#         "pinyin": "xuéxí",
#         "vietnamese": "học tập",
#         "example_sentence": "我喜欢学习中文。(Wǒ xǐhuān xuéxí zhōngwén.) - Tôi thích học tiếng Trung."
#     }
# }
```

#### Từ tiếng Việt → Tìm chữ Trung

```python
# Tìm từ tiếng Trung từ nghĩa tiếng Việt
result = helper.get_vocabulary_info(vietnamese="bạn bè")
print(result["data"]["chinese"])   # 朋友
print(result["data"]["pinyin"])    # péngyǒu
```

#### Sử dụng model khác

```python
# Sử dụng GPT-4
helper = VocabularyAIHelper(model="gpt-4-turbo-preview")
result = helper.get_vocabulary_info(chinese="困难")
```

### 3. Google Translate Fallback

SDK tự động chuyển sang Google Translate nếu OpenAI không khả dụng:

```python
from home.ai_helper import GoogleTranslator

# Sử dụng trực tiếp Google Translate
translator = GoogleTranslator()
result = translator.translate("你好", source_lang="zh-CN", target_lang="vi")
print(result["translated"])  # xin chào
```

## 🎯 Tính năng nổi bật

### ✅ ChineseAIEngine

- ✨ **Dịch 2 chiều thông minh**: Trung → Việt và Việt → Trung
- 💾 **Auto-save**: Tự động lưu từ vựng vào file
- 🔧 **Configurable**: Tùy chỉnh model, temperature, max_tokens
- 📝 **Logging**: Ghi log chi tiết cho debug
- 🔄 **Retry logic**: Tự động retry khi gặp lỗi network
- 📚 **Function calling**: Sử dụng OpenAI function calling để lưu từ vựng

### ✅ VocabularyAIHelper

- 🎯 **Thông tin đầy đủ**: Chinese, Pinyin, Vietnamese, Example
- 🔄 **Auto fallback**: Tự động chuyển sang Google Translate khi AI lỗi
- 📦 **Dataclass structure**: Dữ liệu có cấu trúc rõ ràng
- 🛡️ **Error handling**: Xử lý lỗi toàn diện
- 📊 **JSON parsing**: Parse thông minh với markdown code blocks
- 🌐 **Multi-translator**: Hỗ trợ deep-translator và googletrans

## 🏗️ Kiến trúc

```
AI SDK Architecture
│
├── translator/ai_engine.py
│   ├── ChineseAIEngine (Main SDK)
│   ├── AIConfig (Configuration)
│   ├── VocabularyEntry (Data model)
│   └── ModelType (Enum)
│
└── home/ai_helper.py
    ├── VocabularyAIHelper (Main SDK)
    ├── GoogleTranslator (Fallback)
    ├── VocabularyData (Data model)
    ├── TranslationResult (Result model)
    └── TranslationMethod (Enum)
```

## 🔌 Tích hợp với Django Views

### Ví dụ trong views.py

```python
from django.http import JsonResponse
from translator.ai_engine import ChineseAIEngine
from home.ai_helper import VocabularyAIHelper

def translate_view(request):
    """View để dịch văn bản"""
    text = request.POST.get('text', '')
    engine = ChineseAIEngine()
    result = engine.translate(text)
    return JsonResponse({'result': result})

def auto_fill_vocabulary(request):
    """View tự động điền từ vựng"""
    chinese = request.POST.get('chinese', '')
    helper = VocabularyAIHelper()
    result = helper.get_vocabulary_info(chinese=chinese)
    return JsonResponse(result)
```

## 📊 Error Handling

SDK xử lý các lỗi phổ biến:

```python
try:
    engine = ChineseAIEngine()
    result = engine.translate("你好")
except ValueError as e:
    print(f"API key không hợp lệ: {e}")
except Exception as e:
    print(f"Lỗi không xác định: {e}")
```

## 🔍 Logging

SDK sử dụng Python logging để theo dõi:

```python
import logging

# Cấu hình logging level
logging.basicConfig(level=logging.DEBUG)

# Khi chạy sẽ thấy:
# INFO: ✓ OpenAI client initialized successfully
# INFO: → Translating: 你好
# INFO: ✓ Translation completed
# INFO: ✓ Saved vocabulary: 你好
```

## 🔧 Backward Compatibility

Code cũ vẫn hoạt động bình thường:

```python
# Code cũ (vẫn hoạt động)
from translator.ai_engine import chay_gia_su, luu_tu_vung
result = chay_gia_su("你好")

# Code mới (khuyến khích)
from translator.ai_engine import ChineseAIEngine
engine = ChineseAIEngine()
result = engine.translate("你好")
```

## 📝 Best Practices

1. **Sử dụng environment variables** cho API keys
2. **Caching results** để giảm chi phí API
3. **Error logging** để theo dõi vấn đề
4. **Rate limiting** khi gọi API nhiều lần
5. **Validate input** trước khi gọi AI

## 🐛 Troubleshooting

### Lỗi: "API key không tồn tại"

```bash
# Kiểm tra API key
echo %OPENAI_API_KEY%  # Windows
echo $OPENAI_API_KEY   # Linux/Mac
```

### Lỗi: "Google Translate failed"

```bash
# Cài lại packages
pip uninstall deep-translator googletrans
pip install deep-translator googletrans==4.0.0rc1
```

### Lỗi: "JSON parsing error"

SDK tự động fallback sang Google Translate. Kiểm tra logs để xem chi tiết.

## 📈 Performance Tips

- Sử dụng `gpt-3.5-turbo` cho tốc độ nhanh hơn
- Sử dụng `gpt-4o` cho độ chính xác cao hơn
- Giảm `max_tokens` nếu chỉ cần kết quả ngắn
- Cache kết quả để tránh gọi API lặp lại

## 📄 License

MIT License - Free to use and modify

## 👥 Contributors

- AI SDK Development Team
- Học Tiếng Trung Project

---

**Version**: 2.0.0  
**Last Updated**: February 2026  
**Status**: ✅ Production Ready
