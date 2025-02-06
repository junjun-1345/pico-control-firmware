import machine
import bluetooth
import json
import gc
import time
import micropython

gc.enable()
gc.collect()

class BLEDevice:
    def __init__(self):
        # 内蔵LED（接続状況表示用）
        self.led = machine.Pin('LED', machine.Pin.OUT)
        
        # ピン管理用の辞書（初期状態は空）
        self.digital_outputs = {}
        self.digital_inputs = {}
        self.analog_inputs = {}
        
        # BLE の初期化
        self.ble = bluetooth.BLE()
        self.ble.active(True)
        self.conn_handle = None  # BLE接続ハンドル
        
        # BLEサービスの設定（後で read_pins() で全ピン状態を動的に参照）
        self._setup_service()
        self.start_advertising()
        
        # BLE IRQ ハンドラの登録
        self.ble.irq(self.ble_irq)
        self.last_notification = time.time()
    
    # ピン追加用の関数
    def add_digital_output(self, name, pin_number, mode):
      self.digital_outputs[name] = {
        "pin": machine.Pin(pin_number, mode),
        "gp": pin_number,
    }

    def add_digital_input(self, name, pin_number, mode, pull=None):
        if pull is None:
            pin_obj = machine.Pin(pin_number, mode)
        else:
            pin_obj = machine.Pin(pin_number, mode, pull)
        self.digital_inputs[name] = {
            "pin": pin_obj,
            "gp": pin_number,
        }
        # 入力状態の変化を検知するため、IRQ を設定
        pin_obj.irq(trigger=machine.Pin.IRQ_FALLING | machine.Pin.IRQ_RISING,
                    handler=self.input_irq)

    def add_analog_input(self, name, pin_number):
        self.analog_inputs[name] = {
            "adc": machine.ADC(pin_number),
            "gp": pin_number,
        }

    
    def _setup_service(self):
        # サービスとキャラクタリスティックの UUID（16bit形式）
        service_uuid = bluetooth.UUID(0x1234)
        char_uuid    = bluetooth.UUID(0x5678)
        self.service = (
            service_uuid,
            ((char_uuid, bluetooth.FLAG_READ | bluetooth.FLAG_WRITE | bluetooth.FLAG_NOTIFY),),
        )
        self.handles = self.ble.gatts_register_services((self.service,))
        # 初期状態のデータを書き込み
        initial_data = {
            'status': 'ready',
            'data': self.read_pins()
        }
        self.ble.gatts_write(self.handles[0][0], json.dumps(initial_data).encode())
    
    def start_advertising(self):
        name = "Pico-W"
        # アドバタイジングデータの作成
        adv_data = (b'\x02\x01\x06' +
                    bytes([len(name) + 1, 0x09]) +
                    name.encode() +
                    b'\x03\x03\x34\x12')
        print("Advertising started")
        self.ble.gap_advertise(100000, adv_data)
        print("Advertising now...")
    
    def read_pins(self):
    # 全てのピンの状態をまとめて返す
        state = {
            "d": {  # data
                "do": {},  # digital_outputs
                "di": {},  # digital_inputs
                "ai": {}   # analog_inputs
            }
        }
            
        for key, obj in self.digital_outputs.items():
            state["d"]["do"][key] = {
                "v": obj["pin"].value(),  # value
                "g": obj["gp"]            # gp
            }
                
        for key, obj in self.digital_inputs.items():
            state["d"]["di"][key] = {
                "v": obj["pin"].value(),
                "g": obj["gp"]
            }
                
        for key, obj in self.analog_inputs.items():
            state["d"]["ai"][key] = {
                "v": obj["adc"].read_u16(),
                "g": obj["gp"]
            }
                
        return state

    
    def notify(self, conn_handle, data):
        try:
            encoded_data = json.dumps(data).encode()
            print("Sending notification:", encoded_data)
            self.ble.gatts_notify(conn_handle, self.handles[0][0], encoded_data)
        except Exception as e:
            print("notify error:", e)
    
    def handle_write(self, conn_handle, data):
        try:
            msg = json.loads(data.decode())
            cmd = msg.get("c", msg.get("cmd"))  # Support both formats
            
            if cmd in ["s", "set"]:  # Optimized set command
                category_map = {
                    "do": "digital_outputs",
                    "di": "digital_inputs",
                    "ai": "analog_inputs"
                }
                category = category_map.get(msg.get("t")) or msg.get("category")
                pin_key = msg.get("p") or msg.get("pin")
                val = msg.get("v") or msg.get("val")
                
                if category == "digital_outputs" and pin_key in self.digital_outputs:
                    self.digital_outputs[pin_key]["pin"].value(val)
                    self.led.value(val)
                    self.notify(conn_handle, {"s": "ok"})  # Optimized status
                    self.notify(conn_handle, self.read_pins())
                    
            elif cmd in ["r", "read"]:  # Optimized read command
                self.notify(conn_handle, self.read_pins())
                
        except Exception as e:
            print("handle_write error:", e)

    
    def input_irq(self, pin):
        # IRQ 内で重い処理を避け、処理は micropython.schedule で委譲
        micropython.schedule(self.input_handler, 0)
    
    def input_handler(self, dummy):
        current_state = self.read_pins()
        print("Input change detected:", current_state)
        if self.conn_handle is not None:
            self.notify(self.conn_handle, {"data": current_state})
    
    def ble_irq(self, event, data):
        if event == 1:  # 接続時
            conn_handle, _, _ = data
            self.conn_handle = conn_handle
            self.led.value(1)
            self.notify(conn_handle, {"status": "connected"})
            self.notify(conn_handle, {"data": self.read_pins()})
        elif event == 2:  # 切断時
            self.led.value(0)
            self.conn_handle = None
        elif event == 3:  # データ受信時
            conn_handle, value_handle = data
            received = self.ble.gatts_read(value_handle)
            if received:
                self.handle_write(conn_handle, received)
        pass

    def run(self):
        print("BLEDevice running...")
        while True:
            gc.collect()
            if self.conn_handle is not None:
                if time.time() - self.last_notification >= 5:
                    self.notify(self.conn_handle, {"data": self.read_pins()})
                    self.last_notification = time.time()
            time.sleep(1)
        pass

if __name__ == '__main__':
    device = BLEDevice()
    device.run()
