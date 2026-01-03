# Exemple Complet : Vente Solution IA d'Automatisation

Cet exemple montre un argumentaire commercial COMPLET,
comme un vrai playbook de vente.

---

## 1. LE VENDEUR

```yaml
vendeur:
  nom: "{{user.name}}"
  role: "Business Developer"
```

---

## 2. LA SOCIÉTÉ

```yaml
societe:
  nom: "AutomateAI"
  baseline: "L'IA qui travaille pour vous"
  secteur: "Éditeur IA / Automatisation"
  creation: "2022"
  taille: "18 employés"
  siege: "Paris"

  histoire: |
    Fondée par 2 anciens directeurs administratifs qui en avaient marre
    de voir leurs équipes perdre des heures sur des tâches répétitives.
    Ils ont créé la solution qu'ils auraient voulu avoir.

  mission: |
    Libérer les équipes des tâches administratives répétitives
    pour qu'elles se concentrent sur ce qui compte vraiment.

  valeurs:
    - "Simplicité d'usage"
    - "IA éthique et locale"
    - "Accompagnement humain"
```

---

## 3. LE PRODUIT - ARGUMENTAIRE COMPLET

### 3.1 LE PROBLÈME CLIENT

```yaml
probleme:
  titre: "Les tâches administratives tuent la productivité"

  constat: |
    Dans une entreprise moyenne, chaque employé perd 2 à 4 heures par jour
    sur des tâches répétitives et sans valeur ajoutée :
    - Trier et classer des emails
    - Répondre aux mêmes questions encore et encore
    - Chercher des documents
    - Saisir des données d'un système à l'autre
    - Faire des reporting manuels
    - Relancer des factures
    - Traiter des demandes clients récurrentes

  impact_chiffre:
    - "20h/semaine perdues par employé administratif"
    - "Coût caché : 15-25k€/an par employé en temps perdu"
    - "Erreurs humaines : 3-5% sur les tâches répétitives"
    - "Turnover : les bons éléments partent car ils s'ennuient"

  douleurs_par_persona:
    dirigeant:
      - "Je paie des gens qualifiés pour faire du copier-coller"
      - "Je n'ai pas de visibilité sur ce qui prend du temps"
      - "On rate des opportunités car on est noyés dans l'admin"

    daf:
      - "Les erreurs de saisie me coûtent cher"
      - "Le reporting prend 2 jours chaque mois"
      - "Je n'arrive pas à réduire les coûts sans licencier"

    manager_operationnel:
      - "Mon équipe est démotivée par les tâches répétitives"
      - "Je passe mon temps à vérifier leur travail"
      - "Les bons partent, je garde ceux qui acceptent la routine"

    employe:
      - "J'ai été embauché pour mon expertise, pas pour trier des mails"
      - "Je fais le même geste 50 fois par jour"
      - "Je m'ennuie, j'ai l'impression de ne servir à rien"
```

### 3.2 LA SOLUTION

```yaml
solution:
  nom: "AutomateAI Box"
  baseline: "Votre assistant IA qui automatise l'administratif"

  proposition_valeur: |
    On automatise vos tâches administratives répétitives grâce à des IA
    qui travaillent pour vous 24h/24, sur un serveur LOCAL dans vos bureaux.
    Résultat : vos équipes gagnent 10-15h par semaine et se concentrent
    sur ce qui compte vraiment.

  comment_ca_marche:
    resume: |
      On installe une petite box (un mini-serveur) dans vos locaux.
      Cette box contient des IA spécialisées qui apprennent vos process
      et automatisent vos tâches répétitives.

    etapes:
      1_audit:
        titre: "Audit de vos tâches (1 journée)"
        description: |
          On passe une journée avec vos équipes pour identifier
          les tâches répétitives et chronophages.
          On mesure le temps passé sur chaque tâche.
          Livrable : rapport avec potentiel d'automatisation.

      2_installation:
        titre: "Installation de la Box (2 heures)"
        description: |
          On installe le mini-serveur dans vos locaux.
          Connexion à votre réseau interne.
          Aucune donnée ne sort de chez vous.

      3_configuration:
        titre: "Configuration des agents IA (1-2 semaines)"
        description: |
          On programme les agents IA selon vos process.
          Chaque agent fait UNE tâche simple et la fait bien.
          On les connecte à vos outils (email, ERP, CRM...).

      4_formation:
        titre: "Formation de vos équipes (2 jours)"
        description: |
          Formation pratique avec vos vrais cas d'usage.
          Chaque employé apprend à "parler" à l'IA.
          Support dédié pendant 1 mois.

      5_production:
        titre: "Mise en production progressive"
        description: |
          On commence par les tâches les plus simples.
          On ajuste en fonction des retours.
          Montée en puissance sur 1 mois.

    technologie:
      architecture: "Multi-agents spécialisés"
      explication: |
        Plutôt qu'une grosse IA généraliste, on utilise plusieurs
        petites IA spécialisées. Chaque agent fait UNE chose :
        - Agent Tri : classe les emails entrants
        - Agent Réponse : répond aux questions fréquentes
        - Agent Extraction : extrait les données des documents
        - Agent Saisie : remplit les formulaires automatiquement
        - Agent Reporting : génère les rapports
        - Agent Relance : envoie les relances automatiques

      avantage: |
        Une IA spécialisée fait mieux qu'une IA généraliste.
        Si un agent a un problème, les autres continuent.
        On peut ajouter des agents selon vos besoins.

      local_vs_cloud: |
        TOUT tourne en LOCAL sur notre box dans vos locaux.
        Vos données ne sortent JAMAIS de chez vous.
        Pas de dépendance à Internet pour fonctionner.
        100% conforme RGPD par design.
```

