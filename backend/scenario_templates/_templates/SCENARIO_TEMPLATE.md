# Template de Scénario Commercial

Ce fichier définit la structure complète d'un scénario de training commercial.
Le flow est centré sur le vendeur, pas sur le prospect.

---

## Structure du Scénario

```
VENDEUR → SOCIÉTÉ → PRODUIT → PREUVES → PROSPECT (besoin + objections)
```

---

## 1. LE VENDEUR

Qui est le commercial qui passe l'appel ?

```yaml
vendeur:
  # Rempli automatiquement avec le profil de l'élève
  nom: "{{user.name}}"
  experience: "{{user.experience_level}}"  # junior, confirmé, senior
```

---

## 2. LA SOCIÉTÉ

Pour quelle entreprise travaille le vendeur ?

```yaml
societe:
  nom: ""                    # Nom de l'entreprise
  secteur: ""                # Secteur d'activité
  creation: ""               # Année de création
  taille: ""                 # Nombre d'employés
  siege: ""                  # Localisation
  positionnement: ""         # En 1 phrase: qu'est-ce qui vous rend unique?
  valeurs: []                # 2-3 valeurs clés
```

---

## 3. LE PRODUIT / LA SOLUTION

Qu'est-ce que le vendeur vend ?

```yaml
produit:
  nom: ""                    # Nom commercial
  type: ""                   # SaaS, Service, Produit physique, Conseil...

  # Le problème résolu (CRUCIAL)
  probleme_resolu: ""        # En 1 phrase: quel problème vous réglez?
  pour_qui: ""               # Cible idéale (taille, secteur, profil)

  # Comment ça marche
  fonctionnement: ""         # Explication simple en 2-3 phrases
  benefices_cles:            # Les 3-4 bénéfices principaux
    - ""
    - ""
    - ""

  # Prix
  prix:
    modele: ""               # Par utilisateur, forfait, à l'usage...
    entree_de_gamme: ""      # Prix de départ
    offre_populaire: ""      # L'offre la plus vendue
    engagement: ""           # Mensuel, annuel, sans engagement

  # Différenciation
  differenciateur: ""        # LA raison de vous choisir vs concurrence

  # Garanties
  garanties:
    - ""                     # Essai gratuit, satisfait ou remboursé...
```

---

## 4. LES PREUVES (Clients Satisfaits)

Ce sont les armes du vendeur pour répondre aux objections.

```yaml
preuves:
  # Statistiques globales
  stats:
    nb_clients: ""           # "500+ clients"
    satisfaction: ""         # "4.8/5"
    anciennete: ""           # "Depuis 2019"
    resultat_moyen: ""       # "+30% de productivité en moyenne"

  # Témoignages clients (2-3 minimum)
  temoignages:
    - client:
        nom: ""              # Nom du contact
        poste: ""            # Son poste
        entreprise: ""       # Nom de l'entreprise
        secteur: ""          # Secteur d'activité
        taille: ""           # Taille de l'entreprise
      probleme_initial: ""   # Quel était son problème?
      solution_apportee: ""  # Comment vous l'avez résolu
      resultat_chiffre: ""   # Résultat mesurable
      citation: ""           # Verbatim du client

  # Références notables (logos, noms connus)
  references:
    - ""
    - ""

  # Certifications / Labels
  certifications:
    - ""
```

---

## 5. LA CONCURRENCE

Contre qui le vendeur se bat ?

```yaml
concurrence:
  concurrent_principal:
    nom: ""
    positionnement: ""       # Comment ils se présentent
    forces: []               # Ce qu'ils font bien
    faiblesses: []           # Leurs points faibles
    prix_comparatif: ""      # Plus cher, moins cher, similaire

  notre_avantage: ""         # Pourquoi nous choisir vs eux (1 phrase)

  # Objection "On a déjà un prestataire"
  argument_switch: ""        # Pourquoi changer?
  facilite_migration: ""     # Comment on facilite la transition
```

---

## 6. LE PROSPECT (Généré par IA)

