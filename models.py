from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
import os
import uuid


def user_avatar_path(instance, filename):
    """Генерация пути для аватара пользователя"""
    ext = filename.split('.')[-1]
    filename = f'{instance.user.username}_{uuid.uuid4().hex[:8]}.{ext}'
    return os.path.join('avatars', filename)


class ProgrammingLanguage(models.Model):
    """Языки программирования"""
    name = models.CharField(max_length=100, verbose_name="Название")
    slug = models.SlugField(unique=True)
    description = models.TextField(verbose_name="Описание")
    release_year = models.IntegerField(verbose_name="Год создания")
    paradigm = models.CharField(max_length=100, verbose_name="Парадигма", blank=True)
    website = models.URLField(verbose_name="Сайт", blank=True)
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    popularity_index = models.IntegerField(default=0, verbose_name="Индекс популярности")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Язык программирования"
        verbose_name_plural = "Языки программирования"

    def __str__(self):
        return self.name

    # Генерация slug вынесена в сигналы


class ProjectCategory(models.Model):
    """Категории проектов"""
    name = models.CharField(max_length=100, verbose_name="Название")
    slug = models.SlugField(unique=True)
    description = models.TextField(verbose_name="Описание")
    icon = models.CharField(max_length=50, verbose_name="Иконка", blank=True)
    color = models.CharField(max_length=7, default="#007bff", verbose_name="Цвет")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Категория проекта"
        verbose_name_plural = "Категории проектов"

    def __str__(self):
        return self.name

    # Генерация slug вынесена в сигналы


class Program(models.Model):
    """Программы (по аналогии с приложениями)"""
    name = models.CharField(max_length=200, verbose_name="Название")
    slug = models.SlugField(unique=True)
    description = models.TextField(verbose_name="Описание")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор")
    website = models.URLField(verbose_name="Сайт", blank=True)
    repository = models.URLField(verbose_name="Репозиторий", blank=True)
    license = models.CharField(max_length=100, verbose_name="Лицензия", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Программа"
        verbose_name_plural = "Программы"

    def __str__(self):
        return self.name

    # Генерация slug вынесена в сигналы


class Project(models.Model):
    """Проекты"""
    STATUS_CHOICES = (
        ('planning', 'Планирование'),
        ('development', 'В разработке'),
        ('testing', 'Тестирование'),
        ('released', 'Выпущен'),
        ('archived', 'В архиве'),
    )

    name = models.CharField(max_length=200, verbose_name="Название проекта")
    slug = models.SlugField(unique=True)
    description = models.TextField(verbose_name="Описание")
    category = models.ForeignKey(ProjectCategory, on_delete=models.CASCADE, verbose_name="Категория")
    program = models.ForeignKey(Program, on_delete=models.CASCADE, verbose_name="Программа")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning', verbose_name="Статус")
    start_date = models.DateField(verbose_name="Дата начала", null=True, blank=True)
    end_date = models.DateField(verbose_name="Дата окончания", null=True, blank=True)
    repository = models.URLField(verbose_name="Репозиторий", blank=True)
    website = models.URLField(verbose_name="Сайт проекта", blank=True)
    documentation = models.URLField(verbose_name="Документация", blank=True)
    is_open_source = models.BooleanField(default=False, verbose_name="Open Source")
    stars = models.IntegerField(default=0, verbose_name="Звезды на GitHub")
    forks = models.IntegerField(default=0, verbose_name="Форки")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Проект"
        verbose_name_plural = "Проекты"
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    # Генерация slug вынесена в сигналы


class DevelopmentTeam(models.Model):
    """Команды разработчиков"""
    name = models.CharField(max_length=200, verbose_name="Название команды")
    slug = models.SlugField(unique=True)
    description = models.TextField(verbose_name="Описание команды")
    leader = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='led_development_teams',
                               verbose_name="Лидер команды")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, verbose_name="Проект")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Команда разработчиков"
        verbose_name_plural = "Команды разработчиков"

    def __str__(self):
        return self.name

    # Генерация slug вынесена в сигналы


class Technology(models.Model):
    """Технологии и фреймворки"""
    name = models.CharField(max_length=100, verbose_name="Название")
    slug = models.SlugField(unique=True)
    description = models.TextField(verbose_name="Описание")
    category = models.CharField(max_length=100, verbose_name="Категория")
    website = models.URLField(verbose_name="Сайт", blank=True)
    documentation = models.URLField(verbose_name="Документация", blank=True)
    github = models.URLField(verbose_name="GitHub", blank=True)
    release_date = models.DateField(verbose_name="Дата релиза")
    current_version = models.CharField(max_length=20, verbose_name="Текущая версия", blank=True)
    programming_language = models.ForeignKey(ProgrammingLanguage, on_delete=models.SET_NULL, null=True,
                                             verbose_name="Язык программирования")
    is_trending = models.BooleanField(default=False, verbose_name="В тренде")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Технология"
        verbose_name_plural = "Технологии"
        ordering = ['-release_date']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('technology_detail', kwargs={'slug': self.slug})

    # Генерация slug вынесена в сигналы


