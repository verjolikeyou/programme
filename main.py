
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import base64
from pathlib import Path
from flask import Flask, render_template_string, request, redirect, url_for
from flask import send_from_directory



app = Flask(__name__)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.root_path, 'favicon.ico', mimetype='image/vnd.microsoft.icon')
    
@app.route("/google6de0069661b79218.html")
def verification_google():
    return "google-site-verification: google6de0069661b79218.html"

def dossier_application():
    """Dossier de l'application."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent

def charger_pdf_en_base64_images(nom_pdf, max_pages=5):
    """Convertit un PDF en images base64 si PyMuPDF (fitz) est disponible."""
    chemin = dossier_application() / nom_pdf
    images = []
    if not chemin.is_file():
        return images
    try:
        import fitz
        with fitz.open(str(chemin)) as doc:
            for i, page in enumerate(doc):
                if i >= max_pages:
                    break
                pix = page.get_pixmap(dpi=150)
                img_data = pix.tobytes("png")
                b64 = base64.b64encode(img_data).decode("utf-8")
                images.append(b64)
    except Exception as e:
        print(f"Erreur lors de la lecture du PDF {nom_pdf}: {e}")
    return images

# =============================================================================
# TEMPLATE DE BASE (DESIGN EXACT, BOUTONS 3D, FOND PASTEL & CAHIER SÉYÈS)
# =============================================================================
BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <link rel="shortcut icon" href="/favicon.ico" type="image/x-icon">
    <meta name="google-site-verification" content="uyEStLcFVZvMf9">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ titre_page|default("Programme en 11 eme") }}</title>
    <link href="https://fonts.googleapis.com/css2?family=Fredoka:wght@400;600;700;800&family=Comic+Neue:wght@400;700&display=swap" rel="stylesheet">
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        body {
            font-family: "Comic Sans MS", "Comic Neue", "Fredoka", Arial, sans-serif;
            background: linear-gradient(180deg, #E0F7FA 0%, #FFF9C4 60%, #FFE0B2 100%);
            min-height: 100vh;
            color: #2D3748;
            display: flex;
            justify-content: center;
            align-items: flex-start;
            padding: 15px;
        }
        .container {
            width: 100%;
            max-width: 760px;
            background: rgba(255, 255, 255, 0.96);
            border: 3px solid #80DEEA;
            border-radius: 24px;
            box-shadow: 0 12px 30px rgba(0, 0, 0, 0.12);
            padding: 22px;
            position: relative;
            overflow: hidden;
        }
        h1.titre-principal {
            color: #D90429;
            font-size: 24px;
            font-weight: 800;
            text-align: center;
            margin-bottom: 16px;
            line-height: 1.35;
        }
        .sous-titre-selection {
            display: block;
            font-size: 17px;
            color: #475569;
            font-weight: bold;
            margin-top: 4px;
        }
        .badge-date {
            display: inline-block;
            background: #4361EE;
            color: #ffffff;
            font-size: 14px;
            font-weight: bold;
            padding: 6px 18px;
            border-radius: 12px;
            margin-bottom: 12px;
            text-align: center;
        }
        .titre-lecon {
            color: #FF2E93;
            font-size: 19px;
            font-weight: 800;
            text-align: center;
            margin-bottom: 16px;
        }

        /* Cadre interne avec coins arrondis et bordure turquoise comme PySide6 */
        .cadre-menu {
            border: 3px solid #80DEEA;
            border-radius: 20px;
            padding: 16px;
            background: rgba(255, 255, 255, 0.5);
            margin-bottom: 10px;
        }
        
        /* Boutons 3D Bleus */
        .btn-bleu {
            display: block;
            width: 100%;
            background-color: #4CC9F0;
            color: #ffffff;
            font-family: inherit;
            font-size: 16px;
            font-weight: bold;
            text-align: center;
            text-decoration: none;
            border-radius: 14px;
            border: 3px solid #4361EE;
            border-bottom: 5px solid #3A0CA3;
            padding: 10px 14px;
            margin-bottom: 10px;
            cursor: pointer;
            transition: all 0.12s ease-in-out;
            user-select: none;
        }
        .btn-bleu:hover {
            background-color: #38B6FF;
            border-color: #3A0CA3;
        }
        .btn-bleu.selected, .btn-bleu:checked {
            background-color: #7209B7 !important;
            border-color: #560FA0 !important;
            border-bottom: 5px solid #3A0CA3 !important;
            color: #ffffff !important;
        }
        .btn-bleu:active {
            border-bottom-width: 2px;
            transform: translateY(3px);
        }

        /* Boutons 3D Rouges / Corail (Programme) */
        .btn-corail {
            display: block;
            width: 100%;
            background-color: #FF6B6B;
            color: #ffffff;
            font-family: inherit;
            font-size: 17px;
            font-weight: bold;
            text-align: center;
            text-decoration: none;
            border-radius: 14px;
            border: 3px solid #E63946;
            border-bottom: 5px solid #B71C1C;
            padding: 12px 14px;
            margin-bottom: 12px;
            cursor: pointer;
            transition: all 0.12s ease-in-out;
        }
        .btn-corail:hover {
            background-color: #FA5252;
            border-color: #B71C1C;
        }
        .btn-corail:active {
            border-bottom-width: 2px;
            transform: translateY(3px);
        }

        /* Boutons 3D Roses */
        .btn-rose {
            display: block;
            width: 100%;
            background-color: #F0F2F5;
            color: #FF2E93;
            font-family: inherit;
            font-size: 15px;
            font-weight: 800;
            text-align: center;
            text-decoration: none;
            border: 3px solid #FF2E93;
            border-bottom: 5px solid #C40058;
            border-radius: 14px;
            padding: 10px 12px;
            margin-bottom: 10px;
            cursor: pointer;
            transition: all 0.12s ease-in-out;
            user-select: none;
        }
        .btn-rose:hover {
            background-color: #E5E9F0;
            color: #FF0040;
            border-color: #FF0040;
            border-bottom-color: #B3002D;
        }
        .btn-rose.selected {
            background-color: #FF2E93 !important;
            color: #ffffff !important;
            border-color: #C40058 !important;
            border-bottom: 5px solid #85003A !important;
        }
        .btn-rose:active {
            border-bottom-width: 2px;
            transform: translateY(3px);
        }

        /* Bouton 3D Jaune-Vert "Choose" façon QCommandLinkButton */
        .btn-choose {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            width: 100%;
            background-color: #FFF3BF;
            border: 3px solid #FFD43B;
            border-bottom: 6px solid #FAB005;
            border-radius: 16px;
            padding: 10px 16px;
            color: #2B8A3E;
            font-family: "Fredoka", "Arial Rounded MT Bold", "Comic Sans MS", sans-serif;
            font-size: 19px;
            font-weight: bold;
            text-decoration: none;
            cursor: pointer;
            transition: all 0.15s ease-in-out;
            margin-top: 6px;
            margin-bottom: 8px;
        }
        .btn-choose:hover {
            background-color: #FFE066;
            border-color: #FCC419;
            border-bottom: 6px solid #F59F00;
        }
        .btn-choose:active {
            background-color: #FFD43B;
            border-bottom-width: 2px;
            transform: translateY(4px);
        }

        /* Bouton Retour Gris */
        .btn-retour {
            display: block;
            width: 100%;
            background-color: #6C757D;
            color: #ffffff;
            font-size: 15px;
            font-weight: bold;
            text-decoration: none;
            border-radius: 12px;
            border: none;
            padding: 9px 18px;
            margin-top: 8px;
            text-align: center;
            cursor: pointer;
            transition: background 0.2s;
        }
        .btn-retour:hover {
            background-color: #5A6268;
        }

        .cadre-contenu {
            background: linear-gradient(135deg, #FFF6F6 0%, #F0F4FF 100%);
            border: 2px solid #80DEEA;
            border-radius: 18px;
            padding: 16px;
            margin-bottom: 16px;
            line-height: 1.8;
            font-size: 15px;
        }

        /* Rendu Feuille de Cahier d'écolier Séyès */
        .cahier-seyes {
            background-color: #FFFFFF;
            background-image: 
                linear-gradient(to right, transparent 65px, #EF4444 65px, #EF4444 67px, transparent 67px),
                linear-gradient(#E2E8F0 1px, transparent 1px),
                linear-gradient(90deg, #E2E8F0 1px, transparent 1px);
            background-size: 100% 100%, 22px 22px, 22px 22px;
            border: 3px solid #80DEEA;
            border-radius: 16px;
            padding: 20px 20px 20px 80px;
            margin-bottom: 16px;
            overflow-x: auto;
        }
        .cahier-ligne-texte {
            color: #1E3A8A;
            font-weight: bold;
            font-size: 16px;
            margin-bottom: 12px;
        }

        /* Rubans décoratifs latéraux pour la section dessin */
        .dessin-wrapper {
            display: flex;
            align-items: stretch;
            gap: 10px;
        }
        .ruban-cote {
            width: 45px;
            background: #FFF0F5;
            border-radius: 12px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: space-around;
            font-size: 18px;
            padding: 10px 0;
            user-select: none;
        }
        .dessin-contenu {
            flex: 1;
            background: #ffffff;
            border: 3px solid #F97316;
            border-radius: 16px;
            padding: 16px;
        }
        table.table-calc {
            width: 100%;
            border-collapse: separate;
            border-spacing: 10px;
            font-family: 'Courier New', Courier, monospace;
            font-size: 16px;
            font-weight: bold;
        }
        table.table-calc td {
            background: #ffffff;
            border: 2px solid #80DEEA;
            border-radius: 12px;
            padding: 12px;
            text-align: center;
            vertical-align: top;
        }

        /* Animation de chargement circulaire (Loading 2ème interface) */
        .loader-ring {
            display: inline-block;
            position: relative;
            width: 100px;
            height: 100px;
            margin: 16px auto;
        }
        .loader-ring div {
            box-sizing: border-box;
            display: block;
            position: absolute;
            width: 80px;
            height: 80px;
            margin: 10px;
            border: 8px solid #4361EE;
            border-radius: 50%;
            animation: ring 1.2s cubic-bezier(0.5, 0, 0.5, 1) infinite;
            border-color: #4361EE transparent transparent transparent;
        }
        .loader-ring div:nth-child(1) { animation-delay: -0.45s; }
        .loader-ring div:nth-child(2) { animation-delay: -0.3s; }
        .loader-ring div:nth-child(3) { animation-delay: -0.15s; }
        @keyframes ring {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        /* Zone de défilement pour Boscher */
        .scroll-vertical {
            max-height: 440px;
            overflow-y: auto;
            padding-right: 6px;
            margin-bottom: 12px;
        }
        .scroll-vertical::-webkit-scrollbar {
            width: 8px;
        }
        .scroll-vertical::-webkit-scrollbar-thumb {
            background-color: #80DEEA;
            border-radius: 8px;
        }
    </style>
</head>
<body>
    <div class="container">
        {{ contenu|safe }}
    </div>
</body>
</html>
"""

def afficher(corps_html):
    return render_template_string(BASE_TEMPLATE, contenu=corps_html)

# =============================================================================
# 1ÈRE INTERFACE : ACCUEIL ET SÉLECTION DE MATIÈRE
# =============================================================================
@app.route("/")
def page_choix():
    html = """
        <div class="cadre-menu">
            <h1 class="titre-principal" id="titre-principal-choix">
                Programme en 11 eme
                <span class="sous-titre-selection" id="sous-titre-choix">Choisissez une matière</span>
            </h1>

            <button type="button" class="btn-bleu btn-option-choix" data-nom="Francais">Français</button>
            <button type="button" class="btn-bleu btn-option-choix" data-nom="Mathematiques">Mathématiques</button>
            <button type="button" class="btn-bleu btn-option-choix" data-nom="Cours">Cours</button>
            <button type="button" class="btn-bleu btn-option-choix" data-nom="Dessin">Dessin</button>
            <button type="button" class="btn-bleu btn-option-choix" data-nom="Anglais">Anglais</button>
            <button type="button" class="btn-bleu btn-option-choix" data-nom="Methode boscher">Méthode boscher</button>
            <button type="button" class="btn-bleu btn-option-choix" data-nom="Lecons de chose">Leçons de chose</button>

            <button type="button" id="btn-valider-matiere" class="btn-choose">
                <span>➜ Choose</span>
            </button>
        </div>

        <script>
            let matiereChoisie = "Francais";
            const boutons = document.querySelectorAll('.btn-option-choix');
            const titrePrincipal = document.getElementById('titre-principal-choix');
            const sousTitre = document.getElementById('sous-titre-choix');
            const btnValider = document.getElementById('btn-valider-matiere');

            // Sélection par défaut
            boutons[0].classList.add('selected');
            sousTitre.textContent = boutons[0].textContent;

            boutons.forEach(btn => {
                btn.addEventListener('click', () => {
                    boutons.forEach(b => b.classList.remove('selected'));
                    btn.classList.add('selected');
                    matiereChoisie = btn.getAttribute('data-nom');
                    sousTitre.textContent = btn.textContent;
                });
            });

            btnValider.addEventListener('click', () => {
                window.location.href = "/chargement?matiere=" + encodeURIComponent(matiereChoisie);
            });
        </script>
    """
    return afficher(html)

# =============================================================================
# 2ÈME INTERFACE : PAGE DE CHARGEMENT ANIMÉE (AVEC TIMER 1.5s COMME DANS LE SCRIPT PYSIDE6)
# =============================================================================
@app.route("/chargement")
def page_chargement():
    matiere = request.args.get("matiere", "Francais")
    
    # Destination selon la matière (exactement selon le dispatch Qt)
    if matiere == "Dessin":
        destination = "/dessin"
    elif matiere == "Cours":
        destination = "/cours"
    elif matiere == "Methode boscher":
        destination = "/methode-boscher"
    elif matiere == "Lecons de chose":
        destination = "/lecons-de-chose"
    elif matiere == "Anglais":
        destination = "/anglais"
    else:
        destination = f"/programme?matiere={matiere}"

    html = f"""
        <div style="text-align:center; padding: 20px 10px;">
            <h1 class="titre-principal">Programme en 11 eme</h1>
            <div style="font-size:24px; font-weight:bold; color:#2B8A3E; margin:12px 0;">
                {matiere}
            </div>

            <div class="loader-ring">
                <div></div><div></div><div></div><div></div>
            </div>

            <div style="font-size:19px; font-weight:bold; color:#3A0CA3; margin-top:14px;">
                Chargement en cours...
            </div>
        </div>

        <script>
            // Reproduction du QTimer.singleShot(1500, self.ouvrir_interface_suivante)
            setTimeout(() => {{
                window.location.href = "{destination}";
            }}, 1500);
        </script>
    """
    return afficher(html)

# =============================================================================
# 3ÈME INTERFACE : PAGE PROGRAMME (LEÇONS OU EXERCICES POUR FRANÇAIS & MATHÉMATIQUES)
# =============================================================================
@app.route("/programme")
def page_programme():
    matiere = request.args.get("matiere", "Francais")
    matiere_affiche = "Français" if matiere == "Francais" else "Mathématiques"
    prefixe = "/francais" if matiere == "Francais" else "/mathematiques"

    html = f"""
        <div class="cadre-menu" style="text-align:center;">
            <h1 class="titre-principal">
                {matiere_affiche}<br>
                <span class="sous-titre-selection">Leçons ou Exercices</span>
            </h1>

            <div style="background:rgba(255,255,255,0.7); border-radius:14px; padding:12px; margin-bottom:18px; color:#222; font-size:18px; font-weight:bold; border:2px dashed #80DEEA;">
                Matière choisie : <span style="color:#0D47A1;">{matiere_affiche}</span><br>
                <span style="font-size:15px; color:#555;">Sélectionnez Leçons ou Exercices.</span>
            </div>

            <a href="{prefixe}/lecons" class="btn-corail">Leçons</a>
            <a href="{prefixe}/exercices" class="btn-corail">Exercices</a>

            <a href="/" class="btn-choose">
                <span>← Retour au choix</span>
            </a>
        </div>
    """
    return afficher(html)

@app.route("/anglais")
def page_anglais():
    html = """
        <h1 class="titre-principal">Anglais — 11ème</h1>
        <div class="cadre-contenu" style="text-align:center;">
            <p style="font-size:18px; font-weight:bold; color:#0D47A1;">🇬🇧 Welcome to English Class!</p>
            <p style="margin-top:10px;">Les notions et activités d'anglais seront chargées selon les séquences prévues.</p>
        </div>
        <div style="text-align:center;">
            <a href="/" class="btn-retour">← Revenir au choix</a>
        </div>
    """
    return afficher(html)

# =============================================================================
# 4ÈME INTERFACE & SOUS-MENUS : DESSIN (CAROTTE & CARTABLE)
# =============================================================================
@app.route("/dessin")
def page_dessin():
    html = """
        <div class="cadre-menu">
            <h1 class="titre-principal" id="titre-dessin">
                Dessin<br>
                <span class="sous-titre-selection" id="sous-titre-dessin">Choisissez un dessin à réaliser</span>
            </h1>

            <button type="button" class="btn-rose btn-option" data-url="/dessin/carotte" data-titre="1- Carotte">1- Carotte</button>
            <button type="button" class="btn-rose btn-option" data-url="/dessin/cartable" data-titre="2- Cartable">2- Cartable</button>

            <button type="button" id="btn-valider" class="btn-choose">➜ Choose</button>
            <a href="/" class="btn-retour">← Revenir au choix</a>
        </div>

        <script>
            let urlChoisie = "/dessin/carotte";
            const boutons = document.querySelectorAll('.btn-option');
            const sousTitre = document.getElementById('sous-titre-dessin');
            const btnValider = document.getElementById('btn-valider');

            boutons[0].classList.add('selected');
            sousTitre.textContent = boutons[0].getAttribute('data-titre');

            boutons.forEach(b => {
                b.addEventListener('click', () => {
                    boutons.forEach(x => x.classList.remove('selected'));
                    b.classList.add('selected');
                    urlChoisie = b.getAttribute('data-url');
                    sousTitre.textContent = b.getAttribute('data-titre');
                });
            });

            btnValider.addEventListener('click', () => {
                window.location.href = urlChoisie;
            });
        </script>
    """
    return afficher(html)

@app.route("/dessin/carotte")
def page_dessin_carotte():
    pdf_imgs = charger_pdf_en_base64_images("carot.pdf")
    html = f"""
        <div style="text-align:center; margin-bottom:12px;">
            <span class="badge-date" style="background:#EA580C;">🥕 Atelier Dessin : Comment dessiner une Carotte</span>
        </div>
        
        <div class="dessin-wrapper">
            <div class="ruban-cote"><span>✏️</span><span>⭐</span><span>🎨</span><span>🥕</span><span>✨</span></div>
            <div class="dessin-contenu">
                {''.join([f'<div style="text-align:center; margin-bottom:15px; border:2px dashed #FB923C; border-radius:12px; padding:8px;"><img src="data:image/png;base64,{img}" style="max-width:100%; border-radius:8px;"></div>' for img in pdf_imgs]) if pdf_imgs else '<p style="background:#FFF7ED; border:2px dashed #F97316; border-radius:10px; padding:10px; font-size:13px; color:#9A3412;">Document carot.pdf non détecté à côté du script (Les étapes illustrées ci-dessous restent actives).</p>'}
                
                <div style="background:#FFFAF0; border:2px solid #FDBA74; border-radius:12px; padding:14px; margin-top:12px;">
                    <p style="font-size:18px; font-weight:900; color:#EA580C; text-align:center; margin-bottom:10px;">✨ Les Étapes pour réussir la Carotte ✨</p>
                    <div style="background:#FFFFFF; border:2px solid #FED7AA; border-radius:10px; padding:10px; margin-bottom:10px;">
                        <b style="color:#C2410C;">• Étape 1 :</b> Tracer la forme conique allongée (ovale pointu vers le bas) qui forme le corps de la carotte.
                    </div>
                    <div style="background:#FFFFFF; border:2px solid #FED7AA; border-radius:10px; padding:10px; margin-bottom:10px;">
                        <b style="color:#C2410C;">• Étape 2 :</b> Ajouter de petits traits horizontaux légèrement incurvés le long du corps pour donner du relief.
                    </div>
                    <div style="background:#FFFFFF; border:2px solid #FED7AA; border-radius:10px; padding:10px; margin-bottom:10px;">
                        <b style="color:#15803D;">• Étape 3 :</b> Dessiner les fanes (les feuilles au sommet) avec 3 ou 4 bosses arrondies.
                    </div>
                    <div style="background:#ECFDF5; border:2px dashed #10B981; border-radius:10px; padding:10px;">
                        <b style="color:#047857;">• Finition :</b> Colorier le corps en bel orange et le feuillage en vert tendre ou foncé !
                    </div>
                </div>
            </div>
            <div class="ruban-cote"><span>🌸</span><span>🖍️</span><span>🥕</span><span>📐</span><span>⭐</span></div>
        </div>

        <div style="text-align:center;">
            <a href="/dessin" class="btn-retour">← Revenir au choix du Dessin</a>
        </div>
    """
    return afficher(html)

@app.route("/dessin/cartable")
def page_dessin_cartable():
    pdf_imgs = charger_pdf_en_base64_images("school bag.pdf")
    html = f"""
        <div style="text-align:center; margin-bottom:12px;">
            <span class="badge-date" style="background:#FF2E93;">🎒 Atelier Dessin : Comment dessiner un Cartable Mignon</span>
        </div>
        
        <div class="dessin-wrapper">
            <div class="ruban-cote"><span>🎒</span><span>⭐</span><span>🎨</span><span>🖍️</span><span>✨</span></div>
            <div class="dessin-contenu" style="border-color:#FF2E93;">
                {''.join([f'<div style="text-align:center; margin-bottom:15px; border:2px dashed #F472B6; border-radius:12px; padding:8px;"><img src="data:image/png;base64,{img}" style="max-width:100%; border-radius:8px;"></div>' for img in pdf_imgs]) if pdf_imgs else '<p style="background:#FDF2F8; border:2px dashed #F472B6; border-radius:10px; padding:10px; font-size:13px; color:#9D174D;">Document school bag.pdf non détecté à côté du script (Le tutoriel complet étape par étape ci-dessous reste actif).</p>'}

                <div style="background:#FFF5F7; border:2px solid #F472B6; border-radius:14px; padding:14px;">
                    <p style="font-size:18px; font-weight:900; color:#DB2777; text-align:center; margin-bottom:4px;">
                        🎒 How to Draw a Cute School Backpack — 6 Easy Steps!
                    </p>
                    <p style="text-align:center; font-size:13px; color:#6B7280; font-weight:bold; margin-bottom:12px;">
                        Suivez ces 6 étapes pas à pas avec votre crayon et amusez-vous !
                    </p>
                    <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
                        <div style="background:#FFFFFF; border:2px solid #80DEEA; border-radius:10px; padding:10px;">
                            <b style="color:#0284C7;">Step 1 • Draw the Main Body</b><br>
                            Tracer un grand rectangle aux coins bien arrondis pour former le corps du cartable.
                        </div>
                        <div style="background:#FFFFFF; border:2px solid #80DEEA; border-radius:10px; padding:10px;">
                            <b style="color:#0284C7;">Step 2 • Add the Flap</b><br>
                            Ajouter le rabat supérieur avec une ligne courbée en haut du sac (curved flap on top).
                        </div>
                        <div style="background:#FFFFFF; border:2px solid #80DEEA; border-radius:10px; padding:10px;">
                            <b style="color:#0284C7;">Step 3 • Draw the Side Pockets</b><br>
                            Dessiner les deux petites poches latérales de chaque côté pour ranger les gourdes.
                        </div>
                        <div style="background:#FFFFFF; border:2px solid #80DEEA; border-radius:10px; padding:10px;">
                            <b style="color:#0284C7;">Step 4 • Add the Straps</b><br>
                            Tracer les deux jolies bretelles pour les épaules (two straps for your shoulders).
                        </div>
                        <div style="background:#FFFFFF; border:2px solid #80DEEA; border-radius:10px; padding:10px;">
                            <b style="color:#0284C7;">Step 5 • Draw Details</b><br>
                            Dessiner la fermeture éclair, la poche avant, et les détails mignons (étoiles ⭐, coeur 💖).
                        </div>
                        <div style="background:#FFFFFF; border:2px solid #80DEEA; border-radius:10px; padding:10px;">
                            <b style="color:#D81B60;">Step 6 • Add a Cute Face!</b><br>
                            Ajouter les yeux kawaii brillants, de jolis cils, des pommettes roses et un grand sourire !
                        </div>
                    </div>
                    <div style="background:#F0FDF4; border:2px dashed #16A34A; border-radius:10px; padding:10px; margin-top:12px; text-align:center;">
                        <b style="color:#15803D;">🎉 À votre tour : Now it's your turn!</b><br>
                        <span style="color:#166534; font-size:13px;">Vous pouvez colorier en rose, ajouter des étoiles vertes, des autocollants et des motifs originaux !</span>
                    </div>
                </div>
            </div>
            <div class="ruban-cote"><span>🌸</span><span>✂️</span><span>🎒</span><span>🌟</span><span>⭐</span></div>
        </div>

        <div style="text-align:center;">
            <a href="/dessin" class="btn-retour">← Revenir au choix du Dessin</a>
        </div>
    """
    return afficher(html)

# =============================================================================
# SECTION COURS
# =============================================================================
@app.route("/cours")
def page_cours():
    html = """
        <div class="cadre-menu">
            <h1 class="titre-principal" id="titre-cours">
                Cours<br>
                <span class="sous-titre-selection" id="sous-titre-cours">Choisissez une leçon</span>
            </h1>

            <button type="button" class="btn-rose btn-option" data-url="/cours/pose-et-effectue" data-titre="1-Pose et effectue">1-Pose et effectue</button>
            <button type="button" class="btn-rose btn-option" data-url="/cours/decompose" data-titre="1-Décompose">1-Décompose</button>

            <button type="button" id="btn-valider" class="btn-choose">➜ Choose</button>
            <a href="/" class="btn-retour">← Revenir au choix</a>
        </div>

        <script>
            let urlChoisie = "/cours/pose-et-effectue";
            const boutons = document.querySelectorAll('.btn-option');
            const sousTitre = document.getElementById('sous-titre-cours');
            const btnValider = document.getElementById('btn-valider');

            boutons[0].classList.add('selected');
            sousTitre.textContent = boutons[0].getAttribute('data-titre');

            boutons.forEach(b => {
                b.addEventListener('click', () => {
                    boutons.forEach(x => x.classList.remove('selected'));
                    b.classList.add('selected');
                    urlChoisie = b.getAttribute('data-url');
                    sousTitre.textContent = b.getAttribute('data-titre');
                });
            });

            btnValider.addEventListener('click', () => {
                window.location.href = urlChoisie;
            });
        </script>
    """
    return afficher(html)

@app.route("/cours/pose-et-effectue")
def page_cours_pose_effectue():
    html = """
        <div style="text-align:center;">
            <span class="badge-date">📅 Mercredi 07 Octobre 2026</span>
            <div class="titre-lecon">📖 Arithmétique : 1- Pose et effectue</div>
        </div>

        <table class="table-calc">
            <tr>
                <td>
                    <span style="color:#0D47A1;">15 + 13 = 28</span><br><br>
                    &nbsp;&nbsp;1 5<br>
                    + 1 3<br>
                    -------<br>
                    &nbsp;&nbsp;2 8
                </td>
                <td>
                    <span style="color:#0D47A1;">36 + 32 = 68</span><br><br>
                    &nbsp;&nbsp;3 6<br>
                    + 3 2<br>
                    -------<br>
                    &nbsp;&nbsp;6 8
                </td>
                <td>
                    <span style="color:#0D47A1;">40 + 55 = 95</span><br><br>
                    &nbsp;&nbsp;4 0<br>
                    + 5 5<br>
                    -------<br>
                    &nbsp;&nbsp;9 5
                </td>
            </tr>
        </table>

        <div style="font-size:16px; font-weight:800; color:#2E7D32; margin-top:15px; margin-bottom:8px;">
            ✍️ 3- Écris en lettres :
        </div>
        <div style="background:#FFFFFF; border:2px dashed #4CAF50; border-radius:12px; padding:12px; font-size:14px; font-weight:bold; color:#1B5E20; line-height:2;">
            ✦ <b>2</b> = deux &nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;&nbsp; ✦ <b>5</b> = cinq &nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;&nbsp; ✦ <b>10</b> = dix<br>
            ✦ <b>0</b> = zéro &nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;&nbsp; ✦ <b>7</b> = sept
        </div>

        <div style="text-align:center;">
            <a href="/cours" class="btn-retour">← Revenir aux Cours</a>
        </div>
    """
    return afficher(html)

@app.route("/cours/decompose")
def page_cours_decompose():
    html = """
        <div style="text-align:center;">
            <span class="badge-date">📅 Mercredi 14 Octobre 2026</span>
            <div class="titre-lecon">📖 Arithmétique : 1- Décompose & Compose</div>
        </div>

        <p style="font-size:15px; font-weight:bold; color:#0D47A1; margin-top:10px; margin-bottom:6px;">1) Décompose :</p>
        <div style="background:#FFFFFF; border:2px solid #80DEEA; border-radius:12px; padding:12px; font-size:14px; font-weight:bold; color:#333333; line-height:2.2;">
            ✦ 24 = <b style="color:#D81B60;">2 d 4 u</b><br>
            ✦ 15 = <b style="color:#D81B60;">1 d 5 u</b><br>
            ✦ 3 &nbsp;= <b style="color:#D81B60;">3 u</b><br>
            ✦ 56 = <b style="color:#D81B60;">5 d 6 u</b><br>
            ✦ 78 = <b style="color:#D81B60;">7 d 8 u</b><br>
            ✦ 49 = <b style="color:#D81B60;">4 d 9 u</b>
        </div>

        <table class="table-calc" style="margin-top:12px;">
            <tr>
                <td>
                    <span style="color:#C2185B;">46 + 36 = 82</span><br><br>
                    &nbsp;&nbsp;4 6<br>
                    + 3 6<br>
                    -------<br>
                    &nbsp;&nbsp;8 2
                </td>
                <td>
                    <span style="color:#C2185B;">17 + 4 = 21</span><br><br>
                    &nbsp;&nbsp;1 7<br>
                    + &nbsp;&nbsp;4<br>
                    -------<br>
                    &nbsp;&nbsp;2 1
                </td>
                <td>
                    <span style="color:#C2185B;">22 + 19 = 41</span><br><br>
                    &nbsp;&nbsp;2 2<br>
                    + 1 9<br>
                    -------<br>
                    &nbsp;&nbsp;4 1
                </td>
            </tr>
        </table>

        <p style="font-size:15px; font-weight:bold; color:#1B5E20; margin-top:14px; margin-bottom:6px;">2) Compose :</p>
        <div style="background:#E8F5E9; border:2px dashed #4CAF50; border-radius:12px; padding:12px; font-size:14px; font-weight:bold; color:#1B5E20; line-height:2.2;">
            ✦ 3 d 5 u = <b style="color:#0D47A1;">35</b><br>
            ✦ 5 u &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;= <b style="color:#0D47A1;">5</b><br>
            ✦ 2 d 8 u = <b style="color:#0D47A1;">28</b><br>
            ✦ 9 u &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;= <b style="color:#0D47A1;">9</b><br>
            ✦ 7 d 2 u = <b style="color:#0D47A1;">72</b>
        </div>

        <p style="font-size:14px; font-weight:bold; color:#E65100; margin-top:14px; margin-bottom:6px;">✍️ Écriture :</p>
        <div style="background:#FFF9C4; border-radius:12px; padding:12px; font-size:14px; font-style:italic; color:#4E342E; line-height:2;">
            • Maman va au marché.<br>
            • Marius plante une fleur.
        </div>

        <div style="text-align:center;">
            <a href="/cours" class="btn-retour">← Revenir aux Cours</a>
        </div>
    """
    return afficher(html)

