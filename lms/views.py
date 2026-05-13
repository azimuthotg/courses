import csv
import io

from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.views.generic import ListView, DetailView, View, FormView, CreateView, UpdateView, DeleteView
from django.shortcuts import get_object_or_404, render, redirect
from django.http import Http404, HttpResponse, StreamingHttpResponse
from django.urls import reverse, reverse_lazy
from django.db.models import Avg, Q
from django.utils import timezone

from .models import Course, Lesson, Quiz, Question, Answer, UserProgress, UserQuizAttempt, Certificate
from .forms import CourseForm, LessonForm, LocalUserCreationForm, QuestionWithAnswersForm, QuizSubmitForm
from .utils import generate_certificate_pdf, link_callback, log_audit, mark_completed


VALID_QUIZ_TYPES = dict(Quiz.QUIZ_TYPE_CHOICES)
CANONICAL_QUIZ_TYPE = 'post'


def get_shared_course_quiz(course, create=False):
    """Return the single question set used by both pre-test and post-test."""
    canonical = Quiz.objects.filter(course=course, quiz_type=CANONICAL_QUIZ_TYPE).first()
    if canonical and canonical.questions.exists():
        return canonical

    legacy_pre = Quiz.objects.filter(course=course, quiz_type='pre').first()
    if legacy_pre and legacy_pre.questions.exists():
        return legacy_pre

    if canonical:
        return canonical
    if create:
        return Quiz.objects.create(course=course, quiz_type=CANONICAL_QUIZ_TYPE)
    return None


def quiz_type_display(quiz_type):
    return VALID_QUIZ_TYPES.get(quiz_type, 'แบบทดสอบ')


