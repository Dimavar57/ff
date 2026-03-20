from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg, Sum, Max
from django.utils import timezone
from django.db import IntegrityError
import json
import secrets
from django.utils.timezone import timedelta
from django.core.mail import send_mail
from django.template.loader import render_to_string

from techreview import settings
from .models import (
    Article, Technology, Project, Program, DevelopmentTeam,
    ProgrammingLanguage, ProjectCategory, UserProfile, Comment,
    Rating, Subscription, UserTeam, LanguageUsage, ProjectTechStack,
    Tag, ChangeLog, TeamInvitation
)
from .forms import (
    ArticleForm, UserRegisterForm, UserLoginForm, UserProfileForm,
    CommentForm, RatingForm, TechnologyForm, ProjectForm,
    ProgramForm, DevelopmentTeamForm, UserTeamForm,
    LanguageUsageForm, ProjectTechStackForm, SubscriptionForm,
    SearchForm, TeamInvitationForm, InvitationResponseForm
)



@login_required
def invite_to_team(request, team_id):
    team = get_object_or_404(DevelopmentTeam, id=team_id)
    user = request.user

    # Проверка: пользователь — лидер команды
    if team.leader != user:
        messages.error(request, "Только лидер может приглашать участников.")
        return HttpResponseForbidden()

    # Пример: приглашаем другого пользователя (можно расширить)
    users = UserProfile.objects.exclude(user=user).exclude(user__in=team.members.all())

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        invited_user = get_object_or_404(UserProfile, id=user_id).user
        UserTeam.objects.get_or_create(team=team, user=invited_user, role='member')
        messages.success(request, f"Пользователь {invited_user.username} приглашён в команду!")
        return redirect('team_detail', pk=team.id)

    return render(request, 'reviews/invite_to_team.html', {
        'team': team,
        'users': users
    })


def team_detail(request, slug):
    """Детальная страница команды с оптимизированными запросами"""
    team = get_object_or_404(
        DevelopmentTeam.objects.select_related('leader', 'project'),
        slug=slug
    )
    
    # Оптимизированный запрос участников
    members = UserTeam.objects.filter(
        team=team, 
        is_active=True
    ).select_related('user').order_by('role')
    
    # Проверяем, является ли пользователь участником команды
    is_member = False
    user_team = None
    if request.user.is_authenticated:
        try:
            user_team = UserTeam.objects.get(user=request.user, team=team)
            is_member = user_team.is_active
        except UserTeam.DoesNotExist:
            pass
    
    # Получаем приглашения для лидера команды
    all_invitations = []
    pending_invitations = []
    pending_count = 0
    
    if request.user == team.leader or request.user.is_staff:
        all_invitations = team.invitations.all().order_by('-created_at')[:5]
        pending_invitations = team.invitations.filter(status='pending').order_by('-created_at')[:5]
        pending_count = team.invitations.filter(status='pending').count()

    context = {
        'team': team,
        'members': members,
        'is_member': is_member,
        'user_team': user_team,
        'role_choices': dict(UserTeam.ROLE_CHOICES),
        'all_invitations': all_invitations,
        'pending_invitations': pending_invitations,
        'pending_count': pending_count,
    }

    return render(request, 'reviews/team_detail.html', context)


def statistics(request):
    """Страница статистики"""
    # Общая статистика
    stats = {
        'total_articles': Article.objects.filter(status='published').count(),
        'total_technologies': Technology.objects.count(),
        'total_projects': Project.objects.count(),
        'total_users': User.objects.count(),
        'total_comments': Comment.objects.filter(is_approved=True).count(),
        'total_teams': DevelopmentTeam.objects.count(),
        'total_ratings': Rating.objects.count(),
    }

    # Популярные статьи
    popular_articles = Article.objects.filter(status='published').order_by('-views')[:10]

    # Технологии с лучшим рейтингом
    technologies_with_rating = []
    for tech in Technology.objects.all():
        avg_rating = Rating.objects.filter(
            object_type='technology',
            object_id=tech.id
        ).aggregate(Avg('score'))['score__avg']

        if avg_rating:
            review_count = Rating.objects.filter(
                object_type='technology',
                object_id=tech.id
            ).count()

            technologies_with_rating.append({
                'technology': tech,
                'rating': avg_rating,
                'review_count': review_count
            })

    top_technologies = sorted(technologies_with_rating, key=lambda x: x['rating'], reverse=True)[:10]

    # Активные пользователи
    active_users = User.objects.annotate(
        article_count=Count('article'),
        comment_count=Count('comment')
    ).order_by('-article_count')[:10]

    # Распределение проектов по статусам
    project_statuses = Project.objects.values('status').annotate(
        count=Count('id')
    ).order_by('status')

    context = {
        'stats': stats,
        'popular_articles': popular_articles,
        'top_technologies': top_technologies,
        'active_users': active_users,
        'project_statuses': project_statuses,
    }

    return render(request, 'reviews/statistics.html', context)