Le prospect est généré dynamiquement en fonction du produit.
Il a un BESOIN réel mais aussi des OBJECTIONS à lever.

```yaml
prospect:
  # Identité
  identite:
    nom: ""
    prenom: ""
    poste: ""                # Décideur, influenceur, utilisateur
    entreprise: ""
    secteur: ""
    taille_entreprise: ""

  # Personnalité (affecte le ton des réponses)
  personnalite: ""           # pressé, méfiant, sympathique, analytique, émotif

  # LE BESOIN (ce qui fait que le produit est pertinent)
  besoin:
    situation_actuelle: ""   # Comment il gère aujourd'hui
    douleur: ""              # Ce qui lui pose problème
    enjeu: ""                # Pourquoi c'est important
    declencheur: ""          # Ce qui pourrait le faire bouger maintenant

  # LES OBJECTIONS (les freins à l'achat)
  objections:
    - type: "budget"
      exprimee: ""           # Ce qu'il dit
      cachee: ""             # Ce qu'il pense vraiment
      intensite: ""          # faible, moyenne, forte

    - type: "timing"
      exprimee: ""
      cachee: ""
      intensite: ""

    - type: "concurrence"
      exprimee: ""
      cachee: ""
      intensite: ""

    - type: "confiance"
      exprimee: ""
      cachee: ""
      intensite: ""

    - type: "decision"
      exprimee: ""
      cachee: ""
      intensite: ""

    - type: "statu_quo"
      exprimee: ""
      cachee: ""
      intensite: ""
```

---

## 7. LES TYPES D'OBJECTIONS

### Budget
- "C'est trop cher"
- "On n'a pas le budget"
- "C'est pas prévu"
- **Réponse type:** ROI, coût de l'inaction, facilités de paiement

### Timing
- "Pas maintenant"
- "Rappelez-moi en septembre"
- "On est en plein rush"
- **Réponse type:** Urgence, coût de l'attente, simplicité de mise en place

### Concurrence
- "On a déjà quelqu'un"
- "On utilise [concurrent]"
- "Mon neveu s'en occupe"
- **Réponse type:** Différenciation, témoignage de switch, complémentarité

### Confiance
- "Je vous connais pas"
- "C'est quoi votre boîte?"
- "Vous êtes fiables?"
- **Réponse type:** Références, certifications, essai gratuit, garanties

### Décision
- "C'est pas moi qui décide"
- "Faut que j'en parle à mon associé"
- "Le DG doit valider"
- **Réponse type:** Préparer un dossier, proposer un call commun, identifier le décideur

### Statu Quo
- "Ça fonctionne bien comme ça"
- "On a toujours fait comme ça"
- "Pourquoi changer?"
- **Réponse type:** Risques de ne rien faire, opportunités manquées, évolution du marché

---

## 8. OBJECTIFS DE LA SESSION

```yaml
objectifs:
  # Selon le skill pratiqué
  skill: ""                  # cold_calling, objection_handling, closing...
  niveau: ""                 # easy, medium, expert

  # Objectifs
  ideal: ""                  # Le meilleur résultat possible
  acceptable: ""             # Un résultat correct
  minimum: ""                # Le minimum acceptable
  echec: ""                  # Ce qui constitue un échec

  # Critères de succès
  criteres:
    - ""
    - ""
```

---

## 9. RÈGLES DE CONVERSATION

```yaml
regles:
  # Démarrage
  premier_message: ""        # Qui parle en premier et dit quoi

  # Durée
  echanges_minimum: 5        # Avant de pouvoir closer
  echanges_maximum: 20       # Fin automatique après

  # Fin de conversation
  declencheurs_fin:
    - "au revoir"
    - "bonne journée"
    - "je vous laisse"
    - "on se rappelle"

  # Comportement du prospect selon la jauge
  jauge_comportement:
    hostile: "Répond sèchement, menace de raccrocher"
    resistant: "Objections en rafale, sceptique"
    neutre: "Écoute sans enthousiasme"
    interesse: "Pose des questions, s'ouvre"
    pret_a_acheter: "Signaux d'achat, questions pratiques"
```