### 3.3 LES BÉNÉFICES

```yaml
benefices:
  principal: "Gagnez 10-15h par semaine et par employé administratif"

  par_categorie:
    temps:
      - "10-15h gagnées par semaine par employé"
      - "Reporting automatique en temps réel"
      - "Réponses aux emails récurrents en quelques secondes"
      - "Plus de recherche de documents : l'IA sait où tout est"

    argent:
      - "ROI moyen de 300% la première année"
      - "Économie de 15-25k€/an par employé administratif"
      - "Réduction des erreurs de saisie de 95%"
      - "Pas besoin de recruter pour absorber la croissance"

    qualite:
      - "0 erreur sur les tâches répétitives"
      - "Traitement 24h/24, 7j/7"
      - "Cohérence des réponses aux clients"
      - "Traçabilité complète des actions"

    humain:
      - "Équipes recentrées sur les tâches à valeur ajoutée"
      - "Motivation et engagement en hausse"
      - "Réduction du turnover"
      - "Montée en compétence sur le pilotage de l'IA"

    conformite:
      - "100% RGPD : données en local"
      - "Traçabilité complète pour audits"
      - "Pas de données dans le cloud US"
```

### 3.4 LE PRIX

```yaml
prix:
  modele: "Box + Abonnement mensuel"

  detail:
    box:
      prix: "2 500€ HT (achat unique)"
      inclus:
        - "Mini-serveur haute performance"
        - "Installation sur site"
        - "Configuration de base"
        - "Garantie 3 ans"

    abonnement:
      starter:
        prix: "490€/mois"
        inclus:
          - "Jusqu'à 5 agents IA"
          - "Support email"
          - "Mises à jour incluses"
        pour_qui: "TPE, 1-10 employés"

      business:
        prix: "990€/mois"
        inclus:
          - "Jusqu'à 15 agents IA"
          - "Support téléphone prioritaire"
          - "1 journée d'optimisation/trimestre"
        pour_qui: "PME, 10-50 employés"

      enterprise:
        prix: "Sur devis"
        inclus:
          - "Agents illimités"
          - "Account manager dédié"
          - "SLA garanti"
        pour_qui: "ETI, 50+ employés"

  engagement: "12 mois (mensuel possible +20%)"

  garanties:
    - "30 jours satisfait ou remboursé"
    - "Audit gratuit sans engagement"
    - "ROI garanti ou on prolonge gratuitement"
```

### 3.5 PITCH COMMERCIAL

