from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.text import slugify
import uuid
from reviews.models import (
    Article, Technology, Project, Program, DevelopmentTeam,
    ProjectCategory, Tag, ProgrammingLanguage
)


def generate_unique_slug(model_class, instance, slug_field='slug', name_field=None):
    """Генерация уникального slug с улучшенной обработкой"""
    # Если slug уже есть и он валидный, не трогаем
    if getattr(instance, slug_field) and getattr(instance, slug_field).strip():
        current_slug = getattr(instance, slug_field)
        # Проверяем, не начинается/заканчивается ли slug дефисом
        if current_slug.startswith('-') or current_slug.endswith('-'):
            # Нужно исправить
            pass
        else:
            return instance

    # Определяем поле с названием
    if name_field:
        name = getattr(instance, name_field, '')
    elif hasattr(instance, 'title'):
        name = instance.title
    elif hasattr(instance, 'name'):
        name = instance.name
    else:
        name = str(instance)

    if not name:
        name = f"{model_class.__name__.lower()}-{uuid.uuid4().hex[:8]}"

    base_slug = slugify(name)

    # Очищаем slug от дефисов в начале и конце
    base_slug = base_slug.strip('-')

    # Если slug пустой после очистки
    if not base_slug:
        base_slug = f"{model_class.__name__.lower()}-{uuid.uuid4().hex[:8]}"

    slug = base_slug

    # Проверяем уникальность
    counter = 1
    original_slug = slug
    while model_class.objects.filter(**{slug_field: slug}).exclude(id=instance.id).exists():
        slug = f"{original_slug}-{uuid.uuid4().hex[:8]}"
        counter += 1
        if counter > 100:
            slug = f"{original_slug}-{uuid.uuid4()}"
            break

    setattr(instance, slug_field, slug)
    return instance


@receiver(pre_save, sender=Article)
def generate_article_slug(sender, instance, **kwargs):
    generate_unique_slug(Article, instance, 'slug', 'title')


@receiver(pre_save, sender=Technology)
def generate_technology_slug(sender, instance, **kwargs):
    generate_unique_slug(Technology, instance, 'slug', 'name')


@receiver(pre_save, sender=Project)
def generate_project_slug(sender, instance, **kwargs):
    generate_unique_slug(Project, instance, 'slug', 'name')


@receiver(pre_save, sender=Program)
def generate_program_slug(sender, instance, **kwargs):
    generate_unique_slug(Program, instance, 'slug', 'name')


@receiver(pre_save, sender=DevelopmentTeam)
def generate_team_slug(sender, instance, **kwargs):
    generate_unique_slug(DevelopmentTeam, instance, 'slug', 'name')


@receiver(pre_save, sender=ProjectCategory)
def generate_category_slug(sender, instance, **kwargs):
    generate_unique_slug(ProjectCategory, instance, 'slug', 'name')


@receiver(pre_save, sender=Tag)
def generate_tag_slug(sender, instance, **kwargs):
    generate_unique_slug(Tag, instance, 'slug', 'name')


@receiver(pre_save, sender=ProgrammingLanguage)
def generate_language_slug(sender, instance, **kwargs):
    generate_unique_slug(ProgrammingLanguage, instance, 'slug', 'name')