class LMSLoginView(LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        log_audit(self.request.user, 'login', request=self.request)
        return response


class LMSLogoutView(LogoutView):
    next_page = '/login/'

    def post(self, request, *args, **kwargs):
        log_audit(request.user, 'logout', request=request)
        return super().post(request, *args, **kwargs)


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff


class LocalUserCreateView(LoginRequiredMixin, StaffRequiredMixin, FormView):
    template_name = 'lms/local_user_form.html'
    form_class = LocalUserCreationForm
    success_url = reverse_lazy('local-user-create')

    def form_valid(self, form):
        user = form.save()
        log_audit(self.request.user, 'staff_user_create', user.username, self.request)
        messages.success(self.request, f'สร้างผู้ใช้ {user.username} สำเร็จ')
        return super().form_valid(form)


class StaffDashboardView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    model = Course
    template_name = 'lms/staff/dashboard.html'
    context_object_name = 'courses'
    queryset = Course.objects.all()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        course_stats = {}
        for course in ctx['courses']:
            course_stats[course.pk] = {
                'enrollment': UserProgress.objects.filter(course=course).count(),
                'completed': UserProgress.objects.filter(course=course, status='completed').count(),
                'certificates': Certificate.objects.filter(course=course).count(),
            }
        ctx['course_stats'] = course_stats
        return ctx


class StaffCourseListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    model = Course
    template_name = 'lms/staff/course_list.html'
    context_object_name = 'courses'
    queryset = Course.objects.all().prefetch_related('lessons', 'quizzes')


class StaffCourseCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    model = Course
    form_class = CourseForm
    template_name = 'lms/staff/course_form.html'
    success_url = reverse_lazy('staff-course-list')

    def form_valid(self, form):
        response = super().form_valid(form)
        log_audit(self.request.user, 'staff_course_create', self.object.title, self.request)
        messages.success(self.request, 'สร้างหลักสูตรสำเร็จ')
        return response


class StaffCourseEditView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    model = Course
    form_class = CourseForm
    template_name = 'lms/staff/course_form.html'

    def get_success_url(self):
        return reverse('staff-course-edit', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        course = self.object
        ctx['lessons'] = course.lessons.all()
        ctx['shared_quiz'] = get_shared_course_quiz(course)
        return ctx

    def form_valid(self, form):
        response = super().form_valid(form)
        log_audit(self.request.user, 'staff_course_edit', self.object.title, self.request)
        messages.success(self.request, 'บันทึกหลักสูตรสำเร็จ')
        return response


class StaffCourseDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    model = Course
    template_name = 'lms/staff/course_confirm_delete.html'
    success_url = reverse_lazy('staff-course-list')

    def form_valid(self, form):
        course_title = self.object.title
        log_audit(self.request.user, 'staff_course_delete', course_title, self.request)
        messages.success(self.request, f'ลบหลักสูตร {self.object.title} สำเร็จ')
        return super().form_valid(form)


class StaffLessonCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    model = Lesson
    form_class = LessonForm
    template_name = 'lms/staff/lesson_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.course = get_object_or_404(Course, pk=kwargs['course_pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['course'] = self.course
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['course'] = self.course
        return ctx

    def form_valid(self, form):
        form.instance.course = self.course
        messages.success(self.request, 'เพิ่มบทเรียนสำเร็จ')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('staff-course-edit', kwargs={'pk': self.course.pk})


class StaffLessonEditView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    model = Lesson
    form_class = LessonForm
    template_name = 'lms/staff/lesson_form.html'

    def get_queryset(self):
        return Lesson.objects.filter(course__pk=self.kwargs['course_pk'])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['course'] = self.object.course
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['course'] = self.object.course
        return ctx

    def form_valid(self, form):
        messages.success(self.request, 'บันทึกบทเรียนสำเร็จ')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('staff-course-edit', kwargs={'pk': self.object.course.pk})


class StaffLessonDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    model = Lesson
    template_name = 'lms/staff/lesson_confirm_delete.html'

    def get_queryset(self):
        return Lesson.objects.filter(course__pk=self.kwargs['course_pk'])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['course'] = self.object.course
        return ctx

    def form_valid(self, form):
        self.course_pk = self.object.course.pk
        messages.success(self.request, 'ลบบทเรียนสำเร็จ')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('staff-course-edit', kwargs={'pk': getattr(self, 'course_pk', self.kwargs['course_pk'])})


class StaffQuizEditView(LoginRequiredMixin, StaffRequiredMixin, View):
    template_name = 'lms/staff/quiz_edit.html'

    def get(self, request, course_pk, quiz_type):
        course = get_object_or_404(Course, pk=course_pk)
        quiz = self._get_or_create_quiz(course, quiz_type)
        return render(request, self.template_name, {
            'course': course,
            'quiz': quiz,
            'quiz_type': quiz_type,
            'questions': quiz.questions.prefetch_related('answers').all(),
        })

    def _get_or_create_quiz(self, course, quiz_type):
        if quiz_type not in VALID_QUIZ_TYPES:
            raise Http404('ไม่พบประเภทแบบทดสอบ')
        return get_shared_course_quiz(course, create=True)


class StaffQuestionCreateView(LoginRequiredMixin, StaffRequiredMixin, FormView):
    form_class = QuestionWithAnswersForm
    template_name = 'lms/staff/question_form.html'

    def dispatch(self, request, *args, **kwargs):
        if kwargs['quiz_type'] not in VALID_QUIZ_TYPES:
            raise Http404('ไม่พบประเภทแบบทดสอบ')
        self.course = get_object_or_404(Course, pk=kwargs['course_pk'])
        self.quiz = get_shared_course_quiz(self.course, create=True)
        self.quiz_type = kwargs['quiz_type']
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({'course': self.course, 'quiz': self.quiz, 'quiz_type': self.quiz_type})
        return ctx

    def form_valid(self, form):
        question = Question.objects.create(
            quiz=self.quiz,
            text=form.cleaned_data['question_text'],
            order=form.cleaned_data['question_order'],
        )
        Answer.objects.bulk_create([
            Answer(question=question, text=answer['text'], is_correct=answer['is_correct'])
            for answer in form.get_answer_data()
        ])
        messages.success(self.request, 'เพิ่มคำถามสำเร็จ')
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('staff-quiz-edit', kwargs={'course_pk': self.course.pk, 'quiz_type': self.quiz_type})


class StaffQuestionEditView(LoginRequiredMixin, StaffRequiredMixin, FormView):
    form_class = QuestionWithAnswersForm
    template_name = 'lms/staff/question_form.html'

    def dispatch(self, request, *args, **kwargs):
        if kwargs['quiz_type'] not in VALID_QUIZ_TYPES:
            raise Http404('ไม่พบประเภทแบบทดสอบ')
        self.course = get_object_or_404(Course, pk=kwargs['course_pk'])
        self.quiz = get_shared_course_quiz(self.course)
        if not self.quiz:
            raise Http404('ยังไม่มีชุดคำถามสำหรับหลักสูตรนี้')
        self.quiz_type = kwargs['quiz_type']
        self.question = get_object_or_404(Question, pk=kwargs['pk'], quiz=self.quiz)
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = {
            'question_text': self.question.text,
            'question_order': self.question.order,
        }
        answers = list(self.question.answers.order_by('pk'))
        for idx in range(1, 5):
            if idx <= len(answers):
                answer = answers[idx - 1]
                initial[f'answer_{idx}'] = answer.text
                if answer.is_correct:
                    initial['correct_answer'] = str(idx)
        return initial

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            'course': self.course,
            'quiz': self.quiz,
            'quiz_type': self.quiz_type,
            'question': self.question,
            'object': self.question,
        })
        return ctx

    def form_valid(self, form):
        self.question.text = form.cleaned_data['question_text']
        self.question.order = form.cleaned_data['question_order']
        self.question.save()

        answers = list(self.question.answers.order_by('pk'))
        answer_data = form.get_answer_data()
        for idx, data in enumerate(answer_data):
            if idx < len(answers):
                answer = answers[idx]
                answer.text = data['text']
                answer.is_correct = data['is_correct']
                answer.save()
            else:
                Answer.objects.create(question=self.question, **data)
        if len(answers) > 4:
            for answer in answers[4:]:
                answer.delete()
        messages.success(self.request, 'บันทึกคำถามสำเร็จ')
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('staff-quiz-edit', kwargs={'course_pk': self.course.pk, 'quiz_type': self.quiz_type})


class StaffQuestionDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    model = Question
    template_name = 'lms/staff/question_confirm_delete.html'

    def get_queryset(self):
        if self.kwargs['quiz_type'] not in VALID_QUIZ_TYPES:
            raise Http404('ไม่พบประเภทแบบทดสอบ')
        course = get_object_or_404(Course, pk=self.kwargs['course_pk'])
        quiz = get_shared_course_quiz(course)
        if not quiz:
            return Question.objects.none()
        return Question.objects.filter(quiz=quiz)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['course'] = self.object.quiz.course
        ctx['quiz'] = self.object.quiz
        ctx['quiz_type'] = self.kwargs['quiz_type']
        return ctx

    def form_valid(self, form):
        self.course_pk = self.object.quiz.course.pk
        self.quiz_type = self.kwargs['quiz_type']
        messages.success(self.request, 'ลบคำถามสำเร็จ')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('staff-quiz-edit', kwargs={
            'course_pk': getattr(self, 'course_pk', self.kwargs['course_pk']),
            'quiz_type': getattr(self, 'quiz_type', self.kwargs['quiz_type']),
        })


class StaffCourseReportView(LoginRequiredMixin, StaffRequiredMixin, DetailView):
    model = Course
    template_name = 'lms/staff/course_report.html'
    context_object_name = 'course'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        course = self.object
        ctx['enrollment_count'] = UserProgress.objects.filter(course=course).count()
        ctx['completed_count'] = UserProgress.objects.filter(course=course, status='completed').count()
        ctx['certificate_count'] = Certificate.objects.filter(course=course).count()

        post_quiz = get_shared_course_quiz(course)
        ctx['post_quiz'] = post_quiz
        ctx['pass_rate'] = 0
        ctx['avg_score'] = 0
        if post_quiz:
            attempts = UserQuizAttempt.objects.filter(quiz=post_quiz, attempt_type='post')
            total_users_attempted = attempts.values('user').distinct().count()
            users_passed = attempts.filter(is_passed=True).values('user').distinct().count()
            ctx['pass_rate'] = (users_passed / total_users_attempted * 100) if total_users_attempted else 0
            ctx['avg_score'] = attempts.aggregate(avg=Avg('score_percentage'))['avg'] or 0

        quiz_stats = []
        for quiz_type, quiz_label in Quiz.QUIZ_TYPE_CHOICES:
            if not post_quiz:
                continue
            attempts = UserQuizAttempt.objects.filter(quiz=post_quiz, attempt_type=quiz_type)
            quiz_stats.append({
                'quiz_type': quiz_type,
                'quiz_label': quiz_label,
                'total_attempts': attempts.count(),
                'passed': attempts.filter(is_passed=True).count(),
                'avg_score': attempts.aggregate(avg=Avg('score_percentage'))['avg'] or 0,
            })
        ctx['quiz_stats'] = quiz_stats
        return ctx


