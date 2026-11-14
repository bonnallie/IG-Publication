# Publications Sexy Pace Collective

Automatise l'annonce du long run du samedi. L'utilisateur parle français (Québec) ; réponses directes, sans préambule.

## Qui fait quoi

- **Instagram (grille + stories)** : `publier.py`, lancé par GitHub Actions avec l'API Meta. Secrets du dépôt : `IG_USER_ID`, `IG_ACCESS_TOKEN`.
- **Groupe Facebook, événement Facebook, conversation Instagram « Sexy... Trail ✌️ »** : aucune API. L'utilisateur le fait faire par l'extension Claude pour Chrome, ou colle le texte lui-même.
- La Page Facebook n'est pas utilisée pour publier.

## Quand l'utilisateur dit « fais la publication pour <lieu> pour samedi »

1. Vérifier que `lieux/<slug>/` existe avec ses 6 JPEG. Sinon, voir « Nouveau lieu ».
2. Demander l'heure de publication si elle n'est pas donnée (sinon : tout de suite).
3. Lancer le workflow `annonce.yml` (outil GitHub `actions_run_trigger`) avec `lieu`, et `date` si ce n'est pas samedi prochain. La légende par défaut est courte (« 🚨21 novembre 👈 Voici les infos pour ce weekend! On se voit bientôt! :D ») car tout est déjà dans les visuels ; de temps en temps, proposer une variante créative via `legende` (la ligne de date est ajoutée automatiquement). Il publie le carrousel et les 3 stories, puis enregistre `sortie.json`.
4. Vérifier que l'exécution a réussi, puis donner à l'utilisateur deux consignes prêtes à coller dans l'extension Chrome (texte : `python3 publier.py kit`, aussi dans le résumé de l'exécution) :
   - maintenant : publier l'annonce dans https://www.facebook.com/groups/sexypace et y créer l'événement ;
   - vendredi 15 h : « C'est demain @tout le monde » dans le groupe, et le message « qui vient ? » dans la conversation Instagram, avec deux emojis au choix (thème libre, différents chaque semaine) pour 8h et 9h.

Les rappels en stories partent seuls (`rappels.yml`) : mercredi 14 h et vendredi 15 h, heure de Montréal, seulement si `sortie.json` vise le samedi qui vient.

## Changement de lieu de dernière minute

Relancer `annonce.yml` avec le nouveau lieu et `changement: true`. Dire à l'utilisateur de supprimer l'ancienne publication à la main et lui redonner les consignes Chrome corrigées.

## Nouveau lieu

Il faut 3 visuels 1080x1920 fournis par l'utilisateur (le texte est incrusté dans l'image). Les déposer en `lieux/<slug>/1.png`, `2.png`, `3.png`, ajouter la fiche dans `lieux/lieux.json`, lancer `python3 outils/preparer_images.py`, pousser.

## Tester sans publier

`python3 publier.py --dry-run annonce --lieu kohi`
