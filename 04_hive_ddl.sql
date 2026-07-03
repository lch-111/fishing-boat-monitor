-- ============================================
-- 04_hive_ddl.sql
-- Hive数据库与基础表创建脚本
-- 作用：创建数据库、原始数据外部表、清洗后分区表
-- 执行方式：hive -f 04_hive_ddl.sql
-- 注意：数据清洗逻辑在 02_data_cleaning.sql 中执行
-- ============================================

-- ============================================
-- 步骤1：创建数据库
-- 所有表均存放在 ocean_ais 数据库中
-- ============================================
CREATE DATABASE IF NOT EXISTS ocean_ais;
USE ocean_ais;

-- ============================================
-- 步骤2：创建原始数据外部表
-- 直接映射HDFS上的CSV文件，字段类型全为STRING
-- 避免脏数据导致加载失败，清洗时再做类型转换
-- skip.header.line.count=1 跳过CSV表头行
-- ============================================
DROP TABLE IF EXISTS ais_trajectory_raw;
CREATE EXTERNAL TABLE ais_trajectory_raw (
    vessel_id STRING,
    x STRING,
    y STRING,
    speed STRING,
    direction STRING,
    record_time STRING,
    operation_type STRING,
    sea_area STRING
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION '/ocean/ais/raw'
TBLPROPERTIES ("skip.header.line.count"="1");

-- ============================================
-- 步骤3：创建清洗后数据分区表
-- 字段类型已标准化为数值型和dt型
-- 按dt分区，便于后续按record_time范围高效查询
-- ============================================
DROP TABLE IF EXISTS ais_trajectory_cleaned;
CREATE TABLE ais_trajectory_cleaned (
    vessel_id STRING,
    x DOUBLE,
    y DOUBLE,
    speed FLOAT,
    direction INT,
    record_time STRING,
    operation_type STRING,
    sea_area STRING
)
PARTITIONED BY (dt STRING)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE;

-- ============================================
-- 步骤4：验证表创建成功
-- 查看当前数据库下的所有表
-- ============================================
SHOW TABLES;
