from ble_device import BLEDevice
from machine import Pin

# BLEDevice のインスタンス生成
device = BLEDevice()

# 関数でピンのカスタマイズ
# 例: 外部LEDを GP16 で動作させたい場合
device.add_digital_output("LED1", 19, Pin.OUT)
device.add_digital_output("LED2", 20, Pin.OUT)

# 例: ボタン入力用に GP2 を使用する
device.add_digital_input("Button", 16, Pin.IN, Pin.PULL_UP)
# ADC入力は GP26
device.add_analog_input("ADC", 26)

# メインループの開始
device.run()