class UserTeam(models.Model):
    """Участие пользователей в командах (промежуточная таблица)"""
    ROLE_CHOICES = (
        ('developer', 'Разработчик'),
        ('designer', 'Дизайнер'),
        ('tester', 'Тестировщик'),
        ('manager', 'Менеджер'),
        ('contributor', 'Контрибьютор'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    team = models.ForeignKey(DevelopmentTeam, on_delete=models.CASCADE, verbose_name="Команда")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='contributor', verbose_name="Роль")
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, verbose_name="Активный участник")

    class Meta:
        verbose_name = "Участник команды"
        verbose_name_plural = "Участники команд"
        unique_together = ('user', 'team')

    def __str__(self):
        return f"{self.user.username} в {self.team.name}"


class LanguageUsage(models.Model):
    """Использование языков программирования в проектах (промежуточная таблица)"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, verbose_name="Проект")
    language = models.ForeignKey(ProgrammingLanguage, on_delete=models.CASCADE, verbose_name="Язык программирования")
    percentage = models.IntegerField(
        verbose_name="Процент использования",
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=0
    )
    is_main = models.BooleanField(default=False, verbose_name="Основной язык")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Использование языка"
        verbose_name_plural = "Использование языков"
        unique_together = ('project', 'language')

    def __str__(self):
        return f"{self.language.name} в {self.project.name}"


class ProjectTechStack(models.Model):
    """Технологический стек проекта (промежуточная таблица)"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, verbose_name="Проект")
    technology = models.ForeignKey(Technology, on_delete=models.CASCADE, verbose_name="Технология")
    purpose = models.CharField(max_length=200, verbose_name="Назначение", blank=True)

    class Meta:
        verbose_name = "Технология проекта"
        verbose_name_plural = "Технологии проектов"
        unique_together = ('project', 'technology')

    def __str__(self):
        return f"{self.technology.name} в {self.project.name}"


class Article(models.Model):
    """Статьи/обзоры"""
    STATUS_CHOICES = (
        ('draft', 'Черновик'),
        ('published', 'Опубликовано'),
        ('archived', 'В архиве'),
        ('deleted', 'Удалено'),
    )

    ARTICLE_TYPE_CHOICES = (
        ('review', 'Обзор'),
        ('tutorial', 'Туториал'),
        ('comparison', 'Сравнение'),
        ('news', 'Новость'),
        ('analysis', 'Анализ'),
    )

    title = models.CharField(max_length=200, verbose_name="Заголовок")
    slug = models.SlugField(unique=True)
    content = models.TextField(verbose_name="Содержание")
    excerpt = models.TextField(verbose_name="Краткое описание", max_length=300)
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор")
    article_type = models.CharField(max_length=20, choices=ARTICLE_TYPE_CHOICES, default='review',
                                    verbose_name="Тип статьи")
    technology = models.ForeignKey(Technology, on_delete=models.SET_NULL, null=True, blank=True,
                                   verbose_name="Технология")
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Проект")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft', verbose_name="Статус")
    views = models.PositiveIntegerField(default=0, verbose_name="Просмотры")
    featured_image = models.ImageField(upload_to='articles/', blank=True, null=True, verbose_name="Изображение")
    tags = models.CharField(max_length=200, verbose_name="Теги", blank=True, help_text="Через запятую")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_date = models.DateTimeField(default=timezone.now, verbose_name="Дата публикации")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата удаления")
    deleted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='deleted_articles', verbose_name="Удалил")

    class Meta:
        verbose_name = "Статья"
        verbose_name_plural = "Статьи"
        ordering = ['-published_date']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('article_detail', kwargs={'slug': self.slug})

    def get_tags_list(self):
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',')]
        return []

    def increment_views(self):
        self.views += 1
        self.save(update_fields=['views'])

    def soft_delete(self, user=None):
        self.status = 'deleted'
        self.deleted_at = timezone.now()
        if user:
            self.deleted_by = user
        self.save()

    def restore(self):
        self.status = 'published'
        self.deleted_at = None
        self.deleted_by = None
        self.save()

    def is_deleted(self):
        return self.status == 'deleted'


class Comment(models.Model):
    """Комментарии к статьям"""
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='comments', verbose_name="Статья")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор")
    content = models.TextField(verbose_name="Комментарий")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies',
                               verbose_name="Родительский комментарий")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_approved = models.BooleanField(default=True, verbose_name="Одобрен")

    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"
        ordering = ['-created_at']

    def __str__(self):
        return f'Комментарий от {self.author} к "{self.article.title}"'


