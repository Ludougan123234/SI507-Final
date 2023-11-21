from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader

def hello(request):
    # template = loader.get_template("html/landing.html")
    context = {"greetings": "hi there!"}
    return render(request, 'html/landing.html', context)