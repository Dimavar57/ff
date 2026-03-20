# reviews/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.db.models import Count, Avg
from django.contrib import messages
from .models import (
    ProgrammingLanguage, Technology, ProjectCategory, Program,
    Project, DevelopmentTeam, UserTeam, LanguageUsage,
    ProjectTechStack, Article, Comment, Rating, Subscription,
    Tag, ChangeLog, UserProfile
)


admin.site.site_header = 'TechReview - Администрирование'
admin.site.site_title = 'TechReview Admin'
admin.site.index_title = 'Панель управления'


class UserProfileInline(admin.StackedInline):
    model = UserProfile  # ИСПРАВЛЕНО: было Profile, стало UserProfile
    can_delete = False
    verbose_name_plural = 'Профиль'
    fields = ('bio', 'avatar', 'website', 'github', 'twitter', 'linkedin', 'job_title', 'company', 'skills',
              'programming_languages')




class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined', 'article_count',
                    'comment_count')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups', 'date_joined')

    def article_count(self, obj):
        return obj.article_set.count()

    article_count.short_description = 'Статей'

    def comment_count(self, obj):
        return obj.comment_set.count()

    comment_count.short_description = 'Комментариев'


class ProgrammingLanguageAdmin(admin.ModelAdmin):
    list_display = ('name', 'release_year', 'paradigm', 'is_active', 'popularity_index', 'project_count', 'created_at')
    list_filter = ('is_active', 'release_year')
    search_fields = ('name', 'description', 'paradigm')
    readonly_fields = ('created_at',)

    def project_count(self, obj):
        return LanguageUsage.objects.filter(language=obj).count()

    project_count.short_description = 'Проектов'


class TechnologyAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'programming_language', 'release_date', 'is_trending', 'article_count',
                    'project_count', 'avg_rating')
    list_filter = ('category', 'is_trending', 'programming_language', 'release_date')
    search_fields = ('name', 'description', 'category')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at',)

    def article_count(self, obj):
        return obj.article_set.count()

    article_count.short_description = 'Статей'

    def project_count(self, obj):
        return ProjectTechStack.objects.filter(technology=obj).count()

    project_count.short_description = 'Проектов'

    def avg_rating(self, obj):
        ratings = Rating.objects.filter(object_type='technology', object_id=obj.id)
        avg = ratings.aggregate(Avg('score'))['score__avg']
        return round(avg, 1) if avg else '-'

    avg_rating.short_description = 'Средний рейтинг'


class ProjectCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'project_count', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}

    def project_count(self, obj):
        return obj.project_set.count()

    project_count.short_description = 'Проектов'


class ProgramAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'created_at', 'project_count')
    list_filter = ('created_at',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    raw_id_fields = ('author',)

    def project_count(self, obj):
        return obj.project_set.count()

    project_count.short_description = 'Проектов'


class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'program', 'status', 'start_date', 'end_date', 'is_open_source', 'team_count',
                    'language_count', 'tech_count')
    list_filter = ('status', 'category', 'is_open_source', 'start_date', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ()

    def team_count(self, obj):
        return DevelopmentTeam.objects.filter(project=obj).count()

    team_count.short_description = 'Команд'

    def language_count(self, obj):
        return LanguageUsage.objects.filter(project=obj).count()

    language_count.short_description = 'Языков'

    def tech_count(self, obj):
        return ProjectTechStack.objects.filter(project=obj).count()

    tech_count.short_description = 'Технологий'


class DevelopmentTeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'leader', 'project', 'created_at', 'member_count')
    list_filter = ('created_at', 'project')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    raw_id_fields = ('leader', 'project')

    def member_count(self, obj):
        return UserTeam.objects.filter(team=obj).count()

    member_count.short_description = 'Участников'


class UserTeamAdmin(admin.ModelAdmin):
    list_display = ('user', 'team', 'role', 'joined_at', 'is_active')
    list_filter = ('role', 'is_active', 'joined_at')
    search_fields = ('user__username', 'team__name')
    raw_id_fields = ('user', 'team')


class LanguageUsageAdmin(admin.ModelAdmin):
    list_display = ('project', 'language', 'percentage', 'is_main', 'created_at')
    list_filter = ('is_main', 'language')
    search_fields = ('project__name', 'language__name')
    raw_id_fields = ('project', 'language')


class ProjectTechStackAdmin(admin.ModelAdmin):
    list_display = ('project', 'technology', 'purpose')
    list_filter = ('technology__category',)
    search_fields = ('project__name', 'technology__name', 'purpose')
    raw_id_fields = ('project', 'technology')