def language_statistics(request):
    """Статистика использования языков программирования"""
    base_stats = LanguageUsage.objects.values(
        'language__name',
        'language__id'
    ).annotate(
        project_count=Count('project', distinct=True),
        avg_percentage=Avg('percentage'),
        latest_usage=Max('created_at')
    ).order_by('-project_count')

    language_stats = []
    for stat in base_stats:
        total_usage = LanguageUsage.objects.filter(
            language__id=stat['language__id']
        ).aggregate(total=Sum('percentage'))['total'] or 0

        language_stats.append({
            **stat,
            'total_percentage': total_usage
        })

    popular_languages = language_stats[:10]

    ninety_days_ago = timezone.now() - timedelta(days=90)
    active_languages = LanguageUsage.objects.filter(
        created_at__gte=ninety_days_ago
    ).values('language__name', 'language__id').annotate(
        recent_project_count=Count('project', distinct=True)
    ).order_by('-recent_project_count')[:10]

    languages_by_category = LanguageUsage.objects.values(
        'language__name',
        'project__category__name'
    ).annotate(
        category_project_count=Count('project', distinct=True)
    ).order_by('language__name', '-category_project_count')

    category_stats = {}
    for item in languages_by_category:
        lang_name = item['language__name']
        category_name = item['project__category__name'] or 'Без категории'

        if lang_name not in category_stats:
            category_stats[lang_name] = {}
        category_stats[lang_name][category_name] = item['category_project_count']

    trends = {}
    current_year = timezone.now().year
    for year_offset in range(3):
        year = current_year - year_offset
        year_trend = LanguageUsage.objects.filter(
            created_at__year=year
        ).values('language__name').annotate(
            yearly_count=Count('project', distinct=True)
        ).order_by('-yearly_count')[:5]
        trends[year] = list(year_trend)

    total_languages = len(language_stats)
    total_projects = sum(stat['project_count'] for stat in language_stats)
    avg_projects = total_projects / total_languages if total_languages > 0 else 0
    total_percentage = sum(stat['total_percentage'] for stat in language_stats)

    context = {
        'language_stats': language_stats,
        'popular_languages': popular_languages,
        'active_languages': active_languages,
        'category_stats': category_stats,
        'trends': trends,
        'current_year': current_year,
        'total_languages': total_languages,
        'total_projects': total_projects,
        'avg_projects': round(avg_projects, 1),
        'total_percentage': round(total_percentage, 0),
    }

    return render(request, 'reviews/language_statistics.html', context)


@login_required
def my_projects(request):
    """Проекты пользователя"""
    created_projects = Project.objects.filter(
        id__in=Program.objects.filter(author=request.user).values('project__id')
    )

    user_teams = UserTeam.objects.filter(user=request.user, is_active=True)
    participating_projects = Project.objects.filter(
        id__in=DevelopmentTeam.objects.filter(
            id__in=user_teams.values('team_id')
        ).values('project_id')
    )

    released_count = created_projects.filter(status='released').count()

    context = {
        'created_projects': created_projects,
        'participating_projects': participating_projects,
        'user_teams': user_teams,
        'released_count': released_count,
    }

    return render(request, 'reviews/my_projects.html', context)


