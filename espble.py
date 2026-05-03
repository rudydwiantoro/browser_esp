import bluetooth
import machine
import time
from micropython import const
import tft_config
import st7789py as st7789
import vga1_16x16 as font

# Konstanta Event Bluetooth
_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)

# UUID harus sama dengan versi Browser
SERVICE_UUID = bluetooth.UUID("4fafc201-1fb5-459e-8fcc-c5c9c331914b")
CHAR_UUID = bluetooth.UUID("beb5483e-36e1-4688-b7f5-ea07361b26a8")
CHAR_PROPS = bluetooth.FLAG_WRITE | bluetooth.FLAG_READ

# AD types
_ADV_TYPE_FLAGS = const(0x01)
_ADV_TYPE_NAME = const(0x09)
_ADV_TYPE_UUID128_COMPLETE = const(0x07)

def center_on(display, using_font, text, y, fg, bg):
    x = (display.width - len(text) * using_font.WIDTH) // 2
    display.text(using_font, text, x, y, fg, bg)

class ESP32_BLE:
    def __init__(self, name="Vi-Em Vending"):
        self.ble = bluetooth.BLE()
        self.ble.active(True)
        self.ble.irq(self.ble_irq)
        
        # Register Service & Characteristic
        service = (SERVICE_UUID, ((CHAR_UUID, CHAR_PROPS),),)
        ((self.handle,),) = self.ble.gatts_register_services((service,))
        
        # Mulai Advertising
        self.name = name
        self.setup_display()
        self.advertise()

    def setup_display(self):
        self.tft = tft_config.config(tft_config.WIDE)
        self.tft.rotation(3)
        self.show_status("READY", st7789.YELLOW, st7789.BLACK)

    def show_status(self, text, fg, bg):
        self.tft.fill(bg)
        y = self.tft.height // 2 - font.HEIGHT // 2
        center_on(self.tft, font, text, y, fg, bg)

    def ble_irq(self, event, data):
        if event == _IRQ_CENTRAL_CONNECT:
            print("Browser Terhubung!")
            self.show_status("CONNECTED", st7789.CYAN, st7789.BLACK)
        elif event == _IRQ_CENTRAL_DISCONNECT:
            print("Browser Terputus. Advertising ulang...")
            self.show_status("DISCONNECT", st7789.MAGENTA, st7789.BLACK)
            self.advertise()
        elif event == _IRQ_GATTS_WRITE:
            conn_handle, value_handle = data
            if value_handle == self.handle:
                # Baca data yang dikirim browser
                msg = self.ble.gatts_read(self.handle)
                self.process_command(msg)

    def process_command(self, msg):
        if not msg:
            return

        # Mode kompatibel lama: Uint8Array([0..3]).
        if len(msg) == 1:
            command = msg[0]
            if command == 1:
                print("Perintah Diterima: ON")
                self.show_status("ON", st7789.GREEN, st7789.BLACK)
            elif command == 0:
                print("Perintah Diterima: OFF")
                self.show_status("OFF", st7789.RED, st7789.BLACK)
            elif command == 2:
                print("Perintah Diterima: BLINK")
                self.blink_status()
            elif command == 3:
                print("Perintah Diterima: CLEAR")
                self.show_status("", st7789.WHITE, st7789.BLACK)
            return

        # Mode teks baru: "ON", "OFF", "BLINK", "CLEAR", "TXT:pesan"
        try:
            text = msg.decode().strip()
        except Exception:
            print("Format command tidak dikenal:", msg)
            return

        upper_text = text.upper()
        if upper_text == "ON":
            self.show_status("ON", st7789.GREEN, st7789.BLACK)
        elif upper_text == "OFF":
            self.show_status("OFF", st7789.RED, st7789.BLACK)
        elif upper_text == "BLINK":
            self.blink_status()
        elif upper_text == "CLEAR":
            self.show_status("", st7789.WHITE, st7789.BLACK)
        elif upper_text.startswith("TXT:"):
            custom = text[4:].strip()
            if not custom:
                custom = "-"
            self.show_status(custom[:18], st7789.WHITE, st7789.BLACK)
        else:
            print("Command teks tidak dikenal:", text)

    def blink_status(self):
        for _ in range(3):
            self.show_status("BLINK", st7789.YELLOW, st7789.BLACK)
            time.sleep_ms(250)
            self.show_status("", st7789.WHITE, st7789.BLACK)
            time.sleep_ms(150)
        self.show_status("BLINK", st7789.YELLOW, st7789.BLACK)

    def advertise(self):
        # Total 1 paket advertising maksimal 31 byte.
        # UUID 128-bit (18 byte inkl. header) + flags (3 byte) + nama bisa overflow.
        # Solusi: taruh UUID di adv_data, nama di scan response (resp_data).
        adv_data = bytearray()
        adv_data += bytes([2, _ADV_TYPE_FLAGS, 0x06])
        service_uuid = bytes(SERVICE_UUID)
        adv_data += bytes([len(service_uuid) + 1, _ADV_TYPE_UUID128_COMPLETE]) + service_uuid

        resp_data = bytearray()
        name_bytes = self.name.encode()
        max_name_len = 29  # 31 - (len + type)
        if len(name_bytes) > max_name_len:
            name_bytes = name_bytes[:max_name_len]
        resp_data += bytes([len(name_bytes) + 1, _ADV_TYPE_NAME]) + name_bytes

        # MicroPython memakai microseconds. 100_000 us = 100 ms.
        self.ble.gap_advertise(100_000, adv_data=adv_data, resp_data=resp_data)

# Inisialisasi
ble_vending = ESP32_BLE()
print("Menunggu perintah dari browser...")
