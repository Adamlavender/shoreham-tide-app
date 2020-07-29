
import pandas as pd
from pandas import Series,DataFrame
import numpy as np
from datetime import datetime,timedelta
import calendar 
jtide_df = pd.read_csv('Shoreham_England.csv')


i = 1
date_list=[]
day_list=[]

for i in range(len(jtide_df)):
    date_list.append(datetime(jtide_df["Year"][i],jtide_df["Month"][i],jtide_df["Day"][i]))
    i+=1
for date in date_list:
    
    day_name = (calendar.day_name[date.weekday()]) 
    day_list.append(day_name)

jtide_df["Day_of_week"] = day_list
jtide_df["Date"] = date_list

try:
    jtide_df.drop(columns = ["TwilightBegin","Transit","TwilightEnd"],inplace=True)
except:
    pass


while True:
        try:
            earliest_date = datetime.strptime(input("Please enter the earliest date in the format dd/mm/yyyy\n"),"%d/%m/%Y")
        except:
            print('Sorry, not correct format please try again!')
        else:
            break
            
while True:
        try:
            latest_date = datetime.strptime(input("Please enter the latest date in the format dd/mm/yyyy\n"),"%d/%m/%Y")
        except ValueError:
            print('Sorry, not correct format please try again!')
        else:
            break
while True:
    try:
        earliest_time = datetime.strptime(input("Please enter the earliest time in 24 hour time in the format hh:mm e.g 14:02\n"),"%H:%M")
    except ValueError:
        print('Sorry, not correct format please try again!')
    else:
        break


while True:
    try:
        latest_time = datetime.strptime(input("Please enter the latest time in 24 hour time in the format hh:mm e.g 14:02\n"),"%H:%M")
    except ValueError:
        print('Sorry, not correct format please try again!')
    else:
        break


while True:
    try:
        min_desired_tide = float(input("Please minimum tide height(m)'\n"))
    except ValueError:
        print('Sorry, a bet must be an integer!')
    else:
        if type(min_desired_tide) == float:
            break
        else:
            print("Do not enter units")
        
        
while True:
    try:
        max_desired_tide = float(input("Please Maximum tide height(m) without units'\n"))
    except ValueError:
        print('Sorry, a bet must be an integer!')
    else:
        if type(max_desired_tide) == float:
            break
        else:
            print("Do not enter units")
            
while True:
    try:
        window_range = float(input("How many hours would you like predicted sailing window to be either side of high tide? (No units, in numeric)'\n"))
    except ValueError:
        print('Please only enter an numeric value with no units')
    else:
        break

            
while True:
    try:
        day_of_week = input("Please enter the acceptable days of the week you are looking for in full e.g 'Monday,Thursday'\n").split(",")
    except ValueError:
        print('Please enter the full day of the week!')
    else:
        break


date_range = pd.date_range(earliest_date,latest_date)

def time_in_range(earliest_time,latest_time, x):
    """Return true if x is in the range [start, end]"""
    if earliest_time <= latest_time:
        return earliest_time <= x <= latest_time
    else:
        return earliest_time <= x or x <= latest_time


# In[493]:


accepted_times = DataFrame(columns = jtide_df.columns)
accepted_dates = DataFrame(columns = jtide_df.columns)

for date in date_range:
    accepted_dates = accepted_dates.append(jtide_df.loc[jtide_df["Date"] == date], ignore_index=True)     
for time in accepted_dates["Time"]:
        if time_in_range(earliest_time,latest_time,datetime.strptime(time,"%H:%M:%S")):
            accepted_times = accepted_times.append(accepted_dates.loc[accepted_dates["Time"] == time], ignore_index=True) 
    


desired_weekday = []
for item in day_of_week:
    item = item.replace(" ","").lower().capitalize()
    desired_weekday.append(item)



accepted_days = DataFrame(columns = jtide_df.columns)
i = 0

# for input_day in desired_weekday:
for day in accepted_times["Day_of_week"]:
    accepted_days = accepted_days.append(accepted_times.loc[accepted_times["Day_of_week"] == desired_weekday[i]])
    
    i += 1
    if i == len(desired_weekday):
        break
            
