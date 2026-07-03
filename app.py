# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '/bigdata/server/spark-3.0.0-bin-without-hadoop/python')
sys.path.insert(0, '/bigdata/server/spark-3.0.0-bin-without-hadoop/python/lib/py4j-0.10.9-src.zip')

from flask import Flask, jsonify, send_from_directory
from pyspark.sql import SparkSession
from collections import defaultdict
import threading
import time
from datetime import datetime

app = Flask(__name__, static_folder='/bigdata/data')

spark = SparkSession.builder \
    .appName("FishMonitor") \
    .config("spark.cleaner.referenceTracking.blocking", "false") \
    .config("spark.sql.adaptive.enabled", "false") \
    .enableHiveSupport() \
    .getOrCreate()

TABLE = "ocean_ais.ais_trajectory_cleaned"

# ========== 全量数据加载到内存 ==========
all_data = []
current_index = 0
total_rows = 9896
lock = threading.Lock()

def load_all_data():
    global all_data, total_rows
    print("🔄 正在从 Hive 加载全部数据...")
    # 注意：字段 direction 替代 heading
    df = spark.sql(f"SELECT vessel_id, x, y, speed, direction, record_time, operation_type, sea_area, dt FROM {TABLE} ORDER BY record_time")
    rows = df.collect()
    processed = []
    for r in rows:
        try:
            rt = datetime.strptime(r['record_time'], '%Y-%m-%d %H:%M:%S')
        except:
            rt = r['record_time']
        processed.append((
            r['vessel_id'], r['x'], r['y'], r['speed'],
            r['direction'], rt, r['operation_type'],
            r['sea_area'], r['dt']
        ))
    all_data = processed
    total_rows = len(all_data)
    print(f"✅ 加载 {total_rows} 条记录，时间范围: {all_data[0][5]} ~ {all_data[-1][5]}")

# 启动时加载
load_all_data()

def get_current_data():
    with lock:
        return all_data[:current_index]

def advance_data():
    global current_index
    with lock:
        if current_index < total_rows:
            current_index = min(current_index + 50, total_rows)
        return current_index

# 初始给 50 条
advance_data()

def auto_advance():
    while True:
        time.sleep(2)
        advance_data()

threading.Thread(target=auto_advance, daemon=True).start()

