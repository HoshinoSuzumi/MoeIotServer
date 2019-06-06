import json
import time
import random
import dht11
import RPi.GPIO as GPIO
from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket

ACTIONS = ['get', 'set', 'ping']
DHT_HOLDER = dht11.DHT11(pin=1)

last_read = 0
curr_temp = 0
curr_humi = 0
switchs = [6, 13, 19, 26]
sw_state = [0, 0, 0, 0]

# initialize GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.cleanup()

GPIO.setup(switchs, GPIO.OUT)
GPIO.output(switchs, 1)


def parse_request(bundle):
    try:
        result = json.loads(bundle, encoding='utf-8')
    except Exception:
        result = None
    return result


def make_response(type, errno, msg, data=None, str_mode=False):
    response = {
        'type': str(type),
        'error': errno,
        'msg': msg,
        'data': '' if data is None else data
    }
    return str(json.dumps(response)) if str_mode else json.dumps(response)


def do_action(inst, bundle):
    global curr_temp, curr_humi, last_read
    action = None
    data = None
    try:
        action = bundle['action']
        data = bundle['data']
    except Exception as e:
        inst.sendMessage(make_response('common', -1, 'Bad request'))
    if action is not None:
        if action not in ACTIONS:
            inst.sendMessage(make_response('common', -1, 'Unknown action'))
        else:
            try:
                if action == 'get':
                    if (int(time.time()) - last_read) >= 2:
                        dhtdata = DHT_HOLDER.read()
                        if dhtdata.is_valid():
                            last_read = int(time.time())
                            curr_temp = dhtdata.temperature
                            curr_humi = dhtdata.humidity
                    if data['type'] == 'temp':
                        inst.sendMessage(make_response('temp', 0, 'success', {
                            'id:': 1,
                            'updated': last_read,
                            'value': curr_temp
                        }))
                    elif data['type'] == 'humi':
                        inst.sendMessage(make_response('humi', 0, 'success', {
                            'id:': 1,
                            'updated': last_read,
                            'value': curr_humi
                        }))
                    elif data['type'] == 'swstate':
                        inst.sendMessage(make_response('swstate', 0, 'success', sw_state))
                    else:
                        inst.sendMessage(make_response('common', -1, 'Unknown sensor'))
                elif action == 'set':
                    index = (int(data['id']) - 1)
                    sw_state[index] = int(data['state'])

                    pin = switchs[index]
                    state = 0 if sw_state[index] == 1 else 1

                    GPIO.output(pin, state)
                    print('Pin: %s | State: %s' % (pin, state))
                    inst.sendMessage(make_response('set', 0, 'success'))
                elif action == 'ping':
                    inst.sendMessage(make_response('pong', 0, 'pong'))
            except Exception:
                inst.sendMessage(make_response('common', -1, 'Argument error'))


class CoreServer(WebSocket):

    def handleMessage(self):
        data = parse_request(self.data)
        if data is None:
            self.sendMessage(make_response('common', -1, 'Invalid request'))
        else:
            do_action(self, data)

    def handleConnected(self):
        print(self.address, 'connected')

    def handleClose(self):
        print(self.address, 'closed')


if __name__ == '__main__':
    print('Initializing...')
    server = SimpleWebSocketServer('0.0.0.0', 18770, CoreServer)
    time.sleep(0.5)
    print('Server is listening...')
    server.serveforever()
