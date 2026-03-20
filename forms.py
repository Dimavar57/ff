from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.files.images import get_image_dimensions

from .models import (
    Article, Comment, Rating, UserProfile, Technology,
    Project, Program, ProjectCategory, DevelopmentTeam,
    UserTeam, LanguageUsage, ProjectTechStack, Subscription,
    ProgrammingLanguage, TeamInvitation
)


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})


class UserLoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))


class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['title', 'excerpt', 'content', 'article_type', 'technology', 'project', 'tags', 'featured_image',
                  'status']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'excerpt': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 15}),
            'article_type': forms.Select(attrs={'class': 'form-control'}),
            'technology': forms.Select(attrs={'class': 'form-control'}),
            'project': forms.Select(attrs={'class': 'form-control'}),
            'tags': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'через запятую'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Оставьте ваш комментарий...'
            })
        }


class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['score', 'review']
        widgets = {
            'score': forms.RadioSelect(choices=[(i, f'{i}★') for i in range(1, 6)]),
            'review': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Ваш отзыв...'})
        }


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            'bio', 'avatar', 'website', 'github', 'twitter', 'linkedin', 
            'job_title', 'company', 'skills', 'programming_languages'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4,
                'placeholder': 'Расскажите о себе...'
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'form-control', 
                'accept': 'image/*'
            }),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'github': forms.URLInput(attrs={'class': 'form-control'}),
            'twitter': forms.URLInput(attrs={'class': 'form-control'}),
            'linkedin': forms.URLInput(attrs={'class': 'form-control'}),
            'job_title': forms.TextInput(attrs={'class': 'form-control'}),
            'company': forms.TextInput(attrs={'class': 'form-control'}),
            'skills': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'data-placeholder': 'Выберите навыки...'
            }),
            'programming_languages': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'data-placeholder': 'Выберите языки...'
            }),
        }

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')

        if avatar:
            try:
                # Проверяем размер файла (максимум 2MB)
                if avatar.size > 2 * 1024 * 1024:
                    raise forms.ValidationError("Размер аватарки не должен превышать 2MB")

                # Проверяем формат файла
                if not avatar.name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    raise forms.ValidationError("Поддерживаются только JPG, PNG и GIF форматы")

                # Проверяем размеры изображения
                w, h = get_image_dimensions(avatar)
                if w > 1024 or h > 1024:
                    raise forms.ValidationError("Максимальный размер изображения 1024x1024 пикселей")

            except AttributeError:
                # Если файл уже был загружен ранее
                pass

        return avatar


class TechnologyForm(forms.ModelForm):
    class Meta:
        model = Technology
        fields = ['name', 'description', 'category', 'website', 'documentation', 'github', 'release_date',
                  'current_version', 'programming_language', 'is_trending']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'category': forms.TextInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'documentation': forms.URLInput(attrs={'class': 'form-control'}),
            'github': forms.URLInput(attrs={'class': 'form-control'}),
            'release_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'current_version': forms.TextInput(attrs={'class': 'form-control'}),
            'programming_language': forms.Select(attrs={'class': 'form-control'}),
        }


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description', 'category', 'program', 'status', 'start_date', 'end_date', 'repository',
                  'website', 'documentation', 'is_open_source']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'program': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'repository': forms.URLInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'documentation': forms.URLInput(attrs={'class': 'form-control'}),
        }


class ProgramForm(forms.ModelForm):
    class Meta:
        model = Program
        fields = ['name', 'description', 'website', 'repository', 'license']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'repository': forms.URLInput(attrs={'class': 'form-control'}),
            'license': forms.TextInput(attrs={'class': 'form-control'}),
        }


class DevelopmentTeamForm(forms.ModelForm):
    class Meta:
        model = DevelopmentTeam
        fields = ['name', 'description', 'project']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'project': forms.Select(attrs={'class': 'form-control'}),
        }


class UserTeamForm(forms.ModelForm):
    class Meta:
        model = UserTeam
        fields = ['user', 'team', 'role']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-control'}),
            'team': forms.Select(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
        }


class LanguageUsageForm(forms.ModelForm):
    class Meta:
        model = LanguageUsage
        fields = ['project', 'language', 'percentage', 'is_main']
        widgets = {
            'project': forms.Select(attrs={'class': 'form-control'}),
            'language': forms.Select(attrs={'class': 'form-control'}),
            'percentage': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class ProjectTechStackForm(forms.ModelForm):
    class Meta:
        model = ProjectTechStack
        fields = ['project', 'technology', 'purpose']
        widgets = {
            'project': forms.Select(attrs={'class': 'form-control'}),
            'technology': forms.Select(attrs={'class': 'form-control'}),
            'purpose': forms.TextInput(attrs={'class': 'form-control'}),
        }


class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = ['email', 'categories', 'technologies']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'categories': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'technologies': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }


class SearchForm(forms.Form):
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Поиск статей, технологий, проектов...'
        })
    )
    category = forms.ModelChoiceField(
        required=False,
        queryset=ProjectCategory.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    technology = forms.ModelChoiceField(
        required=False,
        queryset=Technology.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    article_type = forms.ChoiceField(
        required=False,
        choices=[('', 'Все типы')] + list(Article.ARTICLE_TYPE_CHOICES),
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class TeamInvitationForm(forms.ModelForm):
    class Meta:
        model = TeamInvitation
        fields = ['invitee', 'email', 'message']

    def __init__(self, *args, **kwargs):
        self.team = kwargs.pop('team', None)
        self.inviter = kwargs.pop('inviter', None)
        super().__init__(*args, **kwargs)

        # Фильтруем пользователей, которые уже в команде
        if self.team:
            existing_members = UserTeam.objects.filter(team=self.team, is_active=True).values_list('user_id', flat=True)
            self.fields['invitee'].queryset = User.objects.exclude(id__in=existing_members).exclude(id=self.inviter.id)

    def clean(self):
        cleaned_data = super().clean()
        invitee = cleaned_data.get('invitee')
        email = cleaned_data.get('email')

        if not invitee and not email:
            raise forms.ValidationError("Укажите пользователя или email для приглашения")

        if invitee and self.team:
            # Проверяем, не приглашен ли уже пользователь
            existing_invitation = TeamInvitation.objects.filter(
                team=self.team,
                invitee=invitee,
                status='pending'
            ).exists()

            if existing_invitation:
                raise forms.ValidationError("Пользователь уже приглашен в команду")

        return cleaned_data


class InvitationResponseForm(forms.Form):
    action = forms.ChoiceField(choices=[('accept', 'Принять'), ('decline', 'Отклонить')])