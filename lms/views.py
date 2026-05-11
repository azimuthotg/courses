from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, View
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse

from .models import Course, Lesson, Quiz, Answer, UserProgress, UserQuizAttempt, Certificate
from .forms import QuizSubmitForm
from .utils import generate_certificate_pdf, mark_completed


class LMSLoginView(LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True


class LMSLogoutView(LogoutView):
    next_page = '/login/'


class CourseListView(LoginRequiredMixin, ListView):
    model = Course
    template_name = 'lms/course_list.html'
    context_object_name = 'courses'
    queryset = Course.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user_progresses = UserProgress.objects.filter(
            user=self.request.user,
            course__in=ctx['courses']
        ).values('course_id', 'status')
        ctx['progress_map'] = {p['course_id']: p['status'] for p in user_progresses}
        return ctx


class CourseDetailView(LoginRequiredMixin, DetailView):
    model = Course
    template_name = 'lms/course_detail.html'

    def get_queryset(self):
        return Course.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        course = self.object
        user = self.request.user
        ctx['lessons'] = course.lessons.all()
        ctx['progress'], _ = UserProgress.objects.get_or_create(
            user=user, course=course,
            defaults={'status': 'in_progress'}
        )
        ctx['pre_quiz'] = Quiz.objects.filter(course=course, quiz_type='pre').first()
        ctx['post_quiz'] = Quiz.objects.filter(course=course, quiz_type='post').first()
        ctx['certificate'] = Certificate.objects.filter(user=user, course=course).first()
        if ctx['post_quiz']:
            ctx['best_attempt'] = UserQuizAttempt.objects.filter(
                user=user, quiz=ctx['post_quiz']
            ).order_by('-score_percentage').first()
        return ctx


class LessonView(LoginRequiredMixin, View):
    def get(self, request, course_pk, lesson_pk):
        course = get_object_or_404(Course, pk=course_pk, is_active=True)
        lesson = get_object_or_404(Lesson, pk=lesson_pk, course=course)
        progress, _ = UserProgress.objects.get_or_create(
            user=request.user, course=course,
            defaults={'status': 'in_progress'}
        )
        progress.lessons_completed.add(lesson)

        if not course.require_post_test:
            all_lessons = set(course.lessons.values_list('pk', flat=True))
            watched = set(progress.lessons_completed.values_list('pk', flat=True))
            if all_lessons and all_lessons.issubset(watched):
                mark_completed(request.user, course, progress)

        return render(request, 'lms/lesson.html', {
            'course': course,
            'lesson': lesson,
            'lessons': course.lessons.all(),
            'progress': progress,
        })


class QuizView(LoginRequiredMixin, View):
    template_name = 'lms/quiz.html'

    def _get_objects(self, course_pk, quiz_type):
        course = get_object_or_404(Course, pk=course_pk, is_active=True)
        quiz = get_object_or_404(Quiz, course=course, quiz_type=quiz_type)
        return course, quiz

    def get(self, request, course_pk, quiz_type):
        course, quiz = self._get_objects(course_pk, quiz_type)
        form = QuizSubmitForm(quiz)
        return render(request, self.template_name, {'form': form, 'course': course, 'quiz': quiz})

    def post(self, request, course_pk, quiz_type):
        course, quiz = self._get_objects(course_pk, quiz_type)
        form = QuizSubmitForm(quiz, request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {'form': form, 'course': course, 'quiz': quiz})

        questions = list(quiz.questions.prefetch_related('answers'))
        total = len(questions)
        correct = 0
        for question in questions:
            chosen_pk = form.cleaned_data.get(f'question_{question.pk}')
            try:
                answer = question.answers.get(pk=chosen_pk)
                if answer.is_correct:
                    correct += 1
            except Answer.DoesNotExist:
                pass

        score_pct = (correct / total * 100) if total > 0 else 0
        is_passed = score_pct >= 70

        attempt = UserQuizAttempt.objects.create(
            user=request.user, quiz=quiz,
            score_percentage=score_pct, is_passed=is_passed
        )

        if quiz_type == 'post' and is_passed:
            progress, _ = UserProgress.objects.get_or_create(
                user=request.user, course=course,
                defaults={'status': 'in_progress'}
            )
            mark_completed(request.user, course, progress)

        return render(request, 'lms/quiz_result.html', {
            'course': course,
            'quiz': quiz,
            'attempt': attempt,
            'correct': correct,
            'total': total,
        })


class CertificateDownloadView(LoginRequiredMixin, View):
    def get(self, request, course_pk):
        course = get_object_or_404(Course, pk=course_pk)
        certificate = get_object_or_404(Certificate, user=request.user, course=course)
        pdf_buffer = generate_certificate_pdf(request.user, course, certificate)
        if not pdf_buffer:
            from django.contrib import messages
            messages.error(request, 'ไม่สามารถสร้างใบประกาศได้ กรุณาติดต่อผู้ดูแลระบบ')
            return redirect('course-detail', pk=course_pk)
        filename = f'certificate_{course_pk}_{request.user.username}.pdf'
        response = HttpResponse(pdf_buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
