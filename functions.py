from functools import wraps
from flask import session, flash, redirect
import requests
from urllib import parse
import psycopg2
import os

api_key = "00c5a28809834ec8b204ee9a03fc64c0"

#DATABASE_URL = os.environ['DATABASE_URL']

#conn = psycopg2.connect(DATABASE_URL, sslmode='require')

conn = psycopg2.connect(
    host = 'localhost',
    database = 'mealz',
    user = 'postgres',
    password = 'Lsurules12!')

c = conn.cursor()

# makes sure the user is logged in #
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

# using the api to return a list of dicts with the ingredient info the user needs #
def recipe(id):
    base_url = f"https://api.spoonacular.com/recipes/{id}/ingredientWidget.json?"
    url = base_url  + parse.urlencode({"apiKey": api_key})
    query = requests.get(url).json()
    ingredients = []
    for ingredient in range(len(query["ingredients"])):
        info = {
            "name": (query['ingredients'][ingredient]['name']),
            "value": (query['ingredients'][ingredient]['amount']['us']['value']),
            "unit": (query['ingredients'][ingredient]['amount']['us']['unit'])
        }
        ingredients.append(info)
    return ingredients

# using the api to return a list of dicts with the meal info the user needs #
def lookup(cuisine, meal_type):
    base_url = "https://api.spoonacular.com/recipes/complexSearch?"
    url = base_url  + parse.urlencode({"apiKey": api_key, "cuisine": cuisine, "type": meal_type, "number": '33'})
    query = requests.get(url).json()
    results = []
    try:
        for meal in range(len(query['results'])):
            info = {
                "id": (query['results'][meal]['id']),
                "title": (query['results'][meal]['title']),
                "image": (query['results'][meal]['image'])
            }
            results.append(info)
    except:
        info ={
            "id": ('Not found'),
            "title": ('Not found'),
            "image": ('Not found')
        }
        results.append(info)
    return results

# using the api to return a list of dicts with the cooking instructions info the user needs #
def instructions(id):
    base_url = f"https://api.spoonacular.com/recipes/{id}/analyzedInstructions?"
    url = base_url  + parse.urlencode({"apiKey": api_key})
    query = requests.get(url).json()
    instructions = []
    try:
        for steps in range(len(query[0]['steps'])):
            info = query[0]['steps'][steps]['step']
            instructions.append(info)
    except:
        info = "No instructions for this meal"
        instructions.append(info)
    return instructions

# getting all of the users meal schedule info from data base and returning it in a accessible dictionary #
def meal():
    c.execute("SELECT * FROM meals WHERE user_id = %(user)s", {"user": session["user_id"]})
    query = c.fetchall()
    meals = {}
    for row in query:
        info = {row[1]: {"name": row[3], "image": row[4]}}
        meals.update(info)
    return meals