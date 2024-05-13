'''
This is a project I wrote to help automatically scrape the schedule website for my hockey team and add the games to my google calendar.
Some assumptions:
1. All of the games are in the PM portion of the day
2. All of the games are in 2024

I used the GCSA library from here: https://github.com/kuzmoyev/google-calendar-simple-api?tab=readme-ov-file
I followed the steps in the "Credentials" section of the "Getting Started" page
One other important thing I did was in the "Credentials" section of the google APIs and services, I needed to add "http://localhost:8080/" as an authorized redirect URI for my project

'''

#star tby importing everything we need
from gcsa.google_calendar import GoogleCalendar
from gcsa.event import Event
from datetime import *
from bs4 import BeautifulSoup
import requests
import re

#Initialize the calendar. For this project, this is the joint calendar I share with my partner. Replace the x's with the google calendar ID you want to add to
calendar = GoogleCalendar('xxxxxxxxxxxx')

#Set up how we get the HTML from the URL
def getHTMLdocument(url): 
    '''
    Inputs the URL for the website I want to scrape.
    Returns the text for beautiful soup to work through
    '''

    # request for HTML document of given url 
    response = requests.get(url) 
     
    # response will be provided in JSON format 
    return response.text 

def addGamesToCalendar(teamName, url_to_scrape):
    '''
    Adds the games to my google calendar.
    Input a string of the teamName (must match exactly to the team name as it is on the website) and the URL of the team's schedule
    Adds to the calendar an event with the correct date/time, opponent, and location of the game
    Length of calendar event is 1 hour currently, might update that later
    '''
    

    #assign our document
    html_document = getHTMLdocument(url_to_scrape) 
  
    # create soup object 
    soup = BeautifulSoup(html_document, 'html.parser') 

    #I thought it would make the most sense to use a dictionary here. The keys are the dates of the games. The values are lists of the opponent and location of the game. 
    date_location_opponent = {}

    #Looking at the HTML for the website, I see that it has a unique ID for each game that aligns with the week, so we can do a for loop through it to get the right info
    #In this case, we have 11 weeks of games. I'll need to update this for future seasons with different week numbers
    for week in range(1,12):
        
        #Set up a try-except here in case we have a week that doesn't have a game
        try:
            idToSearch = "WeekBox_" + str(week)
            div_element = soup.find(id=idToSearch) #find the div that has all the information we'll need for the week
            game_details = soup.find_all('div', class_ = 'GameDetails') #did a find all here in the case where we have a week with multiple game
            for games in game_details:
                
                #initialize an empty list for the location and the opponent
                location_opponent = []
                
                #get the date of the game
                date_of_game = games.find('time', class_='e-date')
                input_date_str = date_of_game.get_text() + ' 2024' #the get_text() here returns a date in mmm dd format
                input_date = datetime.strptime(input_date_str, "%b %d %Y") #convert the string form of the date to a datetime object
                output_date_str = input_date.strftime("%Y, %m, %d, ") #output our date in the correct string format. Might be a bit circular to code it this way but it works the way I want it to

                #get the time of the game
                time_of_game = games.find('time', class_='e-time local-info')
                time_of_game_str = time_of_game.get_text().strip().split(' PM')[0] #get only the start time of the game. Only works for PM games
                hour = int(time_of_game_str.split(':')[0]) + 12 #get the hour. Add 12 to get it into military time. only works for PM games
                minute = int(time_of_game_str.split(':')[1])

                #gets the full date and time in the format I want to work properly with gcsa
                full_date_time = output_date_str + str(hour) + ', ' + str(minute)

                #get the location of the game
                location_of_game = games.find('span', class_='e-local local-info')
                location = location_of_game.get_text().strip() #strip away the whitespace
                location_opponent.append(location) #add to our list

                #get the opponent
                team_names = games.find_all('div', class_='team clearfix') #find all the team names listed. This will include my own team
                for teams in team_names:
                    team = teams.get_text().strip() #strip the whitespace
                    try:
                        team = team.split('\n')[0].strip() #sometimes it was getting some extra /n in the string so I wrote this to work around. May not be optimal but it works
                    except:
                        team = team
                    if team != teamName:
                        location_opponent.append(team) #only care about the opponent. Don't want my own team name lists
        
                #assign the list to the value of the key in the dictionary
                date_location_opponent[full_date_time] = location_opponent
                
        except:
            print('There is no game for week ' + str(week))

    #add the games to the calendar
    for gameTime in date_location_opponent:
        #I can come back and maybe fix this later. I needed the date and time in a certain format and could probably get this working properly earlier in the code
        components = gameTime.split(", ")

        #was having issues getting the Event() function to work with a string, so I did this:
        year = int(components[0])
        month = int(components[1])
        day = int(components[2])
        hour = int(components[3])
        minute = int(components[4])

        #add to the google calendar
        event = Event(
            teamName + ' game vs. ' + date_location_opponent[gameTime][1],
            start=datetime(year, month, day, hour, minute),
            location=date_location_opponent[gameTime][0],
            minutes_before_popup_reminder=15
        )
        calendar.add_event(event)

#call the function for my two teams
#addGamesToCalendar('The Big Cottonwoodies', "https://www.quickscores.com/Orgs/ResultsDisplay.php?OrgDir=slchockey&LeagueID=1431065&TeamID=12650229")
#addGamesToCalendar('Grey Grizzlies', "https://www.quickscores.com/Orgs/ResultsDisplay.php?OrgDir=slchockey&LeagueID=1431066&TeamID=12650268")
