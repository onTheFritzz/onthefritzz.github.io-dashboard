import requests, shutil, time, yaml, os
from datetime import datetime as dt
from pyA20.gpio import gpio
from pyA20.gpio import port
from work import dht11

class eReader():
    def __init__(self):
        with open(f'./config.yaml', 'r') as y:
            yml = yaml.safe_load(y)

        self.distanceEndpoint = yml['distanceEndpoint']
        self.noaaEndpoint = yml['noaaEndpoint']
        self.ethEndpoint = yml['ethEndpoint']
        self.htmlOutputFile = yml['htmlOutput']
        self.gitPusher = yml['gitPushFilePath']
        self.dynamicHtml = yml['dynamicHtml']

        if os.name != 'nt':
            self.filePath = yml['linuxFilePath']
        else:
            self.filePath = yml['windowsFilePath']

    def update(self):
        with open(f'{self.dynamicHtml}') as file:
            dashboardHtml = file.read()

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
        os.system(f'sudo bash {e.gitPusher}gitPush.sh &')

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