# =============================================================================
# SECTION MÉTHODE BOSCHER (TOUTES LES 30 LEÇONS COMPLÈTES)
# =============================================================================
BOSCHER_LECONS = [
    ("i - u", "iu"), ("o - a", "oa"), ("e", "e"), ("p", "p"), ("t", "t"),
    ("r", "r"), ("n", "n"), ("m", "m"), ("l", "l"), ("c", "c"),
    ("d", "d"), ("v", "v"), ("s", "s"), ("b", "b"), ("f", "f"),
    ("j", "j"), ("g", "g"), ("ch", "ch"), ("ou", "ou"), ("on", "on"),
    ("oi", "oi"), ("an", "an"), ("in", "in"), ("br", "br"), ("fr", "fr"),
    ("bl", "bl"), ("cl", "cl"), ("ar", "ar"), ("al", "al")
]

@app.route("/methode-boscher")
def page_methode_boscher():
    boutons_html = "".join([
        f'<button type="button" class="btn-rose btn-option" data-url="/methode-boscher/{code}" data-titre="{label}">{label}</button>'
        for label, code in BOSCHER_LECONS
    ])
    html = f"""
        <div class="cadre-menu">
            <h1 class="titre-principal" id="titre-boscher">
                Méthode Boscher<br>
                <span class="sous-titre-selection" id="sous-titre-boscher">Choisissez une leçon</span>
            </h1>

            <div class="scroll-vertical">
                {boutons_html}
            </div>

            <button type="button" id="btn-valider" class="btn-choose">➜ Choose</button>
            <a href="/" class="btn-retour">← Revenir au choix</a>
        </div>

        <script>
            let urlChoisie = "/methode-boscher/iu";
            const boutons = document.querySelectorAll('.btn-option');
            const sousTitre = document.getElementById('sous-titre-boscher');
            const btnValider = document.getElementById('btn-valider');

            boutons[0].classList.add('selected');
            sousTitre.textContent = boutons[0].getAttribute('data-titre');

            boutons.forEach(b => {{
                b.addEventListener('click', () => {{
                    boutons.forEach(x => x.classList.remove('selected'));
                    b.classList.add('selected');
                    urlChoisie = b.getAttribute('data-url');
                    sousTitre.textContent = b.getAttribute('data-titre');
                }});
            }});

            btnValider.addEventListener('click', () => {{
                window.location.href = urlChoisie;
            }});
        </script>
    """
    return afficher(html)

