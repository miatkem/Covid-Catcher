# pylint: disable=C0103, C0413, E1101, W0611
"""Covid Catcher Backend"""
import os
from os.path import join, dirname
import json
import requests
import flask
from flask import request
import flask_sqlalchemy
import flask_socketio
from dotenv import load_dotenv
from covid import get_covid_stats_by_state
from covid import get_covid_stats_by_county
from covid import get_covid_stats_for_all_states
from faq import get_all_questions
from faq import get_all_categories
from faq import FAQ
import news
from news import get_news
import location
from location import get_location
import sites
from sites import get_sites
from sites import search_user
from sites import TestingSites

app = flask.Flask(__name__)
socketio = flask_socketio.SocketIO(app)
socketio.init_app(app, cors_allowed_origins="*")
dotenv_path = join(dirname(__file__), "sql.env")
load_dotenv(dotenv_path)
dotenv_path = join(dirname(__file__), "api-keys.env")
load_dotenv(dotenv_path)
database_uri = os.environ["DATABASE_URL"]
api_k = os.environ["MAP_API_KEY"]
app.config["SQLALCHEMY_DATABASE_URI"] = database_uri
login = 0

db = flask_sqlalchemy.SQLAlchemy(app)
db.init_app(app)
db.app = app
USERS_UPDATED_CHANNEL = "users updated"
STATISTICS = "stats"
NEWUSER = "new user"
FAQS = "faq lists"
ARTICLE = "article list"
SITE = "site page"
SEARCH = "searching"
import models


def emit_all_users(channel):
    """emits all users"""
    all_users = [user.name for user in db.session.query(models.User1).all()]
    socketio.emit(channel, {"allUsers": all_users})
    return channel


def push_stat_data(state):
    """Calls Covid API"""
    information = get_covid_stats_by_state(state)
    print(state)
    case = information.cases
    newCases = information.todaysCases
    death = information.deaths
    newDeaths = information.todayDeaths
    rec = information.recovered
    county_list = []
    county_confirmed = []
    county_deaths = []
    county_rec = []
    updated = []

    print("CASES DEATHS AND RECOVERED: ", case, death, rec)
    allcounty = get_covid_stats_by_county(state, "")
    for x in allcounty:
        county_list.append(x.county)
        county_confirmed.append(x.confirmed)
        county_deaths.append(x.deaths)
        county_rec.append(x.recovered)
        updated.append(x.updatedAt)

    socketio.emit(
        STATISTICS,
        {
            "state": state,
            "cases": case,
            "new_cases": newCases,
            "deaths": death,
            "new_deaths": newDeaths,
            "recovered": rec,
            "countyNames": county_list,
            "countyCases": county_confirmed,
            "countyDeaths": county_deaths,
            "countyRecovered": county_rec,
            "updated": updated,
        },
        room=request.sid,
    )
    r = "stats are pushed"
    return r


@socketio.on("new google user")
def on_new_google_user(data):
    """new user when log in"""
    print("Got an event for new google user input with data:", data)
    push_new_user_to_db(data["name"], data["email"], data["pic"], data["room"])
    emit_all_users(USERS_UPDATED_CHANNEL)
    return USERS_UPDATED_CHANNEL


@socketio.on("email results")
def on_send_results(data):
    #This name would be the user but mailgun will not allow emails to be sent to
    #    unverified users without paying.
    name="Madison"
    msg = "Hello "+name+"! After taking your questionnaire us here at Covid Catcher recommended the following...\n"
    msg +=  data['results']
    print(msg)
    print(requests.post(
	    "https://api.mailgun.net/v3/sandbox65fda9f953cb42baacd1bdd34356b8c4.mailgun.org/messages",
		auth=("api", os.environ["MAIL_API_KEY"]),
		data={"from": "Excited User <mailgun@sandbox65fda9f953cb42baacd1bdd34356b8c4.mailgun.org>",
		    #This only sends to madison becuase mailgun for free can only send to verified emails
		    #To send to the specific users email simply pull the email from the database at this socket
		    #   number and send it there
			"to": ["miatkem@gmail.com"],
			"subject": "Covid Catcher Questionnaire Results",
			"text":msg}).text)


@socketio.on("faq categories")
def on_faq_categories():
    """get all categories for faqs"""
    categories = get_all_categories()
    socketio.emit("faq category list", categories)


@socketio.on("faq questions")
def on_faq_questions(category):
    """get questions and answers in a category"""
    if category == "" or category == None:
        faqs = get_all_questions()
    else:
        faqs = get_all_questions(category)
    response = []
    for faq in faqs:
        response.append(
            {
                "question": faq.question,
                "answer": faq.answer,
            }
        )
    socketio.emit("faq list", response)


