#!/usr/bin/python3
import json

f = open('configs.json',)
configs = json.load(f)
pool_mode = configs["pool_mode"]
from_ = configs["range"]["from"]
to_ = configs["range"]["to"]
ip_block = configs["subnet"]["ip_block"]
subnet_mask = configs["subnet"]["subnet_mask"]
lease_time = configs["lease_time"]
reservation_list = configs["reservation_list"]
black_list = configs["black_list"]