@app.route('/')
def index():
    return send_from_directory('/bigdata/data', '08_dashboard_real.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory('/bigdata/data', filename)

@app.route('/api/realtime/status')
def status():
    return jsonify({"current": current_index, "total": total_rows})

# ==================== 所有接口基于内存实时计算 ====================
@app.route('/api/realtime/summary')
def summary():
    data = get_current_data()
    n = len(data)
    if n == 0:
        return jsonify({"total_points":0,"total_ships":0,"avg_speed":0,"hot_grid_count":0,"abnormal_count":0})
    ships=set(); speeds=[]; grids=set(); tmp={}
    for row in data:
        ships.add(row[0]); speeds.append(row[3])
        x,y=row[1],row[2]
        if x is not None and y is not None and x!=0 and y!=0:
            grids.add((int(x//10)*10, int(y//10)*10))
        if row[3] < 3.0:
            key=(row[0], row[7] if row[7] else '未知')
            tmp[key]=tmp.get(key,0)+1
    abnormal=sum(1 for v in tmp.values() if v>=2)
    avg_spd=round(sum(speeds)/len(speeds),1) if speeds else 0
    return jsonify({
        "total_points":n,"total_ships":len(ships),
        "avg_speed":avg_spd,"hot_grid_count":len(grids),
        "abnormal_count":abnormal
    })

@app.route('/api/realtime/sea-grid-heatmap')
def h1():
    data=get_current_data()
    g={}
    for row in data:
        x,y=row[1],row[2]
        if x is not None and y is not None and x!=0 and y!=0:
            key=(int(x//10)*10, int(y//10)*10)
            if key not in g: g[key]=set()
            g[key].add(row[0])
    return jsonify([{"x":k[0],"y":k[1],"ship_cnt":len(v)} for k,v in g.items()])

@app.route('/api/realtime/worktype-ratio')
def h2():
    data=get_current_data()
    d={}
    for row in data:
        wt=row[6] if row[6] else '未知'
        d[wt]=d.get(wt,0)+1
    return jsonify([{"name":k,"value":v} for k,v in d.items()])

@app.route('/api/realtime/peak-hour')
def h3():
    data=get_current_data()
    d={}
    for row in data:
        t=row[5]
        if isinstance(t,datetime): h=t.hour
        else:
            try: h=int(str(t)[11:13])
            except: continue
        d[h]=d.get(h,0)+1
    return jsonify({"hours":[str(h) for h in sorted(d)],"values":[d[h] for h in sorted(d)]})

@app.route('/api/static/work-duration-dist')
def h4():
    data=get_current_data()
    ship_day={}
    for row in data:
        t=row[5]
        if not t: continue
        dt_str=t.strftime('%Y-%m-%d') if isinstance(t,datetime) else str(t)[:10]
        sid=row[0]
        key=(sid,dt_str)
        if key not in ship_day: ship_day[key]={'min':t,'max':t}
        else:
            if t<ship_day[key]['min']: ship_day[key]['min']=t
            if t>ship_day[key]['max']: ship_day[key]['max']=t
    buckets={'0-2小时':0,'2-4小时':0,'4-6小时':0,'6-8小时':0,'8-10小时':0,'10小时以上':0}
    for k,v in ship_day.items():
        if isinstance(v['min'],datetime): dur=(v['max']-v['min']).total_seconds()/3600
        else:
            try:
                t1=datetime.strptime(str(v['min']),'%Y-%m-%d %H:%M:%S')
                t2=datetime.strptime(str(v['max']),'%Y-%m-%d %H:%M:%S')
                dur=(t2-t1).total_seconds()/3600
            except: continue
        if dur<=2: buckets['0-2小时']+=1
        elif dur<=4: buckets['2-4小时']+=1
        elif dur<=6: buckets['4-6小时']+=1
        elif dur<=8: buckets['6-8小时']+=1
        elif dur<=10: buckets['8-10小时']+=1
        else: buckets['10小时以上']+=1
    labels=["0-2小时","2-4小时","4-6小时","6-8小时","8-10小时","10小时以上"]
    return jsonify({"ranges":labels,"values":[buckets[l] for l in labels]})

@app.route('/api/realtime/ship-top20')
def h5():
    data=get_current_data()
    d={}
    for row in data: d[row[0]]=d.get(row[0],0)+1
    sorted_ships=sorted(d.items(),key=lambda x:x[1],reverse=True)[:20]
    return jsonify({"ships":[s[0] for s in sorted_ships],"values":[s[1] for s in sorted_ships]})

@app.route('/api/realtime/avg-speed')
def h6():
    data=get_current_data()
    d={}
    for row in data:
        wt=row[6] if row[6] else '未知'
        if wt not in d: d[wt]=[]
        d[wt].append(row[3])
    types,vals=[],[]
    for k,v in d.items(): types.append(k); vals.append(round(sum(v)/len(v),2))
    pairs=sorted(zip(types,vals),key=lambda x:x[1],reverse=True)
    return jsonify({"types":[p[0] for p in pairs],"values":[p[1] for p in pairs]})

@app.route('/api/realtime/daily-points')
def h7():
    data=get_current_data()
    d={}
    for row in data:
        t=row[5]
        dt_str=t.strftime('%Y-%m-%d') if isinstance(t,datetime) else str(t)[:10]
        d[dt_str]=d.get(dt_str,0)+1
    sorted_dates=sorted(d.items(),key=lambda x:x[0])
    if len(sorted_dates)>7: sorted_dates=sorted_dates[-7:]
    return jsonify({"dates":[x[0] for x in sorted_dates],"values":[x[1] for x in sorted_dates]})

@app.route('/api/static/max-distance-top20')
def h8():
    data=get_current_data()
    ship_day={}
    for row in data:
        sid=row[0]; t=row[5]; x,y=row[1],row[2]
        if x is None or y is None: continue
        dt_str=t.strftime('%Y-%m-%d') if isinstance(t,datetime) else str(t)[:10]
        key=(sid,dt_str)
        if key not in ship_day: ship_day[key]={'start_x':x,'start_y':y,'max_dist':0.0}
        else:
            dist=((x-ship_day[key]['start_x'])**2+(y-ship_day[key]['start_y'])**2)**0.5
            if dist>ship_day[key]['max_dist']: ship_day[key]['max_dist']=dist
    sorted_result=sorted(ship_day.items(),key=lambda x:x[1]['max_dist'],reverse=True)[:20]
    ships=[f"{k[0]}({k[1]})" for k,v in sorted_result]
    values=[round(v['max_dist'],2) for k,v in sorted_result]
    return jsonify({"ships":ships,"values":values})

# ---------- 异常停泊点（添加 time 字段） ----------
@app.route('/api/realtime/abnormal-stop-points')
def h9():
    data = get_current_data()
    tmp = {}
    for row in data:
        if row[3] < 3.0:
            area = row[7] if row[7] else '未知'
            key = (row[0], area)
            if key not in tmp:
                tmp[key] = {'cnt': 0, 'xs': [], 'ys': []}
            tmp[key]['cnt'] += 1
            x, y = row[1], row[2]
            if x is not None and y is not None:
                tmp[key]['xs'].append(x); tmp[key]['ys'].append(y)
    result = []
    for (ship, area), v in tmp.items():
        if v['cnt'] >= 2:
            avg_x = sum(v['xs'])/len(v['xs']) if v['xs'] else 0
            avg_y = sum(v['ys'])/len(v['ys']) if v['ys'] else 0
            result.append({"ship_id": ship, "sea_area": area, "x": round(avg_x,2), "y": round(avg_y,2), "cnt": v['cnt']})
    result.sort(key=lambda x: x["cnt"], reverse=True)
    # 添加当前数据的最新时间作为所有异常点的统一时间
    if data:
        latest_time = str(max(row[5] for row in data))
        for item in result:
            item["time"] = latest_time
    return jsonify(result[:30])

@app.route('/api/realtime/cross-border')
def h10():
    data = get_current_data()
    result = []
    for row in data:
        x, y = row[1], row[2]
        if x is None or y is None or x == 0 or y == 0: continue
        area = row[7] or '未知'
        if (area == '渤海湾' and (x < 100 or x > 200 or y < 320 or y > 400)) or \
           (area == '黄海中部' and (x < 200 or x > 300 or y < 250 or y > 380)) or \
           (area == '东海近海' and (x < 300 or x > 450 or y < 150 or y > 320)) or \
           (area == '舟山群岛' and (x < 350 or x > 450 or y < 100 or y > 250)) or \
           (area == '南海北部' and (x < 400 or x > 600 or y < 0 or y > 200)):
            result.append({"ship_id": row[0], "sea_area": area, "x": x, "y": y, "time": str(row[5])})
    return jsonify(result[:500])

@app.route('/api/realtime/ship-locations')
def loc():
    data = get_current_data()
    latest = {}
    for row in data:
        sid = row[0]; t = row[5]
        if sid not in latest or t > latest[sid][5]:
            latest[sid] = row
    result = []
    for row in latest.values():
        result.append({
            "ship_id": row[0],
            "x": row[1] if row[1] else 0,
            "y": row[2] if row[2] else 0,
            "work_type": row[6] if row[6] else "未知",
            "sea_area": row[7] if row[7] else "未知"
        })
    return jsonify(result[:500])

@app.route('/api/realtime/latest-boats')
def lb():
    data = get_current_data()
    latest = {}
    for row in data:
        sid = row[0]; t = row[5]
        if sid not in latest or t > latest[sid][5]:
            latest[sid] = row
    sorted_latest = sorted(latest.values(), key=lambda x: x[5], reverse=True)
    result = []
    for row in sorted_latest:
        result.append({
            "ship": row[0],
            "area": row[7] if row[7] else "未知",
            "speed": round(row[3], 1) if row[3] else 0,
            "status": "作业中" if (row[3] or 0) > 5 else "返港中",
            "time": str(row[5])
        })
    return jsonify(result)

print("🌐 Spark 全量加载 + 内存推进模式启动成功")
app.run(host="0.0.0.0", port=5000, debug=False)
