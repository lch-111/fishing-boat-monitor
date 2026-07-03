#!/bin/bash
# ============================================
# 03_hdfs_operations.sh
# HDFS目录创建与数据上传脚本
# 作用：建立项目所需的HDFS目录结构，上传原始CSV数据
# 执行方式：bash 03_hdfs_operations.sh
# ============================================

HDFS_BASE="/ocean/ais"

# ============================================
# 步骤1：创建HDFS原始数据目录
# 用于存放从天池数据集下载的原始CSV文件
# ============================================
echo "=== 创建HDFS原始数据目录 ==="
hdfs dfs -mkdir -p ${HDFS_BASE}/raw
echo "创建 ${HDFS_BASE}/raw 完成"

# ============================================
# 步骤2：创建HDFS清洗后数据目录（可选）
# 如果清洗后数据通过SQL直接写入Hive表，此目录可省略
# 此处预留，用于存放SQL清洗后的中间文件
# ============================================
echo "=== 创建HDFS清洗数据目录 ==="
hdfs dfs -mkdir -p ${HDFS_BASE}/cleaned
echo "创建 ${HDFS_BASE}/cleaned 完成"

# ============================================
# 步骤3：创建HDFS分析结果输出目录
# 用于存放Spark SQL分析后的结果文件
# ============================================
echo "=== 创建HDFS分析结果目录 ==="
hdfs dfs -mkdir -p ${HDFS_BASE}/output/abnormal_stop
hdfs dfs -mkdir -p ${HDFS_BASE}/output/cross_zone
hdfs dfs -mkdir -p ${HDFS_BASE}/output/kmeans_cluster
hdfs dfs -mkdir -p ${HDFS_BASE}/output/dt_prediction
echo "创建 ${HDFS_BASE}/output 各子目录完成"

# ============================================
# 步骤4：上传原始CSV数据到HDFS
# 本地文件 raw_ais_data.csv 需先放置在当前目录
# 上传后Hive外部表可直接映射该路径
# ============================================
echo "=== 上传原始数据到HDFS ==="
hdfs dfs -put -f raw_ais_data.csv ${HDFS_BASE}/raw/
echo "上传 raw_ais_data.csv 到 ${HDFS_BASE}/raw/ 完成"

# ============================================
# 步骤5：验证上传结果
# 列出所有文件，确认数据已成功上传
# ============================================
echo "=== HDFS文件列表验证 ==="
hdfs dfs -ls -R ${HDFS_BASE}

echo "=== HDFS数据上传完成 ==="