@login_required
def my_teams(request):
    """Команды пользователя"""
    led_teams = DevelopmentTeam.objects.filter(leader=request.user)

    user_teams = UserTeam.objects.filter(user=request.user, is_active=True)
    participating_teams = DevelopmentTeam.objects.filter(
        id__in=user_teams.values('team_id')
    ).exclude(leader=request.user)

    total_projects = Project.objects.filter(
        id__in=led_teams.values('project_id')
    ).distinct().count()

    total_members = UserTeam.objects.filter(
        team__in=led_teams,
        is_active=True
    ).count()

    for team in led_teams:
        team.member_count = UserTeam.objects.filter(team=team, is_active=True).count()

    for team in participating_teams:
        team.member_count = UserTeam.objects.filter(team=team, is_active=True).count()
        try:
            team.user_team = UserTeam.objects.get(user=request.user, team=team)
        except UserTeam.DoesNotExist:
            pass

    context = {
        'led_teams': led_teams,
        'participating_teams': participating_teams,
        'total_projects': total_projects,
        'total_members': total_members,
    }

    return render(request, 'reviews/my_teams.html', context)


@login_required
def profile(request):
    """Профиль пользователя"""
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль успешно обновлен!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=user_profile)

    user_articles = Article.objects.filter(author=request.user).exclude(slug='').order_by('-published_date')[:10]
    user_comments = Comment.objects.filter(author=request.user).order_by('-created_at')[:10]
    user_teams = UserTeam.objects.filter(user=request.user, is_active=True)
    user_ratings = Rating.objects.filter(user=request.user).order_by('-created_at')[:10]

    context = {
        'form': form,
        'user_profile': user_profile,
        'user_articles': user_articles,
        'user_comments': user_comments,
        'user_teams': user_teams,
        'user_ratings': user_ratings,
    }

    return render(request, 'reviews/profile.html', context)


@login_required
def create_technology(request):
    """Создание новой технологии"""
    if request.method == 'POST':
        form = TechnologyForm(request.POST)
        if form.is_valid():
            technology = form.save()
            messages.success(request, 'Технология успешно создана!')
            return redirect('technology_detail', slug=technology.slug)
    else:
        form = TechnologyForm()

    context = {
        'form': form,
        'title': 'Создать технологию',
    }

    return render(request, 'reviews/technology_form.html', context)


def home(request):
    """Главная страница"""
    latest_articles = Article.objects.filter(status='published').order_by('-published_date')[:5]
    trending_technologies = Technology.objects.filter(is_trending=True).order_by('-release_date')[:5]
    latest_projects = Project.objects.filter(status='released').order_by('-created_at')[:5]
    popular_articles = Article.objects.filter(status='published').order_by('-views')[:5]

    stats = {
        'total_articles': Article.objects.filter(status='published').count(),
        'total_technologies': Technology.objects.count(),
        'total_projects': Project.objects.count(),
        'total_users': UserProfile.objects.count(),
    }

    context = {
        'latest_articles': latest_articles,
        'trending_technologies': trending_technologies,
        'latest_projects': latest_projects,
        'popular_articles': popular_articles,
        'stats': stats,
    }

    return render(request, 'reviews/home.html', context)


def article_list(request):
    """Список статей"""
    articles = Article.objects.filter(status='published').exclude(status='deleted').order_by('-published_date')
    article_type = request.GET.get('type')
    if article_type:
        articles = articles.filter(article_type=article_type)

    query = request.GET.get('q')
    if query:
        articles = articles.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(excerpt__icontains=query) |
            Q(tags__icontains=query)
        )

    paginator = Paginator(articles, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'article_types': dict(Article.ARTICLE_TYPE_CHOICES),
        'query': query,
        'article_type': article_type,
    }

    return render(request, 'reviews/article_list.html', context)


