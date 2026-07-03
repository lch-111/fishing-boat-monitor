USE ocean_ais;

-- 指标01 海域渔船密度热力图
DROP TABLE IF EXISTS ads_result001;
CREATE EXTERNAL TABLE ads_result001(sea_area STRING, grid_x INT, grid_y INT, density INT)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ',' LOCATION '/ocean/ais/result/result001';
INSERT INTO ads_result001
SELECT sea_area, CAST(FLOOR(x/10) AS INT), CAST(FLOOR(y/10) AS INT), COUNT(DISTINCT vessel_id)
FROM ais_trajectory_cleaned WHERE x IS NOT NULL AND y IS NOT NULL AND x!=0 AND y!=0
GROUP BY sea_area, CAST(FLOOR(x/10) AS INT), CAST(FLOOR(y/10) AS INT);

-- 指标02 三类渔船数量占比
DROP TABLE IF EXISTS ads_result002;
CREATE EXTERNAL TABLE ads_result002(op_type STRING, cnt INT)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ',' LOCATION '/ocean/ais/result/result002';
INSERT INTO ads_result002 SELECT operation_type, COUNT(DISTINCT vessel_id) FROM ais_trajectory_cleaned GROUP BY operation_type;

-- 指标03 高峰作业时段统计
DROP TABLE IF EXISTS ads_result003;
CREATE EXTERNAL TABLE ads_result003(hour_val INT, cnt INT)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ',' LOCATION '/ocean/ais/result/result003';
INSERT INTO ads_result003 SELECT HOUR(record_time), COUNT(*) FROM ais_trajectory_cleaned GROUP BY HOUR(record_time) ORDER BY hour_val;

-- 指标04 作业时长分布（真实时长）
DROP TABLE IF EXISTS ads_result004;
CREATE EXTERNAL TABLE ads_result004(vessel_id STRING, work_date STRING, work_hours DOUBLE)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ',' LOCATION '/ocean/ais/result/result004';
INSERT INTO ads_result004
SELECT vessel_id, CAST(work_date AS STRING),
    (UNIX_TIMESTAMP(MAX(ts), 'yyyy-MM-dd HH:mm:ss') - 
     UNIX_TIMESTAMP(MIN(ts), 'yyyy-MM-dd HH:mm:ss')) / 3600.0 AS work_hours
FROM (
    SELECT vessel_id, record_time AS ts, TO_DATE(record_time) AS work_date
    FROM ocean_ais.ais_trajectory_cleaned
) t
GROUP BY vessel_id, work_date;

-- 指标05 单船月均出海频次
DROP TABLE IF EXISTS ads_result005;
CREATE EXTERNAL TABLE ads_result005(vessel_id STRING, days_at_sea INT)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ',' LOCATION '/ocean/ais/result/result005';
INSERT INTO ads_result005 SELECT vessel_id, COUNT(DISTINCT TO_DATE(record_time)) FROM ais_trajectory_cleaned GROUP BY vessel_id;

-- 指标06 平均航速对比
DROP TABLE IF EXISTS ads_result006;
CREATE EXTERNAL TABLE ads_result006(op_type STRING, avg_speed DOUBLE, max_speed DOUBLE, min_speed DOUBLE, cnt INT)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ',' LOCATION '/ocean/ais/result/result006';
INSERT INTO ads_result006 SELECT operation_type, ROUND(AVG(speed),2), ROUND(MAX(speed),2), ROUND(MIN(speed),2), COUNT(*) FROM ais_trajectory_cleaned GROUP BY operation_type;

-- 指标07 每日轨迹点数量分布
DROP TABLE IF EXISTS ads_result007;
CREATE EXTERNAL TABLE ads_result007(work_date STRING, cnt INT)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ',' LOCATION '/ocean/ais/result/result007';
INSERT INTO ads_result007 SELECT CAST(TO_DATE(record_time) AS STRING), COUNT(*) FROM ais_trajectory_cleaned GROUP BY TO_DATE(record_time);

-- 指标08 渔船活动范围
DROP TABLE IF EXISTS ads_result008;
CREATE EXTERNAL TABLE ads_result008(vessel_id STRING, max_dist DOUBLE)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ',' LOCATION '/ocean/ais/result/result008';
INSERT INTO ads_result008 SELECT vessel_id, ROUND(MAX(SQRT(POW(x-start_x,2)+POW(y-start_y,2))),2) FROM (SELECT vessel_id,x,y,FIRST_VALUE(x) OVER(PARTITION BY vessel_id ORDER BY record_time) AS start_x,FIRST_VALUE(y) OVER(PARTITION BY vessel_id ORDER BY record_time) AS start_y FROM ais_trajectory_cleaned WHERE x!=0 AND y!=0) t GROUP BY vessel_id;

-- 指标09 异常停留识别（按您之前的逻辑：同船同海域低速点≥2）
DROP TABLE IF EXISTS ads_result009;
CREATE EXTERNAL TABLE ads_result009(
    vessel_id STRING, start_time STRING, end_time STRING,
    duration_hrs DOUBLE, coord_x DOUBLE, coord_y DOUBLE)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ',' LOCATION '/ocean/ais/result/result009';
INSERT INTO ads_result009
SELECT 
    vessel_id,
    '' AS start_time,
    '' AS end_time,
    CAST(cnt AS DOUBLE) AS duration_hrs,
    avg_x AS coord_x,
    avg_y AS coord_y
FROM (
    SELECT 
        vessel_id, 
        COALESCE(sea_area, '未知') AS sea_area,
        COUNT(*) AS cnt,
        AVG(x) AS avg_x,
        AVG(y) AS avg_y
    FROM ais_trajectory_cleaned
    WHERE speed < 3.0
      AND x IS NOT NULL AND y IS NOT NULL
    GROUP BY vessel_id, COALESCE(sea_area, '未知')
    HAVING COUNT(*) >= 2
) t;

-- 指标10 疑似跨界捕捞识别
DROP TABLE IF EXISTS ads_result010;
CREATE EXTERNAL TABLE ads_result010(vessel_id STRING, sea_area STRING, coord_x DOUBLE, coord_y DOUBLE, ts STRING)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ',' LOCATION '/ocean/ais/result/result010';
INSERT INTO ads_result010 SELECT vessel_id, sea_area, x, y, CAST(record_time AS STRING) FROM ais_trajectory_cleaned WHERE x IS NOT NULL AND y IS NOT NULL AND x!=0 AND y!=0 AND ((sea_area='渤海湾' AND (x<100 OR x>200 OR y<320 OR y>400)) OR (sea_area='黄海中部' AND (x<200 OR x>300 OR y<250 OR y>380)) OR (sea_area='东海近海' AND (x<300 OR x>450 OR y<150 OR y>320)) OR (sea_area='舟山群岛' AND (x<350 OR x>450 OR y<100 OR y>250)) OR (sea_area='南海北部' AND (x<400 OR x>600 OR y<0 OR y>200)));
