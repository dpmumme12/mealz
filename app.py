from flask import Flask, render_template, redirect, session, request, flash, url_for
import psycopg2
import os
from functions import login_required, recipe, lookup, instructions, meal
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.secret_key = b"\x07\xb0p\xb0\x1e\x8dB\x7f\xd0\x86\xbf'\xac\xf1\x1e\x1d@~\x9d\xef9\xbd\xf9\xa8"

#@app.after_request
#def after_request(response):
    #response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    #response.headers["Expires"] = 0
    #response.headers["Pragma"] = "no-cache"
    #return response

#DATABASE_URL = os.environ['DATABASE_URL']

#conn = psycopg2.connect(DATABASE_URL, sslmode='require')

conn = psycopg2.connect(
    host = 'localhost',
    database = 'mealz',
    user = 'postgres',
    password = 'Lsurules12!')

c = conn.cursor()

@app.route("/", methods=["GET", "POST"])
@login_required
def home():
    if (request.method == "POST"):
        # selecting the meal info from the database #
        c.execute("SELECT * FROM meals WHERE user_id = %(user)s AND meal = %(meal)s", {"user": session["user_id"], "meal": request.form.get("food")})
        meal_query = c.fetchone()

        # setting the database info into a dict to transer the data to another route#
        query = {
            "id": meal_query[2],
            "title": meal_query[3],
            "image": meal_query[4]
        }

        session["dict"] = query

        return redirect(f"/recipes/{query['id']}")

    else:
        meals = meal()

        if (session["user_id"] == 1):
            flash("You are logged in as a guest. All meals added to the schedule will be deleted after logout. Enjoy!")
            return render_template("home.html", alert = "primary", meals = meals)

        return render_template("home.html", meals = meals)


@app.route("/register", methods=["GET", "POST"])
def register():
    if (request.method == "POST"):
        
        # making sure the input fields are valid #
        if not (request.form.get("username")):
            flash("Must provide username.")
            return render_template("register.html", alert = "error")

        elif not (request.form.get("password")):
            flash("Must provide password.")
            return render_template("register.html", alert = "error")

        elif not (request.form.get("confirm password") == request.form.get("password")):
            flash("Passwords must match.")
            return render_template("register.html", alert = "error")

        # hashing the password to securely store it in the database #
        password_hash = generate_password_hash(request.form.get("password"))
        username = request.form.get("username")

        c.execute("SELECT * FROM users WHERE username = %(user)s", {"user": username})
        rows = c.fetchall()

        # checking if username is taken #
        if (len(rows) == 0):
            c.execute("INSERT INTO users(username, password) VALUES(%s, %s)", (request.form.get("username"), password_hash))
        else:
            flash("Username taken.")
            return render_template("register.html", alert = "error")

        conn.commit()

        c.execute("SELECT id FROM users WHERE username = %(user)s AND password = %(password)s", {"user": username, "password": password_hash})
        new_id = c.fetchone()
        new_id = new_id[0]

        # setting the user id to the session #
        session["user_id"] = new_id

        flash("Registered!")

        return redirect("/")

    else:
        return render_template("register.html")


@app.route("/logout")
def logout():
    # clearing the session #
    session.clear()

    return redirect("/")

@app.route("/login", methods = ["GET", "POST"])
def login():
    # making sure no one else is logged in #
    session.clear()

    if (request.method == "POST"):
        # making sure the inputs were valid #
        if not request.form.get("username"):
            flash("Must provide username.")
            return render_template("login.html", alert = "error")
        
        if not request.form.get("password"):
            flash("Must provide password.")
            return render_template("login.html", alert = "error")
        
        c.execute("SELECT * FROM users WHERE username = %(user)s", {"user": request.form.get("username")})

        query = c.fetchone()
        
        if (query == None or not check_password_hash(query[2], request.form.get("password"))):
            flash("Invalid username and/or password.")
            return render_template("login.html", alert = "error")

        session["user_id"] = query[0]

        return redirect("/")
    else:
        return render_template("login.html")

@app.route("/meals", methods = ["GET", "POST"])
def meals():

    if (request.method == "POST"):
        # making sure the input fields from the search bar a valid #
        if not request.form.get("cuisine"):
            flash("Must provide cuisine.")
            return render_template("meals.html", alert = "error")
        
        if not request.form.get("type"):
            flash("Must provide meal type.")
            return render_template("meals.html", alert = "error")
    
        cuisine = request.form.get("cuisine")
        meal_type = request.form.get("type")

        query = lookup(cuisine, meal_type)

        # transferring the query data to recipes route #
        session["dict"] = query
       
       
        return render_template("meals.html", search_query = 1, query = query)


    else:
        return render_template("meals.html")

@app.route('/recipes/<int:id>', methods=['GET','POST'])
def recipes(id):
    # recieving the data from othe routes #
    query = session["dict"]

    if (request.method == "POST"):
        day = request.form.get("day")
        meal = request.form.get("meal")
        meal = day + "-" + meal

        # checking what route the query data came from #
        if (len(query) > 3):
            # parsing out all unnecessary data from meals route in dict #
            for i in range(len(query)):
                if (query[i]["id"] == id):
                    query = query[i]
                    break
            else:
                pass

        c.execute("SELECT * FROM meals WHERE user_id = %(user)s AND meal = %(meal)s", {"user": session["user_id"], "meal": meal})
        rows = c.fetchall()

        # checking if user already has meal in that timeslot in database #
        if (len(rows) == 0):
            c.execute("INSERT INTO meals VALUES(%s, %s, %s, %s, %s)", (session["user_id"], meal, query["id"], query["title"], query["image"]))
        
        else:
            c.execute("UPDATE meals SET meal_id = %(id)s, meal_name = %(title)s, meal_img = %(image)s WHERE user_id = %(user)s AND meal = %(meal)s",
             {"id": query["id"], "title": query["title"], "image": query["image"], "user": session["user_id"], "meal": meal})

        conn.commit()

        return redirect("/")
        
    else:
        # checking what route the query data came from #
        if (len(query) > 3):
            # parsing out all unnecessary data from meals route in dict #
            for i in range(len(query)):
                if (query[i]["id"] == id):
                    query = query[i]
                    break
        else:
            pass

        ingredients = recipe(id)
        instruction = instructions(id)
        ing_len = len(ingredients)
        ins_len = len(instruction)

        # rounding the values so the table doesn't display didgits pass the hundredth place #
        for i in range(ing_len):
            ingredients[i]["value"] = round(ingredients[i]["value"], 2)


        return render_template("recipes.html", query = query, ingredients = ingredients, instruction = instruction, ing_len = ing_len,
                                ins_len = ins_len, search_query = 1, id = id)

@app.route("/clear_table")
def clear_table():
    # deleting all meal information for the user in the database #
    c.execute("DELETE FROM meals WHERE user_id = %(user)s", {"user": session["user_id"]})

    conn.commit()

    return redirect("/")

@app.route("/guest_login")
def guest_login():
    session.clear()

    c.execute("DELETE FROM meals WHERE user_id = %(user)s", {"user": 1})

    conn.commit()

    session["user_id"] = 1

    return redirect("/")
