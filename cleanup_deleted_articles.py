from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from reviews.models import Article
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Очистка старых удаленных статей (старше 30 дней)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Количество дней, после которого удаленные статьи будут полностью удалены (по умолчанию: 30)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать, что будет удалено, без фактического удаления'
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']

        cutoff_date = timezone.now() - timedelta(days=days)

        # Находим статьи, удаленные более days дней назад
        old_deleted_articles = Article.objects.filter(
            status='deleted',
            deleted_at__lt=cutoff_date
        )

        article_count = old_deleted_articles.count()

        if dry_run:
            self.stdout.write(self.style.WARNING(
                f'[DRY RUN] Найдено {article_count} статей для удаления (удалены более {days} дней назад):'
            ))

            for article in old_deleted_articles:
                self.stdout.write(f'  - "{article.title}" (ID: {article.id}, удалена: {article.deleted_at})')

            self.stdout.write(self.style.SUCCESS(
                f'[DRY RUN] Завершено. Будет удалено {article_count} статей.'
            ))
            return

        # Полное удаление старых статей
        deleted_count = 0
        for article in old_deleted_articles:
            try:
                # Удаляем связанные данные
                article.comments.all().delete()
                from reviews.models import Rating
                Rating.objects.filter(object_type='article', object_id=article.id).delete()

                # Удаляем статью
                article.delete()
                deleted_count += 1

                self.stdout.write(f'Удалена статья: "{article.title}" (ID: {article.id})')

            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f'Ошибка при удалении статьи {article.id}: {str(e)}'
                ))
                logger.error(f'Ошибка при удалении статьи {article.id}: {str(e)}')

        if deleted_count > 0:
            self.stdout.write(self.style.SUCCESS(
                f'Успешно удалено {deleted_count} старых удаленных статей.'
            ))
        else:
            self.stdout.write(self.style.WARNING(
                'Не найдено статей для удаления.'
            ))