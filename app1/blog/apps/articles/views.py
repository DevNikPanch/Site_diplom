from django.http import HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render
from .models import Comment, Article


def index(request):
    articles = Article.objects.order_by('-article_date')
    popular_articles = Article.objects.filter(is_popular=True)
    return render(request, 'articles/articles.html', {"articles": articles, "popular_articles": popular_articles})


def section(request, article_id):
    article = Article.objects.get(id=article_id)
    comments = article.comment_set.order_by("-comment_date")[:10]
    user = article.user
    similar_articles = article.get_random_articles()
    return render(request, 'articles/section.html', {"article": article, "comments": comments, "user": user, "similar_articles": similar_articles})


def add_comment(request, article_id):

    article = Article.objects.get(id=article_id)

    article.comment_set.create(comment_text=request.POST['comment'],
                               comment_name=request.POST['name'],
                               comment_email=request.POST['email'],)

    return HttpResponseRedirect(reverse('articles:section', args=(article.id,)))
