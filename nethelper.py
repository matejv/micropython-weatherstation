import webrepl
import network

NETWORKS = (
    ('my-wifi-ssid', 'my-widi-password'),
    ('second-wifi-ssid', 'second-wifi-password'),
)
AP_CONFIG = {'essid':'weatherstation', 'password':'rescueme!!!'}


class NetHelper():
    def __init__(self):
        self.networks = NETWORKS
        self.ap_config = AP_CONFIG
        self.current_network_idx = None
        self.ap = network.WLAN(network.AP_IF)
        self.wlan = network.WLAN(network.STA_IF)
        self.info = ()
        webrepl.start()

    def ap_on(self):
        if self.ap.active():
            return
        self.ap.active(True)
        if self.ap_config:
            self.ap.config(**self.ap_config)

    def ap_off(self):
        if self.ap.active():
            self.ap.active(False)

    def try_connect(self):
        if self.current_network_idx is None:
            self.current_network_idx = 0
        else:
            self.current_network_idx += 1
        if self.current_network_idx >= len(self.networks):
            self.current_network_idx = 0
        net_config = self.networks[self.current_network_idx]
        print('trying %s' % net_config[0])
        self.wlan.connect(*net_config)

    def check(self, recheck=False):
        if self.info and not recheck:
            return self.info
        self.info = ()
        status = self.wlan.status()
        print('NETSTATUS: %d' % status)
        if status == 5: # STAT_GOT_IP
            if self.current_network_idx is None or self.current_network_idx >= len(self.networks):
                essid = 'UNKNOWN'
            else:
                essid = self.networks[self.current_network_idx][0]
            self.info = (essid, self.wlan.ifconfig()[0])
            self.ap_off()
            return self.info
        elif status in [4, 3, 2, 0]: # [STAT_CONNECT_FAIL, STAT_NO_AP_FOUND, STAT_WRONG_PASSWORD, STAT_IDLE]
            self.ap_on()
            self.try_connect()
            return None
        elif status == 1: # STAT_CONNECTING
            self.ap_on()
            return None
        else:
            self.ap_on()
            self.try_connect()
            return None