```yaml
pitch:
  accroche_30_secondes: |
    "Vous savez combien d'heures vos équipes perdent chaque semaine
    à trier des emails, saisir des données ou faire des reporting ?

    En moyenne, c'est 15 à 20 heures par personne.

    Chez AutomateAI, on installe une box avec des IA locales
    qui automatisent ces tâches répétitives.

    Résultat : vos équipes se concentrent sur ce qui compte,
    et vous économisez l'équivalent d'un mi-temps par employé."

  pitch_2_minutes: |
    "Je vais être direct : vos équipes administratives perdent
    probablement 15 à 20 heures par semaine sur des tâches répétitives.

    Trier des emails, répondre aux mêmes questions, saisir des données,
    chercher des documents, faire des reporting...
    Des tâches qu'un robot pourrait faire.

    Le problème c'est que jusqu'ici, les solutions d'automatisation
    c'était soit trop complexe, soit ça envoyait vos données dans le cloud,
    soit ça coûtait une fortune.

    Nous, on a créé AutomateAI Box.

    C'est un mini-serveur qu'on installe chez vous avec des IA spécialisées.
    Chaque IA fait UNE tâche et la fait parfaitement : trier, classer,
    répondre, extraire, saisir...

    On les programme selon VOS process.
    Vos données restent chez VOUS, 100% RGPD.
    Et après 2 jours de formation, vos équipes sont autonomes.

    Nos clients gagnent en moyenne 12 heures par semaine par employé.
    À 30€ de l'heure chargé, ça fait 1 500€ d'économie par mois
    pour un abonnement à 490€.

    On fait un audit gratuit pour mesurer votre potentiel d'automatisation ?"

  questions_decouvertes:
    situation:
      - "Combien de personnes avez-vous sur des fonctions administratives ?"
      - "Quelles sont les tâches qui prennent le plus de temps ?"
      - "Comment gérez-vous le tri des emails aujourd'hui ?"
      - "Combien de temps passe votre équipe sur le reporting ?"

    douleur:
      - "Qu'est-ce qui vous frustre le plus dans la gestion administrative ?"
      - "Avez-vous déjà calculé le coût de ces tâches répétitives ?"
      - "Que pourrait faire votre équipe si elle avait 10h de plus par semaine ?"
      - "Avez-vous du mal à recruter sur ces postes ?"

    impact:
      - "Combien vous coûte une erreur de saisie en moyenne ?"
      - "Que se passe-t-il quand un email client tombe dans les limbes ?"
      - "Quel impact sur vos équipes de faire ces tâches répétitives ?"

    decision:
      - "Qui d'autre serait concerné par ce type de décision ?"
      - "Avez-vous un budget prévu pour l'automatisation cette année ?"
      - "Qu'est-ce qui vous ferait dire 'oui, on y va' ?"

  phrases_cles:
    accroches:
      - "Combien d'heures perdez-vous chaque semaine à faire le travail d'un robot ?"
      - "Et si vos équipes pouvaient enfin se concentrer sur ce qui compte ?"
      - "Vos données restent chez vous. Point final."

    transitions:
      - "Ce que vous décrivez, c'est exactement ce que notre client X vivait..."
      - "C'est intéressant que vous disiez ça, parce que..."
      - "Justement, c'est pour ça qu'on a conçu..."

    preuves:
      - "Notre client Dupont & Fils a réduit son temps admin de 60%"
      - "En moyenne, nos clients voient le ROI en 3 mois"
      - "On a 47 PME qui utilisent la solution au quotidien"

    closing:
      - "On fait un audit gratuit la semaine prochaine ?"
      - "Je vous propose qu'on mesure ensemble votre potentiel"
      - "Qu'est-ce qui vous empêcherait de tester pendant 30 jours ?"
```

### 3.6 OBJECTIONS ET RÉPONSES

