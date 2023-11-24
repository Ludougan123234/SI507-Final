import requests
from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader
from django.views.decorators.csrf import ensure_csrf_cookie
from .forms import DrugForm
from .graph import Graph
import json 
import os

@ensure_csrf_cookie
def index(request):
    greeting_list = ["hello", "bye"]

    # get user option
    if request.method == "POST":
        form = DrugForm(request.POST)
        if form.is_valid():
            # Process form data
            print("form is valid")
            drug = form.cleaned_data['drug']
            sex = form.cleaned_data['sex']
            age_onset = form.cleaned_data['age_onset']
            hospitalization = form.cleaned_data['hospitalization']
            report_date = form.cleaned_data['report_date']
            reporting_country = form.cleaned_data['reporting_country']
            reaction_type = form.cleaned_data['reaction_type']

            print(drug, age_onset)
            # use functions 
            cui_name_pair = getRxNorm(drug)

    else: 
        form = DrugForm()

    f = open('./my_app/cache.json')

    data = json.load(f)

    cached = []
    for i in data['cache']:
        cached.append(i)

    # print(os.getcwd())

    context = {"greetings": greeting_list, 
               "only_one": greeting_list[1], 
               'form': form,
               'cached': cached}
    
    return render(request, "index.html", context)

def getRxNorm(query_str):
    query_str = [i.strip() for i in query_str.split(',')]
    cui_name = {}
    for q in query_str:
        # TODO: Use cache
        content = requests.get(f'https://rxnav.nlm.nih.gov/REST/drugs.json?name={q}').json()
        for i in content['drugGroup']['conceptGroup']:
            try: 
                for j in i['conceptProperties']:
                    # cui_name.append([j['rxcui'], j['name']])
                    cui_name[j['rxcui']] = j['name']
            except KeyError:
                pass
    return cui_name

def getOpenFda(cui, sex, age_onset, hospitalization, report_date, reporting_country, reaction_type):
    results = {}
    # TODO: parse data
    if sex: 
        results['sex'] = ...
    if age_onset:
        results['age_onset'] = ...
    if hospitalization:
        results['hospitalization'] = ...
    if report_date:
        results['report_date'] = ...
    if reporting_country:
        results['reporting_country'] = ...
    if reaction_type:
        results['reaction_type'] = ...
    return results

def getInteractionData(cui):
    pass
    # NOTE: cui should be list, joined by "+"
    # NOTE: should only search for list


def buildGraph(interaction):
    pass
    ...



# references:
# 1. https://realpython.com/django-hosting-on-heroku/#step-7-deploy-your-django-project-to-heroku
# 2. https://docs.djangoproject.com/en/4.2/intro/tutorial01/