def article_detail(request, slug):
    """Детальная страница статьи"""
    try:
        article = Article.objects.get(slug=slug, status='published')
        if article.status == 'deleted':
            raise Http404("Статья не найдена или была удалена")
    except Article.DoesNotExist:
        if request.user.is_authenticated:
            try:
                article = Article.objects.get(slug=slug, author=request.user)
                if article.status == 'draft':
                    messages.info(request, 'Вы просматриваете черновик. Эта статья не видна другим пользователям.')
                elif article.status == 'archived':
                    messages.info(request, 'Эта статья в архиве.')
            except Article.DoesNotExist:
                raise Http404("Статья не найдена")
        else:
            raise Http404("Статья не найдена")

    if article.status == 'published':
        article.increment_views()

    comments = article.comments.filter(parent=None, is_approved=True).order_by('-created_at')
    comment_form = CommentForm()
    rating_form = RatingForm()

    user_rating = None
    if request.user.is_authenticated:
        try:
            user_rating = Rating.objects.get(
                object_type='article',
                object_id=article.id,
                user=request.user
            )
        except Rating.DoesNotExist:
            pass

    similar_articles = Article.objects.filter(
        status='published'
    ).exclude(id=article.id)

    if article.technology:
        similar_articles = similar_articles.filter(technology=article.technology)
    if article.project:
        similar_articles = similar_articles.filter(project=article.project)

    similar_articles = similar_articles.order_by('-views')[:3]

    context = {
        'article': article,
        'comments': comments,
        'comment_form': comment_form,
        'rating_form': rating_form,
        'user_rating': user_rating,
        'similar_articles': similar_articles,
    }

    return render(request, 'reviews/article_detail.html', context)


@login_required
def create_article(request):
    """Создание новой статьи"""
    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            if article.status == 'published':
                article.published_date = timezone.now()
            article.save()
            messages.success(request, 'Статья успешно создана!')
            if article.slug:
                return redirect('article_detail', slug=article.slug)
            else:
                return redirect('article_detail', slug=str(article.id))
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = ArticleForm()

    context = {
        'form': form,
        'title': 'Создать статью',
    }

    return render(request, 'reviews/article_form.html', context)


@login_required
def add_comment(request, slug):
    """Добавление комментария к статье"""
    article = get_object_or_404(Article, slug=slug)

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.article = article
            comment.author = request.user

            parent_id = request.POST.get('parent_id')
            if parent_id:
                try:
                    parent_comment = Comment.objects.get(id=parent_id)
                    comment.parent = parent_comment
                except Comment.DoesNotExist:
                    pass

            comment.save()
            messages.success(request, 'Комментарий добавлен!')

    return redirect('article_detail', slug=article.slug)


def technology_list(request):
    """Список технологий"""
    technologies = Technology.objects.all().order_by('-release_date')
    trending_technologies = Technology.objects.filter(is_trending=True).order_by('-release_date')[:8]
    categories = Technology.objects.values_list('category', flat=True).distinct()
    languages = ProgrammingLanguage.objects.all()

    query = request.GET.get('q')
    if query:
        technologies = technologies.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__icontains=query)
        )

    category = request.GET.get('category')
    if category:
        technologies = technologies.filter(category=category)

    language_id = request.GET.get('language')
    if language_id:
        technologies = technologies.filter(programming_language_id=language_id)

    total_technologies = Technology.objects.count()
    trending_count = Technology.objects.filter(is_trending=True).count()
    current_year = timezone.now().year
    current_year_count = Technology.objects.filter(release_date__year=current_year).count()

    paginator = Paginator(technologies, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'trending_technologies': trending_technologies,
        'categories': categories,
        'languages': languages,
        'query': query,
        'selected_category': category,
        'selected_language': language_id,
        'total_technologies': total_technologies,
        'trending_count': trending_count,
        'current_year': current_year_count,
    }

    return render(request, 'reviews/technology_list.html', context)


def technology_detail(request, slug):
    """Детальная страница технологии"""
    technology = get_object_or_404(Technology, slug=slug)

    articles = Article.objects.filter(technology=technology, status='published').order_by('-published_date')[:5]
    projects = Project.objects.filter(
        id__in=ProjectTechStack.objects.filter(technology=technology).values('project_id')
    )[:5]

    avg_rating = Rating.objects.filter(
        object_type='technology',
        object_id=technology.id
    ).aggregate(Avg('score'))['score__avg']

    rating_form = RatingForm()

    user_rating = None
    if request.user.is_authenticated:
        try:
            user_rating = Rating.objects.get(
                object_type='technology',
                object_id=technology.id,
                user=request.user
            )
        except Rating.DoesNotExist:
            pass

    context = {
        'technology': technology,
        'articles': articles,
        'projects': projects,
        'avg_rating': avg_rating,
        'rating_form': rating_form,
        'user_rating': user_rating,
    }

    return render(request, 'reviews/technology_detail.html', context)


