"""Count courses per university in load_all_courses.py CATALOGUE"""
import re

with open('load_all_courses.py', 'r', encoding='utf-8') as f:
    content = f.read()

sections = re.split(r'#\s*──\s*', content)
for sec in sections:
    m = re.search(r'"source_key":\s*"(\w+)"', sec)
    if m:
        titles = re.findall(r'"title":', sec)
        print(f'{m.group(1)}: {len(titles)} courses')
