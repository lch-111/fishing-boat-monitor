#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python可视化脚本
使用Matplotlib/Seaborn绘制指标1-8的统计图表
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 读取清洗后数据
df = pd.read_csv('cleaned_ais_data.csv', encoding='utf-8')
# 将英文列名映射为中文（适配原脚本）
df.columns = ["渔船ID", "坐标X", "坐标Y", "速度", "方向", "时间", "作业类型", "海域", "日期"]
df['时间'] = pd.to_datetime(df['时间'])

output_dir = 'charts'
os.makedirs(output_dir, exist_ok=True)

# ============================================
# 指标1：各海域网格渔船密度热力图
# ============================================
print("绘制：指标1 - 海域网格渔船密度热力图")
fig, axes = plt.subplots(2, 3, figsize=(18, 12))
axes = axes.flatten()

for idx, (area, ax) in enumerate(zip(df['海域'].unique(), axes)):
    area_df = df[df['海域'] == area]
    # 网格化
    area_df['网格X'] = (area_df['坐标X'] // 10) * 10
    area_df['网格Y'] = (area_df['坐标Y'] // 10) * 10
    grid = area_df.groupby(['网格X', '网格Y'])['渔船ID'].nunique().reset_index()
    grid_pivot = grid.pivot(index='网格Y', columns='网格X', values='渔船ID').fillna(0)

    sns.heatmap(grid_pivot, cmap='YlOrRd', annot=True, fmt='.0f', 
                ax=ax, cbar_kws={'label': '渔船数'})
    ax.set_title(f'{area} - 渔船密度热力图', fontsize=12, fontweight='bold')
    ax.set_xlabel('网格X (km)')
    ax.set_ylabel('网格Y (km)')

# 隐藏多余的子图
for idx in range(len(df['海域'].unique()), len(axes)):
    fig.delaxes(axes[idx])

plt.tight_layout()
plt.savefig(f'{output_dir}/01_海域密度热力图.png', dpi=150, bbox_inches='tight')
plt.close()

# ============================================
# 指标2：三类作业渔船数量占比（饼图）
# ============================================
print("绘制：指标2 - 作业类型占比")
fig, ax = plt.subplots(figsize=(10, 8))
type_counts = df['作业类型'].value_counts()
colors = ['#ff6b6b', '#4ecdc4', '#ffe66d']
explode = (0.05, 0.05, 0.05)

wedges, texts, autotexts = ax.pie(type_counts, labels=type_counts.index, autopct='%1.1f%%',
                                   colors=colors, explode=explode, startangle=90,
                                   textprops={'fontsize': 14})
for autotext in autotexts:
    autotext.set_fontsize(12)
    autotext.set_fontweight('bold')

ax.set_title('三类作业渔船数量占比', fontsize=16, fontweight='bold', pad=20)
plt.savefig(f'{output_dir}/02_作业类型占比.png', dpi=150, bbox_inches='tight')
plt.close()

# ============================================
# 指标3：高峰作业时段统计（24小时柱状图）
# ============================================
print("绘制：指标3 - 24小时出海频次")
fig, ax = plt.subplots(figsize=(14, 6))
df['小时'] = df['时间'].dt.hour
hourly = df.groupby('小时').size().reset_index(name='频次')

bars = ax.bar(hourly['小时'], hourly['频次'], color='#3498db', alpha=0.8, edgecolor='white')
# 高亮高峰时段（6-10点，14-18点）
for i, bar in enumerate(bars):
    if hourly['小时'].iloc[i] in [6, 7, 8, 9, 14, 15, 16, 17]:
        bar.set_color('#e74c3c')
        bar.set_alpha(0.9)

ax.set_xlabel('小时', fontsize=12)
ax.set_ylabel('出海频次', fontsize=12)
ax.set_title('24小时出海频次分布（红色为高峰时段）', fontsize=14, fontweight='bold')
ax.set_xticks(range(0, 24, 2))
ax.grid(axis='y', alpha=0.3)

plt.savefig(f'{output_dir}/03_24小时出海频次.png', dpi=150, bbox_inches='tight')
plt.close()

# ============================================
# 指标4：渔船日均作业时长分布（箱线图+直方图）
# ============================================
print("绘制：指标4 - 日均作业时长分布")
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

# 计算每日作业时长
daily_duration = df.groupby(['渔船ID', df['时间'].dt.date]).agg(
    开始时间=('时间', 'min'),
    结束时间=('时间', 'max')
).reset_index()
daily_duration['作业时长_分钟'] = (daily_duration['结束时间'] - daily_duration['开始时间']).dt.total_seconds() / 60

# 箱线图
sns.boxplot(y=daily_duration['作业时长_分钟'], ax=ax1, color='#2ecc71')
ax1.set_ylabel('作业时长（分钟）', fontsize=12)
ax1.set_title('日均作业时长箱线图', fontsize=14, fontweight='bold')
ax1.grid(axis='y', alpha=0.3)

# 直方图
ax2.hist(daily_duration['作业时长_分钟'], bins=20, color='#9b59b6', alpha=0.8, edgecolor='white')
ax2.set_xlabel('作业时长（分钟）', fontsize=12)
ax2.set_ylabel('频次', fontsize=12)
ax2.set_title('日均作业时长分布直方图', fontsize=14, fontweight='bold')
ax2.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig(f'{output_dir}/04_日均作业时长分布.png', dpi=150, bbox_inches='tight')
plt.close()

# ============================================
# 指标5：单船月均出海频次（排名柱状图）
# ============================================
print("绘制：指标5 - 单船月均出海频次")
fig, ax = plt.subplots(figsize=(14, 8))

monthly_freq = df.groupby('渔船ID')['时间'].apply(lambda x: x.dt.date.nunique()).reset_index(name='出海天数')
monthly_freq = monthly_freq.sort_values('出海天数', ascending=True).tail(30)  # Top30

bars = ax.barh(range(len(monthly_freq)), monthly_freq['出海天数'], color='#1abc9c')
ax.set_yticks(range(len(monthly_freq)))
ax.set_yticklabels(monthly_freq['渔船ID'], fontsize=9)
ax.set_xlabel('出海天数', fontsize=12)
ax.set_title('单船月均出海频次 Top30', fontsize=14, fontweight='bold')
ax.grid(axis='x', alpha=0.3)

# 标注数值
for i, (idx, row) in enumerate(monthly_freq.iterrows()):
    ax.text(row['出海天数'] + 0.1, i, str(row['出海天数']), va='center', fontsize=9)

plt.tight_layout()
plt.savefig(f'{output_dir}/05_单船出海频次.png', dpi=150, bbox_inches='tight')
plt.close()

# ============================================
# 指标6：平均航速对比（分组柱状图）
# ============================================
print("绘制：指标6 - 平均航速对比")
fig, ax = plt.subplots(figsize=(10, 6))

speed_stats = df.groupby('作业类型')['速度'].agg(['mean', 'min', 'max', 'std']).reset_index()
x = np.arange(len(speed_stats))
width = 0.2

bars1 = ax.bar(x - 1.5*width, speed_stats['mean'], width, label='平均速度', color='#3498db')
bars2 = ax.bar(x - 0.5*width, speed_stats['min'], width, label='最小速度', color='#2ecc71')
bars3 = ax.bar(x + 0.5*width, speed_stats['max'], width, label='最大速度', color='#e74c3c')
bars4 = ax.bar(x + 1.5*width, speed_stats['std'], width, label='标准差', color='#f39c12')

ax.set_xlabel('作业类型', fontsize=12)
ax.set_ylabel('速度（节）', fontsize=12)
ax.set_title('平均航速对比（按作业类型）', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(speed_stats['作业类型'])
ax.legend()
ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig(f'{output_dir}/06_平均航速对比.png', dpi=150, bbox_inches='tight')
plt.close()

# ============================================
# 指标7：轨迹点月度分布（折线图）
# ============================================
print("绘制：指标7 - 月度分布")
fig, ax = plt.subplots(figsize=(12, 6))

monthly = df.groupby(df['时间'].dt.month).agg(
    轨迹点数=('渔船ID', 'size'),
    活跃渔船数=('渔船ID', 'nunique')
).reset_index()

ax.plot(monthly['时间'], monthly['轨迹点数'], marker='o', linewidth=2, 
        markersize=8, label='轨迹点数', color='#3498db')
ax2 = ax.twinx()
ax2.plot(monthly['时间'], monthly['活跃渔船数'], marker='s', linewidth=2,
         markersize=8, label='活跃渔船数', color='#e74c3c')

ax.set_xlabel('月份', fontsize=12)
ax.set_ylabel('轨迹点数', fontsize=12, color='#3498db')
ax2.set_ylabel('活跃渔船数', fontsize=12, color='#e74c3c')
ax.set_title('轨迹点月度分布', fontsize=14, fontweight='bold')
ax.set_xticks(monthly['时间'])
ax.grid(alpha=0.3)

lines1, labels1 = ax.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

plt.tight_layout()
plt.savefig(f'{output_dir}/07_月度分布.png', dpi=150, bbox_inches='tight')
plt.close()

# ============================================
# 指标8：渔船活动范围（Top20排名柱状图）
# ============================================
print("绘制：指标8 - 渔船活动范围 Top20")
fig, ax = plt.subplots(figsize=(14, 8))

# 计算每天的最远距离
daily_range = df.groupby(['渔船ID', df['时间'].dt.date]).apply(
    lambda x: np.sqrt((x['坐标X'] - x['坐标X'].iloc[0])**2 + 
                      (x['坐标Y'] - x['坐标Y'].iloc[0])**2).max()
).reset_index(name='最远距离')

# 取每船的最大活动范围
boat_range = daily_range.groupby('渔船ID')['最远距离'].max().reset_index()
boat_range = boat_range.sort_values('最远距离', ascending=True).tail(20)

bars = ax.barh(range(len(boat_range)), boat_range['最远距离'], color='#e67e22')
ax.set_yticks(range(len(boat_range)))
ax.set_yticklabels(boat_range['渔船ID'], fontsize=9)
ax.set_xlabel('最远距离（km）', fontsize=12)
ax.set_title('渔船活动范围 Top20（离港最远距离）', fontsize=14, fontweight='bold')
ax.grid(axis='x', alpha=0.3)

for i, (idx, row) in enumerate(boat_range.iterrows()):
    ax.text(row['最远距离'] + 1, i, f'{row["最远距离"]:.1f}', va='center', fontsize=9)

plt.tight_layout()
plt.savefig(f'{output_dir}/08_活动范围排名.png', dpi=150, bbox_inches='tight')
plt.close()

print(f"\n所有图表已保存至 {output_dir}/ 目录")