def project_list(request):
    """Список проектов"""
    projects = Project.objects.all().order_by('-created_at')

    category_id = request.GET.get('category')
    if category_id:
        projects = projects.filter(category_id=category_id)

    status = request.GET.get('status')
    if status:
        projects = projects.filter(status=status)

    query = request.GET.get('q')
    if query:
        projects = projects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )

    categories = ProjectCategory.objects.all()

    paginator = Paginator(projects, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'categories': categories,
        'status_choices': dict(Project.STATUS_CHOICES),
        'query': query,
        'selected_category': category_id,
        'selected_status': status,
    }

    return render(request, 'reviews/project_list.html', context)


def project_detail(request, slug):
    """Детальная страница проекта"""
    project = get_object_or_404(Project, slug=slug)

    articles = Article.objects.filter(project=project, status='published').order_by('-published_date')[:5]
    teams = DevelopmentTeam.objects.filter(project=project)
    languages = LanguageUsage.objects.filter(project=project).order_by('-percentage')
    tech_stack = ProjectTechStack.objects.filter(project=project)

    avg_rating = Rating.objects.filter(
        object_type='project',
        object_id=project.id
    ).aggregate(Avg('score'))['score__avg']

    rating_form = RatingForm()

    user_rating = None
    if request.user.is_authenticated:
        try:
            user_rating = Rating.objects.get(
                object_type='project',
                object_id=project.id,
                user=request.user
            )
        except Rating.DoesNotExist:
            pass

    context = {
        'project': project,
        'articles': articles,
        'teams': teams,
        'languages': languages,
        'tech_stack': tech_stack,
        'avg_rating': avg_rating,
        'rating_form': rating_form,
        'user_rating': user_rating,
    }

    return render(request, 'reviews/project_detail.html', context)


@login_required
def create_project(request):
    """Создание нового проекта"""
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save()
            messages.success(request, 'Проект успешно создан!')
            return redirect('project_detail', slug=project.slug)
    else:
        form = ProjectForm()

    context = {
        'form': form,
        'title': 'Создать проект',
    }

    return render(request, 'reviews/project_form.html', context)


def program_list(request):
    """Список программ"""
    programs = Program.objects.all().order_by('-created_at')

    query = request.GET.get('q')
    if query:
        programs = programs.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )

    paginator = Paginator(programs, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
    }

    return render(request, 'reviews/program_list.html', context)


def program_detail(request, slug):
    """Детальная страница программы"""
    program = get_object_or_404(Program, slug=slug)
    projects = program.project_set.all()

    context = {
        'program': program,
        'projects': projects,
    }

    return render(request, 'reviews/program_detail.html', context)


def team_list(request):
    """Список команд"""
    teams = DevelopmentTeam.objects.all().order_by('-created_at')

    project_id = request.GET.get('project')
    if project_id:
        teams = teams.filter(project_id=project_id)

    query = request.GET.get('q')
    if query:
        teams = teams.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )

    projects = Project.objects.all()

    paginator = Paginator(teams, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'projects': projects,
        'query': query,
        'selected_project': project_id,
    }

    return render(request, 'reviews/team_list.html', context)


@login_required
def create_team(request):
    """Создание новой команды"""
    if request.method == 'POST':
        form = DevelopmentTeamForm(request.POST)
        if form.is_valid():
            team = form.save(commit=False)
            team.leader = request.user
            team.save()

            UserTeam.objects.create(
                user=request.user,
                team=team,
                role='manager',
                is_active=True
            )

            messages.success(request, 'Команда успешно создана!')
            return redirect('team_detail', slug=team.slug)
    else:
        form = DevelopmentTeamForm()

    context = {
        'form': form,
        'title': 'Создать команду',
    }

    return render(request, 'reviews/team_form.html', context)


@login_required
def join_team(request, team_id):
    """Вступление в команду"""
    team = get_object_or_404(DevelopmentTeam, id=team_id)

    if not UserTeam.objects.filter(user=request.user, team=team).exists():
        UserTeam.objects.create(
            user=request.user,
            team=team,
            role='contributor',
            is_active=True
        )
        messages.success(request, 'Вы успешно вступили в команду!')

    return redirect('team_detail', slug=team.slug)


