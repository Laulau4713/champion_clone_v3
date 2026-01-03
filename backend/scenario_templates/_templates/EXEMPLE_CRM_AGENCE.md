# Exemple Complet : Vente de CRM pour Agences

Deuxième exemple avec un produit et un contexte différent.

---

## 1. LE VENDEUR

```yaml
vendeur:
  nom: "{{user.name}}"
  role: "Business Developer"
  experience: "junior"
```

---

## 2. LA SOCIÉTÉ

```yaml
societe:
  nom: "FlowCRM"
  secteur: "Éditeur SaaS"
  creation: "2021"
  taille: "22 employés"
  siege: "Bordeaux"
  positionnement: "Le CRM qui s'adapte aux agences, pas l'inverse"
  valeurs:
    - "Simplicité avant tout"
    - "Support réactif"
    - "Made in France"
```

---

## 3. LE PRODUIT

```yaml
produit:
  nom: "FlowCRM Agence"
  type: "SaaS"

  probleme_resolu: "Centraliser la gestion clients des agences (com, marketing, web) qui jonglent entre Excel, mails et post-its"

  pour_qui: "Agences de 5 à 50 personnes (communication, marketing, web, RP)"

  fonctionnement: |
    1. Import de vos contacts en 1 clic (Excel, Gmail, LinkedIn)
    2. Pipeline visuel de vos opportunités (drag & drop)
    3. Suivi des projets clients intégré
    4. Rappels automatiques pour ne jamais oublier un suivi

  benefices_cles:
    - "Vue 360° de chaque client (historique, projets, factures)"
    - "Pipeline de vente visuel et intuitif"
    - "Intégration native avec les outils agence (Slack, Gmail, Notion)"
    - "Rapports automatiques pour le dirigeant"

  prix:
    modele: "Par utilisateur"
    entree_de_gamme: "29€/utilisateur/mois"
    offre_populaire: "49€/utilisateur/mois (avec intégrations)"
    engagement: "Mensuel ou annuel (-20%)"

  differenciateur: "Le seul CRM conçu PAR des anciens d'agence POUR les agences. Interface épurée, pas de fonctionnalités inutiles, prise en main en 30 minutes."

  garanties:
    - "14 jours d'essai gratuit"
    - "Import de données offert"
    - "Formation visio incluse"
    - "Sans engagement"
```

---

## 4. LES PREUVES

```yaml
preuves:
  stats:
    nb_clients: "350+ agences"
    satisfaction: "4.9/5 sur G2"
    anciennete: "Depuis 2021"
    resultat_moyen: "+40% d'opportunités trackées, -2h/semaine de reporting"

  temoignages:
    - client:
        nom: "Julie Petit"
        poste: "Fondatrice"
        entreprise: "Agence Pépite"
        secteur: "Communication"
        taille: "8 personnes"
      probleme_initial: |
        Fichier Excel partagé = chaos total.
        Opportunités oubliées, doublons de prospection.
        Impossible de savoir où en était chaque commercial.
      solution_apportee: |
        Migration en 1 journée.
        Chaque commercial a sa vue, la direction voit tout.
        Rappels automatiques = plus d'oublis.
      resultat_chiffre: "30% de CA en plus dès le 2ème trimestre"
      citation: "On a signé 3 clients qu'on aurait oubliés avec l'ancien système. FlowCRM s'est rentabilisé en 2 semaines."

    - client:
        nom: "Thomas Renard"
        poste: "Directeur associé"
        entreprise: "Digital Factory"
        secteur: "Agence web"
        taille: "25 personnes"
      probleme_initial: |
        Utilisait Salesforce, trop complexe et trop cher.
        Les équipes ne l'utilisaient pas vraiment.
        500€/mois pour un outil sous-exploité.
      solution_apportee: |
        Switch vers FlowCRM en 1 semaine.
        Formation de 30 min par équipe.
        Prix divisé par 3.
      resultat_chiffre: "Taux d'utilisation passé de 30% à 95%"
      citation: "Salesforce c'est une Ferrari pour aller chercher le pain. FlowCRM c'est exactement ce qu'il nous fallait, ni plus ni moins."

  references:
    - "Agence Pépite"
    - "Digital Factory"
    - "Com'Unity"
    - "WebForce3"
    - "RP & Co"

  certifications:
    - "Hébergement France (Scaleway)"
    - "Conforme RGPD"
    - "SOC 2 en cours"
```

