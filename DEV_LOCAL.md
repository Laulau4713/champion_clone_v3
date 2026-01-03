# Développement Local

**ATTENTION: Ne pas commiter ce fichier - contient des credentials de test**

---

## 1. Démarrer les serveurs

### Backend (port 8000)
```bash
cd /home/laurent/champion-clone-dev/backend
source venv/bin/activate
python main.py
```

### Frontend (port 3002)
```bash
cd /home/laurent/champion-clone-dev/frontend
npm run dev -- -p 3002
```

### Les deux en parallèle (2 terminaux)
```bash
# Terminal 1 - Backend
cd /home/laurent/champion-clone-dev/backend && source venv/bin/activate && python main.py

# Terminal 2 - Frontend
cd /home/laurent/champion-clone-dev/frontend && npm run dev -- -p 3002
```

---

## 2. Arrêter les serveurs

### Méthode douce (CTRL+C dans le terminal)

### Forcer l'arrêt
```bash
# Tuer le backend
pkill -f "python main.py"

# Tuer le frontend
pkill -f "next dev"

# Tuer tout Node.js (attention si autres apps node)
pkill -f node

# Libérer un port spécifique
lsof -ti:8000 | xargs kill -9  # Backend
lsof -ti:3002 | xargs kill -9  # Frontend
```

### Vérifier les ports utilisés
```bash
lsof -i:8000  # Backend
lsof -i:3002  # Frontend
```

---

## 3. URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3002 |
| Backend API | http://localhost:8000 |
| Login | http://localhost:3002/login |
| Achievements | http://localhost:3002/achievements |
| Admin | http://localhost:3002/admin |
| API Health | http://localhost:8000/health |

---

## 4. Comptes de test

### Admin (accès complet + panel admin)
```
Email:    admin@champion-test.com
Password: Admin123!
```

### Premium (accès complet sans admin)
```
Email:    premium@champion-test.com
Password: Premium123!
```

### Essai gratuit (accès limité, 0 sessions utilisées)
```
Email:    trial@champion-test.com
Password: Trial123!
```

---

## 5. Commandes utiles

### Tester l'API
```bash
# Health check
curl http://localhost:8000/health

# Login (récupérer token) - utiliser Python car le ! pose problème avec curl/bash
python3 -c "
import requests
r = requests.post('http://localhost:8000/auth/login', json={
    'email': 'admin@champion-test.com',
    'password': 'Admin123!'
})
print(r.json())
"
```

### Reset sessions trial
```bash
cd /home/laurent/champion-clone-dev/backend
source venv/bin/activate
python3 -c "
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
        print('✅ Trial sessions reset to 0')

asyncio.run(reset())
"
```

### Rebuild frontend
```bash
cd /home/laurent/champion-clone-dev/frontend
npm run build
```

---

## 6. Troubleshooting

### "Port already in use"
```bash
# Méthode standard
lsof -ti:PORT | xargs kill -9

# Si processus root (nécessite sudo)
sudo fuser -k 8000/tcp
sudo fuser -k 3002/tcp
```

### Frontend affiche que du HTML
Ouvrir dans un **navigateur** (pas curl). Next.js nécessite JavaScript.

### 401 Unauthorized
Token expiré. Se reconnecter via /login.

### Base de données corrompue
```bash
cd /home/laurent/champion-clone-dev/backend
rm champion_clone.db
python main.py  # Recréera la DB
# Puis recréer les comptes de test (voir ci-dessous)
```

### Recréer/reset les comptes de test
```bash
cd /home/laurent/champion-clone-dev/backend
source venv/bin/activate
python3 << 'EOF'
import asyncio
from database import AsyncSessionLocal
from models import User
from sqlalchemy import select
from services.auth import hash_password

async def reset_accounts():
    async with AsyncSessionLocal() as db:
        accounts = [
            ('admin@champion-test.com', 'Admin123!', 'pro', 'admin'),
            ('premium@champion-test.com', 'Premium123!', 'pro', 'user'),
            ('trial@champion-test.com', 'Trial123!', 'free', 'user'),
        ]
        for email, pwd, plan, role in accounts:
            result = await db.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
            if user:
                user.hashed_password = hash_password(pwd)
                print(f"✓ Updated: {email}")
            else:
                new_user = User(
                    email=email,
                    hashed_password=hash_password(pwd),
                    full_name=email.split('@')[0].title(),
                    subscription_plan=plan,
                    role=role,
                    is_active=True
                )
                db.add(new_user)
                print(f"✓ Created: {email}")
        await db.commit()
        print("Done!")

asyncio.run(reset_accounts())
EOF
```