```yaml
objections:
  - objection: "C'est trop cher"
    variantes:
      - "On n'a pas le budget"
      - "2500€ + 490€/mois c'est costaud"
      - "On peut pas se permettre ça maintenant"

    ce_quil_pense_vraiment: |
      "Je ne vois pas le ROI" ou "J'ai peur de me faire avoir"

    reponse: |
      "Je comprends, c'est un investissement.

      Faisons le calcul ensemble :
      Vous avez 3 personnes sur l'administratif.
      Si chacune gagne 10h par semaine, ça fait 30h.
      À 25€ de l'heure chargé, ça fait 3 000€ par mois.

      L'abonnement est à 490€.
      Vous économisez 2 500€ par mois dès le premier mois.
      La box est rentabilisée en 1 mois.

      Et si le ROI n'est pas là après 30 jours, on vous rembourse."

    preuve: "Dupont & Fils : ROI atteint en 6 semaines"

  - objection: "On a déjà essayé l'automatisation, ça n'a pas marché"
    variantes:
      - "On a testé des outils, personne ne les utilise"
      - "L'IA c'est du bullshit marketing"
      - "Mes équipes vont jamais adopter"

    ce_quil_pense_vraiment: |
      "J'ai été déçu et je ne veux pas revivre ça"

    reponse: |
      "C'est justement pour ça qu'on fait différemment.

      Les outils classiques, c'est 'voilà le logiciel, démerdez-vous'.
      Nous, on passe 2 jours à former vos équipes sur LEURS cas d'usage.

      Et surtout, nos IA font UNE tâche chacune.
      C'est pas une usine à gaz généraliste.
      Si l'IA de tri des emails marche, les gens l'utilisent.
      Parce que ça leur fait gagner 1h par jour.

      Cabinet Martin : ils avaient testé 3 solutions avant nous.
      Adoption à 95% en 2 semaines. Pourquoi ?
      Parce que c'est simple et que ça marche."

    preuve: "Cabinet Martin : 3 échecs avant nous, 95% d'adoption"

  - objection: "C'est pas le moment"
    variantes:
      - "Rappelez-moi dans 6 mois"
      - "On est en pleine réorg"
      - "On verra l'année prochaine"

    ce_quil_pense_vraiment: |
      "J'ai d'autres priorités" ou "J'ai pas envie de gérer un projet de plus"

    reponse: |
      "Je comprends, vous avez beaucoup à gérer.

      Justement, combien de temps vos équipes perdent chaque semaine
      sur ces tâches répétitives ?

      Si c'est 15h par semaine et par personne, ça fait
      60h par mois. 720h par an. L'équivalent de 4 mois de travail.

      Chaque mois qu'on attend, c'est 60h de perdues.

      Et l'installation prend 2h. La formation 2 jours.
      Ce n'est pas un projet de 6 mois.

      On peut commencer par un audit gratuit d'1h
      pour voir si ça vaut le coup pour vous ?"

    preuve: "Chiffre impact : coût de l'attente"

  - objection: "Et la sécurité des données ?"
    variantes:
      - "Nos données sont sensibles"
      - "Le RGPD nous interdit d'utiliser l'IA"
      - "On ne peut pas envoyer nos données dans le cloud"

    ce_quil_pense_vraiment: |
      "J'ai peur d'une fuite de données"

    reponse: |
      "Excellente question, c'est exactement pour ça
      qu'on a conçu notre solution différemment.

      Notre box tourne 100% en LOCAL dans vos bureaux.
      Vos données ne sortent JAMAIS de chez vous.

      Pas de cloud américain.
      Pas d'envoi à OpenAI ou Google.
      L'IA tourne sur notre mini-serveur, dans votre réseau.

      On est les seuls à proposer ça.
      C'est pour ça que des cabinets comptables et des avocats
      nous font confiance.

      On peut vous montrer l'architecture technique si vous voulez."

    preuve: "Cabinet comptable Martin : données ultra-sensibles"

  - objection: "Mes employés vont avoir peur de perdre leur job"
    variantes:
      - "Ça va créer des tensions"
      - "Les syndicats vont bloquer"
      - "C'est sensible socialement"

    ce_quil_pense_vraiment: |
      "Je ne veux pas de conflit social"

    reponse: |
      "C'est une vraie préoccupation, et je vais être honnête :
      l'IA ne remplace pas les gens, elle les libère.

      Ce qu'on automatise, c'est le copier-coller, le tri d'emails,
      la saisie répétitive. Des tâches que personne n'aime faire.

      Vos employés ne perdent pas leur job.
      Ils arrêtent de faire le travail d'un robot
      et se concentrent sur ce qui demande de l'intelligence humaine.

      Chez Dupont & Fils, ils ont présenté le projet comme ça :
      'On vous enlève les tâches chiantes.'
      Les équipes ont applaudi.

      Et personne n'a été licencié.
      Ils ont absorbé 30% de croissance sans recruter."

    preuve: "Dupont & Fils : 0 licenciement, +30% d'activité absorbée"

  - objection: "Je dois en parler à mon associé / DG / DAF"
    variantes:
      - "C'est pas moi qui décide"
      - "Il faut que je valide en interne"
      - "Envoyez-moi une présentation"

    ce_quil_pense_vraiment: |
      "Je ne veux pas prendre la décision seul"

    reponse: |
      "Bien sûr, c'est normal.

      Pour faciliter la discussion avec votre [associé/DG/DAF],
      je peux vous préparer :

      1. Un résumé d'1 page avec le ROI chiffré pour votre cas
      2. Une simulation personnalisée du gain de temps
      3. 2-3 références dans votre secteur

      Et si vous voulez, je peux aussi participer à un call
      avec vous et votre [associé] pour répondre à ses questions.

      Qu'est-ce qui serait le plus utile pour le convaincre ?"

    preuve: "Proposer un call à 3"
```

### 3.7 LES PREUVES CLIENTS

