from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    department = models.CharField(max_length=200, blank=True, verbose_name='หน่วยงาน')

    class Meta:
        verbose_name = 'ผู้ใช้งาน'
        verbose_name_plural = 'ผู้ใช้งาน'

    def __str__(self):
        return self.get_full_name() or self.username


class Course(models.Model):
    title = models.CharField(max_length=300, verbose_name='ชื่อหลักสูตร')
    description = models.TextField(blank=True, verbose_name='รายละเอียด')
    thumbnail = models.ImageField(upload_to='course_thumbnails/', blank=True, null=True, verbose_name='ภาพปก')
    require_post_test = models.BooleanField(default=False, verbose_name='บังคับสอบหลังเรียน')
    is_active = models.BooleanField(default=True, verbose_name='เปิดใช้งาน')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'หลักสูตร'
        verbose_name_plural = 'หลักสูตร'

    def __str__(self):
        return self.title


class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=300, verbose_name='ชื่อบทเรียน')
    youtube_video_id = models.CharField(max_length=20, verbose_name='YouTube Video ID')
    order = models.PositiveIntegerField(default=0, verbose_name='ลำดับ')

    class Meta:
        ordering = ['order']
        unique_together = [('course', 'order')]
        verbose_name = 'บทเรียน'
        verbose_name_plural = 'บทเรียน'

    def __str__(self):
        return f'{self.course.title} — บทที่ {self.order}: {self.title}'


class Quiz(models.Model):
    QUIZ_TYPE_CHOICES = [
        ('pre', 'แบบทดสอบก่อนเรียน'),
        ('post', 'แบบทดสอบหลังเรียน'),
    ]
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='quizzes')
    quiz_type = models.CharField(max_length=4, choices=QUIZ_TYPE_CHOICES, verbose_name='ประเภท')

    class Meta:
        unique_together = [('course', 'quiz_type')]
        verbose_name = 'แบบทดสอบ'
        verbose_name_plural = 'แบบทดสอบ'

    def __str__(self):
        return f'{self.course.title} — {self.get_quiz_type_display()}'


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField(verbose_name='คำถาม')
    order = models.PositiveIntegerField(default=0, verbose_name='ลำดับ')

    class Meta:
        ordering = ['order']
        verbose_name = 'คำถาม'
        verbose_name_plural = 'คำถาม'

    def __str__(self):
        return self.text[:80]


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.CharField(max_length=500, verbose_name='คำตอบ')
    is_correct = models.BooleanField(default=False, verbose_name='คำตอบที่ถูกต้อง')

    class Meta:
        verbose_name = 'ตัวเลือก'
        verbose_name_plural = 'ตัวเลือก'

    def __str__(self):
        return self.text


class UserProgress(models.Model):
    STATUS_CHOICES = [
        ('in_progress', 'กำลังเรียน'),
        ('completed', 'เรียนจบแล้ว'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='progresses')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='progresses')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    lessons_completed = models.ManyToManyField(Lesson, blank=True, verbose_name='บทเรียนที่ดูแล้ว')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('user', 'course')]
        verbose_name = 'ความคืบหน้า'
        verbose_name_plural = 'ความคืบหน้า'

    def __str__(self):
        return f'{self.user} — {self.course} ({self.get_status_display()})'


class UserQuizAttempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quiz_attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    score_percentage = models.FloatField(verbose_name='คะแนน (%)')
    is_passed = models.BooleanField(default=False, verbose_name='ผ่าน')
    attempted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-attempted_at']
        verbose_name = 'ผลการสอบ'
        verbose_name_plural = 'ผลการสอบ'

    def __str__(self):
        return f'{self.user} — {self.quiz} — {self.score_percentage:.1f}%'


class Certificate(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='certificates')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='certificates')
    issued_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('user', 'course')]
        verbose_name = 'ใบประกาศนียบัตร'
        verbose_name_plural = 'ใบประกาศนียบัตร'

    def __str__(self):
        return f'{self.user} — {self.course}'
