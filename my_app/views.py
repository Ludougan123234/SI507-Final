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

            context = {"greetings": greeting_list, 
               "only_one": greeting_list[1], 
               'form': form,
               'cached': cui_name_pair}

            return render(request, "index.html", context)

    else: 
        form = DrugForm()

    context = {"greetings": greeting_list, 
               "only_one": greeting_list[1], 
               'form': form}
    
    return render(request, "index.html", context)

def getRxNorm(query_str):
    query_str = [i.strip().lower() for i in query_str.split(',')]
    cui_name = {}  # dictionary to store cui to drug_name mapping
    with open("./my_app/cache.json", 'r') as json_file:
        cache = json.load(json_file)
    
    for q in query_str:
        if q in cache.keys(): 
            print("data found in cache")
            cui_name.update(cache[q])  # update cui_name with cached data
        else: 
            print("Fetching new data")
            response = requests.get(f'https://rxnav.nlm.nih.gov/REST/drugs.json?name={q}').json()
            new_data = {}  # temporary dictionary to store new API data
            try:
                for i in response['drugGroup']['conceptGroup']:
                    if 'conceptProperties' in i:
                        for j in i['conceptProperties']:
                            new_data[j['rxcui']] = j['name']
                cache[q] = new_data  # update cache with new data for q
                cui_name.update(new_data)  # update cui_name with new API data
            except KeyError:
                pass

    # Update the cache file only once after processing all queries
    with open("./my_app/cache.json", "w") as f:
        json.dump(cache, f)

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
