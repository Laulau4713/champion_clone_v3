# Exemple Complet : Vente de Cybersécurité PME

Ce fichier est un exemple concret utilisable pour le training.
Il montre comment remplir le template avec des données réalistes.

---

## 1. LE VENDEUR

```yaml
vendeur:
  nom: "{{user.name}}"
  role: "Commercial terrain"
  experience: "confirmé"
```

---

## 2. LA SOCIÉTÉ

```yaml
societe:
  nom: "CyberShield France"
  secteur: "Cybersécurité"
  creation: "2019"
  taille: "45 employés"
  siege: "Lyon"
  positionnement: "Rendre la cybersécurité accessible aux PME françaises sans équipe IT"
  valeurs:
    - "Simplicité"
    - "Made in France"
    - "Accompagnement humain"
```

---

## 3. LE PRODUIT

```yaml
produit:
  nom: "SecureBox Pro"
  type: "SaaS + Boîtier"

  probleme_resolu: "Protéger les PME des cyberattaques (ransomware, phishing, vol de données) sans avoir besoin d'un service informatique"

  pour_qui: "PME de 10 à 200 employés sans DSI, tous secteurs"

  fonctionnement: |
    1. On installe un boîtier physique sur votre réseau (30 min, on s'en occupe)
    2. Le boîtier analyse tout le trafic et bloque les menaces en temps réel
    3. Vous suivez tout sur un dashboard simple, on vous alerte si besoin

  benefices_cles:
    - "Protection complète : antivirus, firewall, anti-phishing, backup"
    - "Zéro maintenance : on gère tout à distance"
    - "Conformité RGPD incluse"
    - "Support français 7j/7"

  prix:
    modele: "Forfait mensuel selon nombre de postes"
    entree_de_gamme: "199€/mois (jusqu'à 20 postes)"
    offre_populaire: "349€/mois (jusqu'à 50 postes) - la plus vendue"
    engagement: "Sans engagement, résiliable à tout moment"

  differenciateur: "Seule solution française certifiée ANSSI avec installation et support inclus. Nos concurrents vendent un logiciel, nous on vend la tranquillité."

  garanties:
    - "30 jours d'essai gratuit"
    - "Installation offerte"
    - "Satisfait ou remboursé le premier mois"
    - "SLA 99.9% de disponibilité"
```

---

## 4. LES PREUVES

```yaml
preuves:
  stats:
    nb_clients: "1 200+ PME protégées"
    satisfaction: "4.8/5 sur 340 avis"
    anciennete: "Depuis 2019, 5 ans d'expérience"
    resultat_moyen: "0 incident majeur chez nos clients depuis 2022"

  temoignages:
    - client:
        nom: "Marc Dubois"
        poste: "Directeur Général"
        entreprise: "TransLogistic"
        secteur: "Transport & Logistique"
        taille: "42 employés"
      probleme_initial: |
        Ransomware en 2022 : 3 jours d'arrêt total, 45 000€ de pertes.
        Données clients sensibles (contrats transporteurs).
        Aucune protection sérieuse, antivirus grand public.
      solution_apportee: |
        Installation SecureBox en 2h.
        Formation équipe au phishing (1h).
        Backup automatique quotidien.
      resultat_chiffre: "0 incident depuis 18 mois, conformité RGPD obtenue"
      citation: "Avant je stressais à chaque email bizarre. Maintenant je dors tranquille. Et c'est même pas moi qui gère, ils font tout."

    - client:
        nom: "Sophie Martin"
        poste: "Gérante"
        entreprise: "Cabinet Martin & Associés"
        secteur: "Expertise comptable"
        taille: "12 employés"
      probleme_initial: |
        Données ultra-sensibles (bilans clients, fiches de paie).
        Obligation légale de protection des données.
        "Mon neveu" gérait l'informatique = grosse faille de sécurité.
      solution_apportee: |
        Audit gratuit → 15 failles critiques identifiées.
        SecureBox installé en 1 journée.
        Rapport de conformité RGPD fourni.
      resultat_chiffre: "Audit CNIL passé sans remarque, 0 faille depuis 2 ans"
      citation: "J'ai montré le rapport de conformité à mes clients. Certains m'ont dit que ça les rassurait de travailler avec nous."

    - client:
        nom: "Philippe Roux"
        poste: "DSI à temps partiel"
        entreprise: "MécaPrécision"
        secteur: "Industrie"
        taille: "85 employés"
      probleme_initial: |
        Plans industriels confidentiels (brevets en cours).
        Sous-traitant Airbus = exigences de sécurité strictes.
        Pas de budget pour un DSI temps plein.
      solution_apportee: |
        SecureBox + module "Industrie" (protection plans CAO).
        Rapport mensuel pour Airbus.
        Hotline dédiée.
      resultat_chiffre: "Contrat Airbus renouvelé grâce à la mise en conformité"
      citation: "Airbus nous demandait des garanties. Avec CyberShield, on a pu leur fournir un dossier béton en 48h."

  references:
    - "TransLogistic"
    - "Cabinet Martin & Associés"
    - "MécaPrécision"
    - "Groupe Hôtelier Lumière"
    - "Clinique Vétérinaire du Parc"

  certifications:
    - "Certifié ANSSI (Agence Nationale de la Sécurité des Systèmes d'Information)"
    - "Label France Cybersecurity"
    - "Hébergement données en France (OVH)"
    - "Conforme RGPD"
```