# Dictionnaire de contenu intégral de toutes les leçons Boscher de PySide6
BOSCHER_CONTENUS = {
    "iu": """
        <p><span class="badge-date" style="background:#0284C7;">Méthode Boscher</span></p>
        <p style="font-size:22px; font-weight:900; color:#D90429; margin-top:8px;">La rue à midi.</p>
        <p style="font-size:32px; font-weight:900; color:#E11D48; letter-spacing:8px; text-align:center;">i &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; u</p>
        <div class="cadre-contenu" style="font-size:18px; font-weight:bold; color:#0F172A; line-height:2.4; letter-spacing:3px; text-align:center;">
            i &nbsp;&nbsp;&nbsp; u &nbsp;&nbsp;&nbsp; i &nbsp;&nbsp;&nbsp; i &nbsp;&nbsp;&nbsp; u &nbsp;&nbsp;&nbsp; u &nbsp;&nbsp;&nbsp; i &nbsp;&nbsp;&nbsp; u<br>
            u &nbsp;&nbsp;&nbsp; i &nbsp;&nbsp;&nbsp; u &nbsp;&nbsp;&nbsp; u &nbsp;&nbsp;&nbsp; i &nbsp;&nbsp;&nbsp; i &nbsp;&nbsp;&nbsp; u &nbsp;&nbsp;&nbsp; i
        </div>
        <p style="font-size:16px; font-weight:bold; color:#2563EB; margin-top:14px;">✍️ Écriture et chiffres :</p>
        <div style="background:#F0F9FF; border:2px dashed #0284C7; border-radius:12px; padding:12px; font-size:15px; font-weight:bold; color:#0369A1; line-height:2.2; text-align:center;">
            1 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 2 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 1 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 2 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 1 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 2 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 1 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 2<br>
            ✦ 1 hibou &nbsp;&nbsp;|&nbsp;&nbsp; ✦ 2 hirondelles &nbsp;&nbsp;|&nbsp;&nbsp; ✦ la lune
        </div>
    """,
    "oa": """
        <p><span class="badge-date" style="background:#0284C7;">Méthode Boscher</span></p>
        <p style="font-size:22px; font-weight:900; color:#D90429; margin-top:8px;">La fête de noël.</p>
        <p style="font-size:32px; font-weight:900; color:#E11D48; letter-spacing:8px; text-align:center;">o &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; a</p>
        <div class="cadre-contenu" style="font-size:18px; font-weight:bold; color:#0F172A; line-height:2.4; letter-spacing:3px; text-align:center;">
            u &nbsp;&nbsp;&nbsp; 0 &nbsp;&nbsp;&nbsp; a &nbsp;&nbsp;&nbsp; i &nbsp;&nbsp;&nbsp; o &nbsp;&nbsp;&nbsp; u &nbsp;&nbsp;&nbsp; a &nbsp;&nbsp;&nbsp; 0<br>
            a &nbsp;&nbsp;&nbsp; u &nbsp;&nbsp;&nbsp; 0 &nbsp;&nbsp;&nbsp; a &nbsp;&nbsp;&nbsp; i &nbsp;&nbsp;&nbsp; a &nbsp;&nbsp;&nbsp; 0 &nbsp;&nbsp;&nbsp; i
        </div>
        <p style="font-size:16px; font-weight:bold; color:#16A34A; margin-top:14px;">🫒 Illustrations & Vocabulaire :</p>
        <div style="background:#F0FDF4; border:2px dashed #16A34A; border-radius:12px; padding:12px; font-size:15px; font-weight:bold; color:#15803D; line-height:2.2; text-align:center;">
            ✦ 2 olives &nbsp;&nbsp;|&nbsp;&nbsp; ✦ 1 avion &nbsp;&nbsp;|&nbsp;&nbsp; ✦ 1 âne &nbsp;&nbsp;|&nbsp;&nbsp; des abricots<br>
            1 + 1 = 2 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 2 - 1 = 1
        </div>
    """,
    "e": """
        <p><span class="badge-date" style="background:#0284C7;">Méthode Boscher</span></p>
        <p style="font-size:22px; font-weight:900; color:#D90429; margin-top:8px;">Le déjeuner de bébé.</p>
        <p style="font-size:28px; font-weight:900; color:#E11D48; letter-spacing:6px; text-align:center;">e &nbsp;&nbsp;&nbsp; é &nbsp;&nbsp;&nbsp; è &nbsp;&nbsp;&nbsp; ê</p>
        <div class="cadre-contenu" style="font-size:18px; font-weight:bold; color:#0F172A; line-height:2.4; letter-spacing:3px; text-align:center;">
            è &nbsp;&nbsp;&nbsp; e &nbsp;&nbsp;&nbsp; é &nbsp;&nbsp;&nbsp; ê &nbsp;&nbsp;&nbsp; é &nbsp;&nbsp;&nbsp; è &nbsp;&nbsp;&nbsp; e &nbsp;&nbsp;&nbsp; ê<br>
            é &nbsp;&nbsp;&nbsp; i &nbsp;&nbsp;&nbsp; ê &nbsp;&nbsp;&nbsp; a &nbsp;&nbsp;&nbsp; è &nbsp;&nbsp;&nbsp; 0 &nbsp;&nbsp;&nbsp; u &nbsp;&nbsp;&nbsp; e<br>
            a &nbsp;&nbsp;&nbsp; è &nbsp;&nbsp;&nbsp; 0 &nbsp;&nbsp;&nbsp; e &nbsp;&nbsp;&nbsp; u &nbsp;&nbsp;&nbsp; é &nbsp;&nbsp;&nbsp; i &nbsp;&nbsp;&nbsp; a
        </div>
        <p style="font-size:16px; font-weight:bold; color:#D97706; margin-top:14px;">🍒 Objets et Calculs :</p>
        <div style="background:#FFFBEB; border:2px dashed #D97706; border-radius:12px; padding:12px; font-size:14px; font-weight:bold; color:#B45309; line-height:2.2; text-align:center;">
            ✦ 1 échelle &nbsp;—&nbsp; 1 bêche &nbsp;—&nbsp; des pêches &nbsp;—&nbsp; des cerises<br>
            ✦ 1 + 1 + 1 = 3 &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; 3 - 1 = 2 &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; 3 - 2 = 1
        </div>
    """,
    "p": """
        <p><span class="badge-date" style="background:#0284C7;">Méthode Boscher</span></p>
        <p style="font-size:22px; font-weight:900; color:#D90429; margin-top:8px;">La poule appelle ses petits.</p>
        <p style="font-size:32px; font-weight:900; color:#E11D48; text-align:center;">p = p</p>
        <div class="cadre-contenu" style="font-size:17px; font-weight:bold; color:#0F172A; line-height:2.4; text-align:center;">
            pi . pu . po . pa . pe . pé . pè . pê .<br>
            po . pê . pu . pe . pi . pè . pa . pé .<br>
            <span style="color:#D81B60;">pa pa . pi pe . é pi . pi e .</span>
        </div>
        <p style="font-size:16px; font-weight:bold; color:#7C3AED; margin-top:14px;">🌾 Mots et Calculs :</p>
        <div style="background:#F5F3FF; border:2px dashed #7C3AED; border-radius:12px; padding:12px; font-size:14px; font-weight:bold; color:#5B21B6; line-height:2.2; text-align:center;">
            ✦ pipe &nbsp;—&nbsp; papa &nbsp;—&nbsp; épi &nbsp;—&nbsp; pie &nbsp;—&nbsp; poussins<br>
            ✦ 3 + 1 = 4 &nbsp;&nbsp;|&nbsp;&nbsp; 2 + 2 = 4 &nbsp;&nbsp;|&nbsp;&nbsp; 1 + 3 = 4 &nbsp;&nbsp;|&nbsp;&nbsp; 4 - 1 = 3
        </div>
    """,
    "t": """
        <p><span class="badge-date" style="background:#0284C7;">Méthode Boscher</span></p>
        <p style="font-size:22px; font-weight:900; color:#D90429; margin-top:8px;">Toto a été têtu.</p>
        <p style="font-size:32px; font-weight:900; color:#E11D48; text-align:center;">t = t</p>
        <div class="cadre-contenu" style="font-size:16px; font-weight:bold; color:#0F172A; line-height:2.4; text-align:center;">
            ta . té . ti . te . tu . tè . to . tê .<br>
            to to . tê tu . to mate . tu té . é tu i . tué .<br>
            pa la te . pé té . ta pe . pe ti te . pâ te . é ta pe .<br>
            <span style="color:#2563EB;">to to a é té tê tu . pa pa a ta pé to to .</span>
        </div>
        <p style="font-size:16px; font-weight:bold; color:#DC2626; margin-top:14px;">🔨 Mots :</p>
        <div style="background:#FEF2F2; border:2px dashed #DC2626; border-radius:12px; padding:12px; font-size:14px; font-weight:bold; color:#991B1B; line-height:2; text-align:center;">
            la tête . toto . têtu . tomate . étui .<br>
            papa tape à la petite pipe.
        </div>
    """,
    "r": """
        <p><span class="badge-date" style="background:#0284C7;">Méthode Boscher</span></p>
        <p style="font-size:22px; font-weight:900; color:#D90429; margin-top:8px;">Le chat ronronne devant le rôti.</p>
        <p style="font-size:32px; font-weight:900; color:#E11D48; text-align:center;">r = r</p>
        <div class="cadre-contenu" style="font-size:16px; font-weight:bold; color:#0F172A; line-height:2.4; text-align:center;">
            rê . ra . ré . ru . re . ri . rè . ro .<br>
            ra tiè re . ti re . ra re . ra ta . ra tu re . rue .<br>
            pé re . râ pe . pâ tu re . pa ri . pi re . rô ti .<br>
            <span style="color:#059669;">pa pa a ti ré , a ra té , re ti re ra .</span>
        </div>
        <p style="font-size:16px; font-weight:bold; color:#D97706; margin-top:14px;">🧀 Vocabulaire & Phrase :</p>
        <div style="background:#FFFBEB; border:2px dashed #D97706; border-radius:12px; padding:12px; font-size:14px; font-weight:bold; color:#B45309; line-height:2.2; text-align:center;">
            ✦ râpe &nbsp;—&nbsp; rôti &nbsp;—&nbsp; souris &nbsp;—&nbsp; rats &nbsp;—&nbsp; ratière<br>
            ✦ <i>père a réparé la petite ratière.</i><br>
            5 = 00000 &nbsp;|&nbsp; 5 = 000 + 00 &nbsp;|&nbsp; 4 + 1 = 5 &nbsp;|&nbsp; 3 + 2 = 5
        </div>
    """,
    "n": """
        <p><span class="badge-date" style="background:#0284C7;">Méthode Boscher</span></p>
        <p style="font-size:22px; font-weight:900; color:#D90429; margin-top:8px;">René cherche des nids.</p>
        <p style="font-size:32px; font-weight:900; color:#E11D48; text-align:center;">n = n</p>
        <div class="cadre-contenu" style="font-size:16px; font-weight:bold; color:#0F172A; line-height:2.4; text-align:center;">
            ni . né . na . nè . no . nê . nu . ne .<br>
            ni na . u ne . te nu . pu ni . â ne . u ne no te .<br>
            u ne é pi ne . u ne té ti ne . u ne na ri ne .<br>
            <span style="color:#2563EB;">re né a é té re te nu , pa pa a pu ni re né .</span>
        </div>
        <p style="font-size:16px; font-weight:bold; color:#16A34A; margin-top:14px;">🪺 Vocabulaire & Phrase :</p>
        <div style="background:#F0FDF4; border:2px dashed #16A34A; border-radius:12px; padding:12px; font-size:14px; font-weight:bold; color:#15803D; line-height:2.2; text-align:center;">
            ✦ un nid &nbsp;—&nbsp; une tétine &nbsp;—&nbsp; une niche &nbsp;—&nbsp; une noix<br>
            ✦ <i>nina . note . rené . tétine . une épine .</i><br>
            ✦ <i>irène ira nu-tête . rené a été puni .</i>
        </div>
    """,
    "m": """
        <p><span class="badge-date" style="background:#0284C7;">Méthode Boscher</span></p>
        <p style="font-size:22px; font-weight:900; color:#D90429; margin-top:8px;">Rémi et Maria partagent une pomme.</p>
        <p style="font-size:32px; font-weight:900; color:#E11D48; text-align:center;">m = m</p>
        <div class="cadre-contenu" style="font-size:16px; font-weight:bold; color:#0F172A; line-height:2.4; text-align:center;">
            mé . me . mu . mo . mê . mi . mè . ma .<br>
            mi mi . ma ria . ma mè re . une ma re . une mi ne .<br>
            a mi . nu mé ro . une to ma te . une mi nu te .<br>
            <span style="color:#C026D3;">ré mi a pa ti né , re né a i mi té ré mi .</span>
        </div>
        <p style="font-size:16px; font-weight:bold; color:#E11D48; margin-top:14px;">🍎 Lecture courante & Calculs :</p>
        <div style="background:#FFF1F2; border:2px dashed #E11D48; border-radius:12px; padding:12px; font-size:14px; font-weight:bold; color:#9F1239; line-height:2.2; text-align:center;">
            ✦ <i>ma mère a ramené petite maria.</i><br>
            ✦ une mare &nbsp;—&nbsp; une tomate &nbsp;—&nbsp; une minute &nbsp;—&nbsp; les pommes<br>
            6 - 1 = 5 &nbsp;&nbsp;|&nbsp;&nbsp; 6 - 2 = 4 &nbsp;&nbsp;|&nbsp;&nbsp; 6 - 3 = 3 &nbsp;&nbsp;|&nbsp;&nbsp; 6 - 4 = 2
        </div>
    """,
    "l": """
        <p><span class="badge-date" style="background:#0284C7;">Méthode Boscher</span></p>
        <p style="font-size:22px; font-weight:900; color:#D90429; margin-top:8px;">Émile soigne les lapins.</p>
        <p style="font-size:32px; font-weight:900; color:#E11D48; text-align:center;">l = l</p>
        <div class="cadre-contenu" style="font-size:16px; font-weight:bold; color:#0F172A; line-height:2.4; text-align:center;">
            lê . la . le . lé . li . lè . lo . lu .<br>
            é mi le . la lu ne . le lo to . la la me . la li me .<br>
            la pe lo te . la tu li pe . la pa ro le . la pi le .<br>
            <span style="color:#0284C7;">a li ne ô te ra le rô ti , la to ma te , le pâ té .</span>
        </div>
        <p style="font-size:16px; font-weight:bold; color:#2563EB; margin-top:14px;">✍️ Écriture et phrase :</p>
        <div style="background:#EFF6FF; border:2px dashed #2563EB; border-radius:12px; padding:12px; font-size:14px; font-weight:bold; color:#1E40AF; line-height:2.2; text-align:center;">
            ✦ <i>la lime . le loto . une pelote . la parole .</i><br>
            ✦ <i>amélie, retire ta pèlerine .</i>
        </div>
        <p style="font-size:16px; font-weight:bold; color:#16A34A; margin-top:14px;">🐰 Vocabulaire & Calculs :</p>
        <div style="background:#F0FDF4; border:2px dashed #16A34A; border-radius:12px; padding:12px; font-size:14px; font-weight:bold; color:#15803D; line-height:2.2; text-align:center;">
            ✦ lièvre &nbsp;—&nbsp; le loto &nbsp;—&nbsp; une pile &nbsp;—&nbsp; une lime &nbsp;—&nbsp; tulipes<br>
            ✦ 6 - 1 = 5 &nbsp;&nbsp;|&nbsp;&nbsp; 6 - 4 = 2 &nbsp;&nbsp;|&nbsp;&nbsp; 3 + 3 = 6 &nbsp;&nbsp;|&nbsp;&nbsp; 6 - 2 = 4
        </div>
    """,
    "c": """
        <p><span class="badge-date" style="background:#0284C7;">Méthode Boscher</span></p>
        <p style="font-size:22px; font-weight:900; color:#D90429; margin-top:8px;">Le coq est le roi de la basse-cour.</p>
        <p style="font-size:32px; font-weight:900; color:#E11D48; text-align:center;">c = c</p>
        <div class="cadre-contenu" style="font-size:16px; font-weight:bold; color:#0F172A; line-height:2.4; text-align:center;">
            cu . co . ca .<br>
            co co ri co . l'é cu me . la ca pi ta le . la ca ne .<br>
            l'é co le . la ca po te . la co lè re . le ma ca ro ni .<br>
            <span style="color:#D81B60;">ni co le a u ne pe ti te ca pe li ne .</span>
        </div>
        <p style="font-size:16px; font-weight:bold; color:#D97706; margin-top:14px;">✍️ Écriture et phrase :</p>
        <div style="background:#FFFBEB; border:2px dashed #D97706; border-radius:12px; padding:12px; font-size:14px; font-weight:bold; color:#B45309; line-height:2.2; text-align:center;">
            ✦ <i>cocorico . le côté . la capote . le macaroni .</i><br>
            ✦ <i>émile a été poli à l'école .</i>
        </div>
        <p style="font-size:16px; font-weight:bold; color:#DC2626; margin-top:14px;">🥕 Vocabulaire & Calculs :</p>
        <div style="background:#FEF2F2; border:2px dashed #DC2626; border-radius:12px; padding:12px; font-size:14px; font-weight:bold; color:#991B1B; line-height:2.2; text-align:center;">
            ✦ macaroni &nbsp;—&nbsp; la cape &nbsp;—&nbsp; carottes &nbsp;—&nbsp; canards<br>
            ✦ 7 = 5 + 2 &nbsp;&nbsp;|&nbsp;&nbsp; 7 = 3 + 4 &nbsp;&nbsp;|&nbsp;&nbsp; 3 + 4 = 7 &nbsp;&nbsp;|&nbsp;&nbsp; 1 + 6 = 7
        </div>
    """,
    "d": """
        <p><span class="badge-date" style="background:#0284C7;">Méthode Boscher</span></p>
        <p style="font-size:22px; font-weight:900; color:#D90429; margin-top:8px;">Dédé est malade.</p>
        <p style="font-size:32px; font-weight:900; color:#E11D48; text-align:center;">d = d</p>
        <div class="cadre-contenu" style="font-size:16px; font-weight:bold; color:#0F172A; line-height:2.4; text-align:center;">
            da . dê . de . du . dè . do . di . dé .<br>
            le do do de dé dé . le ma la de . le re mè de .<br>
            u ne da me . le ca ma ra de . le do mi no .<br>
            la mo de . la pé da le . le mo dè le . le dé po té .<br>
            <span style="color:#7C3AED;">ma da me dî ne ra à mi di de pâ té , de rô ti .</span>
        </div>
        <p style="font-size:16px; font-weight:bold; color:#7C3AED; margin-top:14px;">✍️ Écriture et phrase :</p>
        <div style="background:#F5F3FF; border:2px dashed #7C3AED; border-radius:12px; padding:12px; font-size:14px; font-weight:bold; color:#5B21B6; line-height:2.2; text-align:center;">
            ✦ <i>la dame . une pédale . le camarade .</i><br>
            ✦ <i>adèle a copié le modèle de nicole .</i>
        </div>
        <p style="font-size:16px; font-weight:bold; color:#16A34A; margin-top:14px;">🎲 Vocabulaire & Calculs :</p>
        <div style="background:#F0FDF4; border:2px dashed #16A34A; border-radius:12px; padding:12px; font-size:14px; font-weight:bold; color:#15803D; line-height:2.2; text-align:center;">
            ✦ dé &nbsp;—&nbsp; le dodo &nbsp;—&nbsp; damier &nbsp;—&nbsp; domino &nbsp;—&nbsp; radis<br>
            ✦ 7 = 2 + 2 + 2 + 1 &nbsp;&nbsp;|&nbsp;&nbsp; 7 = 3 + 3 + 1 &nbsp;&nbsp;|&nbsp;&nbsp; 7 = 6 + 1
        </div>
    """,
    "v": """
        <p><span class="badge-date" style="background:#0284C7;">Méthode Boscher</span></p>
        <p style="font-size:22px; font-weight:900; color:#D90429; margin-top:8px;">L'avion va vite.</p>
        <p style="font-size:32px; font-weight:900; color:#E11D48; text-align:center;">v = v</p>
        <div class="cadre-contenu" style="font-size:16px; font-weight:bold; color:#0F172A; line-height:2.4; text-align:center;">
            vo . vé . vê . va . vu . ve . vi . vè .<br>
            la lo co mo ti ve . le na vi re . la vé ri té .<br>
            de vi ne . la ve . a va le . dé vo ré . vê tu . vi dé .<br>
            l'a va re . le pa vé . le rê ve . u ne vi pè re .<br>
            <span style="color:#0284C7;">la pi e vo le . é ve li ne va vi te à la ca ve .</span>
        </div>
        <p style="font-size:16px; font-weight:bold; color:#0369A1; margin-top:14px;">✍️ Écriture et phrase :</p>
        <div style="background:#F0F9FF; border:2px dashed #0284C7; border-radius:12px; padding:12px; font-size:14px; font-weight:bold; color:#075985; line-height:2.2; text-align:center;">
            ✦ <i>la vérité . vide la cuve . le navire va vite .</i><br>
            ✦ <i>éva a vu une vipère à côté d'adèle .</i>
        </div>
        <p style="font-size:16px; font-weight:bold; color:#D97706; margin-top:14px;">🚢 Vocabulaire & Calculs :</p>
        <div style="background:#FFFBEB; border:2px dashed #D97706; border-radius:12px; padding:12px; font-size:14px; font-weight:bold; color:#B45309; line-height:2.2; text-align:center;">
            ✦ navire à vapeur &nbsp;—&nbsp; vipère &nbsp;—&nbsp; cuve &nbsp;—&nbsp; avion &nbsp;—&nbsp; navets &nbsp;—&nbsp; voiles<br>
            ✦ 8 = 2 + 2 + 2 + 2 &nbsp;&nbsp;|&nbsp;&nbsp; 8 = 4 + 4 &nbsp;&nbsp;|&nbsp;&nbsp; 6 + 2 = 8 &nbsp;&nbsp;|&nbsp;&nbsp; 5 + 3 = 8
        </div>
    """,
    "s": """
        <p><span class="badge-date" style="background:#0284C7;">Méthode Boscher</span></p>
        <p style="font-size:22px; font-weight:900; color:#D90429; margin-top:8px;">Le semeur.</p>
        <p style="font-size:32px; font-weight:900; color:#E11D48; text-align:center;">s = s</p>
        <div class="cadre-contenu" style="font-size:16px; font-weight:bold; color:#0F172A; line-height:2.4; text-align:center;">
            su . sé . so . sê . si . sa . se . sè .<br>
            si mo ne . sè me . si do ni e . sa me di . sè ve .<br>
            la sè ve . le so li de . la se ri ne . la sa va te .<br>
            la sa li è re . de la sa li ve . de la sa la de .<br>
            <span style="color:#16A34A;">si mo ne a sa li sa ca pe . sa mè re la la ve ra .</span>
        </div>
        <p style="font-size:16px; font-weight:bold; color:#15803D; margin-top:14px;">✍️ Écriture et phrase :</p>
        <div style="background:#F0FDF4; border:2px dashed #16A34A; border-radius:12px; padding:12px; font-size:14px; font-weight:bold; color:#14532D; line-height:2.2; text-align:center;">
            ✦ <i>la dame arrive . la soupe de la salade .</i><br>
            ✦ <i>sidonie sèmera de la salade .</i>
        </div>
        <p style="font-size:16px; font-weight:bold; color:#E11D48; margin-top:14px;">🌱 Vocabulaire :</p>
        <div style="background:#FFF1F2; border:2px dashed #E11D48; border-radius:12px; padding:12px; font-size:14px; font-weight:bold; color:#9F1239; line-height:2.2; text-align:center;">
            ✦ le semeur &nbsp;—&nbsp; la salade &nbsp;—&nbsp; la terrine &nbsp;—&nbsp; la savate<br>
            ✦ 8 = 4 + 4 &nbsp;&nbsp;|&nbsp;&nbsp; 8 = 5 + 3 &nbsp;&nbsp;|&nbsp;&nbsp; 8 = 6 + 2 &nbsp;&nbsp;|&nbsp;&nbsp; 8 = 7 + 1
        </div>
    """,
    "b": """
        <p><span class="badge-date" style="background:#0284C7;">Méthode Boscher</span></p>
        <p style="font-size:22px; font-weight:900; color:#D90429; margin-top:8px;">La cabane du sabotier.</p>
        <p style="font-size:32px; font-weight:900; color:#E11D48; text-align:center;">b = b</p>
        <div class="cadre-contenu" style="font-size:16px; font-weight:bold; color:#0F172A; line-height:2.4; text-align:center;">
            bè . ba . be . bo . bê . bi . bé . bu .<br>
            la sa bo tiè re . du bo bo . la bê te . la ro be . le tu be .<br>
            u ne ca ra bi ne . u ne ca bi ne . de la bi è re .<br>
            lé a dé vi de la bo bi ne . bé bé a sa li sa ro be .<br>
            <span style="color:#9333EA;">le pè re d'é va bâ ti ra u ne ca ba ne so li de .</span>
        </div>
        <p style="font-size:16px; font-weight:bold; color:#7E22CE; margin-top:14px;">✍️ Écriture et phrase :</p>
        <div style="background:#FAF5FF; border:2px dashed #9333EA; border-radius:12px; padding:12px; font-size:14px; font-weight:bold; color:#581C87; line-height:2.2; text-align:center;">
            ✦ <i>bête . cabane . sabotière . lave la robe .</i><br>
            ✦ <i>adèle dévidera la bobine .</i>
        </div>
        <p style="font-size:16px; font-weight:bold; color:#C2410C; margin-top:14px;">🪵 Vocabulaire & Calculs :</p>
        <div style="background:#FFF7ED; border:2px dashed #EA580C; border-radius:12px; padding:12px; font-size:14px; font-weight:bold; color:#9A3412; line-height:2.2; text-align:center;">
            ✦ cabane &nbsp;—&nbsp; bobine &nbsp;—&nbsp; 9 sabots &nbsp;—&nbsp; bûchette &nbsp;—&nbsp; carabine<br>
            ✦ 9 = 2 + 2 + 2 + 2 + 1 &nbsp;&nbsp;|&nbsp;&nbsp; 9 = 4 + 4 + 1 &nbsp;&nbsp;|&nbsp;&nbsp; 9 = 8 + 1 &nbsp;&nbsp;|&nbsp;&nbsp; 9 = 6 + 3
        </div>
    """,
    "f": """
        <p><span class="badge-date" style="background:#0284C7;">Méthode Boscher</span></p>
        <p style="font-size:22px; font-weight:900; color:#D90429; margin-top:8px;">Éva fera du café.</p>
        <p style="font-size:32px; font-weight:900; color:#E11D48; text-align:center;">f = f</p>
        <div class="cadre-contenu" style="font-size:16px; font-weight:bold; color:#0F172A; line-height:2.4; text-align:center;">
            fu . fé . fo . fe . fê . fi . fa . fè .<br>
            ca fe tiè re . ca lo ri fè re . ca ra fe . fa mi ne .<br>
            u ne fè ve . u ne fê te . de la fa ri ne . fi ni .<br>
            la ca ba ne fu me . la lo co mo ti ve fi le vi te .<br>
            <span style="color:#D90429;">é va fe ra du ca fé . sa mè re fe ra du ba ba .</span>
        </div>
        <p style="font-size:16px; font-weight:bold; color:#B91C1C; margin-top:14px;">✍️ Écriture et phrase :</p>
        <div style="background:#FEF2F2; border:2px dashed #DC2626; border-radius:12px; padding:12px; font-size:14px; font-weight:bold; color:#991B1B; line-height:2.2; text-align:center;">
            ✦ <i>farine . fève . café . une carafe de bière .</i><br>
            ✦ <i>liliane sera à la fête de papa samedi .</i>
        </div>
        <p style="font-size:16px; font-weight:bold; color:#047857; margin-top:14px;">☕ Vocabulaire & Calculs :</p>
        <div style="background:#ECFDF5; border:2px dashed #059669; border-radius:12px; padding:12px; font-size:14px; font-weight:bold; color:#065F46; line-height:2.2; text-align:center;">
            ✦ le café &nbsp;—&nbsp; la carafe &nbsp;—&nbsp; les fèves &nbsp;—&nbsp; la farine<br>
            ✦ 9 = 10 - 1 &nbsp;&nbsp;|&nbsp;&nbsp; 10 - 9 = 1 &nbsp;&nbsp;|&nbsp;&nbsp; 9 - 3 = 6 &nbsp;&nbsp;|&nbsp;&nbsp; 9 - 6 = 3
        </div>
    """,
    "j": """
        <p><span class="badge-date" style="background:#0284C7;">Méthode Boscher</span></p>
        <p style="font-size:22px; font-weight:900; color:#D90429; margin-top:8px;">La joie au jour de l'an.</p>
        <p style="font-size:32px; font-weight:900; color:#E11D48; text-align:center;">j = j</p>
        <div class="cadre-contenu" style="font-size:16px; font-weight:bold; color:#0F172A; line-height:2.4; text-align:center;">
            jo . jé . ju . je . ja . jè . ji . jê .<br>
            u ne jo li e ju pe . bé bé ca jo le sa mè re .<br>
            je rê ve . je me lè ve . je me la ve . je dî ne .<br>
            je sè me . je fu me . je vi de la ca ra fe .<br>
            <span style="color:#0284C7;">ja ni ne fe ra u ne jo li e ro be à si mo ne .</span>
        </div>
        <p style="font-size:16px; font-weight:bold; color:#1D4ED8; margin-top:14px;">✍️ Écriture et phrase :</p>
        <div style="background:#EFF6FF; border:2px dashed #2563EB; border-radius:12px; padding:12px; font-size:14px; font-weight:bold; color:#1E40AF; line-height:2.2; text-align:center;">
            ✦ <i>je rêve . je me lave . je dîne . je cajole .</i><br>
            ✦ <i>julia a déjà réparé la robe de sa mère .</i>
        </div>
        <p style="font-size:16px; font-weight:bold; color:#B45309; margin-top:14px;">🧸 Vocabulaire & Calculs :</p>
        <div style="background:#FFFBEB; border:2px dashed #D97706; border-radius:12px; padding:12px; font-size:14px; font-weight:bold; color:#78350F; line-height:2.2; text-align:center;">
            ✦ la jupe &nbsp;—&nbsp; des jouets &nbsp;—&nbsp; des jetons &nbsp;—&nbsp; 10 jacinthes<br>
            ✦ 10 = 2 + 2 + 2 + 2 + 2 &nbsp;&nbsp;|&nbsp;&nbsp; 10 = 5 + 5 &nbsp;&nbsp;|&nbsp;&nbsp; 10 = 8 + 2 &nbsp;&nbsp;|&nbsp;&nbsp; 10 = 7 + 3
        </div>
    """,
    "g": """
        <p><span class="badge-date" style="background:#0284C7;">Méthode Boscher</span></p>
        <p style="font-size:22px; font-weight:900; color:#D90429; margin-top:8px;">Le marché aux légumes.</p>
        <p style="font-size:32px; font-weight:900; color:#E11D48; text-align:center;">g = g</p>
        <div class="cadre-contenu" style="font-size:16px; font-weight:bold; color:#0F172A; line-height:2.4; text-align:center;">
            ga . go . gu .<br>
            le lé gu me . la ga re . la ri go le . l'é ga li té .<br>
            u ne ré ga la de . u ne ga le rie . é ga ré . gâ té .<br>
            u ne fi gu re . du ma la ga . la ga le . je fa go te .<br>
            <span style="color:#2563EB;">la bê te de jé rô me ga lo pe vi te .</span>
        </div>
        <p style="font-size:16px; font-weight:bold; color:#16A34A; margin-top:14px;">✍️ Écriture et phrase :</p>
        <div style="background:#F0FDF4; border:2px dashed #16A34A; border-radius:12px; padding:12px; font-size:14px; font-weight:bold; color:#15803D; line-height:2.2; text-align:center;">
            ✦ <i>gare . galopade . une gamine . je fagote .</i><br>
            ✦ <i>émile se lavera la figure, ira à l'école .</i>
        </div>
        <p style="font-size:16px; font-weight:bold; color:#D97706; margin-top:14px;">🥕 Vocabulaire & Calculs :</p>
        <div style="background:#FFFBEB; border:2px dashed #D97706; border-radius:12px; padding:12px; font-size:14px; font-weight:bold; color:#B45309; line-height:2.2; text-align:center;">
            ✦ légumes &nbsp;—&nbsp; la gare &nbsp;—&nbsp; la galerie &nbsp;—&nbsp; la gourde<br>
            ✦ 10 - 5 = 5 &nbsp;&nbsp;|&nbsp;&nbsp; 10 - 4 = 6 &nbsp;&nbsp;|&nbsp;&nbsp; 10 - 3 = 7 &nbsp;&nbsp;|&nbsp;&nbsp; 10 - 2 = 8
        </div>
    """,
    "ch": """
        <p><span class="badge-date" style="background:#0284C7;">Méthode Boscher</span></p>
        <p style="font-size:22px; font-weight:900; color:#D90429; margin-top:8px;">Le cheval tire la charrue.</p>
        <p style="font-size:32px; font-weight:900; color:#E11D48; text-align:center;">ch = ch</p>
        <div class="cadre-contenu" style="font-size:16px; font-weight:bold; color:#0F172A; line-height:2.4; text-align:center;">
            cha . chi . che . chê . cho . chè . chu .<br>
            u ne bû che . de chê ne . la ga lo che . la chi ca ne .<br>
            la va che . le fi chu . le châ le . la che ve lu re .<br>
            je che mi ne . je bê che . je pê che . je me fâ che .<br>
            <span style="color:#C026D3;">mi che li ne a dé chi ré la po che de sa ro be .</span>
        </div>
        <p style="font-size:16px; font-weight:bold; color:#9333EA; margin-top:14px;">✍️ Écriture et phrase :</p>
        <div style="background:#FAF5FF; border:2px dashed #9333EA; border-radius:12px; padding:12px; font-size:14px; font-weight:bold; color:#6B21A8; line-height:2.2; text-align:center;">
            ✦ <i>je pèle une pêche . je fagote du chêne .</i><br>
            ✦ <i>la gamine a égaré le fichu de sa mère .</i>
        </div>
        <p style="font-size:16px; font-weight:bold; color:#DC2626; margin-top:14px;">🐴 Vocabulaire & Calculs :</p>
        <div style="background:#FEF2F2; border:2px dashed #DC2626; border-radius:12px; padding:12px; font-size:14px; font-weight:bold; color:#991B1B; line-height:2.2; text-align:center;">
            ✦ cheval &nbsp;—&nbsp; charrue &nbsp;—&nbsp; chat &nbsp;—&nbsp; ruche &nbsp;—&nbsp; 10 châtaignes<br>
            ✦ 9 + 1 = 10 &nbsp;&nbsp;|&nbsp;&nbsp; 8 + 2 = 10 &nbsp;&nbsp;|&nbsp;&nbsp; 7 + 3 = 10 &nbsp;&nbsp;|&nbsp;&nbsp; 6 + 4 = 10
        </div>
    """,
    "ou": """
        <p><span class="badge-date" style="background:#0284C7;">Méthode Boscher</span></p>
        <p style="font-size:22px; font-weight:900; color:#D90429; margin-top:8px;">La soupe aux choux.</p>
        <p style="font-size:32px; font-weight:900; color:#E11D48; text-align:center;">ou = ou</p>
        <div class="cadre-contenu" style="font-size:15px; font-weight:bold; color:#0F172A; line-height:2.4; text-align:center;">
            cou . sou . fou . chou . pou . vou . gou .<br>
            la sou piè re . la bou che . le cou de . le bi jou .<br>
            la sou cou pe . la cha lou pe . la cou tu re . la dou ve .<br>
            un fi lou . un mou le . u ne rou te . un jou jou . un sou .<br>
            la cu ve cou le . la pou le cou ve . la bou le rou le .<br>
            <span style="color:#059669;">ju le cou pe un chou , le cou cou a va lé u ne mou che .</span>
        </div>
        <p style="font-size:16px; font-weight:bold; color:#047857; margin-top:14px;">✍️ Écriture et phrase :</p>
        <div style="background:#ECFDF5; border:2px dashed #059669; border-radius:12px; padding:12px; font-size:14px; font-weight:bold; color:#065F46; line-height:2.2; text-align:center;">
            ✦ <i>la poule . une douve . une boule . un coucou .</i><br>
            ✦ <i>éliane achète un joujou , je débouche la carafe .</i><br>
            ✦ <i>ma mère coupera un chou , fera de la soupe .</i>
        </div>
        <p style="font-size:16px; font-weight:bold; color:#D97706; margin-top:14px;">🥬 Vocabulaire & Calculs :</p>
        <div style="background:#FFFBEB; border:2px dashed #D97706; border-radius:12px; padding:12px; font-size:14px; font-weight:bold; color:#B45309; line-height:2.2; text-align:center;">
            ✦ chou &nbsp;—&nbsp; soupe &nbsp;—&nbsp; marmite &nbsp;—&nbsp; toupie &nbsp;—&nbsp; 10 boules<br>
            ✦ 10 - 1 = 9 &nbsp;&nbsp;|&nbsp;&nbsp; 10 - 2 = 8 &nbsp;&nbsp;|&nbsp;&nbsp; 10 - 3 = 7 &nbsp;&nbsp;|&nbsp;&nbsp; 10 - 4 = 6
        </div>
    """,
    "on": """
        <p><span class="badge-date" style="background:#0284C7;">Méthode Boscher</span></p>
        <p style="font-size:22px; font-weight:900; color:#D90429; margin-top:8px;">Léon achète du bonbon.</p>
        <p style="font-size:32px; font-weight:900; color:#E11D48; text-align:center;">on = on</p>
        <div class="cadre-contenu" style="font-size:15px; font-weight:bold; color:#0F172A; line-height:2.4; text-align:center;">
            bon . mon . ton . son . ron . lon . gon .<br>
            con fi tu re . bâ ton . co ton . con te . ga lon . ron de .<br>
            mon ca pu chon . ton pe lo ton . un bon ja pon .<br>
            un bou ton . un gou jon . un mou ton . un bou chon .<br>
            <span style="color:#D90429;">lé on a du bon bon . é cou te le son du vi o lon .</span><br>
            <span style="color:#2563EB;">si mon a ton du son jo li mou ton .</span>
        </div>
        <p style="font-size:16px; font-weight:bold; color:#B91C1C; margin-top:14px;">✍️ Écriture et phrase :</p>
        <div style="background:#FEF2F2; border:2px dashed #DC2626; border-radius:12px; padding:12px; font-size:14px; font-weight:bold; color:#991B1B; line-height:2.2; text-align:center;">
            ✦ <i>le savon . la confiture . un bouchon . le canon .</i><br>
            ✦ <i>léon a goûté le melon . déroule ton peloton .</i><br>
            ✦ <i>léontine a déchiré le galon de son jupon .</i>
        </div>
        <p style="font-size:16px; font-weight:bold; color:#1E3A8A; margin-top:14px;">🍬 Vocabulaire & Nombres pairs :</p>
        <div style="background:#EFF6FF; border:2px dashed #2563EB; border-radius:12px; padding:12px; font-size:14px; font-weight:bold; color:#1E40AF; line-height:2.2; text-align:center;">
            ✦ un mouton &nbsp;—&nbsp; un violon &nbsp;—&nbsp; un melon &nbsp;—&nbsp; des boutons<br>
            ✦ 0 + 2 = 2 &nbsp;&nbsp;|&nbsp;&nbsp; 2 + 2 = 4 &nbsp;&nbsp;|&nbsp;&nbsp; 4 + 2 = 6 &nbsp;&nbsp;|&nbsp;&nbsp; 6 + 2 = 8 &nbsp;&nbsp;|&nbsp;&nbsp; 8 + 2 = 10
        </div>
    """,
    "oi": """
        <p><span class="badge-date" style="background:#0284C7;">Méthode Boscher</span></p>
        <p style="font-size:22px; font-weight:900; color:#D90429; margin-top:8px;">Toinon garde ses oies.</p>
        <p style="font-size:32px; font-weight:900; color:#E11D48; text-align:center;">oi = oi</p>
        <div class="cadre-contenu" style="font-size:15px; font-weight:bold; color:#0F172A; line-height:2.4; text-align:center;">
            voi . toi . boi . moi . foi . poi . noi . joi .<br>
            voi la . u ne voi tu re . u ne é toi le . hor re .<br>
            de l'a voi ne . u ne é cu moi re . u ne pi voi ne .<br>
            u ne poi re . un con voi . la boî te . la mé moi re .<br>
            la cha lou pe à voi le . u ne fi gu re tou te noi re .<br>
            <span style="color:#0284C7;">toi non a chè te ra un cou pon de toi le à la foi re .</span>
        </div>
        <p style="font-size:16px; font-weight:bold; color:#0369A1; margin-top:14px;">✍️ Écriture et phrase :</p>
        <div style="background:#F0F9FF; border:2px dashed #0284C7; border-radius:12px; padding:12px; font-size:14px; font-weight:bold; color:#075985; line-height:2.2; text-align:center;">
            ✦ <i>la mémoire . une foire . la voiture . une boîte .</i><br>
            ✦ <i>voilà du bonbon . simon a semé de l'avoine .</i><br>
            ✦ <i>toinon coupera la toile , léa fera la couette .</i>
        </div>
        <p style="font-size:16px; font-weight:bold; color:#D97706; margin-top:14px;">🦆 Vocabulaire & Nombres impairs :</p>
        <div style="background:#FFFBEB; border:2px dashed #D97706; border-radius:12px; padding:12px; font-size:14px; font-weight:bold; color:#B45309; line-height:2.2; text-align:center;">
            ✦ oie &nbsp;—&nbsp; passoire &nbsp;—&nbsp; voile &nbsp;—&nbsp; armoire &nbsp;—&nbsp; pivoine<br>
            ✦ 1 . 3 . 5 . 7 . 9 &nbsp;&nbsp;|&nbsp;&nbsp; 1 + 2 = 3 &nbsp;&nbsp;|&nbsp;&nbsp; 3 + 2 = 5 &nbsp;&nbsp;|&nbsp;&nbsp; 5 + 2 = 7 &nbsp;&nbsp;|&nbsp;&nbsp; 7 + 2 = 9
        </div>
    """,
    "an": """
        <p><span class="badge-date" style="background:#0284C7;">Méthode Boscher</span></p>
        <p style="font-size:22px; font-weight:900; color:#D90429; margin-top:8px;">Entrez dans la danse.</p>
        <p style="font-size:32px; font-weight:900; color:#E11D48; text-align:center;">an = an</p>
        <div class="cadre-contenu" style="font-size:15px; font-weight:bold; color:#0F172A; line-height:2.4; text-align:center;">
            pan . gan . man . chan . ban . can . dan .<br>
            u ne chan son . u ne man da ri ne . ma man . ma tan te .<br>
            la san té . u ne a man de . la man che . la fan fa re .<br>
            un ru ban . mon pan ta lon . un ou ra gan . an toi ne .<br>
            fan chon la ve la ban de de toi le , je cou pe la poi re .<br>
            <span style="color:#D81B60;">jean dan se ra di man che à la fê te du can ton .</span>
        </div>
        <p style="font-size:16px; font-weight:bold; color:#C026D3; margin-top:14px;">✍️ Écriture et phrase :</p>
        <div style="background:#FAF5FF; border:2px dashed #A855F7; border-radius:12px; padding:12px; font-size:14px; font-weight:bold; color:#7E22CE; line-height:2.2; text-align:center;">
            ✦ <i>la danse . une chanson . un ouragan . ma tante .</i><br>
            ✦ <i>la méchante boude . voilà la soupe fumante .</i><br>
            ✦ <i>antoine a déchiré son joli pantalon de coton .</i>
        </div>
        <p style="font-size:16px; font-weight:bold; color:#16A34A; margin-top:14px;">🍊 Vocabulaire & Moitiés :</p>
        <div style="background:#F0FDF4; border:2px dashed #16A34A; border-radius:12px; padding:12px; font-size:14px; font-weight:bold; color:#15803D; line-height:2.2; text-align:center;">
            ✦ un banc &nbsp;—&nbsp; mandarine &nbsp;—&nbsp; un ruban &nbsp;—&nbsp; anse &nbsp;—&nbsp; amandes<br>
            ✦ moitié de 2 = 1 &nbsp;&nbsp;|&nbsp;&nbsp; de 4 = 2 &nbsp;&nbsp;|&nbsp;&nbsp; de 6 = 3 &nbsp;&nbsp;|&nbsp;&nbsp; de 8 = 4 &nbsp;&nbsp;|&nbsp;&nbsp; de 10 = 5
        </div>
    """,
    "in": """
        <p><span class="badge-date" style="background:#0284C7;">Méthode Boscher</span></p>
        <p style="font-size:22px; font-weight:900; color:#D90429; margin-top:8px;">Le poteau indicateur.</p>
        <p style="font-size:32px; font-weight:900; color:#E11D48; text-align:center;">in = in</p>
        <div class="cadre-contenu" style="font-size:15px; font-weight:bold; color:#0F172A; line-height:2.4; text-align:center;">
            vin . lin . pin . fin . tin . rin . min . din .<br>
            le sa pin . le che min . le ga min . le ma rin . ma lin .<br>
            un la pin . un din don . u ne din de . le ca le pin .<br>
            la pin ta de . du bou din . le pé pin . un pan tin . du lin .<br>
            u ne re din go te noi re . an to nin fe ra du bon vin .<br>
            <span style="color:#2563EB;">le pin son chan te de bon ma tin à cô té du mou lin .</span>
        </div>
        <p style="font-size:16px; font-weight:bold; color:#1D4ED8; margin-top:14px;">✍️ Écriture et phrase :</p>
        <div style="background:#EFF6FF; border:2px dashed #2563EB; border-radius:12px; padding:12px; font-size:14px; font-weight:bold; color:#1E40AF; line-height:2.2; text-align:center;">
            ✦ <i>un calepin . du boudin . un sapin . le chemin .</i><br>
            ✦ <i>le gamin fera le pantin . le pépin de la poire .</i><br>
            ✦ <i>mon lapin a dévoré toute l'avoine de ma tante .</i>
        </div>
        <p style="font-size:16px; font-weight:bold; color:#16A34A; margin-top:14px;">🌲 Vocabulaire & Calculs :</p>
        <div style="background:#F0FDF4; border:2px dashed #16A34A; border-radius:12px; padding:12px; font-size:14px; font-weight:bold; color:#15803D; line-height:2.2; text-align:center;">
            ✦ un sapin &nbsp;—&nbsp; un dindon &nbsp;—&nbsp; 3 pintades &nbsp;—&nbsp; le moulin<br>
            ✦ 1 + 3 = 4 &nbsp;&nbsp;|&nbsp;&nbsp; 4 + 3 = 7 &nbsp;&nbsp;|&nbsp;&nbsp; 7 + 3 = 10 &nbsp;&nbsp;|&nbsp;&nbsp; 9 - 3 = 6 &nbsp;&nbsp;|&nbsp;&nbsp; 6 - 3 = 3
        </div>
    """,
    "br": """
        <p><span class="badge-date" style="background:#0284C7;">Méthode Boscher</span></p>
        <p style="font-size:13px; color:#64748B; font-weight:bold; margin:4px 0; text-align:center;">in. oi. eu. un. on. an. ou.</p>
        <p style="font-size:22px; font-weight:900; color:#D90429; margin:6px 0; text-align:center;">la chèvre broute.</p>
        <p style="font-size:30px; font-weight:900; color:#E11D48; margin:4px 0; text-align:center;">br. &nbsp; pr. &nbsp; dr. &nbsp; vr.</p>
        
        <div class="cadre-contenu" style="font-size:15px; font-weight:bold; color:#0F172A; line-height:2.2; text-align:center;">
            <span style="color:#C026D3; font-size:17px;">pro. vre. bran. droi. vri. pru. dré.</span><br><br>
            lè vre. fou dre. pro me na de. brû lu re. pro fon de.<br>
            pou dre. li è vre. bro che. bra vou re. a droi te.<br>
            la pro pre té. un ca dre. u ne cou leu vre. je bro de.<br>
            u ne bran che de sa pin. ta fi gu re se ra pro pre.<br>
            an dré, prê te-moi un li vre, la chè vre brou te le pré.<br>
            ma man a pré pa ré un bon pâ té de li è vre.
        </div>

        <p style="font-size:16px; font-weight:bold; color:#0D47A1; margin-top:12px;">✍️ Écriture courante (cursive) :</p>
        <div style="background:#F0F9FF; border:2px dashed #0284C7; border-radius:12px; padding:12px; font-size:14px; font-style:italic; font-weight:bold; color:#0369A1; line-height:2.1; text-align:left;">
            un lièvre. une prune. la foudre. je brode.<br>
            maman achète du poivre. voilà la broche.<br>
            andré a vu une couleuvre à la promenade.
        </div>

        <p style="font-size:16px; font-weight:bold; color:#16A34A; margin-top:12px;">🖼️ Objets & Calculs :</p>
        <div style="background:#F0FDF4; border:2px dashed #16A34A; border-radius:12px; padding:12px; font-size:13px; font-weight:bold; color:#15803D; line-height:2;">
            ✦ un cadre &nbsp;|&nbsp; ✦ une couleuvre &nbsp;|&nbsp; ✦ des prunes<br>
            <b>11 = 10 + 1</b><br>
            11 = 9 + 2 &nbsp;&nbsp;|&nbsp;&nbsp; 11 = 8 + 3 &nbsp;&nbsp;|&nbsp;&nbsp; 3 + 8 = 11 &nbsp;&nbsp;|&nbsp;&nbsp; 1 + 10 = 11<br>
            11 = 8 + 3 &nbsp;&nbsp;|&nbsp;&nbsp; 11 = 6 + 5 &nbsp;&nbsp;|&nbsp;&nbsp; 5 + 6 = 11 &nbsp;&nbsp;|&nbsp;&nbsp; 4 + 7 = 11<br>
            11 = 7 + 4 &nbsp;&nbsp;|&nbsp;&nbsp; 11 = 4 + 7 &nbsp;&nbsp;|&nbsp;&nbsp; 8 + 3 = 11 &nbsp;&nbsp;|&nbsp;&nbsp; 6 + 5 = 11<br>
            11 = 6 + 5 &nbsp;&nbsp;|&nbsp;&nbsp; 11 = 2 + 9 &nbsp;&nbsp;|&nbsp;&nbsp; 7 + 4 = 11 &nbsp;&nbsp;|&nbsp;&nbsp; 9 + 2 = 11<br>
            11 = 5 + 5 + 1 &nbsp;|&nbsp; 11 = 1 + 10 &nbsp;|&nbsp; 2 + 9 = 11 &nbsp;|&nbsp; 5 + 6 = 11
        </div>
    """,
    "fr": """
        <p><span class="badge-date" style="background:#0284C7;">Méthode Boscher</span></p>
        <p style="font-size:13px; color:#64748B; font-weight:bold; margin:4px 0; text-align:center;">eu. vr. un. ou. pr. oi. br. on. dr. an. on.</p>
        <p style="font-size:22px; font-weight:900; color:#D90429; margin:6px 0; text-align:center;">sous la grêle.</p>
        <p style="font-size:30px; font-weight:900; color:#E11D48; margin:4px 0; text-align:center;">fr. &nbsp; tr. &nbsp; cr. &nbsp; gr.</p>
        
        <div class="cadre-contenu" style="font-size:15px; font-weight:bold; color:#0F172A; line-height:2.2; text-align:center;">
            <span style="color:#C026D3; font-size:17px;">croi. tre. grin. frè. tran. gré. crin.</span><br><br>
            la grê le. un a bri. du cha grin. un li tre. un fri pon.<br>
            vi tre. sou fre. é cri tu re. cru che. gran di. dé grin go lé.<br>
            tran che. fri tu re. gri ve. fre lon. croû ton. su cre. croî tre.<br>
            la fou dre gron de. mon frè re é cri ra à no tre tan te.<br>
            je bro de seu le u ne cra va te. ou vre la fe nê tre.<br>
            vo tre ca ma ra de a sa li la gra vu re de son li vre.
        </div>

        <p style="font-size:16px; font-weight:bold; color:#991B1B; margin-top:12px;">✍️ Écriture courante (cursive) :</p>
        <div style="background:#FEF2F2; border:2px dashed #DC2626; border-radius:12px; padding:12px; font-size:14px; font-style:italic; font-weight:bold; color:#991B1B; line-height:2.1; text-align:left;">
            la friture. du pétrole. un croûton. de la grêle.<br>
            votre jeune frère a du chagrin. la cravate brune.<br>
            la montre de votre neveu a un joli cadran.
        </div>

        <p style="font-size:16px; font-weight:bold; color:#D97706; margin-top:12px;">🍓 Objets & Calculs :</p>
        <div style="background:#FFFBEB; border:2px dashed #D97706; border-radius:12px; padding:12px; font-size:13px; font-weight:bold; color:#B45309; line-height:2;">
            ✦ une cravate &nbsp;|&nbsp; ✦ une grive &nbsp;|&nbsp; ✦ un frelon &nbsp;|&nbsp; ✦ une montre &nbsp;|&nbsp; ✦ framboises<br>
            <b>11 - 1 = 10</b><br>
            11 - 2 = 9 &nbsp;&nbsp;|&nbsp;&nbsp; 11 - 7 = 4 &nbsp;&nbsp;|&nbsp;&nbsp; 11 - 4 = 7 &nbsp;&nbsp;|&nbsp;&nbsp; 5 + 5 = 10<br>
            11 - 5 = 6 &nbsp;&nbsp;|&nbsp;&nbsp; 11 - 6 = 5 &nbsp;&nbsp;|&nbsp;&nbsp; 11 - 6 = 5 &nbsp;&nbsp;|&nbsp;&nbsp; 11 - 7 = 4<br>
            11 - 3 = 8 &nbsp;&nbsp;|&nbsp;&nbsp; 11 - 8 = 3 &nbsp;&nbsp;|&nbsp;&nbsp; 11 - 8 = 3 &nbsp;&nbsp;|&nbsp;&nbsp; 7 + 4 = 11<br>
            11 - 6 = 5 &nbsp;&nbsp;|&nbsp;&nbsp; 11 - 4 = 7 &nbsp;&nbsp;|&nbsp;&nbsp; 11 - 5 = 6 &nbsp;&nbsp;|&nbsp;&nbsp; 9 + 2 = 11<br>
            11 - 8 = 3 &nbsp;&nbsp;|&nbsp;&nbsp; 11 - 9 = 2 &nbsp;&nbsp;|&nbsp;&nbsp; 11 - 9 = 2 &nbsp;&nbsp;|&nbsp;&nbsp; 11 - 5 = 6
        </div>
    """,
    "bl": """
        <p><span class="badge-date" style="background:#0284C7;">Méthode Boscher</span></p>
        <p style="font-size:13px; color:#64748B; font-weight:bold; margin:4px 0; text-align:center;">in. eu. an. tr. gr. in. oi. dr. pr. on. ou. br.</p>
        <p style="font-size:22px; font-weight:900; color:#D90429; margin:6px 0; text-align:center;">andré joue de la flûte.</p>
        <p style="font-size:30px; font-weight:900; color:#E11D48; margin:4px 0; text-align:center;">bl. &nbsp; pl. &nbsp; fl.</p>
        
        <div class="cadre-contenu" style="font-size:15px; font-weight:bold; color:#0F172A; line-height:2.2; text-align:center;">
            <span style="color:#C026D3; font-size:17px;">pla. blé. fleu. bli. plan. flo. plu. flé.</span><br><br>
            plan che. meu ble. éta bli. ta ble. flû te. plu me.<br>
            trè fle. fla con. pla ta ne. o bli gai toi re. blon de. flé tri.<br>
            un fleu ve. u ne fa ble. je pleu re. je plan te un pin.<br>
            le feu ron fle. du sa ble fin. la plan te fleu ri ra.<br>
            la meu niè re mou dra le blé. de la dou blu re blan che.<br>
            flo ra a trou vé son pro blè me seu le. bra vo flo ra.
        </div>

        <p style="font-size:16px; font-weight:bold; color:#065F46; margin-top:12px;">✍️ Écriture courante (cursive) :</p>
        <div style="background:#ECFDF5; border:2px dashed #059669; border-radius:12px; padding:12px; font-size:14px; font-style:italic; font-weight:bold; color:#065F46; line-height:2.1; text-align:left;">
            le flacon. la planche. du plâtre. je plante un pin.<br>
            flora a du ruban bleu. de la doublure neuve.<br>
            andré a semé du trèfle. planté un platane.
        </div>

        <p style="font-size:16px; font-weight:bold; color:#2563EB; margin-top:12px;">🎶 Objets & Calculs :</p>
        <div style="background:#EFF6FF; border:2px dashed #2563EB; border-radius:12px; padding:12px; font-size:13px; font-weight:bold; color:#1E40AF; line-height:2;">
            ✦ une flûte &nbsp;|&nbsp; ✦ un flacon &nbsp;|&nbsp; ✦ platane &nbsp;|&nbsp; ✦ trèfle<br>
            12 = 6 + 6 &nbsp;&nbsp;|&nbsp;&nbsp; 12 = 5 + 7 &nbsp;&nbsp;|&nbsp;&nbsp; 8 + 4 = 12 &nbsp;&nbsp;|&nbsp;&nbsp; 9 + 3 = 12<br>
            12 = 10 + 2 &nbsp;&nbsp;|&nbsp;&nbsp; 12 = 4 + 8 &nbsp;&nbsp;|&nbsp;&nbsp; 5 + 7 = 12 &nbsp;&nbsp;|&nbsp;&nbsp; 4 + 8 = 12<br>
            12 = 9 + 3 &nbsp;&nbsp;|&nbsp;&nbsp; 12 = 3 + 9 &nbsp;&nbsp;|&nbsp;&nbsp; 6 + 6 = 12 &nbsp;&nbsp;|&nbsp;&nbsp; 10 + 2 = 12<br>
            12 = 8 + 4 &nbsp;&nbsp;|&nbsp;&nbsp; 12 = 10 + 2 &nbsp;|&nbsp; 3 + 9 = 12 &nbsp;&nbsp;|&nbsp;&nbsp; 6 + 6 = 12<br>
            12 = 7 + 5 &nbsp;&nbsp;|&nbsp;&nbsp; 12 = 2 + 10 &nbsp;|&nbsp; 7 + 5 = 12 &nbsp;&nbsp;|&nbsp;&nbsp; 5 + 7 = 12<br>
            <b>6 fois 2 = 12 &nbsp;|&nbsp; 2 fois 6 = 12 &nbsp;|&nbsp; 3 fois 4 = 12</b>
        </div>
    """,
    "cl": """
        <p><span class="badge-date" style="background:#0284C7;">Méthode Boscher</span></p>
        <p style="font-size:13px; color:#64748B; font-weight:bold; margin:4px 0; text-align:center;">fr. un. tr. pl. on. an. bl. oi. eu. fr. ou. in.</p>
        <p style="font-size:22px; font-weight:900; color:#D90429; margin:6px 0; text-align:center;">la demeure de mon oncle.</p>
        <p style="font-size:30px; font-weight:900; color:#E11D48; margin:4px 0; text-align:center;">cl. &nbsp; gl.</p>
        
        <div class="cadre-contenu" style="font-size:15px; font-weight:bold; color:#0F172A; line-height:2.2; text-align:center;">
            <span style="color:#C026D3; font-size:17px;">glan. clé. glou. clo. gloi. cla. cloi.</span><br><br>
            clô tu re. é glan ti ne. bou cle. on gle. ré cla mé.<br>
            gloi re. glo be. clé ma ti te. trin gle. cla po té. clo re.<br>
            un clou. l'é pin gle. le glou ton. la clo che. je gla ne.<br>
            le glou glou du fla con. mon on cle a un é ta bli.<br>
            la voi le du na vi re se gon fle. la fou dre é cla te.<br>
            la clé ma ti te cou vre la clô tu re du jar din.
        </div>

        <p style="font-size:16px; font-weight:bold; color:#581C87; margin-top:12px;">✍️ Écriture courante (cursive) :</p>
        <div style="background:#FAF5FF; border:2px dashed #9333EA; border-radius:12px; padding:12px; font-size:14px; font-style:italic; font-weight:bold; color:#581C87; line-height:2.1; text-align:left;">
            un clou. une glande. la cloche. une épingle.<br>
            votre frère réclame à boire. coupe ton ongle.<br>
            léon a retrouvé la clé de l'étable de son oncle.
        </div>

        <p style="font-size:16px; font-weight:bold; color:#B45309; margin-top:12px;">🔔 Objets & Calculs :</p>
        <div style="background:#FFFBEB; border:2px dashed #D97706; border-radius:12px; padding:12px; font-size:13px; font-weight:bold; color:#B45309; line-height:2;">
            ✦ clôture &nbsp;|&nbsp; ✦ cloche &nbsp;|&nbsp; ✦ glands &nbsp;|&nbsp; ✦ clématite &nbsp;|&nbsp; ✦ églantines<br>
            12 - 6 = 6 &nbsp;&nbsp;|&nbsp;&nbsp; 12 - 10 = 2 &nbsp;|&nbsp; 12 - 4 = 8 &nbsp;&nbsp;|&nbsp;&nbsp; 8 + 4 = 12<br>
            12 - 9 = 3 &nbsp;&nbsp;|&nbsp;&nbsp; 12 - 5 = 7 &nbsp;&nbsp;|&nbsp; 12 - 7 = 5 &nbsp;&nbsp;|&nbsp;&nbsp; 12 - 2 = 10<br>
            12 - 8 = 4 &nbsp;&nbsp;|&nbsp;&nbsp; 12 - 3 = 9 &nbsp;&nbsp;|&nbsp; 12 - 9 = 3 &nbsp;&nbsp;|&nbsp;&nbsp; 12 - 6 = 6<br>
            12 - 4 = 8 &nbsp;&nbsp;|&nbsp;&nbsp; 12 - 2 = 10 &nbsp;|&nbsp; 12 - 6 = 6 &nbsp;&nbsp;|&nbsp;&nbsp; 9 + 3 = 12<br>
            12 - 7 = 5 &nbsp;&nbsp;|&nbsp;&nbsp; 12 - 1 = 11 &nbsp;|&nbsp; 12 - 3 = 9 &nbsp;&nbsp;|&nbsp;&nbsp; 7 + 5 = 12
        </div>
    """,
    "ar": """
        <p><span class="badge-date" style="background:#0284C7;">Méthode Boscher</span></p>
        <p style="font-size:13px; color:#64748B; font-weight:bold; margin:4px 0; text-align:center;">oi. fl. an. vr. pl. in. cr. el. eu. bl. on. dr.</p>
        <p style="font-size:22px; font-weight:900; color:#D90429; margin:6px 0; text-align:center;">le fleuve déborde.</p>
        <p style="font-size:30px; font-weight:900; color:#E11D48; margin:4px 0; text-align:center;">ar. &nbsp; or. &nbsp; ir. &nbsp; ur.</p>
        
        <div class="cadre-contenu" style="font-size:15px; font-weight:bold; color:#0F172A; line-height:2.2; text-align:center;">
            <span style="color:#C026D3; font-size:17px;">char. cor. gar. por. sur. bor. vrir.</span><br><br>
            jar din. ar bre. por te. bor du re. cor ne. ou vrir. sor tir.<br>
            mar ché. mar mi te. sar di ne. char don. é cor ché. bar bu.<br>
            la cor de. du char bon. u ne ar moi re. dor mir. mor dre.<br>
            mar ti ne re gar de sur la por te. mé dor te mor dra.<br>
            le fleu ve a dé bor dé sur le jar din plan té.<br>
            por te la mou tar de, le su cre, la crè me sur la ta ble.
        </div>

        <p style="font-size:16px; font-weight:bold; color:#0F172A; margin-top:12px;">✍️ Écriture courante (cursive) :</p>
        <div style="background:#F8FAFC; border:2px dashed #64748B; border-radius:12px; padding:12px; font-size:14px; font-style:italic; font-weight:bold; color:#1E293B; line-height:2.1; text-align:left;">
            une virgule. un torchon. du marbre. le marché.<br>
            émile a bu du vin pur. aline partira jeudi.<br>
            ton oncle va venir, va ouvrir la porte du jardin.
        </div>

        <p style="font-size:16px; font-weight:bold; color:#16A34A; margin-top:12px;">🌳 Objets & Calculs :</p>
        <div style="background:#F0FDF4; border:2px dashed #16A34A; border-radius:12px; padding:12px; font-size:13px; font-weight:bold; color:#15803D; line-height:2;">
            ✦ un arbre &nbsp;|&nbsp; ✦ cornes &nbsp;|&nbsp; ✦ une tortue &nbsp;|&nbsp; ✦ sardines &nbsp;|&nbsp; ✦ chardons<br>
            13 = 10 + 3 &nbsp;&nbsp;|&nbsp;&nbsp; 13 = 6 + 6 + 1 &nbsp;|&nbsp; 5 + 8 = 13 &nbsp;&nbsp;|&nbsp;&nbsp; 2 + 9 = 11<br>
            13 = 9 + 4 &nbsp;&nbsp;|&nbsp;&nbsp; 13 = 5 + 8 &nbsp;&nbsp;&nbsp;&nbsp;|&nbsp; 9 + 4 = 13 &nbsp;&nbsp;|&nbsp;&nbsp; 10 + 3 = 13<br>
            13 = 8 + 5 &nbsp;&nbsp;|&nbsp;&nbsp; 13 = 3 + 10 &nbsp;&nbsp;&nbsp;|&nbsp; 7 + 6 = 13 &nbsp;&nbsp;|&nbsp;&nbsp; 8 + 4 = 12<br>
            13 = 7 + 6 &nbsp;&nbsp;|&nbsp;&nbsp; 13 = 6 + 7 &nbsp;&nbsp;&nbsp;&nbsp;|&nbsp; 6 + 7 = 13 &nbsp;&nbsp;|&nbsp;&nbsp; 4 + 9 = 13<br>
            13 = 11 + 2 &nbsp;|&nbsp;&nbsp; 13 = 4 + 9 &nbsp;&nbsp;&nbsp;&nbsp;|&nbsp; 3 + 10 = 13 &nbsp;|&nbsp;&nbsp; 5 + 7 = 12
        </div>
    """,
    "al": """
        <p><span class="badge-date" style="background:#0284C7;">Méthode Boscher</span></p>
        <p style="font-size:13px; color:#64748B; font-weight:bold; margin:4px 0; text-align:center;">vr. ir. in. cl. or. an. gr. un. ur. bl. ar. eu.</p>
        <p style="font-size:22px; font-weight:900; color:#D90429; margin:6px 0; text-align:center;">le maréchal ferre le cheval.</p>
        <p style="font-size:30px; font-weight:900; color:#E11D48; margin:4px 0; text-align:center;">al. &nbsp; il. &nbsp; ol. &nbsp; ul.</p>
        
        <div class="cadre-contenu" style="font-size:15px; font-weight:bold; color:#0F172A; line-height:2.2; text-align:center;">
            <span style="color:#C026D3; font-size:17px;">bal. col. fil. bol. mal. vol. nul. val.</span><br><br>
            a ni mal. bo cal. cal cul. a vril. ré col te. cou til.<br>
            car na val. ca nal. in sul te. bru tal. ma ti nal. un bal.<br>
            un vol can. un gril. u ne cul bu te. un bol. je val se.<br>
            jean bri de son che val. mon lo cal se ra a gré a ble.<br>
            clo til de boi ra un bol de crè me. j'a chè ve mon cal cul.<br>
            le ma ré chal cou pe la cor ne du che val.
        </div>

        <p style="font-size:16px; font-weight:bold; color:#0369A1; margin-top:12px;">✍️ Écriture courante (cursive) :</p>
        <div style="background:#F0F9FF; border:2px dashed #0284C7; border-radius:12px; padding:12px; font-size:14px; font-style:italic; font-weight:bold; color:#075985; line-height:2.1; text-align:left;">
            un maréchal. du tumulte. une salle de bal.<br>
            je coupe le crin du cheval. médor va à son chenil.<br>
            la voiture de la bouchère a culbuté à côté du fleuve.
        </div>

        <p style="font-size:16px; font-weight:bold; color:#D97706; margin-top:12px;">🎈 Objets & Calculs :</p>
        <div style="background:#FFFBEB; border:2px dashed #D97706; border-radius:12px; padding:12px; font-size:13px; font-weight:bold; color:#B45309; line-height:2;">
            ✦ un bocal &nbsp;|&nbsp; ✦ un bol &nbsp;|&nbsp; ✦ un gril &nbsp;|&nbsp; ✦ des ballons<br>
            13 - 3 = 10 &nbsp;&nbsp;|&nbsp;&nbsp; 13 - 2 = 11 &nbsp;|&nbsp; 13 - 7 = 6 &nbsp;&nbsp;|&nbsp;&nbsp; 13 - 8 = 5<br>
            13 - 1 = 12 &nbsp;&nbsp;|&nbsp;&nbsp; 13 - 5 = 8 &nbsp;&nbsp;|&nbsp; 13 - 5 = 8 &nbsp;&nbsp;|&nbsp;&nbsp; 11 - 4 = 7<br>
            13 - 4 = 9 &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp; 13 - 10 = 3 &nbsp;|&nbsp; 13 - 6 = 7 &nbsp;&nbsp;|&nbsp;&nbsp; 10 - 5 = 5<br>
            13 - 6 = 7 &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp; 13 - 9 = 4 &nbsp;&nbsp;|&nbsp; 13 - 10 = 3 &nbsp;|&nbsp;&nbsp; 12 - 6 = 6<br>
            13 - 8 = 5 &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp; 13 - 7 = 6 &nbsp;&nbsp;|&nbsp; 13 - 4 = 9 &nbsp;&nbsp;|&nbsp;&nbsp; 13 - 5 = 8
        </div>
    """,
    "en": """
        <p><span class="badge-date" style="background:#0284C7;">Méthode Boscher</span></p>
        <p style="font-size:22px; font-weight:900; color:#D90429; margin-top:8px;">Le vent souffle.</p>
        <p style="font-size:32px; font-weight:900; color:#E11D48; text-align:center;">en = en</p>

        <div class="cadre-contenu" style="font-size:16px; font-weight:bold; color:#0F172A; line-height:2.4; text-align:center;">
            pen . gen . men . chen . ben . ten . ren .<br>
            le ven t . la den te . un ser pen t . la gen tian e .<br>
            une cen taine . un quen ouille . la tor ren te .<br>
            <span style="color:#2563EB;">le ven t souf fle for t sur le gran d sa pin .</span>
        </div>

        <p style="font-size:16px; font-weight:bold; color:#16A34A; margin-top:14px;">✍️ Écriture et phrase :</p>
        <div style="background:#F0FDF4; border:2px dashed #16A34A; border-radius:12px; padding:12px; font-size:14px; font-weight:bold; color:#15803D; line-height:2.2; text-align:center;">
            ✦ <i>le vent . une dent . un serpent .</i><br>
            ✦ <i>jules a peur du grand serpent vert .</i>
        </div>
    """
}

