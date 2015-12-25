# -*- coding: utf-8 -*- 
from kombu import Producer, Connection, Exchange
import time

conn = Connection("amqp://root:passw0rd@192.168.13.45:5672//")
channel = conn.channel()
exchange = Exchange("MR", "topic", channel, durable=True)
sender = Producer(channel, exchange, "MRtest")
for i in range(0, 10000):
    time.sleep(0.0001)
    sender.publish("MRTest"+str(i) ,delivery_mode="transient")