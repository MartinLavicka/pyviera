import logging
import socket
import time
import xml.etree.ElementTree as ET

try:
    # Python 3
    from urllib.request import urlopen, Request
    from urllib.parse import urlparse, urljoin
except ImportError:
    # Python 2
    from urllib2 import urlopen, urlparse, Request
    from urlparse import urljoin

LOGGER = logging.getLogger("pyviera")

IFACE = '0.0.0.0'
SSDP_MCAST_ADDR = '239.255.255.250'
SSDP_PORT = 1900
TIME_OUT = 1

COMMANDS = {
    '30s_skip': 'NRC_30S_SKIP-ONOFF',
    'toggle_3d': 'NRC_3D-ONOFF',
    'apps': 'NRC_APPS-ONOFF',
    'aspect': 'NRC_ASPECT-ONOFF',
    'blue': 'NRC_BLUE-ONOFF',
    'cancel': 'NRC_CANCEL-ONOFF',
    'cc': 'NRC_CC-ONOFF',
    'chat_mode': 'NRC_CHAT_MODE-ONOFF',
    'ch_down': 'NRC_CH_DOWN-ONOFF',
    'input': 'NRC_CHG_INPUT-ONOFF',
    'network': 'NRC_CHG_NETWORK-ONOFF',
    'ch_up': 'NRC_CH_UP-ONOFF',
    'num': 'NRC_D{}-ONOFF',
    'diga_control': 'NRC_DIGA_CTL-ONOFF',
    'display': 'NRC_DISP_MODE-ONOFF',
    'down': 'NRC_DOWN-ONOFF',
    'enter': 'NRC_ENTER-ONOFF',
    'guide': 'NRC_EPG-ONOFF',
    'ez_sync': 'NRC_EZ_SYNC-ONOFF',
    'favorite': 'NRC_FAVORITE-ONOFF',
    'fast_forward': 'NRC_FF-ONOFF',
    'game': 'NRC_GAME-ONOFF',
    'green': 'NRC_GREEN-ONOFF',
    '???_1': 'NRC_GUIDE-ONOFF',
    'hold': 'NRC_HOLD-ONOFF',
    'home': 'NRC_HOME-ONOFF',
    'index': 'NRC_INDEX-ONOFF',
    'info': 'NRC_INFO-ONOFF',
    'connect': 'NRC_INTERNET-ONOFF',
    'left': 'NRC_LEFT-ONOFF',
    'menu': 'NRC_MENU-ONOFF',
    'mpx': 'NRC_MPX-ONOFF',
    'mute': 'NRC_MUTE-ONOFF',
    'net_bs': 'NRC_NET_BS-ONOFF',
    'net_cs': 'NRC_NET_CS-ONOFF',
    'net_td': 'NRC_NET_TD-ONOFF',
    'off_timer': 'NRC_OFFTIMER-ONOFF',
    'pause': 'NRC_PAUSE-ONOFF',
    'pictai': 'NRC_PICTAI-ONOFF',
    'play': 'NRC_PLAY-ONOFF',
    'p_nr': 'NRC_P_NR-ONOFF',
    'power': 'NRC_POWER-ONOFF',
    'program': 'NRC_PROG-ONOFF',
    'record': 'NRC_REC-ONOFF',
    'red': 'NRC_RED-ONOFF',
    'return': 'NRC_RETURN-ONOFF',
    'rewind': 'NRC_REW-ONOFF',
    'right': 'NRC_RIGHT-ONOFF',
    'r_screen': 'NRC_R_SCREEN-ONOFF',
    'last_view': 'NRC_R_TUNE-ONOFF',
    'sap': 'NRC_SAP-ONOFF',
    'toggle_sd_card': 'NRC_SD_CARD-ONOFF',
    'skip_next': 'NRC_SKIP_NEXT-ONOFF',
    'skip_prev': 'NRC_SKIP_PREV-ONOFF',
    'split': 'NRC_SPLIT-ONOFF',
    'stop': 'NRC_STOP-ONOFF',
    'subtitles': 'NRC_STTL-ONOFF',
    'option': 'NRC_SUBMENU-ONOFF',
    'surround': 'NRC_SURROUND-ONOFF',
    'swap': 'NRC_SWAP-ONOFF',
    'text': 'NRC_TEXT-ONOFF',
    'tv': 'NRC_TV-ONOFF',
    'up': 'NRC_UP-ONOFF',
    'link': 'NRC_VIERA_LINK-ONOFF',
    'vol_down': 'NRC_VOLDOWN-ONOFF',
    'vol_up': 'NRC_VOLUP-ONOFF',
    'vtools': 'NRC_VTOOLS-ONOFF',
    'yellow': 'NRC_YELLOW-ONOFF',
}


