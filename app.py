debug = False

import requests, shutil, time, yaml, os
from datetime import datetime as dt

if os.name != 'nt':
    import board, adafruit_dht

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

    def update(self, display=''):
        if display == 'breaktime':
            shutil.copyfile(f'{self.filePath}breaktime.html', f'{self.filePath}index.html')
            print('Updated display to breaktime.')
        
        elif display == 'stats':
            dashboardHtml = """
    <!DOCTYPE html>
    <html>
    <head>
    <script>
    setInterval(function() {
     window.location.reload();
    }, 300_000);
    </script>
    <style>
    .card {
      /* Add shadows to create the "card" effect */
      box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
      transition: 0.3s;
    }

    /* On mouse-over, add a deeper shadow */
    .card:hover {
      box-shadow: 0 8px 16px 0 rgba(0,0,0,0.2);
    }

    /* Add some padding inside the card container */
    .container {
      padding: 2px 16px;
    }

    .card {
      border: 1px solid #000;
      display: inline-block;
      padding: 10px;
      margin: 5px;
      height: 240px; /*240px*/
      width: 300px;  /*300px*/
    }

    .weatherImg {
      opacity: 0.80;
    }

    </style>
    </head>
    <body>
    <center>
    <div class="card">
        <img src="../images/commute.png" alt="Avatar">
        <div class="container">
          <h8><b>#COMMUTETITLE#</b></h8><br>
          <font size="30"><b>#COMMUTESTATUS#</b></font></h9>
        </div>
    </div>

    <div class="card">
        <img src="../images/ether.png" alt="Avatar">
        <div class="container">
          <h8><b>#ETHERTITLE#</b></h8><br>
          <font size="30"><b>#ETHERPRICE#</b></font></h9>
        </div>
    </div>
    <br>
    <div class="card">
        <img src="../images/warehouse.png" alt="Avatar">
        <div class="container">
          <h8><b>#WAREHOUSETITLE#</b></h8></font><br>
          <font size="30"><b>#WAREHOUSETEMP#</b></font><br>
        </div>
    </div>

    <div class="card">
        <!--<img src="thermo.png" alt="Avatar">-->
        <img src="../images/weather.png" alt="Avatar">
        <!--<div class="weatherImg"><img src="#WEATHERICON#" alt="Avatar" width="150" height="150"></div>-->
        <div class="container">
          <h8><b>#OUTSIDETITLE#</b></h8></font><br>
          <font size="30"><b>#OUTSIDETEMP#</b></font><br>
        </div>
    </div>
    <br>
    #TIMESTAMP#
    </center>
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
            #dashboardHtml = dashboardHtml.replace('#WEATHERICON#', weatherIcon)
            dashboardHtml = dashboardHtml.replace('#ETHERTITLE#', cryptoTitle).replace('#ETHERPRICE#', cryptoPrice)
            dashboardHtml = dashboardHtml.replace('#TIMESTAMP#', currentTime)
            
            with open(f'{self.filePath}{self.htmlOutputFile}', 'w+') as html:
              html.write(dashboardHtml)
            
            with open(f'{self.filePath}index.html', 'w+') as html:
                html.write(dashboardHtml)

            print('Updated display to stats.')

        elif display == 'logo':
            shutil.copyfile(f'{self.filePath}logo.html', f'{self.filePath}index.html')
            print('Updated display to logo.')
    
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
        x = 0
        while x < 5: # DHT11 doesn't output stats 100% of the time. Seems to be > 5/1 hit to miss ratio.
            try: # Try catching temp/humid 5x before moving along
                dhtDevice = adafruit_dht.DHT11(board.D4)
                tempC = dhtDevice.temperature
                tempF = round(tempC * (9 / 5) + 32)

                humidity = dhtDevice.humidity
                dhtDevice.exit()

                printString = f'{tempF}*F / {humidity}%'
                print(f'Warehouse Temp: {printString}')
                outputString = f'{tempF}&#176;F / {humidity}%'
                return(outputString)
            
            except:
                x += 1
                dhtDevice.exit()
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

if __name__ == "__main__":
  e = eReader()
  while True:
    now = dt.now().strftime('%H:%M:%S')
    print(now)
    weekNumber = dt.today().weekday()

    if weekNumber < 5:
        if now < '08:00:00':
            e.update(display='logo') 

        elif now > '09:00:00' and now < '09:15:00':
            e.getTravelTime()
            e.update(display='stats')
            os.system(f'bash {e.gitterFilePath}gitter.sh &')
            print('Sleeping 900...')
            if debug != True:
                time.sleep(900)

        #elif now > '10:30:00' and now < '10:45:00':
        #    e.update(display='breaktime')
        #    print('First Break.')

        #elif now > '12:30:00' and now < '13:00:00':
        #    e.update(display='breaktime')
        #    print('Lunch time.')

        #elif now > '14:30:00' and now < '14:45:00':
        #    e.update(display='breaktime')
        #    print('Second Break.')

        elif now > '16:15:00' and now < '17:00:00':
            e.getTravelTime()
            e.update(display='stats')
            print('Sleeping 500...')
            if debug != True:
                time.sleep(500)
        
        #elif now > '17:00:00':
        #    e.update(display='logo')
        
        else:
            e.update(display='stats')
            shutil.copyfile(f'{e.filePath}{e.htmlOutputFile}', f'{e.filePath}index.html')

    else:
        e.update(display='logo')

    if debug == False:
        #print('Sleeping 150...')
        #time.sleep(150)
        os.system(f'bash {e.gitterFilePath}gitter.sh &')
        print('Sleeping 150...')
        time.sleep(150)
    else:
        time.sleep(5)