---

## 5. LA CONCURRENCE

```yaml
concurrence:
  concurrent_principal:
    nom: "Pipedrive"
    positionnement: "CRM simple pour commerciaux"
    forces:
      - "Interface intuitive"
      - "Connu et reconnu"
      - "Beaucoup d'intégrations"
    faiblesses:
      - "Pas pensé pour les agences (pas de gestion projet)"
      - "Support en anglais"
      - "Données hébergées aux US"
    prix_comparatif: "Prix similaire mais moins adapté aux agences"

  concurrent_secondaire:
    nom: "HubSpot"
    positionnement: "Suite marketing complète"
    forces:
      - "Gratuit pour commencer"
      - "Très complet"
    faiblesses:
      - "Devient très cher dès qu'on veut des fonctionnalités"
      - "Usine à gaz"
      - "Conçu pour les startups tech, pas les agences"
    prix_comparatif: "Gratuit puis 800€/mois pour être utile"

  notre_avantage: |
    FlowCRM = le CRM des agences. Conçu par des anciens d'agence.
    Pas de fonctionnalités inutiles, juste ce qu'il faut.
    Support français réactif, hébergement France.

  argument_switch: |
    "Vous payez pour un outil générique que personne n'utilise vraiment.
    FlowCRM est fait pour votre métier. Vos équipes l'adopteront
    parce qu'il leur fait gagner du temps, pas perdre."

  facilite_migration: |
    - Export de votre ancien CRM en 1 clic
    - Import dans FlowCRM en 10 minutes
    - On vous accompagne gratuitement
```

---

## 6. LE PROSPECT (Exemple généré)

```yaml
prospect:
  identite:
    prenom: "Camille"
    nom: "Durand"
    poste: "Directrice Générale"
    entreprise: "StudioCréa"
    secteur: "Agence de communication"
    taille_entreprise: "12 personnes"
    localisation: "Lyon"

  personnalite: "speed"
  # Traits : parle vite, veut aller à l'essentiel,
  # pas le temps pour le blabla, mais ouverte si c'est pertinent

  contexte_appel: |
    Appel suite à un téléchargement de votre guide
    "10 erreurs de prospection en agence".
    Elle l'a téléchargé il y a 3 jours mais pas encore lu.
    Elle décroche entre deux meetings.

  besoin:
    situation_actuelle: |
      - Prospection sur Excel + Notion
      - Chaque commercial a son fichier
      - Pas de visibilité sur le pipeline global
      - Reporting manuel chaque vendredi (1h perdue)

    douleur: |
      A perdu un gros appel d'offres parce que personne n'avait relancé.
      Le client a signé avec un concurrent.
      "On ne savait même pas qu'on était en compétition finale."

    enjeu: |
      - Agence en croissance (objectif +30% cette année)
      - Recrute 2 nouveaux commerciaux
      - Besoin de process avant d'agrandir l'équipe

    declencheur: |
      Le téléchargement du guide = elle cherche des solutions.
      Timing parfait pour proposer une démo.

  objections:
    - type: "timing"
      exprimee: "Là on est en plein rush pour un pitch, c'est pas le moment..."
      cachee: "J'ai pas la bande passante pour un nouveau projet"
      intensite: "forte"
      reponse_cle: |
        → Justement, pour le prochain pitch vous aurez un vrai suivi
        → Setup en 30min, formation en 1h
        → "Quand est le pitch? On peut caler la démo juste après?"

    - type: "budget"
      exprimee: "Combien ça coûte? On a des budgets serrés..."
      cachee: "J'ai peur que ça coûte aussi cher que Salesforce"
      intensite: "moyenne"
      reponse_cle: |
        → 49€/utilisateur, soit 600€/mois pour 12 personnes
        → Moins cher qu'un freelance 1 jour/mois
        → Digital Factory économise 300€/mois vs Salesforce

    - type: "statu_quo"
      exprimee: "On a notre système avec Notion, ça fonctionne..."
      cachee: "Flemme de changer les habitudes de l'équipe"
      intensite: "moyenne"
      reponse_cle: |
        → L'appel d'offres perdu, c'était à cause de Notion?
        → Les nouveaux commerciaux vont galérer avec un système maison
        → Agence Pépite utilisait aussi Notion → +30% de CA après switch

    - type: "adoption"
      exprimee: "Mon équipe va jamais l'utiliser..."
      cachee: "On a déjà essayé des outils, personne ne s'en sert"
      intensite: "forte"
      reponse_cle: |
        → Digital Factory : utilisation passée de 30% à 95%
        → Interface ultra simple, prise en main en 30 min
        → On fait la formation avec votre équipe
```

