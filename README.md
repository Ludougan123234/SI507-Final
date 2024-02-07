# SI507-Final

This repository contains code files for SI 507 final project (UMich School of Information).\
This project aims to:
1. Experiment with representing drug-drug interaction as graphs
2. Experiment with the Django web framework, and how it can be used in combination with plotly and dash visualization frameworks to offer interactive drug-drug interaction and drug information visualization. 
3. Experiment with CI & CD using GitHub Actions. Each commit from the local machine triggers a build on GitHub, which triggers a deployment workflow on Heroku, saving time for manual deployment. 

Project report can be found here: [Google docs](https://docs.google.com/document/d/1IB7vYoPBKedIA_RoMFylsc4cCSRefzhItVSUIK1HF5c/edit?usp=sharing)

⚠️⚠️⚠️⚠️ \
This project is originally deployed as a [Heroku web app](https://mjpan-fp507-2d393f67a958.herokuapp.com/index) for interactivity. However, due to platform cost concerns and the deprecation of the [NIH drug-drug interaction API](https://blog.drugbank.com/nih-discontinues-their-drug-interaction-api/), this application is taken offline and is no longer available.
If you wish to see the app in action, please refer to the [one-minute demo video](https://drive.google.com/file/d/1OWcb8oovu2z5seZLCm__oaMao2jOr3b7/view?usp=sharing).\
⚠️⚠️⚠️⚠️

## How to run the code

To run the code, first install the dependencies by running the following command in the terminal:

```bash
pip install -r requirements.txt
```

The `requirements.txt` file contains all the required packages for this project.

Then, run the following command to start the server:

```bash
python manage.py runserver
```

This command starts a server at localhost (usually with port 8000). The web application can be accessed by going to the url: `localhost:[PORT]/index`. (the port number should be the same as the one shown in the terminal on line `Starting development server at http://127.0.0.1:[PORT]`)

The Django secret key as well as the FDA API secret key is provided in the .env file in the zip file submitted to canvas. Make sure that you are in the directory of the project when running the above commands with the virtual environment with django installation activated.

## Repository file structure

| File  | is directory?  | description |
|:-----:  |:-----:  |:-----:  |
| `.github/workflow` | ✅ | Workflow file for github action (for automatic deployment to heroku) |
|`mjpan507`  | ✅ |  Django configuration |
| `my_app` | ✅ | Project code (contains: application view, logic, and graph) <br><strong style="color:red"> If you are grading this assignment, please look at this directory </strong> |
| `.gitignore` | ❌ |  Git ignore file |
| `README.md` | ❌ | Readme file |
| `manage.py`|❌ | Django configuration file |
| `requirements.txt` | ❌| Required python package |
| `runtime.txt` | ❌| Heroku version python configuration |
| `graph.json` | ❌ | The json representation of graph data structure used in this project |


## How to interact with the web application

[1-minute demo](https://drive.google.com/file/d/1OWcb8oovu2z5seZLCm__oaMao2jOr3b7/view?usp=sharing)

## Reflection and further improvements
1. Better user interface design for the visualizations
2. Use Postgre SQL to implement caching of data to ensure file and data persistence on cloud platforms with ephemeral file systems.