@login_required
def leave_team(request, team_id):
    """Выход из команды"""
    team = get_object_or_404(DevelopmentTeam, id=team_id)
    UserTeam.objects.filter(user=request.user, team=team).delete()
    messages.success(request, 'Вы вышли из команды')

    return redirect('team_detail', slug=team.slug)


def language_list(request):
    """Список языков программирования"""
    languages = ProgrammingLanguage.objects.all().order_by('-popularity_index')

    is_active = request.GET.get('is_active')
    if is_active == 'true':
        languages = languages.filter(is_active=True)
    elif is_active == 'false':
        languages = languages.filter(is_active=False)

    query = request.GET.get('q')
    if query:
        languages = languages.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )

    paginator = Paginator(languages, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    language_usage = LanguageUsage.objects.values('language__name').annotate(
        project_count=Count('project'),
        avg_percentage=Avg('percentage')
    ).order_by('-project_count')[:10]

    context = {
        'page_obj': page_obj,
        'query': query,
        'selected_active': is_active,
        'language_usage': language_usage,
    }

    return render(request, 'reviews/language_list.html', context)


def language_detail(request, pk):
    """Детальная страница языка программирования"""
    language = get_object_or_404(ProgrammingLanguage, pk=pk)

    technologies = Technology.objects.filter(programming_language=language).order_by('-release_date')
    projects = Project.objects.filter(
        id__in=LanguageUsage.objects.filter(language=language).values('project_id')
    )[:10]

    usage_stats = LanguageUsage.objects.filter(language=language).aggregate(
        total_projects=Count('project'),
        avg_percentage=Avg('percentage')
    )

    context = {
        'language': language,
        'technologies': technologies,
        'projects': projects,
        'usage_stats': usage_stats,
    }

    return render(request, 'reviews/language_detail.html', context)


def register(request):
    """Регистрация пользователя"""
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                UserProfile.objects.get_or_create(user=user)
                login(request, user)
                messages.success(request, 'Регистрация прошла успешно!')
                return redirect('home')
            except Exception as e:
                messages.error(request, f'Ошибка регистрации: {str(e)[:50]}...')
    else:
        form = UserRegisterForm()

    context = {'form': form}
    return render(request, 'reviews/register.html', context)


def user_login(request):
    """Авторизация пользователя"""
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, 'Вы успешно вошли в систему!')
                return redirect('home')
            else:
                messages.error(request, 'Неверное имя пользователя или пароль')
    else:
        form = UserLoginForm()

    context = {'form': form}
    return render(request, 'reviews/login.html', context)


def user_logout(request):
    """Выход из системы"""
    logout(request)
    messages.success(request, 'Вы вышли из системы')
    return redirect('home')


@login_required
def rate_object(request):
    """Оценка объекта (технологии, проекта, статьи)"""
    if request.method == 'POST':
        form = RatingForm(request.POST)
        if form.is_valid():
            object_type = request.POST.get('object_type')
            object_id = request.POST.get('object_id')

            rating, created = Rating.objects.get_or_create(
                object_type=object_type,
                object_id=object_id,
                user=request.user,
                defaults=form.cleaned_data
            )

            if not created:
                rating.score = form.cleaned_data['score']
                rating.review = form.cleaned_data['review']
                rating.save()

            messages.success(request, 'Спасибо за вашу оценку!')

            if object_type == 'technology':
                technology = Technology.objects.get(id=object_id)
                return redirect('technology_detail', slug=technology.slug)
            elif object_type == 'project':
                project = Project.objects.get(id=object_id)
                return redirect('project_detail', slug=project.slug)
            elif object_type == 'article':
                article = Article.objects.get(id=object_id)
                return redirect('article_detail', slug=article.slug)

    return redirect('home')


def subscribe(request):
    """Подписка на рассылку"""
    if request.method == 'POST':
        form = SubscriptionForm(request.POST)
        if form.is_valid():
            subscription, created = Subscription.objects.get_or_create(
                email=form.cleaned_data['email'],
                defaults=form.cleaned_data
            )

            if not created:
                subscription.is_active = True
                subscription.save()
                subscription.categories.set(form.cleaned_data['categories'])
                subscription.technologies.set(form.cleaned_data['technologies'])
                messages.success(request, 'Ваши настройки подписки обновлены!')
            else:
                messages.success(request, 'Вы успешно подписались на рассылку!')

            return redirect('home')
    else:
        form = SubscriptionForm()

    context = {'form': form}
    return render(request, 'reviews/subscribe.html', context)