---

## 7. OBJECTIFS DE LA SESSION

```yaml
objectifs:
  skill: "decouverte_besoins"
  niveau: "easy"

  ideal: "Démo fixée cette semaine avec l'équipe commerciale"
  acceptable: "Call de 20min fixé pour approfondir les besoins"
  minimum: "Autorisation d'envoyer une vidéo démo personnalisée"
  echec: "Pas d'intérêt, renvoi vers le guide téléchargé"

  criteres_succes:
    - "A creusé le problème de l'appel d'offres perdu"
    - "A identifié les 2 nouveaux commerciaux comme déclencheur"
    - "A répondu à l'objection timing"
    - "A proposé une démo courte et concrète"
```

---

## 8. RÈGLES DE CONVERSATION

```yaml
regles:
  premier_message: |
    Camille décroche rapidement :
    "Oui allô?"
    (ton pressé, on entend du bruit de bureau)

  echanges_minimum: 5
  echanges_maximum: 12

  specificite_prospect: |
    Camille parle vite et coupe la parole si on est trop lent.
    Elle apprécie qu'on aille droit au but.
    Si on lui fait perdre son temps, elle raccroche.
    Mais si on lui montre qu'on comprend son problème, elle s'ouvre.

  comportement_selon_jauge:
    0-30_hostile: |
      "Écoutez j'ai vraiment pas le temps là..."
      Soupirs audibles, répond par oui/non.
      Cherche à raccrocher.

    31-50_resistant: |
      "Oui j'ai téléchargé votre truc, et?"
      Teste si vous allez au but.
      Objections rapides.

    51-70_neutre: |
      "Ok, expliquez-moi en 2 minutes"
      Écoute mais chronomètre.
      "Et concrètement?"

    71-85_interessee: |
      "Ah oui c'est exactement notre problème avec l'appel d'offres..."
      Partage des détails.
      Pose des questions.

    86-100_prete: |
      "Ok vous avez 15 minutes jeudi pour me montrer?"
      Propose des créneaux.
      "Envoyez-moi une invitation"
```

---

## MAPPING OBJECTIONS → PREUVES

| Objection | Preuve à utiliser |
|-----------|-------------------|
| "Pas le temps" | Setup en 30min, formation 1h |
| "C'est cher" | Digital Factory : -300€/mois vs Salesforce |
| "On a Notion" | Agence Pépite +30% CA après switch de Notion |
| "L'équipe va pas l'utiliser" | Digital Factory : 30% → 95% d'utilisation |
| "On connaît pas" | 350 agences clientes, 4.9/5 sur G2 |