accepted_tides = accepted_days.loc[accepted_days["Tide"] > min_desired_tide]
accepted_tides = accepted_tides.loc[accepted_tides["Tide"] < max_desired_tide]      


def roundTime(dt=None, roundTo=60):
    if dt == None :
        dt = datetime.datetime.now()
    seconds = (dt.replace(tzinfo=None) - dt.min).seconds
    rounding = (seconds+roundTo/2) // roundTo * roundTo
    return dt + timedelta(0,rounding-seconds,-dt.microsecond)

time_range = []
time_range_start = []

for time in accepted_tides["Time"]:
    time_range.append(roundTime(datetime.strptime(time,"%H:%M:%S"),roundTo=30*60))
#     time_range.append(datetime.strptime(time,"%H:%M:%S"))


for item in time_range:
    if item == earliest_time + timedelta(hours=window_range) - timedelta(hours=0.5):
        item = item + timedelta(hours=0.5)
    elif item == latest_time - timedelta(hours=window_range) + timedelta(hours=0.5):
        item = item - timedelta(minutes=30)
        
    time_range_start.append(item - timedelta(hours=window_range))
time_range


accepted_tides["Start"] = time_range_start

accepted_start = [x for x in time_range_start if x >= earliest_time  and x <= (latest_time - timedelta(hours= 2*window_range)) ]
accepted_end = [x + timedelta(hours=2 * window_range) for x in accepted_start]


accepted_window = accepted_tides.loc[(accepted_tides["Start"] >= earliest_time) & (accepted_tides["Start"] <= (latest_time - timedelta(hours= 2*window_range)))]
accepted_window.reset_index(drop=True,inplace =True)    


time_range2 = []
for i in range(len(accepted_start)):

    time_range2.append(datetime.strftime(accepted_start[i],"%H:%M:%S") + " - " + datetime.strftime(accepted_end[i], "%H:%M:%S"))
accepted_window["Sailing_window_rounded"] = time_range2

accepted_window.drop(columns=["DaylightTime","Month","Day","Year","Start","Sunrise"]).rename(columns={"Time":"Tide Time","Sailing_window_rounded":f"Recommended sailing window"})

google_calendar_df = accepted_window.copy()

google_calendar_df["End Time"] = google_calendar_df["Start"] + timedelta(hours=5)
google_calendar_df.rename(columns={"Start":"Start Time"}, inplace=True)
google_calendar_df.rename(columns={"Time":"Tide Time","Date":"Start Date"}, inplace=True)
i = 0
for row in google_calendar_df:
    google_calendar_df["Description"] = "Tide Time = " + str(google_calendar_df["Tide Time"][i]) + "\nTide Height = " + str(google_calendar_df["Tide"][i]) + "\nSunset Time = " + google_calendar_df["Sunset"][i] +"\n\nIf you are unable to sail or would like your name added to the list you MUST text Michelle on 07446841128 by 5pm the evening before - at the latest! \n\nCANCELLED SESSIONS WILL BE POSTED ON SOCIAL MEDIA AND OUR WEBSITE.\n\n@adursailing www.adursailing.co.uk\n\nPlease bring \n\n- spare set of dry clothing\n- separate jumper or sweatshirt for on the water\n- waterproof top for on the water\n- closed toe footwear\n- food and drink\n- sun cream"
    i += 1
    if i == len(google_calendar_df["Description"]):
        break

google_calendar_df["Location"] = "Adur Sailing Club, 223 Harbour Way, Shoreham-by-Sea BN43 5HZ, UK"
for i in range(len(google_calendar_df)):
    google_calendar_df["Start Time"][i] = datetime.strftime(google_calendar_df["Start Time"][i],"%I:%M %p")
    google_calendar_df["End Time"][i] = datetime.strftime(google_calendar_df["End Time"][i],"%I:%M %p")

google_calendar_df["Subject"] = "Adur Sailing Session"
google_calendar_df.drop(columns=["Sunset","Day_of_week","Units","Sailing_window_rounded","Type"],inplace=True)
google_calendar_df["End Date"] = google_calendar_df["Start Date"]
google_calendar_df.to_csv("Sailing_cal2.csv")
google_calendar_df

# %%
