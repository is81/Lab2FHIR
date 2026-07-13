import fitz, os, random, sys
sys.path.insert(0, "backend/src")
from db.models import SessionLocal, Report

db = SessionLocal()
real_names, real_doctors, real_hospitals = set(), set(), set()
for r in db.query(Report).all():
    if r.patient_name: real_names.add(r.patient_name)
    if r.doctor: real_doctors.add(r.doctor)
    if r.hospital: real_hospitals.add(r.hospital)
db.close()

surnames = '张李王赵陈刘黄周吴徐孙马朱胡郭何高林郑罗梁谢宋唐许韩冯邓曹彭曾肖田董潘袁蔡蒋余于杜叶程苏魏吕丁任卢姚沈钟姜崔谭陆汪范金石廖贾夏韦付方白邹孟熊秦邱江尹薛闫段雷侯龙史陶黎贺顾毛郝龚邵万钱严覃武戴莫孔向汤'
given = '一二三四五六七八十明华强伟芳秀英丽文志国建平勇军斌杰超涛鑫敏静娟玲萍红辉刚波峰宇'

name_map, used = {}, set()
for name in sorted(real_names):
    while True:
        fake = random.choice(surnames) + random.choice(given)
        if len(name) >= 3: fake += random.choice(given)
        if fake not in used: break
    name_map[name] = fake
    used.add(fake)

doctor_map = {d: f"赵医师{i+1:02d}" for i, d in enumerate(sorted(real_doctors))}
hospital_map = {h: "某市第一人民医院" for h in real_hospitals}

all_terms = {}
all_terms.update(name_map)
all_terms.update(doctor_map)
all_terms.update(hospital_map)
# 按文本长度降序
sorted_terms = sorted(all_terms.items(), key=lambda x: -len(x[0]))

pdf_dir = "docs/pdf_test"
count = 0
for fname in sorted(os.listdir(pdf_dir)):
    if not fname.endswith('.pdf') or fname.startswith('_'): continue
    path = os.path.join(pdf_dir, fname)
    doc = fitz.open(path)
    for page in doc:
        for real, fake in sorted_terms:
            areas = page.search_for(real)
            for rect in areas:
                # 1. 用白色矩形覆盖原文
                white = fitz.Rect(rect.x0 - 2, rect.y0 - 1, rect.x1 + 2, rect.y1 + 1)
                page.draw_rect(white, color=None, fill=(1, 1, 1))
                # 2. 在原位插入新文本
                page.insert_text(
                    (rect.x0, rect.y1 - 1),
                    fake,
                    fontname="china-s",
                    fontsize=rect.y1 - rect.y0 + 2
                )
    tmp = path + ".tmp"
    doc.save(tmp)
    doc.close()
    os.replace(tmp, path)
    count += 1

print(f"脱敏完成: {count} 份")