class Viera(object):
    def __init__(self, hostname, control_url, service_type):
        self.hostname = hostname
        self.control_url = control_url
        self.service_type = service_type
        self.throttle = .5
        self.last_called = time.time()

        for name, key in COMMANDS.items():
            if name == 'num':
                setattr(self, name, self.send_num(key))
            else:
                setattr(self, name, self.send_key(key))

    @staticmethod
    def discover():
        LOGGER.info("Looking for TVs")
        sock = Viera.create_socket(IFACE, SSDP_PORT)
        Viera.send_request(sock)
        responses = Viera.receive_responses(sock)
        responses = (r for r in responses if 'Panasonic' in r)
        urls = (Viera.parse_response(r) for r in responses)
        data = ((url, urlopen(url).read()) for url in urls)

        return list((Viera.parse_description(*d) for d in data))

    @staticmethod
    def create_socket(ip_addr, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(TIME_OUT)
        sock.bind((ip_addr, port))

        return sock

    @staticmethod
    def send_request(sock):
        header = 'M-SEARCH * HTTP/1.1'
        fields = (
            ('ST', 'urn:panasonic-com:device:p00RemoteController:1'),
            ('MX', '1'),
            ('MAN', '"ssdp:discover"'),
            ('HOST', '239.255.255.250:1900'),
        )

        packet = '\r\n'.join([header] + [': '.join(pair) for pair in fields]) + '\r\n'
        packet = packet.encode('utf-8')

        LOGGER.debug("Sending to %s:%s:\n%s", SSDP_MCAST_ADDR, SSDP_PORT, packet)
        sock.sendto(packet, (SSDP_MCAST_ADDR, SSDP_PORT))

    @staticmethod
    def receive_responses(sock):
        responses = []
        try:
            while True:
                data = sock.recv(1024)
                data = data.decode('utf-8')
                LOGGER.debug("Received a response:\n%s", data)
                responses.append(data)
        except socket.timeout:
            # Done receiving responses
            LOGGER.debug("Done receiving responses")

        return responses

    @staticmethod
    def parse_response(data):
        for line in data.splitlines():
            parts = line.split(': ')
            if len(parts) > 1 and parts[0] == 'LOCATION':
                return parts[1]

    @staticmethod
    def parse_description(url, data):
        name_space = '{urn:schemas-upnp-org:device-1-0}'
        root = ET.fromstring(data)
        service = root.find('./{ns}device/{ns}serviceList/{ns}service'.format(ns=name_space))

        if service is None:
            raise Exception("No service description was found.")

        service_type = service.find('./{ns}serviceType'.format(ns=name_space)).text
        control_url = urljoin(url, service.find('./{ns}controlURL'.format(ns=name_space)).text)
        hostname = urlparse(url).netloc

        return Viera(hostname, control_url, service_type)

    def send_num(self, key):
        def func(number):
            for digit in str(number):
                self.send_key(key.format(digit))()

        return func

    def send_key(self, key):
        def func():
            time_last_call = time.time() - self.last_called
            if time_last_call < self.throttle:
                LOGGER.debug("Sleeping for %s", self.throttle - time_last_call)
                time.sleep(self.throttle - time_last_call)
                self.last_called = time.time()

            name = 'X_SendKey'
            params = '<X_KeyEvent>{}</X_KeyEvent>'.format(key)

            soap_body = (
                '<?xml version="1.0"?>'
                '<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope"'
                'SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">'
                '<SOAP-ENV:Body>'
                '<m:{name} xmlns:m="{service_type}">'
                '{params}'
                '</m:{name}>'
                '</SOAP-ENV:Body>'
                '</SOAP-ENV:Envelope>'
            ).format(
                name=name,
                service_type=self.service_type,
                params=params
            )

            soap_body = soap_body.encode('utf-8')

            headers = {
                'Host': self.hostname,
                'Content-Length': len(soap_body),
                'Content-Type': 'text/xml',
                'SOAPAction': '"{}#{}"'.format(self.service_type, name),
            }

            LOGGER.info("Sending key %s", key)
            LOGGER.debug("Sending key to %s:\n%s\n%s", self.control_url, headers, soap_body)

            req = Request(self.control_url, soap_body, headers)
            urlopen(req).read()

        return func