class ArticleStatusFilter(admin.SimpleListFilter):
    """Кастомный фильтр для статуса статей"""
    title = 'Статус статьи'
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return (
            ('active', 'Активные (черновики, опубликованные, архив)'),
            ('deleted', 'Удаленные'),
            ('all', 'Все'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'active':
            return queryset.exclude(status='deleted')
        elif self.value() == 'deleted':
            return queryset.filter(status='deleted')
        elif self.value() == 'all':
            return queryset
        return queryset.exclude(status='deleted')


class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'article_type', 'technology', 'project', 'status', 'published_date', 'views',
                    'comment_count', 'is_deleted_display')
    list_filter = (ArticleStatusFilter, 'article_type', 'technology', 'project', 'published_date')
    search_fields = ('title', 'content', 'excerpt', 'tags')
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ('author', 'technology', 'project', 'deleted_by')
    readonly_fields = ('created_at', 'updated_at', 'views', 'deleted_at', 'deleted_by_display')
    date_hierarchy = 'published_date'
    actions = ['soft_delete_selected', 'restore_selected', 'hard_delete_selected']

    fieldsets = (
        ('Основное', {
            'fields': ('title', 'slug', 'excerpt', 'content', 'author', 'article_type')
        }),
        ('Связи', {
            'fields': ('technology', 'project', 'tags')
        }),
        ('Медиа и статус', {
            'fields': ('featured_image', 'status', 'published_date')
        }),
        ('Информация об удалении', {
            'fields': ('deleted_at', 'deleted_by_display'),
            'classes': ('collapse',),
            'description': 'Информация об удалении статьи (если применимо)'
        }),
        ('Статистика', {
            'fields': ('views', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def comment_count(self, obj):
        return obj.comments.count()

    comment_count.short_description = 'Комментариев'

    def is_deleted_display(self, obj):
        if obj.status == 'deleted':
            return format_html(
                '<span style="color: red; font-weight: bold;">🗑 Удалена</span><br>'
                '<small style="color: #666;">{}</small>',
                obj.deleted_at.strftime('%d.%m.%Y %H:%M') if obj.deleted_at else ''
            )
        return format_html('<span style="color: green;">✓ Активна</span>')

    is_deleted_display.short_description = 'Статус удаления'
    is_deleted_display.admin_order_field = 'status'

    def deleted_by_display(self, obj):
        if obj.deleted_by:
            return format_html(
                '<strong>{}</strong><br><small>{}</small>',
                obj.deleted_by.username,
                obj.deleted_by.email
            )
        return '-'

    deleted_by_display.short_description = 'Удалил'

    def get_queryset(self, request):
        """Показываем все статьи, включая удаленные"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(status__in=['draft', 'published', 'archived'])

    def soft_delete_selected(self, request, queryset):
        """Мягкое удаление выбранных статей"""
        count = 0
        for article in queryset:
            if article.status != 'deleted':
                article.soft_delete(request.user)
                count += 1

        self.message_user(
            request,
            f'Успешно удалено {count} статей. Они перемещены в корзину.',
            messages.SUCCESS
        )

    soft_delete_selected.short_description = "Мягкое удаление выбранных статей"

    def restore_selected(self, request, queryset):
        """Восстановление выбранных статей"""
        count = 0
        for article in queryset:
            if article.status == 'deleted':
                article.restore()
                count += 1

        self.message_user(
            request,
            f'Успешно восстановлено {count} статей.',
            messages.SUCCESS
        )

    restore_selected.short_description = "Восстановить выбранные статьи"

    def hard_delete_selected(self, request, queryset):
        """Полное удаление выбранных статей"""
        if not request.user.is_superuser:
            self.message_user(request, "Только суперпользователи могут полностью удалять статьи.", messages.ERROR)
            return

        count = queryset.count()
        for article in queryset:
            article.comments.all().delete()
            Rating.objects.filter(object_type='article', object_id=article.id).delete()
            article.delete()

        self.message_user(
            request,
            f'Успешно полностью удалено {count} статей.',
            messages.SUCCESS
        )

    hard_delete_selected.short_description = "Полное удаление выбранных статей"
    hard_delete_selected.allowed_permissions = ('delete',)

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def delete_model(self, request, obj):
        if request.user.is_superuser:
            obj.comments.all().delete()
            Rating.objects.filter(object_type='article', object_id=obj.id).delete()
            obj.delete()
            self.message_user(request, "Статья полностью удалена.", messages.SUCCESS)
        else:
            obj.soft_delete(request.user)
            self.message_user(request, "Статья перемещена в корзину.", messages.WARNING)

    def get_actions(self, request):
        actions = super().get_actions(request)
        if not request.user.is_superuser:
            if 'hard_delete_selected' in actions:
                del actions['hard_delete_selected']
        return actions


class CommentAdmin(admin.ModelAdmin):
    list_display = ('article', 'author', 'created_at', 'is_approved', 'has_replies')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('content', 'author__username', 'article__title')
    raw_id_fields = ('article', 'author', 'parent')
    actions = ['approve_comments', 'disapprove_comments']

    def has_replies(self, obj):
        return obj.replies.count() > 0

    has_replies.short_description = 'Есть ответы'
    has_replies.boolean = True

    def approve_comments(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, 'Выбранные комментарии одобрены.')

    def disapprove_comments(self, request, queryset):
        queryset.update(is_approved=False)
        self.message_user(request, 'Выбранные комментарии скрыты.')

    approve_comments.short_description = 'Одобрить выбранные комментарии'
    disapprove_comments.short_description = 'Скрыть выбранные комментарии'


class RatingAdmin(admin.ModelAdmin):
    list_display = ('get_object_name', 'object_type', 'user', 'score', 'created_at', 'has_review')
    list_filter = ('object_type', 'score', 'created_at')
    search_fields = ('user__username', 'review')
    raw_id_fields = ('user',)

    def get_object_name(self, obj):
        if obj.object_type == 'technology':
            try:
                tech = Technology.objects.get(id=obj.object_id)
                return tech.name
            except Technology.DoesNotExist:
                return f'Технология #{obj.object_id}'
        elif obj.object_type == 'project':
            try:
                project = Project.objects.get(id=obj.object_id)
                return project.name
            except Project.DoesNotExist:
                return f'Проект #{obj.object_id}'
        elif obj.object_type == 'article':
            try:
                article = Article.objects.get(id=obj.object_id)
                return article.title
            except Article.DoesNotExist:
                return f'Статья #{obj.object_id}'
        return f'Объект #{obj.object_id}'

    get_object_name.short_description = 'Объект'

    def has_review(self, obj):
        return bool(obj.review)

    has_review.short_description = 'Есть отзыв'
    has_review.boolean = True


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('email', 'user', 'is_active', 'subscribed_at', 'category_count', 'technology_count')
    list_filter = ('is_active', 'subscribed_at')
    search_fields = ('email', 'user__username')
    filter_horizontal = ('categories', 'technologies')

    def category_count(self, obj):
        return obj.categories.count()

    category_count.short_description = 'Категорий'

    def technology_count(self, obj):
        return obj.technologies.count()

    technology_count.short_description = 'Технологий'


class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at',)


class ChangeLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'table_name', 'get_record_name', 'changed_by', 'ip_address', 'created_at')
    list_filter = ('action', 'table_name', 'created_at')
    search_fields = ('record_id', 'changed_by__username', 'ip_address')
    readonly_fields = ('action', 'table_name', 'record_id', 'changed_by', 'changes', 'ip_address', 'user_agent',
                       'created_at')
    date_hierarchy = 'created_at'

    def get_record_name(self, obj):
        return f'#{obj.record_id}'

    get_record_name.short_description = 'Запись'


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'job_title', 'company', 'skill_count', 'language_count')
    search_fields = ('user__username', 'user__email', 'bio', 'job_title', 'company')
    filter_horizontal = ('skills', 'programming_languages')

    def skill_count(self, obj):
        return obj.skills.count()

    skill_count.short_description = 'Навыков'

    def language_count(self, obj):
        return obj.programming_languages.count()

    language_count.short_description = 'Языков'


# Регистрация всех моделей
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

admin.site.register(ProgrammingLanguage, ProgrammingLanguageAdmin)
admin.site.register(Technology, TechnologyAdmin)
admin.site.register(ProjectCategory, ProjectCategoryAdmin)
admin.site.register(Program, ProgramAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(DevelopmentTeam, DevelopmentTeamAdmin)
admin.site.register(UserTeam, UserTeamAdmin)
admin.site.register(LanguageUsage, LanguageUsageAdmin)
admin.site.register(ProjectTechStack, ProjectTechStackAdmin)
admin.site.register(Article, ArticleAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Rating, RatingAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(ChangeLog, ChangeLogAdmin)
admin.site.register(UserProfile, UserProfileAdmin)