---

## 5. LA CONCURRENCE

```yaml
concurrence:
  concurrent_principal:
    nom: "Norton / Avast / Kaspersky (antivirus grand public)"
    positionnement: "Protection basique pour particuliers et TPE"
    forces:
      - "Prix bas (50-100€/an)"
      - "Connu du grand public"
      - "Facile à installer"
    faiblesses:
      - "Protection limitée (pas de firewall réseau)"
      - "Pas de backup inclus"
      - "Support en anglais ou chatbot"
      - "Pas de conformité RGPD"
      - "Aucun accompagnement"
    prix_comparatif: "5x moins cher mais 10x moins de protection"

  concurrent_secondaire:
    nom: "Prestataire informatique local"
    positionnement: "Le gars qui vient quand ça plante"
    forces:
      - "Relation de confiance locale"
      - "Intervention sur site"
    faiblesses:
      - "Réactif, pas préventif"
      - "Pas spécialiste cybersécurité"
      - "Disponibilité limitée"
      - "Coût horaire élevé (80-150€/h)"
    prix_comparatif: "Semble moins cher mais coûte plus en cas de problème"

  notre_avantage: |
    On est le seul à combiner :
    - Protection pro niveau grande entreprise
    - Prix PME (moins de 10€/poste/mois)
    - Zéro gestion pour vous (on fait tout)
    - Support humain français

  argument_switch: |
    "Vous payez pour un antivirus qui ne vous protège que partiellement.
    Pour 150€ de plus par mois, vous avez une protection complète
    ET quelqu'un qui surveille pour vous 24/7.
    Si demain vous avez un ransomware, votre antivirus ne vous remboursera pas
    les 3 jours d'arrêt et les données perdues."

  facilite_migration: |
    - On s'occupe de tout : désinstallation ancien système, installation nouveau
    - Migration en 2h, aucune interruption d'activité
    - Formation équipe incluse (1h)
    - On garde l'historique de vos backups si vous en avez
```

---

## 6. LE PROSPECT (Exemple généré)

```yaml
prospect:
  identite:
    prenom: "Jean-Pierre"
    nom: "Moreau"
    poste: "Directeur Général"
    entreprise: "MétalPro SARL"
    secteur: "Industrie métallurgique"
    taille_entreprise: "28 employés"
    localisation: "Zone industrielle de Vénissieux"

  personnalite: "pragmatique"
  # Traits : va droit au but, veut des faits pas du blabla,
  # respecte ceux qui connaissent leur sujet, méfiant envers les commerciaux

  contexte_appel: |
    Appel à froid. Vous avez trouvé l'entreprise sur LinkedIn.
    Vous appelez le standard, c'est lui qui décroche (petite boîte).
    Il est en train de traiter ses emails, légèrement distrait.

  # LE BESOIN (réel, que votre produit résout)
  besoin:
    situation_actuelle: |
      - Antivirus Avast gratuit sur les postes
      - Backup manuel sur disque dur externe "quand on y pense"
      - Le fils du comptable "s'y connaît en informatique"
      - Serveur local avec tous les plans et devis

    douleur: |
      Le mois dernier, un email de phishing a failli passer.
      Le comptable a cliqué, heureusement le lien était mort.
      Jean-Pierre a réalisé que tout aurait pu disparaître.

    enjeu: |
      - Devis et plans confidentiels (clients grands comptes)
      - Si fuite de données → perte de contrats
      - 5 ans d'historique sur le serveur, aucune copie externe

    declencheur: |
      Un ami chef d'entreprise s'est fait pirater le mois dernier.
      2 semaines d'arrêt. Jean-Pierre y pense depuis.

  # LES OBJECTIONS (freins à l'achat malgré le besoin)
  objections:
    - type: "budget"
      exprimee: "350€ par mois c'est un budget quand même..."
      cachee: "Je sais que c'est important mais j'ai d'autres priorités"
      intensite: "moyenne"
      reponse_cle: |
        → Comparer au coût d'un incident (TransLogistic : 45k€)
        → Ramener au coût par jour (12€/jour = 1 café par employé)
        → Mentionner le client industrie MécaPrécision

    - type: "timing"
      exprimee: "Là c'est pas le moment, on est en pleine prod..."
      cachee: "J'ai pas envie de gérer un projet de plus"
      intensite: "moyenne"
      reponse_cle: |
        → Installation en 2h, aucune interruption
        → On s'occupe de tout, vous n'avez rien à gérer
        → Plus on attend, plus le risque augmente

    - type: "statu_quo"
      exprimee: "Bon, ça fait 10 ans qu'on fonctionne comme ça..."
      cachee: "Pourquoi changer si ça marche?"
      intensite: "forte"
      reponse_cle: |
        → Les attaques ont explosé depuis le COVID (+400%)
        → Son ami s'est fait pirater récemment (utiliser son propre exemple)
        → "Ça marchait" jusqu'au jour où ça ne marche plus

    - type: "confiance"
      exprimee: "CyberShield... j'ai jamais entendu parler"
      cachee: "C'est peut-être une arnaque"
      intensite: "moyenne"
      reponse_cle: |
        → Certifié ANSSI (l'État français)
        → 1200 PME clientes
        → Mentionner des références locales si possible
        → Proposer l'essai gratuit 30 jours sans engagement

    - type: "decision"
      exprimee: "Faut que j'en parle à mon associé"
      cachee: "Je veux pas prendre la décision seul"
      intensite: "faible"
      reponse_cle: |
        → Proposer un call à 3
        → Envoyer une synthèse pour l'associé
        → "Qu'est-ce qui le convaincrait lui?"
```

