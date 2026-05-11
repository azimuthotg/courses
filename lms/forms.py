from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm


class LocalUserCreationForm(UserCreationForm):
    """Create local staff/user accounts managed by admins."""

    first_name = forms.CharField(label='ชื่อ', max_length=150, required=False)
    last_name = forms.CharField(label='นามสกุล', max_length=150, required=False)
    email = forms.EmailField(label='อีเมล', required=False)
    department = forms.CharField(label='หน่วยงาน', max_length=200, required=False)
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
            'is_staff',
            'is_active',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        text_class = (
            'w-full rounded-lg border border-gray-300 px-3 py-2 text-sm '
            'focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100'
        )
        check_class = 'h-4 w-4 rounded border-gray-300 text-blue-700 focus:ring-blue-500'
        for name, field in self.fields.items():
            if name in ('is_staff', 'is_active'):
                field.widget.attrs.update({'class': check_class})
            else:
                field.widget.attrs.update({'class': text_class})


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
