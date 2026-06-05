# Déploiement GitHub — INTELO2026

**Organisation :** https://github.com/INTELO2026  
**Dépôt participants (public) :** https://github.com/INTELO2026/fraud-challenge

---

## Maintenant : quoi faire, dans l’ordre

### Étape A — Créer le dépôt sur GitHub (2 min)

1. Connectez-vous à l’org [INTELO2026](https://github.com/INTELO2026).
2. **New repository** → nom : `fraud-challenge`
3. Visibilité : **Public**
4. **Ne cochez pas** « Add a README » (vous poussez depuis votre PC).

### Étape B — Pousser le code depuis votre machine (5 min)

Dans PowerShell :

```powershell
cd "d:\Projet\Hackathin IT"

git init
git add README.md fraud_detection.py tests data scripts .github requirements.txt pytest.ini .gitignore DEPLOIEMENT.md
git commit -m "Hackathon INTELO2026: défi fraude + CI"
git branch -M main
git remote add origin https://github.com/INTELO2026/fraud-challenge.git
git push -u origin main
```

**Important :** ne faites **pas** `git add organisateur/` sur ce dépôt public.

### Étape C — Réglages du dépôt (5 min)

Sur https://github.com/INTELO2026/fraud-challenge → **Settings** :

| Menu | Réglage |
|------|---------|
| **Actions → General** | Autoriser les workflows sur les **pull requests depuis les forks** |
| **Branches → Add branch ruleset** (ou classic protection) | Branche `main` : exiger une PR, exiger le check **Hackathon — Score tests publics** |

### Étape D — Test organisateur (10 min)

1. Avec **votre compte perso**, forkez `INTELO2026/fraud-challenge`.
2. Clonez le fork, modifiez une ligne dans `README.md`, push.
3. Ouvrez une **PR** vers `INTELO2026/fraud-challenge` → onglet **Checks** : la CI doit tourner et afficher le score **X/11**.

### Étape E — Message aux participants (jour J)

Copier-coller :

```
Dépôt officiel : https://github.com/INTELO2026/fraud-challenge

1. Forkez ce dépôt (bouton Fork en haut à droite)
2. Clonez VOTRE fork : git clone https://github.com/VOTRE-PSEUDO/fraud-challenge.git
3. pip install -r requirements.txt
4. pytest tests/ -v
5. Implémentez detect_fraud dans fraud_detection.py (pas de site web obligatoire)
6. git push puis ouvrez une Pull Request vers INTELO2026/fraud-challenge
7. La CI affiche X/11 tests publics passés
```

---

## Classement final (organisateurs)

La CI publique ne lance que les **11 tests visibles**. Pour le podium (21 tests) :

```powershell
python organisateur/scripts/validate_epreuve.py
python organisateur/scripts/score_submission.py C:\chemin\vers\fork-du-participant
```

Gardez le dossier `organisateur/` en local ou dans un repo **privé** séparé.

---

## Checklist veille / matin

- [ ] Repo public live : https://github.com/INTELO2026/fraud-challenge
- [ ] `python organisateur/scripts/validate_epreuve.py` → 21/21
- [ ] Test fork + PR → CI + score X/11
- [ ] Canal support (Discord/Slack)

## Quota GitHub Actions

Repo public sous org : minutes Actions incluses (souvent suffisant pour ~100 participants si runs ~1 min).
