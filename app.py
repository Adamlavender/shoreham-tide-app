from flask import Flask, render_template, url_for, request, redirect,flash,send_file
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm, Form
from flask_wtf.csrf import CSRFProtect
from wtforms import StringField, TextField, SubmitField,PasswordField, validators,BooleanField,DateField,SelectField,DateTimeField,TimeField,SelectMultipleField,DecimalField,RadioField
from wtforms.validators import DataRequired, Length, Regexp, NumberRange,ValidationError,StopValidation
from datetime import datetime
import pandas as pd
from pandas import Series,DataFrame
import numpy as np
from datetime import datetime,timedelta
import calendar 
from logging.config import dictConfig


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)

csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    csrf.init_app(app)

app.config.from_mapping(
    SECRET_KEY=b'\xd6\x04\xbdj\xfe\xed$c\x1e@\xad\x0f\x13,@G')

Bootstrap(app)

def date():
    date_range_error = 'Date must be between 06/07/2020 and 12/12/2034'
    date_order = 'Earliest date must be before latest date'
    datetime_error = "Date must be date in the format dd/mm/yyyy"
    
    

    def _date(form, field):
      l = field.data
      print(type(l))
      if type(l) == datetime:
          l = field.data
          if l < datetime.strptime("06/07/2020","%d/%m/%Y") or l > datetime.strptime("12/12/2034","%d/%m/%Y"):
              raise ValidationError(date_range_error)
          if type(form.earliest_date.data) == datetime and type(form.latest_date.data) == datetime:
              if form.earliest_date.data > form.latest_date.data:
                raise StopValidation(date_order)

              
      else: raise StopValidation(datetime_error)
        


    return _date


def time():
    time_order = 'Earliest time must be before latest time'
    time_error = "Date must be time in the format HH:MM"
    
    

    def _time(form, field):
      l = field.data
      print(type(l))
      if type(l) == datetime:
          l = field.data
          if type(form.earliest_time.data) == datetime and type(form.latest_time.data) == datetime:
              if form.earliest_time.data > form.latest_time.data:
                raise StopValidation(time_order)     
      else: raise StopValidation(time_error)
    return _time






class ContactForm(FlaskForm):
  errors = ''
  earliest_date = DateTimeField('Earliest Date in the format dd/mm/yyyy',[date()], default=datetime.strptime("06/07/2020","%d/%m/%Y"),format="%d/%m/%Y")
  
  latest_date = DateTimeField('Latest Date in the format dd/mm/yyyy', [date()], default=datetime.strptime("06/11/2020","%d/%m/%Y"),format="%d/%m/%Y")

  earliest_time = DateTimeField('Earliest Time in the format HH:MM', [
      validators.DataRequired(message="Please enter time in the correct format"),time()], default=datetime.strptime("09:00","%H:%M"),format="%H:%M")
  latest_time = DateTimeField('Latest Time n the format HH:MM',[
        validators.DataRequired(message="Please enter time in the correct format"),time()], default=datetime.strptime("18:00","%H:%M"),format="%H:%M")

  min_desired_tide = DecimalField("Lowest tide (no units in metres)",[validators.NumberRange(min=0,max=10, message="Number between 0 and 10 without units")],default=float("5"))
  max_desired_tide = DecimalField("Highest tide (no units in metres)",[validators.NumberRange(min=0,max=10,message="Number between 0 and 10 without units")], default=float("7"))

  included_tides = RadioField("Within desired tide range, please select desired tide type", [DataRequired(message="Please pick tides to include")], 
                                                        choices=[("H","High"),
                                                                  ("L","Low"),
                                                                  ("Both","Both")], default="High")
  day_of_week = SelectMultipleField('Desired days of the week (cmd click to pick multiple)', [DataRequired(message="Please select one or more days of the week")],
                        choices=[('Monday', 'Mon'),
                                  ('Tuesday', 'Tue'),
                                 ('Wednesday', 'Wed'),
                                 ('Thursday', 'Thur'),
                                 ('Friday', 'Fri'),
                                 ('Saturday', 'Sat'),
                                 ('Sunday', 'Sun')], default="Sunday")
  window_range = SelectField('Pick number of hours either side of high tide to sail', [DataRequired(message="Pick number of hours either side of high tide to sail")],
                        choices=[('0.5', '0.5'),
                                 ('1', '1'),
                                 ('1.5', '1.5'),
                                 ('2', '2'),
                                 ('2.5', '2.5'),
                                 ('3', '3')], default="2.5")
  download_type = SelectMultipleField('I would like to download my data as: (cmd click to pick multiple)', [DataRequired(message="Please select")],
                        choices=[('none', 'None'),
                                  ('google_cal', 'CSV to import into google calendar'),
                                 ('table_view', 'CSV that looks like this table')], default="Sunday")
                                 
  
  submit = SubmitField('Submit')
  
