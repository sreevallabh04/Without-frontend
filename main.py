import os
import asyncio
import speech_recognition as sr
import pyttsx3
import pywhatkit
import datetime
import wikipedia
import pyjokes
import webbrowser
import aiohttp
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import subprocess

# API Keys
NEWS_API_KEY = "e1b9396392044aa5bcecb7f0ab29dbb6"
WEATHER_API_KEY = "029fd7af99a54f22ac6173050240108"

# Initialize Text-to-Speech Engine
engine = pyttsx3.init()
engine.setProperty('voice', engine.getProperty('voices')[1].id)
engine.setProperty('rate', 140)

def talk(text):
    """Speak the given text aloud."""
    engine.say(text)
    engine.runAndWait()

def take_command():
    """Listen for a voice command and return the recognized text."""
    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            print("Listening...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=10)
            command = recognizer.recognize_google(audio).lower()
            print(f"Command: {command}")
            return command
    except sr.UnknownValueError:
        talk("I didn't catch that. Please repeat.")
    except sr.RequestError as e:
        talk("There was an issue with the speech recognition service.")
    except Exception as e:
        talk("An error occurred. Please try again.")
        print(f"Error: {e}")
    return ""

async def get_weather(city_name):
    """Fetch the current weather for a city using Weather API."""
    url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={city_name}&aqi=no"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                temperature = data['current']['temp_c']
                location = data['location']['name']
                result = f"The temperature in {location} is {temperature} degrees Celsius."
                talk(result)
                return result
            else:
                talk("I couldn't fetch the weather information. Please try again.")
                return "Error fetching weather data."

async def get_news():
    """Fetch top news headlines using News API."""
    url = f"https://newsapi.org/v2/top-headlines?country=in&apiKey={NEWS_API_KEY}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                headlines = [article["title"] for article in data.get("articles", [])[:5]]
                talk("Here are today's top headlines.")
                for headline in headlines:
                    talk(headline)
                return headlines
            else:
                talk("I couldn't fetch the news. Please try again.")
                return []

def search_google(query):
    """Perform a Google search and return top results."""
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get("https://www.google.com")
    search_box = driver.find_element(By.NAME, "q")
    search_box.send_keys(query)
    search_box.submit()
    driver.implicitly_wait(3)
    results = driver.find_elements(By.CSS_SELECTOR, 'h3')
    links = [result.find_element(By.XPATH, '..').get_attribute('href') for result in results[:5]]
    driver.quit()
    return links

def get_wikipedia_summary(query):
    """Fetch a brief summary from Wikipedia."""
    try:
        return wikipedia.summary(query, sentences=2)
    except wikipedia.exceptions.DisambiguationError:
        return "There are multiple entries for this topic. Please be more specific."
    except wikipedia.exceptions.PageError:
        return "I couldn't find any information on that topic."
    except Exception as e:
        return f"Error retrieving information: {e}"

def open_file(file_name):
    """Open a file on the user's laptop."""
    try:
        file_path = os.path.expanduser(f"~/Desktop/{file_name}")  # Change the path as needed
        if os.path.exists(file_path):
            talk(f"Opening {file_name}")
            subprocess.run(["xdg-open" if os.name == "posix" else "start", file_path], shell=True)
        else:
            talk(f"The file {file_name} does not exist on your desktop.")
    except Exception as e:
        talk("An error occurred while trying to open the file.")
        print(f"Error: {e}")

def execute_command(command):
    """Process and execute user commands."""
    if 'what can you do' in command or 'list your functions' in command:
        features = (
            "I can do the following things: "
            "1. Play songs on YouTube. "
            "2. Tell you the current time, date, and day. "
            "3. Provide weather updates for a city. "
            "4. Fetch the latest news headlines. "
            "5. Give brief summaries from Wikipedia. "
            "6. Crack a joke for you. "
            "7. Perform a Google search and provide top results. "
            "8. Open websites like Google, YouTube, or others. "
            "9. Open specific files on your desktop. "
            "10. Exit the assistant when you are done."
        )
        talk(features)
        print(features)
    elif 'play' in command:
        song = command.replace('play', '').strip()
        talk(f"Playing {song}")
        pywhatkit.playonyt(song)
    elif 'time' in command:
        time_now = datetime.datetime.now().strftime('%I:%M %p')
        talk(f"The current time is {time_now}")
    elif 'date' in command:
        date_today = datetime.datetime.now().strftime('%d %B, %Y')
        talk(f"Today's date is {date_today}")
    elif 'day' in command:
        day_today = datetime.datetime.now().strftime('%A')
        talk(f"Today is {day_today}")
    elif 'weather in' in command:
        city = command.replace('weather in', '').strip()
        asyncio.run(get_weather(city))
    elif 'news' in command:
        asyncio.run(get_news())
    elif 'who is' in command or 'tell me about' in command:
        topic = command.replace('who is', '').replace('tell me about', '').strip()
        summary = get_wikipedia_summary(topic)
        talk(summary)
    elif 'joke' in command:
        joke = pyjokes.get_joke()
        talk(joke)
    elif 'search' in command:
        query = command.replace('search', '').strip()
        talk("Searching Google...")
        links = search_google(query)
        for link in links:
            print(link)
    elif 'open' in command:
        if 'file' in command:
            file_name = command.replace('open file', '').strip()
            open_file(file_name)
        else:
            site = command.replace('open', '').strip()
            talk(f"Opening {site}")
            webbrowser.open(f"https://{site}.com")
    elif 'exit' in command or 'bye' in command:
        talk("Goodbye! Have a great day!")
        return False
    else:
        talk("I didn't understand that. Can you repeat?")
    return True

def run_virtual_assistant():
    """Main function to run the virtual assistant."""
    talk("Hello, I am Zara, your virtual assistant. How can I assist you today?")
    while True:
        command = take_command()
        if command and not execute_command(command):
            break

if __name__ == "__main__":
    run_virtual_assistant()
