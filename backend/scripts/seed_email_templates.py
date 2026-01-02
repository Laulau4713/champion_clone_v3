#!/usr/bin/env python3
"""
Script to seed email templates for Champion Clone.

Usage:
    cd backend
    source venv/bin/activate
    python scripts/seed_email_templates.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from database import AsyncSessionLocal, init_db
from models import EmailTemplate, EmailTrigger

# Email templates to seed
TEMPLATES = [
    {
        "trigger": EmailTrigger.WELCOME.value,
        "subject": "Bienvenue sur Champion Clone !",
        "body_html": """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
        .button { display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
        .footer { text-align: center; margin-top: 20px; color: #888; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Bienvenue, {{user_name}} !</h1>
        </div>
        <div class="content">
            <p>Merci de rejoindre Champion Clone !</p>
            <p>Vous etes maintenant pret a :</p>
            <ul>
                <li>Uploader des videos de vos meilleurs commerciaux</li>
                <li>Extraire automatiquement leurs techniques de vente</li>
                <li>Entrainer votre equipe avec des scenarios personnalises</li>
            </ul>
            <p style="text-align: center;">
                <a href="{{app_url}}/dashboard" class="button">Commencer maintenant</a>
            </p>
        </div>
        <div class="footer">
            <p>{{app_name}} - Entrainement commercial IA</p>
        </div>
    </div>
</body>
</html>
        """,
        "body_text": """
Bienvenue, {{user_name}} !

Merci de rejoindre Champion Clone !

Vous etes maintenant pret a :
- Uploader des videos de vos meilleurs commerciaux
- Extraire automatiquement leurs techniques de vente
- Entrainer votre equipe avec des scenarios personnalises

Commencez maintenant : {{app_url}}/dashboard

{{app_name}} - Entrainement commercial IA
        """,
        "variables": ["user_name", "user_email", "app_name", "app_url"],
        "is_active": True,
    },
    {
        "trigger": EmailTrigger.FIRST_CHAMPION.value,
        "subject": "Votre premier Champion est pret !",
        "body_html": """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
        .button { display: inline-block; background: #11998e; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
        .footer { text-align: center; margin-top: 20px; color: #888; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Champion analyse !</h1>
        </div>
        <div class="content">
            <p>Bonjour {{user_name}},</p>
            <p>Excellente nouvelle ! Votre champion <strong>{{champion_name}}</strong> a ete analyse avec succes.</p>
            <p>Nous avons extrait :</p>
            <ul>
                <li>Les techniques de vente cles</li>
                <li>Les patterns de communication</li>
                <li>Les strategies de closing</li>
            </ul>
            <p>Vous pouvez maintenant commencer a vous entrainer !</p>
            <p style="text-align: center;">
                <a href="{{app_url}}/dashboard" class="button">Voir les scenarios</a>
            </p>
        </div>
        <div class="footer">
            <p>{{app_name}}</p>
        </div>
    </div>
</body>
</html>
        """,
        "body_text": """
Bonjour {{user_name}},

Excellente nouvelle ! Votre champion {{champion_name}} a ete analyse avec succes.

Nous avons extrait :
- Les techniques de vente cles
- Les patterns de communication
- Les strategies de closing

Vous pouvez maintenant commencer a vous entrainer !

Voir les scenarios : {{app_url}}/dashboard

{{app_name}}
        """,
        "variables": ["user_name", "champion_name", "app_name", "app_url"],
        "is_active": True,
    },
    {
        "trigger": EmailTrigger.FIRST_SESSION.value,
        "subject": "Bravo pour votre premiere session !",
        "body_html": """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
        .score { font-size: 48px; font-weight: bold; color: #f5576c; text-align: center; margin: 20px 0; }
        .button { display: inline-block; background: #f5576c; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
        .footer { text-align: center; margin-top: 20px; color: #888; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Premiere session terminee !</h1>
        </div>
        <div class="content">
            <p>Bravo {{user_name}} !</p>
            <p>Vous avez termine votre premiere session d'entrainement.</p>
            <div class="score">{{score}}/10</div>
            <p>Continuez a vous entrainer pour ameliorer votre score et maitriser les techniques de vente de vos champions.</p>
            <p style="text-align: center;">
                <a href="{{app_url}}/dashboard" class="button">Continuer l'entrainement</a>
            </p>
        </div>
        <div class="footer">
            <p>{{app_name}}</p>
        </div>
    </div>
</body>
</html>
        """,
        "body_text": """
Bravo {{user_name}} !

Vous avez termine votre premiere session d'entrainement.

Score : {{score}}/10

Continuez a vous entrainer pour ameliorer votre score et maitriser les techniques de vente de vos champions.

Continuer l'entrainement : {{app_url}}/dashboard

{{app_name}}
        """,
        "variables": ["user_name", "score", "app_name", "app_url"],
        "is_active": True,
    },
    {
        "trigger": EmailTrigger.INACTIVE_3_DAYS.value,
        "subject": "On vous attend sur Champion Clone !",
        "body_html": """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
        .button { display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
        .footer { text-align: center; margin-top: 20px; color: #888; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Vous nous manquez !</h1>
        </div>
        <div class="content">
            <p>Bonjour {{user_name}},</p>
            <p>Cela fait quelques jours que nous ne vous avons pas vu sur Champion Clone.</p>
            <p>N'oubliez pas que la pratique reguliere est la cle de l'amelioration !</p>
            <p>Vos champions vous attendent pour une nouvelle session d'entrainement.</p>
            <p style="text-align: center;">
                <a href="{{app_url}}/dashboard" class="button">Reprendre l'entrainement</a>
            </p>
        </div>
        <div class="footer">
            <p>{{app_name}}</p>
        </div>
    </div>
</body>
</html>
        """,
        "body_text": """
Bonjour {{user_name}},

Cela fait quelques jours que nous ne vous avons pas vu sur Champion Clone.

N'oubliez pas que la pratique reguliere est la cle de l'amelioration !

Vos champions vous attendent pour une nouvelle session d'entrainement.

Reprendre l'entrainement : {{app_url}}/dashboard

{{app_name}}
        """,
        "variables": ["user_name", "days_inactive", "app_name", "app_url"],
        "is_active": True,
    },
    {
        "trigger": EmailTrigger.INACTIVE_7_DAYS.value,
        "subject": "Une semaine deja ? Revenez vous entrainer !",
        "body_html": """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #ff6b6b 0%, #feca57 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
        .button { display: inline-block; background: #ff6b6b; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
        .footer { text-align: center; margin-top: 20px; color: #888; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>On ne vous oublie pas !</h1>
        </div>
        <div class="content">
            <p>Bonjour {{user_name}},</p>
            <p>Une semaine s'est ecoulee depuis votre derniere visite.</p>
            <p>Les meilleurs commerciaux s'entrainent regulierement. Ne laissez pas vos competences s'eroder !</p>
            <p>Que diriez-vous d'une petite session aujourd'hui ?</p>
            <p style="text-align: center;">
                <a href="{{app_url}}/dashboard" class="button">Je m'entraine maintenant</a>
            </p>
        </div>
        <div class="footer">
            <p>{{app_name}}</p>
        </div>
    </div>
</body>
</html>
        """,
        "body_text": """
Bonjour {{user_name}},

Une semaine s'est ecoulee depuis votre derniere visite.

Les meilleurs commerciaux s'entrainent regulierement. Ne laissez pas vos competences s'eroder !

Que diriez-vous d'une petite session aujourd'hui ?

Je m'entraine maintenant : {{app_url}}/dashboard

{{app_name}}
        """,
        "variables": ["user_name", "days_inactive", "app_name", "app_url"],
        "is_active": True,
    },
    {
        "trigger": EmailTrigger.INACTIVE_30_DAYS.value,
        "subject": "Nous aimerions vous revoir sur Champion Clone",
        "body_html": """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #2c3e50 0%, #4ca1af 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
        .button { display: inline-block; background: #4ca1af; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
        .footer { text-align: center; margin-top: 20px; color: #888; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Cela fait longtemps...</h1>
        </div>
        <div class="content">
            <p>Bonjour {{user_name}},</p>
            <p>Cela fait maintenant un mois que vous n'avez pas utilise Champion Clone.</p>
            <p>Beaucoup de choses ont peut-etre change depuis. Nous avons ameliore notre plateforme et vos champions sont toujours la, prets a vous aider a progresser.</p>
            <p>Si vous avez des questions ou besoin d'aide, n'hesitez pas a nous contacter.</p>
            <p style="text-align: center;">
                <a href="{{app_url}}/dashboard" class="button">Revenir sur Champion Clone</a>
            </p>
        </div>
        <div class="footer">
            <p>{{app_name}}</p>
        </div>
    </div>
</body>
</html>
        """,
        "body_text": """
Bonjour {{user_name}},

Cela fait maintenant un mois que vous n'avez pas utilise Champion Clone.

Beaucoup de choses ont peut-etre change depuis. Nous avons ameliore notre plateforme et vos champions sont toujours la, prets a vous aider a progresser.

Si vous avez des questions ou besoin d'aide, n'hesitez pas a nous contacter.

Revenir sur Champion Clone : {{app_url}}/dashboard

{{app_name}}
        """,
        "variables": ["user_name", "days_inactive", "app_name", "app_url"],
        "is_active": True,
    },
    {
        "trigger": EmailTrigger.MILESTONE_10_SESSIONS.value,
        "subject": "10 sessions ! Vous etes sur la bonne voie !",
        "body_html": """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #f7971e 0%, #ffd200 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
        .milestone { font-size: 72px; text-align: center; margin: 20px 0; }
        .button { display: inline-block; background: #f7971e; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
        .footer { text-align: center; margin-top: 20px; color: #888; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Felicitations !</h1>
        </div>
        <div class="content">
            <p>Bravo {{user_name}} !</p>
            <div class="milestone">10</div>
            <p style="text-align: center; font-size: 18px;"><strong>sessions completees !</strong></p>
            <p>Votre engagement porte ses fruits. Continuez sur cette lancee pour devenir un veritable champion de la vente !</p>
            <p style="text-align: center;">
                <a href="{{app_url}}/dashboard" class="button">Voir mes statistiques</a>
            </p>
        </div>
        <div class="footer">
            <p>{{app_name}}</p>
        </div>
    </div>
</body>
</html>
        """,
        "body_text": """
Bravo {{user_name}} !

10 sessions completees !

Votre engagement porte ses fruits. Continuez sur cette lancee pour devenir un veritable champion de la vente !

Voir mes statistiques : {{app_url}}/dashboard

{{app_name}}
        """,
        "variables": ["user_name", "app_name", "app_url"],
        "is_active": True,
    },
    {
        "trigger": EmailTrigger.MILESTONE_50_SESSIONS.value,
        "subject": "50 sessions ! Vous etes un expert !",
        "body_html": """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #8e2de2 0%, #4a00e0 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
        .milestone { font-size: 72px; text-align: center; margin: 20px 0; }
        .badge { font-size: 48px; text-align: center; }
        .button { display: inline-block; background: #8e2de2; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
        .footer { text-align: center; margin-top: 20px; color: #888; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Incroyable !</h1>
        </div>
        <div class="content">
            <div class="badge">&#127942;</div>
            <p style="text-align: center;">Felicitations {{user_name}} !</p>
            <div class="milestone">50</div>
            <p style="text-align: center; font-size: 18px;"><strong>sessions completees !</strong></p>
            <p>Vous faites partie des utilisateurs les plus dedies de Champion Clone. Votre maitrise des techniques de vente doit etre impressionnante maintenant !</p>
            <p style="text-align: center;">
                <a href="{{app_url}}/dashboard" class="button">Continuer ma progression</a>
            </p>
        </div>
        <div class="footer">
            <p>{{app_name}}</p>
        </div>
    </div>
</body>
</html>
        """,
        "body_text": """
Felicitations {{user_name}} !

50 sessions completees !

Vous faites partie des utilisateurs les plus dedies de Champion Clone. Votre maitrise des techniques de vente doit etre impressionnante maintenant !

Continuer ma progression : {{app_url}}/dashboard

{{app_name}}
        """,
        "variables": ["user_name", "app_name", "app_url"],
        "is_active": True,
    },
]


async def seed_email_templates():
    """Seed the email templates."""
    print("Initializing database...")
    await init_db()

    async with AsyncSessionLocal() as db:
        print("\nSeeding email templates...")

        created = 0
        skipped = 0

        for template_data in TEMPLATES:
            # Check if template already exists
            result = await db.execute(select(EmailTemplate).where(EmailTemplate.trigger == template_data["trigger"]))
            existing = result.scalar_one_or_none()

            if existing:
                print(f"  [SKIP] {template_data['trigger']} (already exists)")
                skipped += 1
                continue

            # Create template
            template = EmailTemplate(
                trigger=template_data["trigger"],
                subject=template_data["subject"],
                body_html=template_data["body_html"].strip(),
                body_text=template_data["body_text"].strip(),
                variables=template_data["variables"],
                is_active=template_data["is_active"],
            )
            db.add(template)
            print(f"  [CREATE] {template_data['trigger']}")
            created += 1

        await db.commit()

        print("\n" + "=" * 50)
        print("Email templates seeded!")
        print("=" * 50)
        print(f"  Created: {created}")
        print(f"  Skipped: {skipped}")
        print(f"  Total templates: {len(TEMPLATES)}")
        print("=" * 50)


if __name__ == "__main__":
    asyncio.run(seed_email_templates())
