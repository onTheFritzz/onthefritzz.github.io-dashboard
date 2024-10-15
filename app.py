import requests, shutil, time, yaml, os
from datetime import datetime as dt
from pyA20.gpio import gpio
from pyA20.gpio import port
from work import dht11

class eReader():
    def __init__(self):
        with open(f'./config.yaml', 'r') as y:
            yml = yaml.safe_load(y)

        #print(yml)
        self.distanceEndpoint = yml['distanceEndpoint']
        self.noaaEndpoint = yml['noaaEndpoint']
        self.ethEndpoint = yml['ethEndpoint']
        self.htmlOutputFile = yml['htmlOutput']
        self.gitterFilePath = yml['gitterFilePath']

        if os.name != 'nt':
            self.filePath = yml['linuxFilePath']
        else:
            self.filePath = yml['windowsFilePath']

    def update(self):
        dashboardHtml = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stylish 3D Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Montserrat', sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #282A36; /* Dark background */
            color: #F8F8F2; /* Light text color */
            border-radius: 10px; /* Rounded corners */
            box-shadow: 0 0 20px rgba(0, 0, 0, 0.5); /* Shadow for depth */
        }

        .dashboard {
            display: flex;
            flex-wrap: wrap;
            gap: 20px; /* Gap between cards */
            justify-content: center;
            perspective: 1000px; /* Adds perspective for 3D effect */
        }
        
        .card {
            background-color: #44475A; /* Card background */
            border: 1px solid rgba(255, 255, 255, 0.1); /* Subtle border for cards */
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2); /* Enhanced shadow for depth */
            border-radius: 10px;
            padding: 10px; /* Adjusted padding for better layout */
            flex: 1 1 30%; /* Flexible width */
            max-width: 30%;
            height: 350px; /* Adjusted height to accommodate image and text */
            text-align: center;
            transform-style: preserve-3d; /* Enable 3D transformations */
            transition: box-shadow 0.3s, transform 0.3s; /* Transition for shadow effect */
        }

        .card img {
            width: 100%; /* Set image width to 100% of the card */
            height: auto; /* Set height to auto for proper aspect ratio */
            max-height: 200px; /* Max height for image */
            object-fit: contain; /* Maintain aspect ratio without cutting off */
            border-radius: 10px; /* Rounded corners for the image */
            margin-bottom: 10px; /* Space below the image */
        }
        
        .card:hover {
            box-shadow: 0 15px 40px rgba(0, 0, 0, 0.3); /* Increase shadow on hover */
            transform: translateY(-5px); /* Lift the card slightly on hover */
        }

        .card h3 {
            font-size: 1.4em;
            color: #FF79C6; /* Pink color for headings */
            margin-bottom: 15px;
            text-transform: uppercase; /* Uppercase for headings */
        }
        
        .card .value {
            font-size: 2.8em;
            color: #50FA7B; /* Light green for values */
            font-weight: bold;
            transition: color 0.3s; /* Smooth color transition */
        }
        
        .card:hover .value {
            color: #FFB86C; /* Light orange on hover */
        }

        @media (max-width: 768px) {
            .card {
                flex: 1 1 45%; /* Adjust for smaller screens */
                max-width: 45%;
            }
        }
        
        @media (max-width: 480px) {
            .card {
                flex: 1 1 100%; /* Stack cards on very small screens */
                max-width: 100%;
            }
        }
    </style>
</head>
<body>

<div class="dashboard">
    <div class="card">
        <img src="../images/commute.png" alt="Commute">
        <h3>#COMMUTETITLE#</h3>
        <div class="value" id="commute">#COMMUTESTATUS#</div>
    </div>
    <div class="card">
        <img src="../images/ether.png" alt="Ether">
        <h3>#ETHERTITLE#</h3>
        <div class="value" id="ether">#ETHERPRICE#</div>
    </div>
    <div class="card">
        <img src="../images/warehouse.png" alt="Warehouse">
        <h3>#WAREHOUSETITLE#</h3>
        <div class="value" id="warehouse">#WAREHOUSETEMP#</div>
    </div>
    <div class="card">
        <img src="../images/weather.png" alt="Weather">
        <h3>#OUTSIDETITLE#</h3>
        <div class="value" id="pressure">#OUTSIDETEMP#</div>
    </div>
</div>

<script>
// Sample JSON data for environmental variables

