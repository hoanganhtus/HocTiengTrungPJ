import os
import json
from openai import OpenAI

# 1. THIẾT LẬP API KEY
# Tú nhớ thay Key thật vào đây nhé

# Không khởi tạo client ở đây để tránh lỗi khi import module
client = None


def get_openai_client():
    """Khởi tạo OpenAI client khi cần dùng"""
    global client
    if client is None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            try:
                client = OpenAI(api_key=api_key)
            except Exception as e:
                print(f"Lỗi khởi tạo OpenAI client: {e}")
                client = None
    return client


# 2. HÀM LƯU TỪ VỰNG
def luu_tu_vung(tu_moi, pinyin, nghia):
    try:
        # Lưu vào file text (Tạm thời)
        # Lưu ý: Trong Django, đường dẫn file sẽ tính từ thư mục gốc của dự án
        dong_noi_dung = f"{tu_moi} ({pinyin}) : {nghia}\n"
        with open("tu_vung_trung_viet.txt", "a", encoding="utf-8") as f:
            f.write(dong_noi_dung)
        return f"Đã lưu: {tu_moi} ({pinyin})"
    except Exception as e:
        return f"Lỗi ghi file: {e}"


# 3. SCHEMA
tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "luu_tu_vung",
            "description": "Lưu từ vựng tiếng Trung, Pinyin và nghĩa tiếng Việt.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tu_moi": {"type": "string", "description": "Từ vựng Tiếng Trung"},
                    "pinyin": {"type": "string", "description": "Phiên âm Pinyin"},
                    "nghia": {"type": "string", "description": "Nghĩa Tiếng Việt"},
                },
                "required": ["tu_moi", "pinyin", "nghia"],
            },
        },
    }
]


# 4. HÀM CHẠY AGENT (Logic chính)
def chay_gia_su(cau_hoi):
    # Khởi tạo client nếu chưa có
    client = get_openai_client()
    if not client:
        return "Lỗi: Không thể khởi tạo OpenAI client. Vui lòng kiểm tra API key."

    prompt_hai_chieu = """
    Bạn là Gia sư song ngữ Trung - Việt.
    1. Nếu nhập Tiếng Trung: Hiện Pinyin -> Dịch Việt -> Lưu từ mới.
    2. Nếu nhập Tiếng Việt: Dịch Trung -> Hiện Pinyin -> Lưu từ Trung mới dịch được.
    Luôn ưu tiên gọi hàm 'luu_tu_vung'.
    """

    messages = [
        {"role": "system", "content": prompt_hai_chieu},
        {"role": "user", "content": cau_hoi},
    ]

    try:
        # Gọi AI lần 1
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tools_schema,
            tool_choice="auto",
        )

        message_phan_hoi = response.choices[0].message

        # Kiểm tra tool call
        if message_phan_hoi.tool_calls:
            messages.append(message_phan_hoi)

            for tool_call in message_phan_hoi.tool_calls:
                try:
                    args = json.loads(tool_call.function.arguments)

                    # Gọi hàm Python
                    ket_qua = luu_tu_vung(args["tu_moi"], args["pinyin"], args["nghia"])

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": ket_qua,
                        }
                    )
                except Exception as e:
                    print(f"Lỗi tool: {e}")

            # Gọi AI lần 2
            final_response = client.chat.completions.create(
                model="gpt-4o", messages=messages
            )
            return final_response.choices[0].message.content

        return message_phan_hoi.content

    except Exception as e:
        return f"Lỗi kết nối OpenAI: {str(e)}"
