from flask import Flask, render_template, request
from nba_api.stats.endpoints import leaguedashteamstats
import pandas as pd
import random

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def home():

    tables = {}
    simulation = None
    # Default season
    default_season = "2024-25"

    stats = leaguedashteamstats.LeagueDashTeamStats(
        season=default_season,
        measure_type_detailed_defense='Advanced'
    )

    default_df = stats.get_data_frames()[0]

    nba_teams = sorted(
        default_df['TEAM_NAME'].unique().tolist()
    )

    if request.method == "POST":

        season_input = request.form["season"]
        selected_option = request.form["mode"]

        # =========================
        # CONVERT SINGLE YEAR
        # =========================

        if len(season_input) == 4 and season_input.isdigit():

            start_year = int(season_input)
            end_year = str(start_year + 1)[-2:]

            season_input = f"{start_year}-{end_year}"

        # =========================
        # VALIDATE SEASON
        # =========================

        valid_seasons = []

        for year in range(2000, 2026):

            next_year = str(year + 1)[-2:]
            valid_seasons.append(f"{year}-{next_year}")

        if season_input not in valid_seasons:

            return render_template(
                "index.html",
                error="Invalid season format."
            )

        # =========================
        # LOAD DATA
        # =========================

        stats = leaguedashteamstats.LeagueDashTeamStats(
            season=season_input,
            measure_type_detailed_defense='Advanced'
        )

        df = stats.get_data_frames()[0]

        nba_teams = sorted(
            df['TEAM_NAME'].unique().tolist()
        )

        # =========================
        # ANALYTICS TABLES
        # =========================

        if selected_option == "Analytics Tables":

            df['OFF_EXPECTATION_DIFF'] = (
                df['OFF_RATING'] - df['E_OFF_RATING']
            ).round(2)

            df['DEF_EXPECTATION_DIFF'] = (
                df['DEF_RATING'] - df['E_DEF_RATING']
            ).round(2)

            df['EXPECTED_WINS'] = (
                41 + (df['E_NET_RATING'] * 2.7)
            ).round(1)

            df['WIN_DIFFERENCE'] = (
                df['W'] - df['EXPECTED_WINS']
            ).round(1)

            tables["Offensive Rating"] = df[
                ['TEAM_NAME', 'OFF_RATING', 'OFF_RATING_RANK']
            ].sort_values(
                by='OFF_RATING',
                ascending=False
            ).to_html(
                classes="table table-dark table-striped",
                index=False
            )

            tables["Defensive Rating"] = df[
                ['TEAM_NAME', 'DEF_RATING', 'DEF_RATING_RANK']
            ].sort_values(
                by='DEF_RATING'
            ).to_html(
                classes="table table-dark table-striped",
                index=False
            )

            tables["Net Rating"] = df[
                ['TEAM_NAME', 'NET_RATING']
            ].sort_values(
                by='NET_RATING',
                ascending=False
            ).to_html(
                classes="table table-dark table-striped",
                index=False
            )

            tables["Expected Offensive Rating"] = df[
                ['TEAM_NAME', 'E_OFF_RATING']
            ].sort_values(
                by='E_OFF_RATING',
                ascending=False
            ).to_html(
                classes="table table-dark table-striped",
                index=False
            )

            tables["Offense vs Expected"] = df[
                [
                    'TEAM_NAME',
                    'OFF_RATING',
                    'E_OFF_RATING',
                    'OFF_EXPECTATION_DIFF'
                ]
            ].sort_values(
                by='OFF_EXPECTATION_DIFF',
                ascending=False
            ).to_html(
                classes="table table-dark table-striped",
                index=False
            )

            tables["Expected Defensive Rating"] = df[
                ['TEAM_NAME', 'E_DEF_RATING']
            ].sort_values(
                by='E_DEF_RATING'
            ).to_html(
                classes="table table-dark table-striped",
                index=False
            )

            tables["Defense vs Expected"] = df[
                [
                    'TEAM_NAME',
                    'DEF_RATING',
                    'E_DEF_RATING',
                    'DEF_EXPECTATION_DIFF'
                ]
            ].sort_values(
                by='DEF_EXPECTATION_DIFF',
                ascending=False
            ).to_html(
                classes="table table-dark table-striped",
                index=False
            )

            tables["Expected Wins"] = df[
                [
                    'TEAM_NAME',
                    'W',
                    'EXPECTED_WINS',
                    'WIN_DIFFERENCE'
                ]
            ].sort_values(
                by='WIN_DIFFERENCE',
                ascending=False
            ).to_html(
                classes="table table-dark table-striped",
                index=False
            )

        # =========================
        # GAME SIMULATION
        # =========================

        elif selected_option == "Game Simulation":

            team1_name = request.form["team1"]
            team2_name = request.form["team2"]

            team1 = df[df['TEAM_NAME'] == team1_name]
            team2 = df[df['TEAM_NAME'] == team2_name]

            team1_score = (
                (
                    team1['E_OFF_RATING'].values[0] +
                    team2['E_DEF_RATING'].values[0]
                ) / 2
            )

            team2_score = (
                (
                    team2['E_OFF_RATING'].values[0] +
                    team1['E_DEF_RATING'].values[0]
                ) / 2
            )

            team1_wins = 0
            team2_wins = 0
            overtime_games = 0

            for i in range(100):

                team1_final = round(
                    team1_score + random.randint(-10, 10)
                )

                team2_final = round(
                    team2_score + random.randint(-10, 10)
                )

                if team1_final > team2_final:
                    team1_wins += 1

                elif team2_final > team1_final:
                    team2_wins += 1

                else:
                    overtime_games += 1

            simulation = {
                "team1": team1_name,
                "team2": team2_name,
                "team1_wins": team1_wins,
                "team2_wins": team2_wins,
                "overtime_games": overtime_games
            }

    return render_template(
        "index.html",
        tables=tables,
        simulation=simulation,
        nba_teams=nba_teams
    )

if __name__ == "__main__":
    app.run(debug=True)