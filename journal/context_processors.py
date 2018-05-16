from journal.models import Category, Video, News, Comment, Journalist
from journal.forms import NewsletterForm
import requests


def global_var(request):
    # Meteo
    url = 'http://api.openweathermap.org/data/2.5/weather?q=Rabat&units=metric&appid=91d3852842a30e80531df63b131af6d4'
    r = requests.get(url).json()
    weather = {
        'city': 'Casablanca',
        'temperature': r['main']['temp'],
        'description': r['weather'][0]['description'],
        'icon': r['weather'][0]['icon'],
    }

    # TOP_READ
    video_id = Video.objects.filter(active=True).values_list('id', flat=True)
    top_read = News.objects.filter(active=True).exclude(id__in=video_id).order_by('-view_number', 'id')[:7]

    # TOP COMMENTS
    top_comment = Comment.objects.all().order_by('-number_like', '-date_publication')[:4]

    # IS JOURNALIST
    check = False

    if request.user.is_authenticated:
        user = request.user
        if user.email in Journalist.email_list():
            check = True

    context = {
        'categories': Category.objects.all().order_by('name'),
        'weather': weather,
        'topRead': top_read,
        'topComment': top_comment,
        'newsletterForm': NewsletterForm(),
        'is_journalist': check
    }

    return context
