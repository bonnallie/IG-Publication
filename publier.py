#!/usr/bin/env python3
"""Publication Instagram des sorties Sexy Pace Collective.

Commandes :
  annonce --lieu SLUG [--date AAAA-MM-JJ] [--changement]   carrousel grille + 3 stories, enregistre sortie.json
  rappel                                                   stories de rappel (mer. 14h / ven. 15h) si dues
  stories                                                  republie tout de suite les 3 stories de la sortie courante
  kit                                                      affiche les textes pour Facebook / conversation privée

Variables d'environnement : IG_USER_ID, IG_ACCESS_TOKEN, IMAGE_BASE_URL
(optionnel : GRAPH_HOST, par défaut graph.facebook.com). Ajouter --dry-run pour ne rien publier.
"""
import argparse
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

RACINE = Path(__file__).resolve().parent
FUSEAU = ZoneInfo("America/Toronto")
SORTIE = RACINE / "sortie.json"
JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
        "septembre", "octobre", "novembre", "décembre"]
# rappels : jours avant la sortie -> heure locale minimale
RAPPELS = {3: 14, 1: 15}
DRY = False


def lieux():
    return json.loads((RACINE / "lieux" / "lieux.json").read_text(encoding="utf-8"))


def date_longue(d):
    return f"{JOURS[d.weekday()]} {d.day}{'er' if d.day == 1 else ''} {MOIS[d.month - 1]}"


def prochain_samedi(aujourdhui):
    return aujourdhui + dt.timedelta(days=(5 - aujourdhui.weekday()) % 7 or 7)


def fiche(slug):
    data = lieux()
    if slug not in data["lieux"]:
        sys.exit(f"Lieu inconnu : {slug}. Lieux disponibles : {', '.join(data['lieux'])}")
    manquants = [f for n in (1, 2, 3) for f in (f"story-{n}.jpg", f"grille-{n}.jpg")
                 if not (RACINE / "lieux" / slug / f).exists()]
    if manquants:
        sys.exit(f"Images manquantes pour {slug} : {', '.join(manquants)}")
    return data["lieux"][slug]


def legende(slug, date, changement=False):
    l = fiche(slug)
    entete = "⚠️ CHANGEMENT DE LIEU ⚠️\n\n" if changement else ""
    return (
        f"{entete}LONG RUN DU SAMEDI · {date_longue(date)}\n\n"
        f"📍 {l['nom']}\n{l['adresse']}\n\n"
        "8H > ROUTE\n± 9-10 km, 60 min, rythme Sexy Pace inclusif. Tous les niveaux bienvenus.\n\n"
        "9H > TRAIL\n± 11-13 km & 300-400 D+. Retour au même point de départ.\n\n"
        "Envie d'une longue? Enchaîne les deux! Juste le temps de changer de souliers, et hop, on repart.\n\n"
        "On part à l'heure pile. Arrive d'avance pour ne rien manquer.\n\n"
        "Qui sera de la partie?\n\n"
        "#sexypacecollective #longrun #courseapied #trailrunning #laurentides"
    )


def api(methode, chemin, **params):
    params["access_token"] = os.environ["IG_ACCESS_TOKEN"]
    hote = os.environ.get("GRAPH_HOST", "graph.facebook.com")
    url = f"https://{hote}/{chemin}"
    corps = urllib.parse.urlencode(params).encode()
    if methode == "GET":
        url, corps = f"{url}?{corps.decode()}", None
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=corps, method=methode), timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"Erreur API Meta ({e.code}) sur {chemin} : {e.read().decode(errors='replace')}")


def url_image(slug, fichier):
    return f"{os.environ['IMAGE_BASE_URL'].rstrip('/')}/lieux/{slug}/{fichier}"


def conteneur(**params):
    if DRY:
        print("  [dry-run] conteneur", {k: (v if len(str(v)) < 90 else str(v)[:90] + '…') for k, v in params.items()})
        return "DRY"
    return api("POST", f"{os.environ['IG_USER_ID']}/media", **params)["id"]


