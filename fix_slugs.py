# reviews/management/commands/fix_slugs.py
from django.core.management.base import BaseCommand
from reviews.models import Article, Technology, Project, Program, DevelopmentTeam, ProjectCategory, Tag, ProgrammingLanguage
from django.utils.text import slugify
import uuid


class Command(BaseCommand):
    help = 'Исправляет неправильные slug для всех моделей'

    def handle(self, *args, **kwargs):
        models_to_fix = [
            (Article, 'title'),
            (Technology, 'name'),
            (Project, 'name'),
            (Program, 'name'),
            (DevelopmentTeam, 'name'),
            (ProjectCategory, 'name'),
            (Tag, 'name'),
            (ProgrammingLanguage, 'name'),
        ]

        for model, name_field in models_to_fix:
            self.stdout.write(f"\nПроверка {model.__name__}...")
            fixed_count = 0

            records = model.objects.all()
            for record in records:
                old_slug = record.slug
                needs_fix = False

                # Проверяем, нужно ли исправить slug
                if not record.slug or record.slug.strip() == '':
                    needs_fix = True
                elif record.slug.startswith('-') or record.slug.endswith('-'):
                    needs_fix = True
                elif model.objects.filter(slug=record.slug).exclude(id=record.id).exists():
                    needs_fix = True

                if needs_fix:
                    # Получаем имя для генерации slug
                    name_value = getattr(record, name_field, '')

                    if name_value:
                        # Генерируем базовый slug
                        base_slug = slugify(name_value)
                    else:
                        base_slug = f"{model.__name__.lower()}-{uuid.uuid4().hex[:8]}"

                    # Убедимся, что slug не начинается или заканчивается дефисом
                    if base_slug.startswith('-'):
                        base_slug = base_slug[1:]
                    if base_slug.endswith('-'):
                        base_slug = base_slug[:-1]

                    # Если slug пустой
                    if not base_slug or base_slug.strip() == '':
                        base_slug = f"{model.__name__.lower()}-{uuid.uuid4().hex[:8]}"

                    # Устанавливаем новый slug
                    record.slug = base_slug

                    # Проверяем уникальность
                    counter = 1
                    original_slug = record.slug
                    while model.objects.filter(slug=record.slug).exclude(id=record.id).exists():
                        suffix = uuid.uuid4().hex[:8]
                        record.slug = f"{original_slug}-{suffix}"
                        counter += 1
                        if counter > 100:
                            record.slug = f"{original_slug}-{uuid.uuid4()}"
                            break

                    # Сохраняем изменения
                    record.save(update_fields=['slug'])
                    fixed_count += 1

                    self.stdout.write(f"  Исправлен {model.__name__} '{name_value}': {old_slug} -> {record.slug}")

            if fixed_count > 0:
                self.stdout.write(f"  Исправлено записей: {fixed_count}")
            else:
                self.stdout.write(f"  Все slug в порядке")

        self.stdout.write(self.style.SUCCESS("\nГотово! Все slug проверены и исправлены."))