/*const data = {
    "warehouse": "99°C/48%",
    "humidity": "60 %",
    "windSpeed": "15 km/h",
    "pressure": "1015 hPa",
    "visibility": "10 km",
    "uvIndex": "5"
};

// Function to display data in the dashboard
function loadDashboardData() {
    document.getElementById('temperature').innerText = data.temperature;
    document.getElementById('humidity').innerText = data.humidity;
    document.getElementById('windSpeed').innerText = data.windSpeed;
    document.getElementById('pressure').innerText = data.pressure;
    document.getElementById('visibility').innerText = data.visibility;
    document.getElementById('uvIndex').innerText = data.uvIndex;
}

// Load the data after the page is fully loaded
window.onload = loadDashboardData;
*/
</script>
#TIMESTAMP#
</body>
</html>                   
    """
        travelTitle = 'Drive Home'

        with open(f'{self.filePath}current-travel-time.txt', 'r') as r: #self.getTravelTime() # '17-21mins'#
            travelInfo = r.readlines()[0]
            print(travelInfo)

        whTitle = 'Warehouse Temp/Humidity'
            
        if os.name != 'nt':
            whTempHumid = self.getWarehouseTemp() #'57&#176;F / 45%'
        else:
            whTempHumid = '12&#176;F / 99%'

        outsideTitle = 'Outside Temp/Humidity'
        outsideTempHumid = self.scrapeNOAA()

        cryptoTitle = 'ETHEREUM Price'
        cryptoPrice = self.getCryptoPrice()

        currentTime = f'APIs Last Updated: {dt.now().strftime("%m-%d-%Y %H:%M:%S")}'

        dashboardHtml = dashboardHtml.replace('#WAREHOUSETITLE#', whTitle).replace('#WAREHOUSETEMP#', whTempHumid)
        dashboardHtml = dashboardHtml.replace('#COMMUTETITLE#', travelTitle).replace('#COMMUTESTATUS#', travelInfo)
        dashboardHtml = dashboardHtml.replace('#OUTSIDETITLE#', outsideTitle).replace('#OUTSIDETEMP#', outsideTempHumid)
        dashboardHtml = dashboardHtml.replace('#ETHERTITLE#', cryptoTitle).replace('#ETHERPRICE#', cryptoPrice)
        dashboardHtml = dashboardHtml.replace('#TIMESTAMP#', currentTime)
            
        with open(f'{self.filePath}{self.htmlOutputFile}', 'w+') as html:
          html.write(dashboardHtml)
            
        with open(f'{self.filePath}index.html', 'w+') as html:
            html.write(dashboardHtml)

        print('Updated display to stats.')
        self.gitPushup()

    def scrapeNOAA(self):
        x = 0
        while x < 3:
            try:
                noaaGet = requests.get(self.noaaEndpoint)
                noaaJson = noaaGet.json()

                todayForecast = noaaJson['properties']['periods'][0]

                #icon = f'http://api.weather.gov{todayForecast["icon"]}'
                temp, unit = [todayForecast['temperature'], todayForecast['temperatureUnit']]
                try:
                    humidity = f"{todayForecast['relativeHumidity']['value']}"
                except:
                    humidity = "NA"

                printString = f'{temp}*{unit} / {humidity}%'
                print(f'Outside Temp: {printString}')

                outputArray = f'{temp}&#176;{unit} / {humidity}%'#, icon]
                return(outputArray)
            
            except:
                x += 1
                outputArray = [f'NA / NA', 'NA']
                continue

        return(outputArray)

    def getWarehouseTemp(self):
        PIN2 = port.PA6
        gpio.init()

        x = 0
        while x < 5: # DHT11 doesn't output stats 100% of the time. Seems to be > 5/1 hit to miss ratio.
            try: # Try catching temp/humid 5x before moving along
                instance = dht11.DHT11(pin=PIN2)
                dhtDevice = instance.read()

                tempC = dhtDevice.temperature
                tempF = round(tempC * (9 / 5) + 32)

                humidity = dhtDevice.humidity

                printString = f'{tempF}*F / {humidity}%'
                print(f'Warehouse Temp: {printString}')
                outputString = f'{tempF}&#176;F / {humidity}%'
                return(outputString)
            
            except:
                x += 1
                print('Warehouse temp error!')
                outputString = f'NA / NA'
                time.sleep(1)
                continue

        return(outputString)
        
    def getCryptoPrice(self):
        cryptoPrice = requests.get(self.ethEndpoint)
        cryptoJson = cryptoPrice.json()
        cryptoToUSD = round(float(cryptoJson['data']['amount']), 2)
        outputString = f'${cryptoToUSD}'

        print(f'Crypto: {outputString}')
        return(outputString)
    
    def getTravelTime(self):
        responseJson = requests.get(self.distanceEndpoint).json()
        durationTime = responseJson['rows'][0]['elements'][0]['duration']['text']
        durationInTraffic = responseJson['rows'][0]['elements'][0]['duration_in_traffic']['text']
        travelTimeRange = f'{durationTime.replace(" mins", "")}-{durationInTraffic}'

        with open(f'{self.filePath}current-travel-time.txt', 'w+') as w:
            w.write(travelTimeRange)

        print(f'API Credit Used! - Travel: {travelTimeRange}')
        return(travelTimeRange)

    def gitPushup(self):
        print('Pushing updates to git...')
        os.system(f'sudo bash {e.gitterFilePath}gitPush.sh &')

if __name__ == "__main__":
  e = eReader()
  while True:
    now = dt.now().strftime('%H:%M:%S')
    print(now)
    weekNumber = dt.today().weekday()

    if weekNumber < 5:
        if now > '08:00:00' and now < '08:15:00':
            e.getTravelTime()
            e.update()
            print('Sleeping 900...')
            time.sleep(900)

        elif now > '15:45:00' and now < '16:30:00':
            e.getTravelTime()
            e.update()
            print('Sleeping 500...')
            time.sleep(500)

        else:
            e.update()
            shutil.copyfile(f'{e.filePath}{e.htmlOutputFile}', f'{e.filePath}index.html')

    else:
        pass

    print('Sleeping 150...')
    time.sleep(150)