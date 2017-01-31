from machine import I2C, Pin, Timer
import socket
import utime as time
import dht
from bmp180 import BMP180 # https://github.com/micropython-IMU/micropython-bmp180
from esp8266_i2c_lcd import I2cLcd # https://github.com/dhylands/python_lcd/
import clock, nethelper

class WeatherStation:
    DHTPIN = 14 # DHT data pin
    BMPSCL = 5  # BMP I2C clock pin
    BMPSDA = 4  # BMP I2C data pin
    DISSCL = 12 # LCD I2C clock pin
    DISSDA = 13 # LCD I2C data pin
    DEFAULT_LCD_ADDR = 0x27
    DEFAULT_INTERVAL = 10
    MEASURE_TRIES = 3
    SERVER_NAME = 'graphite.example.com' # hostname of your graphite server
    SERVER_PORT = 2003

    def __init__(self):
        self.bmp = None
        self.dht = None
        self.lcd = None
        self.socket = None
        self.online = False
        self.interval = self.DEFAULT_INTERVAL
        self.init_lcd()
        self.init_net()
        self.init_bmp()
        self.init_dht()
        self.init_clock()
        self.init_socket()
        tim = Timer(-1)
        tim.init(period=self.interval*1000, mode=Timer.PERIODIC, callback=self.update)
        self.update(None)

    def update(self, timer):
        print('update')
        self.check_net()
        self.update_clock()
        self.measure()
        self.update_lcd()
        self.send_data()

    def measure(self):
        print('measure')
        tries = self.MEASURE_TRIES
        while tries:
            try:
                self.dht.measure()
            except:
                tries -= 1

    def update_lcd(self):
        print('update_lcd')
        if self.online:
            now = time.localtime()
            time_str = '%02d:%02d' % (now[3], now[4])
        else:
            time_str = 'noNet'
        #self.lcd.clear() # this will cause flicker
        self.lcd.move_to(0, 0) # better to overwrite whole display
        self.lcd.putstr('T: %.1f\xdfC       H: %.0f%%     %s' % (
            self.dht.temperature(),
            self.dht.humidity(),
            time_str
        ))

    def send_data(self):
        print('send_data')
        if not self.socket:
            print('no_socket')
            return
        data = 'weatherstation.temp.dht %.1f\nweatherstation.hum.dht %.0f\nweatherstation.temp.bmp %.1f\nweatherstation.pressure.bmp %.1f\nweatherstation.time %s\n' % (
            self.dht.temperature(),
            self.dht.humidity(),
            self.bmp.temperature,
            self.bmp.pressure,
            self.clock.get_ts()
        )
        try:
            print('writing socket')
            self.socket.write(data)
            print('socket write complete')
        except:
            print('wtite failed')
            self.check_net(recheck=True)
            self.init_socket()

    def init_bmp(self):
        bus =  I2C(scl=Pin(self.BMPSCL), sda=Pin(self.BMPSDA), freq=100000)
        self.bmp = BMP180(bus)

    def init_dht(self):
        self.dht = dht.DHT22(Pin(self.DHTPIN))

    def init_lcd(self):
        i2c = I2C(scl=Pin(self.DISSCL), sda=Pin(self.DISSDA), freq=400000)
        self.lcd = I2cLcd(i2c, self.DEFAULT_LCD_ADDR, 2, 16)

    def init_net(self):
        self.net = nethelper.NetHelper()
        self.net.check()

    def check_net(self, recheck=False):
        info = self.net.check(recheck)
        if info and self.online:
            return True
        elif info and not self.online:
            import utime
            self.online = True
            self.got_online()
            self.lcd.clear()
            self.lcd.putstr('% 16s%s' % (info[1], info[0]))
            utime.sleep_ms(5000)
            self.lcd.clear()
            return True
        elif not info and self.online:
            import utime
            self.online = False
            self.lcd.clear()
            self.lcd.putstr('Reconnecting...')
            utime.sleep_ms(5000)
            self.lcd.clear()
            return False
        elif not info and not self.online:
            return False

    def got_online(self):
        self.init_socket()
        self.init_clock()

    def init_socket(self):
        print('init_socket')
        if self.online and not self.socket:
            addr_info = socket.getaddrinfo(self.SERVER_NAME, self.SERVER_PORT)
            addr = addr_info[0][-1]
            self.socket = socket.socket()
            self.socket.connect(addr)
        elif not self.online:
            self.socket = None

    def init_clock(self):
        self.clock = clock.Clock()

    def update_clock(self):
        if self.online:
            self.clock.sync()
