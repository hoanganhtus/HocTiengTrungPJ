from django.db import models
from django.utils import timezone


class StudySession(models.Model):
    """Mô hình lưu trữ các buổi học"""

    date = models.DateField(default=timezone.now, verbose_name="Ngày học")
    duration_minutes = models.IntegerField(default=0, verbose_name="Thời lượng (phút)")
    notes = models.TextField(blank=True, null=True, verbose_name="Ghi chú")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]
        verbose_name = "Buổi học"
        verbose_name_plural = "Các buổi học"

    def __str__(self):
        return f"Buổi học ngày {self.date}"


class Vocabulary(models.Model):
    """Mô hình lưu trữ từ vựng đã học"""

    chinese = models.CharField(max_length=100, verbose_name="Tiếng Trung")
    pinyin = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Phiên âm"
    )
    vietnamese = models.CharField(max_length=200, verbose_name="Nghĩa tiếng Việt")
    example_sentence = models.TextField(blank=True, null=True, verbose_name="Câu ví dụ")
    session = models.ForeignKey(
        StudySession,
        on_delete=models.CASCADE,
        related_name="vocabularies",
        null=True,
        blank=True,
    )
    learned_date = models.DateField(default=timezone.now, verbose_name="Ngày học")
    mastery_level = models.IntegerField(default=1, verbose_name="Độ thuần thục (1-5)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]  # Sắp xếp theo thời gian tạo mới nhất
        verbose_name = "Từ vựng"
        verbose_name_plural = "Từ vựng"

    def __str__(self):
        return f"{self.chinese} - {self.vietnamese}"
