import re

with open('08_dashboard_real.html', 'r', encoding='utf-8') as f:
    content = f.read()

old_series = r"series:\[\{type:'scatter',data:d\.map\(function\(x\){return {value:\[x\.x,x\.y\],ship_id:x\.ship_id,sea_area:x\.sea_area};}\),symbolSize:10,itemStyle:{color:'#ffcc00'}}\]"

new_series = """series:[{
        type:'scatter',
        data:d.map(function(x){
            return {value:[x.x,x.y], ship_id:x.ship_id, sea_area:x.sea_area};
        }),
        symbolSize:12,
        itemStyle:{
            color: function(param){
                var area = param.data.sea_area;
                var colors = {
                    '渤海湾': '#ff6b6b',
                    '黄海中部': '#4ecdc4', 
                    '东海近海': '#ffe66d',
                    '舟山群岛': '#a29bfe',
                    '南海北部': '#fd79a8'
                };
                return colors[area] || '#ffcc00';
            }
        }
    }]"""

content = re.sub(old_series, new_series, content, flags=re.DOTALL)
with open('08_dashboard_real.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('✅ 跨界捕捞点已按海域分色')
