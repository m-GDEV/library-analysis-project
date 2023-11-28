# Name:        Guelph Library Analysis
# Description: Script to monitor Guelph's library Occupancy/Capacity
# Author:      Musa Ahmed
# Date:        November 21, 2023


"""
Steps:
    1 - Run in infinite loop writing to the same file everytime
    2 - If planning on running for a very long time make a periodic backup of file
    3 - In loop, during open hours, get occupancy every ten minutes
    4 - Then write the following to the csv file:
            occupancy -> int
            capacity -> int
            time of day -> int (time in seconds. 0 is 00:00)
            day of the week -> int (1 is Monday, 7 is Sunday)
            current date -> datetime
            opening hours -> int (time in seconds)
            closing hours -> int (time in seconds)
            temperature (actual) -> int
            temperature (feels like) -> int
            sunrise & sunset -> int (time in seconds)
            one/few word(s) to describe the weather -> str
    5 - Analyze the data:
            determine the percentage of occupancy
            compare sunrise and sunset and how early/late it gets busy/empty

Resources:
- For general reference: https://www.lib.uoguelph.ca/
- For occupancy: https://display.safespace.io/value/live/e81c82f9
- For capacity (likely is static): https://display.safespace.io/entity/space/hash/e81c82f9
- For Hours, open status: https://api3-ca.libcal.com/api_hours_today.php?iid=3228&format=json
- For date conversions:
    https://strftime.org/
    https://www.programiz.com/python-programming/datetime/strptime
    https://www.datacamp.com/tutorial/converting-strings-datetime-objects
- For weather: https://wttr.in
- For csv writing: https://chat.openai.com/c/52b3b04d-611d-453f-8dfa-ac08ad84dcb5
"""

# Step 0 (setup stuff)
from datetime import datetime, time
from time import sleep
from dotenv import dotenv_values
import smtplib
import requests
import csv
import os

# Some misc functions needed for the program
def convertTimeFromApiToSeconds(hour: str, minutes: str):
    if "am" in hour:
        return (int(hour.replace("am", "")) * 3600) + (int(minutes) * 60)
    elif "pm" in hour:
        return (int(hour.replace("pm", "")) * 3600 * 2) + (int(minutes) * 60)
    else:
        return 0

def send_mail(receiving : str, password, title: str, body: str):
    # Auth
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login("guycool123abc@gmail.com", password)

    # Sending email
    msg = f"Subject: {title}\n\n\n{body}"

    server.sendmail(
        "guycool123abc@gmail.com",
        receiving,
        msg
    )

# This class is meant only to be used as an object.
# It will contain the data collected everytime the loop is run
class DataObject:
    def __init__(
        self,
        occupancy: int,
        capacity: int,
        currentTime: time,
        dayOfWeek: int,
        currentDate: datetime,
        openingTime: str,
        closingTime: str,
        currentActualTemperature: float,
        currentFeelTemperature: float,
        currentSunriseTime: int,
        currentSunsetTime: int,
        weatherDescription: str) -> None:
        self.occupancy = occupancy
        self.capacity = capacity
        self.currentTime = currentTime
        self.dayOfWeek = dayOfWeek
        self.currentDate = currentDate
        self.openingTime = convertTimeFromApiToSeconds(openingTime, '0')
        self.closingTime = convertTimeFromApiToSeconds(closingTime, '0')
        self.currentActualTemperature = currentActualTemperature
        self.currentFeelTemperature = currentFeelTemperature
        self.currentSunriseTime = currentSunriseTime
        self.currentSunsetTime = currentSunsetTime
        self.weatherDescription = weatherDescription

    def __str__(self):
        return f"""
--- DataObject DEBUG ---
Occupancy:\t{self.occupancy}
Capacity:\t{self.capacity}
Current Time:\t{self.currentTime}
Day of Week:\t{self.dayOfWeek}
Current Date:\t{self.currentDate}
Opening Time:\t{self.openingTime}
Closing Time:\t{self.closingTime}
Temperature A:\t{self.currentActualTemperature}
Temperature F:\t{self.currentFeelTemperature}
Sunrise Time:\t{self.currentSunriseTime}
Sunset Time:\t{self.currentSunsetTime}
Weather Description : {self.weatherDescription}
        """

    def toRow(self):
        return [
            self.occupancy,
            self.capacity,
            self.currentTime,
            self.dayOfWeek,
            self.currentDate,
            self.openingTime,
            self.closingTime,
            self.currentActualTemperature,
            self.currentFeelTemperature,
            self.currentSunriseTime,
            self.currentSunsetTime,
            self.weatherDescription
        ]

