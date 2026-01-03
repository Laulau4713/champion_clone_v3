# Développement Local

**ATTENTION: Ne pas commiter ce fichier - contient des credentials de test**

---

## 1. Démarrer les serveurs

### Docker Compose (recommandé)
```bash
cd /home/laurent/champion-clone-dev
source .env
docker-compose up -d
```

### Vérifier que tout tourne
```bash
docker-compose ps
docker-compose logs -f  # Suivre les logs
```

### Sans Docker (développement)

#### Backend (port 8000)
```bash
cd /home/laurent/champion-clone-dev/backend
source venv/bin/activate
python main.py
```

#### Frontend (port 3000)
```bash
cd /home/laurent/champion-clone-dev/frontend
npm run dev
```

---

## 2. Arrêter les serveurs

### Docker
```bash
docker-compose stop      # Arrêter
docker-compose down      # Arrêter et supprimer containers
docker-compose restart frontend  # Redémarrer un service
```

### Sans Docker
```bash
# CTRL+C dans le terminal ou:
pkill -f "python main.py"
pkill -f "next dev"
```

---

## 3. URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Login | http://localhost:3000/login |
| Training V2 | http://localhost:3000/training |
| Dashboard | http://localhost:3000/dashboard |
| Admin | http://localhost:3000/admin |
| API Health | http://localhost:8000/health |

---

## 4. Comptes de test

### Compte Demo (Premium - illimité)
```
Email:    demo@test.com
Password: demo1234
Plan:     pro
```

### Admin Enterprise
```
Email:    admin@test.com
Password: demo1234
Plan:     enterprise
Role:     admin
```

### Essai gratuit (3 sessions max)
```
Email:    trial@champion-test.com
Password: Trial123!
Plan:     free
```

---

## 5. Commandes utiles

### Rebuild frontend après modifications
```bash
source .env
docker-compose build frontend
docker-compose up -d frontend
```

### Rebuild sans cache
```bash
source .env
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

### Voir les logs
```bash
docker-compose logs backend --tail=50
docker-compose logs frontend --tail=50
```

### Accéder au shell d'un container
```bash
docker exec -it champion-clone-dev-backend-1 bash
docker exec -it champion-clone-dev-frontend-1 sh
```

### Tester l'API
```bash
# Health check
curl http://localhost:8000/health

# Login
curl -s -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@test.com","password":"demo1234"}'
```

---

## 6. Base de données

### Lister les utilisateurs
```bash
docker-compose exec backend python -c "
import asyncio
from sqlalchemy import select
from database import AsyncSessionLocal
from models import User

async def list_users():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).limit(10))
        for u in result.scalars():
            print(f'{u.email} | {u.subscription_plan} | {u.role}')

asyncio.run(list_users())
" 2>&1 | grep -v "INFO sqlalchemy"
```

### Passer un user en Premium
```bash
docker-compose exec backend python -c "
import asyncio
from sqlalchemy import select
from database import AsyncSessionLocal
from models import User

async def upgrade():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == 'demo@test.com'))
        user = result.scalar_one_or_none()
        if user:
            user.subscription_plan = 'pro'
            user.trial_sessions_used = 0
            await session.commit()
            print('OK')

asyncio.run(upgrade())
"
```

### Reset mot de passe
```bash
docker-compose exec backend python -c "
import asyncio
import bcrypt
from sqlalchemy import select
from database import AsyncSessionLocal
from models import User

async def reset():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == 'demo@test.com'))
        user = result.scalar_one_or_none()
        if user:
            user.hashed_password = bcrypt.hashpw('demo1234'.encode(), bcrypt.gensalt()).decode()
            await session.commit()
            print('OK')

asyncio.run(reset())
"
```

---

## 7. Troubleshooting

### "Permission denied" sur .next
```bash
docker exec --user root champion-clone-dev-frontend-1 rm -rf /app/.next
docker-compose build frontend
docker-compose up -d frontend
```

### "TRIAL_EXPIRED" - Sessions épuisées
Passer le compte en premium (voir section 6).

### Container en boucle de restart
```bash
docker-compose logs frontend --tail=30  # Voir l'erreur
docker-compose build --no-cache frontend  # Rebuild complet
docker-compose up -d frontend
```

### 401 Unauthorized / Token expiré
Se reconnecter via /login.

### 403 sur le dashboard
Le compte n'a pas les permissions. Utiliser un compte enterprise pour les features champions.

### Ports déjà utilisés
```bash
docker-compose down
lsof -ti:8000 | xargs kill -9
lsof -ti:3000 | xargs kill -9
docker-compose up -d
```