class Rating(models.Model):
    """Рейтинги технологий и проектов"""
    TECHNOLOGY = 'technology'
    PROJECT = 'project'
    ARTICLE = 'article'

    OBJECT_TYPE_CHOICES = (
        (TECHNOLOGY, 'Технология'),
        (PROJECT, 'Проект'),
        (ARTICLE, 'Статья'),
    )

    object_type = models.CharField(max_length=20, choices=OBJECT_TYPE_CHOICES, verbose_name="Тип объекта")
    object_id = models.PositiveIntegerField(verbose_name="ID объекта")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    score = models.PositiveSmallIntegerField(
        choices=[(i, i) for i in range(1, 6)],
        verbose_name="Оценка",
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    review = models.TextField(verbose_name="Отзыв", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Рейтинг"
        verbose_name_plural = "Рейтинги"
        unique_together = ('object_type', 'object_id', 'user')

    def __str__(self):
        return f'{self.score}/5 ({self.get_object_type_display()}) от {self.user.username}'


class Subscription(models.Model):
    """Подписка на рассылку"""
    email = models.EmailField(unique=True, verbose_name="Email")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Пользователь")
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    subscribed_at = models.DateTimeField(auto_now_add=True)
    categories = models.ManyToManyField(ProjectCategory, blank=True, verbose_name="Категории для рассылки")
    technologies = models.ManyToManyField(Technology, blank=True, verbose_name="Технологии для рассылки")

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"

    def __str__(self):
        return self.email


class Tag(models.Model):
    """Теги для категоризации"""
    name = models.CharField(max_length=50, unique=True, verbose_name="Название")
    slug = models.SlugField(unique=True)
    description = models.TextField(verbose_name="Описание", blank=True)
    color = models.CharField(max_length=7, default="#6c757d", verbose_name="Цвет")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"

    def __str__(self):
        return self.name

    # Генерация slug вынесена в сигналы


class ChangeLog(models.Model):
    """История изменений"""
    ACTION_CHOICES = (
        ('create', 'Создание'),
        ('update', 'Обновление'),
        ('delete', 'Удаление'),
    )

    TABLE_CHOICES = (
        ('article', 'Статья'),
        ('technology', 'Технология'),
        ('project', 'Проект'),
        ('user', 'Пользователь'),
        ('program', 'Программа'),
        ('team', 'Команда'),
    )

    action = models.CharField(max_length=10, choices=ACTION_CHOICES, verbose_name="Действие")
    table_name = models.CharField(max_length=20, choices=TABLE_CHOICES, verbose_name="Таблица")
    record_id = models.PositiveIntegerField(verbose_name="ID записи")
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Изменено пользователем")
    changes = models.JSONField(verbose_name="Изменения", help_text="JSON с изменениями")
    ip_address = models.GenericIPAddressField(verbose_name="IP адрес", null=True, blank=True)
    user_agent = models.TextField(verbose_name="User Agent", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "История изменений"
        verbose_name_plural = "История изменений"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_action_display()} в {self.get_table_name_display()} #{self.record_id}"


class Skill(models.Model):
    """Навыки пользователей"""
    name = models.CharField('Название навыка', max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Навык"
        verbose_name_plural = "Навыки"


class UserProfile(models.Model):
    """Профиль пользователя"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(
        upload_to=user_avatar_path,
        null=True,
        blank=True,
        verbose_name='Аватар',
        default='avatars/default_avatar.png'
    )
    bio = models.TextField('О себе', blank=True, max_length=500)
    job_title = models.CharField('Должность', max_length=100, blank=True)
    company = models.CharField('Компания', max_length=100, blank=True)
    website = models.URLField('Веб-сайт', blank=True)
    github = models.URLField('GitHub', blank=True)
    twitter = models.URLField('Twitter', blank=True)
    linkedin = models.URLField('LinkedIn', blank=True)

    skills = models.ManyToManyField(Skill, blank=True, verbose_name='Навыки')
    programming_languages = models.ManyToManyField(ProgrammingLanguage, blank=True,
                                                   verbose_name='Языки программирования')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Профиль {self.user.username}'

    # Метод save удалён — используется стандартное поведение Django

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"


class TeamInvitation(models.Model):
    """Приглашения в команду"""
    STATUS_CHOICES = [
        ('pending', 'Ожидание'),
        ('accepted', 'Принято'),
        ('declined', 'Отклонено'),
        ('expired', 'Просрочено'),
    ]

    team = models.ForeignKey(DevelopmentTeam, on_delete=models.CASCADE, related_name='invitations')
    inviter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invitations')
    invitee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_invitations', null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    token = models.CharField(max_length=64, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['team', 'invitee']

    def __str__(self):
        return f"Приглашение в {self.team.name} для {self.invitee.username if self.invitee else self.email}"

    def is_expired(self):
        return self.expires_at < timezone.now()

    def can_accept(self):
        return self.status == 'pending' and not self.is_expired()

    def accept(self):
        if self.can_accept():
            UserTeam.objects.get_or_create(
                user=self.invitee,
                team=self.team,
                defaults={'role': 'contributor', 'is_active': True}
            )
            self.status = 'accepted'
            self.responded_at = timezone.now()
            self.save()
            return True
        return False

    def decline(self):
        if self.status == 'pending':
            self.status = 'declined'
            self.responded_at = timezone.now()
            self.save()
            return True
        return False