def push_new_user_to_db(name, email, picture, room):
    """puts new user in the database"""
    global login
    all_users = [user.email for user in db.session.query(models.User1).all()]
    if email in all_users:
        print(email, " is already a user in the database!")
    else:
        db.session.add(models.User1(name, email, picture, room))
        db.session.commit()
    login = 1
    userLog()
    emit_all_users(USERS_UPDATED_CHANNEL)
    return name


def get_state_colors():
    """Colors for USA map"""
    state_colors = []
    state_cases = []
    state_active = []
    for i in get_covid_stats_for_all_states():
        state_colors.append(i.color)
        state_cases.append(i.cases)
        state_active.append(i.activeCases)
    socketio.emit(
        "colors", {"colors": state_colors, "cases": state_cases, "active": state_active}
    )


def userLog():
    """User Login Check"""
    if login == 1:
        socketio.emit(NEWUSER, {"login": 1})
    return True


@socketio.on("search loc")
def search_loc(data):
    """Search for location covid stats"""
    state = data["loc"]
    push_stat_data(state)


@socketio.on("connect")
def on_connect():
    """Socket for when user connects"""
    articleList()
    #test_location()
    get_state_colors()
    ip = request.environ["HTTP_X_FORWARDED_FOR"]
    loc = get_location(ip)
    push_stat_data(loc.state)
    return True


@socketio.on("search location")
def searching(data):
    """Search location"""
    a = data["area"]
    areaLoc = search_user(a)
    allsites = get_sites(areaLoc[0], areaLoc[1])
    title_list = []
    address_list = []
    lat_list = []
    lng_list = []
    phone_list = []
    web_list = []
    miles_list = []
    counter = 0
    for site in allsites:
        if counter != 3:
            title_list.append(site.title)
            address_list.append(site.entireAddress)
            lat_list.append(site.latitude)
            lng_list.append(site.longitude)
            phone_list.append(site.phone)
            web_list.append(site.web)
            miles_list.append(site.miles)
            counter += 1
        else:
            break

    socketio.emit(
        SITE,
        {
            "user_lat": areaLoc[0],
            "user_lng": areaLoc[1],
            "title": title_list,
            "address": address_list,
            "latitude": lat_list,
            "longitude": lng_list,
            "phone": phone_list,
            "web": web_list,
            "miles": miles_list,
            "key": api_k,
        }, room=request.sid
    )
    return True

'''
def test_location():
    """Get testing locations"""
    ip = request.environ["HTTP_X_FORWARDED_FOR"]
    loc = get_location(ip)
    lat = loc.latitude
    lng = loc.longitude
    allsites = get_sites(lat, lng)
    title_list = []
    address_list = []
    lat_list = []
    lng_list = []
    phone_list = []
    web_list = []
    miles_list = []
    counter = 0
    for site in allsites:
        if counter != 3:
            title_list.append(site.title)
            address_list.append(site.entireAddress)
            lat_list.append(site.latitude)
            lng_list.append(site.longitude)
            phone_list.append(site.phone)
            web_list.append(site.web)
            miles_list.append(site.miles)
            counter += 1
        else:
            break

    socketio.emit(
        SITE,
        {
            "user_lat": lat,
            "user_lng": lng,
            "title": title_list,
            "address": address_list,
            "latitude": lat_list,
            "longitude": lng_list,
            "phone": phone_list,
            "web": web_list,
            "miles": miles_list,
            "key": api_k,
        },
    )
    return True'''


def articleList():
    """Calls the Article API"""
    articles = get_news(
        5, since=news.YESTERDAY.strftime("%yyyy-%mm-%dd"), query="covid"
    )
    title_list = []
    desc_list = []
    url_list = []
    image_list = []
    source_list = []
    for art in articles:
        image_list.append(art.image)
        title_list.append(art.title)
        source_list.append(art.source)
        desc_list.append(art.description)
        url_list.append(art.url)
    socketio.emit(
        ARTICLE,
        {
            "title": title_list,
            "desc": desc_list,
            "url": url_list,
            "img": image_list,
            "sources": source_list,
        },
    )
    return True


@app.route("/")
def index():
    """loads page"""
    models.db.create_all()
    db.session.commit()
    return flask.render_template("index.html")


@app.errorhandler(404)
def page_not_found(e):
    """Handles Page Not Found"""
    return flask.render_template("index.html")


if __name__ == "__main__":
    socketio.run(
        app,
        host=os.getenv("IP", "0.0.0.0"),
        port=int(os.getenv("PORT", 8080)),
        debug=True,
    )