def createDataObject(weatherKey) -> DataObject:
    # Get data
    occupancy = requests.get("https://display.safespace.io/value/live/e81c82f9").json()
    capacity: int = 3500
    currentTime: time = datetime.now().time()
    dayOfWeek: int = datetime.now().weekday() + 1
    currentDate: datetime = datetime.now()

    openingTime: str = requests.get("https://api3-ca.libcal.com/api_hours_today.php?iid=3228&format=json").json()['locations'][0]['times']['hours'][0]['from']
    closingTime: str = requests.get("https://api3-ca.libcal.com/api_hours_today.php?iid=3228&format=json").json()['locations'][0]['times']['hours'][0]['to']

    currentActualTemperature: float = float(requests.get(f"https://api.openweathermap.org/data/2.5/weather?q=Guelph&appid={weatherKey}&units=metric").json()['main']['temp'])
    currentFeelTemperature: float = float(requests.get(f"https://api.openweathermap.org/data/2.5/weather?q=Guelph&appid={weatherKey}&units=metric").json()['main']['feels_like'])

    currentSunriseTime: int = int(requests.get(f"https://api.openweathermap.org/data/2.5/weather?q=Guelph&appid={weatherKey}&units=metric").json()['sys']['sunrise'])
    currentSunsetTime: int = int(requests.get(f"https://api.openweathermap.org/data/2.5/weather?q=Guelph&appid={weatherKey}&units=metric").json()['sys']['sunset'])

    weatherDescription: str = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q=Guelph&appid={weatherKey}&units=metric").json()['weather'][0]['description']

    # Create an instance of the DataObject class
    data_instance = DataObject(
        occupancy=occupancy,
        capacity=capacity,
        currentTime=currentTime,
        dayOfWeek=dayOfWeek,
        currentDate=currentDate,
        openingTime=openingTime,
        closingTime=closingTime,
        currentActualTemperature=currentActualTemperature,
        currentFeelTemperature=currentFeelTemperature,
        currentSunriseTime=currentSunriseTime,
        currentSunsetTime=currentSunsetTime,
        weatherDescription=weatherDescription
    )

    return data_instance

# Step 1
iterations = 0
backups = 0
writes = 0

credentials = dotenv_values("./credentials")
weatherKey = credentials['weatherKey']
mailPassword = credentials['mailPassword']


try:
    while True:
        if requests.get("https://api3-ca.libcal.com/api_hours_today.php?iid=3228&format=json").json()['locations'][0]['times']['status'] == "open":

            data_instance = createDataObject(weatherKey)
            # Print data
            print("\n-----------------------------------")
            print(f"--- Iterations: {iterations} | Backups: {backups} ---")
            print(data_instance)

            # Saving file
            with open('./library-analysis-data.csv', 'a+', newline='') as file:
                file_writer = csv.writer(file, delimiter=',')

                # If data file is empty (i.e running on a new computer) create the head title thing csvs need
                if len(file.readlines()) == 0:
                    file_writer.writerow(list(vars(data_instance)))

                file_writer.writerow(data_instance.toRow())
                writes += 1
                print(f"--- File Written\t{writes} Writes ---")

            # Around every 12 hours
            if iterations % 72 == 0:
                # Backup the file
                print(f"--- File Backed Up {backups + 1} Backups ---")
                os.system(f"cp ./library-analysis-data.csv ./library-analysis-data.csv.BACKUP{backups}")
                backups += 1

        # If library is not open
        else:
            print("Library not open, sleeping")

        # General that happens every loop
        sleep(600) # 10 minutes
        iterations += 1

# In the case the script stops working (broken api, etc) send me an email
except Exception as e:
    send_mail("musaa.ahmed7@gmail.com", mailPassword, "Library Script has stopped! - " + str(e), repr(e))
    raise e
