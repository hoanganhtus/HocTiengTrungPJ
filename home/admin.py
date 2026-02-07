from django.contrib import admin
from .models import StudySession, Vocabulary


@admin.register(StudySession)
class StudySessionAdmin(admin.ModelAdmin):
    list_display = ["date", "duration_minutes", "created_at"]
    list_filter = ["date"]
    search_fields = ["notes"]
    date_hierarchy = "date"
    ordering = ["-date"]


@admin.register(Vocabulary)
class VocabularyAdmin(admin.ModelAdmin):
    list_display = ["chinese", "pinyin", "vietnamese", "learned_date", "mastery_level"]
    list_filter = ["learned_date", "mastery_level"]
    search_fields = ["chinese", "vietnamese", "pinyin"]
    date_hierarchy = "learned_date"
    ordering = ["-learned_date"]
    list_editable = ["mastery_level"]
