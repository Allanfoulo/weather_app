import streamlit as st
import requests
import os
from dotenv import load_dotenv
import groq
import re
from datetime import datetime

load_dotenv()

def get_weather_data(city, weather_api_key):
     
        if city is None or weather_api_key is None:
            raise ValueError("City and API key must not be None")
        
        base_url = "http://api.openweathermap.org/data/2.5/weather?"
        complete_url =f"{base_url}appid={weather_api_key}&q={city}"
        response = requests.get(complete_url)

        return response.json()


def generate_weather_description(data, groq_api_key):
    client = groq.Client()
    
    try:
        # Convert Temperature from Kelvin to Celsius
        temperature = data['main']['temp'] - 273.15  # to Conver it to Celsius
        description = data['weather'][0]['description']
        city_displayed = data['sys']['name'] if 'sys' in data and 'name' in data['sys'] else 'Unknown'
        prompt = f"The current Weather in {city_displayed} is {description} with a temperature of {temperature:.1f}C. Explain this in a simple way for a general audience"

        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                },
            ],
            max_tokens=60,
        )
        if len(response.choices) > 0:
            return response.choices[0].message.content
        else:
            return "No weather description available"

    except Exception as e:
        return f"Error: {str(e)}"


def get_weekly_forecast(weather_api_key,lat,lon):
    base_url="http://api.openweathermap.org/data/2.5/weather?" 
    weekly_forecast_complete_url=f"{base_url}forecast?lat={lat}&lon={lon}&appid={weather_api_key}"
    weekly_forecast_response=requests.get(weekly_forecast_complete_url)

       
    return weekly_forecast_response.json()

def display_weekly_forecast(data):
    try:
        st.write("========================================")
        st.write("### Weekly Weather Forecast")
        display_dates=set() #To Keep Track of dates for which forecast havs been displayed

        c1,c2,c3,c4=st.columns(4)
        with c1:
            st.metric("","Day")
        with c2:
            st.metric("","Desc")
        with c3:
            st.metric("","Min_temp")
        with c4:
            st.metric("","Max_temp")

        for day in data:
            date=datetime.fromtimestamp(day['dt']).strftime('%A, %B %d')
            #Ccheck if the date has already been displayed
            if date not in display_dates:
                display_dates.add(date)

                min_temp=day['main']['temp_min']-273.15 #conver Kelvin to Celsius
                max_temp=day['main']['temp_max']-273.15
                description = day['weather'][0]['description']

                with c1:
                    st.write(f"{date}")
                with c2:
                    st.write(f"{description.capitalize()}")
                with c3:
                    st.write(f"{min_temp:.1f}°C")
                with c4:
                    st.write(f"{max_temp:.1f}°C")

    except Exception as e:
        st.error("Error in displaying weekly forecast"+ str(e))


#Funtion to normalize the city name
def normalize_city_name(city):
    # Remove any non-alphabetic characters and convert to lowercase
    return re.sub(r'[^a-zA-Z]', '', city).lower()


# Main function to test app in Streamlit
def weather_tool():
    # Configuration
    st.title("Weather Forecasting with LLM")
    city_4normilization = st.text_input("Enter City name", "London")

    city = normalize_city_name(city_4normilization)

    # API Keys
    weather_api_key = os.getenv("OWM_API_KEY")
    groq_api_key = os.getenv("GROQ_API_KEY")

    # Button to fetch and display Weather Data
    submit = st.button("Get Weather")

    if submit:
        st.title("Weather updates for " + city + " is")
        with st.spinner('Fetching Weather data ...'):
            weather_data = get_weather_data(city, weather_api_key)

            

            # Check if the city is found and display weather data
            if weather_data.get("cod") != 404:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Temperature", f"{weather_data['main']['temp'] - 273.15:.2f}°C")
                    st.metric("Humidity", f"{weather_data['main']['humidity']} %")
                with col2:
                    st.metric("Pressure", f"{weather_data['main']['pressure']} hPa")
                    st.metric("Wind Speed", f"{weather_data['wind']['speed']} m/s")

                lat= weather_data['coord']['lat']
                lon= weather_data['coord']['lon']



                # Generate and display a friendly weather description
                weather_description = generate_weather_description(weather_data, groq_api_key)
                st.write(weather_description)

                #Call Funtion to get the weekly forecast
                forecast_data= get_weekly_forecast(weather_api_key,lat,lon)
                
                print(forecast_data)

                print(forecast_data)#This is the just to check what the data looks like

                if forecast_data.get('cod')!='404':
                    display_weekly_forecast(forecast_data)
                else:
                    st.error("Error fetching weekly forecast data!")


            else:
                # Display an error message if the city is not found
                st.error("City not found or an error occurred")


if __name__ == "__main__":
    weather_tool()