@app.route("/methode-boscher/<lecon>")
def page_lecon_boscher(lecon):
    corps = BOSCHER_CONTENUS.get(lecon, "<p>Leçon introuvable</p>")
    html = f"""
        <div style="text-align:center;">
            {corps}
        </div>
        <div style="text-align:center; margin-top:16px;">
            <a href="/methode-boscher" class="btn-retour">← Revenir à la Méthode Boscher</a>
        </div>
    """
    return afficher(html)

# =============================================================================
# SECTION LEÇONS DE CHOSE
# =============================================================================
@app.route("/lecons-de-chose")
def page_lecons_de_chose():
    html = """
        <div class="cadre-menu">
            <h1 class="titre-principal" id="titre-chose">
                Leçons de chose<br>
                <span class="sous-titre-selection" id="sous-titre-chose">Choisissez une leçon</span>
            </h1>

            <button type="button" class="btn-rose btn-option" data-url="/lecons-de-chose/nagent" data-titre="LES ANIMAUX QUI NAGENT.">LES ANIMAUX QUI NAGENT.</button>
            <button type="button" class="btn-rose btn-option" data-url="/lecons-de-chose/volent" data-titre="LES ANIMAUX QUI VOLENT.">LES ANIMAUX QUI VOLENT.</button>
            <button type="button" class="btn-rose btn-option" data-url="/lecons-de-chose/marchent" data-titre="LES ANIMAUX QUI MARCHENT.">LES ANIMAUX QUI  MARCHENT.</button>
            <button type="button" class="btn-rose btn-option" data-url="/lecons-de-chose/rampent" data-titre="LES ANIMAUX QUI RAMPENT.">LES ANIMAUX QUI RAMPENT.</button>

            <button type="button" id="btn-valider" class="btn-choose">➜ Choose</button>
            <a href="/" class="btn-retour">← Revenir au choix</a>
        </div>

        <script>
            let urlChoisie = "/lecons-de-chose/nagent";
            const boutons = document.querySelectorAll('.btn-option');
            const sousTitre = document.getElementById('sous-titre-chose');
            const btnValider = document.getElementById('btn-valider');

            boutons[0].classList.add('selected');
            sousTitre.textContent = boutons[0].getAttribute('data-titre');

            boutons.forEach(b => {
                b.addEventListener('click', () => {
                    boutons.forEach(x => x.classList.remove('selected'));
                    b.classList.add('selected');
                    urlChoisie = b.getAttribute('data-url');
                    sousTitre.textContent = b.getAttribute('data-titre');
                });
            });

            btnValider.addEventListener('click', () => {
                window.location.href = urlChoisie;
            });
        </script>
    """
    return afficher(html)

@app.route("/lecons-de-chose/nagent")
def page_chose_nagent():
    html = """
        <div style="text-align:center;">
            <span class="badge-date" style="background:#0284C7;">📅 Mercredi 01 Octobre 2026</span>
            <div class="titre-lecon" style="color:#D90429;">LES ANIMAUX QUI NAGENT</div>
        </div>

        <div style="background:#E0F2FE; border-left:5px solid #0284C7; border-radius:10px; padding:12px; font-size:14px; line-height:2; color:#0369A1; margin-bottom:14px;">
            ✦ <b>Définition :</b> Les animaux qui nagent sont des animaux qui se déplacent dans l'eau. Ils utilisent généralement leurs <b>nageoires</b> ou leurs <b>pattes palmées</b> pour nager et se déplacer.
        </div>

        <p style="font-size:16px; font-weight:800; color:#0D47A1; margin-bottom:8px;">🐟 Les animaux qui nagent :</p>
        <div style="background:#FFFFFF; border:3px solid #80DEEA; border-radius:14px; padding:14px; font-size:15px; font-weight:bold; color:#0F172A; line-height:2.4;">
            ✦ <b style="color:#0284C7;">le poisson</b> &nbsp;&nbsp;|&nbsp;&nbsp; ✦ <b style="color:#0284C7;">le dauphin</b><br>
            ✦ <b style="color:#0284C7;">le requin</b> &nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp; ✦ <b style="color:#0284C7;">le phoque</b><br>
            ✦ <b style="color:#0284C7;">le crabe</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp; ✦ <b style="color:#0284C7;">l'anguille</b><br>
            ✦ <b style="color:#0284C7;">la tortue de mer</b> &nbsp;&nbsp;|&nbsp;&nbsp; ✦ <b style="color:#0284C7;">la baleine</b><br>
            ✦ <b style="color:#0284C7;">le crocodile</b> (dans l'eau) &nbsp;&nbsp;|&nbsp;&nbsp; ✦ <b style="color:#0284C7;">le canard</b>
        </div>

        <div style="background:#F0FDF4; border:2px dashed #16A34A; border-radius:12px; padding:12px; margin-top:14px; font-size:14px; font-weight:bold; color:#15803D; line-height:2;">
            💡 <b>À retenir :</b><br>
            • Les poissons ont des nageoires et des branchies pour respirer dans l'eau.<br>
            • Le dauphin et la baleine sont des mammifères marins qui savent très bien nager !
        </div>

        <div style="text-align:center;">
            <a href="/lecons-de-chose" class="btn-retour">← Revenir aux Leçons de chose</a>
        </div>
    """
    return afficher(html)

@app.route("/lecons-de-chose/volent")
def page_chose_volent():
    html = """
        <div style="text-align:center;">
            <span class="badge-date" style="background:#0284C7;">📅 Vendredi 03 Octobre 2026</span>
            <div class="titre-lecon" style="color:#D90429;">LES ANIMAUX QUI VOLENT</div>
        </div>

        <div style="background:#FEF3C7; border-left:5px solid #F59E0B; border-radius:10px; padding:12px; font-size:14px; line-height:2; color:#92400E; margin-bottom:14px;">
            ✦ <b>Définition :</b> Les animaux qui volent sont des animaux qui ont des <b>ailes</b> pour se déplacer dans l'air.
        </div>

        <p style="font-size:16px; font-weight:800; color:#B45309; margin-bottom:8px;">🦅 1. Les oiseaux et mammifères volants :</p>
        <div style="background:#FFFFFF; border:3px solid #80DEEA; border-radius:14px; padding:12px; font-size:15px; font-weight:bold; color:#0F172A; line-height:2.3;">
            ✦ <b style="color:#EA580C;">le pigeon</b> &nbsp;&nbsp;|&nbsp;&nbsp; ✦ <b style="color:#EA580C;">l'aigle</b><br>
            ✦ <b style="color:#EA580C;">l'hirondelle</b> &nbsp;&nbsp;|&nbsp;&nbsp; ✦ <b style="color:#EA580C;">la chauve-souris</b> (mammifère volant)<br>
            ✦ <b style="color:#EA580C;">le perroquet</b> &nbsp;&nbsp;|&nbsp;&nbsp; ✦ <b style="color:#EA580C;">le canard sauvage</b>
        </div>

        <p style="font-size:16px; font-weight:800; color:#15803D; margin-top:14px; margin-bottom:8px;">🦋 2. Les insectes volants :</p>
        <div style="background:#F0FDF4; border:2px dashed #16A34A; border-radius:12px; padding:12px; font-size:14px; font-weight:bold; color:#166534; line-height:2.2;">
            ✦ <b>le papillon</b> &nbsp;—&nbsp; ✦ <b>l'abeille</b> &nbsp;—&nbsp; ✦ <b>la mouche</b><br>
            ✦ <b>la libellule</b> &nbsp;—&nbsp; ✦ <b>la coccinelle</b> &nbsp;—&nbsp; ✦ <b>le moustique</b> &nbsp;—&nbsp; ✦ <b>la sauterelle</b>
        </div>

        <div style="background:#FFF1F2; border:2px dashed #E11D48; border-radius:12px; padding:10px; margin-top:14px; font-size:13px; font-weight:bold; color:#9F1239;">
            ⚠️ <b>Attention :</b> Le crabe et l'anguille ne volent pas, ils se déplacent dans l'eau ou sur le sable !
        </div>

        <div style="text-align:center;">
            <a href="/lecons-de-chose" class="btn-retour">← Revenir aux Leçons de chose</a>
        </div>
    """
    return afficher(html)

@app.route("/lecons-de-chose/marchent")
def page_chose_marchent():
    html = """
        <div style="text-align:center;">
            <span class="badge-date" style="background:#0284C7;">📅 Mercredi 01 Octobre 2026</span>
            <div class="titre-lecon" style="color:#D90429;">LES ANIMAUX QUI MARCHENT</div>
        </div>

        <div style="background:#F3E8FF; border-left:5px solid #9333EA; border-radius:10px; padding:12px; font-size:14px; line-height:2; color:#6B21A8; margin-bottom:14px;">
            ✦ <b>Définition :</b> Les animaux qui marchent sont des animaux terrestres qui se déplacent sur la terre ferme à l'aide de leurs <b>pattes</b> (2 pattes ou 4 pattes).
        </div>

        <p style="font-size:16px; font-weight:800; color:#7E22CE; margin-bottom:8px;">🐾 Les animaux qui marchent :</p>
        <div style="background:#FFFFFF; border:3px solid #80DEEA; border-radius:14px; padding:14px; font-size:14px; font-weight:bold; color:#0F172A; line-height:2.4;">
            ✦ <b style="color:#7C3AED;">le chat</b> &nbsp;&nbsp;|&nbsp;&nbsp; ✦ <b style="color:#7C3AED;">le chien</b> &nbsp;&nbsp;|&nbsp;&nbsp; ✦ <b style="color:#7C3AED;">la chèvre</b><br>
            ✦ <b style="color:#7C3AED;">le lion</b> &nbsp;&nbsp;|&nbsp;&nbsp; ✦ <b style="color:#7C3AED;">le tigre</b> &nbsp;&nbsp;|&nbsp;&nbsp; ✦ <b style="color:#7C3AED;">le léopard</b><br>
            ✦ <b style="color:#7C3AED;">le cheval</b> &nbsp;&nbsp;|&nbsp;&nbsp; ✦ <b style="color:#7C3AED;">le dromadaire</b> &nbsp;&nbsp;|&nbsp;&nbsp; ✦ <b style="color:#7C3AED;">le zèbre</b><br>
            ✦ <b style="color:#7C3AED;">l'éléphant</b> &nbsp;&nbsp;|&nbsp;&nbsp; ✦ <b style="color:#7C3AED;">la girafe</b> &nbsp;&nbsp;|&nbsp;&nbsp; ✦ <b style="color:#7C3AED;">le cerf</b><br>
            ✦ <b style="color:#7C3AED;">la gazelle</b> &nbsp;&nbsp;|&nbsp;&nbsp; ✦ <b style="color:#7C3AED;">l'hippopotame</b> &nbsp;&nbsp;|&nbsp;&nbsp; ✦ <b style="color:#7C3AED;">le rhinocéros</b><br>
            ✦ <b style="color:#7C3AED;">le renard</b> &nbsp;&nbsp;|&nbsp;&nbsp; ✦ <b style="color:#7C3AED;">le canard</b> &nbsp;&nbsp;|&nbsp;&nbsp; ✦ <b style="color:#7C3AED;">l'autruche</b> &nbsp;&nbsp;|&nbsp;&nbsp; ✦ <b style="color:#7C3AED;">le dindon</b>
        </div>

        <div style="background:#F0FDF4; border:2px dashed #16A34A; border-radius:12px; padding:12px; margin-top:14px; font-size:14px; font-weight:bold; color:#15803D; line-height:2;">
            💡 <b>Distinction utile :</b><br>
            • <b>Quadrupèdes</b> : animaux à 4 pattes (le lion, le chat, le cheval, l'éléphant...)<br>
            • <b>Bipèdes</b> : animaux à 2 pattes (l'autruche, le canard, la poule, le dindon...)
        </div>

        <div style="text-align:center;">
            <a href="/lecons-de-chose" class="btn-retour">← Revenir aux Leçons de chose</a>
        </div>
    """
    return afficher(html)

@app.route("/lecons-de-chose/rampent")
def page_chose_rampent():
    html = """
        <div style="text-align:center;">
            <span class="badge-date" style="background:#0284C7;">📅 Mercredi 10 Octobre 2026</span>
            <div class="titre-lecon" style="color:#D90429;">LES ANIMAUX QUI RAMPENT</div>
        </div>

        <div style="background:#ECFDF5; border-left:5px solid #059669; border-radius:10px; padding:12px; font-size:14px; line-height:2; color:#065F46; margin-bottom:14px;">
            ✦ <b>Définition :</b> Les animaux qui rampent sont des animaux qui n'ont pas de pattes ou qui ont de très petites pattes, et qui utilisent leur <b>ventre</b> pour avancer et se déplacer (la reptation).
        </div>

        <p style="font-size:16px; font-weight:800; color:#047857; margin-bottom:8px;">🐍 Les animaux qui rampent :</p>
        <div style="background:#FFFFFF; border:3px solid #80DEEA; border-radius:14px; padding:14px; font-size:15px; font-weight:bold; color:#0F172A; line-height:2.4;">
            ✦ <b style="color:#059669;">le serpent</b> &nbsp;&nbsp;|&nbsp;&nbsp; ✦ <b style="color:#059669;">le ver de terre</b><br>
            ✦ <b style="color:#059669;">l'escargot</b> &nbsp;&nbsp;|&nbsp;&nbsp; ✦ <b style="color:#059669;">la chenille</b><br>
            ✦ <b style="color:#059669;">le lézard</b> &nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp; ✦ <b style="color:#059669;">la tortue</b><br>
            ✦ <b style="color:#059669;">le scorpion</b> &nbsp;&nbsp;|&nbsp;&nbsp; ✦ <b style="color:#059669;">le crocodile</b> (au sol)<br>
            ✦ <b style="color:#059669;">la limace</b>
        </div>

        <div style="background:#FFFBEB; border:2px dashed #D97706; border-radius:12px; padding:12px; margin-top:14px; font-size:14px; font-weight:bold; color:#B45309; line-height:2;">
            💡 <b>Mots à retenir :</b><br>
            • <i>ramper</i> : se déplacer en traînant son corps sur le sol.<br>
            • Le serpent et le ver de terre n'ont pas de pattes ; la chenille et le lézard ont de petites pattes et rasent le sol.
        </div>

        <div style="text-align:center;">
            <a href="/lecons-de-chose" class="btn-retour">← Revenir aux Leçons de chose</a>
        </div>
    """
    return afficher(html)

# =============================================================================
# MENUS FRANÇAIS (LEÇONS & EXERCICES) AVEC BOUTON CHOOSE
# =============================================================================
@app.route("/francais/lecons")
def page_francais_lecons():
    html = """
        <div class="cadre-menu">
            <h1 class="titre-principal" id="titre-fr-lecons">
                Français — Leçons<br>
                <span class="sous-titre-selection" id="sous-titre-fr-lecons">Choisissez une matière</span>
            </h1>

            <button type="button" class="btn-rose btn-option" data-url="/francais/lecons/orthographe" data-titre="Orthographe">Orthographe</button>
            <button type="button" class="btn-rose btn-option" data-url="/francais/lecons/conjugaison" data-titre="Conjugaison">Conjugaison</button>
            <button type="button" class="btn-rose btn-option" data-url="/francais/lecons/grammaire" data-titre="Grammaire">Grammaire</button>
            <button type="button" class="btn-rose btn-option" data-url="/francais/lecons/vocabulaire" data-titre="Vocabulaire">Vocabulaire</button>

            <button type="button" id="btn-valider" class="btn-choose">➜ Choose</button>
            <a href="/programme?matiere=Francais" class="btn-retour">← Revenir</a>
        </div>

        <script>
            let urlChoisie = "/francais/lecons/orthographe";
            const boutons = document.querySelectorAll('.btn-option');
            const sousTitre = document.getElementById('sous-titre-fr-lecons');
            const btnValider = document.getElementById('btn-valider');

            boutons[0].classList.add('selected');
            sousTitre.textContent = boutons[0].getAttribute('data-titre');

            boutons.forEach(b => {
                b.addEventListener('click', () => {
                    boutons.forEach(x => x.classList.remove('selected'));
                    b.classList.add('selected');
                    urlChoisie = b.getAttribute('data-url');
                    sousTitre.textContent = b.getAttribute('data-titre');
                });
            });

            btnValider.addEventListener('click', () => {
                window.location.href = urlChoisie;
            });
        </script>
    """
    return afficher(html)

@app.route("/francais/exercices")
def page_francais_exercices():
    html = """
        <div class="cadre-menu">
            <h1 class="titre-principal" id="titre-fr-exercices">
                Français — Exercices<br>
                <span class="sous-titre-selection" id="sous-titre-fr-exercices">Choisissez une option</span>
            </h1>

            <button type="button" class="btn-rose btn-option" data-url="/francais/exercices/orthographe" data-titre="Orthographe">Orthographe</button>
            <button type="button" class="btn-rose btn-option" data-url="/francais/exercices/conjugaison" data-titre="Conjugaison">Conjugaison</button>
            <button type="button" class="btn-rose btn-option" data-url="/francais/exercices/grammaire" data-titre="Grammaire">Grammaire</button>
            <button type="button" class="btn-rose btn-option" data-url="/francais/exercices/dictee" data-titre="Dictée préparée">Dictée préparée</button>

            <button type="button" id="btn-valider" class="btn-choose">➜ Choose</button>
            <a href="/programme?matiere=Francais" class="btn-retour">← Revenir</a>
        </div>

        <script>
            let urlChoisie = "/francais/exercices/orthographe";
            const boutons = document.querySelectorAll('.btn-option');
            const sousTitre = document.getElementById('sous-titre-fr-exercices');
            const btnValider = document.getElementById('btn-valider');

            boutons[0].classList.add('selected');
            sousTitre.textContent = boutons[0].getAttribute('data-titre');

            boutons.forEach(b => {
                b.addEventListener('click', () => {
                    boutons.forEach(x => x.classList.remove('selected'));
                    b.classList.add('selected');
                    urlChoisie = b.getAttribute('data-url');
                    sousTitre.textContent = b.getAttribute('data-titre');
                });
            });

            btnValider.addEventListener('click', () => {
                window.location.href = urlChoisie;
            });
        </script>
    """
    return afficher(html)

# =============================================================================
# SOUS-MENUS LEÇONS FRANÇAIS (ORTHOGRAPHE, CONJUGAISON, GRAMMAIRE, VOCABULAIRE)
# =============================================================================
@app.route("/francais/lecons/orthographe")
def page_lecons_orthographe():
    html = """
        <div class="cadre-menu">
            <h1 class="titre-principal" id="titre-ortho">
                Leçons d'Orthographe<br>
                <span class="sous-titre-selection" id="sous-titre-ortho">Choisissez une leçon</span>
            </h1>

            <button type="button" class="btn-rose btn-option" data-url="/francais/lecons/orthographe/son-i" data-titre='Le son "i".'>Le son "i".</button>
            <button type="button" class="btn-rose btn-option" data-url="/francais/lecons/orthographe/son-e" data-titre='Le son "e".'>Le son "e".</button>
            <button type="button" class="btn-rose btn-option" data-url="/francais/lecons/orthographe/son-ar" data-titre="Le son ar">Le son ar</button>

            <button type="button" id="btn-valider" class="btn-choose">➜ Choose</button>
            <a href="/francais/lecons" class="btn-retour">← Revenir aux leçons de Français</a>
        </div>

        <script>
            let urlChoisie = "/francais/lecons/orthographe/son-i";
            const boutons = document.querySelectorAll('.btn-option');
            const sousTitre = document.getElementById('sous-titre-ortho');
            const btnValider = document.getElementById('btn-valider');

            boutons[0].classList.add('selected');
            sousTitre.textContent = boutons[0].getAttribute('data-titre');

            boutons.forEach(b => {
                b.addEventListener('click', () => {
                    boutons.forEach(x => x.classList.remove('selected'));
                    b.classList.add('selected');
                    urlChoisie = b.getAttribute('data-url');
                    sousTitre.textContent = b.getAttribute('data-titre');
                });
            });

            btnValider.addEventListener('click', () => {
                window.location.href = urlChoisie;
            });
        </script>
    """
    return afficher(html)

@app.route("/francais/lecons/orthographe/son-i")
def page_lecon_ortho_son_i():
    html = """
        <div style="text-align:center;">
            <span class="badge-date">📅 Jeudi 17 Septembre 2026</span>
            <div class="titre-lecon">📖 Orthographe : Le son « i »</div>
        </div>
        <div class="cadre-contenu">
            ✦ <b>i :</b> une amie &nbsp;—&nbsp; une épicerie &nbsp;—&nbsp; la pluie &nbsp;—&nbsp; la chemise<br>
            ✦ <b>y :</b> <b style="color:#0D47A1;">Lyon</b> &nbsp;—&nbsp; le <b style="color:#0D47A1;">paddy</b> &nbsp;—&nbsp; la <b style="color:#0D47A1;">pyramide</b> &nbsp;—&nbsp; le <b style="color:#0D47A1;">pyjama</b><br>
            ✦ <b>it :</b> le <b style="color:#D81B60;">lit</b> &nbsp;—&nbsp; un hab<b style="color:#D81B60;">it</b> &nbsp;—&nbsp; la nu<b style="color:#D81B60;">it</b> &nbsp;—&nbsp; le fru<b style="color:#D81B60;">it</b><br>
            ✦ <b>ie :</b> la v<b style="color:#1B5E20;">ie</b> &nbsp;—&nbsp; Mar<b style="color:#1B5E20;">ie</b> &nbsp;—&nbsp; le paraplu<b style="color:#1B5E20;">ie</b><br>
            ✦ <b>î :</b> une <b style="color:#E65100;">île</b> &nbsp;—&nbsp; une ab<b style="color:#E65100;">î</b>me<br>
            ✦ <b>is :</b> la sour<b style="color:#6A1B9A;">is</b> &nbsp;—&nbsp; Par<b style="color:#6A1B9A;">is</b> &nbsp;—&nbsp; un tap<b style="color:#6A1B9A;">is</b><br>
            ✦ <b>id :</b> le n<b style="color:#00838F;">id</b> &nbsp;&nbsp;|&nbsp;&nbsp; ✦ <b>iz :</b> le r<b style="color:#00838F;">iz</b><br>
            ✦ <b>h (muet) :</b> un <b style="color:#C2185B;">hibou</b> &nbsp;—&nbsp; l'<b style="color:#C2185B;">hirondelle</b>
        </div>
        <div style="background:#E1F5FE; border-radius:12px; padding:10px; font-size:14px; color:#0D47A1; font-weight:bold;">
            💡 <b>Règle :</b> Le son « i » peut s'écrire simplement <i>i</i> ou <i>y</i>, mais aussi avec des lettres muettes finales comme <i>it, is, id, iz, ie</i> !
        </div>
        <div style="text-align:center;">
            <a href="/francais/lecons/orthographe" class="btn-retour">← Revenir aux Leçons d'Orthographe</a>
        </div>
    """
    return afficher(html)

