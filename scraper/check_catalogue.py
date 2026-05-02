import load_all_courses
cats = load_all_courses.CATALOGUE
total = sum(len(v['courses']) for v in cats.values())
print(f'Universities: {len(cats)}, Total CATALOGUE courses: {total}')
for k, v in cats.items():
    print(f'  {k}: {len(v["courses"])}')