# form = ContactForm(request.form)
@app.route("/",methods = ['POST', 'GET'])
def index():
    form = ContactForm(request.form)
    if request.method == 'POST':
        if form.is_submitted():
            print ("Form successfully submitted")
            
        if form.validate():
            earliest_date = form.earliest_date.data
            latest_date = form.latest_date.data
            earliest_time = form.earliest_time.data
            latest_time = form.latest_time.data
            # earliest_time = form.earliest_time.data
            # latest_time = form.latest_time.data
            min_desired_tide = float(form.min_desired_tide.data)
            max_desired_tide = float(form.max_desired_tide.data)
            window_range = float(form.window_range.data)
            tide_type = str(form.included_tides.data)
            day_of_week = form.day_of_week.data
            global download_type
            download_type = form.download_type.data
            return set_values(earliest_date, latest_date, earliest_time, latest_time, min_desired_tide, max_desired_tide, window_range, day_of_week,tide_type)
           
        else:
          return render_template("index.html",form=form)
      
    return render_template('index.html', 
                               title='Application Form',
                                   form=form)
    # return earliest_date,latest_date,earliest_time,latest_time,min_desired_tide,max_desired_tide,window_range,day_of_week
    

    

def set_values(earliest_date,latest_date,earliest_time,latest_time,min_desired_tide,max_desired_tide,window_range,day_of_week,tide_type):

  print(earliest_date,latest_date,earliest_time,latest_time,min_desired_tide,max_desired_tide,window_range,day_of_week)
  print(type(download_type), download_type)
  jtide_df = pd.read_csv('Shoreham_tides.csv')

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
  jtide_df.drop_duplicates(keep="last",inplace=True, ignore_index=True)
  try:
      jtide_df.drop(columns = ["TwilightBegin","Transit","TwilightEnd"],inplace=True)
      
  except:
      pass
  
  

  date_range = pd.date_range(earliest_date,latest_date)

  def time_in_range(earliest_time,latest_time, x):
      """Return true if x is in the range [start, end]"""
      if earliest_time <= latest_time:
          return earliest_time <= x <= latest_time
      else:
          return earliest_time <= x or x <= latest_time



  

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
  if tide_type == "H" or tide_type == "L":
        accepted_tides = accepted_days.loc[(accepted_days["Tide"] > min_desired_tide) & (accepted_days["Type"] == tide_type) & (accepted_days["Tide"] < max_desired_tide)] 
  else:
      accepted_tides = accepted_days.loc[(accepted_days["Tide"] > min_desired_tide) & (accepted_days["Tide"] < max_desired_tide)]

      
  accepted_tides.drop_duplicates(keep="last",inplace=True, ignore_index=True)

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
      print(item)
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
  accepted_window.drop_duplicates(keep="last",inplace=True, ignore_index=True)   


  for i in range(len(accepted_window["Date"])):
      accepted_window["Date"][i] = datetime.strftime(accepted_window["Date"][i],"%d/%m/%Y")

  time_range2 = []
  for i in range(len(accepted_start)):

      time_range2.append(datetime.strftime(accepted_start[i],"%H:%M") + " - " + datetime.strftime(accepted_end[i], "%H:%M"))
  accepted_window["Sailing_window_rounded"] = time_range2

  

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

  global final_table
  final_table = accepted_window.drop(columns=["Unnamed: 0","DaylightTime","Month","Day","Year","Start","Sunrise","Units"]).rename(columns={"Time":"Tide Time","Tide":"Tide Height(m)","Type":"Tide Type","Sailing_window_rounded":"Recommended sailing window","Day_of_week":"Day of week","TwighlightEnd": "Last Daylight"})
  final_table.to_csv("My_tide_data.csv")
  return render_template('update.html',tables=[final_table.to_html(classes='data')],titles = ['Predicted tides'],download_type= download_type)

@app.route('/download-cal')
def download_cal():
  if 'google_cal' in download_type:
    path = "Sailing_cal2.csv"
    return send_file(path, as_attachment=True)
      
@app.route('/download-table')
def download_table():
  if 'table_view' in download_type:
    path = "My_tide_data.csv"
    return send_file(path, as_attachment=True)


  

	



if __name__ == "__main__":
  app.run(debug=True,port="5566")