def search(request):
    """Поиск по сайту"""
    form = SearchForm(request.GET or None)
    results = []

    if form.is_valid():
        query = form.cleaned_data.get('q')
        category = form.cleaned_data.get('category')
        technology = form.cleaned_data.get('technology')
        article_type = form.cleaned_data.get('article_type')

        articles = Article.objects.filter(status='published')
        if query:
            articles = articles.filter(
                Q(title__icontains=query) |
                Q(content__icontains=query) |
                Q(excerpt__icontains=query) |
                Q(tags__icontains=query)
            )
        if article_type:
            articles = articles.filter(article_type=article_type)

        technologies = Technology.objects.all()
        if query:
            technologies = technologies.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(category__icontains=query)
            )
        if technology:
            technologies = technologies.filter(id=technology)

        projects = Project.objects.all()
        if query:
            projects = projects.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query)
            )
        if category:
            projects = projects.filter(category_id=category)

        results = {
            'articles': articles[:10],
            'technologies': technologies[:10],
            'projects': projects[:10],
        }

    context = {
        'form': form,
        'results': results,
    }

    return render(request, 'reviews/search.html', context)


def changelog(request):
    """История изменений"""
    changes = ChangeLog.objects.all().order_by('-created_at')

    action = request.GET.get('action')
    if action:
        changes = changes.filter(action=action)

    table = request.GET.get('table')
    if table:
        changes = changes.filter(table_name=table)

    paginator = Paginator(changes, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'action_choices': dict(ChangeLog.ACTION_CHOICES),
        'table_choices': dict(ChangeLog.TABLE_CHOICES),
        'selected_action': action,
        'selected_table': table,
    }

    return render(request, 'reviews/changelog.html', context)


def api_articles(request):
    """API для получения статей (для мобильного приложения)"""
    articles = Article.objects.filter(status='published').order_by('-published_date')

    article_type = request.GET.get('type')
    if article_type:
        articles = articles.filter(article_type=article_type)

    limit = request.GET.get('limit', 20)
    articles = articles[:int(limit)]

    data = []
    for article in articles:
        data.append({
            'id': article.id,
            'title': article.title,
            'excerpt': article.excerpt,
            'author': article.author.username,
            'article_type': article.article_type,
            'views': article.views,
            'published_date': article.published_date.isoformat(),
            'tags': article.get_tags_list(),
            'url': request.build_absolute_uri(article.get_absolute_url()),
        })

    return JsonResponse(data, safe=False)


def api_technologies(request):
    """API для получения технологий (для мобильного приложения)"""
    technologies = Technology.objects.all().order_by('-release_date')

    trending = request.GET.get('trending')
    if trending == 'true':
        technologies = technologies.filter(is_trending=True)

    limit = request.GET.get('limit', 20)
    technologies = technologies[:int(limit)]

    data = []
    for tech in technologies:
        avg_rating = Rating.objects.filter(
            object_type='technology',
            object_id=tech.id
        ).aggregate(Avg('score'))['score__avg']

        data.append({
            'id': tech.id,
            'name': tech.name,
            'category': tech.category,
            'release_date': tech.release_date.isoformat(),
            'current_version': tech.current_version,
            'is_trending': tech.is_trending,
            'avg_rating': avg_rating,
            'url': request.build_absolute_uri(tech.get_absolute_url()),
        })

    return JsonResponse(data, safe=False)


