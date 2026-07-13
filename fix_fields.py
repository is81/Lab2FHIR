import sys
sys.path.insert(0, 'backend/src')
from db.models import SessionLocal, Report
from parsers.patient_parser import parse_patient_info

db = SessionLocal()
for r in db.query(Report).all():
    if r.raw_text:
        p = parse_patient_info(r.raw_text)
        r.patient_name = p.get('patient_name', r.patient_name)
        r.hospital = p.get('hospital', r.hospital)
        r.department = p.get('department', '')
        r.doctor = p.get('doctor', '')
        print(f'{r.patient_name} | {r.hospital} | {r.department} | {r.doctor}')
db.commit()
db.close()
print('Done')
