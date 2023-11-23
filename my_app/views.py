from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader
from django.views.decorators.csrf import ensure_csrf_cookie
from .forms import DrugForm
import requests


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

            # use functions 

            print(drug)
    else: 
        form = DrugForm()



    context = {"greetings": greeting_list, 
               "only_one": greeting_list[1], 
               'form': form}
    return render(request, "index.html", context)

def getRxNorm(query_str):
    content = requests.get(f'https://rxnav.nlm.nih.gov/REST/drugs.json?name={query_str}').json()
    cui_name = []
    for i in content['drugGroup']['conceptGroup']:
        try: 
            for j in i['conceptProperties']:
                cui_name.append([j['rxcui'], j['name']])
        except KeyError:
            pass
    return cui_name

# references:
# 1. https://realpython.com/django-hosting-on-heroku/#step-7-deploy-your-django-project-to-heroku
# 2. https://docs.djangoproject.com/en/4.2/intro/tutorial01/
