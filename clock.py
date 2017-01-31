from socket import socket, getaddrinfo, AF_INET, SOCK_DGRAM
import ustruct as struct
import utime as time
from machine import RTC


class Clock():
    NTP_HOST = 'pool.ntp.org' # NTP server to use
    NTP_PORT = 123
    TZ_OFFSET = 3600 # timezone (UTC+1)
    LEAP_SECONDS = 27 # TODO get this from NTP response
    MAX_AGE = 600 # how often to sync clock (in seconds)
    NTP_PACKET_FORMAT = "!12I"
    NTP_DELTA = 2208988800 # reference time (in seconds since 1900-01-01 00:00:00)
    NTP_QUERY = '\x1b' + 47 * '\0'
    NTP_BUFFSIZE = 64
    EPOCH = 946684800 # seconds from 1970-01-01 00:00:00 UTC to 2000-01-01 00:00:00 UTC

    def __init__(self):
        self.ntp_host = self.NTP_HOST
        self.tz_offset = self.TZ_OFFSET
        self.clock_max_age = self.MAX_AGE
        self.clock_set = False
        self.clock_last_set = 0

    def get_ntp(self):
        addr_info = getaddrinfo(self.NTP_HOST, self.NTP_PORT)
        addr = addr_info[0][-1]
        s = socket(AF_INET, SOCK_DGRAM)
        s.sendto(self.NTP_QUERY, addr)
        msg, address = s.recvfrom(self.NTP_BUFFSIZE)
        s.close()
        unpacked = struct.unpack(self.NTP_PACKET_FORMAT, msg[0:struct.calcsize(self.NTP_PACKET_FORMAT)])
        # this won't work right on nodemcu - not enough bits for int ot something like that
        #ts = unpacked[10] + float(unpacked[11]) / 2**32 - NTP_DELTA
        # this will be good enough
        ts = unpacked[10] - self.NTP_DELTA
        return ts

    def get_ntp_epoch(self):
        return self.get_ntp() - self.EPOCH - self.LEAP_SECONDS

    def set_time(self):
        now = time.localtime(self.get_ntp_epoch() + self.tz_offset)
        RTC().datetime(now[:3]+(now[6],)+now[3:6]+(0,)) # some strange workarounds

    def get_ts(self):
        return time.mktime(time.localtime()) + self.EPOCH + self.LEAP_SECONDS - self.tz_offset

    def sync(self):
        if not self.clock_set or time.ticks_diff(time.ticks_ms(), self.clock_last_set) > (self.clock_max_age*1000):
            self.set_time()
            print('clock sync')
            self.clock_set = True
            self.clock_last_set = time.ticks_ms()
