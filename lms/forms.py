from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import Course, Lesson


TEXT_INPUT_CLASS = (
    'w-full rounded-lg border border-gray-300 px-3 py-2 text-sm '
    'focus:border-teal-600 focus:outline-none focus:ring-2 focus:ring-teal-100'
)
CHECK_INPUT_CLASS = 'h-4 w-4 rounded border-gray-300 text-teal-700 focus:ring-teal-600'


def apply_tailwind_widgets(fields):
    for name, field in fields.items():
        if isinstance(field.widget, (forms.CheckboxInput, forms.RadioSelect)):
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': CHECK_INPUT_CLASS})
        elif isinstance(field.widget, forms.ClearableFileInput):
            field.widget.attrs.update({'class': 'block w-full text-sm text-gray-700'})
        else:
            field.widget.attrs.update({'class': TEXT_INPUT_CLASS})


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = [
            'title',
            'description',
            'thumbnail',
            'certificate_background',
            'require_post_test',
            'pass_threshold',
            'is_active',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }
        help_texts = {
            'certificate_background': 'อัปโหลดภาพพื้นหลังใบประกาศแนวนอน เช่น A4 landscape หรืออัตราส่วนประมาณ 1.414:1',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_tailwind_widgets(self.fields)


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title', 'youtube_video_id', 'order']
        help_texts = {
            'youtube_video_id': 'กรอกเฉพาะ Video ID เช่น dQw4w9WgXcQ',
        }

    def __init__(self, *args, **kwargs):
        self.course = kwargs.pop('course', None)
        super().__init__(*args, **kwargs)
        apply_tailwind_widgets(self.fields)

    def clean(self):
        cleaned_data = super().clean()
        course = self.course or getattr(self.instance, 'course', None)
        order = cleaned_data.get('order')
        if course and order is not None:
            exists = Lesson.objects.filter(course=course, order=order).exclude(pk=self.instance.pk).exists()
            if exists:
                self.add_error('order', 'ลำดับนี้ถูกใช้แล้วในหลักสูตรนี้')
        return cleaned_data


class QuestionWithAnswersForm(forms.Form):
    question_text = forms.CharField(label='คำถาม', widget=forms.Textarea(attrs={'rows': 4}))
    question_order = forms.IntegerField(label='ลำดับ', initial=0, min_value=0)
    answer_1 = forms.CharField(max_length=500, label='ตัวเลือก 1')
    answer_2 = forms.CharField(max_length=500, label='ตัวเลือก 2')
    answer_3 = forms.CharField(max_length=500, label='ตัวเลือก 3')
    answer_4 = forms.CharField(max_length=500, label='ตัวเลือก 4')
    correct_answer = forms.ChoiceField(
        choices=[('1', '1'), ('2', '2'), ('3', '3'), ('4', '4')],
        widget=forms.RadioSelect,
        label='คำตอบที่ถูกต้อง',
        initial='1',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_tailwind_widgets(self.fields)
        self.fields['correct_answer'].widget.attrs.update({'class': CHECK_INPUT_CLASS})

    def get_answer_data(self):
        correct_answer = int(self.cleaned_data['correct_answer'])
        return [
            {
                'text': self.cleaned_data[f'answer_{idx}'],
                'is_correct': idx == correct_answer,
            }
            for idx in range(1, 5)
        ]


class LocalUserCreationForm(UserCreationForm):
    """Create local staff/user accounts managed by admins."""

    first_name = forms.CharField(label='ชื่อ', max_length=150, required=False)
    last_name = forms.CharField(label='นามสกุล', max_length=150, required=False)
    email = forms.EmailField(label='อีเมล', required=False)
    department = forms.CharField(label='หน่วยงาน', max_length=200, required=False)
    line_user_id = forms.CharField(label='LINE User ID', max_length=50, required=False)
    is_staff = forms.BooleanField(label='ให้สิทธิ์เจ้าหน้าที่', required=False)
    is_active = forms.BooleanField(label='เปิดใช้งานบัญชี', required=False, initial=True)

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = (
            'username',
            'first_name',
            'last_name',
            'email',
            'department',
            'line_user_id',
            'is_staff',
            'is_active',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_tailwind_widgets(self.fields)


class QuizSubmitForm(forms.Form):
    """Dynamically builds one RadioSelect field per Question."""

    def __init__(self, quiz, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for question in quiz.questions.prefetch_related('answers').all():
            choices = [(a.pk, a.text) for a in question.answers.all()]
            self.fields[f'question_{question.pk}'] = forms.ChoiceField(
                label=question.text,
                choices=choices,
                widget=forms.RadioSelect,
                required=True,
            )
