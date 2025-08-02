from flask import Flask, render_template, request
import requests
from datetime import datetime, timedelta
import os
import os

API_KEY = os.environ.get("API_KEY")


app = Flask(__name__)

def get_team_id(team_name):
    url = "https://api-football-v1.p.rapidapi.com/v3/teams"
    querystring = {"search": team_name}
    headers = {
        "X-RapidAPI-Key": API_KEY,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers, params=querystring)
    data = response.json()
    if data.get('results', 0) == 0:
        return None
    return data['response'][0]['team']['id']

def get_next_match(team_id):
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    querystring = {"team": str(team_id), "next": "1"}
    headers = {
        "X-RapidAPI-Key": API_KEY,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers, params=querystring)
    data = response.json()
    if data['results'] == 0:
        return None

    match = data['response'][0]
    utc_str = match['fixture']['date']
    utc_time = datetime.strptime(utc_str, "%Y-%m-%dT%H:%M:%S+00:00")
    kst_time = utc_time + timedelta(hours=9)

    return {
        "date": kst_time.strftime("%Y-%m-%d"),
        "time": kst_time.strftime("%H:%M"),
        "venue": match['fixture']['venue']['name'],
        "city": match['fixture']['venue']['city'],
        "league": match['league']['name'],
        "round": match['league']['round'],
        "home": match['teams']['home']['name'],
        "away": match['teams']['away']['name'],
        "home_logo": match['teams']['home']['logo'],
        "away_logo": match['teams']['away']['logo'],
        "home_id": match['teams']['home']['id'],
        "away_id": match['teams']['away']['id'],
        "league_id": match['league']['id'],
        "season": match['league']['season']
    }

def get_last_matches(team_id):
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    querystring = {"team": str(team_id), "last": "5"}
    headers = {
        "X-RapidAPI-Key": API_KEY,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers, params=querystring)
    data = response.json()
    results = []

    for match in data['response']:
        home_id = match['teams']['home']['id']
        home_score = match['goals']['home']
        away_score = match['goals']['away']
        is_home = (team_id == home_id)

        if home_score is None or away_score is None:
            results.append("❓")
            continue

        if home_score == away_score:
            results.append("➖")
        elif (is_home and home_score > away_score) or (not is_home and away_score > home_score):
            results.append("✅")
        else:
            results.append("❌")

    return results

def get_top_players(league_id, season, team_id):
    url = "https://api-football-v1.p.rapidapi.com/v3/players/topscorers"
    querystring = {"league": str(league_id), "season": str(season)}
    headers = {
        "X-RapidAPI-Key": API_KEY,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers, params=querystring)
    data = response.json()

    top_scorer = None
    top_assister = None
    max_goals = 0
    max_assists = 0

    for player in data['response']:
        if player['statistics'][0]['team']['id'] != team_id:
            continue

        stats = player['statistics'][0]
        goals = stats['goals']['total'] or 0
        assists = stats['goals']['assists'] or 0

        if goals > max_goals:
            max_goals = goals
            top_scorer = {
                "name": player['player']['name'],
                "goals": goals
            }
        if assists > max_assists:
            max_assists = assists
            top_assister = {
                "name": player['player']['name'],
                "assists": assists
            }

    return top_scorer, top_assister

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        team_name = request.form["team_name"]
        team_id = get_team_id(team_name)

        if team_id:
            match = get_next_match(team_id)
            if match:
                home_last = get_last_matches(match['home_id'])
                away_last = get_last_matches(match['away_id'])
                top_scorer, top_assister = get_top_players(match['league_id'], match['season'], team_id)

                return render_template("result.html",
                                       match=match,
                                       team_name=team_name,
                                       home_last=home_last,
                                       away_last=away_last,
                                       top_scorer=top_scorer,
                                       top_assister=top_assister)

        return render_template("index.html", error="❌ Team information not found.")

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)

'''
git add .
git commit -m "return"
git push
'''