def publier(id_conteneur):
    if DRY:
        return "DRY"
    for _ in range(20):
        etat = api("GET", id_conteneur, fields="status_code").get("status_code")
        if etat in ("FINISHED", None):
            break
        if etat in ("ERROR", "EXPIRED"):
            sys.exit(f"Conteneur {id_conteneur} en état {etat}")
        time.sleep(3)
    return api("POST", f"{os.environ['IG_USER_ID']}/media_publish", creation_id=id_conteneur)["id"]


def publier_carrousel(slug, texte):
    print("Carrousel grille…")
    enfants = [conteneur(image_url=url_image(slug, f"grille-{n}.jpg"), is_carousel_item="true") for n in (1, 2, 3)]
    print("  publié :", publier(conteneur(media_type="CAROUSEL", children=",".join(enfants), caption=texte)))


def publier_stories(slug):
    for n in (1, 2, 3):
        print(f"Story {n}/3…")
        print("  publiée :", publier(conteneur(media_type="STORIES", image_url=url_image(slug, f"story-{n}.jpg"))))


def lire_sortie():
    if not SORTIE.exists():
        return None
    return json.loads(SORTIE.read_text(encoding="utf-8"))


def ecrire_sortie(s):
    if not DRY:
        SORTIE.write_text(json.dumps(s, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def cmd_annonce(a):
    maintenant = dt.datetime.now(FUSEAU)
    date = dt.date.fromisoformat(a.date) if a.date else prochain_samedi(maintenant.date())
    if date < maintenant.date():
        sys.exit(f"La date {date} est passée.")
    texte = legende(a.lieu, date, a.changement)
    print(texte, "\n")
    publier_carrousel(a.lieu, texte)
    publier_stories(a.lieu)
    ecrire_sortie({"lieu": a.lieu, "date": date.isoformat(), "rappels_faits": []})


def cmd_rappel(a):
    s = lire_sortie()
    maintenant = dt.datetime.now(FUSEAU)
    if not s:
        return print("Aucune sortie annoncée : rien à faire.")
    jours = (dt.date.fromisoformat(s["date"]) - maintenant.date()).days
    if jours not in RAPPELS or maintenant.hour < RAPPELS[jours]:
        return print(f"Pas de rappel dû (sortie dans {jours} j, {maintenant:%H:%M}).")
    cle = maintenant.date().isoformat()
    if cle in s["rappels_faits"]:
        return print("Rappel déjà publié aujourd'hui.")
    publier_stories(s["lieu"])
    s["rappels_faits"].append(cle)
    ecrire_sortie(s)


def cmd_stories(a):
    s = lire_sortie() or sys.exit("Aucune sortie annoncée.")
    publier_stories(s["lieu"])


def cmd_kit(a):
    s = lire_sortie() or sys.exit("Aucune sortie annoncée.")
    l, d = fiche(s["lieu"]), dt.date.fromisoformat(s["date"])
    print(f"""## Groupe Facebook (annonce)
{legende(s['lieu'], d).split(chr(10) + chr(10) + '#')[0]}

## Événement Facebook
Nom : Long run du samedi · {l['nom']}
Date : {date_longue(d)}, 8 h à 11 h
Lieu : {l['nom']}, {l['adresse']}
Description : même texte que l'annonce.

## Vendredi · groupe Facebook
C'est demain @tout le monde! {l['nom']}, {l['adresse']}. 8h route, 9h trail.

## Vendredi · conversation Instagram « Sexy... Trail ✌️ »
C'est demain tout le monde! 📍 {l['nom']}
Qui vient?
À 8h : (emoji au choix)
À 9h : (emoji au choix)""")


def main():
    global DRY
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dry-run", action="store_true")
    sp = p.add_subparsers(dest="cmd", required=True)
    an = sp.add_parser("annonce")
    an.add_argument("--lieu", required=True)
    an.add_argument("--date")
    an.add_argument("--changement", action="store_true")
    an.set_defaults(f=cmd_annonce)
    for nom, f in (("rappel", cmd_rappel), ("stories", cmd_stories), ("kit", cmd_kit)):
        sp.add_parser(nom).set_defaults(f=f)
    a = p.parse_args()
    DRY = a.dry_run
    if DRY:
        os.environ.setdefault("IMAGE_BASE_URL", "https://exemple.invalid")
        os.environ.setdefault("IG_USER_ID", "0")
    a.f(a)


if __name__ == "__main__":
    main()
