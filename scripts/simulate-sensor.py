"""
Simulador de sensor.
Publica leituras periódicas para o tópico MQTT que o IoT Agent JSON espera:
  /json/<apikey>/<device_id>/attrs

Uso:
    pip install paho-mqtt --break-system-packages
    python3 simulate-sensor.py --host localhost --count 5 --interval 5
"""
import argparse
import json
import random
import time

import paho.mqtt.client as mqtt

APIKEY = "sc2026json01"
DEVICE_ID = "sim-room-101"
TOPIC = f"/json/{APIKEY}/{DEVICE_ID}/attrs"


def generate_reading():
    return {
        "t": round(random.uniform(20.0, 26.0), 1),   # temperatura (°C) - BME280
        "h": round(random.uniform(35.0, 60.0), 1),   # humidade (%) - BME280
        "p": round(random.uniform(1005.0, 1020.0), 1),  # pressão (hPa) - BME280
        "c": round(random.uniform(400.0, 900.0), 0),    # CO2 aprox. (ppm) - MQ135
    }


def main():
    parser = argparse.ArgumentParser(description="Simulador de sensor indoor via MQTT")
    parser.add_argument("--host", default="localhost", help="Hostname do broker MQTT")
    parser.add_argument("--port", type=int, default=1883, help="Porta do broker MQTT")
    parser.add_argument("--count", type=int, default=5, help="Número de leituras a enviar")
    parser.add_argument("--interval", type=float, default=5.0, help="Segundos entre leituras")
    args = parser.parse_args()

    client = mqtt.Client()
    client.connect(args.host, args.port, keepalive=30)
    client.loop_start()

    print(f"A publicar em {TOPIC} no broker {args.host}:{args.port}")
    for i in range(args.count):
        reading = generate_reading()
        payload = json.dumps(reading)
        client.publish(TOPIC, payload)
        print(f"[{i + 1}/{args.count}] -> {payload}")
        time.sleep(args.interval)

    client.loop_stop()
    client.disconnect()


if __name__ == "__main__":
    main()