@app.route("/francais/lecons/orthographe/son-e")
def page_lecon_ortho_son_e():
    html = """
        <div style="text-align:center;">
            <span class="badge-date">📅 Lundi 12 Octobre 2026</span>
            <div class="titre-lecon">📖 Orthographe : Le son « e »</div>
        </div>
        <div class="cadre-contenu">
            ✦ <b>e :</b> l<b style="color:#0D47A1;">e</b> m<b style="color:#0D47A1;">e</b>nu &nbsp;—&nbsp; la capitain<b style="color:#0D47A1;">e</b> &nbsp;—&nbsp; p<b style="color:#0D47A1;">e</b>tit<b style="color:#0D47A1;">e</b> prom<b style="color:#0D47A1;">e</b>nad<b style="color:#0D47A1;">e</b><br>
            ✦ <b>eu :</b> le j<b style="color:#D81B60;">eu</b> &nbsp;—&nbsp; nev<b style="color:#D81B60;">eu</b> &nbsp;—&nbsp; av<b style="color:#D81B60;">eu</b>gle &nbsp;—&nbsp; fl<b style="color:#D81B60;">eu</b>ve &nbsp;—&nbsp; je pl<b style="color:#D81B60;">eu</b>re<br>
            ✦ <b>oeu :</b> un <b style="color:#1B5E20;">oeu</b>f &nbsp;—&nbsp; un b<b style="color:#1B5E20;">oeu</b>f &nbsp;—&nbsp; le n<b style="color:#1B5E20;">oeu</b>d &nbsp;—&nbsp; une s<b style="color:#1B5E20;">oeu</b>r &nbsp;—&nbsp; un c<b style="color:#1B5E20;">oeu</b>r<br>
            ✦ <b>oei :</b> un <b style="color:#E65100;">oei</b>l
        </div>
        <div style="background:#FFF9C4; border-radius:12px; padding:10px; font-size:14px; color:#E65100; font-weight:bold;">
            🔍 <b>Remarque :</b> Les graphies <i>eu</i> et <i>oeu</i> se prononcent de façon semblable comme dans le jeu, la soeur et le noeud !
        </div>
        <div style="text-align:center;">
            <a href="/francais/lecons/orthographe" class="btn-retour">← Revenir aux Leçons d'Orthographe</a>
        </div>
    """
    return afficher(html)

@app.route("/francais/lecons/orthographe/son-ar")
def page_lecon_ortho_son_ar():
    html = """
        <div style="text-align:center;">
            <span class="badge-date">📅 Mardi 27 Octobre 2026</span>
            <div class="titre-lecon">📖 Le son « ar »</div>
        </div>
        <div class="cadre-contenu">
            ✦ <b style="color:#D90429; font-size:17px;">ar :</b> &nbsp;&nbsp;la <b style="color:#0D47A1;">carte</b> &nbsp;—&nbsp; un <b style="color:#0D47A1;">armoire</b><br><br>
            ✦ ✦ <b style="color:#16A34A; font-size:17px;">are :</b> &nbsp;&nbsp;la <b style="color:#047857;">mare</b> &nbsp;—&nbsp; un <b style="color:#047857;">arc</b> &nbsp;—&nbsp; la <b style="color:#047857;">tare</b>.
        </div>
        <div style="background:#F0FDF4; border:2px dashed #16A34A; border-radius:12px; padding:12px; font-size:14px; color:#15803D; font-weight:bold;">
            💡 <b>Mots à retenir :</b><br>
            • <i>la carte</i> &nbsp;|&nbsp; • <i>une armoire</i><br>
            • <i>la mare</i> &nbsp;|&nbsp; • <i>un arc</i> &nbsp;|&nbsp; • <i>la tare</i>
        </div>
        <div style="text-align:center;">
            <a href="/francais/lecons/orthographe" class="btn-retour">← Revenir aux Leçons d'Orthographe</a>
        </div>
    """
    return afficher(html)

@app.route("/francais/lecons/conjugaison")
def page_lecons_conjugaison():
    html = """
        <div class="cadre-menu">
            <h1 class="titre-principal" id="titre-conj">
                Leçons de Conjugaison<br>
                <span class="sous-titre-selection" id="sous-titre-conj">Choisissez une leçon</span>
            </h1>

            <button type="button" class="btn-rose btn-option" data-url="/francais/lecons/conjugaison/singulier" data-titre="Les pronoms personnels sujets au singuliers">Les pronoms personnels sujets au singuliers</button>
            <button type="button" class="btn-rose btn-option" data-url="/francais/lecons/conjugaison/pluriel" data-titre="Les PPS aux pluriels">Les PPS aux pluriels</button>

            <button type="button" id="btn-valider" class="btn-choose">➜ Choose</button>
            <a href="/francais/lecons" class="btn-retour">← Revenir aux leçons de Français</a>
        </div>

        <script>
            let urlChoisie = "/francais/lecons/conjugaison/singulier";
            const boutons = document.querySelectorAll('.btn-option');
            const sousTitre = document.getElementById('sous-titre-conj');
            const btnValider = document.getElementById('btn-valider');

            boutons[0].classList.add('selected');
            sousTitre.textContent = boutons[0].getAttribute('data-titre');

            boutons.forEach(b => {
                b.addEventListener('click', () => {
                    boutons.forEach(x => x.classList.remove('selected'));
                    b.classList.add('selected');
                    urlChoisie = b.getAttribute('data-url');
                    sousTitre.textContent = b.getAttribute('data-titre');
                });
            });

            btnValider.addEventListener('click', () => {
                window.location.href = urlChoisie;
            });
        </script>
    """
    return afficher(html)

@app.route("/francais/lecons/conjugaison/singulier")
def page_lecon_conj_singulier():
    html = """
        <div style="text-align:center;">
            <span class="badge-date">📅 Lundi 21 Septembre 2026</span>
            <div class="titre-lecon">📖 Les Pronoms Personnels Sujets au Singulier</div>
        </div>
        <div class="cadre-contenu">
            ✦ <b style="color:#0D47A1;">Je</b> dessine une fleur.<br>
            ✦ <b style="color:#0D47A1;">Tu</b> marches doucement.<br>
            <div style="background:#E8F5E9; border-left:4px solid #2E7D32; padding:6px 10px; margin:8px 0; font-size:14px;">
                ➔ <b>Je</b> et <b>Tu</b> sont des pronoms personnels sujets toujours employés pour <u>une seule personne</u>.
            </div>
            ✦ Allah est gentil. ➔ <b style="color:#D81B60;">Il</b> est gentil.<br>
            ✦ Le coq chante. ➔ <b style="color:#D81B60;">Il</b> chante.<br>
            ✦ Fatou prend le livre. ➔ <b style="color:#D81B60;">Elle</b> prend le livre.<br>
            <div style="background:#FFF3E0; border-left:4px solid #E65100; padding:6px 10px; margin:8px 0; font-size:14px;">
                ➔ On emploie <b>Il</b> ou <b>Elle</b> quand on parle d'une autre personne, d'un animal ou d'une chose.
            </div>
        </div>
        <table border="1" cellpadding="8" style="width:100%; border-collapse:collapse; text-align:center; background:#fff; font-size:14px; border-color:#80DEEA;">
            <tr style="background:#B3E5FC; font-weight:bold; color:#0D47A1;"><td>Pronom</td><td>Personne</td></tr>
            <tr><td><b>Je</b></td><td>1ère personne du singulier</td></tr>
            <tr><td><b>Tu</b></td><td>2ème personne du singulier</td></tr>
            <tr><td><b>Il / Elle</b></td><td>3ème personne du singulier</td></tr>
        </table>
        <div style="text-align:center;">
            <a href="/francais/lecons/conjugaison" class="btn-retour">← Revenir aux Leçons de Conjugaison</a>
        </div>
    """
    return afficher(html)

@app.route("/francais/lecons/conjugaison/pluriel")
def page_lecon_conj_pluriel():
    html = """
        <div style="text-align:center;">
            <span class="badge-date">📅 Mercredi 14 Octobre 2026</span>
            <div class="titre-lecon">📖 Les Pronoms Personnels Sujets aux Pluriels</div>
        </div>
        <div class="cadre-contenu">
            Les pronoms personnels sujets au pluriel sont :<br>
            ✦ <b style="color:#0D47A1;">Nous</b> (1ère personne du pluriel)<br>
            ✦ <b style="color:#0D47A1;">Vous</b> (2ème personne du pluriel)<br>
            ✦ <b style="color:#D81B60;">Ils</b> (3ème personne du pluriel masculin)<br>
            ✦ <b style="color:#D81B60;">Elles</b> (3ème personne du pluriel féminin)
        </div>
        <div style="background:#E8F5E9; border-radius:12px; padding:12px; font-size:14px; color:#1B5E20; font-weight:bold; line-height:2;">
            ✦ On emploie <b style="color:#D81B60;">Ils</b> quand il s'agit de 2 ou plusieurs garçons, personnes masculines ou animaux.<br>
            <i>Exemple :</i> Luc et Paul vont à l'école. ➔ <b style="color:#0D47A1;">Ils</b> vont à l'école.<br><br>
            ✦ On emploie <b style="color:#D81B60;">Elles</b> quand il s'agit de 2 ou plusieurs filles, personnes féminines ou animaux.<br>
            <i>Exemple :</i> Amina et Marie jouent. ➔ <b style="color:#0D47A1;">Elles</b> jouent.
        </div>
        <div style="text-align:center;">
            <a href="/francais/lecons/conjugaison" class="btn-retour">← Revenir aux Leçons de Conjugaison</a>
        </div>
    """
    return afficher(html)

@app.route("/francais/lecons/grammaire")
def page_lecons_grammaire():
    html = """
        <div class="cadre-menu">
            <h1 class="titre-principal" id="titre-gramm">
                Leçons de Grammaire<br>
                <span class="sous-titre-selection" id="sous-titre-gramm">Choisissez une leçon</span>
            </h1>

            <button type="button" class="btn-rose btn-option" data-url="/francais/lecons/grammaire/26-lettres" data-titre="Les 26 lettres de l'alphabet francais">Les 26 lettres de l'alphabet francais</button>
            <button type="button" class="btn-rose btn-option" data-url="/francais/lecons/grammaire/syllabes" data-titre="Les syllabes">Les syllabes</button>
            <button type="button" class="btn-rose btn-option" data-url="/francais/lecons/grammaire/noms" data-titre="les noms">les noms</button>

            <button type="button" id="btn-valider" class="btn-choose">➜ Choose</button>
            <a href="/francais/lecons" class="btn-retour">← Revenir aux leçons de Français</a>
        </div>

        <script>
            let urlChoisie = "/francais/lecons/grammaire/26-lettres";
            const boutons = document.querySelectorAll('.btn-option');
            const sousTitre = document.getElementById('sous-titre-gramm');
            const btnValider = document.getElementById('btn-valider');

            boutons[0].classList.add('selected');
            sousTitre.textContent = boutons[0].getAttribute('data-titre');

            boutons.forEach(b => {
                b.addEventListener('click', () => {
                    boutons.forEach(x => x.classList.remove('selected'));
                    b.classList.add('selected');
                    urlChoisie = b.getAttribute('data-url');
                    sousTitre.textContent = b.getAttribute('data-titre');
                });
            });

            btnValider.addEventListener('click', () => {
                window.location.href = urlChoisie;
            });
        </script>
    """
    return afficher(html)

@app.route("/francais/lecons/grammaire/26-lettres")
def page_lecon_gramm_26_lettres():
    html = """
        <div style="text-align:center;">
            <span class="badge-date">📅 Lundi 21 Septembre 2026</span>
            <div class="titre-lecon">📖 Les 26 Lettres de l'Alphabet Français</div>
        </div>
        <div class="cadre-contenu" style="text-align:center; font-size:16px;">
            <b style="color:#0D47A1; letter-spacing:1px;">a - b - c - d - e - f - g - h - i - j - k - l - m<br>
            n - o - p - q - r - s - t - u - v - w - x - y - z</b>
        </div>
        <div style="background:#E1F5FE; border-radius:12px; padding:12px; font-size:14px; line-height:2;">
            ✦ Dans l'alphabet français, il y a exactement <b style="color:#D81B60;">26 lettres</b>.<br>
            ✦ Il y a <b style="color:#1B5E20;">6 voyelles :</b> <b>a - e - i - o - u - y</b>.<br>
            ✦ Il y a <b style="color:#0D47A1;">20 consonnes :</b> <b>b - c - d - f - g - h - j - k - l - m - n - p - q - r - s - t - v - w - x - z</b>.
        </div>
        <div style="text-align:center;">
            <a href="/francais/lecons/grammaire" class="btn-retour">← Revenir aux Leçons de Grammaire</a>
        </div>
    """
    return afficher(html)

@app.route("/francais/lecons/grammaire/syllabes")
def page_lecon_gramm_syllabes():
    html = """
        <div style="text-align:center;">
            <span class="badge-date">📅 Mercredi 07 Octobre 2026</span>
            <div class="titre-lecon">📖 Les Syllabes</div>
        </div>
        <div class="cadre-contenu">
            ✦ Une <b>syllabe</b> est une partie de mot que l'on prononce d'un seul coup de voix, contient une voyelle prononcée.<br>
            ✦ En frappant dans les mains, on peut compter et séparer les syllabes d'un mot.
        </div>
        <p style="font-weight:bold; color:#1B5E20; margin-bottom:8px;">Exemples de séparation et de comptage :</p>
        <div style="background:#FFF9C4; border-radius:12px; padding:12px; font-size:15px; line-height:2.2; font-weight:bold; color:#3E2723;">
            • pa - pa = <b>2 syllabes</b><br>
            • mou - le = <b>2 syllabes</b><br>
            • vil - la - ge = <b>3 syllabes</b><br>
            • ma - la - de = <b>3 syllabes</b><br>
            • pro - me - na - de = <b>4 syllabes</b><br>
            • py - ra - mi - de = <b>4 syllabes</b><br>
            • lo - co - mo - ti - ve = <b>5 syllabes</b>
        </div>
        <div style="text-align:center;">
            <a href="/francais/lecons/grammaire" class="btn-retour">← Revenir aux Leçons de Grammaire</a>
        </div>
    """
    return afficher(html)

@app.route("/francais/lecons/grammaire/noms")
def page_lecon_gramm_noms():
    html = """
        <h1 class="titre-principal">📖 Grammaire : Les Noms</h1>
        <p style="font-size:15px; font-weight:bold; color:#0D47A1; margin-bottom:6px;">1) Qu'est-ce qu'un nom ?</p>
        <div class="cadre-contenu">
            Le nom est un mot qui sert à nommer une <b>personne</b>, un <b>animal</b> ou une <b>chose</b>.
        </div>
        <div style="background:#E8F5E9; border-radius:12px; padding:12px; font-size:14px; line-height:2.2;">
            ✦ <b style="color:#0D47A1;">Noms de personnes :</b> Marius, Claudette, le maître, maman, Jean, le bébé.<br>
            ✦ <b style="color:#2E7D32;">Noms d'animaux :</b> le chat, la crevette, le boeuf, le papillon, le mouton.<br>
            ✦ <b style="color:#D81B60;">Noms de choses :</b> le stylo, la gourde, le tableau, la table, la trousse.
        </div>

        <div style="margin-top:16px; background:#FEF2F2; border:3px solid #EF4444; border-radius:14px; padding:14px;">
            <div style="text-align:center; margin-bottom:10px;">
                <span style="background:#DC2626; color:#ffffff; font-size:13px; font-weight:bold; padding:4px 12px; border-radius:10px;">
                    📅 Mardi 27 Octobre 2026 — Suite les noms
                </span>
            </div>
            <p style="font-size:15px; font-weight:bold; color:#991B1B; margin-bottom:6px;">✨ Les noms propres :</p>
            <div style="background:#ffffff; border-radius:10px; padding:12px; font-size:14px; line-height:2.2; color:#1F2937;">
                ✦ <b>Un nom propre</b> commence toujours par une <b>lettre majuscule</b>.<br>
                ✦ Il appartient à :
                <ul style="margin:6px 0; padding-left:22px;">
                    <li><b>une seule personne</b> (ex : <i>Marius, Claudette</i>),</li>
                    <li><b>une seule chose</b>,</li>
                    <li><b>un quartier</b> (ex : <i>Mandroseza</i>),</li>
                    <li><b>un pays</b> (ex : <i>Madagascar, France</i>).</li>
                </ul>
            </div>
        </div>
        <div style="text-align:center;">
            <a href="/francais/lecons/grammaire" class="btn-retour">← Revenir aux Leçons de Grammaire</a>
        </div>
    """
    return afficher(html)

@app.route("/francais/lecons/vocabulaire")
def page_lecons_vocabulaire():
    html = """
        <div class="cadre-menu">
            <h1 class="titre-principal" id="titre-vocab">
                Leçons de Vocabulaire<br>
                <span class="sous-titre-selection" id="sous-titre-vocab">Choisissez une leçon</span>
            </h1>

            <button type="button" class="btn-rose btn-option" data-url="/francais/lecons/vocabulaire/corps" data-titre="La propreté du corps">La propreté du corps</button>
            <button type="button" class="btn-rose btn-option" data-url="/francais/lecons/vocabulaire/environnement" data-titre="La propreté de l'environnement">La propreté de l'environnement</button>
            <button type="button" class="btn-rose btn-option" data-url="/francais/lecons/vocabulaire/ecole" data-titre="L'école">L'école</button>

            <button type="button" id="btn-valider" class="btn-choose">➜ Choose</button>
            <a href="/francais/lecons" class="btn-retour">← Revenir aux leçons de Français</a>
        </div>

        <script>
            let urlChoisie = "/francais/lecons/vocabulaire/corps";
            const boutons = document.querySelectorAll('.btn-option');
            const sousTitre = document.getElementById('sous-titre-vocab');
            const btnValider = document.getElementById('btn-valider');

            boutons[0].classList.add('selected');
            sousTitre.textContent = boutons[0].getAttribute('data-titre');

            boutons.forEach(b => {
                b.addEventListener('click', () => {
                    boutons.forEach(x => x.classList.remove('selected'));
                    b.classList.add('selected');
                    urlChoisie = b.getAttribute('data-url');
                    sousTitre.textContent = b.getAttribute('data-titre');
                });
            });

            btnValider.addEventListener('click', () => {
                window.location.href = urlChoisie;
            });
        </script>
    """
    return afficher(html)

@app.route("/francais/lecons/vocabulaire/corps")
def page_lecon_vocab_corps():
    html = """
        <div style="text-align:center;">
            <span class="badge-date">📅 Jeudi 01 Octobre 2026</span>
            <div class="titre-lecon">📖 Vocabulaire : La propreté du corps</div>
        </div>
        <div class="cadre-contenu">
            Pour être propre et en bonne santé :<br>
            ✦ On doit se <b>brosser les dents</b> après chaque repas.<br>
            ✦ On doit se <b>laver le visage</b> et les yeux chaque matin.<br>
            ✦ Pour entretenir le corps : couper ses <b>ongles</b>, laver les <b>pieds</b> et protéger la <b>peau</b>.
        </div>
        <p style="font-weight:bold; color:#0D47A1; margin-bottom:8px;">🚿 Comment prendre une douche ?</p>
        <div style="background:#E1F5FE; border-radius:12px; padding:12px; font-size:14px; line-height:2.1; color:#01579B;">
            1. On a besoin de <b>l'eau</b> et du <b>savon</b>.<br>
            2. On verse de l'eau sur le corps.<br>
            3. On savonne bien le corps.<br>
            4. On frotte bien le corps pour enlever toute la saleté.<br>
            5. On se lave les mains et on s'essuie avec une serviette propre.
        </div>
        <div style="text-align:center;">
            <a href="/francais/lecons/vocabulaire" class="btn-retour">← Revenir aux Leçons de Vocabulaire</a>
        </div>
    """
    return afficher(html)

@app.route("/francais/lecons/vocabulaire/environnement")
def page_lecon_vocab_environnement():
    html = """
        <div style="text-align:center;">
            <span class="badge-date">📅 Mardi 06 Octobre 2026</span>
            <div class="titre-lecon">📖 Vocabulaire : La propreté de l'environnement</div>
        </div>
        <div class="cadre-contenu">
            ✦ On <b>ne jette pas par terre</b> les ordures comme les bouts de papiers, les bouts de craie, les sachets.<br>
            ✦ <b>Il est interdit</b> de salir l'environnement.<br>
            ✦ Avant de prendre un sachet ou une boîte, on doit toujours se laver les mains.<br>
            ✦ L'élève est <b>responsable</b> de la propreté de sa classe et de sa cour.<br>
            ✦ Il faut <b>donner le bon exemple</b> à ses camarades en déposant les déchets dans la poubelle.
        </div>
        <div style="text-align:center;">
            <a href="/francais/lecons/vocabulaire" class="btn-retour">← Revenir aux Leçons de Vocabulaire</a>
        </div>
    """
    return afficher(html)

@app.route("/francais/lecons/vocabulaire/ecole")
def page_lecon_vocab_ecole():
    html = """
        <div style="text-align:center;">
            <span class="badge-date">📅 Mardi 20 Octobre 2026</span>
            <div class="titre-lecon">📖 Vocabulaire : L'école</div>
        </div>

        <p style="font-weight:bold; color:#0D47A1; margin-bottom:6px;">🏫 À l'école, on trouve :</p>
        <div style="background:#ffffff; border:2px solid #80DEEA; border-radius:12px; padding:10px; font-size:14px; line-height:2;">
            ✦ <b>La directrice</b><br>
            ✦ <b>Les maîtresses</b><br>
            ✦ <b>Les écoliers</b>
        </div>

        <p style="font-weight:bold; color:#1B5E20; margin-top:12px; margin-bottom:6px;">🪑 Les effets scolaires dans la classe :</p>
        <div style="background:#E8F5E9; border-radius:12px; padding:10px; font-size:14px; line-height:2;">
            Le tableau &nbsp;—&nbsp; la règle &nbsp;—&nbsp; les tables-bancs &nbsp;—&nbsp; la craie.
        </div>

        <p style="font-weight:bold; color:#D81B60; margin-top:12px; margin-bottom:6px;">🎒 Les fournitures scolaires de l'écolier :</p>
        <div style="background:#FFF3E0; border-radius:12px; padding:10px; font-size:14px; line-height:2;">
            Les cahiers &nbsp;—&nbsp; les stylos &nbsp;—&nbsp; les livres &nbsp;—&nbsp; le crayon &nbsp;—&nbsp; la gomme &nbsp;—&nbsp; la trousse &nbsp;—&nbsp; le taille-crayon &nbsp;—&nbsp; les feutres &nbsp;—&nbsp; les crayons de couleur &nbsp;—&nbsp; la paire de ciseaux.
        </div>

        <div style="margin-top:16px; background:#EFF6FF; border:3px solid #3B82F6; border-radius:14px; padding:14px;">
            <div style="text-align:center; margin-bottom:8px;">
                <span style="background:#1D4ED8; color:#ffffff; font-size:13px; font-weight:bold; padding:4px 12px; border-radius:10px;">
                    📅 Mardi 27 Octobre 2026 — Suite à l'école
                </span>
            </div>
            <div style="background:#ffffff; border-radius:10px; padding:12px; font-size:14px; line-height:2.2; color:#1E3A8A; font-weight:bold;">
                ✦ Notre école s'appelle : <span style="color:#D90429;">Mon enfance</span>.<br>
                ✦ Elle est dirigée par : <span style="color:#D90429;">Madame Razafindrazaza Marcelline</span>.<br>
                ✦ C'est une école <b>privée</b>.<br>
                ✦ Elle se trouve à : <span style="color:#047857;">Mandroseza</span>.<br>
                ✦ Les classes qui existent sont :
                <ul style="margin:6px 0; padding-left:24px; color:#111827;">
                    <li><span style="color:#7C3AED;">préscolaire</span>.</li>
                    <li><span style="color:#7C3AED;">primaire</span>.</li>
                </ul>
            </div>
        </div>
        <div style="text-align:center;">
            <a href="/francais/lecons/vocabulaire" class="btn-retour">← Revenir aux Leçons de Vocabulaire</a>
        </div>
    """
    return afficher(html)

# =============================================================================
# EXERCICES DE FRANÇAIS (DICTÉES, ORTHOGRAPHE, CONJUGAISON, GRAMMAIRE)
# =============================================================================
@app.route("/francais/exercices/dictee")
def page_exercices_dictee():
    html = """
        <div class="cadre-menu">
            <h1 class="titre-principal" id="titre-ex-dictee">
                Dictée préparée<br>
                <span class="sous-titre-selection" id="sous-titre-ex-dictee">Choisissez une dictée</span>
            </h1>

            <button type="button" class="btn-rose btn-option" data-url="/francais/exercices/dictee/02-octobre" data-titre="1-Vendredi 02 Octobre (Je porte un pyjama bleu...)">1-Vendredi 02 Octobre (Je porte un pyjama bleu...)</button>
            <button type="button" class="btn-rose btn-option" data-url="/francais/exercices/dictee/09-octobre" data-titre="1-Vendredi 09 Octobre (Je plante un pin...)">1-Vendredi 09 Octobre (Je plante un pin...)</button>
            <button type="button" class="btn-rose btn-option" data-url="/francais/exercices/dictee/16-octobre" data-titre="1-Vendredi 16 Octobre (Il brosse seul les dents...)">1-Vendredi 16 Octobre (Il brosse seul les dents...)</button>
            <button type="button" class="btn-rose btn-option" data-url="/francais/exercices/dictee/22-octobre" data-titre="1-Jeudi 22 Octobre (La propreté est bon pour nous...)">1-Jeudi 22 Octobre (La propreté est bon pour nous...)</button>
            <button type="button" class="btn-rose btn-option" data-url="/francais/exercices/dictee/30-octobre" data-titre="1-Ils montrent la carte de l'étudiant.">1-Ils montrent la carte de l'étudiant.</button>

            <button type="button" id="btn-valider" class="btn-choose">➜ Choose</button>
            <a href="/francais/exercices" class="btn-retour">← Revenir aux exercices de Français</a>
        </div>

        <script>
            let urlChoisie = "/francais/exercices/dictee/02-octobre";
            const boutons = document.querySelectorAll('.btn-option');
            const sousTitre = document.getElementById('sous-titre-ex-dictee');
            const btnValider = document.getElementById('btn-valider');

            boutons[0].classList.add('selected');
            sousTitre.textContent = boutons[0].getAttribute('data-titre');

            boutons.forEach(b => {
                b.addEventListener('click', () => {
                    boutons.forEach(x => x.classList.remove('selected'));
                    b.classList.add('selected');
                    urlChoisie = b.getAttribute('data-url');
                    sousTitre.textContent = b.getAttribute('data-titre');
                });
            });

            btnValider.addEventListener('click', () => {
                window.location.href = urlChoisie;
            });
        </script>
    """
    return afficher(html)

@app.route("/francais/exercices/dictee/02-octobre")
def page_ex_dictee_02_oct():
    html = """
        <div style="text-align:center;">
            <span class="badge-date">📅 Vendredi 02 Octobre 2026</span>
            <div class="titre-lecon">✏️ Dictée préparée</div>
        </div>
        <div class="cadre-contenu" style="font-size:16px; line-height:2.4;">
            ✦ <b style="color:#0D47A1;">Je porte un pyjama bleu.</b><br>
            ✦ <b style="color:#0D47A1;">Tu mange le riz.</b><br>
            ✦ <b style="color:#0D47A1;">Marius coupe ses ongles vendredi.</b><br>
            ✦ <b style="color:#0D47A1;">Elle lave le visage de mon neveu.</b><br>
            ✦ <b style="color:#0D47A1;">Il est à Paris.</b>
        </div>
        <div style="text-align:center;">
            <a href="/francais/exercices/dictee" class="btn-retour">← Revenir aux Dictées préparées</a>
        </div>
    """
    return afficher(html)

@app.route("/francais/exercices/dictee/09-octobre")
def page_ex_dictee_09_oct():
    html = """
        <div style="text-align:center;">
            <span class="badge-date">📅 Vendredi 09 Octobre 2026</span>
            <div class="titre-lecon">✏️ Dictée préparée</div>
        </div>
        <div class="cadre-contenu" style="font-size:16px; line-height:2.4;">
            ✦ <b style="color:#0D47A1;">Je plante un pin.</b><br>
            ✦ <b style="color:#0D47A1;">Elle adore la propreté.</b><br>
            ✦ <b style="color:#0D47A1;">Tu porte un habit propre.</b><br>
            ✦ <b style="color:#0D47A1;">Maman regarde le prix du riz.</b><br>
            ✦ <b style="color:#0D47A1;">Il est sur l'île verte.</b>
        </div>
        <div style="text-align:center;">
            <a href="/francais/exercices/dictee" class="btn-retour">← Revenir aux Dictées préparées</a>
        </div>
    """
    return afficher(html)

@app.route("/francais/exercices/dictee/16-octobre")
def page_ex_dictee_16_oct():
    html = """
        <div style="text-align:center;">
            <span class="badge-date">📅 Vendredi 16 Octobre 2026</span>
            <div class="titre-lecon">✏️ Dictée préparée</div>
        </div>
        <div class="cadre-contenu" style="font-size:16px; line-height:2.4;">
            ✦ <b style="color:#0D47A1;">Il brosse seule les dents.</b><br>
            ✦ <b style="color:#0D47A1;">Nous gardons la salle propre.</b><br>
            ✦ <b style="color:#0D47A1;">Vous avez une jolie fleur dans le jardin.</b><br>
            ✦ <b style="color:#0D47A1;">Je suis dans la cour.</b><br>
            ✦ <b style="color:#0D47A1;">Élise adore Fanny.</b>
        </div>
        <div style="text-align:center;">
            <a href="/francais/exercices/dictee" class="btn-retour">← Revenir aux Dictées préparées</a>
        </div>
    """
    return afficher(html)

@app.route("/francais/exercices/dictee/22-octobre")
def page_ex_dictee_22_oct():
    html = """
        <div style="text-align:center;">
            <span class="badge-date">📅 Jeudi 22 Octobre 2026</span>
            <div class="titre-lecon">✏️ Dictée préparée</div>
        </div>
        <div class="cadre-contenu" style="font-size:16px; line-height:2.4;">
            ✦ <b style="color:#0D47A1;">La propreté est est bon pour nous.</b><br>
            ✦ <b style="color:#0D47A1;">Nous gardons la salle propre.</b><br>
            ✦ <b style="color:#0D47A1;">Médor te mordra.</b><br>
            ✦ <b style="color:#0D47A1;">Aline prépare le déjeuner.</b><br>
            ✦ <b style="color:#0D47A1;">Elles ont des jolis noeuds.</b>
        </div>
        <div style="text-align:center;">
            <a href="/francais/exercices/dictee" class="btn-retour">← Revenir aux Dictées préparées</a>
        </div>
    """
    return afficher(html)

