# reviews/signals.py
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.text import slugify
import uuid
from .models import Article, Technology, Project, Program, DevelopmentTeam, ProjectCategory, Tag, ProgrammingLanguage


def generate_unique_slug(model_class, instance, slug_field='slug', name_field='name'):
    """Генерация уникального slug"""
    if not getattr(instance, slug_field) or getattr(instance, slug_field).strip() == '':
        # Определяем поле с названием
        if hasattr(instance, 'title'):
            name = instance.title
        elif hasattr(instance, 'name'):
            name = instance.name
        else:
            name = str(instance)

        base_slug = slugify(name)

        # Если slugify вернул пустую строку
        if not base_slug or base_slug.strip() == '':
            base_slug = f"{model_class.__name__.lower()}-{uuid.uuid4().hex[:8]}"

        slug = base_slug

        # Проверяем уникальность
        counter = 1
        original_slug = slug
        while model_class.objects.filter(**{slug_field: slug}).exclude(id=instance.id).exists():
            slug = f"{original_slug}-{uuid.uuid4().hex[:8]}"
            counter += 1
            if counter > 100:  # На всякий случай
                slug = f"{original_slug}-{uuid.uuid4()}"
                break

        # Удаляем дефисы в начале и конце
        if slug.startswith('-'):
            slug = slug[1:]
        if slug.endswith('-'):
            slug = slug[:-1]

        setattr(instance, slug_field, slug)
    return instance


@receiver(pre_save, sender=Article)
def generate_article_slug(sender, instance, **kwargs):
    generate_unique_slug(Article, instance, 'slug', 'title')


@receiver(pre_save, sender=Technology)
def generate_technology_slug(sender, instance, **kwargs):
    generate_unique_slug(Technology, instance)


@receiver(pre_save, sender=Project)
def generate_project_slug(sender, instance, **kwargs):
    generate_unique_slug(Project, instance)


@receiver(pre_save, sender=Program)
def generate_program_slug(sender, instance, **kwargs):
    generate_unique_slug(Program, instance)


@receiver(pre_save, sender=DevelopmentTeam)
def generate_team_slug(sender, instance, **kwargs):
    generate_unique_slug(DevelopmentTeam, instance)


@receiver(pre_save, sender=ProjectCategory)
def generate_category_slug(sender, instance, **kwargs):
    generate_unique_slug(ProjectCategory, instance)


@receiver(pre_save, sender=Tag)
def generate_tag_slug(sender, instance, **kwargs):
    generate_unique_slug(Tag, instance)


@receiver(pre_save, sender=ProgrammingLanguage)
def generate_language_slug(sender, instance, **kwargs):
    generate_unique_slug(ProgrammingLanguage, instance)