import re
with open('/mnt/d/Erp-bench/v16-bench/apps/custom_ui/custom_ui/public/css/minimal_desk_v8.css', 'r') as f:
    content = f.read()
# Replace exact occurrences of .navbar with .page-head
content = re.sub(r'\.navbar([, :{\n])', r'.page-head\1', content)
with open('/mnt/d/Erp-bench/v16-bench/apps/custom_ui/custom_ui/public/css/minimal_desk_v8.css', 'w') as f:
    f.write(content)
