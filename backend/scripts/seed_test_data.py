#!/usr/bin/env python3
"""Seed test data for admin dashboard."""

import asyncio
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from models import (
    User, Champion, TrainingSession, ActivityLog, ErrorLog,
    EmailTemplate, EmailLog, WebhookEndpoint, WebhookLog,
    AdminAlert, UserJourney, SubscriptionEvent
)
from services.auth import hash_password

DATABASE_URL = "sqlite+aiosqlite:///./champion_clone.db"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def seed_data():
    async with async_session() as db:
        print("Creating test users...")

        # Create test users with various states
        users_data = [
            {"email": "marie.dupont@example.com", "full_name": "Marie Dupont", "subscription_plan": "pro"},
            {"email": "jean.martin@example.com", "full_name": "Jean Martin", "subscription_plan": "starter"},
            {"email": "sophie.bernard@example.com", "full_name": "Sophie Bernard", "subscription_plan": "pro"},
            {"email": "pierre.durand@example.com", "full_name": "Pierre Durand", "subscription_plan": "free"},
            {"email": "claire.petit@example.com", "full_name": "Claire Petit", "subscription_plan": "enterprise"},
            {"email": "lucas.moreau@example.com", "full_name": "Lucas Moreau", "subscription_plan": "starter"},
            {"email": "emma.leroy@example.com", "full_name": "Emma Leroy", "subscription_plan": "pro"},
            {"email": "thomas.roux@example.com", "full_name": "Thomas Roux", "subscription_plan": "free"},
            {"email": "julie.simon@example.com", "full_name": "Julie Simon", "subscription_plan": "starter"},
            {"email": "nicolas.laurent@example.com", "full_name": "Nicolas Laurent", "subscription_plan": "pro"},
        ]

        created_users = []
        for i, u_data in enumerate(users_data):
            # Check if user exists
            existing = await db.execute(select(User).where(User.email == u_data["email"]))
            if existing.scalar_one_or_none():
                print(f"  User {u_data['email']} already exists, skipping...")
                result = await db.execute(select(User).where(User.email == u_data["email"]))
                created_users.append(result.scalar_one())
                continue

            user = User(
                email=u_data["email"],
                hashed_password=hash_password("TestPass123!"),
                full_name=u_data["full_name"],
                role="user",
                is_active=random.choice([True, True, True, False]),  # 75% active
                subscription_plan=u_data["subscription_plan"],
                subscription_status="active" if random.random() > 0.2 else "expired",
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 90)),
            )
            db.add(user)
            await db.flush()
            created_users.append(user)
            print(f"  Created user: {user.email}")

        await db.commit()

        print("\nCreating champions...")
        champions_data = [
            {"name": "Jordan Belfort", "desc": "Style agressif et direct", "owner_idx": 0},
            {"name": "Grant Cardone", "desc": "Style energique et persuasif", "owner_idx": 1},
            {"name": "Zig Ziglar", "desc": "Style motivationnel et inspirant", "owner_idx": 2},
            {"name": "Brian Tracy", "desc": "Style methodique et structure", "owner_idx": 3},
            {"name": "Tony Robbins", "desc": "Style inspirant et emotionnel", "owner_idx": 4},
        ]

        created_champions = []
        for c_data in champions_data:
            owner = created_users[c_data["owner_idx"]]
            champion = Champion(
                user_id=owner.id,
                name=c_data["name"],
                description=c_data["desc"],
                video_path=f"/uploads/video_{random.randint(1000,9999)}.mp4",
                audio_path=f"/audio/audio_{random.randint(1000,9999)}.wav",
                transcript=f"Transcription de {c_data['name']}...",
                patterns_json={"techniques": ["closing", "objection_handling"], "score": random.randint(70, 95)},
                status="ready",
            )
            db.add(champion)
            await db.flush()
            created_champions.append(champion)
            print(f"  Created champion: {champion.name}")

        await db.commit()

        print("\nCreating training sessions...")
        scenarios_list = [
            {"context": "Cold Call", "prospect_type": "PME", "challenge": "Premier contact"},
            {"context": "Objection Prix", "prospect_type": "Grand Compte", "challenge": "Negociation"},
            {"context": "Closing", "prospect_type": "Startup", "challenge": "Decision finale"},
        ]

        for _ in range(25):
            user = random.choice(created_users)
            champion = random.choice(created_champions) if created_champions else None
            if not champion:
                continue

            session = TrainingSession(
                user_id=str(user.id),
                champion_id=champion.id,
                scenario=random.choice(scenarios_list),
                status=random.choice(["completed", "completed", "completed", "active", "abandoned"]),
                overall_score=random.randint(50, 100) / 10 if random.random() > 0.3 else None,
                feedback_summary="Bon travail sur le closing, ameliorer l'ecoute active.",
                messages=[
                    {"role": "champion", "content": "Bonjour, comment puis-je vous aider?"},
                    {"role": "user", "content": "Je voudrais en savoir plus sur votre produit."},
                ],
            )
            db.add(session)

        await db.commit()
        print(f"  Created 25 training sessions")

        print("\nCreating activity logs...")
        actions = ["login", "logout", "upload", "analyze", "training_start", "training_complete", "register"]

        for day_offset in range(30):
            num_activities = random.randint(5, 25)
            for _ in range(num_activities):
                user = random.choice(created_users)
                action = random.choice(actions)

                activity = ActivityLog(
                    user_id=user.id,
                    action=action,
                    resource_type="champion" if action in ["upload", "analyze"] else "session" if "training" in action else None,
                    resource_id=str(random.randint(1, 100)) if action not in ["login", "logout", "register"] else None,
                    ip_address=f"192.168.1.{random.randint(1, 254)}",
                    user_agent="Mozilla/5.0",
                    created_at=datetime.utcnow() - timedelta(days=day_offset, hours=random.randint(0, 23)),
                )
                db.add(activity)

        await db.commit()
        print(f"  Created ~450 activity logs")

        print("\nCreating error logs...")
        error_types = ["ValidationError", "APIError", "DatabaseError", "TimeoutError", "AuthError"]
        endpoints = ["/upload", "/analyze", "/training/start", "/auth/login", "/champions"]

        for _ in range(15):
            error = ErrorLog(
                user_id=random.choice(created_users).id if random.random() > 0.3 else None,
                error_type=random.choice(error_types),
                error_message=f"Error message {random.randint(1000, 9999)}",
                stack_trace="Traceback...",
                endpoint=random.choice(endpoints),
                request_data={"key": "value"},
                is_resolved=random.choice([True, True, False]),
                resolution_notes="Fixed by updating validation" if random.random() > 0.5 else None,
                created_at=datetime.utcnow() - timedelta(days=random.randint(0, 14)),
            )
            db.add(error)

        await db.commit()
        print(f"  Created 15 error logs")

        print("\nCreating email templates...")
        templates = [
            {"trigger": "user.registered", "subject": "Bienvenue sur Champion Clone!"},
            {"trigger": "training.completed", "subject": "Bravo! Session terminee"},
            {"trigger": "subscription.expiring", "subject": "Votre abonnement expire bientot"},
        ]

        for t in templates:
            existing = await db.execute(select(EmailTemplate).where(EmailTemplate.trigger == t["trigger"]))
            if existing.scalar_one_or_none():
                continue
            template = EmailTemplate(
                trigger=t["trigger"],
                subject=t["subject"],
                body_html=f"<h1>{t['subject']}</h1><p>Contenu email...</p>",
                body_text=f"{t['subject']}\n\nContenu email...",
                is_active=True,
            )
            db.add(template)

        await db.commit()
        print(f"  Created email templates")

        print("\nCreating email logs...")
        statuses = ["sent", "sent", "sent", "sent", "opened", "clicked", "failed"]
        triggers = ["user.registered", "training.completed", "subscription.expiring"]

        for _ in range(50):
            user = random.choice(created_users)
            email_log = EmailLog(
                user_id=user.id,
                trigger=random.choice(triggers),
                to_email=user.email,
                subject="Email subject",
                status=random.choice(statuses),
                opened_at=datetime.utcnow() - timedelta(days=random.randint(0, 25)) if random.random() > 0.5 else None,
            )
            db.add(email_log)

        await db.commit()
        print(f"  Created 50 email logs")

        print("\nCreating webhook endpoints...")
        webhooks_data = [
            {"name": "Example API", "url": "https://api.example.com/webhooks/champion"},
            {"name": "Slack", "url": "https://hooks.slack.com/services/xxx"},
            {"name": "Zapier", "url": "https://zapier.com/hooks/catch/123"},
        ]

        created_webhooks = []
        for w in webhooks_data:
            existing = await db.execute(select(WebhookEndpoint).where(WebhookEndpoint.url == w["url"]))
            if existing.scalar_one_or_none():
                result = await db.execute(select(WebhookEndpoint).where(WebhookEndpoint.url == w["url"]))
                created_webhooks.append(result.scalar_one())
                continue
            webhook = WebhookEndpoint(
                name=w["name"],
                url=w["url"],
                secret=f"whsec_{random.randint(100000, 999999)}",
                events=["user.registered", "training.completed"],
                is_active=True,
            )
            db.add(webhook)
            await db.flush()
            created_webhooks.append(webhook)

        await db.commit()
        print(f"  Created webhook endpoints")

        print("\nCreating webhook logs...")
        if created_webhooks:
            for _ in range(30):
                webhook = random.choice(created_webhooks)
                success = random.random() > 0.15  # 85% success rate

                log = WebhookLog(
                    endpoint_id=webhook.id,
                    event=random.choice(["user.registered", "training.completed"]),
                    payload={"event": "data"},
                    status="success" if success else "failed",
                    response_code=200 if success else random.choice([500, 502, 504]),
                    response_body="OK" if success else "Error",
                    attempts=1,
                )
                db.add(log)

        await db.commit()
        print(f"  Created 30 webhook logs")

        print("\nCreating admin alerts...")
        alerts_data = [
            {"type": "system", "severity": "info", "title": "Mise a jour disponible", "message": "Version 2.1 disponible"},
            {"type": "security", "severity": "warning", "title": "Tentatives de connexion", "message": "5 tentatives echouees pour user@test.com"},
            {"type": "billing", "severity": "error", "title": "Paiement echoue", "message": "Le paiement pour user123 a echoue"},
            {"type": "system", "severity": "critical", "title": "Service indisponible", "message": "Le service d'analyse est temporairement indisponible"},
            {"type": "usage", "severity": "info", "title": "Nouveau record", "message": "100 sessions completees cette semaine!"},
        ]

        for a in alerts_data:
            alert = AdminAlert(
                type=a["type"],
                severity=a["severity"],
                title=a["title"],
                message=a["message"],
                is_read=random.choice([True, False]),
                is_dismissed=False,
                created_at=datetime.utcnow() - timedelta(hours=random.randint(1, 72)),
            )
            db.add(alert)

        await db.commit()
        print(f"  Created 5 admin alerts")

        print("\nCreating user journeys...")
        stages = ["registered", "first_login", "first_upload", "first_analysis", "first_training", "active_user", "power_user"]

        for user in created_users:
            # Create journey progression for each user
            num_stages = random.randint(1, len(stages))
            prev_stage = None
            for i in range(num_stages):
                journey = UserJourney(
                    user_id=user.id,
                    stage=stages[i],
                    previous_stage=prev_stage,
                )
                db.add(journey)
                prev_stage = stages[i]

        await db.commit()
        print(f"  Created user journeys")

        print("\n" + "="*50)
        print("Test data seeded successfully!")
        print("="*50)


if __name__ == "__main__":
    asyncio.run(seed_data())