@app.route("/francais/exercices/dictee/30-octobre")
def page_ex_dictee_30_oct():
    html = """
        <div style="text-align:center;">
            <span class="badge-date">📅 Vendredi 30 Octobre 2026</span>
            <div class="titre-lecon">✏️ Dictée préparée</div>
        </div>
        <div class="cadre-contenu" style="font-size:16px; line-height:2.4;">
            ✦ <b style="color:#0D47A1;">Ils montrent la carte de l'étudiant.</b><br>
            ✦ <b style="color:#0D47A1;">Une écolière surveille les élèves.</b><br>
            ✦ <b style="color:#0D47A1;">Nous cultivons un are de riz.</b><br>
            ✦ <b style="color:#0D47A1;">Le fleuve a débordé sur le jardin planté.</b><br>
            ✦ <b style="color:#0D47A1;">La clématite couvre la clôture du jardin.</b>
        </div>
        <div style="text-align:center;">
            <a href="/francais/exercices/dictee" class="btn-retour">← Revenir aux Dictées préparées</a>
        </div>
    """
    return afficher(html)

@app.route("/francais/exercices/orthographe")
def page_exercices_orthographe():
    html = """
        <div class="cadre-menu">
            <h1 class="titre-principal" id="titre-ex-ortho">
                Exercices d'Orthographe<br>
                <span class="sous-titre-selection" id="sous-titre-ex-ortho">Choisissez un exercice</span>
            </h1>

            <button type="button" class="btn-rose btn-option" data-url="/francais/exercices/orthographe/ie-y-it" data-titre="1-Complete par ie, y , it.">1-Complete par ie, y , it.</button>
            <button type="button" class="btn-rose btn-option" data-url="/francais/exercices/orthographe/is-id-iz" data-titre="1-Complete par is, id, iz.">1-Complete par is, id, iz.</button>
            <button type="button" class="btn-rose btn-option" data-url="/francais/exercices/orthographe/i-isc" data-titre="1-Complete par î , isc.">1-Complete par î , isc.</button>
            <button type="button" class="btn-rose btn-option" data-url="/francais/exercices/orthographe/e-eu" data-titre="1-Complete par e, eu.">1-Complete par e, eu.</button>
            <button type="button" class="btn-rose btn-option" data-url="/francais/exercices/orthographe/oeu-oei" data-titre="1-Complete par oeu, oei.">1-Complete par oeu, oei.</button>
            <button type="button" class="btn-rose btn-option" data-url="/francais/exercices/orthographe/dictee" data-titre="1-Dictée.">1-Dictée.</button>

            <button type="button" id="btn-valider" class="btn-choose">➜ Choose</button>
            <a href="/francais/exercices" class="btn-retour">← Revenir aux exercices de Français</a>
        </div>

        <script>
            let urlChoisie = "/francais/exercices/orthographe/ie-y-it";
            const boutons = document.querySelectorAll('.btn-option');
            const sousTitre = document.getElementById('sous-titre-ex-ortho');
            const btnValider = document.getElementById('btn-valider');

            boutons[0].classList.add('selected');
            sousTitre.textContent = boutons[0].getAttribute('data-titre');

            boutons.forEach(b => {
                b.addEventListener('click', () => {
                    boutons.forEach(x => x.classList.remove('selected'));
                    b.classList.add('selected');
                    urlChoisie = b.getAttribute('data-url');
                    sousTitre.textContent = b.getAttribute('data-titre');
                });
            });

            btnValider.addEventListener('click', () => {
                window.location.href = urlChoisie;
            });
        </script>
    """
    return afficher(html)

@app.route("/francais/exercices/orthographe/ie-y-it")
def page_ex_ortho_ie_y_it():
    html = """
        <div style="text-align:center;">
            <span class="badge-date">📅 Mardi 22 Septembre 2026</span>
            <div class="titre-lecon">✏️ Orthographe — Exercices</div>
        </div>
        <p style="font-weight:bold; color:#0D47A1; margin-bottom:6px;">1) Il y a combien de lettres dans l'alphabet français ?</p>
        <div style="background:#E1F5FE; border-radius:10px; padding:10px; font-weight:bold; color:#1B5E20; margin-bottom:12px;">
            Il y a 26 lettres.
        </div>
        <p style="font-weight:bold; color:#0D47A1; margin-bottom:6px;">2) Complète par : ie , y , it :</p>
        <div style="background:#fff; border:2px solid #80DEEA; border-radius:10px; padding:12px; font-size:15px; line-height:2;">
            ✦ le l<b>it</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp; le padd<b>y</b><br>
            ✦ Marie &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp; ✦ la nu<b>it</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp; le st<b>y</b>lo<br>
            ✦ la v<b>ie</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp; le paraplu<b>ie</b>
        </div>
        <div style="text-align:center;">
            <a href="/francais/exercices/orthographe" class="btn-retour">← Revenir aux exercices d'Orthographe</a>
        </div>
    """
    return afficher(html)

@app.route("/francais/exercices/orthographe/is-id-iz")
def page_ex_ortho_is_id_iz():
    html = """
        <div style="text-align:center;">
            <span class="badge-date">📅 Lundi 14 Septembre 2026</span>
            <div class="titre-lecon">✏️ Orthographe — Exercices</div>
        </div>
        <p style="font-weight:bold; color:#0D47A1; margin-bottom:6px;">1) Complète par : is , id , iz :</p>
        <div style="background:#fff; border:2px solid #80DEEA; border-radius:10px; padding:12px; font-size:15px; line-height:2; margin-bottom:12px;">
            ✦ le r<b>iz</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp; le tap<b>is</b><br>
            ✦ une sour<b>is</b> &nbsp;|&nbsp;&nbsp; le n<b>id</b><br>
            ✦ le l<b>it</b>
        </div>
        <p style="font-weight:bold; color:#0D47A1; margin-bottom:6px;">2) Cherche 2 mots qui contiennent « is » :</p>
        <div style="background:#E1F5FE; border-radius:10px; padding:10px; font-weight:bold; color:#0D47A1;">
            ✦ tapis &nbsp;&nbsp;|&nbsp;&nbsp; ✦ souris
        </div>
        <div style="text-align:center;">
            <a href="/francais/exercices/orthographe" class="btn-retour">← Revenir aux exercices d'Orthographe</a>
        </div>
    """
    return afficher(html)

@app.route("/francais/exercices/orthographe/i-isc")
def page_ex_ortho_i_isc():
    html = """
        <div style="text-align:center;">
            <span class="badge-date">📅 Mardi 06 Octobre 2026</span>
            <div class="titre-lecon">✏️ Orthographe — Exercices</div>
        </div>
        <p style="font-weight:bold; color:#0D47A1; margin-bottom:6px;">1) Complète par : î , isc :</p>
        <div style="background:#fff; border:2px solid #80DEEA; border-radius:10px; padding:12px; font-size:15px; line-height:2; margin-bottom:12px;">
            ✦ l'<b>î</b>le &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp; une ab<b>î</b>me<br>
            ✦ la perdrix &nbsp;&nbsp;|&nbsp;&nbsp; le h<b>isc</b>
        </div>
        <p style="font-weight:bold; color:#0D47A1; margin-bottom:6px;">2) Donne 1 mot qui contient « h » :</p>
        <div style="background:#E1F5FE; border-radius:10px; padding:10px; font-weight:bold; color:#1B5E20;">
            ✦ hibou
        </div>
        <div style="text-align:center;">
            <a href="/francais/exercices/orthographe" class="btn-retour">← Revenir aux exercices d'Orthographe</a>
        </div>
    """
    return afficher(html)

@app.route("/francais/exercices/orthographe/e-eu")
def page_ex_ortho_e_eu():
    html = """
        <div class="titre-lecon">✏️ Orthographe — Exercices</div>
        <p style="font-weight:bold; color:#0D47A1; margin-bottom:6px;">1) Complète par : e , eu :</p>
        <div style="background:#fff; border:2px solid #80DEEA; border-radius:10px; padding:12px; font-size:15px; line-height:2; margin-bottom:12px;">
            ✦ promenade &nbsp;|&nbsp; fl<b>eu</b>ve<br>
            ✦ petite &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|&nbsp; le j<b>eu</b>
        </div>
        <p style="font-weight:bold; color:#0D47A1; margin-bottom:6px;">2) Cherche 2 mots qui contiennent « eu » :</p>
        <div style="background:#E1F5FE; border-radius:10px; padding:10px; font-weight:bold; color:#0D47A1;">
            ✦ le jeu &nbsp;&nbsp;|&nbsp;&nbsp; ✦ fleuve
        </div>
        <div style="text-align:center;">
            <a href="/francais/exercices/orthographe" class="btn-retour">← Revenir aux exercices d'Orthographe</a>
        </div>
    """
    return afficher(html)

@app.route("/francais/exercices/orthographe/oeu-oei")
def page_ex_ortho_oeu_oei():
    html = """
        <div style="text-align:center;">
            <span class="badge-date">📅 Mardi 15 Octobre 2026</span>
            <div class="titre-lecon">✏️ Orthographe — Exercices</div>
        </div>
        <p style="font-weight:bold; color:#0D47A1; margin-bottom:6px;">1) Complète par : oeu , oei :</p>
        <div style="background:#fff; border:2px solid #80DEEA; border-radius:10px; padding:12px; font-size:15px; line-height:2; margin-bottom:12px;">
            ✦ un n<b>oeu</b>d &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp; une s<b>oeu</b>r<br>
            ✦ l'<b>oei</b>l &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp; le b<b>oeu</b>f
        </div>
        <p style="font-weight:bold; color:#0D47A1; margin-bottom:6px;">2) Cherche 2 mots qui contiennent « oeu » :</p>
        <div style="background:#E1F5FE; border-radius:10px; padding:10px; font-weight:bold; color:#0D47A1;">
            ✦ boeuf &nbsp;&nbsp;|&nbsp;&nbsp; ✦ soeur
        </div>
        <div style="text-align:center;">
            <a href="/francais/exercices/orthographe" class="btn-retour">← Revenir aux exercices d'Orthographe</a>
        </div>
    """
    return afficher(html)

@app.route("/francais/exercices/orthographe/dictee")
def page_ex_ortho_dictee_ar():
    html = """
        <div style="text-align:center;">
            <span class="badge-date">📅 Mardi 27 Octobre 2026</span>
            <div class="titre-lecon">✏️ Orthographe — Dictée & Exercices</div>
        </div>

        <p style="font-weight:bold; color:#0D47A1; margin-bottom:6px;">1) Dictée :</p>
        <div style="background:#fff; border:2px solid #80DEEA; border-radius:10px; padding:10px; font-size:15px; font-weight:bold; color:#1E3A8A; margin-bottom:12px;">
            une armoire &nbsp;—&nbsp; un are &nbsp;—&nbsp; un mare &nbsp;—&nbsp; la carte
        </div>

        <p style="font-weight:bold; color:#0D47A1; margin-bottom:6px;">2) Complète par : are - ar :</p>
        <div style="background:#fff; border:2px solid #80DEEA; border-radius:10px; padding:10px; font-size:15px; line-height:2; margin-bottom:12px;">
            ✦ la t<b style="color:#D81B60;">are</b> &nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp; p<b style="color:#D81B60;">ar</b><br>
            ✦ un c<b style="color:#D81B60;">ar</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp; la m<b style="color:#D81B60;">are</b>
        </div>

        <p style="font-weight:bold; color:#0D47A1; margin-bottom:6px;">3) Trouves 1 mot contenant « are » :</p>
        <div style="background:#E1F5FE; border-radius:10px; padding:8px; font-size:15px; font-weight:bold; color:#15803D; margin-bottom:12px;">
            ✦ la mare
        </div>

        <p style="font-weight:bold; color:#0D47A1; margin-bottom:6px;">4) Cherche 2 mots qui contient « ar » :</p>
        <div style="background:#E1F5FE; border-radius:10px; padding:8px; font-size:15px; font-weight:bold; color:#15803D;">
            ✦ par &nbsp;&nbsp;|&nbsp;&nbsp; ✦ car
        </div>
        <div style="text-align:center;">
            <a href="/francais/exercices/orthographe" class="btn-retour">← Revenir aux exercices d'Orthographe</a>
        </div>
    """
    return afficher(html)

@app.route("/francais/exercices/conjugaison")
def page_exercices_conjugaison():
    html = """
        <div class="cadre-menu">
            <h1 class="titre-principal" id="titre-ex-conj">
                Exercices de Conjugaison<br>
                <span class="sous-titre-selection" id="sous-titre-ex-conj">Choisissez un exercice</span>
            </h1>

            <button type="button" class="btn-rose btn-option" data-url="/francais/exercices/conjugaison/je-tu" data-titre="1-Remplace par les pronoms personnels sujet je ou Tu...">1-Remplace par les pronoms personnels sujet je ou Tu...</button>
            <button type="button" class="btn-rose btn-option" data-url="/francais/exercices/conjugaison/il-elle" data-titre="1-Remplace les mots soulignés par Il ou Elle..">1-Remplace les mots soulignés par Il ou Elle..</button>
            <button type="button" class="btn-rose btn-option" data-url="/francais/exercices/conjugaison/singulier" data-titre="1-Remplace les mots soulignés par les PPS au sigulier.">1-Remplace les mots soulignés par les PPS au sigulier.</button>
            <button type="button" class="btn-rose btn-option" data-url="/francais/exercices/conjugaison/nous-vous" data-titre="1-Remplace par les PPS Nous, Vous">1-Remplace par les PPS Nous, Vous</button>
            <button type="button" class="btn-rose btn-option" data-url="/francais/exercices/conjugaison/pluriels" data-titre="1-Remplace par les mots soulignés par les PPS au pluriels">1-Remplace par les mots soulignés par les PPS au pluriels</button>
            <button type="button" class="btn-rose btn-option" data-url="/francais/exercices/conjugaison/remplace-soulignes" data-titre="1-Remplace les mots soulignés.">1-Remplace les mots soulignés.</button>

            <button type="button" id="btn-valider" class="btn-choose">➜ Choose</button>
            <a href="/francais/exercices" class="btn-retour">← Revenir aux exercices de Français</a>
        </div>

        <script>
            let urlChoisie = "/francais/exercices/conjugaison/je-tu";
            const boutons = document.querySelectorAll('.btn-option');
            const sousTitre = document.getElementById('sous-titre-ex-conj');
            const btnValider = document.getElementById('btn-valider');

            boutons[0].classList.add('selected');
            sousTitre.textContent = boutons[0].getAttribute('data-titre');

            boutons.forEach(b => {
                b.addEventListener('click', () => {
                    boutons.forEach(x => x.classList.remove('selected'));
                    b.classList.add('selected');
                    urlChoisie = b.getAttribute('data-url');
                    sousTitre.textContent = b.getAttribute('data-titre');
                });
            });

            btnValider.addEventListener('click', () => {
                window.location.href = urlChoisie;
            });
        </script>
    """
    return afficher(html)

@app.route("/francais/exercices/conjugaison/je-tu")
def page_ex_conj_je_tu():
    html = """
        <div style="text-align:center;">
            <span class="badge-date">📅 Jeudi 24 Septembre 2026</span>
            <div class="titre-lecon">✏️ Conjugaison — Exercices</div>
        </div>
        <p style="font-weight:bold; color:#0D47A1; margin-bottom:8px;">1) Remplace par « Je » ou « Tu » :</p>
        <div class="cadre-contenu" style="font-size:15px; line-height:2.2;">
            ✦ Moi joue dans la cour. ➔ <b style="color:#1B5E20;">Je</b> joue dans la cour.<br>
            ✦ Toi vas à l'école. ➔ <b style="color:#1B5E20;">Tu</b> vas à l'école.<br>
            ✦ Moi dessine un chapeau. ➔ <b style="color:#1B5E20;">Je</b> dessine un chapeau.<br>
            ✦ Toi as un stylo. ➔ <b style="color:#1B5E20;">Tu</b> as un stylo.
        </div>
        <div style="text-align:center;">
            <a href="/francais/exercices/conjugaison" class="btn-retour">← Revenir aux exercices de Conjugaison</a>
        </div>
    """
    return afficher(html)

@app.route("/francais/exercices/conjugaison/il-elle")
def page_ex_conj_il_elle():
    html = """
        <div class="titre-lecon">✏️ Conjugaison — Exercices</div>
        <p style="font-weight:bold; color:#0D47A1; margin-bottom:8px;">1) Remplace les mots soulignés par « Il » ou « Elle » :</p>
        <div class="cadre-contenu" style="font-size:15px; line-height:2.2;">
            ✦ <u>René</u> continue son devoir. ➔ <b style="color:#1B5E20;">Il</b> continue son devoir.<br>
            ✦ <u>Julie</u> est malade. ➔ <b style="color:#1B5E20;">Elle</b> est malade.<br>
            ✦ <u>Ma tante</u> va au marché. ➔ <b style="color:#1B5E20;">Elle</b> va au marché.<br>
            ✦ <u>Mathis</u> est gentil. ➔ <b style="color:#1B5E20;">Il</b> est gentil.
        </div>
        <div style="text-align:center;">
            <a href="/francais/exercices/conjugaison" class="btn-retour">← Revenir aux exercices de Conjugaison</a>
        </div>
    """
    return afficher(html)

@app.route("/francais/exercices/conjugaison/singulier")
def page_ex_conj_singulier():
    html = """
        <div class="titre-lecon">✏️ Conjugaison — Exercices</div>
        <p style="font-weight:bold; color:#0D47A1; margin-bottom:8px;">1) Remplace les mots soulignés par les PPS au singulier :</p>
        <div class="cadre-contenu" style="font-size:15px; line-height:2.2;">
            ✦ <u>Le garçon</u> mange du chocolat. ➔ <b style="color:#1B5E20;">Il</b> mange du chocolat.<br>
            ✦ <u>Amina</u> dort seule. ➔ <b style="color:#1B5E20;">Elle</b> dort seule.<br>
            ✦ <u>Max</u> joue au ballon. ➔ <b style="color:#1B5E20;">Il</b> joue au ballon.<br>
            ✦ <u>Mon frère</u> lit la leçon. ➔ <b style="color:#1B5E20;">Il</b> lit la leçon.
        </div>
        <div style="text-align:center;">
            <a href="/francais/exercices/conjugaison" class="btn-retour">← Revenir aux exercices de Conjugaison</a>
        </div>
    """
    return afficher(html)

@app.route("/francais/exercices/conjugaison/nous-vous")
def page_ex_conj_nous_vous():
    html = """
        <div style="text-align:center;">
            <span class="badge-date">📅 Jeudi 15 Octobre 2026</span>
            <div class="titre-lecon">✏️ Conjugaison — Exercices</div>
        </div>
        <p style="font-weight:bold; color:#0D47A1; margin-bottom:8px;">1) Remplace par les PPS « Nous » et « Vous » :</p>
        <div class="cadre-contenu" style="font-size:15px; line-height:2.2;">
            ✦ Toi et moi regardons la télévision. ➔ <b style="color:#1B5E20;">Nous</b> regardons la télévision.<br>
            ✦ Toi et mon maître allez à Rome. ➔ <b style="color:#1B5E20;">Vous</b> allez à Rome.<br>
            ✦ Moi et maman achetons un stylo. ➔ <b style="color:#1B5E20;">Nous</b> achetons un stylo.<br>
            ✦ Toi et Lucie avez un joli cartable. ➔ <b style="color:#1B5E20;">Vous</b> avez un joli cartable.
        </div>
        <div style="text-align:center;">
            <a href="/francais/exercices/conjugaison" class="btn-retour">← Revenir aux exercices de Conjugaison</a>
        </div>
    """
    return afficher(html)

@app.route("/francais/exercices/conjugaison/pluriels")
def page_ex_conj_pluriels():
    html = """
        <div style="text-align:center;">
            <span class="badge-date">📅 Mardi 20 Octobre 2026</span>
            <div class="titre-lecon">✏️ Conjugaison — Exercices</div>
        </div>
        <p style="font-weight:bold; color:#0D47A1; margin-bottom:8px;">1) Remplace par les PPS au pluriel :</p>
        <div class="cadre-contenu" style="font-size:15px; line-height:2.2;">
            ✦ <u>Toi et Marie</u> avez mal au coeur. ➔ <b style="color:#1B5E20;">Vous</b> avez mal au coeur.<br>
            ✦ <u>Moi et papa</u> adorons le thé. ➔ <b style="color:#1B5E20;">Nous</b> adorons le thé.<br>
            ✦ <u>Les filles</u> entrent dans la salle. ➔ <b style="color:#1B5E20;">Elles</b> entrent dans la salle.<br>
            ✦ <u>Mathieu et Jules</u> jouent à la corde. ➔ <b style="color:#1B5E20;">Ils</b> jouent à la corde.
        </div>
        <div style="text-align:center;">
            <a href="/francais/exercices/conjugaison" class="btn-retour">← Revenir aux exercices de Conjugaison</a>
        </div>
    """
    return afficher(html)

@app.route("/francais/exercices/conjugaison/remplace-soulignes")
def page_ex_conj_remplace_soulignes():
    html = """
        <div style="text-align:center;">
            <span class="badge-date">📅 Lundi 26 Octobre 2026</span>
            <div class="titre-lecon">✏️ Conjugaison — Exercices</div>
        </div>

        <p style="font-weight:bold; color:#0D47A1; margin-bottom:8px;">1) Remplace les mots soulignés par : Ils, Elles, Nous, Vous :</p>
        <div class="cadre-contenu" style="font-size:15px; line-height:2.3;">
            ✦ <u>Marie et Clara</u> étudient bien.<br>
            &nbsp;&nbsp;&nbsp;➔ <b style="color:#15803D;">Elles</b><br><br>
            ✦ <u>Jonathan et André</u> utilisent une moule.<br>
            &nbsp;&nbsp;&nbsp;➔ <b style="color:#15803D;">Ils</b><br><br>
            ✦ <u>Moi et Jean</u> assoyons près de la mare.<br>
            &nbsp;&nbsp;&nbsp;➔ <b style="color:#15803D;">Nous</b><br><br>
            ✦ <u>Toi et Victor</u> avez votre stylo.<br>
            &nbsp;&nbsp;&nbsp;➔ <b style="color:#15803D;">Vous</b><br><br>
            ✦ <u>Max et Maxime</u> montrent la carte.<br>
            &nbsp;&nbsp;&nbsp;➔ <b style="color:#15803D;">Ils</b>
        </div>

        <p style="font-weight:bold; color:#0D47A1; margin-top:12px; margin-bottom:8px;">2) Cite les PPS :</p>
        <div style="background:#F0FDF4; border:2px dashed #16A34A; border-radius:10px; padding:10px; font-size:15px; font-weight:bold; color:#166534;">
            - je, Tu, Il, Elle, Nous, Vous, Ils, Elles
        </div>

        <div style="text-align:center;">
            <a href="/francais/exercices/conjugaison" class="btn-retour">← Revenir aux exercices de Conjugaison</a>
        </div>
    """
    return afficher(html)

@app.route("/francais/exercices/grammaire")
def page_exercices_grammaire():
    html = """
        <div class="cadre-menu">
            <h1 class="titre-principal" id="titre-ex-gramm">
                Exercices de Grammaire<br>
                <span class="sous-titre-selection" id="sous-titre-ex-gramm">Choisissez un exercice</span>
            </h1>

            <button type="button" class="btn-rose btn-option" data-url="/francais/exercices/grammaire/26-lettres" data-titre="1-Quels sont les 26 lettres de l'alphabet..">1-Quels sont les 26 lettres de l'alphabet..</button>
            <button type="button" class="btn-rose btn-option" data-url="/francais/exercices/grammaire/voyelles" data-titre="1-Combien y a t-il de voyelles...">1-Combien y a t-il de voyelles...</button>
            <button type="button" class="btn-rose btn-option" data-url="/francais/exercices/grammaire/separe-syllabes" data-titre="1-Sépare les syllabes et donne ses nombres..">1-Sépare les syllabes et donne ses nombres..</button>
            <button type="button" class="btn-rose btn-option" data-url="/francais/exercices/grammaire/compte-syllabes" data-titre="1-Compte et sépare les syllabes..">1-Compte et sépare les syllabes..</button>
            <button type="button" class="btn-rose btn-option" data-url="/francais/exercices/grammaire/animal-chose-pers" data-titre="1-Complète par  animal-chose-personne..">1-Complète par  animal-chose-personne..</button>
            <button type="button" class="btn-rose btn-option" data-url="/francais/exercices/grammaire/souligne-bonne-rep" data-titre="1-Souligne la bonne réponse.">1-Souligne la bonne réponse.</button>

            <button type="button" id="btn-valider" class="btn-choose">➜ Choose</button>
            <a href="/francais/exercices" class="btn-retour">← Revenir aux exercices de Français</a>
        </div>

        <script>
            let urlChoisie = "/francais/exercices/grammaire/26-lettres";
            const boutons = document.querySelectorAll('.btn-option');
            const sousTitre = document.getElementById('sous-titre-ex-gramm');
            const btnValider = document.getElementById('btn-valider');

            boutons[0].classList.add('selected');
            sousTitre.textContent = boutons[0].getAttribute('data-titre');

            boutons.forEach(b => {
                b.addEventListener('click', () => {
                    boutons.forEach(x => x.classList.remove('selected'));
                    b.classList.add('selected');
                    urlChoisie = b.getAttribute('data-url');
                    sousTitre.textContent = b.getAttribute('data-titre');
                });
            });

            btnValider.addEventListener('click', () => {
                window.location.href = urlChoisie;
            });
        </script>
    """
    return afficher(html)

@app.route("/francais/exercices/grammaire/26-lettres")
def page_ex_gramm_26_lettres():
    html = """
        <div style="text-align:center;">
            <span class="badge-date">📅 Lundi 21 Septembre 2026</span>
            <div class="titre-lecon">✏️ Grammaire — Exercices</div>
        </div>
        <p style="font-weight:bold; color:#0D47A1; margin-bottom:6px;">1) Quels sont les 26 lettres de l'alphabet français ?</p>
        <div style="background:#fff; border:2px solid #80DEEA; border-radius:10px; padding:12px; font-size:15px; line-height:2; margin-bottom:12px;">
            <b style="color:#D81B60;">a - b - c - d - e - f - g - h - i - j - k - l - m - n - o - p - q - r - s - t - u - v - w - x - y - z</b>
        </div>
        <p style="font-weight:bold; color:#0D47A1; margin-bottom:6px;">2) Il y a combien de lettres dans l'alphabet français ?</p>
        <div style="background:#E1F5FE; border-radius:10px; padding:10px; font-size:15px; font-weight:bold; color:#1B5E20;">
            Il y a 26 lettres.
        </div>
        <div style="text-align:center;">
            <a href="/francais/exercices/grammaire" class="btn-retour">← Revenir aux exercices de Grammaire</a>
        </div>
    """
    return afficher(html)

@app.route("/francais/exercices/grammaire/voyelles")
def page_ex_gramm_voyelles():
    html = """
        <div style="text-align:center;">
            <span class="badge-date">📅 Mardi 29 Septembre 2026</span>
            <div class="titre-lecon">✏️ Grammaire — Voyelles et Consonnes</div>
        </div>
        <p style="font-weight:bold; color:#0D47A1; margin-bottom:6px;">1) Combien y a-t-il de voyelles ?</p>
        <div style="background:#E1F5FE; border-radius:10px; padding:10px; font-size:15px; font-weight:bold; color:#1B5E20; margin-bottom:12px;">
            Il y a 6 voyelles. (a - e - i - u - y - o)
        </div>
        <p style="font-weight:bold; color:#0D47A1; margin-bottom:6px;">2) Combien de consonnes y a-t-il ?</p>
        <div style="background:#E1F5FE; border-radius:10px; padding:10px; font-size:15px; font-weight:bold; color:#1B5E20;">
            Il y a 20 consonnes.
        </div>
        <div style="text-align:center;">
            <a href="/francais/exercices/grammaire" class="btn-retour">← Revenir aux exercices de Grammaire</a>
        </div>
    """
    return afficher(html)

@app.route("/francais/exercices/grammaire/separe-syllabes")
def page_ex_gramm_separe_syllabes():
    html = """
        <div style="text-align:center;">
            <span class="badge-date">📅 Mercredi 07 Octobre 2026</span>
            <div class="titre-lecon">✏️ Grammaire — Exercices</div>
        </div>
        <p style="font-weight:bold; color:#0D47A1; margin-bottom:8px;">1) Sépare les syllabes et donne ses nombres :</p>
        <div class="cadre-contenu" style="font-size:15px; line-height:2.2;">
            ✦ papa = <b style="color:#1B5E20;">pa - pa</b> = 2 syllabes<br>
            ✦ camarade = <b style="color:#1B5E20;">ca - ma - ra - de</b> = 4 syllabes<br>
            ✦ village = <b style="color:#1B5E20;">vi - lla - ge</b> = 3 syllabes<br>
            ✦ locomotive = <b style="color:#1B5E20;">lo - co - mo - ti - ve</b> = 5 syllabes<br>
            ✦ promenade = <b style="color:#1B5E20;">pro - me - na - de</b> = 4 syllabes
        </div>
        <div style="text-align:center;">
            <a href="/francais/exercices/grammaire" class="btn-retour">← Revenir aux exercices de Grammaire</a>
        </div>
    """
    return afficher(html)

@app.route("/francais/exercices/grammaire/compte-syllabes")
def page_ex_gramm_compte_syllabes():
    html = """
        <div style="text-align:center;">
            <span class="badge-date">📅 Lundi 12 Octobre 2026</span>
            <div class="titre-lecon">✏️ Grammaire — Exercices</div>
        </div>
        <p style="font-weight:bold; color:#0D47A1; margin-bottom:8px;">1) Compte et sépare les syllabes :</p>
        <div class="cadre-contenu" style="font-size:15px; line-height:2.2;">
            ✦ chaloupe = <b style="color:#1B5E20;">cha - lou - pe</b> = 3 syllabes<br>
            ✦ moule = <b style="color:#1B5E20;">mou - le</b> = 2 syllabes<br>
            ✦ couture = <b style="color:#1B5E20;">cou - tu - re</b> = 3 syllabes<br>
            ✦ chicane = <b style="color:#1B5E20;">chi - ca - ne</b> = 3 syllabes<br>
            ✦ pyramide = <b style="color:#1B5E20;">py - ra - mi - de</b> = 4 syllabes
        </div>
        <div style="text-align:center;">
            <a href="/francais/exercices/grammaire" class="btn-retour">← Revenir aux exercices de Grammaire</a>
        </div>
    """
    return afficher(html)

@app.route("/francais/exercices/grammaire/animal-chose-pers")
def page_ex_gramm_animal_chose_pers():
    html = """
        <div class="titre-lecon">✏️ Grammaire — Exercices</div>
        <p style="font-weight:bold; color:#0D47A1; margin-bottom:8px;">1) Complète par : animal — chose — personne :</p>
        <div class="cadre-contenu" style="font-size:15px; line-height:2.2;">
            ✦ Le stylo est un nom d'<b style="color:#1B5E20;">une chose</b>.<br>
            ✦ Marius est un nom d'<b style="color:#1B5E20;">une personne</b>.<br>
            ✦ Le chat est un nom d'<b style="color:#1B5E20;">un animal</b>.<br>
            ✦ La crevette est un nom d'<b style="color:#1B5E20;">un animal</b>.<br>
            ✦ Le tableau est un nom d'<b style="color:#1B5E20;">une chose</b>.
        </div>
        <div style="text-align:center;">
            <a href="/francais/exercices/grammaire" class="btn-retour">← Revenir aux exercices de Grammaire</a>
        </div>
    """
    return afficher(html)

