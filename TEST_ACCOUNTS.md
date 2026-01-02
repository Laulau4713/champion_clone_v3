# Comptes de Test

**ATTENTION: Ne pas commiter ce fichier - le déplacer avant commit**

## URLs

- Frontend: http://localhost:3002
- Backend API: http://localhost:8000
- Login: http://localhost:3002/login

---

## Admin

| Champ    | Valeur                    |
| -------- | ------------------------- |
| Email    | `admin@champion-test.com` |
| Password | Admin123                  |
| Role     | admin                     |
| Plan     | pro                       |

Accès: Dashboard, Learn, Training, Trophées, Upload, **Panel Admin**

---

## Utilisateur Premium

| Champ               | Valeur                      |
| ------------------- | --------------------------- |
| Email               | `premium@champion-test.com` |
| Password Premium123 |
| Role                | user                        |
| Plan                | pro                         |

Accès: Dashboard, Learn, Training, Trophées, Upload

---

## Utilisateur Essai Gratuit

| Champ              | Valeur                    |
| ------------------ | ------------------------- |
| Email              | `trial@champion-test.com` |
| Password           | Trial123                  |
| Role               | user                      |
| Plan               | free                      |
| Sessions utilisées | 0                         |

Accès limité: Dashboard, Learn (Module 1 only), Training (limité), Trophées

---

## Commandes utiles

```bash
# Démarrer le backend
cd backend && source venv/bin/activate && python main.py

# Démarrer le frontend
cd frontend && npm run dev -- -p 3002

# Reset un compte (trial sessions à 0)
source venv/bin/activate && python3 -c "
import asyncio
from database import AsyncSessionLocal
from models import User
from sqlalchemy import select

async def reset():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == 'trial@champion-test.com'))
        user = result.scalar_one()
        user.trial_sessions_used = 0
        await db.commit()
        print('Reset OK')

asyncio.run(reset())
"
```
