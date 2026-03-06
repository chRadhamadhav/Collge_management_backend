import asyncio
import os
import sys

sys.path.append(os.getcwd())

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.staff import Staff
from app.models.user import User

async def test():
    with open('staff_result.txt', 'w', encoding='utf-8') as f:
        async with AsyncSessionLocal() as db:
            res = await db.execute(select(Staff, User).join(User, Staff.user_id == User.id))
            records = res.all()
            f.write('--- ALL STAFF RECORDS ---\n')
            f.write(f'Total Staff: {len(records)}\n')
            for s, u in records:
                f.write(f'Name: {u.full_name}, Dept ID: {s.department_id}, Role: {u.role}\n')
            
            # Also print HOD department id
            res2 = await db.execute(select(User).where(User.role == 'hod'))
            hods = res2.scalars().all()
            f.write('\n--- HOD RECORDS ---\n')
            for h in hods:
                s_res = await db.execute(select(Staff).where(Staff.user_id == h.id))
                st = s_res.scalar_one_or_none()
                f.write(f'HOD Name: {h.full_name}, Dept ID: {st.department_id if st else "None"}\n')

if __name__ == '__main__':
    asyncio.run(test())