@app.route("/francais/exercices/grammaire/souligne-bonne-rep")
def page_ex_gramm_souligne_bonne_rep():
    html = """
        <div style="text-align:center;">
            <span class="badge-date">📅 Mercredi 28 Octobre 2026</span>
            <div class="titre-lecon">✏️ Grammaire — Souligne la bonne réponse</div>
        </div>

        <p style="font-weight:bold; color:#0D47A1; margin-bottom:8px;">1) Soulignes la bonne réponse :</p>
        <div class="cadre-contenu" style="font-size:15px; line-height:2.4;">
            • Les noms propres commencent par :<br>
            &nbsp;&nbsp;&nbsp;&nbsp;- une lettre minuscule<br>
            &nbsp;&nbsp;&nbsp;&nbsp;- <b style="color:#15803D; text-decoration:underline;">une lettre majuscule</b> ✓<br><br>
            • Maman est un nom qui appartient à :<br>
            &nbsp;&nbsp;&nbsp;&nbsp;- <b style="color:#15803D; text-decoration:underline;">tout le monde</b> ✓<br>
            &nbsp;&nbsp;&nbsp;&nbsp;- une seule personne
        </div>

        <p style="font-weight:bold; color:#0D47A1; margin-top:12px; margin-bottom:8px;">2) Entoures les intrus :</p>
        <div style="background:#EFF6FF; border:2px dashed #3B82F6; border-radius:10px; padding:12px; font-size:15px; line-height:2.2; margin-bottom:8px;">
            Paris &nbsp;—&nbsp; <span style="border:2px solid #DC2626; border-radius:8px; padding:2px 6px; color:#DC2626; font-weight:bold;">Marie</span> &nbsp;—&nbsp; Mandroseza &nbsp;—&nbsp; <span style="border:2px solid #DC2626; border-radius:8px; padding:2px 6px; color:#DC2626; font-weight:bold;">Madagascar</span> &nbsp;—&nbsp; Milou &nbsp;—&nbsp; Babi
        </div>
        <div style="background:#EFF6FF; border:2px dashed #3B82F6; border-radius:10px; padding:12px; font-size:15px; line-height:2.2;">
            Yvon &nbsp;—&nbsp; <span style="border:2px solid #DC2626; border-radius:8px; padding:2px 6px; color:#DC2626; font-weight:bold;">Capeline</span> &nbsp;—&nbsp; Luca &nbsp;—&nbsp; <span style="border:2px solid #DC2626; border-radius:8px; padding:2px 6px; color:#DC2626; font-weight:bold;">Max</span> &nbsp;—&nbsp; Rose &nbsp;—&nbsp; une Tulipe
        </div>

        <p style="font-weight:bold; color:#0D47A1; margin-top:12px; margin-bottom:8px;">3) Donnes 4 noms propres :</p>
        <div style="background:#F0FDF4; border:2px dashed #16A34A; border-radius:10px; padding:10px; font-size:15px; font-weight:bold; color:#166534;">
            ✦ Bady &nbsp;|&nbsp; ✦ Paris &nbsp;|&nbsp; ✦ Diego &nbsp;|&nbsp; ✦ Tamatave
        </div>

        <div style="text-align:center;">
            <a href="/francais/exercices/grammaire" class="btn-retour">← Revenir aux exercices de Grammaire</a>
        </div>
    """
    return afficher(html)

# =============================================================================
# MENUS MATHÉMATIQUES (LEÇONS & EXERCICES) AVEC BOUTON CHOOSE
# =============================================================================
@app.route("/mathematiques/lecons")
def page_mathematiques_lecons():
    html = """
        <div class="cadre-menu">
            <h1 class="titre-principal" id="titre-math-lecons">
                Mathématiques — Leçons<br>
                <span class="sous-titre-selection" id="sous-titre-math-lecons">Choisissez une leçon</span>
            </h1>

            <button type="button" class="btn-rose btn-option" data-url="/mathematiques/lecons/arithmetique" data-titre="Arithmétiques">Arithmétiques</button>
            <button type="button" class="btn-rose btn-option" data-url="/mathematiques/lecons/geometrie" data-titre="Géométrie">Géométrie</button>
            <button type="button" class="btn-rose btn-option" data-url="/mathematiques/lecons/metrique" data-titre="Systeme métrique">Systeme métrique</button>

            <button type="button" id="btn-valider" class="btn-choose">➜ Choose</button>
            <a href="/programme?matiere=Mathematiques" class="btn-retour">← Revenir</a>
        </div>

        <script>
            let urlChoisie = "/mathematiques/lecons/arithmetique";
            const boutons = document.querySelectorAll('.btn-option');
            const sousTitre = document.getElementById('sous-titre-math-lecons');
            const btnValider = document.getElementById('btn-valider');

            boutons[0].classList.add('selected');
            sousTitre.textContent = boutons[0].getAttribute('data-titre');

            boutons.forEach(b => {
                b.addEventListener('click', () => {
                    boutons.forEach(x => x.classList.remove('selected'));
                    b.classList.add('selected');
                    urlChoisie = b.getAttribute('data-url');
                    sousTitre.textContent = b.getAttribute('data-titre');
                });
            });

            btnValider.addEventListener('click', () => {
                window.location.href = urlChoisie;
            });
        </script>
    """
    return afficher(html)

@app.route("/mathematiques/exercices")
def page_mathematiques_exercices():
    html = """
        <div class="cadre-menu">
            <h1 class="titre-principal" id="titre-math-ex">
                Exercices de Mathématiques<br>
                <span class="sous-titre-selection" id="sous-titre-math-ex">Choisissez une option</span>
            </h1>

            <button type="button" class="btn-rose btn-option" data-url="/mathematiques/exercices/arithmetique" data-titre="Arithmétiques">Arithmétiques</button>
            <button type="button" class="btn-rose btn-option" data-url="/mathematiques/exercices/geometrie" data-titre="Géométrie">Géométrie</button>
            <button type="button" class="btn-rose btn-option" data-url="/mathematiques/exercices/metrique" data-titre="Systeme métrique">Systeme métrique</button>

            <button type="button" id="btn-valider" class="btn-choose">➜ Choose</button>
            <a href="/programme?matiere=Mathematiques" class="btn-retour">← Revenir</a>
        </div>

        <script>
            let urlChoisie = "/mathematiques/exercices/arithmetique";
            const boutons = document.querySelectorAll('.btn-option');
            const sousTitre = document.getElementById('sous-titre-math-ex');
            const btnValider = document.getElementById('btn-valider');

            boutons[0].classList.add('selected');
            sousTitre.textContent = boutons[0].getAttribute('data-titre');

            boutons.forEach(b => {
                b.addEventListener('click', () => {
                    boutons.forEach(x => x.classList.remove('selected'));
                    b.classList.add('selected');
                    urlChoisie = b.getAttribute('data-url');
                    sousTitre.textContent = b.getAttribute('data-titre');
                });
            });

            btnValider.addEventListener('click', () => {
                window.location.href = urlChoisie;
            });
        </script>
    """
    return afficher(html)

# =============================================================================
# SOUS-MENUS MATHÉMATIQUES (ARITHMÉTIQUE, GÉOMÉTRIE, MÉTRIQUE)
# =============================================================================
@app.route("/mathematiques/lecons/arithmetique")
def page_arithmetique():
    html = """
        <div class="cadre-menu">
            <h1 class="titre-principal" id="titre-arith">
                Arithmétique<br>
                <span class="sous-titre-selection" id="sous-titre-arith">Choisissez une leçon</span>
            </h1>

            <button type="button" class="btn-rose btn-option" data-url="/mathematiques/lecons/arithmetique/comptage-10" data-titre="Comptage de 1 en 1 de 0 à 10">Comptage de 1 en 1 de 0 à 10</button>
            <button type="button" class="btn-rose btn-option" data-url="/mathematiques/lecons/arithmetique/comptage-49" data-titre="Comptage de 1 en 1 de 0 à 49">Comptage de 1 en 1 de 0 à 49</button>
            <button type="button" class="btn-rose btn-option" data-url="/mathematiques/lecons/arithmetique/addition-sans" data-titre="Addition sans retenue">Addition sans retenue</button>
            <button type="button" class="btn-rose btn-option" data-url="/mathematiques/lecons/arithmetique/addition-avec" data-titre="Addition avec retenue">Addition avec retenue</button>
            <button type="button" class="btn-rose btn-option" data-url="/mathematiques/lecons/arithmetique/comptage-119" data-titre="Comptage de 1 en 1 de 80 à 119">Comptage de 1 en 1 de 80 à 119</button>

            <button type="button" id="btn-valider" class="btn-choose">➜ Choose</button>
            <a href="/mathematiques/lecons" class="btn-retour">← Revenir aux leçons de Mathématiques</a>
        </div>

        <script>
            let urlChoisie = "/mathematiques/lecons/arithmetique/comptage-10";
            const boutons = document.querySelectorAll('.btn-option');
            const sousTitre = document.getElementById('sous-titre-arith');
            const btnValider = document.getElementById('btn-valider');

            boutons[0].classList.add('selected');
            sousTitre.textContent = boutons[0].getAttribute('data-titre');

            boutons.forEach(b => {
                b.addEventListener('click', () => {
                    boutons.forEach(x => x.classList.remove('selected'));
                    b.classList.add('selected');
                    urlChoisie = b.getAttribute('data-url');
                    sousTitre.textContent = b.getAttribute('data-titre');
                });
            });

            btnValider.addEventListener('click', () => {
                window.location.href = urlChoisie;
            });
        </script>
    """
    return afficher(html)

@app.route("/mathematiques/lecons/arithmetique/comptage-10")
def page_lecon_comptage_10():
    html = """
        <div style="text-align:center;">
            <span class="badge-date">📅 Jeudi 17 Septembre 2026</span>
            <div class="titre-lecon">✨ Comptage de 1 en 1 de 0 à 10 ✨</div>
        </div>
        <div style="background-color:#E8F5E9; border:2px dashed #4CAF50; border-radius:14px; padding:16px; font-size:16px; font-weight:bold; color:#2E7D32; text-align:center;">
            0 ➔ 1 ➔ 2 ➔ 3 ➔ 4 ➔ 5 ➔ 6 ➔ 7 ➔ 8 ➔ 9 ➔ 10
        </div>
        <div style="text-align:center;">
            <a href="/mathematiques/lecons/arithmetique" class="btn-retour">← Revenir aux leçons d'Arithmétique</a>
        </div>
    """
    return afficher(html)

@app.route("/mathematiques/lecons/arithmetique/comptage-49")
def page_lecon_comptage_49():
    chiffres_49 = " ➔ ".join(str(i) for i in range(50))
    chiffres_79 = " - ".join(str(i) for i in range(50, 80))
    html = f"""
        <div style="text-align:center;">
            <span class="badge-date">📅 Lundi 28 Septembre 2026</span>
            <div class="titre-lecon">✨ Comptage de 1 en 1 de 0 à 49 ✨</div>
        </div>
        <div style="background-color:#E8F5E9; border:2px dashed #4CAF50; border-radius:12px; padding:12px; line-height:2; font-size:13px; color:#2E7D32; text-align:center;">
            {chiffres_49}
        </div>
        <p style="font-size:15px; font-weight:800; color:#FF2E93; margin-top:16px; margin-bottom:8px; text-align:center;">✍️ Écriture littérale de 0 à 10</p>
        <div style="background:#fff; border:2px solid #80DEEA; border-radius:10px; padding:10px; font-size:14px; font-weight:bold; color:#5D4037; text-align:center;">
            0=zéro | 1=un | 2=deux | 3=trois | 4=quatre | 5=cinq | 6=six | 7=sept | 8=huit | 9=neuf | 10=dix
        </div>

        <div style="margin-top:16px; background:#F0F9FF; border:3px solid #0284C7; border-radius:14px; padding:14px; text-align:center;">
            <div style="margin-bottom:8px;">
                <span style="background:#0284C7; color:#ffffff; font-size:13px; font-weight:bold; padding:4px 12px; border-radius:10px;">
                    📅 Lundi 12 Octobre 2026 — Suite de la leçon
                </span>
            </div>
            <p style="font-size:15px; font-weight:800; color:#0369A1; margin-bottom:8px;">✨ Comptage de 1 en 1 de 50 à 79 ✨</p>
            <div style="background:#ffffff; border-radius:10px; padding:12px; font-size:14px; font-weight:bold; color:#0F172A; line-height:2;">
                {chiffres_79}
            </div>
        </div>
        <div style="text-align:center;">
            <a href="/mathematiques/lecons/arithmetique" class="btn-retour">← Revenir aux leçons d'Arithmétique</a>
        </div>
    """
    return afficher(html)

@app.route("/mathematiques/lecons/arithmetique/comptage-119")
def page_lecon_comptage_119():
    chiffres_119 = " - ".join(str(i) for i in range(80, 120))
    html = f"""
        <div style="text-align:center;">
            <span class="badge-date">📅 Lundi 26 Octobre 2026</span>
            <div class="titre-lecon">✨ Comptage de 1 en 1 de 80 à 119 ✨</div>
        </div>

        <div style="background-color:#FFFFFF; border:3px solid #80DEEA; border-radius:14px; padding:14px; line-height:2.2; font-size:14px; font-weight:bold; color:#0F172A; text-align:center;">
            {chiffres_119}
        </div>

        <p style="font-size:15px; font-weight:800; color:#16A34A; margin-top:16px; margin-bottom:8px; text-align:center;">📊 Tableau de numération (110) :</p>
        <table border="2" cellpadding="8" cellspacing="0" style="width:65%; margin:auto; border-collapse:collapse; text-align:center; font-size:16px; font-weight:bold; background:#fff; border-color:#0284C7;">
            <tr style="background:#E0F2FE; color:#0369A1;">
                <td width="33%">c</td>
                <td width="33%">d</td>
                <td width="33%">u</td>
            </tr>
            <tr style="color:#D90429; font-size:18px;">
                <td>1</td>
                <td>1</td>
                <td>0</td>
            </tr>
        </table>
        <p style="font-size:13px; font-weight:bold; color:#0369A1; margin-top:8px; text-align:center;">110 = 1 centaine, 1 dizaine, 0 unité</p>

        <div style="text-align:center;">
            <a href="/mathematiques/lecons/arithmetique" class="btn-retour">← Revenir aux leçons d'Arithmétique</a>
        </div>
    """
    return afficher(html)

@app.route("/mathematiques/lecons/arithmetique/addition-sans")
def page_lecon_addition_sans():
    html = """
        <div style="text-align:center;">
            <span class="badge-date">📅 Lundi 05 Octobre 2026</span>
            <div class="titre-lecon">Addition Sans Retenue</div>
        </div>
        <div style="background-color:#E8F5E9; border-left:5px solid #2E7D32; padding:12px; border-radius:8px; font-size:14px; margin-bottom:12px;">
            <b>Règle :</b> Le signe de l'addition est le <b style="color:#1B5E20; font-size:16px;">+</b>
        </div>
        <div style="background-color:#B3E5FC; border-radius:12px; padding:14px; font-family:monospace; font-size:17px; font-weight:bold; color:#1A237E; text-align:center;">
            5 + 3 = 8 &nbsp;&nbsp;|&nbsp;&nbsp; 13 + 5 = 18 &nbsp;&nbsp;|&nbsp;&nbsp; 31 + 16 = 47
        </div>
        <div style="text-align:center;">
            <a href="/mathematiques/lecons/arithmetique" class="btn-retour">← Revenir aux leçons d'Arithmétique</a>
        </div>
    """
    return afficher(html)

@app.route("/mathematiques/lecons/arithmetique/addition-avec")
def page_lecon_addition_avec():
    html = """
        <div style="text-align:center;">
            <span class="badge-date">📅 Mercredi 21 Octobre 2026</span>
            <div class="titre-lecon">Addition Avec Retenue</div>
        </div>
        <div style="background-color:#E1BEE7; border-radius:12px; padding:14px; font-family:monospace; font-size:17px; font-weight:bold; color:#4A148C; text-align:center;">
            26 + 37 = 63 &nbsp;&nbsp;|&nbsp;&nbsp; 15 + 26 = 41
        </div>
        <div style="text-align:center;">
            <a href="/mathematiques/lecons/arithmetique" class="btn-retour">← Revenir aux leçons d'Arithmétique</a>
        </div>
    """
    return afficher(html)

@app.route("/mathematiques/lecons/geometrie")
def page_geometrie():
    html = """
        <div class="cadre-menu">
            <h1 class="titre-principal" id="titre-geo">
                Géométrie<br>
                <span class="sous-titre-selection" id="sous-titre-geo">Choisissez une leçon</span>
            </h1>

            <button type="button" class="btn-rose btn-option" data-url="/mathematiques/lecons/geometrie/point" data-titre="Les points">Les points</button>
            <button type="button" class="btn-rose btn-option" data-url="/mathematiques/lecons/geometrie/lignes" data-titre="Les lignes">Les lignes</button>

            <button type="button" id="btn-valider" class="btn-choose">➜ Choose</button>
            <a href="/mathematiques/lecons" class="btn-retour">← Revenir</a>
        </div>

        <script>
            let urlChoisie = "/mathematiques/lecons/geometrie/point";
            const boutons = document.querySelectorAll('.btn-option');
            const sousTitre = document.getElementById('sous-titre-geo');
            const btnValider = document.getElementById('btn-valider');

            boutons[0].classList.add('selected');
            sousTitre.textContent = boutons[0].getAttribute('data-titre');

            boutons.forEach(b => {
                b.addEventListener('click', () => {
                    boutons.forEach(x => x.classList.remove('selected'));
                    b.classList.add('selected');
                    urlChoisie = b.getAttribute('data-url');
                    sousTitre.textContent = b.getAttribute('data-titre');
                });
            });

            btnValider.addEventListener('click', () => {
                window.location.href = urlChoisie;
            });
        </script>
    """
    return afficher(html)

@app.route("/mathematiques/lecons/geometrie/point")
def page_lecon_point():
    html = """
        <div style="text-align:center;">
            <span class="badge-date">📅 Jeudi 17 Septembre 2026</span>
            <div class="titre-lecon">Le Point</div>
        </div>
        <div style="background-color:#E8F5E9; border-left:5px solid #1B5E20; padding:14px; border-radius:8px; font-size:15px; color:#1B5E20; margin-bottom:20px;">
            ✦ Un point est une figure géométrique sans dimension (on ne peut pas mesurer).
        </div>
        <p style="text-align:center; font-size:28px; color:#D81B60; font-weight:bold;">● Point A</p>
        <div style="text-align:center;">
            <a href="/mathematiques/lecons/geometrie" class="btn-retour">← Revenir à la Géométrie</a>
        </div>
    """
    return afficher(html)

@app.route("/mathematiques/lecons/geometrie/lignes")
def page_lecon_lignes():
    html = """
        <div style="text-align:center;">
            <span class="badge-date">📅 Jeudi 13 Octobre 2026</span>
            <div class="titre-lecon">📖 Géométrie — Les 5 sortes de lignes</div>
        </div>

        <div class="cahier-seyes">
            <div class="cahier-ligne-texte">Il y a 5 sortes de lignes :</div>
            
            <div style="margin-bottom:22px;">
                <p style="color:#1E3A8A; font-weight:bold; margin-bottom:6px;">1. Ligne droite horizontale</p>
                <svg width="240" height="30"><line x1="20" y1="15" x2="220" y2="15" stroke="#0284C7" stroke-width="3"/></svg>
            </div>

            <div style="margin-bottom:22px;">
                <p style="color:#1E3A8A; font-weight:bold; margin-bottom:6px;">2. Ligne droite verticale</p>
                <svg width="240" height="70"><line x1="60" y1="5" x2="60" y2="65" stroke="#0284C7" stroke-width="3"/></svg>
            </div>

            <div style="margin-bottom:22px;">
                <p style="color:#1E3A8A; font-weight:bold; margin-bottom:6px;">3. Ligne droite oblique</p>
                <svg width="240" height="50"><line x1="20" y1="40" x2="160" y2="10" stroke="#0284C7" stroke-width="3"/></svg>
            </div>

            <div style="margin-bottom:22px;">
                <p style="color:#1E3A8A; font-weight:bold; margin-bottom:6px;">4. Ligne brisée</p>
                <svg width="240" height="40"><polyline points="20,30 50,10 80,30 110,10 140,30" fill="none" stroke="#0284C7" stroke-width="3"/></svg>
            </div>

            <div style="margin-bottom:22px;">
                <p style="color:#1E3A8A; font-weight:bold; margin-bottom:6px;">5. Ligne courbe</p>
                <svg width="240" height="40"><path d="M 20 20 Q 60 0 100 25 T 180 20" fill="none" stroke="#0284C7" stroke-width="3"/></svg>
            </div>
        </div>

        <div style="text-align:center;">
            <a href="/mathematiques/lecons/geometrie" class="btn-retour">← Revenir à la Géométrie</a>
        </div>
    """
    return afficher(html)

@app.route("/mathematiques/lecons/metrique")
def page_metrique():
    html = """
        <div class="cadre-menu">
            <h1 class="titre-principal" id="titre-met">
                Système métrique<br>
                <span class="sous-titre-selection" id="sous-titre-met">Choisissez une leçon</span>
            </h1>

            <button type="button" class="btn-rose btn-option" data-url="/mathematiques/lecons/metrique/regle" data-titre="Mesurer avec un règle graduée">Mesurer avec un règle graduée</button>
            <button type="button" class="btn-rose btn-option" data-url="/mathematiques/lecons/metrique/segment" data-titre="Mesurer un segment">Mesurer un segment</button>

            <button type="button" id="btn-valider" class="btn-choose">➜ Choose</button>
            <a href="/mathematiques/lecons" class="btn-retour">← Revenir</a>
        </div>

        <script>
            let urlChoisie = "/mathematiques/lecons/metrique/regle";
            const boutons = document.querySelectorAll('.btn-option');
            const sousTitre = document.getElementById('sous-titre-met');
            const btnValider = document.getElementById('btn-valider');

            boutons[0].classList.add('selected');
            sousTitre.textContent = boutons[0].getAttribute('data-titre');

            boutons.forEach(b => {
                b.addEventListener('click', () => {
                    boutons.forEach(x => x.classList.remove('selected'));
                    b.classList.add('selected');
                    urlChoisie = b.getAttribute('data-url');
                    sousTitre.textContent = b.getAttribute('data-titre');
                });
            });

            btnValider.addEventListener('click', () => {
                window.location.href = urlChoisie;
            });
        </script>
    """
    return afficher(html)

@app.route("/mathematiques/lecons/metrique/regle")
def page_lecon_regle():
    lignes_graduations = ""
    for i in range(9):
        gx = 10 + i * 35
        lignes_graduations += f'<line x1="{gx}" y1="10" x2="{gx}" y2="24" stroke="#854D0E" stroke-width="1.5"/>'
        lignes_graduations += f'<text x="{gx - 4}" y="38" font-size="11" font-weight="bold" fill="#854D0E">{i}</text>'
        if i < 8:
            for mm in range(1, 10):
                mx = gx + mm * 3.5
                hmm = 18 if mm == 5 else 15
                lignes_graduations += f'<line x1="{mx}" y1="10" x2="{mx}" y2="{hmm}" stroke="#854D0E" stroke-width="1"/>'

    html = f"""
        <div style="text-align:center;">
            <span class="badge-date">📅 Mardi 23 Septembre 2026</span>
            <div class="titre-lecon">📏 Système métrique — Mesurer avec une règle graduée</div>
        </div>

        <div class="cahier-seyes">
            <div class="cahier-ligne-texte">1. Poser le 0 de la règle sur le point de départ.</div>
            <div class="cahier-ligne-texte">2. Marquer la graduation voulue (ex: 4 cm) et relier.</div>

            <svg width="340" height="130" style="margin-top:10px;">
                <rect x="10" y="10" width="300" height="45" rx="6" fill="#FEF08A" stroke="#CA8A04" stroke-width="2"/>
                {lignes_graduations}
                <line x1="10" y1="85" x2="150" y2="85" stroke="#DC2626" stroke-width="3"/>
                <line x1="10" y1="78" x2="10" y2="92" stroke="#DC2626" stroke-width="3"/>
                <line x1="150" y1="78" x2="150" y2="92" stroke="#DC2626" stroke-width="3"/>
                <text x="65" y="108" font-size="13" font-weight="bold" fill="#DC2626">4 cm</text>
            </svg>
        </div>

        <div style="text-align:center;">
            <a href="/mathematiques/lecons/metrique" class="btn-retour">← Revenir au Système métrique</a>
        </div>
    """
    return afficher(html)

@app.route("/mathematiques/lecons/metrique/segment")
def page_lecon_segment():
    html = """
        <div style="text-align:center;">
            <span class="badge-date">📅 Jeudi 08 Octobre 2026</span>
            <div class="titre-lecon">📖 Système métrique — Mesurer un segment</div>
        </div>

        <div class="cahier-seyes">
            <div class="cahier-ligne-texte">✦ Le segment est une ligne limitée qui a un début et une fin :</div>
            <svg width="300" height="50">
                <line x1="30" y1="25" x2="210" y2="25" stroke="#0F172A" stroke-width="3"/>
                <line x1="30" y1="15" x2="30" y2="35" stroke="#0F172A" stroke-width="3"/>
                <line x1="210" y1="15" x2="210" y2="35" stroke="#0F172A" stroke-width="3"/>
                <text x="12" y="30" font-size="14" font-weight="bold" fill="#DC2626">A</text>
                <text x="220" y="30" font-size="14" font-weight="bold" fill="#DC2626">B</text>
                <text x="80" y="15" font-size="12" font-weight="bold" fill="#047857">Segment [AB]</text>
            </svg>

            <div class="cahier-ligne-texte" style="margin-top:20px;">✦ La demi-droite est limitée d'un seul côté par son origine :</div>
            <svg width="300" height="50">
                <line x1="30" y1="25" x2="210" y2="25" stroke="#0F172A" stroke-width="3"/>
                <line x1="30" y1="15" x2="30" y2="35" stroke="#0F172A" stroke-width="3"/>
                <polyline points="200,20 210,25 200,30" fill="none" stroke="#0F172A" stroke-width="3"/>
                <text x="12" y="30" font-size="14" font-weight="bold" fill="#DC2626">A</text>
                <text x="75" y="15" font-size="12" font-weight="bold" fill="#047857">Demi-droite [Ax)</text>
            </svg>

            <div class="cahier-ligne-texte" style="margin-top:20px;">✦ La droite n'a pas de limites :</div>
            <svg width="300" height="50">
                <line x1="10" y1="25" x2="230" y2="25" stroke="#0F172A" stroke-width="3" stroke-dasharray="6,4"/>
                <text x="90" y="15" font-size="12" font-weight="bold" fill="#047857">Droite (d)</text>
            </svg>
        </div>

        <div style="text-align:center;">
            <a href="/mathematiques/lecons/metrique" class="btn-retour">← Revenir au Système métrique</a>
        </div>
    """
    return afficher(html)

# =============================================================================
# EXERCICES DE MATHÉMATIQUES (ARITHMÉTIQUE, GÉOMÉTRIE, MÉTRIQUE)
# =============================================================================
@app.route("/mathematiques/exercices/arithmetique")
def page_exercices_arithmetique():
    html = """
        <div class="cadre-menu">
            <h1 class="titre-principal" id="titre-ex-arith">
                Exercices d'Arithmétique<br>
                <span class="sous-titre-selection" id="sous-titre-ex-arith">Choisissez un exercice</span>
            </h1>

            <button type="button" class="btn-rose btn-option" data-url="/mathematiques/exercices/arithmetique/comptage-10" data-titre="1-Compte de 1 en 1 de 0 à 10.">1-Compte de 1 en 1 de 0 à 10.</button>
            <button type="button" class="btn-rose btn-option" data-url="/mathematiques/exercices/arithmetique/comptage-49" data-titre="1-Compte de 1 en 1 de 30 à 49.">1-Compte de 1 en 1 de 30 à 49.</button>
            <button type="button" class="btn-rose btn-option" data-url="/mathematiques/exercices/arithmetique/ecris-lettres" data-titre="1-Ecris en lettres.">1-Ecris en lettres.</button>
            <button type="button" class="btn-rose btn-option" data-url="/mathematiques/exercices/arithmetique/comptage-75" data-titre="1-Compte de 1 en 1 de 55 à 75.">1-Compte de 1 en 1 de 55 à 75.</button>
            <button type="button" class="btn-rose btn-option" data-url="/mathematiques/exercices/arithmetique/pose-effectue" data-titre="1-Pose et effectue.">1-Pose et effectue.</button>
            <button type="button" class="btn-rose btn-option" data-url="/mathematiques/exercices/arithmetique/ecris" data-titre="1-Ecris">1-Ecris</button>

            <button type="button" id="btn-valider" class="btn-choose">➜ Choose</button>
            <a href="/mathematiques/exercices" class="btn-retour">← Revenir</a>
        </div>

        <script>
            let urlChoisie = "/mathematiques/exercices/arithmetique/comptage-10";
            const boutons = document.querySelectorAll('.btn-option');
            const sousTitre = document.getElementById('sous-titre-ex-arith');
            const btnValider = document.getElementById('btn-valider');

            boutons[0].classList.add('selected');
            sousTitre.textContent = boutons[0].getAttribute('data-titre');

            boutons.forEach(b => {
                b.addEventListener('click', () => {
                    boutons.forEach(x => x.classList.remove('selected'));
                    b.classList.add('selected');
                    urlChoisie = b.getAttribute('data-url');
                    sousTitre.textContent = b.getAttribute('data-titre');
                });
            });

            btnValider.addEventListener('click', () => {
                window.location.href = urlChoisie;
            });
        </script>
    """
    return afficher(html)

@app.route("/mathematiques/exercices/arithmetique/comptage-10")
def page_ex_comptage_10():
    html = """
        <div style="text-align:center;">
            <span class="badge-date">📅 Lundi 21 Septembre 2026</span>
            <div class="titre-lecon">✏️ Arithmétiques — Exercices</div>
        </div>
        <p style="font-weight:bold; color:#0D47A1; margin-bottom:6px;">1) Compte de 1 en 1 de 0 à 10 :</p>
        <div style="background:#fff; border:2px solid #80DEEA; border-radius:10px; padding:10px; text-align:center; font-size:15px; margin-bottom:12px;">
            0 - 1 - 2 - 3 - 4 - 5 - 6 - 7 - 8 - 9 - 10
        </div>
        <p style="font-weight:bold; color:#0D47A1; margin-bottom:6px;">2) Complète les pointillés :</p>
        <div style="background:#fff; border:2px solid #80DEEA; border-radius:10px; padding:10px; text-align:center; font-size:15px; margin-bottom:12px;">
            2 - 3 - 4 - 5 - 6 - 7 - <b style="color:red;">. . .</b> - 9 - 10
        </div>
        <p style="font-weight:bold; color:#0D47A1; margin-bottom:6px;">3) Dictée :</p>
        <div style="background:#fff; border:2px solid #80DEEA; border-radius:10px; padding:10px; color:#D81B60; font-weight:bold; text-align:center; font-size:15px;">
            9 - 2 - 10 - 3 - 8
        </div>
        <div style="text-align:center;">
            <a href="/mathematiques/exercices/arithmetique" class="btn-retour">← Revenir aux exercices d'Arithmétique</a>
        </div>
    """
    return afficher(html)

