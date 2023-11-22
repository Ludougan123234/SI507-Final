from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader

def index(request):
    # template = loader.get_template("html/landing.html")
    greeting_list = [
        'hello',
        'uwu',
        'bye'
    ]
    context = {"greetings": greeting_list,
               'only_one': greeting_list[1]}
    return render(request, 'index.html', context) 


# references: 
# 1. https://realpython.com/django-hosting-on-heroku/#step-7-deploy-your-django-project-to-heroku
# 2. https://docs.djangoproject.com/en/4.2/intro/tutorial01/