class StaffCourseReportExportView(LoginRequiredMixin, StaffRequiredMixin, View):
    def get(self, request, pk):
        course = get_object_or_404(Course, pk=pk)
        progress_qs = UserProgress.objects.filter(course=course).select_related('user')

        attempts = UserQuizAttempt.objects.filter(
            quiz__course=course,
            attempt_type='post',
        ).select_related('user')

        best_map = {}
        for attempt in attempts:
            uid = attempt.user_id
            if uid not in best_map or attempt.score_percentage > best_map[uid].score_percentage:
                best_map[uid] = attempt

        cert_set = set(Certificate.objects.filter(course=course).values_list('user_id', flat=True))

        rows = []
        for progress in progress_qs:
            best = best_map.get(progress.user_id)
            rows.append([
                progress.user.username,
                progress.user.get_full_name(),
                progress.user.department,
                'จบแล้ว' if progress.status == 'completed' else 'กำลังเรียน',
                progress.lessons_completed.count(),
                f'{best.score_percentage:.1f}' if best else '-',
                'ผ่าน' if best and best.is_passed else 'ไม่ผ่าน' if best else '-',
                'มี' if progress.user_id in cert_set else 'ยังไม่มี',
            ])

        def stream():
            yield '\ufeff'
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow([
                'รหัสนักศึกษา', 'ชื่อ-นามสกุล', 'สาขา/แผนก',
                'สถานะ', 'บทเรียนที่ดู', 'คะแนน Post-test', 'ผ่าน/ไม่ผ่าน', 'ใบประกาศฯ'
            ])
            yield output.getvalue()
            output.seek(0)
            output.truncate()
            for row in rows:
                writer.writerow(row)
                yield output.getvalue()
                output.seek(0)
                output.truncate()

        filename = f'report_{course.pk}_{course.title[:20]}.csv'
        response = StreamingHttpResponse(stream(), content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class BulkUserImportView(LoginRequiredMixin, StaffRequiredMixin, View):
    template_name = 'lms/staff/bulk_user_import.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        csv_file = request.FILES.get('csv_file')
        if not csv_file:
            messages.error(request, 'กรุณาเลือกไฟล์ CSV')
            return render(request, self.template_name)

        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'ไฟล์ต้องเป็น .csv เท่านั้น')
            return render(request, self.template_name)

        created = 0
        skipped = 0
        errors = []
        User = get_user_model()

        try:
            decoded = csv_file.read().decode('utf-8-sig')
            reader = csv.DictReader(io.StringIO(decoded))

            for row_number, row in enumerate(reader, start=2):
                username = row.get('username', '').strip()
                if not username:
                    errors.append(f'แถว {row_number}: ไม่มี username')
                    continue
                if User.objects.filter(username=username).exists():
                    skipped += 1
                    continue

                try:
                    user = User(
                        username=username,
                        first_name=row.get('first_name', '').strip(),
                        last_name=row.get('last_name', '').strip(),
                        email=row.get('email', '').strip(),
                        department=row.get('department', '').strip(),
                        is_staff=row.get('is_staff', 'False').strip().lower() == 'true',
                        line_user_id=row.get('line_user_id', '').strip(),
                    )
                    password = row.get('password', '').strip()
                    if password:
                        user.set_password(password)
                    else:
                        user.set_unusable_password()
                    user.full_clean()
                    user.save()
                    created += 1
                except Exception as exc:
                    errors.append(f'แถว {row_number} ({username}): {exc}')

            messages.success(
                request,
                f'สร้างสำเร็จ {created} คน | ข้ามซ้ำ {skipped} คน | ผิดพลาด {len(errors)} รายการ',
            )
            for error in errors[:10]:
                messages.warning(request, error)
            log_audit(
                request.user,
                'bulk_user_import',
                f'created={created}, skipped={skipped}, errors={len(errors)}',
                request,
            )
        except Exception as exc:
            messages.error(request, f'อ่านไฟล์ไม่ได้: {exc}')

        return render(request, self.template_name)


