import re

with open('frontend/index.html', encoding='utf-8') as f:
    html = f.read()

with open('frontend/app.js', encoding='utf-8') as f:
    js = f.read()

# Let's inspect sections in index.html
sections = re.findall(r'<section\s+id=[\'"]([^\'"]+)[\'"](.*?)<\/section>', html, re.DOTALL)
print(f"Found {len(sections)} sections")

for sec_id, sec_content in sections:
    print(f"\n==========================================")
    print(f"SECTION: {sec_id}")
    print(f"==========================================")
    # find metric values, cards, buttons, tables, canvases
    metric_values = re.findall(r'class=[\'"][^\'"]*metric-value[^\'"]*[\'"][^>]*id=[\'"]([^\'"]+)[\'"]', sec_content)
    metric_values += re.findall(r'id=[\'"]([^\'"]+)[\'"][^>]*class=[\'"][^\'"]*metric-value[^\'"]*[\'"]', sec_content)
    
    canvases = re.findall(r'<canvas\s+id=[\'"]([^\'"]+)[\'"]', sec_content)
    tables = re.findall(r'id=[\'"]([^\'"]+)[\'"][^>]*(?:<table|<tbody)|\b(?:table|tbody)\b[^>]*id=[\'"]([^\'"]+)[\'"]', sec_content)
    
    all_ids = re.findall(r'id=[\'"]([^\'"]+)[\'"]', sec_content)
    print(f"  Metric Value IDs: {metric_values}")
    print(f"  Canvas IDs: {canvases}")
    print(f"  All IDs ({len(all_ids)}): {all_ids}")
