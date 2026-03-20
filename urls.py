from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    # Основные страницы
    path('', views.home, name='home'),
    path('search/', views.search, name='search'),
    path('statistics/', views.statistics, name='statistics'),
    path('changelog/', views.changelog, name='changelog'),

    # Статьи
    path('articles/', views.article_list, name='article_list'),
    path('articles/create/', views.create_article, name='create_article'),
    path('articles/<slug:slug>/', views.article_detail, name='article_detail'),
    path('articles/<slug:slug>/comment/', views.add_comment, name='add_comment'),

    # Технологии
    path('technologies/', views.technology_list, name='technology_list'),
    path('technologies/create/', views.create_technology, name='create_technology'),
    path('technologies/<slug:slug>/', views.technology_detail, name='technology_detail'),

    # Проекты
    path('projects/', views.project_list, name='project_list'),
    path('projects/create/', views.create_project, name='create_project'),
    path('projects/<slug:slug>/', views.project_detail, name='project_detail'),
    path('my-projects/', views.my_projects, name='my_projects'),

    # Программы
    path('programs/', views.program_list, name='program_list'),
    path('programs/<slug:slug>/', views.program_detail, name='program_detail'),

    # Команды
    path('teams/', views.team_list, name='team_list'),
    path('teams/create/', views.create_team, name='create_team'),
    path('teams/<slug:slug>/', views.team_detail, name='team_detail'),
    path('teams/<int:team_id>/join/', views.join_team, name='join_team'),
    path('teams/<int:team_id>/leave/', views.leave_team, name='leave_team'),
    path('my-teams/', views.my_teams, name='my_teams'),

    # Языки программирования
    path('languages/', views.language_list, name='language_list'),
    path('languages/<int:pk>/', views.language_detail, name='language_detail'),
    path('languages/statistics/', views.language_statistics, name='language_statistics'),

    # Пользователи
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.profile, name='profile'),

    # Действия
    path('rate/', views.rate_object, name='rate_object'),
    path('subscribe/', views.subscribe, name='subscribe'),

    # API для мобильного приложения
    path('api/articles/', views.api_articles, name='api_articles'),
    path('api/technologies/', views.api_technologies, name='api_technologies'),

    # Приглашения
    path('teams/<int:team_id>/invite/', views.invite_to_team, name='invite_to_team'),
    path('invitations/<str:token>/', views.invitation_detail, name='invitation_detail'),
    path('invitations/accept/<str:token>/', views.accept_invitation, name='accept_invitation'),
    path('invitations/decline/<str:token>/', views.decline_invitation, name='decline_invitation'),
    path('my-invitations/', views.my_invitations, name='my_invitations'),


    path('teams/<int:team_id>/invite/', views.invite_to_team, name='invite_to_team'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)