class CourseListView(LoginRequiredMixin, ListView):
    model = Course
    template_name = 'lms/course_list.html'
    context_object_name = 'courses'

    def get_queryset(self):
        queryset = Course.objects.filter(is_active=True)
        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(Q(title__icontains=query) | Q(description__icontains=query))
        return queryset

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user_progresses = UserProgress.objects.filter(
            user=self.request.user,
            course__in=ctx['courses']
        ).values('course_id', 'status')
        ctx['progress_map'] = {p['course_id']: p['status'] for p in user_progresses}
        ctx['search_query'] = self.request.GET.get('q', '')
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
        lessons = course.lessons.all()
        progress, _ = UserProgress.objects.get_or_create(
            user=user, course=course,
            defaults={'status': 'in_progress'}
        )
        lessons_total = lessons.count()
        lessons_done = progress.lessons_completed.count()
        progress_pct = int(lessons_done / lessons_total * 100) if lessons_total > 0 else 0
        ctx['lessons'] = lessons
        ctx['progress'] = progress
        ctx['lessons_total'] = lessons_total
        ctx['lessons_done'] = lessons_done
        ctx['progress_pct'] = progress_pct
        shared_quiz = get_shared_course_quiz(course)
        ctx['pre_quiz'] = shared_quiz
        ctx['post_quiz'] = shared_quiz
        ctx['certificate'] = Certificate.objects.filter(user=user, course=course).first()
        if shared_quiz:
            ctx['best_attempt'] = UserQuizAttempt.objects.filter(
                user=user, quiz=shared_quiz, attempt_type='post'
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
        lessons = course.lessons.all()

        if not course.require_post_test:
            all_lessons = set(lessons.values_list('pk', flat=True))
            watched = set(progress.lessons_completed.values_list('pk', flat=True))
            if all_lessons and all_lessons.issubset(watched):
                mark_completed(request.user, course, progress)

        lessons_list = list(lessons)
        current_index = next((i for i, l in enumerate(lessons_list) if l.pk == lesson.pk), 0)
        prev_lesson = lessons_list[current_index - 1] if current_index > 0 else None
        next_lesson = lessons_list[current_index + 1] if current_index < len(lessons_list) - 1 else None
        lessons_total = len(lessons_list)
        lessons_done = progress.lessons_completed.count()
        progress_pct = int(lessons_done / lessons_total * 100) if lessons_total > 0 else 0

        return render(request, 'lms/lesson.html', {
            'course': course,
            'lesson': lesson,
            'lessons': lessons,
            'progress': progress,
            'youtube_origin': f'{request.scheme}://{request.get_host()}',
            'prev_lesson': prev_lesson,
            'next_lesson': next_lesson,
            'lesson_number': current_index + 1,
            'lesson_total': lessons_total,
            'progress_pct': progress_pct,
            'lessons_done': lessons_done,
            'lessons_total': lessons_total,
        })


class QuizView(LoginRequiredMixin, View):
    template_name = 'lms/quiz.html'

    def _get_objects(self, course_pk, quiz_type):
        if quiz_type not in VALID_QUIZ_TYPES:
            raise Http404('ไม่พบประเภทแบบทดสอบ')
        course = get_object_or_404(Course, pk=course_pk, is_active=True)
        quiz = get_shared_course_quiz(course)
        if not quiz:
            raise Http404('ยังไม่มีชุดคำถามสำหรับหลักสูตรนี้')
        return course, quiz

    def get(self, request, course_pk, quiz_type):
        course, quiz = self._get_objects(course_pk, quiz_type)
        form = QuizSubmitForm(quiz)
        return render(request, self.template_name, {
            'form': form,
            'course': course,
            'quiz': quiz,
            'quiz_type': quiz_type,
            'quiz_title': quiz_type_display(quiz_type),
        })

    def post(self, request, course_pk, quiz_type):
        course, quiz = self._get_objects(course_pk, quiz_type)
        form = QuizSubmitForm(quiz, request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {
                'form': form,
                'course': course,
                'quiz': quiz,
                'quiz_type': quiz_type,
                'quiz_title': quiz_type_display(quiz_type),
            })

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
        is_passed = score_pct >= course.pass_threshold

        review_questions = quiz.questions.prefetch_related('answers').order_by('order')
        answer_review = []
        for question in review_questions:
            user_answer_id = request.POST.get(f'question_{question.pk}')
            correct_answer = question.answers.filter(is_correct=True).first()
            user_answer = question.answers.filter(pk=user_answer_id).first() if user_answer_id else None
            answer_review.append({
                'question': question.text,
                'user_answer': user_answer.text if user_answer else '(ไม่ได้ตอบ)',
                'correct_answer': correct_answer.text if correct_answer else '',
                'is_correct': user_answer == correct_answer if user_answer else False,
            })

        attempt = UserQuizAttempt.objects.create(
            user=request.user, quiz=quiz,
            attempt_type=quiz_type,
            score_percentage=score_pct, is_passed=is_passed
        )
        log_audit(
            request.user,
            'quiz_pass' if is_passed else 'quiz_fail',
            f'{course.title} | {quiz_type} | {score_pct:.1f}%',
            request,
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
            'quiz_type': quiz_type,
            'quiz_title': quiz_type_display(quiz_type),
            'attempt': attempt,
            'correct': correct,
            'total': total,
            'answer_review': answer_review,
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


class UserProfileView(LoginRequiredMixin, View):
    def get(self, request):
        progress_list = UserProgress.objects.filter(
            user=request.user
        ).select_related('course').order_by('-updated_at')

        attempts = UserQuizAttempt.objects.filter(
            user=request.user
        ).select_related('quiz__course').order_by('-attempted_at')

        best_attempts = {}
        for attempt in attempts:
            course_id = attempt.quiz.course_id
            if course_id not in best_attempts or attempt.score_percentage > best_attempts[course_id].score_percentage:
                best_attempts[course_id] = attempt

        certificates = Certificate.objects.filter(user=request.user).select_related('course')
        cert_map = {cert.course_id: cert for cert in certificates}

        return render(request, 'lms/profile.html', {
            'progress_list': progress_list,
            'best_attempts': best_attempts,
            'cert_map': cert_map,
        })


class LearnerTranscriptView(LoginRequiredMixin, View):
    def get(self, request):
        progress_list = UserProgress.objects.filter(
            user=request.user
        ).select_related('course').order_by('course__title')

        attempts = UserQuizAttempt.objects.filter(
            user=request.user,
            attempt_type='post',
        ).select_related('quiz__course')

        best_map = {}
        for attempt in attempts:
            course_id = attempt.quiz.course_id
            if course_id not in best_map or attempt.score_percentage > best_map[course_id].score_percentage:
                best_map[course_id] = attempt

        certs = {
            cert.course_id: cert
            for cert in Certificate.objects.filter(user=request.user).select_related('course')
        }

        from django.template.loader import render_to_string
        from xhtml2pdf import pisa

        html = render_to_string('lms/transcript_template.html', {
            'user': request.user,
            'progress_list': progress_list,
            'best_map': best_map,
            'certs': certs,
            'generated_at': timezone.now(),
        }, request=request)
        buffer = io.BytesIO()
        pisa.CreatePDF(html, dest=buffer, link_callback=link_callback)
        buffer.seek(0)

        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="transcript_{request.user.username}.pdf"'
        return response
