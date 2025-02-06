# Pico BLE Device - Raspberry Pi Pico の BLE GPIO 制御

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)

🚀 **Pico BLE Device** は、Raspberry Pi Pico の GPIO ピンを **BLE（Bluetooth Low Energy）** 経由で制御・監視できるファームウェアです。

---

## 📥 **セットアップ手順**

### **1. 必要なツール**

- **Raspberry Pi Pico W**（BLE 対応）
- **VS Code**（エディタ）
- **Micropico 拡張機能**（VS Code で Pico にアップロード）
- **Python（MicroPython 環境）**

### **2. VS Code に Micropico をインストール**

1. **VS Code を開く**
2. **拡張機能（Extensions）で「Micropico」と検索**
3. **インストールする**

### **3. Raspberry Pi Pico に MicroPython を書き込む**

1. **Pico を BOOTSEL モードで PC に接続**（BOOTSEL ボタンを押しながら USB 接続）
2. [MicroPython UF2 ファイル](https://micropython.org/download/rp2-pico-w/) をダウンロード
3. **Pico にドラッグ＆ドロップ** で書き込み

### **4. `ble_device.py` をアップロード**

1. **該当ファイルを右クリック**
2. **Upload File to Pico を選択**
