import random
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings


class Article(models.Model):
    def articles_directory_path(instance, filename):
        return 'articles/{0}'.format(filename)
        
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    article_image = models.FileField(upload_to=articles_directory_path)

    article_title = models.CharField("Заглавие статьи", max_length=200)
    article_date = models.DateTimeField("Дата статьи", default=timezone.now)
    article_author = models.CharField("Автор статьи", max_length=50)
    article_text = models.TextField("Текст статьи")
    is_popular = models.BooleanField("Популярная новость", default=False)
    
    
    def __str__(self):
        return self.article_title


    def get_random_articles(self):
        other_articles = [article for article in Article.objects.all() if article.id != self.id]
        random.shuffle(other_articles)
        return other_articles

    class Meta:
        verbose_name = "Статья"
        verbose_name_plural = "Статьи"
        
class Comment(models.Model):
    class QuestionStatus(models.TextChoices):
        PENDING = 'pending', 'На рассмотрении'
        IN_PROGRESS = 'in_progress', 'В работе'
        ACCEPTED = 'accepted', 'Принят в работу'
        COMPLETED = 'completed', 'Завершён'

    def get_random_color():
        def r(): return random.randint(0, 255)
        return '#%02X%02X%02X' % (r(), r(), r())

    article = models.ForeignKey(Article, on_delete=models.CASCADE, null=True)
    comment_text = models.TextField("Текст комментария")
    comment_date = models.DateTimeField("Дата комментария", default=timezone.now)
    comment_name = models.CharField("Автор комментария", max_length=50)
    comment_email = models.EmailField("Почта автора комментария", max_length=50)
    icon_color = models.CharField("Цвет иконки", max_length=50, default=get_random_color)

    is_question = models.BooleanField("Это вопрос", default=False)
    status = models.CharField(
        "Статус вопроса",
        max_length=20,
        choices=QuestionStatus.choices,
        default=QuestionStatus.PENDING,
        blank=True,
    )

    def __str__(self):
        return self.comment_name

    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        old_status = None
        if not is_new:
            old_obj = Comment.objects.filter(pk=self.pk).first()
            if old_obj:
                old_status = old_obj.status

        super().save(*args, **kwargs)

        if self.is_question:
            if is_new:
                self._send_status_email(
                    subject=f'Ваш вопрос получен: "{self.article.article_title}"',
                    message=(
                        f'Здравствуйте, {self.comment_name}!\n\n'
                        f'Ваш вопрос "{self.comment_text}" к статье "{self.article.article_title}" получен и находится на рассмотрении.\n'
                        f'Мы свяжемся с вами в ближайшее время.\n\n'
                        f'С уважением, УМУП Ульяновскводоканал.'
                    )
                )
            else:
                if old_status and old_status != self.status:
                    status_display = self.get_status_display()
                    self._send_status_email(
                        subject=f'Статус вашего вопроса изменён: "{self.article.article_title}"',
                        message=f'Здравствуйте, {self.comment_name}!\n\n'
                                f'Статус вашего вопроса "{self.comment_text}" к статье "{self.article.article_title}" изменён на "{status_display}".\n\n'
                                f'С уважением, УМУП Ульяновскводоканал.'
                    )

    def _send_status_email(self, subject, message):
        try:
            result = send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[self.comment_email],
                fail_silently=False,
            )
            print(f"[EMAIL] Письмо отправлено на {self.comment_email}. Результат: {result}")
        except Exception as e:
            print(f"[EMAIL] ОШИБКА при отправке на {self.comment_email}: {e}")