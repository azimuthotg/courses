from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import (
    AuditLog,
    Answer,
    Certificate,
    Course,
    Lesson,
    Question,
    Quiz,
    User,
    UserProgress,
    UserQuizAttempt,
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('LMS profile', {'fields': ('department', 'line_user_id')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('LMS profile', {'fields': ('department', 'line_user_id')}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'department', 'line_user_id', 'is_staff')
    list_filter = BaseUserAdmin.list_filter + ('department',)
    search_fields = BaseUserAdmin.search_fields + ('department',)


class LessonInline(admin.TabularInline):
    model = Lesson
    fields = ('order', 'title', 'youtube_video_id')
    extra = 1
    ordering = ('order',)


class QuizInline(admin.TabularInline):
    model = Quiz
    fields = ('quiz_type',)
    extra = 0
    show_change_link = True


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'require_post_test', 'pass_threshold', 'lesson_count', 'created_at')
    list_filter = ('is_active', 'require_post_test', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at',)
    inlines = (LessonInline, QuizInline)

    @admin.display(description='บทเรียน')
    def lesson_count(self, obj):
        return obj.lessons.count()


class AnswerInline(admin.TabularInline):
    model = Answer
    fields = ('text', 'is_correct')
    extra = 2


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('course', 'quiz_type', 'question_count')
    list_filter = ('quiz_type', 'course')
    search_fields = ('course__title',)

    @admin.display(description='คำถาม')
    def question_count(self, obj):
        return obj.questions.count()


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('short_text', 'course', 'quiz_type', 'order')
    list_filter = ('quiz__course', 'quiz__quiz_type')
    search_fields = ('text', 'quiz__course__title')
    ordering = ('quiz__course__title', 'quiz__quiz_type', 'order')
    inlines = (AnswerInline,)

    @admin.display(description='คำถาม', ordering='text')
    def short_text(self, obj):
        return str(obj)

    @admin.display(description='หลักสูตร', ordering='quiz__course__title')
    def course(self, obj):
        return obj.quiz.course

    @admin.display(description='ประเภท', ordering='quiz__quiz_type')
    def quiz_type(self, obj):
        return obj.quiz.get_quiz_type_display()


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('text', 'question', 'course', 'is_correct')
    list_filter = ('is_correct', 'question__quiz__course', 'question__quiz__quiz_type')
    search_fields = ('text', 'question__text', 'question__quiz__course__title')

    @admin.display(description='หลักสูตร', ordering='question__quiz__course__title')
    def course(self, obj):
        return obj.question.quiz.course


@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'status', 'completed_lesson_count', 'updated_at')
    list_filter = ('status', 'course', 'updated_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'course__title')
    filter_horizontal = ('lessons_completed',)
    readonly_fields = ('updated_at',)

    @admin.display(description='บทเรียนที่ดูแล้ว')
    def completed_lesson_count(self, obj):
        return obj.lessons_completed.count()


@admin.register(UserQuizAttempt)
class UserQuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'quiz', 'attempt_type', 'score_percentage', 'is_passed', 'attempted_at')
    list_filter = ('attempt_type', 'is_passed', 'quiz__course', 'attempted_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'quiz__course__title')
    readonly_fields = ('attempted_at',)


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'serial_number', 'issued_at')
    list_filter = ('course', 'issued_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'course__title', 'serial_number')
    readonly_fields = ('issued_at',)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'user', 'action', 'description', 'ip_address')
    list_filter = ('action', 'created_at')
    search_fields = ('user__username', 'description')
    readonly_fields = ('user', 'action', 'description', 'ip_address', 'created_at')
    ordering = ('-created_at',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