---

## 7. OBJECTIFS DE LA SESSION

```yaml
objectifs:
  skill: "cold_calling"  # ou "objection_handling", "closing"...
  niveau: "medium"

  ideal: |
    RDV démo fixé dans la semaine avec les 2 associés
    + Audit gratuit accepté

  acceptable: |
    RDV téléphonique de 30min fixé pour approfondir
    + Email de présentation à envoyer

  minimum: |
    Autorisation de rappeler à une date précise
    + Intérêt confirmé

  echec: |
    - "Rappelez-moi dans 6 mois" (sans date précise)
    - "Envoyez-moi un email" (poubelle)
    - Raccrochage

  criteres_succes:
    - "A identifié le besoin du prospect"
    - "A répondu à au moins 2 objections"
    - "A utilisé une preuve client pertinente"
    - "A proposé un next step concret"
    - "A gardé un ton professionnel même sous pression"
```

---

## 8. RÈGLES DE CONVERSATION

```yaml
regles:
  premier_message: |
    Le prospect décroche :
    "MétalPro, bonjour ?"
    (ton neutre, légèrement pressé)

  echanges_minimum: 6
  echanges_maximum: 18

  declencheurs_fin:
    - "au revoir"
    - "bonne journée"
    - "on se rappelle"
    - "envoyez-moi ça par email"
    - "je vous laisse"

  comportement_selon_jauge:
    0-20_hostile: |
      Ton sec, répond par monosyllabes.
      "Écoutez, j'ai pas le temps là..."
      Menace de raccrocher.

    21-40_resistant: |
      Objections en rafale.
      "Oui mais...", "C'est bien beau mais..."
      Cherche la faille.

    41-60_neutre: |
      Écoute poliment sans enthousiasme.
      "Mmh mmh", "D'accord", "Je vois"
      Ni pour ni contre.

    61-80_interesse: |
      Pose des questions.
      "Et concrètement comment ça marche?"
      "Vous avez des clients dans l'industrie?"
      Partage des infos sur sa situation.

    81-100_pret: |
      Signaux d'achat.
      "Et pour la mise en place, ça se passe comment?"
      "C'est quoi les délais?"
      "Mon associé est là jeudi, vous pouvez nous rappeler?"
```

---

## 9. MAPPING OBJECTIONS → PREUVES

| Objection | Preuve à utiliser |
|-----------|-------------------|
| "C'est cher" | TransLogistic : 45k€ de pertes avec ransomware |
| "On a déjà Avast" | Cabinet Martin : 15 failles détectées malgré antivirus |
| "J'ai pas le temps" | Installation en 2h, zéro interruption |
| "Je vous connais pas" | Certifié ANSSI, 1200 clients |
| "C'est pas prioritaire" | Ami de Jean-Pierre piraté récemment |
| "Faut voir avec mon associé" | Proposer démo à 2 |

---

## UTILISATION

Ce fichier peut être :
1. **Converti en JSON** pour le backend
2. **Utilisé par l'IA** pour générer des variantes
3. **Adapté par l'élève** avec son propre produit

L'IA génère dynamiquement le prospect en s'assurant que :
- Le besoin correspond au produit
- Les objections sont réalistes pour ce type de vente
- Les réponses possibles utilisent les preuves disponibles