@login_required
def invite_to_team(request, team_id):
    """Приглашение участника в команду"""
    team = get_object_or_404(DevelopmentTeam, id=team_id)

    if not (team.leader == request.user or request.user.is_staff):
        messages.error(request, 'У вас нет прав для приглашения участников')
        return redirect('team_detail', slug=team.slug)

    if request.method == 'POST':
        form = TeamInvitationForm(request.POST, team=team, inviter=request.user)
        if form.is_valid():
            invitation = form.save(commit=False)
            invitation.team = team
            invitation.inviter = request.user
            invitation.token = secrets.token_urlsafe(32)
            invitation.expires_at = timezone.now() + timedelta(days=7)

            invitation.save()

            if invitation.invitee:
                send_invitation_email(invitation)
                messages.success(request, f'Приглашение отправлено пользователю {invitation.invitee.username}')
            else:
                send_invitation_email(invitation)
                messages.success(request, f'Приглашение отправлено на email {invitation.email}')

            return redirect('team_detail', slug=team.slug)
    else:
        form = TeamInvitationForm(team=team, inviter=request.user)

    context = {
        'form': form,
        'team': team,
        'title': 'Пригласить участника',
    }

    return render(request, 'reviews/invite_to_team.html', context)


def send_invitation_email(invitation):
    """Отправка email с приглашением"""
    subject = f'Приглашение в команду {invitation.team.name}'

    if invitation.invitee:
        recipient = invitation.invitee.email
        template = 'reviews/emails/invitation_registered.html'
    else:
        recipient = invitation.email
        template = 'reviews/emails/invitation_email.html'

    context = {
        'invitation': invitation,
        'team': invitation.team,
        'inviter': invitation.inviter,
        'accept_url': f"{settings.SITE_URL}/invitations/accept/{invitation.token}/",
        'decline_url': f"{settings.SITE_URL}/invitations/decline/{invitation.token}/",
    }

    html_message = render_to_string(template, context)
    plain_message = f"Вы приглашены в команду {invitation.team.name}.\n\n"
    plain_message += f"Приглашение от: {invitation.inviter.username}\n"
    plain_message += f"Команда: {invitation.team.name}\n"
    plain_message += f"Проект: {invitation.team.project.name if invitation.team.project else 'Без проекта'}\n\n"
    plain_message += f"Чтобы принять приглашение, перейдите по ссылке: {settings.SITE_URL}/invitations/accept/{invitation.token}/\n"
    plain_message += f"Чтобы отклонить приглашение: {settings.SITE_URL}/invitations/decline/{invitation.token}/\n\n"
    plain_message += f"Приглашение действительно до: {invitation.expires_at.strftime('%d.%m.%Y %H:%M')}"

    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient],
        html_message=html_message,
        fail_silently=False,
    )


@login_required
def invitation_detail(request, token):
    """Детальная страница приглашения"""
    invitation = get_object_or_404(TeamInvitation, token=token)

    if invitation.invitee and invitation.invitee != request.user:
        raise Http404("Приглашение не найдено")

    if request.method == 'POST':
        form = InvitationResponseForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']

            if action == 'accept':
                if invitation.accept():
                    messages.success(request, 'Вы успешно вступили в команду!')
                    return redirect('team_detail', slug=invitation.team.slug)
                else:
                    messages.error(request, 'Не удалось принять приглашение. Возможно, оно устарело.')
            elif action == 'decline':
                if invitation.decline():
                    messages.info(request, 'Вы отклонили приглашение.')
                    return redirect('home')

    else:
        form = InvitationResponseForm()

    context = {
        'invitation': invitation,
        'form': form,
    }

    return render(request, 'reviews/invitation_detail.html', context)


def accept_invitation(request, token):
    """Быстрое принятие приглашения по ссылке"""
    invitation = get_object_or_404(TeamInvitation, token=token)

    if invitation.accept():
        messages.success(request, 'Вы успешно вступили в команду!')
    else:
        messages.error(request, 'Не удалось принять приглашение. Возможно, оно устарело.')

    return redirect('team_detail', slug=invitation.team.slug)


def decline_invitation(request, token):
    """Быстрый отказ от приглашения по ссылке"""
    invitation = get_object_or_404(TeamInvitation, token=token)

    if invitation.decline():
        messages.info(request, 'Вы отклонили приглашение.')

    return redirect('home')


@login_required
def my_invitations(request):
    """Список приглашений пользователя"""
    invitations = TeamInvitation.objects.filter(
        invitee=request.user,
        status='pending'
    ).order_by('-created_at')

    context = {
        'invitations': invitations,
    }

    return render(request, 'reviews/my_invitations.html', context)