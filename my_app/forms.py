from django import forms

class DrugForm(forms.Form):
    drug = forms.CharField(label='Please enter a series of drug names', initial='Tylenol, Zocor, Diflucan')
    sex = forms.BooleanField(label='Patient sex', required=False, initial=True)
    age_onset = forms.BooleanField(label='Age of onset', required=False)
    hospitalization = forms.BooleanField(label='Hospitalization', required=False)
    report_date = forms.BooleanField(label='Report date', required=False)
    reporting_country = forms.BooleanField(label='Reporting country', required=False)
    reaction_type = forms.BooleanField(label='Reaction type', required=False)