```yaml
preuves:
  stats_globales:
    clients: "47 PME équipées"
    satisfaction: "4.8/5"
    heures_economisees: "12h/semaine en moyenne par employé"
    roi_moyen: "300% la première année"

  temoignages:
    - client:
        nom: "Pierre Dupont"
        poste: "Directeur Général"
        entreprise: "Dupont & Fils"
        secteur: "Négoce BTP"
        taille: "35 employés"

      avant: |
        - 4 personnes à l'administratif
        - 20h/semaine chacun sur tâches répétitives
        - Erreurs de saisie fréquentes
        - Retards de facturation

      apres: |
        - Mêmes 4 personnes, mais recentrées
        - 8h/semaine de tâches répétitives (vs 20h)
        - 0 erreur de saisie
        - Facturation J+1 au lieu de J+7

      resultats_chiffres:
        - "60% de réduction du temps admin"
        - "0 erreur de saisie (vs 3-5%)"
        - "ROI atteint en 6 semaines"
        - "+30% de croissance absorbée sans recruter"

      citation: |
        "Mes équipes admin passaient leur temps à faire du copier-coller.
        Maintenant elles gèrent la relation client.
        On a absorbé 30% de croissance sans recruter personne."

    - client:
        nom: "Sophie Martin"
        poste: "Gérante"
        entreprise: "Cabinet Martin Expertise"
        secteur: "Expert-comptable"
        taille: "12 employés"

      avant: |
        - Tri manuel de 200 emails/jour
        - Saisie des factures fournisseurs manuelle
        - Reporting mensuel = 2 jours de travail
        - Avaient testé 3 solutions avant (échecs)

      apres: |
        - Emails triés automatiquement
        - Factures extraites et saisies par l'IA
        - Reporting temps réel
        - Adoption à 95% dès la 2ème semaine

      resultats_chiffres:
        - "4h/jour gagnées sur le tri email"
        - "Saisie factures : 2min vs 15min"
        - "Reporting : temps réel vs 2 jours"
        - "Adoption : 95% (vs 30% solutions précédentes)"

      citation: |
        "On avait tout essayé : Zapier, des macros Excel, un stagiaire...
        AutomateAI c'est la première solution que l'équipe utilise vraiment.
        Parce que c'est simple et que ça marche."
```

---

## 4. LE PROSPECT (Généré par IA)

```yaml
prospect:
  identite:
    prenom: "François"
    nom: "Legrand"
    poste: "DAF"
    entreprise: "MétalService"
    secteur: "Industrie - Distribution"
    taille_entreprise: "45 employés"

  personnalite: "analytique"
  # Veut des chiffres, des preuves, du concret
  # Méfiant envers le "marketing"
  # Prend son temps pour décider

  besoin:
    situation_actuelle: |
      - 5 personnes au service admin/compta
      - Saisie manuelle des commandes (80/jour)
      - Tri emails clients = 2h/jour
      - Reporting Excel mensuel = 3 jours
      - Relances clients manuelles

    douleur: |
      Le mois dernier, une erreur de saisie a causé une livraison
      à la mauvaise adresse. Client furieux, avoir de 2000€.
      François passe ses week-ends à vérifier les saisies.

    enjeu: |
      - Croissance de 20% prévue l'an prochain
      - Impossible de recruter (personne ne veut faire de la saisie)
      - Besoin de fiabiliser sans exploser la masse salariale

    declencheur: |
      Le DG lui a demandé un plan pour "faire plus avec moins".
      Il cherche des solutions.

  objections_probables:
    - type: "preuve"
      exprimee: "Vous avez des références dans l'industrie ?"
      intensite: "forte"

    - type: "securite"
      exprimee: "Et nos données de prix, elles vont où ?"
      intensite: "forte"

    - type: "roi"
      exprimee: "Comment vous calculez le ROI ?"
      intensite: "moyenne"

    - type: "adoption"
      exprimee: "Mon équipe est pas très tech..."
      intensite: "moyenne"
```

---

## 5. OBJECTIFS DE LA SESSION

```yaml
objectifs:
  skill: "decouverte_besoins"  # ou objection_handling, closing
  niveau: "medium"

  ideal: "RDV audit gratuit fixé avec le DG et le DAF"
  acceptable: "Envoi proposition chiffrée + call de suivi fixé"
  minimum: "Accord pour recevoir une simulation ROI personnalisée"

  criteres_evaluation:
    - "A utilisé les questions de découverte"
    - "A chiffré l'impact pour le client"
    - "A répondu aux objections avec des preuves"
    - "A proposé un next step concret"
```
