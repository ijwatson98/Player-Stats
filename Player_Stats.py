#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import pandas as pd
import requests
from bs4 import BeautifulSoup
# import ip_rotator


# In[ ]:


# proxy = ip_rotator.Proxy(https=True)


# In[ ]:


def get_players():

    url = "https://fbref.com/en/comps/Big5/stats/players/Big-5-European-Leagues-Stats"

    # page = proxy.session.get(url)
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')

    players = soup.find_all("td", {"class":"left", "data-stat":"player"})
    positions = soup.find_all("td", {"class":"center", "data-stat":"position"})#
    teams = soup.find_all("td", {"class":"left", "data-stat":"team"})

    players_list = []
    for i in range(len(players)):
        name = players[i].find("a").text
        position = positions[i].text
        team = teams[i].text
        href = players[i].find("a").get("href")
        players_list.append([name, position, team, href])
    df = pd.DataFrame(players_list, columns=["Name", "Position", "Team", "URL"])
    df["Position"] = df["Position"].str.split(",").apply(lambda x: x[0])
    
    df.set_index("Name", inplace=True)
    
    return df


# In[ ]:


# player_database = get_players()


# In[ ]:


# player_database.to_csv("player-database-20jan23.csv")


# In[ ]:


player_database = pd.read_csv("player-database-20jan23.csv", header=0, index_col=0)


# In[ ]:


player_database.loc["Raphinha"]


# In[ ]:


gk_database = player_database[player_database["Position"]=="GK"]


# In[ ]:


df_database = player_database[player_database["Position"]=="DF"]


# In[ ]:


mf_database = player_database[player_database["Position"]=="MF"]


# In[ ]:


fw_database = player_database[player_database["Position"]=="FW"]


# In[ ]:


def player_stats(player_name, player_database=player_database):
    
    # proxy.changeIp()
    
    url_end = player_database.loc[player_name]["URL"]
    
    # Define the URL of the page you want to scrape
    url = "https://fbref.com{}".format(url_end)

    # Send a GET request to the website
    # response = proxy.session.get(url)
    page = requests.get(url)

    # Parse the HTML content of the page
    soup = BeautifulSoup(page.content, 'html.parser')

    import regex as re
    
    # Find the table containing the performance statistics
    table = soup.find('table', {'id': re.compile(r'scout_summary')})

    # Find all the rows in the table
    rows = table.find_all('tr')

    import pandas as pd

    # Extract the data from the rows of the table
    data = []
    index = []
    for row in rows:
        index.append(row.find('th').text)
        data.append([cell.text for cell in row.find_all('td')])

    # Extract the column titles from the table
    column_titles = [cell.text for cell in table.find('thead').find_all('th')]

    # create index dataframe
    index_df = pd.DataFrame(index, columns=[column_titles[0]])

    # Create a dataframe from the extracted data
    data_df = pd.DataFrame(data, columns=column_titles[1:])

    # concatenate index_df and data_df
    stats = pd.concat([index_df, data_df], axis=1)
    stats = stats.drop(stats.index[0]).set_index("Statistic", drop=True)
    stats = stats[stats.astype(bool)].dropna()
    if player_database.loc[player_name]["Position"] != "GK":
        stats["Per 90"]["Pass Completion %"] = stats["Per 90"]["Pass Completion %"].replace("%", "")
    else:
        stats["Per 90"]["Save% (Penalty Kicks)"] = stats["Per 90"]["Save% (Penalty Kicks)"].replace("%", "")
        stats["Per 90"]["Save Percentage"] = stats["Per 90"]["Save Percentage"].replace("%", "")
        stats["Per 90"]["Clean Sheet Percentage"] = stats["Per 90"]["Clean Sheet Percentage"].replace("%", "")
        stats["Per 90"]["Launch %"] = stats["Per 90"]["Launch %"].replace("%", "")
        stats["Per 90"]["Crosses Stopped %"] = stats["Per 90"]["Crosses Stopped %"].replace("%", "")
    stats = stats.astype("float")
    stats = stats.reset_index()
    stats = stats.assign(Name=player_name).set_index(["Name", "Statistic"], drop=True)
    
    return stats


# In[ ]:


stats = player_stats("Tyler Adams")


# In[ ]:


stats


# In[ ]:


def stats_database(player_database):
    
    df = pd.DataFrame()

    for i in player_database.index:
        try:
            df = df.append(player_stats(i))
        except:
            pass

    return df            


# In[ ]:


mf_stats = stats_database(player_database)


# In[ ]:


# all_stats.to_csv("stats-database-20jan23.csv")


# In[ ]:


import plotly.express as px


# In[ ]:


def polar_plots(player_name1, player_name2, tables=False):
    
    import plotly.graph_objects as go

    player1 = player_stats(player_name1)
    player2 = player_stats(player_name2)
    
    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
          r=player1["Percentile"],
          theta=player1.index.get_level_values(1),
          fill='toself',
          name=player1.index.get_level_values(0)[0]
    ))
    fig.add_trace(go.Scatterpolar(
          r=player2["Percentile"],
          theta=player2.index.get_level_values(1),
          fill='toself',
          name=player2.index.get_level_values(0)[0]
    ))

    fig.update_layout(
      polar=dict(
        radialaxis=dict(
          visible=True,
          range=[0, 100]
        )),
      showlegend=True
    )

    fig.show()   
    
    if tables:
        print(player1)
        print(player2)


# In[ ]:


polar_plots("Kalvin Phillips", "Weston McKennie", tables=True)


# In[ ]:


def similar_players(player_name, database):
    
    import numpy as np
    
    player1 = player_stats(player_name)
    
    all_diffs = []
    
    for i in database.index:
        try:
            player2 = player_stats(i)
            sq_diffs = []
            for j in player2.index:
                sq_diffs.append((player1.loc[j]["Percentile"] - player2.loc[j]["Percentile"])**2)
            avg_sq_diffs = sum(sq_diffs)/len(sq_diffs)
            all_diffs.append(avg_sq_diffs)
        except:
            all_diffs.append(np.inf)
            pass
        
    min_idx = all_diffs.index(min(all_diffs))
    
    player_match = database.index[min_idx]
    
    # polar_plots(player_name, player_match, tables=False)
    
    return player_match


# In[ ]:


similar_players("Harry Kane", fw_database)