@app.route("/mathematiques/exercices/arithmetique/comptage-49")
def page_ex_comptage_49():
    html = """
        <div style="text-align:center;">
            <span class="badge-date">📅 Mardi 29 Septembre 2026</span>
            <div class="titre-lecon">✏️ Arithmétique — Exercices</div>
        </div>
        <p style="font-weight:bold; color:#0D47A1; margin-bottom:6px;">1) Compte de 1 en 1 de 30 à 49 :</p>
        <div style="background:#fff; border:2px solid #80DEEA; border-radius:10px; padding:10px; line-height:2; text-align:center; font-size:15px; margin-bottom:12px;">
            30 - 31 - 32 - 33 - 34 - 35 - 36 - 37 - 38<br>39 - 40 - 41 - 42 - 43 - 44 - 45 - 46 - 47<br>48 - 49
        </div>
        <p style="font-weight:bold; color:#0D47A1; margin-bottom:6px;">2) Écrire en lettre :</p>
        <div style="background:#fff; border:2px solid #80DEEA; border-radius:10px; padding:10px; font-size:15px; margin-bottom:12px;">
            1 = un &nbsp;&nbsp;|&nbsp;&nbsp; 5 = cinq<br>0 = zéro &nbsp;|&nbsp;&nbsp; 2 = deux
        </div>
        <p style="font-weight:bold; color:#0D47A1; margin-bottom:6px;">3) Dictée :</p>
        <div style="background:#fff; border:2px solid #80DEEA; border-radius:10px; padding:10px; color:#D81B60; font-weight:bold; text-align:center; font-size:15px;">
            42 - 18 - 30 - 5 - 44 - 25 - 3
        </div>
        <div style="text-align:center;">
            <a href="/mathematiques/exercices/arithmetique" class="btn-retour">← Revenir aux exercices d'Arithmétique</a>
        </div>
    """
    return afficher(html)

@app.route("/mathematiques/exercices/arithmetique/ecris-lettres")
def page_ex_ecris_lettres():
    html = """
        <div class="titre-lecon">✏️ Arithmétique — Écris en lettres</div>
        <p style="font-weight:bold; color:#0D47A1; margin-bottom:6px;">1) Écris en lettres :</p>
        <div style="background:#fff; border:2px solid #80DEEA; border-radius:10px; padding:10px; font-size:15px; line-height:2; margin-bottom:12px;">
            10 = dix &nbsp;&nbsp;|&nbsp;&nbsp; 8 = huit<br>2 = deux &nbsp;|&nbsp;&nbsp; 6 = six<br>5 = cinq
        </div>
        <p style="font-weight:bold; color:#0D47A1; margin-bottom:6px;">2) Pose et effectue :</p>
        <div style="background:#E1F5FE; border-radius:10px; padding:10px; font-family:monospace; font-size:16px; font-weight:bold; text-align:center;">
            7 + 2 = 9 &nbsp;&nbsp;|&nbsp;&nbsp; 23 + 15 = 38<br>11 + 8 = 19 &nbsp;|&nbsp;&nbsp; 34 + 14 = 48
        </div>
        <div style="text-align:center;">
            <a href="/mathematiques/exercices/arithmetique" class="btn-retour">← Revenir aux exercices d'Arithmétique</a>
        </div>
    """
    return afficher(html)

@app.route("/mathematiques/exercices/arithmetique/comptage-75")
def page_ex_comptage_75():
    html = """
        <div style="text-align:center;">
            <span class="badge-date">📅 Lundi 12 Octobre 2026</span>
            <div class="titre-lecon">✏️ Arithmétique — Exercices</div>
        </div>
        <p style="font-weight:bold; color:#0D47A1; margin-bottom:6px;">1) Compte de 1 en 1 de 55 à 75 :</p>
        <div style="background:#fff; border:2px solid #80DEEA; border-radius:10px; padding:10px; line-height:2; text-align:center; font-size:14px; margin-bottom:12px;">
            55 - 56 - 57 - 58 - 59 - 60 - 61 - 62 - 63 - 64<br>65 - 66 - 67 - 68 - 69 - 70 - 71 - 72 - 73 - 74 - 75
        </div>
        <p style="font-weight:bold; color:#0D47A1; margin-bottom:6px;">2) Décompose :</p>
        <div style="background:#fff; border:2px solid #80DEEA; border-radius:10px; padding:10px; color:#B71C1C; font-weight:bold; font-size:15px; margin-bottom:12px;">
            24 = 2 d 4 u &nbsp;&nbsp;|&nbsp;&nbsp; 67 = 6 d 7 u<br>3 = 3 u &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp; 15 = 1 d 5 u
        </div>
        <p style="font-weight:bold; color:#0D47A1; margin-bottom:6px;">3) Pose et effectue :</p>
        <div style="background:#E1F5FE; border-radius:10px; padding:10px; font-family:monospace; font-size:16px; font-weight:bold; text-align:center;">
            46 + 23 = 69 &nbsp;|&nbsp; 23 + 2 = 25<br>50 + 49 = 99 &nbsp;|&nbsp; 18 + 21 = 39
        </div>
        <div style="text-align:center;">
            <a href="/mathematiques/exercices/arithmetique" class="btn-retour">← Revenir aux exercices d'Arithmétique</a>
        </div>
    """
    return afficher(html)

@app.route("/mathematiques/exercices/arithmetique/pose-effectue")
def page_ex_pose_effectue():
    html = """
        <div style="text-align:center;">
            <span class="badge-date">📅 Mercredi 21 Octobre 2026</span>
            <div class="titre-lecon">✏️ Arithmétique — Pose et Effectue (Avec retenue)</div>
        </div>
        <div style="background:#E1F5FE; border-radius:10px; padding:12px; font-family:monospace; font-size:16px; font-weight:bold; text-align:center; margin-bottom:12px;">
            54 + 16 = 70 &nbsp;|&nbsp; 28 + 35 = 63<br>46 + 26 = 72 &nbsp;|&nbsp; 12 + 5 = 17<br>36 + 28 = 64 &nbsp;|&nbsp; 33 + 15 = 48
        </div>
        <p style="font-weight:bold; color:#0D47A1; margin-bottom:6px;">2) Décompose :</p>
        <div style="background:#fff; border:2px solid #80DEEA; border-radius:10px; padding:10px; color:#B71C1C; font-weight:bold; font-size:15px;">
            57 = 5 d 7 u &nbsp;&nbsp;|&nbsp;&nbsp; 8 = 8 u &nbsp;&nbsp;|&nbsp;&nbsp; 62 = 6 d 2 u
        </div>
        <div style="text-align:center;">
            <a href="/mathematiques/exercices/arithmetique" class="btn-retour">← Revenir aux exercices d'Arithmétique</a>
        </div>
    """
    return afficher(html)

@app.route("/mathematiques/exercices/arithmetique/ecris")
def page_ex_arith_ecris():
    html = """
        <div style="text-align:center;">
            <span class="badge-date">📅 Lundi 26 Octobre 2026</span>
            <div class="titre-lecon">✏️ Arithmétique — Écris & Décompose</div>
        </div>

        <p style="font-weight:bold; color:#0D47A1; margin-bottom:6px;">1) Écris en lettres :</p>
        <div style="background:#fff; border:2px solid #80DEEA; border-radius:10px; padding:10px; font-size:15px; font-weight:bold; line-height:2.2; margin-bottom:12px;">
            ✦ <b>6</b> = six<br>
            ✦ <b>8</b> = huit<br>
            ✦ <b>0</b> = zéro<br>
            ✦ <b>10</b> = dix
        </div>

        <p style="font-weight:bold; color:#0D47A1; margin-bottom:6px;">2) Compte de 1 en 1 de 87 à 107 :</p>
        <div style="background:#F0F9FF; border:2px dashed #0284C7; border-radius:10px; padding:10px; font-size:13px; font-weight:bold; color:#0369A1; line-height:2; text-align:center; margin-bottom:12px;">
            87 - 88 - 89 - 90 - 91 - 92 - 93 - 94 - 95 - 96 - 97 - 98 - 99 - 100 - 101 - 102 - 103 - 104 - 105 - 106 - 107.
        </div>

        <p style="font-weight:bold; color:#0D47A1; margin-bottom:6px;">3) Décompose :</p>
        <div style="background:#fff; border:2px solid #80DEEA; border-radius:10px; padding:10px; font-size:15px; font-weight:bold; line-height:2.2;">
            ✦ 85 = <b style="color:#D81B60;">8 d 5 u</b><br>
            ✦ 92 = <b style="color:#D81B60;">9 d 2 u</b><br>
            ✦ 5 &nbsp;= <b style="color:#D81B60;">5 u</b><br>
            ✦ 113 = <b style="color:#D81B60;">1 c 1 d 3 u</b><br>
            ✦ 7 &nbsp;= <b style="color:#D81B60;">7 u</b><br>
            ✦ 119 = <b style="color:#D81B60;">1 c 1 d 9 u</b>
        </div>
        <div style="text-align:center;">
            <a href="/mathematiques/exercices/arithmetique" class="btn-retour">← Revenir aux exercices d'Arithmétique</a>
        </div>
    """
    return afficher(html)

@app.route("/mathematiques/exercices/geometrie")
def page_exercices_geometrie():
    html = """
        <div class="cadre-menu">
            <h1 class="titre-principal" id="titre-ex-geo">
                Exercices de Géométrie<br>
                <span class="sous-titre-selection" id="sous-titre-ex-geo">Choisissez un exercice</span>
            </h1>

            <button type="button" class="btn-rose btn-option" data-url="/mathematiques/exercices/geometrie/ligne-6cm" data-titre="1-Trace une ligne droite horizontale de 6cm.">1-Trace une ligne droite horizontale de 6cm.</button>
            <button type="button" class="btn-rose btn-option" data-url="/mathematiques/exercices/geometrie/souligne" data-titre="1-Souligne la bonne réponse.">1-Souligne la bonne réponse.</button>

            <button type="button" id="btn-valider" class="btn-choose">➜ Choose</button>
            <a href="/mathematiques/exercices" class="btn-retour">← Revenir</a>
        </div>

        <script>
            let urlChoisie = "/mathematiques/exercices/geometrie/ligne-6cm";
            const boutons = document.querySelectorAll('.btn-option');
            const sousTitre = document.getElementById('sous-titre-ex-geo');
            const btnValider = document.getElementById('btn-valider');

            boutons[0].classList.add('selected');
            sousTitre.textContent = boutons[0].getAttribute('data-titre');

            boutons.forEach(b => {
                b.addEventListener('click', () => {
                    boutons.forEach(x => x.classList.remove('selected'));
                    b.classList.add('selected');
                    urlChoisie = b.getAttribute('data-url');
                    sousTitre.textContent = b.getAttribute('data-titre');
                });
            });

            btnValider.addEventListener('click', () => {
                window.location.href = urlChoisie;
            });
        </script>
    """
    return afficher(html)

@app.route("/mathematiques/exercices/geometrie/ligne-6cm")
def page_ex_geo_ligne_6cm():
    html = """
        <div class="titre-lecon">✏️ Géométrie — Lignes de 6 cm et 4 cm</div>

        <div class="cahier-seyes">
            <div class="cahier-ligne-texte">1) Trace une ligne droite horizontale de 6 cm :</div>
            <svg width="260" height="50">
                <line x1="20" y1="20" x2="188" y2="20" stroke="#1E3A8A" stroke-width="3"/>
                <text x="90" y="14" font-size="12" font-weight="bold" fill="#047857">6 cm</text>
            </svg>

            <div class="cahier-ligne-texte" style="margin-top:16px;">2) Trace une ligne droite verticale de 4 cm :</div>
            <svg width="200" height="140">
                <line x1="50" y1="10" x2="50" y2="122" stroke="#1E3A8A" stroke-width="3"/>
                <text x="60" y="70" font-size="12" font-weight="bold" fill="#047857">4 cm</text>
            </svg>
        </div>

        <div style="text-align:center;">
            <a href="/mathematiques/exercices/geometrie" class="btn-retour">← Revenir aux exercices de Géométrie</a>
        </div>
    """
    return afficher(html)

@app.route("/mathematiques/exercices/geometrie/souligne")
def page_ex_geo_souligne():
    html = """
        <div style="text-align:center;">
            <span class="badge-date">📅 Mercredi 14 Octobre 2026</span>
            <div class="titre-lecon">✏️ Géométrie — Souligne la bonne réponse & Tracés</div>
        </div>

        <div class="cahier-seyes">
            <div class="cahier-ligne-texte">1) Souligne la bonne réponse :</div>
            <div style="font-size:15px; line-height:2.2; margin-bottom:15px;">
                - 2 sortes de lignes<br>
                - 6 sortes de lignes<br>
                - <b style="color:#16A34A; text-decoration:underline;">5 sortes de lignes</b> ✓ (Bonne réponse)
            </div>

            <div class="cahier-ligne-texte">2) Trace une ligne droite horizontale :</div>
            <svg width="260" height="40"><line x1="20" y1="20" x2="188" y2="20" stroke="#0284C7" stroke-width="3"/><text x="60" y="14" font-size="12" font-weight="bold" fill="#047857">Ligne horizontale</text></svg>

            <div class="cahier-ligne-texte" style="margin-top:12px;">3) Trace une ligne droite oblique :</div>
            <svg width="260" height="60"><line x1="20" y1="50" x2="160" y2="15" stroke="#0284C7" stroke-width="3"/><text x="60" y="25" font-size="12" font-weight="bold" fill="#047857">Ligne oblique</text></svg>

            <div class="cahier-ligne-texte" style="margin-top:12px;">4) Trace une ligne verticale :</div>
            <svg width="200" height="130"><line x1="50" y1="10" x2="50" y2="122" stroke="#0284C7" stroke-width="3"/><text x="60" y="65" font-size="12" font-weight="bold" fill="#047857">Ligne verticale</text></svg>
        </div>

        <div style="text-align:center;">
            <a href="/mathematiques/exercices/geometrie" class="btn-retour">← Revenir aux exercices de Géométrie</a>
        </div>
    """
    return afficher(html)

@app.route("/mathematiques/exercices/metrique")
def page_exercices_metrique():
    html = """
        <div class="cadre-menu">
            <h1 class="titre-principal" id="titre-ex-met">
                Exercices Système Métrique<br>
                <span class="sous-titre-selection" id="sous-titre-ex-met">Choisissez un exercice</span>
            </h1>

            <button type="button" class="btn-rose btn-option" data-url="/mathematiques/exercices/metrique/ligne-horiz" data-titre="1-Trace une ligne horizontale.">1-Trace une ligne horizontale.</button>
            <button type="button" class="btn-rose btn-option" data-url="/mathematiques/exercices/metrique/ligne-7cm" data-titre="1-Trace une ligne horizontale de 7cm.">1-Trace une ligne horizontale de 7cm.</button>
            <button type="button" class="btn-rose btn-option" data-url="/mathematiques/exercices/metrique/segment-ab" data-titre="1-Trace le segment [AB].">1-Trace le segment [AB].</button>
            <button type="button" class="btn-rose btn-option" data-url="/mathematiques/exercices/metrique/demi-droite" data-titre="1-Trace un demi droite.">1-Trace un demi droite.</button>
            <button type="button" class="btn-rose btn-option" data-url="/mathematiques/exercices/metrique/ij-4cm" data-titre="1-Trace [IJ] = 4cm.">1-Trace [IJ] = 4cm.</button>
            <button type="button" class="btn-rose btn-option" data-url="/mathematiques/exercices/metrique/segment-ab-6cm" data-titre="1-Trace un segment [AB] de 6 cm.">1-Trace un segment [AB] de 6 cm.</button>

            <button type="button" id="btn-valider" class="btn-choose">➜ Choose</button>
            <a href="/mathematiques/exercices" class="btn-retour">← Revenir</a>
        </div>

        <script>
            let urlChoisie = "/mathematiques/exercices/metrique/ligne-horiz";
            const boutons = document.querySelectorAll('.btn-option');
            const sousTitre = document.getElementById('sous-titre-ex-met');
            const btnValider = document.getElementById('btn-valider');

            boutons[0].classList.add('selected');
            sousTitre.textContent = boutons[0].getAttribute('data-titre');

            boutons.forEach(b => {
                b.addEventListener('click', () => {
                    boutons.forEach(x => x.classList.remove('selected'));
                    b.classList.add('selected');
                    urlChoisie = b.getAttribute('data-url');
                    sousTitre.textContent = b.getAttribute('data-titre');
                });
            });

            btnValider.addEventListener('click', () => {
                window.location.href = urlChoisie;
            });
        </script>
    """
    return afficher(html)

@app.route("/mathematiques/exercices/metrique/ligne-horiz")
def page_ex_met_ligne_horiz():
    html = """
        <div style="text-align:center;">
            <span class="badge-date">📅 Mardi 22 Septembre 2026</span>
            <div class="titre-lecon">✏️ Système Métrique — Lignes 5 cm, 8 cm, 3 cm</div>
        </div>

        <div class="cahier-seyes">
            <div class="cahier-ligne-texte">1) Ligne horizontale de 5 cm :</div>
            <svg width="220" height="40"><line x1="20" y1="20" x2="160" y2="20" stroke="#1E3A8A" stroke-width="3"/><text x="75" y="14" font-size="12" font-weight="bold" fill="#047857">5 cm</text></svg>

            <div class="cahier-ligne-texte" style="margin-top:16px;">2) Ligne verticale de 8 cm :</div>
            <svg width="180" height="240"><line x1="50" y1="10" x2="50" y2="234" stroke="#1E3A8A" stroke-width="3"/><text x="60" y="120" font-size="12" font-weight="bold" fill="#047857">8 cm</text></svg>

            <div class="cahier-ligne-texte" style="margin-top:16px;">3) Ligne oblique de 3 cm :</div>
            <svg width="200" height="60"><line x1="20" y1="45" x2="104" y2="15" stroke="#1E3A8A" stroke-width="3"/><text x="45" y="25" font-size="12" font-weight="bold" fill="#047857">3 cm</text></svg>
        </div>

        <div style="text-align:center;">
            <a href="/mathematiques/exercices/metrique" class="btn-retour">← Revenir aux exercices de Système Métrique</a>
        </div>
    """
    return afficher(html)

@app.route("/mathematiques/exercices/metrique/ligne-7cm")
def page_ex_met_ligne_7cm():
    html = """
        <div style="text-align:center;">
            <span class="badge-date">📅 Lundi 29 Septembre 2026</span>
            <div class="titre-lecon">✏️ Système Métrique — Ligne horizontale 7 cm, verticale 4 cm, oblique 5 cm</div>
        </div>

        <div class="cahier-seyes">
            <div class="cahier-ligne-texte">1) Ligne horizontale de 7 cm :</div>
            <svg width="260" height="40"><line x1="20" y1="20" x2="216" y2="20" stroke="#0F172A" stroke-width="3"/><text x="100" y="14" font-size="12" font-weight="bold" fill="#047857">7 cm</text></svg>

            <div class="cahier-ligne-texte" style="margin-top:16px;">2) Ligne verticale de 4 cm :</div>
            <svg width="180" height="140"><line x1="50" y1="10" x2="50" y2="122" stroke="#0F172A" stroke-width="3"/><text x="60" y="70" font-size="12" font-weight="bold" fill="#047857">4 cm</text></svg>

            <div class="cahier-ligne-texte" style="margin-top:16px;">3) Ligne oblique de 5 cm :</div>
            <svg width="220" height="80"><line x1="20" y1="65" x2="160" y2="15" stroke="#0F172A" stroke-width="3"/><text x="75" y="32" font-size="12" font-weight="bold" fill="#047857">5 cm</text></svg>
        </div>

        <div style="text-align:center;">
            <a href="/mathematiques/exercices/metrique" class="btn-retour">← Revenir aux exercices de Système Métrique</a>
        </div>
    """
    return afficher(html)

@app.route("/mathematiques/exercices/metrique/segment-ab")
def page_ex_met_segment_ab():
    html = """
        <div style="text-align:center;">
            <span class="badge-date">📅 Jeudi 08 Octobre 2026</span>
            <div class="titre-lecon">✏️ Système Métrique — Trace les segments [AB], [DE], [AC], [FH]</div>
        </div>

        <div class="cahier-seyes">
            <div class="cahier-ligne-texte">1) Trace les segments en ligne horizontale :</div>

            <svg width="300" height="45">
                <line x1="30" y1="20" x2="170" y2="20" stroke="#1E3A8A" stroke-width="3"/>
                <line x1="30" y1="10" x2="30" y2="30" stroke="#1E3A8A" stroke-width="3"/>
                <line x1="170" y1="10" x2="170" y2="30" stroke="#1E3A8A" stroke-width="3"/>
                <text x="12" y="25" font-size="14" font-weight="bold" fill="#DC2626">A</text>
                <text x="180" y="25" font-size="14" font-weight="bold" fill="#DC2626">B</text>
                <text x="65" y="12" font-size="12" font-weight="bold" fill="#047857">[AB] = 5 cm</text>
            </svg>

            <svg width="300" height="45" style="margin-top:10px;">
                <line x1="30" y1="20" x2="226" y2="20" stroke="#1E3A8A" stroke-width="3"/>
                <line x1="30" y1="10" x2="30" y2="30" stroke="#1E3A8A" stroke-width="3"/>
                <line x1="226" y1="10" x2="226" y2="30" stroke="#1E3A8A" stroke-width="3"/>
                <text x="12" y="25" font-size="14" font-weight="bold" fill="#DC2626">D</text>
                <text x="236" y="25" font-size="14" font-weight="bold" fill="#DC2626">E</text>
                <text x="90" y="12" font-size="12" font-weight="bold" fill="#047857">[DE] = 7 cm</text>
            </svg>

            <svg width="300" height="45" style="margin-top:10px;">
                <line x1="30" y1="20" x2="114" y2="20" stroke="#1E3A8A" stroke-width="3"/>
                <line x1="30" y1="10" x2="30" y2="30" stroke="#1E3A8A" stroke-width="3"/>
                <line x1="114" y1="10" x2="114" y2="30" stroke="#1E3A8A" stroke-width="3"/>
                <text x="12" y="25" font-size="14" font-weight="bold" fill="#DC2626">A</text>
                <text x="124" y="25" font-size="14" font-weight="bold" fill="#DC2626">C</text>
                <text x="45" y="12" font-size="12" font-weight="bold" fill="#047857">[AC] = 3 cm</text>
            </svg>

            <svg width="300" height="45" style="margin-top:10px;">
                <line x1="30" y1="20" x2="254" y2="20" stroke="#1E3A8A" stroke-width="3"/>
                <line x1="30" y1="10" x2="30" y2="30" stroke="#1E3A8A" stroke-width="3"/>
                <line x1="254" y1="10" x2="254" y2="30" stroke="#1E3A8A" stroke-width="3"/>
                <text x="12" y="25" font-size="14" font-weight="bold" fill="#DC2626">F</text>
                <text x="264" y="25" font-size="14" font-weight="bold" fill="#DC2626">H</text>
                <text x="110" y="12" font-size="12" font-weight="bold" fill="#047857">[FH] = 8 cm</text>
            </svg>
        </div>

        <div style="text-align:center;">
            <a href="/mathematiques/exercices/metrique" class="btn-retour">← Revenir aux exercices de Système Métrique</a>
        </div>
    """
    return afficher(html)

@app.route("/mathematiques/exercices/metrique/demi-droite")
def page_ex_met_demi_droite():
    html = """
        <div style="text-align:center;">
            <span class="badge-date">📅 Mardi 13 Octobre 2026</span>
            <div class="titre-lecon">✏️ Système Métrique — Tracé de Segments et Demi-droites</div>
        </div>

        <div class="cahier-seyes">
            <div class="cahier-ligne-texte">1) Trace la demi-droite [CD[ = 3 cm en ligne horizontale :</div>
            <svg width="220" height="40">
                <line x1="30" y1="20" x2="114" y2="20" stroke="#1E3A8A" stroke-width="3"/>
                <line x1="30" y1="10" x2="30" y2="30" stroke="#1E3A8A" stroke-width="3"/>
                <polyline points="106,15 114,20 106,25" fill="none" stroke="#1E3A8A" stroke-width="3"/>
                <text x="12" y="25" font-size="14" font-weight="bold" fill="#DC2626">C</text>
                <text x="122" y="25" font-size="14" font-weight="bold" fill="#DC2626">D</text>
                <text x="50" y="12" font-size="12" font-weight="bold" fill="#047857">3 cm</text>
            </svg>

            <div class="cahier-ligne-texte" style="margin-top:16px;">2) Trace [HD] = 6 cm en ligne verticale :</div>
            <svg width="180" height="190">
                <line x1="50" y1="15" x2="50" y2="183" stroke="#1E3A8A" stroke-width="3"/>
                <line x1="42" y1="15" x2="58" y2="15" stroke="#1E3A8A" stroke-width="3"/>
                <line x1="42" y1="183" x2="58" y2="183" stroke="#1E3A8A" stroke-width="3"/>
                <text x="45" y="10" font-size="14" font-weight="bold" fill="#DC2626">H</text>
                <text x="45" y="198" font-size="14" font-weight="bold" fill="#DC2626">D</text>
                <text x="60" y="100" font-size="12" font-weight="bold" fill="#047857">6 cm</text>
            </svg>

            <div class="cahier-ligne-texte" style="margin-top:16px;">3) Trace [EF] en ligne oblique de 4 cm :</div>
            <svg width="220" height="70">
                <line x1="30" y1="55" x2="142" y2="15" stroke="#1E3A8A" stroke-width="3"/>
                <line x1="24" y1="50" x2="36" y2="60" stroke="#1E3A8A" stroke-width="3"/>
                <line x1="136" y1="10" x2="148" y2="20" stroke="#1E3A8A" stroke-width="3"/>
                <text x="12" y="65" font-size="14" font-weight="bold" fill="#DC2626">E</text>
                <text x="150" y="15" font-size="14" font-weight="bold" fill="#DC2626">F</text>
                <text x="70" y="28" font-size="12" font-weight="bold" fill="#047857">4 cm</text>
            </svg>
        </div>

        <div style="text-align:center;">
            <a href="/mathematiques/exercices/metrique" class="btn-retour">← Revenir aux exercices de Système Métrique</a>
        </div>
    """
    return afficher(html)

@app.route("/mathematiques/exercices/metrique/ij-4cm")
def page_ex_met_ij_4cm():
    html = """
        <div style="text-align:center;">
            <span class="badge-date">📅 Vendredi 16 Octobre 2026</span>
            <div class="titre-lecon">✏️ Système Métrique — Segments [IJ] = 4cm, [AC] = 7cm, [EP] = 5cm</div>
        </div>

        <div class="cahier-seyes">
            <div class="cahier-ligne-texte">1) Trace [IJ] = 4 cm en ligne verticale :</div>
            <svg width="180" height="140">
                <line x1="50" y1="15" x2="50" y2="127" stroke="#1E3A8A" stroke-width="3"/>
                <line x1="42" y1="15" x2="58" y2="15" stroke="#1E3A8A" stroke-width="3"/>
                <line x1="42" y1="127" x2="58" y2="127" stroke="#1E3A8A" stroke-width="3"/>
                <text x="47" y="10" font-size="14" font-weight="bold" fill="#DC2626">I</text>
                <text x="47" y="142" font-size="14" font-weight="bold" fill="#DC2626">J</text>
                <text x="60" y="70" font-size="12" font-weight="bold" fill="#047857">4 cm</text>
            </svg>

            <div class="cahier-ligne-texte" style="margin-top:16px;">2) Trace [AC] = 7 cm en ligne oblique :</div>
            <svg width="260" height="100">
                <line x1="30" y1="85" x2="226" y2="15" stroke="#1E3A8A" stroke-width="3"/>
                <line x1="24" y1="80" x2="36" y2="90" stroke="#1E3A8A" stroke-width="3"/>
                <line x1="220" y1="10" x2="232" y2="20" stroke="#1E3A8A" stroke-width="3"/>
                <text x="12" y="95" font-size="14" font-weight="bold" fill="#DC2626">A</text>
                <text x="234" y="15" font-size="14" font-weight="bold" fill="#DC2626">C</text>
                <text x="115" y="42" font-size="12" font-weight="bold" fill="#047857">7 cm</text>
            </svg>

            <div class="cahier-ligne-texte" style="margin-top:16px;">3) Trace [EP] = 5 cm en ligne horizontale :</div>
            <svg width="220" height="45">
                <line x1="30" y1="20" x2="170" y2="20" stroke="#1E3A8A" stroke-width="3"/>
                <line x1="30" y1="10" x2="30" y2="30" stroke="#1E3A8A" stroke-width="3"/>
                <line x1="170" y1="10" x2="170" y2="30" stroke="#1E3A8A" stroke-width="3"/>
                <text x="12" y="25" font-size="14" font-weight="bold" fill="#DC2626">E</text>
                <text x="180" y="25" font-size="14" font-weight="bold" fill="#DC2626">P</text>
                <text x="75" y="12" font-size="12" font-weight="bold" fill="#047857">5 cm</text>
            </svg>
        </div>

        <div style="text-align:center;">
            <a href="/mathematiques/exercices/metrique" class="btn-retour">← Revenir aux exercices de Système Métrique</a>
        </div>
    """
    return afficher(html)

@app.route("/mathematiques/exercices/metrique/segment-ab-6cm")
def page_ex_met_segment_ab_6cm():
    html = """
        <div style="text-align:center;">
            <span class="badge-date">📅 Jeudi 29 Octobre 2026</span>
            <div class="titre-lecon">✏️ Système Métrique — Segments et demi-droite ([AB]=6cm, [BC)=4cm, [CD]=7cm)</div>
        </div>

        <div class="cahier-seyes">
            <div class="cahier-ligne-texte">1) Trace un segment [AB] = 6 cm en ligne oblique :</div>
            <svg width="240" height="90">
                <line x1="30" y1="75" x2="198" y2="15" stroke="#1E3A8A" stroke-width="3"/>
                <line x1="24" y1="70" x2="36" y2="80" stroke="#1E3A8A" stroke-width="3"/>
                <line x1="192" y1="10" x2="204" y2="20" stroke="#1E3A8A" stroke-width="3"/>
                <text x="12" y="85" font-size="14" font-weight="bold" fill="#DC2626">B</text>
                <text x="206" y="15" font-size="14" font-weight="bold" fill="#DC2626">A</text>
                <text x="100" y="38" font-size="12" font-weight="bold" fill="#047857">6 cm</text>
            </svg>

            <div class="cahier-ligne-texte" style="margin-top:16px;">2) Traces une demi-droite [BC) = 4 cm en ligne verticale :</div>
            <svg width="180" height="140">
                <line x1="50" y1="15" x2="50" y2="127" stroke="#1E3A8A" stroke-width="3"/>
                <line x1="42" y1="15" x2="58" y2="15" stroke="#1E3A8A" stroke-width="3"/>
                <polyline points="45,120 50,127 55,120" fill="none" stroke="#1E3A8A" stroke-width="3"/>
                <text x="47" y="10" font-size="14" font-weight="bold" fill="#DC2626">B</text>
                <text x="47" y="142" font-size="14" font-weight="bold" fill="#DC2626">C</text>
                <text x="60" y="70" font-size="12" font-weight="bold" fill="#047857">4 cm</text>
            </svg>

            <div class="cahier-ligne-texte" style="margin-top:16px;">3) Traces un segment [CD] = 7 cm en ligne horizontale :</div>
            <svg width="280" height="45">
                <line x1="30" y1="20" x2="226" y2="20" stroke="#1E3A8A" stroke-width="3"/>
                <line x1="30" y1="10" x2="30" y2="30" stroke="#1E3A8A" stroke-width="3"/>
                <line x1="226" y1="10" x2="226" y2="30" stroke="#1E3A8A" stroke-width="3"/>
                <text x="12" y="25" font-size="14" font-weight="bold" fill="#DC2626">C</text>
                <text x="236" y="25" font-size="14" font-weight="bold" fill="#DC2626">D</text>
                <text x="110" y="12" font-size="12" font-weight="bold" fill="#047857">7 cm</text>
            </svg>
        </div>

        <div style="text-align:center;">
            <a href="/mathematiques/exercices/metrique" class="btn-retour">← Revenir aux exercices de Système Métrique</a>
        </div>
    """
    return afficher(html)

# =============================================================================
# POINT D'ENTRÉE DU SERVEUR FLASK
# =============================================================================
if __name__ == "__main__":
    print("Application Flask lancée avec succès : http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)
