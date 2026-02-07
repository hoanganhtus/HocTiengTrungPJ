from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta
from .models import StudySession, Vocabulary
from .forms import VocabularyInputForm
from .ai_helper import get_ai_vocabulary_info
import json


def home_view(request):
    # Lấy ngày hôm nay
    today = timezone.now().date()

    # Thống kê hôm nay
    today_sessions = StudySession.objects.filter(date=today)
    today_vocab_count = Vocabulary.objects.filter(learned_date=today).count()
    today_study_time = (
        today_sessions.aggregate(total=Sum("duration_minutes"))["total"] or 0
    )

    # Thống kê tuần này (7 ngày gần nhất)
    week_ago = today - timedelta(days=7)
    week_sessions = StudySession.objects.filter(date__gte=week_ago)
    week_vocab_count = Vocabulary.objects.filter(learned_date__gte=week_ago).count()
    week_study_time = (
        week_sessions.aggregate(total=Sum("duration_minutes"))["total"] or 0
    )

    # Thống kê tổng
    total_sessions = StudySession.objects.count()
    total_vocab = Vocabulary.objects.count()
    total_study_time = (
        StudySession.objects.aggregate(total=Sum("duration_minutes"))["total"] or 0
    )

    # Lấy các buổi học gần nhất (5 buổi)
    recent_sessions = StudySession.objects.all()[:5]

    # Lấy từ vựng học hôm nay
    today_vocabularies = Vocabulary.objects.filter(learned_date=today)[:10]

    context = {
        "today": {
            "vocab_count": today_vocab_count,
            "study_time": today_study_time,
            "session_count": today_sessions.count(),
        },
        "week": {
            "vocab_count": week_vocab_count,
            "study_time": week_study_time,
            "session_count": week_sessions.count(),
        },
        "total": {
            "vocab_count": total_vocab,
            "study_time": total_study_time,
            "session_count": total_sessions,
        },
        "recent_sessions": recent_sessions,
        "today_vocabularies": today_vocabularies,
    }

    return render(request, "home/home.html", context)


def add_vocabulary_view(request):
    """Trang thêm từ vựng với AI tự động điền"""
    if request.method == "POST":
        form = VocabularyInputForm(request.POST)

        if form.is_valid():
            chinese = form.cleaned_data.get("chinese")
            vietnamese = form.cleaned_data.get("vietnamese")

            # Gọi AI để lấy thông tin đầy đủ
            ai_result = get_ai_vocabulary_info(chinese=chinese, vietnamese=vietnamese)

            if ai_result["success"]:
                vocab_data = ai_result["data"]
                chinese_word = vocab_data["chinese"]

                # Kiểm tra từ vựng đã tồn tại chưa
                existing_vocab = Vocabulary.objects.filter(chinese=chinese_word).first()

                if existing_vocab:
                    # Từ đã tồn tại - hiển thị thông báo
                    messages.warning(
                        request,
                        f'⚠️ Từ "{chinese_word}" đã có trong từ điển! '
                        f"Nghĩa: {existing_vocab.vietnamese}. "
                        f'Học lần đầu: {existing_vocab.learned_date.strftime("%d/%m/%Y")}',
                    )

                    # Vẫn hiển thị kết quả AI để người dùng xem
                    context = {
                        "form": VocabularyInputForm(),
                        "ai_result": vocab_data,
                        "method": ai_result.get("method", "AI"),
                        "duplicate": True,
                        "existing_vocab": existing_vocab,
                        "recent_vocabs": Vocabulary.objects.all()[:5],
                    }
                    return render(request, "home/add_vocabulary.html", context)

                # Lưu từ mới vào database
                vocab = Vocabulary.objects.create(
                    chinese=vocab_data["chinese"],
                    pinyin=vocab_data["pinyin"],
                    vietnamese=vocab_data["vietnamese"],
                    example_sentence=vocab_data["example_sentence"],
                    learned_date=timezone.now().date(),
                    mastery_level=1,
                )

                # Hiển thị phương thức đã dùng (AI hoặc Google Translate)
                method = ai_result.get("method", "AI")
                messages.success(
                    request,
                    f"✅ Đã thêm từ vựng mới ({method}): {vocab.chinese} - {vocab.vietnamese}",
                )

                # Lưu ID từ vừa thêm vào session để highlight
                request.session["last_added_vocab_id"] = vocab.id

                # Trả về JSON nếu là AJAX request
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return render(
                        request,
                        "home/add_vocabulary.html",
                        {
                            "form": VocabularyInputForm(),
                            "ai_result": vocab_data,
                            "method": method,
                            "success": True,
                        },
                    )

                return redirect("add_vocabulary")
            else:
                messages.error(request, f'❌ Lỗi: {ai_result["error"]}')

                # Trả về lỗi nếu là AJAX
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return render(
                        request,
                        "home/add_vocabulary.html",
                        {"form": form, "error": ai_result["error"]},
                    )
        else:
            messages.error(
                request, "❌ Vui lòng nhập ít nhất tiếng Trung hoặc tiếng Việt!"
            )
    else:
        form = VocabularyInputForm()

    # Lấy 5 từ vựng gần nhất - từ mới nhất sẽ ở đầu
    recent_vocabs = Vocabulary.objects.all()[:5]

    # Lấy ID từ vừa thêm để highlight
    last_added_id = request.session.pop("last_added_vocab_id", None)

    context = {
        "form": form,
        "recent_vocabs": recent_vocabs,
        "last_added_id": last_added_id,
    }

    return render(request, "home/add_vocabulary.html", context)
