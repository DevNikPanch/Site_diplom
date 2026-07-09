import random
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


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
    def get_random_color():
        def r(): return random.randint(0, 255)
        return '#%02X%02X%02X' % (r(), r(), r())

    article = models.ForeignKey(Article, on_delete=models.CASCADE, null=True)
    comment_text = models.TextField("Текст комментария")
    comment_date = models.DateTimeField("Дата комментария", default=timezone.now)
    comment_name = models.CharField("Автор комментария", max_length=50)    
    comment_email = models.EmailField(
        "Почта автора комментария", max_length=50)

    icon_color = models.CharField("Цвет иконки", max_length=50, default=get_random_color)

    def __str__(self):
        return self.comment_name

    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"