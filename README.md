# SI507-Final

This repository contains code files for SI 507 final project.

This project aims to represent drug-drug interaction as graphs.

The web application can be accessed here: [Heroku web app](https://mjpan-fp507-2d393f67a958.herokuapp.com/index)

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

The file structure of the repository is listed below:
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
| `try.ipynb` | ❌| Contains code snippets for experimentation with graph data strucutre and API access  |


## How to interact with the web application

See demo video