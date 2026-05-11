from django import forms


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
