# Mirroring iPad → Windows (Python)

Affiche l'écran d'un **iPad** (branché en USB-C) en direct sur un PC **Windows**,
**sans changer aucun pilote** (pas de Zadig) : on passe par les **services développeur
d'Apple** via la librairie `pymobiledevice3`.

> Testé pour un **iPad 10ᵉ génération** (USB-C). Compatible iPhone/iPad iOS 16 et +.

## Deux modes selon la version de l'iPad

| Mode | Version iPad | Méthode | Fluidité | Lanceur |
|------|--------------|---------|----------|---------|
| **Captures** | iOS 16 → 26.x | screenshots PNG (`app.py`) | ~5–20 fps | `lancer_maintenant.bat` |
| **Vidéo HEVC** | **iPadOS 27+** | flux vidéo, fenêtre native (`app_ios27.py`) | ~40–60 fps | `lancer_ios27.bat` |

Le **mode vidéo HEVC** (fluide) est une
fonctionnalité Apple **verrouillée à iPadOS 27 ou plus** : l'iPad lui-même refuse le flux
sur les versions antérieures (`Remote control requires iOS 27.0 or later`). iPadOS 27 est
sorti le **14 septembre 2026** (l'iPad 10ᵉ génération est compatible) : mettre l'iPad à jour
pour profiter du mode vidéo. Sur une version plus ancienne, le **mode captures** reste la seule option.

---

## 1. Contenu du projet

| Fichier                  | Rôle                                                                        |
|--------------------------|-----------------------------------------------------------------------------|
| **`mirror.bat`** ⭐       | **Double-clic recommandé** : détecte la version de l'iPad et lance **tout seul** la bonne méthode. |
| `lancer_maintenant.bat`  | Double-clic : force le mode captures (tunnel + montage + `app.py`).          |
| `lancer_ios27.bat`       | Double-clic : force le mode vidéo HEVC (à utiliser dès iPadOS 27).           |
| `app.py`                 | L'application de capture : affiche l'écran de l'iPad dans une fenêtre.       |
| `app_ios27.py`           | Fenêtre native **fluide** (flux HEVC), juste la vidéo — **uniquement iPadOS 27+**. |
| `_env.bat`               | Utilisé par les lanceurs : crée l'environnement Python local `.venv` et y installe les dépendances. |
| `requirements.txt`       | Les dépendances Python à installer.                                         |
| `README.md`              | Ce guide (installation, activation, dépannage).                             |

> Tous les `.bat` demandent automatiquement les **droits administrateur** (le tunnel l'exige),
> ouvrent une fenêtre **« Tunnel »** à laisser ouverte, montent l'image développeur, puis lancent
> le mode adapté. **En pratique : double-clic sur `mirror.bat` et c'est tout** — il choisit
> automatiquement les captures (iPadOS < 27) ou la vidéo HEVC (iPadOS 27+). Les deux
> `lancer_*.bat` ne servent qu'à forcer un mode précis.

---

## 2. Prérequis (à faire UNE fois sur le PC)

### a) Python
Installer **Python 3.x** (https://www.python.org). Cocher **« Add Python to PATH »** à l'installation.

### b) Pilotes USB Apple — **ÉTAPE CRITIQUE**
Windows ne « parle » à l'iPad (autrement que pour les photos) **que si les pilotes Apple sont installés**.
Installer **l'un** des deux :
- **App « Appareils Apple »** depuis le Microsoft Store *(le plus simple)*, **ou**
- **iTunes** depuis https://www.apple.com/itunes/ *(la version du site Apple)*.

Lancer le logiciel une fois, brancher l'iPad, et accepter **« Faire confiance à cet ordinateur »**.

### c) Câble
Utiliser un câble **USB-C de données** (beaucoup de câbles ne servent qu'à la charge).
Brancher directement sur un port du PC (pas via un hub/station d'accueil).

### d) Dépendances Python — automatique
Rien à faire : au premier lancement, les `.bat` créent un **environnement Python local**
`.venv` dans ce dossier et y installent les dépendances (`requirements.txt`). Rien n'est
installé dans le Python global de l'ordi ; supprimer le dossier `.venv` suffit à tout retirer.
Si `requirements.txt` change, les dépendances sont réinstallées automatiquement.

Pour les commandes manuelles de ce guide, utiliser le Python du `.venv` : soit l'activer
(`.venv\Scripts\activate`), soit remplacer `python` par `.venv\Scripts\python.exe`.

---

## 3. Activer le mode développeur sur l'iPad

Le mode développeur est **obligatoire** pour la capture d'écran. ⚠️ **Point piège :**
l'entrée « Mode développeur » **n'apparaît pas** dans les Réglages tant qu'un outil de
développement n'a pas parlé à l'iPad au moins une fois.

### Étape 1 — Vérifier que l'iPad est bien détecté
```
python -m pymobiledevice3 usbmux list
```
- L'iPad doit apparaître dans la liste.
- **Liste vide ?** → voir le **Dépannage** plus bas (cause n°1 : pilotes Apple).

### Étape 2 — Faire apparaître / activer le mode développeur
```
python -m pymobiledevice3 amfi enable-developer-mode
```
- L'iPad **redémarre**, puis affiche **« Activer le mode développeur ? »** → **Activer** (+ code).
- **Si la commande dit qu'elle ne peut pas activer à cause du code de verrouillage** →
  voir le **Dépannage** (cause n°3).

### Étape 3 — Vérifier
Sur l'iPad : **Réglages → Confidentialité et sécurité → Mode développeur** doit être **activé**.

---

## 4. Lancer (le plus simple : double-clic)

Brancher l'iPad, le déverrouiller, puis **double-cliquer sur `mirror.bat`**. C'est tout.

`mirror.bat` détecte la version de l'iPad et choisit la bonne méthode automatiquement :
- iPadOS **< 27** → mode captures (une fenêtre affiche l'écran ; **quitter :** `q` ou `Échap`).
- iPadOS **27+** → mode vidéo HEVC (une fenêtre affiche l'écran ; `f` = plein écran,
  **quitter :** `q` ou `Échap`).

Dans les deux cas il demande les droits admin, ouvre une fenêtre **« Tunnel »** (à laisser
ouverte) et monte l'image développeur avant de démarrer.

> Pour **forcer** un mode sans détection, utiliser `lancer_maintenant.bat` (captures) ou
> `lancer_ios27.bat` (HEVC).

### Lancement manuel (si tu préfères les commandes)

Sur iOS/iPadOS **17+**, les services développeur exigent **deux prérequis** : un **tunnel**
lancé **en administrateur** et l'**image développeur (DDI) montée**.

1. Terminal **administrateur**, à **laisser ouvert** :
   ```
   python -m pymobiledevice3 remote tunneld
   ```
2. Autre terminal (normal), monter l'image développeur (une fois par redémarrage de l'iPad) :
   ```
   python -m pymobiledevice3 mounter auto-mount
   python -m pymobiledevice3 mounter list      REM doit afficher une image, pas []
   ```
3. Lancer le mode voulu :
   - Mode captures : `python app.py`
   - Mode vidéo HEVC (iPadOS 27+) : `python app_ios27.py`

---

## 4 bis. Mode vidéo HEVC (iPadOS 27+) — détails

Sur **iPadOS 27+**, `mirror.bat` / `lancer_ios27.bat` ouvrent **`app_ios27.py`** : une fenêtre
qui affiche **uniquement l'écran de l'iPad**, sans aucune interface.

- **Fluidité :** ~40–60 fps mesurés (iPad 10ᵉ gén., iPadOS 27.0.1). Le fps s'affiche dans le
  **titre** de la fenêtre ; il baisse quand l'écran ne bouge pas (l'iPad n'envoie que les changements).
- **Orientation :** l'image suit **automatiquement** la rotation de l'iPad.
- **Touches :** `f` = plein écran, `q` ou `Échap` = quitter.
- Lancement manuel : `python app_ios27.py` (tunnel + image développeur requis, comme partout).

### Alternative — page web (avec contrôle tactile/clavier)
```
python -m pymobiledevice3 developer core-device display serve-web --bind 127.0.0.1
```
puis ouvrir **Edge ou Chrome** sur `http://127.0.0.1:8080/`. Permet de **contrôler** l'iPad
(tactile, clavier, boutons), mais l'écran est entouré d'un panneau d'options.
- ⚠️ **Page noire ?** **Firefox ne décode pas le HEVC** : utiliser Edge ou Chrome. Si c'est
  encore noir, installer **« HEVC Video Extensions »** depuis le Microsoft Store.

---

## 5. Dépannage (problèmes rencontrés et solutions)

### Cause n°1 — `usbmux list` est vide, mais l'iPad apparaît dans l'explorateur Windows
**Symptôme :** dans l'Explorateur de fichiers, l'iPad est visible (dossier de photos), mais
`python -m pymobiledevice3 usbmux list` ne montre **rien** ; `lockdown info` répond
**« device is not connected »**.

**Explication :** l'explorateur utilise un pilote **générique** (photos, PTP/MTP) qui ne demande
aucun logiciel Apple. `pymobiledevice3` a besoin d'un **autre canal** (service *usbmux* + pilote
**Apple Mobile Device**), **non installé par défaut**. Voir l'iPad dans l'explorateur **ne suffit pas**.

**Solution :**
1. Installer **l'app « Appareils Apple »** (Microsoft Store) **ou iTunes** (site Apple) — voir §2.b.
2. Vérifier dans `services.msc` que **« Apple Mobile Device Service »** est **En cours d'exécution**
   (sinon : clic droit → Démarrer).
3. Débrancher / rebrancher l'iPad, accepter **« Faire confiance »**, puis refaire `usbmux list`.

---

### Cause n°2 — « Mode développeur » est absent des Réglages
**Symptôme :** dans **Réglages → Confidentialité et sécurité**, on voit « Mode de confinement »
mais **pas** « Mode développeur ».

**Explication :** c'est **normal** au départ. L'entrée n'apparaît **qu'après** qu'un outil dev
ait communiqué avec l'iPad.

**Solution :** lancer la commande de l'**Étape 2** ci-dessus
(`python -m pymobiledevice3 amfi enable-developer-mode`). C'est elle qui fait apparaître l'entrée.
Si elle est bloquée par le code de verrouillage → cause n°3.

---

### Cause n°3 — Activation bloquée par le code de verrouillage (et Touch ID)
**Symptôme :** la commande refuse d'activer le mode développeur **parce qu'un code de
verrouillage est défini**.

**Explication :** pour des raisons de sécurité, l'activation **automatique** est interdite quand
un code existe. Il faut **retirer temporairement le code** (ce qui désactive Touch ID), activer,
puis tout remettre.

**Solution :**
1. **Retirer le code :** Réglages → **Touch ID et code** → (saisir le code) → **« Désactiver le code »**.
   - Si iOS l'exige d'abord : décocher **« Déverrouillage de l'iPad »** sous **Touch ID**, puis désactiver le code.
2. **Activer le mode développeur :**
   ```
   python -m pymobiledevice3 amfi enable-developer-mode
   ```
   → l'iPad redémarre → **« Activer le mode développeur ? »** → **Activer**.
3. **Tout remettre :** Réglages → **Touch ID et code** → **« Activer le code »** (redéfinir le code),
   puis réactiver **Touch ID**.
   → Le mode développeur **reste activé** même après avoir remis le code.

> ⚠️ Pendant le court moment sans code, les données de l'iPad sont moins protégées. Le faire
> rapidement et remettre le code juste après.

---

### Cause n°4 — `No such service: com.apple.coredevice.displayservice` (ou DVT introuvable)
**Symptôme :** le lancement échoue avec un message « No such service » / l'iPad n'expose pas
le service attendu, alors que le tunnel tourne.

**Explication :** les services développeur (DVT screenshot **et** mirroring vidéo) ne sont
disponibles **qu'une fois l'image développeur (DDI) montée** sur l'iPad. La DDI se **démonte
à chaque redémarrage** de l'iPad.

**Solution :**
```
python -m pymobiledevice3 mounter auto-mount
python -m pymobiledevice3 mounter list      REM doit afficher une image, pas []
```
Puis relancer. Si le service reste introuvable juste après le montage, **arrêter puis relancer
`tunneld`** (il doit re-scanner les services nouvellement disponibles). Les `.bat` font le
montage automatiquement.

---

### Cause n°5 — `Remote control requires iOS 27.0 or later` (mode vidéo HEVC)
**Symptôme :** `serve-web` / `lancer_ios27.bat` échoue avec `code 9021` et ce message.

**Explication :** le **flux vidéo HEVC** est verrouillé par Apple à **iPadOS 27+**. Sur une
version antérieure (ex. 26.5), c'est **impossible**, quel que soit l'outil.

**Solution :** mettre l'iPad à jour vers iPadOS 27 (sorti le 14 septembre 2026 ; l'iPad
10ᵉ génération est compatible). D'ici là, utiliser le **mode captures**
(`lancer_maintenant.bat` / `app.py`).

---

### Autres points
- **iOS 17+ : échec / message de tunnel** → lancer `python -m pymobiledevice3 remote tunneld`
  dans un terminal **administrateur** d'abord, **et** monter la DDI (cause n°4). Les `.bat`
  s'en chargent.
- **Image saccadée en mode captures** → c'est la limite de la méthode (~5–20 fps, capture PNG
  par image). Le FPS réel s'affiche en vert en haut à gauche de la fenêtre. Pour de la vraie
  fluidité, c'est le **mode vidéo HEVC** (iPadOS 27+) qu'il faut.
- **`pip` ou commande introuvable** → réinstaller Python en cochant « Add Python to PATH ».
- **iPad sous iOS < 16** → cette méthode ne s'applique pas (pas de mode développeur) ; me le signaler.

---

## 6. Comment ça marche (en bref)

**Mode captures (`app.py`)** : `pymobiledevice3` se connecte à l'iPad via le canal **usbmux**
d'Apple, ouvre le service développeur **DVT** (le même que celui des outils Xcode/Instruments),
et demande une **capture d'écran** en boucle. La capture tourne dans une **tâche de fond** et le
décodage PNG dans un **thread séparé**, pour que réception et affichage se **chevauchent**
(gain de fluidité). On n'affiche toujours que la **dernière image** disponible (temps réel).

**Mode vidéo HEVC (iPadOS 27+)** : l'iPad **encode son écran en H.265 (HEVC) en hardware** et
pousse un flux **RTP/UDP** via le tunnel. C'est le mécanisme utilisé par le mirroring de Xcode.
`app_ios27.py` lance en arrière-plan le serveur de mirroring de `pymobiledevice3` (`serve-web`,
sans navigateur), qui gère la session avec l'iPad (accusés de réception, images clés, reprise
après coupure) ; il lit ensuite son flux `/stream.bin`, le **décode avec PyAV** et affiche
toujours la **dernière image** reçue. L'orientation est lue auprès de SpringBoard ~2×/s.

Aucun pilote n'est modifié : à la fermeture, l'iPad est exactement dans son état normal et reste
synchronisable avec iTunes / l'app Appareils Apple. La seule modification réversible est le
**montage de l'image développeur** (DDI), qui disparaît au redémarrage de l'iPad.
