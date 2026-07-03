#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
渔船北斗轨迹数据生成器
生成模拟的天池"智慧海洋"格式数据
字段：渔船ID, 坐标X, 坐标Y, 速度(节), 方向(度), 时间, 作业类型
"""

import csv
import random
import datetime
import os

# 配置参数
BOAT_COUNT = 200          # 渔船数量
RECORDS_PER_BOAT = 50     # 每条船记录数
OUTPUT_FILE = 'raw_ais_data.csv'

# 海域范围（模拟平面坐标，单位：公里）
AREAS = {
    '渤海湾': {'x_range': (100, 200), 'y_range': (300, 400)},
    '黄海中部': {'x_range': (250, 400), 'y_range': (200, 350)},
    '东海近海': {'x_range': (450, 600), 'y_range': (150, 300)},
    '舟山群岛': {'x_range': (500, 580), 'y_range': (280, 360)},
    '南海北部': {'x_range': (300, 500), 'y_range': (50, 180)},
}

BOAT_TYPES = ['拖网', '围网', '流刺网']
BOAT_PREFIXES = ['鲁渔', '浙渔', '闽渔', '粤渔', '苏渔']

def generate_boat_id():
    prefix = random.choice(BOAT_PREFIXES)
    return f"{prefix}{random.randint(1000, 9999)}"

def generate_records_for_boat(boat_id, boat_type, area_name, base_date):
    records = []
    area = AREAS[area_name]

    # 起始位置（浮点数，内部状态）
    current_x = random.uniform(area['x_range'][0] + 20, area['x_range'][1] - 20)
    current_y = random.uniform(area['y_range'][0] + 20, area['y_range'][1] - 20)

    for i in range(RECORDS_PER_BOAT):
        # 时间：当天 04:00 ~ 20:00
        minutes = 4 * 60 + i * 30 + random.randint(-5, 5)
        if minutes > 20 * 60:
            minutes = 20 * 60
        dt = base_date + datetime.timedelta(minutes=minutes)
        time_str = dt.strftime('%Y-%m-%d %H:%M:%S')

        # 速度：拖网慢(2-6节)，围网快(8-15节)，流刺网中等(4-10节)
        if boat_type == '拖网':
            speed = random.uniform(2, 6)
        elif boat_type == '围网':
            speed = random.uniform(8, 15)
        else:  # 流刺网
            speed = random.uniform(4, 10)

        # 偶尔产生异常值（用于清洗教学）
        if random.random() < 0.02:  # 2%异常
            speed = random.uniform(25, 40)  # 异常高速

        # 位置漂移（每次都要更新，保持内部状态为浮点数）
        dx = random.uniform(-3, 3)
        dy = random.uniform(-3, 3)
        current_x += dx
        current_y += dy
        # 保持在海域内
        current_x = max(area['x_range'][0], min(area['x_range'][1], current_x))
        current_y = max(area['y_range'][0], min(area['y_range'][1], current_y))

        # 决定当前记录是否缺失坐标（只影响输出值）
        if random.random() < 0.01:  # 1%缺失坐标
            out_x = ''
            out_y = ''
        else:
            out_x = round(current_x, 2)
            out_y = round(current_y, 2)

        direction = random.randint(0, 359)

        records.append({
            '渔船ID': boat_id,
            '坐标X': out_x,
            '坐标Y': out_y,
            '速度': round(speed, 1),
            '方向': direction,
            '时间': time_str,
            '作业类型': boat_type,
            '海域': area_name
        })

    return records

def main():
    all_records = []
    base_date = datetime.datetime(2025, 6, 1)

    # 为每条船生成数据
    for i in range(BOAT_COUNT):
        boat_id = generate_boat_id()
        boat_type = random.choice(BOAT_TYPES)
        area_name = random.choice(list(AREAS.keys()))

        # 每条船不同日期（模拟一个月数据）
        day_offset = random.randint(0, 29)
        boat_date = base_date + datetime.timedelta(days=day_offset)

        records = generate_records_for_boat(boat_id, boat_type, area_name, boat_date)
        all_records.extend(records)

    # 写入CSV
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['渔船ID', '坐标X', '坐标Y', '速度', '方向', '时间', '作业类型', '海域'])
        writer.writeheader()
        writer.writerows(all_records)

    print(f"数据生成完成：{OUTPUT_FILE}")
    print(f"总记录数：{len(all_records)}")
    print(f"渔船数量：{BOAT_COUNT}")
    print(f"数据预览（前3条）：")
    for r in all_records[:3]:
        print(r)

if __name__ == '__main__':
    main()