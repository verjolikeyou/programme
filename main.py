
import os
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QSize, QPointF, QRectF
from PySide6.QtGui import (
    QMovie,
    QPainter,
    QPen,
    QColor,
    QFont,
    QBrush,
    QPainterPath,
    QPixmap,
    QImage,
)
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QCommandLinkButton,
    QMessageBox,
    QButtonGroup,
    QStackedWidget,
    QSizePolicy,
    QFrame,
    QScrollArea,
    QTextBrowser,
)

# Support optionnel mais direct de QtPdf pour PySide6
try:
    from PySide6.QtPdf import QPdfDocument
    HAS_QTPDF = True
except Exception:
    HAS_QTPDF = False


def dossier_application():
    """Dossier contenant le script ou l'exécutable."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def chemin_ressource(nom_fichier):
    """
    Cherche d'abord à côté du programme (mode .py / .exe),
    puis dans le dossier temporaire PyInstaller (_MEIPASS).
    """
    candidats = [dossier_application() / nom_fichier]
    dossier_temp = getattr(sys, "_MEIPASS", None)
    if dossier_temp:
        candidats.append(Path(dossier_temp) / nom_fichier)

    for chemin in candidats:
        if chemin.is_file():
            return chemin
    return None


def charger_pages_pdf_ou_images(mots_cles, largeur_max=850, nom_pdf=None):
    """
    Convertit les pages d'un PDF en QPixmap pour les afficher dans
    le QScrollArea. Les PDF fournis sont sélectionnés par leur nom exact :
      - carot.pdf       -> dessin de la carotte
      - school bag.pdf  -> dessin du cartable

    PyMuPDF (fitz) est essayé en premier, puis QtPdf en secours.
    """
    pixmaps = []
    dossier = dossier_application()

    # Sélection exacte du PDF demandé : évite de prendre le mauvais document.
    fichiers_pdf = []
    if nom_pdf:
        chemin = chemin_ressource(nom_pdf)
        if chemin:
            fichiers_pdf = [chemin]
    else:
        for f in dossier.glob("*.pdf"):
            nom = f.name.lower()
            if any(mc.lower() in nom for mc in mots_cles):
                fichiers_pdf.append(f)

    # Méthode prioritaire : PyMuPDF. Copie des pixels indispensable pour
    # éviter que QImage conserve une référence vers la mémoire de fitz.
    if fichiers_pdf:
        try:
            import fitz
            for pdf_path in fichiers_pdf:
                with fitz.open(str(pdf_path)) as doc:
                    for page in doc:
                        rect = page.rect
                        facteur = min(largeur_max / max(1.0, rect.width), 2.0)
                        pix = page.get_pixmap(
                            matrix=fitz.Matrix(facteur, facteur),
                            alpha=False
                        )
                        if pix.n == 4:
                            fmt = QImage.Format.Format_RGBA8888
                        else:
                            fmt = QImage.Format.Format_RGB888
                        image = QImage(
                            pix.samples, pix.width, pix.height, pix.stride, fmt
                        ).copy()
                        if not image.isNull():
                            pixmaps.append(QPixmap.fromImage(image))
        except Exception as erreur:
            print(f"PyMuPDF n'a pas pu lire le PDF : {erreur}")
            pixmaps.clear()

    # Secours : QtPdf, si le module est disponible dans cette installation.
    if not pixmaps and fichiers_pdf and HAS_QTPDF:
        for pdf_path in fichiers_pdf:
            try:
                doc = QPdfDocument()
                doc.load(str(pdf_path))
                for page_idx in range(doc.pageCount()):
                    page_size = doc.pagePointSize(page_idx)
                    facteur = largeur_max / max(1.0, page_size.width())
                    taille = QSize(
                        largeur_max,
                        max(1, int(page_size.height() * facteur))
                    )
                    image = doc.render(page_idx, taille)
                    if not image.isNull():
                        pixmaps.append(QPixmap.fromImage(image))
            except Exception as erreur:
                print(f"QtPdf n'a pas pu lire {pdf_path}: {erreur}")

    # Images associées : conservées pour ne pas supprimer l'ancien usage.
    for ext in ("*.png", "*.jpg", "*.jpeg"):
        for f in dossier.glob(ext):
            nom = f.name.lower()
            if any(mc.lower() in nom for mc in mots_cles):
                image = QPixmap(str(f))
                if not image.isNull():
                    if image.width() > largeur_max:
                        image = image.scaledToWidth(
                            largeur_max,
                            Qt.TransformationMode.SmoothTransformation
                        )
                    pixmaps.append(image)

    return pixmaps


# =============================================================================
# WIDGET DÉCORÉ SUR LES CÔTÉS POUR LES DESSINS ET PDF
# =============================================================================
class RubanDecoratifCote(QWidget):
    """Ruban festif vertical sur les côtés avec des crayons, étoiles et gommes."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(45)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        hauteur = self.height()

        # Fond dégradé pastel doux
        painter.fillRect(0, 0, self.width(), hauteur, QColor("#FFF0F5"))

        # Motifs verticaux répétitifs
        icones = ["✏️", "⭐", "🎨", "🌟", "🖍️", "✨", "📐", "🌸", "🎒", "🥕", "✂️"]
        painter.setFont(QFont("Segoe UI Emoji", 15))
        y = 30
        idx = 0
        while y < hauteur - 20:
            painter.drawText(QRectF(0, y, self.width(), 30), Qt.AlignmentFlag.AlignCenter, icones[idx % len(icones)])
            y += 48
            idx += 1


# =============================================================================
# WIDGET CAHIER D'ÉCOLIER (QUADRILLAGE SÉYÈS & TRACÉS GÉOMÉTRIQUES RÉELS)
# =============================================================================
class CahierDessinWidget(QWidget):
    """
    Dessine une feuille de cahier d'écolier avec carreaux (Séyès),
    marge rouge à gauche, et trace fidèlement les figures géométriques.
    """
    def __init__(self, elements, parent=None, hauteur_min=500):
        super().__init__(parent)
        self.elements = elements
        self.setMinimumHeight(hauteur_min)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        largeur = self.width()
        hauteur = self.height()

        # 1. Fond du papier (blanc d'écolier)
        painter.fillRect(0, 0, largeur, hauteur, QColor("#FFFFFF"))

        # 2. Quadrillage Séyès (carreaux d'écolier 22x22 px)
        taille_carreau = 22
        pen_quadrillage = QPen(QColor("#E2E8F0"), 1)
        painter.setPen(pen_quadrillage)

        x = 0
        while x < largeur:
            painter.drawLine(x, 0, x, hauteur)
            x += taille_carreau

        y = 0
        while y < hauteur:
            painter.drawLine(0, y, largeur, y)
            y += taille_carreau

        # 3. Ligne de marge rouge
        x_marge = 66
        pen_marge = QPen(QColor("#EF4444"), 2)
        painter.setPen(pen_marge)
        painter.drawLine(x_marge, 0, x_marge, hauteur)

        # 4. Tracé des figures géométriques
        x_debut = x_marge + 26
        curseur_y = 28
        facteur_cm = 28.0

        for el in self.elements:
            type_el = el.get("type", "texte")

            if type_el == "texte_enonce":
                painter.setPen(QPen(QColor("#1E3A8A"), 2))
                painter.setFont(QFont("Comic Sans MS", 12, QFont.Weight.Bold))
                painter.drawText(x_debut, curseur_y + 14, el.get("texte", ""))
                curseur_y += 38

            elif type_el == "souligne_reponse":
                painter.setFont(QFont("Comic Sans MS", 11, QFont.Weight.Normal))
                options = el.get("options", [])
                bonne = el.get("bonne", 2)
                for i, opt in enumerate(options):
                    if i == bonne:
                        painter.setPen(QPen(QColor("#16A34A"), 2))
                        painter.setFont(QFont("Comic Sans MS", 11, QFont.Weight.Bold))
                        painter.drawText(x_debut + 20, curseur_y + 14, f"- {opt}  ✓ (Bonne réponse)")
                        fm = painter.fontMetrics()
                        w = fm.horizontalAdvance(f"- {opt}")
                        painter.drawLine(x_debut + 20, curseur_y + 18, x_debut + 20 + w, curseur_y + 18)
                    else:
                        painter.setPen(QPen(QColor("#475569"), 1))
                        painter.setFont(QFont("Comic Sans MS", 11, QFont.Weight.Normal))
                        painter.drawText(x_debut + 20, curseur_y + 14, f"- {opt}")
                    curseur_y += 26
                curseur_y += 12

            elif type_el == "geometrie":
                genre = el.get("genre", "segment")
                orientation = el.get("orientation", "horizontale")
                cm = el.get("cm", 5)
                longueur_px = cm * facteur_cm
                lettre1 = el.get("p1", "")
                lettre2 = el.get("p2", "")
                annotation = el.get("mesure", f"{cm} cm")
                couleur_trait = el.get("couleur", "#0F172A")

                if "titre" in el:
                    painter.setPen(QPen(QColor("#2563EB"), 1))
                    painter.setFont(QFont("Comic Sans MS", 11, QFont.Weight.Bold))
                    painter.drawText(x_debut, curseur_y + 14, el["titre"])
                    curseur_y += 28

                pen_trait = QPen(QColor(couleur_trait), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
                painter.setPen(pen_trait)
                painter.setFont(QFont("Arial Rounded MT Bold", 11, QFont.Weight.Bold))

                if orientation == "horizontale":
                    p_y = curseur_y + 24
                    p_x1 = x_debut + 30
                    p_x2 = p_x1 + longueur_px

                    painter.drawLine(QPointF(p_x1, p_y), QPointF(p_x2, p_y))

                    if genre == "segment":
                        painter.drawLine(QPointF(p_x1, p_y - 8), QPointF(p_x1, p_y + 8))
                        painter.drawLine(QPointF(p_x2, p_y - 8), QPointF(p_x2, p_y + 8))
                    elif genre == "demi_droite":
                        painter.drawLine(QPointF(p_x1, p_y - 8), QPointF(p_x1, p_y + 8))
                        painter.drawLine(QPointF(p_x2 - 8, p_y - 5), QPointF(p_x2, p_y))
                        painter.drawLine(QPointF(p_x2 - 8, p_y + 5), QPointF(p_x2, p_y))
                    elif genre == "droite":
                        painter.setPen(QPen(QColor(couleur_trait), 2, Qt.PenStyle.DashLine))
                        painter.drawLine(QPointF(p_x1 - 15, p_y), QPointF(p_x1, p_y))
                        painter.drawLine(QPointF(p_x2, p_y), QPointF(p_x2 + 15, p_y))
                        painter.setPen(pen_trait)

                    painter.setPen(QPen(QColor("#DC2626"), 2))
                    if lettre1:
                        painter.drawText(int(p_x1 - 18), int(p_y + 5), lettre1)
                    if lettre2:
                        painter.drawText(int(p_x2 + 8), int(p_y + 5), lettre2)

                    painter.setPen(QPen(QColor("#047857"), 2))
                    painter.drawText(QRectF(p_x1, p_y - 24, longueur_px, 20), Qt.AlignmentFlag.AlignCenter, annotation)
                    curseur_y += 62

                elif orientation == "verticale":
                    p_x = x_debut + 80
                    p_y1 = curseur_y + 16
                    p_y2 = p_y1 + longueur_px

                    painter.drawLine(QPointF(p_x, p_y1), QPointF(p_x, p_y2))

                    if genre == "segment":
                        painter.drawLine(QPointF(p_x - 8, p_y1), QPointF(p_x + 8, p_y1))
                        painter.drawLine(QPointF(p_x - 8, p_y2), QPointF(p_x + 8, p_y2))
                    elif genre == "demi_droite":
                        painter.drawLine(QPointF(p_x - 8, p_y1), QPointF(p_x + 8, p_y1))
                        painter.drawLine(QPointF(p_x - 5, p_y2 - 8), QPointF(p_x, p_y2))
                        painter.drawLine(QPointF(p_x + 5, p_y2 - 8), QPointF(p_x, p_y2))
                    elif genre == "droite":
                        painter.setPen(QPen(QColor(couleur_trait), 2, Qt.PenStyle.DashLine))
                        painter.drawLine(QPointF(p_x, p_y1 - 15), QPointF(p_x, p_y1))
                        painter.drawLine(QPointF(p_x, p_y2), QPointF(p_x, p_y2 + 15))
                        painter.setPen(pen_trait)

                    painter.setPen(QPen(QColor("#DC2626"), 2))
                    if lettre1:
                        painter.drawText(int(p_x - 6), int(p_y1 - 8), lettre1)
                    if lettre2:
                        painter.drawText(int(p_x - 6), int(p_y2 + 18), lettre2)

                    painter.setPen(QPen(QColor("#047857"), 2))
                    painter.drawText(int(p_x + 14), int((p_y1 + p_y2) / 2 + 5), annotation)
                    curseur_y += int(longueur_px + 40)

                elif orientation == "oblique":
                    p_x1 = x_debut + 30
                    p_y1 = curseur_y + int(longueur_px * 0.6) + 10
                    p_x2 = p_x1 + int(longueur_px * 0.8)
                    p_y2 = curseur_y + 15

                    painter.drawLine(QPointF(p_x1, p_y1), QPointF(p_x2, p_y2))

                    if genre == "segment":
                        painter.drawLine(QPointF(p_x1 - 5, p_y1 - 5), QPointF(p_x1 + 5, p_y1 + 5))
                        painter.drawLine(QPointF(p_x2 - 5, p_y2 - 5), QPointF(p_x2 + 5, p_y2 + 5))
                    elif genre == "demi_droite":
                        painter.drawLine(QPointF(p_x1 - 5, p_y1 - 5), QPointF(p_x1 + 5, p_y1 + 5))
                        painter.drawLine(QPointF(p_x2 - 8, p_y2 + 2), QPointF(p_x2, p_y2))
                        painter.drawLine(QPointF(p_x2 - 2, p_y2 + 8), QPointF(p_x2, p_y2))

                    painter.setPen(QPen(QColor("#DC2626"), 2))
                    if lettre1:
                        painter.drawText(int(p_x1 - 16), int(p_y1 + 14), lettre1)
                    if lettre2:
                        painter.drawText(int(p_x2 + 8), int(p_y2 - 4), lettre2)

                    painter.setPen(QPen(QColor("#047857"), 2))
                    mx = (p_x1 + p_x2) / 2
                    my = (p_y1 + p_y2) / 2
                    painter.drawText(int(mx - 15), int(my - 10), annotation)
                    curseur_y += int(longueur_px * 0.6 + 45)

            elif type_el == "regle_graduee":
                rx = x_debut + 20
                ry = curseur_y + 15
                rw = int(8 * facteur_cm)
                rh = 40
                painter.setBrush(QBrush(QColor("#FEF08A")))
                painter.setPen(QPen(QColor("#CA8A04"), 2))
                painter.drawRoundedRect(rx, ry, rw, rh, 6, 6)

                painter.setPen(QPen(QColor("#854D0E"), 1))
                painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
                for i in range(9):
                    gx = rx + int(i * facteur_cm)
                    painter.drawLine(gx, ry, gx, ry + 14)
                    painter.drawText(gx - 3, ry + 26, str(i))
                    if i < 8:
                        for mm in range(1, 10):
                            mx = gx + int(mm * facteur_cm / 10.0)
                            h_mm = 8 if mm == 5 else 5
                            painter.drawLine(mx, ry, mx, ry + h_mm)

                sy = ry + rh + 20
                sw = int(el.get("cm", 4) * facteur_cm)
                painter.setPen(QPen(QColor("#DC2626"), 3))
                painter.drawLine(rx, sy, rx + sw, sy)
                painter.drawLine(rx, sy - 6, rx, sy + 6)
                painter.drawLine(rx + sw, sy - 6, rx + sw, sy + 6)
                painter.setFont(QFont("Comic Sans MS", 10, QFont.Weight.Bold))
                painter.drawText(rx + sw // 2 - 15, sy + 18, f"{el.get('cm', 4)} cm")
                curseur_y += rh + 65

            elif type_el == "formes_lignes":
                painter.setFont(QFont("Comic Sans MS", 11, QFont.Weight.Bold))
                items = [
                    ("1. Ligne droite horizontale", "horiz"),
                    ("2. Ligne droite verticale", "vert"),
                    ("3. Ligne droite oblique", "oblique"),
                    ("4. Ligne brisée", "brisee"),
                    ("5. Ligne courbe", "courbe"),
                ]
                for nom, sort in items:
                    painter.setPen(QPen(QColor("#1E3A8A"), 2))
                    painter.drawText(x_debut, curseur_y + 14, nom)
                    curseur_y += 24

                    painter.setPen(QPen(QColor("#0284C7"), 3))
                    if sort == "horiz":
                        painter.drawLine(x_debut + 20, curseur_y + 10, x_debut + 220, curseur_y + 10)
                        curseur_y += 28
                    elif sort == "vert":
                        painter.drawLine(x_debut + 60, curseur_y, x_debut + 60, curseur_y + 40)
                        curseur_y += 50
                    elif sort == "oblique":
                        painter.drawLine(x_debut + 20, curseur_y + 35, x_debut + 160, curseur_y + 5)
                        curseur_y += 48
                    elif sort == "brisee":
                        path = QPainterPath()
                        path.moveTo(x_debut + 20, curseur_y + 25)
                        path.lineTo(x_debut + 50, curseur_y + 5)
                        path.lineTo(x_debut + 80, curseur_y + 25)
                        path.lineTo(x_debut + 110, curseur_y + 5)
                        path.lineTo(x_debut + 140, curseur_y + 25)
                        painter.drawPath(path)
                        curseur_y += 38
                    elif sort == "courbe":
                        path = QPainterPath()
                        path.moveTo(x_debut + 20, curseur_y + 15)
                        path.cubicTo(x_debut + 60, curseur_y - 5, x_debut + 100, curseur_y + 35, x_debut + 140, curseur_y + 15)
                        path.cubicTo(x_debut + 170, curseur_y + 5, x_debut + 190, curseur_y + 25, x_debut + 210, curseur_y + 15)
                        painter.drawPath(path)
                        curseur_y += 38

        if curseur_y + 30 > self.minimumHeight():
            self.setMinimumHeight(curseur_y + 40)


# =============================================================================
# APPLICATION PRINCIPALE
# =============================================================================
class Programme11eme(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Programme en 11 eme")
        self.resize(680, 850)
        self.setMinimumSize(0, 0)

        # Variables de sélection
        self.matiere_choisie = None
        self.option_dessin_choisie = None

        # Variables Mathématiques
        self.lecon_math_choisie = None
        self.exercice_math_choisi = None
        self.option_arithmetique_choisie = None
        self.option_exercice_arith_choisie = None
        self.option_exercice_geo_choisie = None
        self.option_exercice_metrique_choisie = None
        self.option_geometrie_choisie = None
        self.option_metrique_choisie = None

        # Variables Français
        self.lecon_fr_choisie = None
        self.option_lecon_ortho_choisie = None
        self.option_lecon_conj_choisie = None
        self.option_lecon_gramm_choisie = None
        self.option_lecon_vocab_choisie = None
        self.exercice_fr_choisi = None
        self.option_exercice_ortho_choisie = None
        self.option_exercice_conj_choisie = None
        self.option_exercice_gramm_choisie = None
        self.option_exercice_dictee_choisie = None

        # Variables Cours, Boscher, Chose
        self.option_cours_choisie = None
        self.option_boscher_choisie = None
        self.option_chose_choisie = None

        self.movie = None

        self.pages = QStackedWidget(self)
        self.central_widget = self.pages
        self.setCentralWidget(self.pages)

        # Pages générales
        self.page_choix = self.creer_page_choix()
        self.page_chargement = self.creer_page_chargement()
        self.page_programme = self.creer_page_programme()

        # Section Dessin
        self.page_dessin = self.creer_page_dessin()
        self.page_dessin_carotte = self.creer_page_dessin_carotte()
        self.page_dessin_cartable = self.creer_page_dessin_cartable()

        # Page menu Cours
        self.page_cours = self.creer_page_cours()
        self.page_cours_pose_effectue = self.creer_page_cours_pose_effectue()
        self.page_cours_decompose = self.creer_page_cours_decompose()

        # Page menu Méthode Boscher et ses leçons
        self.page_methode_boscher = self.creer_page_methode_boscher()
        self.page_boscher_iu = self.creer_page_boscher_iu()
        self.page_boscher_oa = self.creer_page_boscher_oa()
        self.page_boscher_e = self.creer_page_boscher_e()
        self.page_boscher_p = self.creer_page_boscher_p()
        self.page_boscher_t = self.creer_page_boscher_t()
        self.page_boscher_r = self.creer_page_boscher_r()
        self.page_boscher_n = self.creer_page_boscher_n()
        self.page_boscher_m = self.creer_page_boscher_m()
        self.page_boscher_l = self.creer_page_boscher_l()
        self.page_boscher_c = self.creer_page_boscher_c()
        self.page_boscher_d = self.creer_page_boscher_d()
        self.page_boscher_v = self.creer_page_boscher_v()
        self.page_boscher_s = self.creer_page_boscher_s()
        self.page_boscher_b = self.creer_page_boscher_b()
        self.page_boscher_f = self.creer_page_boscher_f()
        self.page_boscher_j = self.creer_page_boscher_j()
        self.page_boscher_g = self.creer_page_boscher_g()
        self.page_boscher_ch = self.creer_page_boscher_ch()
        self.page_boscher_ou = self.creer_page_boscher_ou()
        self.page_boscher_on = self.creer_page_boscher_on()
        self.page_boscher_oi = self.creer_page_boscher_oi()
        self.page_boscher_an = self.creer_page_boscher_an()
        self.page_boscher_in = self.creer_page_boscher_in()
        self.page_boscher_br = self.creer_page_boscher_br()
        self.page_boscher_fr = self.creer_page_boscher_fr()
        self.page_boscher_bl = self.creer_page_boscher_bl()
        self.page_boscher_cl = self.creer_page_boscher_cl()
        self.page_boscher_ar = self.creer_page_boscher_ar()
        self.page_boscher_al = self.creer_page_boscher_al()
        self.page_boscher_en = self.creer_page_boscher_en()

        # Pages Leçons de chose
        self.page_lecons_de_chose = self.creer_page_lecons_de_chose()
        self.page_chose_nagent = self.creer_page_chose_nagent()
        self.page_chose_volent = self.creer_page_chose_volent()
        self.page_chose_marchent = self.creer_page_chose_marchent()
        self.page_chose_rampent = self.creer_page_chose_rampent()

        # Menus Mathématiques
        self.page_math_lecons = self.creer_page_math_lecons()
        self.page_math_exercices = self.creer_page_math_exercices()

        # Menus Français
        self.page_fr_lecons = self.creer_page_fr_lecons()
        self.page_fr_exercices = self.creer_page_fr_exercices()

        # Sous-menus Français Leçons
        self.page_lecons_orthographe = self.creer_page_lecons_orthographe()
        self.page_lecons_conjugaison = self.creer_page_lecons_conjugaison()
        self.page_lecons_grammaire = self.creer_page_lecons_grammaire()
        self.page_lecons_vocabulaire = self.creer_page_lecons_vocabulaire()

        # Sous-menus Mathématiques
        self.page_arithmetique = self.creer_page_arithmetique()
        self.page_geometrie = self.creer_page_geometrie()
        self.page_metrique = self.creer_page_metrique()
        self.page_exercices_arithmetique = self.creer_page_exercices_arithmetique()
        self.page_exercices_geometrie = self.creer_page_exercices_geometrie()
        self.page_exercices_metrique = self.creer_page_exercices_metrique()

        # Sous-menus Français Exercices
        self.page_exercices_orthographe = self.creer_page_exercices_orthographe()
        self.page_exercices_conjugaison = self.creer_page_exercices_conjugaison()
        self.page_exercices_grammaire = self.creer_page_exercices_grammaire()
        self.page_exercices_dictee = self.creer_page_exercices_dictee()

        # Contenus Français Leçons
        self.page_lecon_ortho_son_i = self.creer_page_lecon_ortho_son_i()
        self.page_lecon_ortho_son_e = self.creer_page_lecon_ortho_son_e()
        self.page_lecon_ortho_son_ar = self.creer_page_lecon_ortho_son_ar()
        self.page_lecon_conj_singulier = self.creer_page_lecon_conj_singulier()
        self.page_lecon_conj_pluriel = self.creer_page_lecon_conj_pluriel()
        self.page_lecon_gramm_26_lettres = self.creer_page_lecon_gramm_26_lettres()
        self.page_lecon_gramm_syllabes = self.creer_page_lecon_gramm_syllabes()
        self.page_lecon_gramm_noms = self.creer_page_lecon_gramm_noms()
        self.page_lecon_vocab_corps = self.creer_page_lecon_vocab_corps()
        self.page_lecon_vocab_environnement = self.creer_page_lecon_vocab_environnement()
        self.page_lecon_vocab_ecole = self.creer_page_lecon_vocab_ecole()

        # Contenus Français Exercices
        self.page_ex_ortho_ie_y_it = self.creer_page_ex_ortho_ie_y_it()
        self.page_ex_ortho_is_id_iz = self.creer_page_ex_ortho_is_id_iz()
        self.page_ex_ortho_i_isc = self.creer_page_ex_ortho_i_isc()
        self.page_ex_ortho_e_eu = self.creer_page_ex_ortho_e_eu()
        self.page_ex_ortho_oeu_oei = self.creer_page_ex_ortho_oeu_oei()
        self.page_ex_ortho_dictee_ar = self.creer_page_ex_ortho_dictee_ar()

        self.page_ex_conj_je_tu = self.creer_page_ex_conj_je_tu()
        self.page_ex_conj_il_elle = self.creer_page_ex_conj_il_elle()
        self.page_ex_conj_singulier = self.creer_page_ex_conj_singulier()
        self.page_ex_conj_nous_vous = self.creer_page_ex_conj_nous_vous()
        self.page_ex_conj_pluriels = self.creer_page_ex_conj_pluriels()
        self.page_ex_conj_remplace_soulignes = self.creer_page_ex_conj_remplace_soulignes()

        self.page_ex_gramm_26_lettres = self.creer_page_ex_gramm_26_lettres()
        self.page_ex_gramm_voyelles = self.creer_page_ex_gramm_voyelles()
        self.page_ex_gramm_separe_syllabes = self.creer_page_ex_gramm_separe_syllabes()
        self.page_ex_gramm_compte_syllabes = self.creer_page_ex_gramm_compte_syllabes()
        self.page_ex_gramm_animal_chose_pers = self.creer_page_ex_gramm_animal_chose_pers()
        self.page_ex_gramm_souligne_bonne_rep = self.creer_page_ex_gramm_souligne_bonne_rep()

        self.page_ex_dictee_02_oct = self.creer_page_ex_dictee_02_oct()
        self.page_ex_dictee_09_oct = self.creer_page_ex_dictee_09_oct()
        self.page_ex_dictee_16_oct = self.creer_page_ex_dictee_16_oct()
        self.page_ex_dictee_22_oct = self.creer_page_ex_dictee_22_oct()
        self.page_ex_dictee_30_oct = self.creer_page_ex_dictee_30_oct()

        # Contenus Mathématiques Leçons
        self.page_lecon_comptage_10 = self.creer_page_lecon_comptage_10()
        self.page_lecon_comptage_49 = self.creer_page_lecon_comptage_49()
        self.page_lecon_comptage_119 = self.creer_page_lecon_comptage_119()
        self.page_lecon_addition_sans = self.creer_page_lecon_addition_sans()
        self.page_lecon_addition_avec = self.creer_page_lecon_addition_avec()
        self.page_lecon_point = self.creer_page_lecon_point()
        self.page_lecon_lignes = self.creer_page_lecon_lignes()
        self.page_lecon_regle = self.creer_page_lecon_regle()
        self.page_lecon_segment = self.creer_page_lecon_segment()

        # Contenus Mathématiques Exercices
        self.page_ex_comptage_10 = self.creer_page_ex_comptage_10()
        self.page_ex_comptage_49 = self.creer_page_ex_comptage_49()
        self.page_ex_ecris_lettres = self.creer_page_ex_ecris_lettres()
        self.page_ex_comptage_75 = self.creer_page_ex_comptage_75()
        self.page_ex_pose_effectue = self.creer_page_ex_pose_effectue()
        self.page_ex_arith_ecris = self.creer_page_ex_arith_ecris()

        self.page_ex_geo_ligne_6cm = self.creer_page_ex_geo_ligne_6cm()
        self.page_ex_geo_souligne = self.creer_page_ex_geo_souligne()
        self.page_ex_met_ligne_horiz = self.creer_page_ex_met_ligne_horiz()
        self.page_ex_met_ligne_7cm = self.creer_page_ex_met_ligne_7cm()
        self.page_ex_met_segment_ab = self.creer_page_ex_met_segment_ab()
        self.page_ex_met_demi_droite = self.creer_page_ex_met_demi_droite()
        self.page_ex_met_ij_4cm = self.creer_page_ex_met_ij_4cm()
        self.page_ex_met_segment_ab_6cm = self.creer_page_ex_met_segment_ab_6cm()

        # Enregistrement de toutes les pages dans le QStackedWidget
        pages_liste = [
            self.page_choix, self.page_chargement, self.page_programme,
            self.page_dessin, self.page_dessin_carotte, self.page_dessin_cartable,
            self.page_cours, self.page_cours_pose_effectue, self.page_cours_decompose,
            self.page_methode_boscher,
            self.page_boscher_iu, self.page_boscher_oa, self.page_boscher_e, self.page_boscher_p,
            self.page_boscher_t, self.page_boscher_r, self.page_boscher_n, self.page_boscher_m,
            self.page_boscher_l, self.page_boscher_c, self.page_boscher_d, self.page_boscher_v,
            self.page_boscher_s, self.page_boscher_b, self.page_boscher_f, self.page_boscher_j,
            self.page_boscher_g, self.page_boscher_ch, self.page_boscher_ou, self.page_boscher_on,
            self.page_boscher_oi, self.page_boscher_an, self.page_boscher_in,
            self.page_boscher_br, self.page_boscher_fr, self.page_boscher_bl, self.page_boscher_cl,
            self.page_boscher_ar, self.page_boscher_al, self.page_boscher_en,
            self.page_lecons_de_chose, self.page_chose_nagent, self.page_chose_volent,
            self.page_chose_marchent, self.page_chose_rampent,
            self.page_math_lecons, self.page_math_exercices,
            self.page_fr_lecons, self.page_fr_exercices,
            self.page_lecons_orthographe, self.page_lecons_conjugaison,
            self.page_lecons_grammaire, self.page_lecons_vocabulaire,
            self.page_arithmetique, self.page_geometrie, self.page_metrique,
            self.page_exercices_arithmetique, self.page_exercices_geometrie, self.page_exercices_metrique,
            self.page_exercices_orthographe, self.page_exercices_conjugaison,
            self.page_exercices_grammaire, self.page_exercices_dictee,
            self.page_lecon_ortho_son_i, self.page_lecon_ortho_son_e, self.page_lecon_ortho_son_ar,
            self.page_lecon_conj_singulier, self.page_lecon_conj_pluriel,
            self.page_lecon_gramm_26_lettres, self.page_lecon_gramm_syllabes, self.page_lecon_gramm_noms,
            self.page_lecon_vocab_corps, self.page_lecon_vocab_environnement, self.page_lecon_vocab_ecole,
            self.page_ex_ortho_ie_y_it, self.page_ex_ortho_is_id_iz, self.page_ex_ortho_i_isc,
            self.page_ex_ortho_e_eu, self.page_ex_ortho_oeu_oei, self.page_ex_ortho_dictee_ar,
            self.page_ex_conj_je_tu, self.page_ex_conj_il_elle, self.page_ex_conj_singulier,
            self.page_ex_conj_nous_vous, self.page_ex_conj_pluriels, self.page_ex_conj_remplace_soulignes,
            self.page_ex_gramm_26_lettres, self.page_ex_gramm_voyelles,
            self.page_ex_gramm_separe_syllabes, self.page_ex_gramm_compte_syllabes, self.page_ex_gramm_animal_chose_pers,
            self.page_ex_gramm_souligne_bonne_rep,
            self.page_ex_dictee_02_oct, self.page_ex_dictee_09_oct, self.page_ex_dictee_16_oct, self.page_ex_dictee_22_oct, self.page_ex_dictee_30_oct,
            self.page_lecon_comptage_10, self.page_lecon_comptage_49, self.page_lecon_comptage_119,
            self.page_lecon_addition_sans, self.page_lecon_addition_avec,
            self.page_lecon_point, self.page_lecon_lignes, self.page_lecon_regle, self.page_lecon_segment,
            self.page_ex_comptage_10, self.page_ex_comptage_49, self.page_ex_ecris_lettres,
            self.page_ex_comptage_75, self.page_ex_pose_effectue, self.page_ex_arith_ecris,
            self.page_ex_geo_ligne_6cm, self.page_ex_geo_souligne,
            self.page_ex_met_ligne_horiz, self.page_ex_met_ligne_7cm, self.page_ex_met_segment_ab,
            self.page_ex_met_demi_droite, self.page_ex_met_ij_4cm, self.page_ex_met_segment_ab_6cm
        ]
        for p in pages_liste:
            self.pages.addWidget(p)

        self.pages.setCurrentWidget(self.page_choix)

    # =========================================================================
    # STYLES COMMUNS & HELPERS
    # =========================================================================
    def style_fond(self, widget):
        widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #E0F7FA, stop: 0.6 #FFF9C4, stop: 1 #FFE0B2
                );
            }
        """)

    def creer_titre(self, texte, parent=None):
        label = QLabel(texte, parent)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setWordWrap(True)
        label.setStyleSheet("""
            QLabel {
                color: #D90429;
                font-family: "Fredoka", "Arial Rounded MT Bold", "Comic Sans MS", Arial;
                font-size: 22px;
                font-weight: bold;
                background: transparent;
                padding: 4px;
            }
        """)
        label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        return label

    def creer_bouton_choix(self, texte, couleur="#4CC9F0"):
        bouton = QPushButton(texte)
        bouton.setCheckable(True)
        bouton.setCursor(Qt.CursorShape.PointingHandCursor)
        bouton.setMinimumHeight(44)
        bouton.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        bouton.setStyleSheet(f"""
            QPushButton {{
                background-color: {couleur};
                color: white;
                font-family: "Comic Sans MS", "Fredoka", "Arial Rounded MT Bold", Arial;
                font-size: 17px;
                font-weight: bold;
                border-radius: 14px;
                border: 3px solid #4361EE;
                border-bottom: 5px solid #3A0CA3;
                padding: 6px 10px;
            }}
            QPushButton:hover {{ background-color: #38B6FF; border-color: #3A0CA3; }}
            QPushButton:checked {{ background-color: #7209B7; border-color: #560FA0; }}
            QPushButton:pressed {{ background-color: #3A0CA3; border-bottom-width: 2px; }}
        """)
        return bouton

    def creer_bouton_rose_3d(self, texte):
        bouton = QPushButton(texte)
        bouton.setCheckable(True)
        bouton.setCursor(Qt.CursorShape.PointingHandCursor)
        bouton.setMinimumHeight(44)
        bouton.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        bouton.setStyleSheet("""
            QPushButton {
                background-color: #F0F2F5;
                color: #FF2E93;
                border: 3px solid #FF2E93;
                border-bottom: 5px solid #C40058;
                border-radius: 14px;
                font-family: "Comic Sans MS", "Fredoka", "Arial Rounded MT Bold", sans-serif;
                font-size: 15px;
                font-weight: 800;
                letter-spacing: 0.5px;
                padding: 6px 10px;
            }
            QPushButton:hover { background-color: #E5E9F0; color: #FF0040; border-color: #FF0040; border-bottom-color: #B3002D; }
            QPushButton:checked { background-color: #FF2E93; color: white; border-color: #C40058; border-bottom: 5px solid #85003A; }
            QPushButton:pressed { background-color: #D8DCE2; border-bottom: 2px solid #B3002D; padding-top: 8px; }
        """)
        return bouton

    def creer_bouton_choose(self, texte="Choose"):
        bouton = QCommandLinkButton(texte)
        bouton.setCursor(Qt.CursorShape.PointingHandCursor)
        bouton.setMinimumHeight(46)
        bouton.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        bouton.setStyleSheet("""
            QCommandLinkButton {
                background-color: #FFF3BF;
                border: 3px solid #FFD43B;
                border-bottom: 6px solid #FAB005;
                border-radius: 16px;
                padding: 6px 14px;
                color: #2B8A3E;
                font-family: "Fredoka", "Arial Rounded MT Bold", "Comic Sans MS", sans-serif;
                font-size: 18px;
                font-weight: bold;
            }
            QCommandLinkButton:hover { background-color: #FFE066; border-color: #FCC419; border-bottom: 6px solid #F59F00; }
            QCommandLinkButton:pressed { background-color: #FFD43B; border-bottom: 2px solid #F59F00; margin-top: 4px; }
        """)
        return bouton

    def creer_navigateur_lecon(self):
        navigateur = QTextBrowser()
        navigateur.setStyleSheet("""
            QTextBrowser {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1, stop: 0 #FFF6F6, stop: 1 #F0F4FF);
                border: 2px solid #80DEEA;
                border-radius: 16px;
                padding: 10px;
                font-family: "Comic Sans MS", "Fredoka", "Arial Rounded MT Bold", sans-serif;
                color: #2D3748;
            }
        """)
        return navigateur

    def creer_page_affichage(self, html, callback_retour, texte_retour="← Revenir"):
        page = QWidget()
        self.style_fond(page)
        l = QVBoxLayout(page)
        l.setContentsMargins(12, 12, 12, 12)
        l.setSpacing(10)

        tb = self.creer_navigateur_lecon()
        tb.setHtml(html)
        l.addWidget(tb, 1)

        btn = QPushButton(texte_retour)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("QPushButton { background-color: #6C757D; color: white; font-size: 15px; font-weight: bold; border-radius: 12px; padding: 8px; } QPushButton:hover { background-color: #5A6268; }")
        btn.clicked.connect(callback_retour)
        l.addWidget(btn)
        return page

    def creer_page_cahier_visuel(self, date_str, titre_str, elements_cahier, callback_retour, texte_retour="← Revenir", hauteur_min=500):
        page = QWidget()
        self.style_fond(page)
        l = QVBoxLayout(page)
        l.setContentsMargins(10, 10, 10, 10)
        l.setSpacing(8)

        header_widget = QWidget()
        header_widget.setStyleSheet("background: transparent;")
        hl = QVBoxLayout(header_widget)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(4)

        if date_str:
            lbl_date = QLabel(f"📅 {date_str}")
            lbl_date.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_date.setStyleSheet("background-color: #4361EE; color: white; font-size: 13px; font-weight: bold; border-radius: 10px; padding: 4px 12px;")
            hl.addWidget(lbl_date)

        lbl_titre = QLabel(titre_str)
        lbl_titre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_titre.setStyleSheet("color: #FF2E93; font-size: 17px; font-weight: 800; background: transparent; padding: 2px;")
        hl.addWidget(lbl_titre)
        l.addWidget(header_widget)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: 3px solid #80DEEA;
                border-radius: 16px;
                background-color: #FFFFFF;
            }
        """)
        cahier = CahierDessinWidget(elements_cahier, hauteur_min=hauteur_min)
        scroll.setWidget(cahier)
        l.addWidget(scroll, 1)

        btn = QPushButton(texte_retour)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("QPushButton { background-color: #6C757D; color: white; font-size: 15px; font-weight: bold; border-radius: 12px; padding: 8px; } QPushButton:hover { background-color: #5A6268; }")
        btn.clicked.connect(callback_retour)
        l.addWidget(btn)
        return page

    # =========================================================================
    # ACCUEIL
    # =========================================================================
    def creer_page_choix(self):
        page = QWidget()
        self.style_fond(page)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        self.titre_choix = self.creer_titre("Programme en 11 eme")
        layout.addWidget(self.titre_choix)

        self.groupe_choix = QButtonGroup(self)
        self.groupe_choix.setExclusive(True)

        self.boutons_choix = {}
        for nom in ("Francais", "Mathematiques", "Cours", "Dessin", "Anglais", "Methode boscher", "Lecons de chose"):
            bouton = self.creer_bouton_choix(nom, "#4CC9F0")
            self.groupe_choix.addButton(bouton)
            self.boutons_choix[nom] = bouton
            bouton.clicked.connect(lambda checked=False, choix=nom: self.selectionner_matiere(choix))
            layout.addWidget(bouton, 1)

        self.bouton_choose = self.creer_bouton_choose("Choose")
        self.bouton_choose.clicked.connect(self.confirmer_matiere)
        layout.addWidget(self.bouton_choose)
        return page

    def creer_page_chargement(self):
        page = QWidget()
        self.style_fond(page)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self.titre_chargement = self.creer_titre("Programme en 11 eme")
        layout.addWidget(self.titre_chargement)

        self.label_matiere_chargement = QLabel("")
        self.label_matiere_chargement.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_matiere_chargement.setWordWrap(True)
        self.label_matiere_chargement.setStyleSheet("font-size: 22px; font-weight: bold; color: #2B8A3E; background: transparent;")
        layout.addWidget(self.label_matiere_chargement)

        self.label_gif = QLabel()
        self.label_gif.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_gif.setMinimumSize(80, 80)
        self.label_gif.setStyleSheet("background: transparent;")
        layout.addWidget(self.label_gif, 1)

        self.label_chargement = QLabel("Chargement en cours...")
        self.label_chargement.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_chargement.setWordWrap(True)
        self.label_chargement.setStyleSheet("font-size: 18px; font-weight: bold; color: #3A0CA3; background: transparent;")
        layout.addWidget(self.label_chargement)
        return page

    def creer_page_programme(self):
        page = QWidget()
        self.style_fond(page)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self.titre_programme = self.creer_titre("Lecons ou Exercices")
        layout.addWidget(self.titre_programme, 1)

        self.texte_programme = QLabel("")
        self.texte_programme.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.texte_programme.setWordWrap(True)
        self.texte_programme.setStyleSheet("QLabel { background: transparent; color: #222222; font-size: 19px; font-weight: bold; padding: 8px; }")
        layout.addWidget(self.texte_programme, 2)

        self.bouton_lecons = self.creer_bouton_choix("Lecons", "#FF6B6B")
        self.bouton_lecons.setCheckable(False)
        self.bouton_lecons.clicked.connect(lambda: self.ouvrir_contenu("Lecons"))
        layout.addWidget(self.bouton_lecons, 1)

        self.bouton_exercices = self.creer_bouton_choix("Exercices", "#FF6B6B")
        self.bouton_exercices.setCheckable(False)
        self.bouton_exercices.clicked.connect(lambda: self.ouvrir_contenu("Exercices"))
        layout.addWidget(self.bouton_exercices, 1)

        self.bouton_retour = self.creer_bouton_choose("Retour au choix")
        self.bouton_retour.clicked.connect(self.retour_au_choix)
        layout.addWidget(self.bouton_retour, 1)
        return page

    # =========================================================================
    # SECTION DESSIN (CAROTTE & CARTABLE)
    # =========================================================================
    def creer_page_dessin(self):
        page = QWidget()
        self.style_fond(page)
        l = QVBoxLayout(page)
        l.setContentsMargins(12, 12, 12, 12)

        cadre = QFrame()
        cadre.setStyleSheet("QFrame { background-color: transparent; border: 3px solid #80DEEA; border-radius: 20px; }")
        cadre_l = QVBoxLayout(cadre)

        self.titre_dessin = self.creer_titre("Dessin\nChoisissez un dessin à réaliser")
        cadre_l.addWidget(self.titre_dessin, 1)

        self.groupe_dessin = QButtonGroup(self)
        self.groupe_dessin.setExclusive(True)

        self.bouton_dessin_carotte = self.creer_bouton_rose_3d("1- Carotte")
        self.bouton_dessin_cartable = self.creer_bouton_rose_3d("2- Cartable")
        self.boutons_dessin = [self.bouton_dessin_carotte, self.bouton_dessin_cartable]

        for b in self.boutons_dessin:
            self.groupe_dessin.addButton(b)
            cadre_l.addWidget(b, 2)
            b.clicked.connect(lambda checked=False, btn=b: self.selectionner_dessin(btn.text()))

        self.bouton_choose_dessin = self.creer_bouton_choose("Choose")
        self.bouton_choose_dessin.clicked.connect(self.confirmer_choix_dessin)
        cadre_l.addWidget(self.bouton_choose_dessin, 1)

        btn_ret = QPushButton("← Revenir au choix")
        btn_ret.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ret.setStyleSheet("QPushButton { background-color: #6C757D; color: white; font-size: 15px; font-weight: bold; border-radius: 12px; padding: 6px; }")
        btn_ret.clicked.connect(self.retour_au_choix)
        cadre_l.addWidget(btn_ret)

        l.addWidget(cadre)
        return page

    def selectionner_dessin(self, nom):
        self.option_dessin_choisie = nom
        self.titre_dessin.setText(f"Dessin\n{nom}")

    def confirmer_choix_dessin(self):
        if not self.option_dessin_choisie:
            return
        if "Carotte" in self.option_dessin_choisie:
            self.charger_contenu_carotte()
            self.pages.setCurrentWidget(self.page_dessin_carotte)
        elif "Cartable" in self.option_dessin_choisie:
            self.charger_contenu_cartable()
            self.pages.setCurrentWidget(self.page_dessin_cartable)

    def retour_a_dessin(self):
        self.pages.setCurrentWidget(self.page_dessin)

    def creer_page_dessin_carotte(self):
        page = QWidget()
        self.style_fond(page)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        header = QLabel("🥕 Atelier Dessin : Comment dessiner une Carotte")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("background-color: #EA580C; color: white; font-size: 17px; font-weight: bold; border-radius: 12px; padding: 6px;")
        layout.addWidget(header)

        # Zone centrale avec décors sur les côtés
        centre_layout = QHBoxLayout()
        centre_layout.setSpacing(6)

        ruban_gauche = RubanDecoratifCote()
        centre_layout.addWidget(ruban_gauche)

        self.scroll_carotte = QScrollArea()
        self.scroll_carotte.setWidgetResizable(True)
        self.scroll_carotte.setStyleSheet("""
            QScrollArea {
                border: 4px solid #F97316;
                border-radius: 16px;
                background-color: #FFFFFF;
            }
        """)
        self.conteneur_carotte = QWidget()
        self.conteneur_carotte.setStyleSheet("background-color: #FFFFFF;")
        self.layout_conteneur_carotte = QVBoxLayout(self.conteneur_carotte)
        self.layout_conteneur_carotte.setContentsMargins(14, 14, 14, 14)
        self.layout_conteneur_carotte.setSpacing(16)
        self.scroll_carotte.setWidget(self.conteneur_carotte)
        centre_layout.addWidget(self.scroll_carotte, 1)

        ruban_droit = RubanDecoratifCote()
        centre_layout.addWidget(ruban_droit)

        layout.addLayout(centre_layout, 1)

        btn_ret = QPushButton("← Revenir au choix du Dessin")
        btn_ret.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ret.setStyleSheet("QPushButton { background-color: #6C757D; color: white; font-size: 15px; font-weight: bold; border-radius: 12px; padding: 8px; } QPushButton:hover { background-color: #5A6268; }")
        btn_ret.clicked.connect(self.retour_a_dessin)
        layout.addWidget(btn_ret)

        return page

    def charger_contenu_carotte(self):
        # Vider l'ancien contenu
        while self.layout_conteneur_carotte.count():
            item = self.layout_conteneur_carotte.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 1. Chargement des pages du PDF de la carotte ou images
        pixmaps = charger_pages_pdf_ou_images(["carotte", "carrot"], nom_pdf="carot.pdf")

        if pixmaps:
            lbl_titre_pdf = QLabel("📄 Dessin de la Carotte & Ses Étapes (Fichier PDF chargé) :")
            lbl_titre_pdf.setStyleSheet("font-size: 14px; font-weight: bold; color: #C2410C;")
            self.layout_conteneur_carotte.addWidget(lbl_titre_pdf)

            for i, px in enumerate(pixmaps):
                cadre_img = QFrame()
                cadre_img.setStyleSheet("QFrame { border: 3px dashed #FB923C; border-radius: 14px; background: #FFF7ED; padding: 8px; }")
                cadre_l = QVBoxLayout(cadre_img)
                lbl_page = QLabel()
                lbl_page.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl_page.setPixmap(px)
                lbl_page.setScaledContents(False)
                lbl_page.setMinimumWidth(0)
                cadre_l.addWidget(lbl_page)
                self.layout_conteneur_carotte.addWidget(cadre_img)
        else:
            # Message informatif si aucun fichier externe
            info = QLabel("Le document « carot.pdf » est introuvable. Placez ce fichier à côté du programme.")
            info.setStyleSheet("background: #FFF7ED; border: 2px dashed #F97316; border-radius: 10px; padding: 8px; font-size: 12px; color: #9A3412;")
            info.setWordWrap(True)
            self.layout_conteneur_carotte.addWidget(info)

        # 2. Description pédagogique des étapes de dessin
        guide_browser = QTextBrowser()
        guide_browser.setOpenExternalLinks(False)
        guide_browser.setStyleSheet("border: 2px solid #FDBA74; border-radius: 12px; background: #FFFAF0; padding: 10px;")
        html_guide = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:left; color:#7C2D12;">
            <p style="font-size:16pt; font-weight:900; color:#EA580C; text-align:center;">✨ Les Étapes pour réussir la Carotte ✨</p>
            
            <div style="background:#FFFFFF; border:2px solid #FED7AA; border-radius:10px; padding:10px; margin-bottom:10px;">
                <b style="color:#C2410C; font-size:13pt;">• Étape 1 :</b> Tracer la forme conique allongée (ovale pointu vers le bas) qui forme le corps de la carotte.
            </div>

            <div style="background:#FFFFFF; border:2px solid #FED7AA; border-radius:10px; padding:10px; margin-bottom:10px;">
                <b style="color:#C2410C; font-size:13pt;">• Étape 2 :</b> Ajouter de petits traits horizontaux légèrement incurvés le long du corps pour donner du relief.
            </div>

            <div style="background:#FFFFFF; border:2px solid #FED7AA; border-radius:10px; padding:10px; margin-bottom:10px;">
                <b style="color:#15803D; font-size:13pt;">• Étape 3 :</b> Dessiner les fanes (les feuilles au sommet) avec 3 ou 4 bosses arrondies.
            </div>

            <div style="background:#ECFDF5; border:2px dashed #10B981; border-radius:10px; padding:10px;">
                <b style="color:#047857; font-size:13pt;">• Finition :</b> Colorier le corps en bel orange et le feuillage en vert tendre ou foncé !
            </div>
        </body></html>
        """
        guide_browser.setHtml(html_guide)
        guide_browser.setMinimumHeight(240)
        self.layout_conteneur_carotte.addWidget(guide_browser)

    def creer_page_dessin_cartable(self):
        page = QWidget()
        self.style_fond(page)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        header = QLabel("🎒 Atelier Dessin : Comment dessiner un Cartable Mignon")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("background-color: #FF2E93; color: white; font-size: 17px; font-weight: bold; border-radius: 12px; padding: 6px;")
        layout.addWidget(header)

        # Zone centrale avec décors sur les côtés
        centre_layout = QHBoxLayout()
        centre_layout.setSpacing(6)

        ruban_gauche = RubanDecoratifCote()
        centre_layout.addWidget(ruban_gauche)

        self.scroll_cartable = QScrollArea()
        self.scroll_cartable.setWidgetResizable(True)
        self.scroll_cartable.setStyleSheet("""
            QScrollArea {
                border: 4px solid #FF2E93;
                border-radius: 16px;
                background-color: #FFFFFF;
            }
        """)
        self.conteneur_cartable = QWidget()
        self.conteneur_cartable.setStyleSheet("background-color: #FFFFFF;")
        self.layout_conteneur_cartable = QVBoxLayout(self.conteneur_cartable)
        self.layout_conteneur_cartable.setContentsMargins(14, 14, 14, 14)
        self.layout_conteneur_cartable.setSpacing(16)
        self.scroll_cartable.setWidget(self.conteneur_cartable)
        centre_layout.addWidget(self.scroll_cartable, 1)

        ruban_droit = RubanDecoratifCote()
        centre_layout.addWidget(ruban_droit)

        layout.addLayout(centre_layout, 1)

        btn_ret = QPushButton("← Revenir au choix du Dessin")
        btn_ret.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ret.setStyleSheet("QPushButton { background-color: #6C757D; color: white; font-size: 15px; font-weight: bold; border-radius: 12px; padding: 8px; } QPushButton:hover { background-color: #5A6268; }")
        btn_ret.clicked.connect(self.retour_a_dessin)
        layout.addWidget(btn_ret)

        return page

    def charger_contenu_cartable(self):
        # Vider l'ancien contenu
        while self.layout_conteneur_cartable.count():
            item = self.layout_conteneur_cartable.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 1. Chargement du PDF du Cartable ou image modèle
        pixmaps = charger_pages_pdf_ou_images(["cartable", "backpack", "sac"], nom_pdf="school bag.pdf")

        if pixmaps:
            lbl_titre_pdf = QLabel("📄 Modèle Cartable (Fichier PDF chargé) :")
            lbl_titre_pdf.setStyleSheet("font-size: 14px; font-weight: bold; color: #BE185D;")
            self.layout_conteneur_cartable.addWidget(lbl_titre_pdf)

            for i, px in enumerate(pixmaps):
                cadre_img = QFrame()
                cadre_img.setStyleSheet("QFrame { border: 3px dashed #F472B6; border-radius: 14px; background: #FDF2F8; padding: 8px; }")
                cadre_l = QVBoxLayout(cadre_img)
                lbl_page = QLabel()
                lbl_page.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl_page.setPixmap(px)
                lbl_page.setScaledContents(False)
                lbl_page.setMinimumWidth(0)
                cadre_l.addWidget(lbl_page)
                self.layout_conteneur_cartable.addWidget(cadre_img)
        else:
            info_pdf = QLabel("Le document « school bag.pdf » est introuvable. Placez ce fichier à côté du programme.")
            info_pdf.setWordWrap(True)
            info_pdf.setStyleSheet("background: #FDF2F8; border: 2px dashed #F472B6; border-radius: 10px; padding: 8px; color: #9D174D;")
            self.layout_conteneur_cartable.addWidget(info_pdf)

        # 2. Recherche aussi d'une image d'étapes (ex: how to draw, steps, etapes)
        images_etapes = charger_pages_pdf_ou_images(["etape", "step", "how_to_draw", "easy_steps"], nom_pdf="__aucun_pdf__.pdf")
        for px_et in images_etapes:
            cadre_et = QFrame()
            cadre_et.setStyleSheet("QFrame { border: 3px solid #3B82F6; border-radius: 14px; background: #EFF6FF; padding: 6px; }")
            l_et = QVBoxLayout(cadre_et)
            lbl_et = QLabel()
            lbl_et.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_et.setPixmap(px_et)
            l_et.addWidget(lbl_et)
            self.layout_conteneur_cartable.addWidget(cadre_et)

        # 3. Guide complet interactif : Les 6 étapes faciles pour dessiner le cartable mignon
        guide_browser = QTextBrowser()
        guide_browser.setStyleSheet("border: 2px solid #F472B6; border-radius: 14px; background: #FFF5F7; padding: 12px;")
        html_guide = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:left; color:#1F2937;">
            <p style="font-size:16pt; font-weight:900; color:#DB2777; text-align:center; margin-bottom:4px;">
                🎒 How to Draw a Cute School Backpack — 6 Easy Steps!
            </p>
            <p style="text-align:center; font-size:11pt; color:#6B7280; font-weight:bold; margin-top:0;">
                Suivez ces 6 étapes pas à pas avec votre crayon et amusez-vous !
            </p>

            <table width="100%" border="0" cellspacing="8" cellpadding="8" style="font-size:11pt;">
                <tr>
                    <td width="50%" style="background:#FFFFFF; border:2px solid #80DEEA; border-radius:12px;">
                        <b style="color:#0284C7; font-size:12pt;">Step 1 • Draw the Main Body</b><br>
                        Tracer un grand rectangle aux coins bien arrondis pour former le corps du cartable.
                    </td>
                    <td width="50%" style="background:#FFFFFF; border:2px solid #80DEEA; border-radius:12px;">
                        <b style="color:#0284C7; font-size:12pt;">Step 2 • Add the Flap</b><br>
                        Ajouter le rabat supérieur avec une ligne courbée en haut du sac (curved flap on top).
                    </td>
                </tr>
                <tr>
                    <td style="background:#FFFFFF; border:2px solid #80DEEA; border-radius:12px;">
                        <b style="color:#0284C7; font-size:12pt;">Step 3 • Draw the Side Pockets</b><br>
                        Dessiner les deux petites poches latérales de chaque côté pour ranger les gourdes.
                    </td>
                    <td style="background:#FFFFFF; border:2px solid #80DEEA; border-radius:12px;">
                        <b style="color:#0284C7; font-size:12pt;">Step 4 • Add the Straps</b><br>
                        Tracer les deux jolies bretelles pour les épaules (two straps for your shoulders).
                    </td>
                </tr>
                <tr>
                    <td style="background:#FFFFFF; border:2px solid #80DEEA; border-radius:12px;">
                        <b style="color:#0284C7; font-size:12pt;">Step 5 • Draw Details</b><br>
                        Dessiner la fermeture éclair, la poche avant, et les détails mignons (étoiles ⭐, coeur 💖).
                    </td>
                    <td style="background:#FFFFFF; border:2px solid #80DEEA; border-radius:12px;">
                        <b style="color:#D81B60; font-size:12pt;">Step 6 • Add a Cute Face!</b><br>
                        Ajouter les yeux kawaii brillants, de jolis cils, des pommettes roses et un grand sourire !
                    </td>
                </tr>
            </table>

            <div style="background:#F0FDF4; border:2px dashed #16A34A; border-radius:12px; padding:10px; margin-top:8px; text-align:center;">
                <b style="color:#15803D; font-size:12pt;">🎉 À votre tour : Now it's your turn!</b><br>
                <span style="color:#166534; font-size:11pt;">Vous pouvez colorier en rose, ajouter des étoiles vertes, des autocollants et des motifs originaux !</span>
            </div>
        </body></html>
        """
        guide_browser.setHtml(html_guide)
        guide_browser.setMinimumHeight(380)
        self.layout_conteneur_cartable.addWidget(guide_browser)

    # =========================================================================
    # SECTION LEÇONS DE CHOSE
    # =========================================================================
    def creer_page_lecons_de_chose(self):
        page = QWidget()
        self.style_fond(page)
        l = QVBoxLayout(page)
        l.setContentsMargins(12, 12, 12, 12)

        cadre = QFrame()
        cadre.setStyleSheet("QFrame { background-color: transparent; border: 3px solid #80DEEA; border-radius: 20px; }")
        cadre_l = QVBoxLayout(cadre)

        self.titre_lecons_de_chose = self.creer_titre("Leçons de chose\nChoisissez une leçon")
        cadre_l.addWidget(self.titre_lecons_de_chose, 1)

        self.groupe_lecons_de_chose = QButtonGroup(self)
        self.groupe_lecons_de_chose.setExclusive(True)

        self.boutons_lecons_de_chose = [
            self.creer_bouton_rose_3d("LES ANIMAUX QUI NAGENT."),
            self.creer_bouton_rose_3d("LES ANIMAUX QUI VOLENT."),
            self.creer_bouton_rose_3d("LES ANIMAUX QUI  MARCHENT."),
            self.creer_bouton_rose_3d("LES ANIMAUX QUI RAMPENT.")
        ]

        for b in self.boutons_lecons_de_chose:
            self.groupe_lecons_de_chose.addButton(b)
            cadre_l.addWidget(b, 2)
            b.clicked.connect(lambda checked=False, btn=b: self.selectionner_chose(btn.text()))

        self.bouton_choose_chose = self.creer_bouton_choose("Choose")
        self.bouton_choose_chose.clicked.connect(self.confirmer_choix_chose)
        cadre_l.addWidget(self.bouton_choose_chose, 1)

        btn_ret = QPushButton("← Revenir au choix")
        btn_ret.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ret.setStyleSheet("QPushButton { background-color: #6C757D; color: white; font-size: 15px; font-weight: bold; border-radius: 12px; padding: 6px; }")
        btn_ret.clicked.connect(self.retour_au_choix)
        cadre_l.addWidget(btn_ret)

        l.addWidget(cadre)
        return page

    def creer_page_chose_nagent(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#0284C7; color:#fff; font-size:14pt; font-weight:bold; padding:6px 16px; border-radius:12px;">📅 Mercredi 01 Octobre 2026</span></p>
            <p style="font-size:18pt; font-weight:900; color:#D90429; margin-top:8px;">LES ANIMAUX QUI NAGENT</p>
            
            <div style="background:#E0F2FE; border-left:5px solid #0284C7; border-radius:10px; padding:12px; text-align:left; font-size:12pt; line-height:2; color:#0369A1;">
                ✦ <b>Définition :</b> Les animaux qui nagent sont des animaux qui se déplacent dans l'eau. Ils utilisent généralement leurs <b>nageoires</b> ou leurs <b>pattes palmées</b> pour nager et se déplacer.
            </div>

            <p style="font-size:14pt; font-weight:800; color:#0D47A1; margin-top:14px; text-align:left;">🐟 Les animaux qui nagent :</p>
            <div style="background:#FFFFFF; border:3px solid #80DEEA; border-radius:14px; padding:14px; font-size:13pt; font-weight:bold; color:#0F172A; text-align:left; line-height:2.4;">
                ✦ <b style="color:#0284C7;">le poisson</b> &nbsp;&nbsp;|&nbsp;&nbsp; ✦ <b style="color:#0284C7;">le dauphin</b><br>
                ✦ <b style="color:#0284C7;">le requin</b> &nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp; ✦ <b style="color:#0284C7;">le phoque</b><br>
                ✦ <b style="color:#0284C7;">le crabe</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp; ✦ <b style="color:#0284C7;">l'anguille</b><br>
                ✦ <b style="color:#0284C7;">la tortue de mer</b> &nbsp;&nbsp;|&nbsp;&nbsp; ✦ <b style="color:#0284C7;">la baleine</b><br>
                ✦ <b style="color:#0284C7;">le crocodile</b> (dans l'eau) &nbsp;&nbsp;|&nbsp;&nbsp; ✦ <b style="color:#0284C7;">le canard</b>
            </div>

            <div style="background:#F0FDF4; border:2px dashed #16A34A; border-radius:12px; padding:10px; margin-top:14px; font-size:12pt; font-weight:bold; color:#15803D; text-align:left; line-height:2;">
                💡 <b>À retenir :</b><br>
                • Les poissons ont des nageoires et des branchies pour respirer dans l'eau.<br>
                • Le dauphin et la baleine sont des mammifères marins qui savent très bien nager !
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_lecons_de_chose, "← Revenir aux Leçons de chose")

    def creer_page_chose_volent(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#0284C7; color:#fff; font-size:14pt; font-weight:bold; padding:6px 16px; border-radius:12px;">📅 Vendredi 03 Octobre 2026</span></p>
            <p style="font-size:18pt; font-weight:900; color:#D90429; margin-top:8px;">LES ANIMAUX QUI VOLENT</p>
            
            <div style="background:#FEF3C7; border-left:5px solid #F59E0B; border-radius:10px; padding:12px; text-align:left; font-size:12pt; line-height:2; color:#92400E;">
                ✦ <b>Définition :</b> Les animaux qui volent sont des animaux qui ont des <b>ailes</b> pour se déplacer dans l'air.
            </div>

            <p style="font-size:14pt; font-weight:800; color:#B45309; margin-top:14px; text-align:left;">🦅 1. Les oiseaux et mammifères volants :</p>
            <div style="background:#FFFFFF; border:3px solid #80DEEA; border-radius:14px; padding:12px; font-size:13pt; font-weight:bold; color:#0F172A; text-align:left; line-height:2.3;">
                ✦ <b style="color:#EA580C;">le pigeon</b> &nbsp;&nbsp;|&nbsp;&nbsp; ✦ <b style="color:#EA580C;">l'aigle</b><br>
                ✦ <b style="color:#EA580C;">l'hirondelle</b> &nbsp;&nbsp;|&nbsp;&nbsp; ✦ <b style="color:#EA580C;">la chauve-souris</b> (mammifère volant)<br>
                ✦ <b style="color:#EA580C;">le perroquet</b> &nbsp;&nbsp;|&nbsp;&nbsp; ✦ <b style="color:#EA580C;">le canard sauvage</b>
            </div>

            <p style="font-size:14pt; font-weight:800; color:#15803D; margin-top:14px; text-align:left;">🦋 2. Les insectes volants :</p>
            <div style="background:#F0FDF4; border:2px dashed #16A34A; border-radius:12px; padding:12px; font-size:12pt; font-weight:bold; color:#166534; text-align:left; line-height:2.2;">
                ✦ <b>le papillon</b> &nbsp;—&nbsp; ✦ <b>l'abeille</b> &nbsp;—&nbsp; ✦ <b>la mouche</b><br>
                ✦ <b>la libellule</b> &nbsp;—&nbsp; ✦ <b>la coccinelle</b> &nbsp;—&nbsp; ✦ <b>le moustique</b> &nbsp;—&nbsp; ✦ <b>la sauterelle</b>
            </div>

            <div style="background:#FFF1F2; border:2px dashed #E11D48; border-radius:12px; padding:10px; margin-top:12px; font-size:11pt; font-weight:bold; color:#9F1239; text-align:left;">
                ⚠️ <b>Attention :</b> Le crabe et l'anguille ne volent pas, ils se déplacent dans l'eau ou sur le sable !
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_lecons_de_chose, "← Revenir aux Leçons de chose")

    def creer_page_chose_marchent(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#0284C7; color:#fff; font-size:14pt; font-weight:bold; padding:6px 16px; border-radius:12px;">📅 Mercredi 01 Octobre 2026</span></p>
            <p style="font-size:18pt; font-weight:900; color:#D90429; margin-top:8px;">LES ANIMAUX QUI MARCHENT</p>
            
            <div style="background:#F3E8FF; border-left:5px solid #9333EA; border-radius:10px; padding:12px; text-align:left; font-size:12pt; line-height:2; color:#6B21A8;">
                ✦ <b>Définition :</b> Les animaux qui marchent sont des animaux terrestres qui se déplacent sur la terre ferme à l'aide de leurs <b>pattes</b> (2 pattes ou 4 pattes).
            </div>

            <p style="font-size:14pt; font-weight:800; color:#7E22CE; margin-top:14px; text-align:left;">🐾 Les animaux qui marchent :</p>
            <div style="background:#FFFFFF; border:3px solid #80DEEA; border-radius:14px; padding:14px; font-size:12pt; font-weight:bold; color:#0F172A; text-align:left; line-height:2.4;">
                ✦ <b style="color:#7C3AED;">le chat</b> &nbsp;&nbsp;|&nbsp;&nbsp; ✦ <b style="color:#7C3AED;">le chien</b> &nbsp;&nbsp;|&nbsp;&nbsp; ✦ <b style="color:#7C3AED;">la chèvre</b><br>
                ✦ <b style="color:#7C3AED;">le lion</b> &nbsp;&nbsp;|&nbsp;&nbsp; ✦ <b style="color:#7C3AED;">le tigre</b> &nbsp;&nbsp;|&nbsp;&nbsp; ✦ <b style="color:#7C3AED;">le léopard</b><br>
                ✦ <b style="color:#7C3AED;">le cheval</b> &nbsp;&nbsp;|&nbsp;&nbsp; ✦ <b style="color:#7C3AED;">le dromadaire</b> &nbsp;&nbsp;|&nbsp;&nbsp; ✦ <b style="color:#7C3AED;">le zèbre</b><br>
                ✦ <b style="color:#7C3AED;">l'éléphant</b> &nbsp;&nbsp;|&nbsp;&nbsp; ✦ <b style="color:#7C3AED;">la girafe</b> &nbsp;&nbsp;|&nbsp;&nbsp; ✦ <b style="color:#7C3AED;">le cerf</b><br>
                ✦ <b style="color:#7C3AED;">la gazelle</b> &nbsp;&nbsp;|&nbsp;&nbsp; ✦ <b style="color:#7C3AED;">l'hippopotame</b> &nbsp;&nbsp;|&nbsp;&nbsp; ✦ <b style="color:#7C3AED;">le rhinocéros</b><br>
                ✦ <b style="color:#7C3AED;">le renard</b> &nbsp;&nbsp;|&nbsp;&nbsp; ✦ <b style="color:#7C3AED;">le canard</b> &nbsp;&nbsp;|&nbsp;&nbsp; ✦ <b style="color:#7C3AED;">l'autruche</b> &nbsp;&nbsp;|&nbsp;&nbsp; ✦ <b style="color:#7C3AED;">le dindon</b>
            </div>

            <div style="background:#F0FDF4; border:2px dashed #16A34A; border-radius:12px; padding:10px; margin-top:14px; font-size:12pt; font-weight:bold; color:#15803D; text-align:left; line-height:2;">
                💡 <b>Distinction utile :</b><br>
                • <b>Quadrupèdes</b> : animaux à 4 pattes (le lion, le chat, le cheval, l'éléphant...)<br>
                • <b>Bipèdes</b> : animaux à 2 pattes (l'autruche, le canard, la poule, le dindon...)
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_lecons_de_chose, "← Revenir aux Leçons de chose")

    def creer_page_chose_rampent(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#0284C7; color:#fff; font-size:14pt; font-weight:bold; padding:6px 16px; border-radius:12px;">📅 Mercredi 10 Octobre 2026</span></p>
            <p style="font-size:18pt; font-weight:900; color:#D90429; margin-top:8px;">LES ANIMAUX QUI RAMPENT</p>
            
            <div style="background:#ECFDF5; border-left:5px solid #059669; border-radius:10px; padding:12px; text-align:left; font-size:12pt; line-height:2; color:#065F46;">
                ✦ <b>Définition :</b> Les animaux qui rampent sont des animaux qui n'ont pas de pattes ou qui ont de très petites pattes, et qui utilisent leur <b>ventre</b> pour avancer et se déplacer (la reptation).
            </div>

            <p style="font-size:14pt; font-weight:800; color:#047857; margin-top:14px; text-align:left;">🐍 Les animaux qui rampent :</p>
            <div style="background:#FFFFFF; border:3px solid #80DEEA; border-radius:14px; padding:14px; font-size:13pt; font-weight:bold; color:#0F172A; text-align:left; line-height:2.4;">
                ✦ <b style="color:#059669;">le serpent</b> &nbsp;&nbsp;|&nbsp;&nbsp; ✦ <b style="color:#059669;">le ver de terre</b><br>
                ✦ <b style="color:#059669;">l'escargot</b> &nbsp;&nbsp;|&nbsp;&nbsp; ✦ <b style="color:#059669;">la chenille</b><br>
                ✦ <b style="color:#059669;">le lézard</b> &nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp; ✦ <b style="color:#059669;">la tortue</b><br>
                ✦ <b style="color:#059669;">le scorpion</b> &nbsp;&nbsp;|&nbsp;&nbsp; ✦ <b style="color:#059669;">le crocodile</b> (au sol)<br>
                ✦ <b style="color:#059669;">la limace</b>
            </div>

            <div style="background:#FFFBEB; border:2px dashed #D97706; border-radius:12px; padding:10px; margin-top:14px; font-size:12pt; font-weight:bold; color:#B45309; text-align:left; line-height:2;">
                💡 <b>Mots à retenir :</b><br>
                • <i>ramper</i> : se déplacer en traînant son corps sur le sol.<br>
                • Le serpent et le ver de terre n'ont pas de pattes ; la chenille et le lézard ont de petites pattes et rasent le sol.
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_lecons_de_chose, "← Revenir aux Leçons de chose")

    # =========================================================================
    # SECTION MÉTHODE BOSCHER
    # =========================================================================
    def creer_page_methode_boscher(self):
        page = QWidget()
        self.style_fond(page)
        l = QVBoxLayout(page)
        l.setContentsMargins(10, 10, 10, 10)

        cadre = QFrame()
        cadre.setStyleSheet("QFrame { background-color: transparent; border: 3px solid #80DEEA; border-radius: 20px; }")
        cadre_l = QVBoxLayout(cadre)

        self.titre_boscher = self.creer_titre("Méthode Boscher\nChoisissez une leçon")
        cadre_l.addWidget(self.titre_boscher)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        conteneur = QWidget()
        conteneur.setStyleSheet("background: transparent;")
        c_layout = QVBoxLayout(conteneur)
        c_layout.setSpacing(8)

        self.groupe_boscher = QButtonGroup(self)
        self.groupe_boscher.setExclusive(True)

        noms_boutons_boscher = [
            "i - u", "o - a", "e", "p", "t", "r", "n", "m", "l", "c",
            "d", "v", "s", "b", "f", "j", "g", "ch", "ou", "on",
            "oi", "an", "in", "br", "fr", "bl", "cl", "ar", "al", "en"
        ]

        self.boutons_methode_boscher = []
        for nom in noms_boutons_boscher:
            b = self.creer_bouton_rose_3d(nom)
            self.groupe_boscher.addButton(b)
            c_layout.addWidget(b)
            self.boutons_methode_boscher.append(b)
            b.clicked.connect(lambda checked=False, btn=b: self.selectionner_boscher(btn.text()))

        scroll.setWidget(conteneur)
        cadre_l.addWidget(scroll, 1)

        self.bouton_choose_boscher = self.creer_bouton_choose("Choose")
        self.bouton_choose_boscher.clicked.connect(self.confirmer_choix_boscher)
        cadre_l.addWidget(self.bouton_choose_boscher)

        btn_ret = QPushButton("← Revenir au choix")
        btn_ret.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ret.setStyleSheet("QPushButton { background-color: #6C757D; color: white; font-size: 15px; font-weight: bold; border-radius: 12px; padding: 6px; }")
        btn_ret.clicked.connect(self.retour_au_choix)
        cadre_l.addWidget(btn_ret)

        l.addWidget(cadre)
        return page

    def creer_page_boscher_iu(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#0284C7; color:#fff; font-size:15pt; font-weight:bold; padding:6px 16px; border-radius:12px;">Méthode Boscher</span></p>
            <p style="font-size:18pt; font-weight:900; color:#D90429; margin-top:8px;">La rue à midi.</p>
            <p style="font-size:26pt; font-weight:900; color:#E11D48; letter-spacing:8px;">i &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; u</p>
            <div style="background:#FFFFFF; border:3px solid #80DEEA; border-radius:14px; padding:12px; font-size:14pt; font-weight:bold; color:#0F172A; line-height:2.4; letter-spacing:3px;">
                i &nbsp;&nbsp;&nbsp; u &nbsp;&nbsp;&nbsp; i &nbsp;&nbsp;&nbsp; i &nbsp;&nbsp;&nbsp; u &nbsp;&nbsp;&nbsp; u &nbsp;&nbsp;&nbsp; i &nbsp;&nbsp;&nbsp; u<br>
                u &nbsp;&nbsp;&nbsp; i &nbsp;&nbsp;&nbsp; u &nbsp;&nbsp;&nbsp; u &nbsp;&nbsp;&nbsp; i &nbsp;&nbsp;&nbsp; i &nbsp;&nbsp;&nbsp; u &nbsp;&nbsp;&nbsp; i
            </div>
            <p style="font-size:14pt; font-weight:bold; color:#2563EB; margin-top:14px;">✍️ Écriture et chiffres :</p>
            <div style="background:#F0F9FF; border:2px dashed #0284C7; border-radius:12px; padding:10px; font-size:13pt; font-weight:bold; color:#0369A1; line-height:2.2;">
                1 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 2 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 1 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 2 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 1 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 2 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 1 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 2<br>
                ✦ 1 hibou &nbsp;&nbsp;|&nbsp;&nbsp; ✦ 2 hirondelles &nbsp;&nbsp;|&nbsp;&nbsp; ✦ la lune
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_methode_boscher, "← Revenir à la Méthode Boscher")

    def creer_page_boscher_oa(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#0284C7; color:#fff; font-size:15pt; font-weight:bold; padding:6px 16px; border-radius:12px;">Méthode Boscher</span></p>
            <p style="font-size:18pt; font-weight:900; color:#D90429; margin-top:8px;">La fête de noël.</p>
            <p style="font-size:26pt; font-weight:900; color:#E11D48; letter-spacing:8px;">o &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; a</p>
            <div style="background:#FFFFFF; border:3px solid #80DEEA; border-radius:14px; padding:12px; font-size:14pt; font-weight:bold; color:#0F172A; line-height:2.4; letter-spacing:3px;">
                u &nbsp;&nbsp;&nbsp; 0 &nbsp;&nbsp;&nbsp; a &nbsp;&nbsp;&nbsp; i &nbsp;&nbsp;&nbsp; o &nbsp;&nbsp;&nbsp; u &nbsp;&nbsp;&nbsp; a &nbsp;&nbsp;&nbsp; 0<br>
                a &nbsp;&nbsp;&nbsp; u &nbsp;&nbsp;&nbsp; 0 &nbsp;&nbsp;&nbsp; a &nbsp;&nbsp;&nbsp; i &nbsp;&nbsp;&nbsp; a &nbsp;&nbsp;&nbsp; 0 &nbsp;&nbsp;&nbsp; i
            </div>
            <p style="font-size:14pt; font-weight:bold; color:#16A34A; margin-top:14px;">🫒 Illustrations & Vocabulaire :</p>
            <div style="background:#F0FDF4; border:2px dashed #16A34A; border-radius:12px; padding:10px; font-size:13pt; font-weight:bold; color:#15803D; line-height:2.2;">
                ✦ 2 olives &nbsp;&nbsp;|&nbsp;&nbsp; ✦ 1 avion &nbsp;&nbsp;|&nbsp;&nbsp; ✦ 1 âne &nbsp;&nbsp;|&nbsp;&nbsp; des abricots<br>
                1 + 1 = 2 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 2 - 1 = 1
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_methode_boscher, "← Revenir à la Méthode Boscher")

    def creer_page_boscher_e(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#0284C7; color:#fff; font-size:15pt; font-weight:bold; padding:6px 16px; border-radius:12px;">Méthode Boscher</span></p>
            <p style="font-size:18pt; font-weight:900; color:#D90429; margin-top:8px;">Le déjeuner de bébé.</p>
            <p style="font-size:24pt; font-weight:900; color:#E11D48; letter-spacing:6px;">e &nbsp;&nbsp;&nbsp; é &nbsp;&nbsp;&nbsp; è &nbsp;&nbsp;&nbsp; ê</p>
            <div style="background:#FFFFFF; border:3px solid #80DEEA; border-radius:14px; padding:12px; font-size:14pt; font-weight:bold; color:#0F172A; line-height:2.4; letter-spacing:3px;">
                è &nbsp;&nbsp;&nbsp; e &nbsp;&nbsp;&nbsp; é &nbsp;&nbsp;&nbsp; ê &nbsp;&nbsp;&nbsp; é &nbsp;&nbsp;&nbsp; è &nbsp;&nbsp;&nbsp; e &nbsp;&nbsp;&nbsp; ê<br>
                é &nbsp;&nbsp;&nbsp; i &nbsp;&nbsp;&nbsp; ê &nbsp;&nbsp;&nbsp; a &nbsp;&nbsp;&nbsp; è &nbsp;&nbsp;&nbsp; 0 &nbsp;&nbsp;&nbsp; u &nbsp;&nbsp;&nbsp; e<br>
                a &nbsp;&nbsp;&nbsp; è &nbsp;&nbsp;&nbsp; 0 &nbsp;&nbsp;&nbsp; e &nbsp;&nbsp;&nbsp; u &nbsp;&nbsp;&nbsp; é &nbsp;&nbsp;&nbsp; i &nbsp;&nbsp;&nbsp; a
            </div>
            <p style="font-size:14pt; font-weight:bold; color:#D97706; margin-top:14px;">🍒 Objets et Calculs :</p>
            <div style="background:#FFFBEB; border:2px dashed #D97706; border-radius:12px; padding:10px; font-size:12pt; font-weight:bold; color:#B45309; line-height:2.2;">
                ✦ 1 échelle &nbsp;—&nbsp; 1 bêche &nbsp;—&nbsp; des pêches &nbsp;—&nbsp; des cerises<br>
                ✦ 1 + 1 + 1 = 3 &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; 3 - 1 = 2 &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; 3 - 2 = 1
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_methode_boscher, "← Revenir à la Méthode Boscher")

    def creer_page_boscher_p(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#0284C7; color:#fff; font-size:15pt; font-weight:bold; padding:6px 16px; border-radius:12px;">Méthode Boscher</span></p>
            <p style="font-size:18pt; font-weight:900; color:#D90429; margin-top:8px;">La poule appelle ses petits.</p>
            <p style="font-size:26pt; font-weight:900; color:#E11D48;">p = p</p>
            <div style="background:#FFFFFF; border:3px solid #80DEEA; border-radius:14px; padding:12px; font-size:14pt; font-weight:bold; color:#0F172A; line-height:2.4;">
                pi . pu . po . pa . pe . pé . pè . pê .<br>
                po . pê . pu . pe . pi . pè . pa . pé .<br>
                <span style="color:#D81B60;">pa pa . pi pe . é pi . pi e .</span>
            </div>
            <p style="font-size:14pt; font-weight:bold; color:#7C3AED; margin-top:14px;">🌾 Mots et Calculs :</p>
            <div style="background:#F5F3FF; border:2px dashed #7C3AED; border-radius:12px; padding:10px; font-size:12pt; font-weight:bold; color:#5B21B6; line-height:2.2;">
                ✦ pipe &nbsp;—&nbsp; papa &nbsp;—&nbsp; épi &nbsp;—&nbsp; pie &nbsp;—&nbsp; poussins<br>
                ✦ 3 + 1 = 4 &nbsp;&nbsp;|&nbsp;&nbsp; 2 + 2 = 4 &nbsp;&nbsp;|&nbsp;&nbsp; 1 + 3 = 4 &nbsp;&nbsp;|&nbsp;&nbsp; 4 - 1 = 3
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_methode_boscher, "← Revenir à la Méthode Boscher")

    def creer_page_boscher_t(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#0284C7; color:#fff; font-size:15pt; font-weight:bold; padding:6px 16px; border-radius:12px;">Méthode Boscher</span></p>
            <p style="font-size:18pt; font-weight:900; color:#D90429; margin-top:8px;">Toto a été têtu.</p>
            <p style="font-size:26pt; font-weight:900; color:#E11D48;">t = t</p>
            <div style="background:#FFFFFF; border:3px solid #80DEEA; border-radius:14px; padding:12px; font-size:14pt; font-weight:bold; color:#0F172A; line-height:2.4;">
                ta . té . ti . te . tu . tè . to . tê .<br>
                to to . tê tu . to mate . tu té . é tu i . tué .<br>
                pa la te . pé té . ta pe . pe ti te . pâ te . é ta pe .<br>
                <span style="color:#2563EB;">to to a é té tê tu . pa pa a ta pé to to .</span>
            </div>
            <p style="font-size:14pt; font-weight:bold; color:#DC2626; margin-top:14px;">🔨 Mots :</p>
            <div style="background:#FEF2F2; border:2px dashed #DC2626; border-radius:12px; padding:10px; font-size:12pt; font-weight:bold; color:#991B1B; line-height:2;">
                la tête . toto . têtu . tomate . étui .<br>
                papa tape à la petite pipe.
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_methode_boscher, "← Revenir à la Méthode Boscher")

    def creer_page_boscher_r(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#0284C7; color:#fff; font-size:15pt; font-weight:bold; padding:6px 16px; border-radius:12px;">Méthode Boscher</span></p>
            <p style="font-size:18pt; font-weight:900; color:#D90429; margin-top:8px;">Le chat ronronne devant le rôti.</p>
            <p style="font-size:26pt; font-weight:900; color:#E11D48;">r = r</p>
            <div style="background:#FFFFFF; border:3px solid #80DEEA; border-radius:14px; padding:12px; font-size:14pt; font-weight:bold; color:#0F172A; line-height:2.4;">
                rê . ra . ré . ru . re . ri . rè . ro .<br>
                ra tiè re . ti re . ra re . ra ta . ra tu re . rue .<br>
                pé re . râ pe . pâ tu re . pa ri . pi re . rô ti .<br>
                <span style="color:#059669;">pa pa a ti ré , a ra té , re ti re ra .</span>
            </div>
            <p style="font-size:14pt; font-weight:bold; color:#D97706; margin-top:14px;">🧀 Vocabulaire & Phrase :</p>
            <div style="background:#FFFBEB; border:2px dashed #D97706; border-radius:12px; padding:10px; font-size:12pt; font-weight:bold; color:#B45309; line-height:2.2;">
                ✦ râpe &nbsp;—&nbsp; rôti &nbsp;—&nbsp; souris &nbsp;—&nbsp; rats &nbsp;—&nbsp; ratière<br>
                ✦ <i>père a réparé la petite ratière.</i><br>
                5 = 00000 &nbsp;|&nbsp; 5 = 000 + 00 &nbsp;|&nbsp; 4 + 1 = 5 &nbsp;|&nbsp; 3 + 2 = 5
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_methode_boscher, "← Revenir à la Méthode Boscher")

    def creer_page_boscher_n(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#0284C7; color:#fff; font-size:15pt; font-weight:bold; padding:6px 16px; border-radius:12px;">Méthode Boscher</span></p>
            <p style="font-size:18pt; font-weight:900; color:#D90429; margin-top:8px;">René cherche des nids.</p>
            <p style="font-size:26pt; font-weight:900; color:#E11D48;">n = n</p>
            <div style="background:#FFFFFF; border:3px solid #80DEEA; border-radius:14px; padding:12px; font-size:14pt; font-weight:bold; color:#0F172A; line-height:2.4;">
                ni . né . na . nè . no . nê . nu . ne .<br>
                ni na . u ne . te nu . pu ni . â ne . u ne no te .<br>
                u ne é pi ne . u ne té ti ne . u ne na ri ne .<br>
                <span style="color:#2563EB;">re né a é té re te nu , pa pa a pu ni re né .</span>
            </div>
            <p style="font-size:14pt; font-weight:bold; color:#16A34A; margin-top:14px;">🪺 Vocabulaire & Phrase :</p>
            <div style="background:#F0FDF4; border:2px dashed #16A34A; border-radius:12px; padding:10px; font-size:12pt; font-weight:bold; color:#15803D; line-height:2.2;">
                ✦ un nid &nbsp;—&nbsp; une tétine &nbsp;—&nbsp; une niche &nbsp;—&nbsp; une noix<br>
                ✦ <i>nina . note . rené . tétine . une épine .</i><br>
                ✦ <i>irène ira nu-tête . rené a été puni .</i>
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_methode_boscher, "← Revenir à la Méthode Boscher")

    def creer_page_boscher_m(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#0284C7; color:#fff; font-size:15pt; font-weight:bold; padding:6px 16px; border-radius:12px;">Méthode Boscher</span></p>
            <p style="font-size:18pt; font-weight:900; color:#D90429; margin-top:8px;">Rémi et Maria partagent une pomme.</p>
            <p style="font-size:26pt; font-weight:900; color:#E11D48;">m = m</p>
            <div style="background:#FFFFFF; border:3px solid #80DEEA; border-radius:14px; padding:12px; font-size:14pt; font-weight:bold; color:#0F172A; line-height:2.4;">
                mé . me . mu . mo . mê . mi . mè . ma .<br>
                mi mi . ma ria . ma mè re . une ma re . une mi ne .<br>
                a mi . nu mé ro . une to ma te . une mi nu te .<br>
                <span style="color:#C026D3;">ré mi a pa ti né , re né a i mi té ré mi .</span>
            </div>
            <p style="font-size:14pt; font-weight:bold; color:#E11D48; margin-top:14px;">🍎 Lecture courante & Calculs :</p>
            <div style="background:#FFF1F2; border:2px dashed #E11D48; border-radius:12px; padding:10px; font-size:12pt; font-weight:bold; color:#9F1239; line-height:2.2;">
                ✦ <i>ma mère a ramené petite maria.</i><br>
                ✦ une mare &nbsp;—&nbsp; une tomate &nbsp;—&nbsp; une minute &nbsp;—&nbsp; les pommes<br>
                6 - 1 = 5 &nbsp;&nbsp;|&nbsp;&nbsp; 6 - 2 = 4 &nbsp;&nbsp;|&nbsp;&nbsp; 6 - 3 = 3 &nbsp;&nbsp;|&nbsp;&nbsp; 6 - 4 = 2
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_methode_boscher, "← Revenir à la Méthode Boscher")

    def creer_page_boscher_l(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#0284C7; color:#fff; font-size:15pt; font-weight:bold; padding:6px 16px; border-radius:12px;">Méthode Boscher</span></p>
            <p style="font-size:18pt; font-weight:900; color:#D90429; margin-top:8px;">Émile soigne les lapins.</p>
            <p style="font-size:26pt; font-weight:900; color:#E11D48;">l = l</p>
            <div style="background:#FFFFFF; border:3px solid #80DEEA; border-radius:14px; padding:12px; font-size:14pt; font-weight:bold; color:#0F172A; line-height:2.4;">
                lê . la . le . lé . li . lè . lo . lu .<br>
                é mi le . la lu ne . le lo to . la la me . la li me .<br>
                la pe lo te . la tu li pe . la pa ro le . la pi le .<br>
                <span style="color:#0284C7;">a li ne ô te ra le rô ti , la to ma te , le pâ té .</span>
            </div>
            <p style="font-size:14pt; font-weight:bold; color:#2563EB; margin-top:14px;">✍️ Écriture et phrase :</p>
            <div style="background:#EFF6FF; border:2px dashed #2563EB; border-radius:12px; padding:10px; font-size:12pt; font-weight:bold; color:#1E40AF; line-height:2.2;">
                ✦ <i>la lime . le loto . une pelote . la parole .</i><br>
                ✦ <i>amélie, retire ta pèlerine .</i>
            </div>
            <p style="font-size:14pt; font-weight:bold; color:#16A34A; margin-top:14px;">🐰 Vocabulaire & Calculs :</p>
            <div style="background:#F0FDF4; border:2px dashed #16A34A; border-radius:12px; padding:10px; font-size:12pt; font-weight:bold; color:#15803D; line-height:2.2;">
                ✦ lièvre &nbsp;—&nbsp; le loto &nbsp;—&nbsp; une pile &nbsp;—&nbsp; une lime &nbsp;—&nbsp; tulipes<br>
                ✦ 6 - 1 = 5 &nbsp;&nbsp;|&nbsp;&nbsp; 6 - 4 = 2 &nbsp;&nbsp;|&nbsp;&nbsp; 3 + 3 = 6 &nbsp;&nbsp;|&nbsp;&nbsp; 6 - 2 = 4
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_methode_boscher, "← Revenir à la Méthode Boscher")

    def creer_page_boscher_c(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#0284C7; color:#fff; font-size:15pt; font-weight:bold; padding:6px 16px; border-radius:12px;">Méthode Boscher</span></p>
            <p style="font-size:18pt; font-weight:900; color:#D90429; margin-top:8px;">Le coq est le roi de la basse-cour.</p>
            <p style="font-size:26pt; font-weight:900; color:#E11D48;">c = c</p>
            <div style="background:#FFFFFF; border:3px solid #80DEEA; border-radius:14px; padding:12px; font-size:14pt; font-weight:bold; color:#0F172A; line-height:2.4;">
                cu . co . ca .<br>
                co co ri co . l'é cu me . la ca pi ta le . la ca ne .<br>
                l'é co le . la ca po te . la co lè re . le ma ca ro ni .<br>
                <span style="color:#D81B60;">ni co le a u ne pe ti te ca pe li ne .</span>
            </div>
            <p style="font-size:14pt; font-weight:bold; color:#D97706; margin-top:14px;">✍️ Écriture et phrase :</p>
            <div style="background:#FFFBEB; border:2px dashed #D97706; border-radius:12px; padding:10px; font-size:12pt; font-weight:bold; color:#B45309; line-height:2.2;">
                ✦ <i>cocorico . le côté . la capote . le macaroni .</i><br>
                ✦ <i>émile a été poli à l'école .</i>
            </div>
            <p style="font-size:14pt; font-weight:bold; color:#DC2626; margin-top:14px;">🥕 Vocabulaire & Calculs :</p>
            <div style="background:#FEF2F2; border:2px dashed #DC2626; border-radius:12px; padding:10px; font-size:12pt; font-weight:bold; color:#991B1B; line-height:2.2;">
                ✦ macaroni &nbsp;—&nbsp; la cape &nbsp;—&nbsp; carottes &nbsp;—&nbsp; canards<br>
                ✦ 7 = 5 + 2 &nbsp;&nbsp;|&nbsp;&nbsp; 7 = 3 + 4 &nbsp;&nbsp;|&nbsp;&nbsp; 3 + 4 = 7 &nbsp;&nbsp;|&nbsp;&nbsp; 1 + 6 = 7
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_methode_boscher, "← Revenir à la Méthode Boscher")

    def creer_page_boscher_d(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#0284C7; color:#fff; font-size:15pt; font-weight:bold; padding:6px 16px; border-radius:12px;">Méthode Boscher</span></p>
            <p style="font-size:18pt; font-weight:900; color:#D90429; margin-top:8px;">Dédé est malade.</p>
            <p style="font-size:26pt; font-weight:900; color:#E11D48;">d = d</p>
            <div style="background:#FFFFFF; border:3px solid #80DEEA; border-radius:14px; padding:12px; font-size:14pt; font-weight:bold; color:#0F172A; line-height:2.4;">
                da . dê . de . du . dè . do . di . dé .<br>
                le do do de dé dé . le ma la de . le re mè de .<br>
                u ne da me . le ca ma ra de . le do mi no .<br>
                la mo de . la pé da le . le mo dè le . le dé po té .<br>
                <span style="color:#7C3AED;">ma da me dî ne ra à mi di de pâ té , de rô ti .</span>
            </div>
            <p style="font-size:14pt; font-weight:bold; color:#7C3AED; margin-top:14px;">✍️ Écriture et phrase :</p>
            <div style="background:#F5F3FF; border:2px dashed #7C3AED; border-radius:12px; padding:10px; font-size:12pt; font-weight:bold; color:#5B21B6; line-height:2.2;">
                ✦ <i>la dame . une pédale . le camarade .</i><br>
                ✦ <i>adèle a copié le modèle de nicole .</i>
            </div>
            <p style="font-size:14pt; font-weight:bold; color:#16A34A; margin-top:14px;">🎲 Vocabulaire & Calculs :</p>
            <div style="background:#F0FDF4; border:2px dashed #16A34A; border-radius:12px; padding:10px; font-size:12pt; font-weight:bold; color:#15803D; line-height:2.2;">
                ✦ dé &nbsp;—&nbsp; le dodo &nbsp;—&nbsp; damier &nbsp;—&nbsp; domino &nbsp;—&nbsp; radis<br>
                ✦ 7 = 2 + 2 + 2 + 1 &nbsp;&nbsp;|&nbsp;&nbsp; 7 = 3 + 3 + 1 &nbsp;&nbsp;|&nbsp;&nbsp; 7 = 6 + 1
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_methode_boscher, "← Revenir à la Méthode Boscher")

    def creer_page_boscher_v(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#0284C7; color:#fff; font-size:15pt; font-weight:bold; padding:6px 16px; border-radius:12px;">Méthode Boscher</span></p>
            <p style="font-size:18pt; font-weight:900; color:#D90429; margin-top:8px;">L'avion va vite.</p>
            <p style="font-size:26pt; font-weight:900; color:#E11D48;">v = v</p>
            <div style="background:#FFFFFF; border:3px solid #80DEEA; border-radius:14px; padding:12px; font-size:14pt; font-weight:bold; color:#0F172A; line-height:2.4;">
                vo . vé . vê . va . vu . ve . vi . vè .<br>
                la lo co mo ti ve . le na vi re . la vé ri té .<br>
                de vi ne . la ve . a va le . dé vo ré . vê tu . vi dé .<br>
                l'a va re . le pa vé . le rê ve . u ne vi pè re .<br>
                <span style="color:#0284C7;">la pi e vo le . é ve li ne va vi te à la ca ve .</span>
            </div>
            <p style="font-size:14pt; font-weight:bold; color:#0369A1; margin-top:14px;">✍️ Écriture et phrase :</p>
            <div style="background:#F0F9FF; border:2px dashed #0284C7; border-radius:12px; padding:10px; font-size:12pt; font-weight:bold; color:#075985; line-height:2.2;">
                ✦ <i>la vérité . vide la cuve . le navire va vite .</i><br>
                ✦ <i>éva a vu une vipère à côté d'adèle .</i>
            </div>
            <p style="font-size:14pt; font-weight:bold; color:#D97706; margin-top:14px;">🚢 Vocabulaire & Calculs :</p>
            <div style="background:#FFFBEB; border:2px dashed #D97706; border-radius:12px; padding:10px; font-size:12pt; font-weight:bold; color:#B45309; line-height:2.2;">
                ✦ navire à vapeur &nbsp;—&nbsp; vipère &nbsp;—&nbsp; cuve &nbsp;—&nbsp; avion &nbsp;—&nbsp; navets &nbsp;—&nbsp; voiles<br>
                ✦ 8 = 2 + 2 + 2 + 2 &nbsp;&nbsp;|&nbsp;&nbsp; 8 = 4 + 4 &nbsp;&nbsp;|&nbsp;&nbsp; 6 + 2 = 8 &nbsp;&nbsp;|&nbsp;&nbsp; 5 + 3 = 8
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_methode_boscher, "← Revenir à la Méthode Boscher")

    def creer_page_boscher_s(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#0284C7; color:#fff; font-size:15pt; font-weight:bold; padding:6px 16px; border-radius:12px;">Méthode Boscher</span></p>
            <p style="font-size:18pt; font-weight:900; color:#D90429; margin-top:8px;">Le semeur.</p>
            <p style="font-size:26pt; font-weight:900; color:#E11D48;">s = s</p>
            <div style="background:#FFFFFF; border:3px solid #80DEEA; border-radius:14px; padding:12px; font-size:14pt; font-weight:bold; color:#0F172A; line-height:2.4;">
                su . sé . so . sê . si . sa . se . sè .<br>
                si mo ne . sè me . si do ni e . sa me di . sè ve .<br>
                la sè ve . le so li de . la se ri ne . la sa va te .<br>
                la sa li è re . de la sa li ve . de la sa la de .<br>
                <span style="color:#16A34A;">si mo ne a sa li sa ca pe . sa mè re la la ve ra .</span>
            </div>
            <p style="font-size:14pt; font-weight:bold; color:#15803D; margin-top:14px;">✍️ Écriture et phrase :</p>
            <div style="background:#F0FDF4; border:2px dashed #16A34A; border-radius:12px; padding:10px; font-size:12pt; font-weight:bold; color:#14532D; line-height:2.2;">
                ✦ <i>la dame arrive . la soupe de la salade .</i><br>
                ✦ <i>sidonie sèmera de la salade .</i>
            </div>
            <p style="font-size:14pt; font-weight:bold; color:#E11D48; margin-top:14px;">🌱 Vocabulaire :</p>
            <div style="background:#FFF1F2; border:2px dashed #E11D48; border-radius:12px; padding:10px; font-size:12pt; font-weight:bold; color:#9F1239; line-height:2.2;">
                ✦ le semeur &nbsp;—&nbsp; la salade &nbsp;—&nbsp; la terrine &nbsp;—&nbsp; la savate<br>
                ✦ 8 = 4 + 4 &nbsp;&nbsp;|&nbsp;&nbsp; 8 = 5 + 3 &nbsp;&nbsp;|&nbsp;&nbsp; 8 = 6 + 2 &nbsp;&nbsp;|&nbsp;&nbsp; 8 = 7 + 1
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_methode_boscher, "← Revenir à la Méthode Boscher")

    def creer_page_boscher_b(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#0284C7; color:#fff; font-size:15pt; font-weight:bold; padding:6px 16px; border-radius:12px;">Méthode Boscher</span></p>
            <p style="font-size:18pt; font-weight:900; color:#D90429; margin-top:8px;">La cabane du sabotier.</p>
            <p style="font-size:26pt; font-weight:900; color:#E11D48;">b = b</p>
            <div style="background:#FFFFFF; border:3px solid #80DEEA; border-radius:14px; padding:12px; font-size:14pt; font-weight:bold; color:#0F172A; line-height:2.4;">
                bè . ba . be . bo . bê . bi . bé . bu .<br>
                la sa bo tiè re . du bo bo . la bê te . la ro be . le tu be .<br>
                u ne ca ra bi ne . u ne ca bi ne . de la bi è re .<br>
                lé a dé vi de la bo bi ne . bé bé a sa li sa ro be .<br>
                <span style="color:#9333EA;">le pè re d'é va bâ ti ra u ne ca ba ne so li de .</span>
            </div>
            <p style="font-size:14pt; font-weight:bold; color:#7E22CE; margin-top:14px;">✍️ Écriture et phrase :</p>
            <div style="background:#FAF5FF; border:2px dashed #9333EA; border-radius:12px; padding:10px; font-size:12pt; font-weight:bold; color:#581C87; line-height:2.2;">
                ✦ <i>bête . cabane . sabotière . lave la robe .</i><br>
                ✦ <i>adèle dévidera la bobine .</i>
            </div>
            <p style="font-size:14pt; font-weight:bold; color:#C2410C; margin-top:14px;">🪵 Vocabulaire & Calculs :</p>
            <div style="background:#FFF7ED; border:2px dashed #EA580C; border-radius:12px; padding:10px; font-size:12pt; font-weight:bold; color:#9A3412; line-height:2.2;">
                ✦ cabane &nbsp;—&nbsp; bobine &nbsp;—&nbsp; 9 sabots &nbsp;—&nbsp; bûchette &nbsp;—&nbsp; carabine<br>
                ✦ 9 = 2 + 2 + 2 + 2 + 1 &nbsp;&nbsp;|&nbsp;&nbsp; 9 = 4 + 4 + 1 &nbsp;&nbsp;|&nbsp;&nbsp; 9 = 8 + 1 &nbsp;&nbsp;|&nbsp;&nbsp; 9 = 6 + 3
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_methode_boscher, "← Revenir à la Méthode Boscher")

    def creer_page_boscher_f(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#0284C7; color:#fff; font-size:15pt; font-weight:bold; padding:6px 16px; border-radius:12px;">Méthode Boscher</span></p>
            <p style="font-size:18pt; font-weight:900; color:#D90429; margin-top:8px;">Éva fera du café.</p>
            <p style="font-size:26pt; font-weight:900; color:#E11D48;">f = f</p>
            <div style="background:#FFFFFF; border:3px solid #80DEEA; border-radius:14px; padding:12px; font-size:14pt; font-weight:bold; color:#0F172A; line-height:2.4;">
                fu . fé . fo . fe . fê . fi . fa . fè .<br>
                ca fe tiè re . ca lo ri fè re . ca ra fe . fa mi ne .<br>
                u ne fè ve . u ne fê te . de la fa ri ne . fi ni .<br>
                la ca ba ne fu me . la lo co mo ti ve fi le vi te .<br>
                <span style="color:#D90429;">é va fe ra du ca fé . sa mè re fe ra du ba ba .</span>
            </div>
            <p style="font-size:14pt; font-weight:bold; color:#B91C1C; margin-top:14px;">✍️ Écriture et phrase :</p>
            <div style="background:#FEF2F2; border:2px dashed #DC2626; border-radius:12px; padding:10px; font-size:12pt; font-weight:bold; color:#991B1B; line-height:2.2;">
                ✦ <i>farine . fève . café . une carafe de bière .</i><br>
                ✦ <i>liliane sera à la fête de papa samedi .</i>
            </div>
            <p style="font-size:14pt; font-weight:bold; color:#047857; margin-top:14px;">☕ Vocabulaire & Calculs :</p>
            <div style="background:#ECFDF5; border:2px dashed #059669; border-radius:12px; padding:10px; font-size:12pt; font-weight:bold; color:#065F46; line-height:2.2;">
                ✦ le café &nbsp;—&nbsp; la carafe &nbsp;—&nbsp; les fèves &nbsp;—&nbsp; la farine<br>
                ✦ 9 = 10 - 1 &nbsp;&nbsp;|&nbsp;&nbsp; 10 - 9 = 1 &nbsp;&nbsp;|&nbsp;&nbsp; 9 - 3 = 6 &nbsp;&nbsp;|&nbsp;&nbsp; 9 - 6 = 3
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_methode_boscher, "← Revenir à la Méthode Boscher")

    def creer_page_boscher_j(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#0284C7; color:#fff; font-size:15pt; font-weight:bold; padding:6px 16px; border-radius:12px;">Méthode Boscher</span></p>
            <p style="font-size:18pt; font-weight:900; color:#D90429; margin-top:8px;">La joie au jour de l'an.</p>
            <p style="font-size:26pt; font-weight:900; color:#E11D48;">j = j</p>
            <div style="background:#FFFFFF; border:3px solid #80DEEA; border-radius:14px; padding:12px; font-size:14pt; font-weight:bold; color:#0F172A; line-height:2.4;">
                jo . jé . ju . je . ja . jè . ji . jê .<br>
                u ne jo li e ju pe . bé bé ca jo le sa mè re .<br>
                je rê ve . je me lè ve . je me la ve . je dî ne .<br>
                je sè me . je fu me . je vi de la ca ra fe .<br>
                <span style="color:#0284C7;">ja ni ne fe ra u ne jo li e ro be à si mo ne .</span>
            </div>
            <p style="font-size:14pt; font-weight:bold; color:#1D4ED8; margin-top:14px;">✍️ Écriture et phrase :</p>
            <div style="background:#EFF6FF; border:2px dashed #2563EB; border-radius:12px; padding:10px; font-size:12pt; font-weight:bold; color:#1E40AF; line-height:2.2;">
                ✦ <i>je rêve . je me lave . je dîne . je cajole .</i><br>
                ✦ <i>julia a déjà réparé la robe de sa mère .</i>
            </div>
            <p style="font-size:14pt; font-weight:bold; color:#B45309; margin-top:14px;">🧸 Vocabulaire & Calculs :</p>
            <div style="background:#FFFBEB; border:2px dashed #D97706; border-radius:12px; padding:10px; font-size:12pt; font-weight:bold; color:#78350F; line-height:2.2;">
                ✦ la jupe &nbsp;—&nbsp; des jouets &nbsp;—&nbsp; des jetons &nbsp;—&nbsp; 10 jacinthes<br>
                ✦ 10 = 2 + 2 + 2 + 2 + 2 &nbsp;&nbsp;|&nbsp;&nbsp; 10 = 5 + 5 &nbsp;&nbsp;|&nbsp;&nbsp; 10 = 8 + 2 &nbsp;&nbsp;|&nbsp;&nbsp; 10 = 7 + 3
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_methode_boscher, "← Revenir à la Méthode Boscher")

    def creer_page_boscher_g(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#0284C7; color:#fff; font-size:15pt; font-weight:bold; padding:6px 16px; border-radius:12px;">Méthode Boscher</span></p>
            <p style="font-size:18pt; font-weight:900; color:#D90429; margin-top:8px;">Le marché aux légumes.</p>
            <p style="font-size:26pt; font-weight:900; color:#E11D48;">g = g</p>
            <div style="background:#FFFFFF; border:3px solid #80DEEA; border-radius:14px; padding:12px; font-size:14pt; font-weight:bold; color:#0F172A; line-height:2.4;">
                ga . go . gu .<br>
                le lé gu me . la ga re . la ri go le . l'é ga li té .<br>
                u ne ré ga la de . u ne ga le rie . é ga ré . gâ té .<br>
                u ne fi gu re . du ma la ga . la ga le . je fa go te .<br>
                <span style="color:#2563EB;">la bê te de jé rô me ga lo pe vi te .</span>
            </div>
            <p style="font-size:14pt; font-weight:bold; color:#16A34A; margin-top:14px;">✍️ Écriture et phrase :</p>
            <div style="background:#F0FDF4; border:2px dashed #16A34A; border-radius:12px; padding:10px; font-size:12pt; font-weight:bold; color:#15803D; line-height:2.2;">
                ✦ <i>gare . galopade . une gamine . je fagote .</i><br>
                ✦ <i>émile se lavera la figure, ira à l'école .</i>
            </div>
            <p style="font-size:14pt; font-weight:bold; color:#D97706; margin-top:14px;">🥕 Vocabulaire & Calculs :</p>
            <div style="background:#FFFBEB; border:2px dashed #D97706; border-radius:12px; padding:10px; font-size:12pt; font-weight:bold; color:#B45309; line-height:2.2;">
                ✦ légumes &nbsp;—&nbsp; la gare &nbsp;—&nbsp; la galerie &nbsp;—&nbsp; la gourde<br>
                ✦ 10 - 5 = 5 &nbsp;&nbsp;|&nbsp;&nbsp; 10 - 4 = 6 &nbsp;&nbsp;|&nbsp;&nbsp; 10 - 3 = 7 &nbsp;&nbsp;|&nbsp;&nbsp; 10 - 2 = 8
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_methode_boscher, "← Revenir à la Méthode Boscher")

    def creer_page_boscher_ch(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#0284C7; color:#fff; font-size:15pt; font-weight:bold; padding:6px 16px; border-radius:12px;">Méthode Boscher</span></p>
            <p style="font-size:18pt; font-weight:900; color:#D90429; margin-top:8px;">Le cheval tire la charrue.</p>
            <p style="font-size:26pt; font-weight:900; color:#E11D48;">ch = ch</p>
            <div style="background:#FFFFFF; border:3px solid #80DEEA; border-radius:14px; padding:12px; font-size:14pt; font-weight:bold; color:#0F172A; line-height:2.4;">
                cha . chi . che . chê . cho . chè . chu .<br>
                u ne bû che . de chê ne . la ga lo che . la chi ca ne .<br>
                la va che . le fi chu . le châ le . la che ve lu re .<br>
                je che mi ne . je bê che . je pê che . je me fâ che .<br>
                <span style="color:#C026D3;">mi che li ne a dé chi ré la po che de sa ro be .</span>
            </div>
            <p style="font-size:14pt; font-weight:bold; color:#9333EA; margin-top:14px;">✍️ Écriture et phrase :</p>
            <div style="background:#FAF5FF; border:2px dashed #9333EA; border-radius:12px; padding:10px; font-size:12pt; font-weight:bold; color:#6B21A8; line-height:2.2;">
                ✦ <i>je pèle une pêche . je fagote du chêne .</i><br>
                ✦ <i>la gamine a égaré le fichu de sa mère .</i>
            </div>
            <p style="font-size:14pt; font-weight:bold; color:#DC2626; margin-top:14px;">🐴 Vocabulaire & Calculs :</p>
            <div style="background:#FEF2F2; border:2px dashed #DC2626; border-radius:12px; padding:10px; font-size:12pt; font-weight:bold; color:#991B1B; line-height:2.2;">
                ✦ cheval &nbsp;—&nbsp; charrue &nbsp;—&nbsp; chat &nbsp;—&nbsp; ruche &nbsp;—&nbsp; 10 châtaignes<br>
                ✦ 9 + 1 = 10 &nbsp;&nbsp;|&nbsp;&nbsp; 8 + 2 = 10 &nbsp;&nbsp;|&nbsp;&nbsp; 7 + 3 = 10 &nbsp;&nbsp;|&nbsp;&nbsp; 6 + 4 = 10
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_methode_boscher, "← Revenir à la Méthode Boscher")

    def creer_page_boscher_ou(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#0284C7; color:#fff; font-size:15pt; font-weight:bold; padding:6px 16px; border-radius:12px;">Méthode Boscher</span></p>
            <p style="font-size:18pt; font-weight:900; color:#D90429; margin-top:8px;">La soupe aux choux.</p>
            <p style="font-size:26pt; font-weight:900; color:#E11D48;">ou = ou</p>
            <div style="background:#FFFFFF; border:3px solid #80DEEA; border-radius:14px; padding:12px; font-size:14pt; font-weight:bold; color:#0F172A; line-height:2.4;">
                cou . sou . fou . chou . pou . vou . gou .<br>
                la sou piè re . la bou che . le cou de . le bi jou .<br>
                la sou cou pe . la cha lou pe . la cou tu re . la dou ve .<br>
                un fi lou . un mou le . u ne rou te . un jou jou . un sou .<br>
                la cu ve cou le . la pou le cou ve . la bou le rou le .<br>
                <span style="color:#059669;">ju le cou pe un chou , le cou cou a va lé u ne mou che .</span>
            </div>
            <p style="font-size:14pt; font-weight:bold; color:#047857; margin-top:14px;">✍️ Écriture et phrase :</p>
            <div style="background:#ECFDF5; border:2px dashed #059669; border-radius:12px; padding:10px; font-size:12pt; font-weight:bold; color:#065F46; line-height:2.2;">
                ✦ <i>la poule . une douve . une boule . un coucou .</i><br>
                ✦ <i>éliane achète un joujou , je débouche la carafe .</i><br>
                ✦ <i>ma mère coupera un chou , fera de la soupe .</i>
            </div>
            <p style="font-size:14pt; font-weight:bold; color:#D97706; margin-top:14px;">🥬 Vocabulaire & Calculs :</p>
            <div style="background:#FFFBEB; border:2px dashed #D97706; border-radius:12px; padding:10px; font-size:12pt; font-weight:bold; color:#B45309; line-height:2.2;">
                ✦ chou &nbsp;—&nbsp; soupe &nbsp;—&nbsp; marmite &nbsp;—&nbsp; toupie &nbsp;—&nbsp; 10 boules<br>
                ✦ 10 - 1 = 9 &nbsp;&nbsp;|&nbsp;&nbsp; 10 - 2 = 8 &nbsp;&nbsp;|&nbsp;&nbsp; 10 - 3 = 7 &nbsp;&nbsp;|&nbsp;&nbsp; 10 - 4 = 6
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_methode_boscher, "← Revenir à la Méthode Boscher")

    def creer_page_boscher_on(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#0284C7; color:#fff; font-size:15pt; font-weight:bold; padding:6px 16px; border-radius:12px;">Méthode Boscher</span></p>
            <p style="font-size:18pt; font-weight:900; color:#D90429; margin-top:8px;">Léon achète du bonbon.</p>
            <p style="font-size:26pt; font-weight:900; color:#E11D48;">on = on</p>
            <div style="background:#FFFFFF; border:3px solid #80DEEA; border-radius:14px; padding:12px; font-size:14pt; font-weight:bold; color:#0F172A; line-height:2.4;">
                bon . mon . ton . son . ron . lon . gon .<br>
                con fi tu re . bâ ton . co ton . con te . ga lon . ron de .<br>
                mon ca pu chon . ton pe lo ton . un bon ja pon .<br>
                un bou ton . un gou jon . un mou ton . un bou chon .<br>
                <span style="color:#D90429;">lé on a du bon bon . é cou te le son du vi o lon .</span><br>
                <span style="color:#2563EB;">si mon a ton du son jo li mou ton .</span>
            </div>
            <p style="font-size:14pt; font-weight:bold; color:#B91C1C; margin-top:14px;">✍️ Écriture et phrase :</p>
            <div style="background:#FEF2F2; border:2px dashed #DC2626; border-radius:12px; padding:10px; font-size:12pt; font-weight:bold; color:#991B1B; line-height:2.2;">
                ✦ <i>le savon . la confiture . un bouchon . le canon .</i><br>
                ✦ <i>léon a goûté le melon . déroule ton peloton .</i><br>
                ✦ <i>léontine a déchiré le galon de son jupon .</i>
            </div>
            <p style="font-size:14pt; font-weight:bold; color:#1E3A8A; margin-top:14px;">🍬 Vocabulaire & Nombres pairs :</p>
            <div style="background:#EFF6FF; border:2px dashed #2563EB; border-radius:12px; padding:10px; font-size:12pt; font-weight:bold; color:#1E40AF; line-height:2.2;">
                ✦ un mouton &nbsp;—&nbsp; un violon &nbsp;—&nbsp; un melon &nbsp;—&nbsp; des boutons<br>
                ✦ 0 + 2 = 2 &nbsp;&nbsp;|&nbsp;&nbsp; 2 + 2 = 4 &nbsp;&nbsp;|&nbsp;&nbsp; 4 + 2 = 6 &nbsp;&nbsp;|&nbsp;&nbsp; 6 + 2 = 8 &nbsp;&nbsp;|&nbsp;&nbsp; 8 + 2 = 10
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_methode_boscher, "← Revenir à la Méthode Boscher")

    def creer_page_boscher_oi(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#0284C7; color:#fff; font-size:15pt; font-weight:bold; padding:6px 16px; border-radius:12px;">Méthode Boscher</span></p>
            <p style="font-size:18pt; font-weight:900; color:#D90429; margin-top:8px;">Toinon garde ses oies.</p>
            <p style="font-size:26pt; font-weight:900; color:#E11D48;">oi = oi</p>
            <div style="background:#FFFFFF; border:3px solid #80DEEA; border-radius:14px; padding:12px; font-size:14pt; font-weight:bold; color:#0F172A; line-height:2.4;">
                voi . toi . boi . moi . foi . poi . noi . joi .<br>
                voi la . u ne voi tu re . u ne é toi le . hor re .<br>
                de l'a voi ne . u ne é cu moi re . u ne pi voi ne .<br>
                u ne poi re . un con voi . la boî te . la mé moi re .<br>
                la cha lou pe à voi le . u ne fi gu re tou te noi re .<br>
                <span style="color:#0284C7;">toi non a chè te ra un cou pon de toi le à la foi re .</span>
            </div>
            <p style="font-size:14pt; font-weight:bold; color:#0369A1; margin-top:14px;">✍️ Écriture et phrase :</p>
            <div style="background:#F0F9FF; border:2px dashed #0284C7; border-radius:12px; padding:10px; font-size:12pt; font-weight:bold; color:#075985; line-height:2.2;">
                ✦ <i>la mémoire . une foire . la voiture . une boîte .</i><br>
                ✦ <i>voilà du bonbon . simon a semé de l'avoine .</i><br>
                ✦ <i>toinon coupera la toile , léa fera la couette .</i>
            </div>
            <p style="font-size:14pt; font-weight:bold; color:#D97706; margin-top:14px;">🦆 Vocabulaire & Nombres impairs :</p>
            <div style="background:#FFFBEB; border:2px dashed #D97706; border-radius:12px; padding:10px; font-size:12pt; font-weight:bold; color:#B45309; line-height:2.2;">
                ✦ oie &nbsp;—&nbsp; passoire &nbsp;—&nbsp; voile &nbsp;—&nbsp; armoire &nbsp;—&nbsp; pivoine<br>
                ✦ 1 . 3 . 5 . 7 . 9 &nbsp;&nbsp;|&nbsp;&nbsp; 1 + 2 = 3 &nbsp;&nbsp;|&nbsp;&nbsp; 3 + 2 = 5 &nbsp;&nbsp;|&nbsp;&nbsp; 5 + 2 = 7 &nbsp;&nbsp;|&nbsp;&nbsp; 7 + 2 = 9
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_methode_boscher, "← Revenir à la Méthode Boscher")

    def creer_page_boscher_an(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#0284C7; color:#fff; font-size:15pt; font-weight:bold; padding:6px 16px; border-radius:12px;">Méthode Boscher</span></p>
            <p style="font-size:18pt; font-weight:900; color:#D90429; margin-top:8px;">Entrez dans la danse.</p>
            <p style="font-size:26pt; font-weight:900; color:#E11D48;">an = an</p>
            <div style="background:#FFFFFF; border:3px solid #80DEEA; border-radius:14px; padding:12px; font-size:14pt; font-weight:bold; color:#0F172A; line-height:2.4;">
                pan . gan . man . chan . ban . can . dan .<br>
                u ne chan son . u ne man da ri ne . ma man . ma tan te .<br>
                la san té . u ne a man de . la man che . la fan fa re .<br>
                un ru ban . mon pan ta lon . un ou ra gan . an toi ne .<br>
                fan chon la ve la ban de de toi le , je cou pe la poi re .<br>
                <span style="color:#D81B60;">jean dan se ra di man che à la fê te du can ton .</span>
            </div>
            <p style="font-size:14pt; font-weight:bold; color:#C026D3; margin-top:14px;">✍️ Écriture et phrase :</p>
            <div style="background:#FAF5FF; border:2px dashed #A855F7; border-radius:12px; padding:10px; font-size:12pt; font-weight:bold; color:#7E22CE; line-height:2.2;">
                ✦ <i>la danse . une chanson . un ouragan . ma tante .</i><br>
                ✦ <i>la méchante boude . voilà la soupe fumante .</i><br>
                ✦ <i>antoine a déchiré son joli pantalon de coton .</i>
            </div>
            <p style="font-size:14pt; font-weight:bold; color:#16A34A; margin-top:14px;">🍊 Vocabulaire & Moitiés :</p>
            <div style="background:#F0FDF4; border:2px dashed #16A34A; border-radius:12px; padding:10px; font-size:12pt; font-weight:bold; color:#15803D; line-height:2.2;">
                ✦ un banc &nbsp;—&nbsp; mandarine &nbsp;—&nbsp; un ruban &nbsp;—&nbsp; anse &nbsp;—&nbsp; amandes<br>
                ✦ moitié de 2 = 1 &nbsp;&nbsp;|&nbsp;&nbsp; de 4 = 2 &nbsp;&nbsp;|&nbsp;&nbsp; de 6 = 3 &nbsp;&nbsp;|&nbsp;&nbsp; de 8 = 4 &nbsp;&nbsp;|&nbsp;&nbsp; de 10 = 5
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_methode_boscher, "← Revenir à la Méthode Boscher")

    def creer_page_boscher_in(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#0284C7; color:#fff; font-size:15pt; font-weight:bold; padding:6px 16px; border-radius:12px;">Méthode Boscher</span></p>
            <p style="font-size:18pt; font-weight:900; color:#D90429; margin-top:8px;">Le poteau indicateur.</p>
            <p style="font-size:26pt; font-weight:900; color:#E11D48;">in = in</p>
            <div style="background:#FFFFFF; border:3px solid #80DEEA; border-radius:14px; padding:12px; font-size:14pt; font-weight:bold; color:#0F172A; line-height:2.4;">
                vin . lin . pin . fin . tin . rin . min . din .<br>
                le sa pin . le che min . le ga min . le ma rin . ma lin .<br>
                un la pin . un din don . u ne din de . le ca le pin .<br>
                la pin ta de . du bou din . le pé pin . un pan tin . du lin .<br>
                u ne re din go te noi re . an to nin fe ra du bon vin .<br>
                <span style="color:#2563EB;">le pin son chan te de bon ma tin à cô té du mou lin .</span>
            </div>
            <p style="font-size:14pt; font-weight:bold; color:#1D4ED8; margin-top:14px;">✍️ Écriture et phrase :</p>
            <div style="background:#EFF6FF; border:2px dashed #2563EB; border-radius:12px; padding:10px; font-size:12pt; font-weight:bold; color:#1E40AF; line-height:2.2;">
                ✦ <i>un calepin . du boudin . un sapin . le chemin .</i><br>
                ✦ <i>le gamin fera le pantin . le pépin de la poire .</i><br>
                ✦ <i>mon lapin a dévoré toute l'avoine de ma tante .</i>
            </div>
            <p style="font-size:14pt; font-weight:bold; color:#16A34A; margin-top:14px;">🌲 Vocabulaire & Calculs :</p>
            <div style="background:#F0FDF4; border:2px dashed #16A34A; border-radius:12px; padding:10px; font-size:12pt; font-weight:bold; color:#15803D; line-height:2.2;">
                ✦ un sapin &nbsp;—&nbsp; un dindon &nbsp;—&nbsp; 3 pintades &nbsp;—&nbsp; le moulin<br>
                ✦ 1 + 3 = 4 &nbsp;&nbsp;|&nbsp;&nbsp; 4 + 3 = 7 &nbsp;&nbsp;|&nbsp;&nbsp; 7 + 3 = 10 &nbsp;&nbsp;|&nbsp;&nbsp; 9 - 3 = 6 &nbsp;&nbsp;|&nbsp;&nbsp; 6 - 3 = 3
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_methode_boscher, "← Revenir à la Méthode Boscher")

    def creer_page_boscher_br(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#0284C7; color:#fff; font-size:14pt; font-weight:bold; padding:6px 16px; border-radius:12px;">Méthode Boscher</span></p>
            <p style="font-size:11pt; color:#64748B; font-weight:bold; margin:4px 0;">in. oi. eu. un. on. an. ou.</p>
            <p style="font-size:19pt; font-weight:900; color:#D90429; margin:6px 0;">la chèvre broute.</p>
            <p style="font-size:26pt; font-weight:900; color:#E11D48; margin:4px 0;">br. &nbsp; pr. &nbsp; dr. &nbsp; vr.</p>
            
            <div style="background:#FFFFFF; border:3px solid #80DEEA; border-radius:14px; padding:12px; font-size:13pt; font-weight:bold; color:#0F172A; line-height:2.2;">
                <span style="color:#C026D3; font-size:15pt;">pro. vre. bran. droi. vri. pru. dré.</span><br><br>
                lè vre. fou dre. pro me na de. brû lu re. pro fon de.<br>
                pou dre. li è vre. bro che. bra vou re. a droi te.<br>
                la pro pre té. un ca dre. u ne cou leu vre. je bro de.<br>
                u ne bran che de sa pin. ta fi gu re se ra pro pre.<br>
                an dré, prê te-moi un li vre, la chè vre brou te le pré.<br>
                ma man a pré pa ré un bon pâ té de li è vre.
            </div>

            <p style="font-size:14pt; font-weight:bold; color:#0D47A1; margin-top:12px;">✍️ Écriture courante (cursive) :</p>
            <div style="background:#F0F9FF; border:2px dashed #0284C7; border-radius:12px; padding:12px; font-size:12pt; font-style:italic; font-weight:bold; color:#0369A1; line-height:2.1; text-align:left;">
                un lièvre. une prune. la foudre. je brode.<br>
                maman achète du poivre. voilà la broche.<br>
                andré a vu une couleuvre à la promenade.
            </div>

            <p style="font-size:14pt; font-weight:bold; color:#16A34A; margin-top:12px;">🖼️ Objets & Calculs :</p>
            <div style="background:#F0FDF4; border:2px dashed #16A34A; border-radius:12px; padding:10px; font-size:11pt; font-weight:bold; color:#15803D; line-height:2;">
                ✦ un cadre &nbsp;|&nbsp; ✦ une couleuvre &nbsp;|&nbsp; ✦ des prunes<br>
                <b>11 = 10 + 1</b><br>
                11 = 9 + 2 &nbsp;&nbsp;|&nbsp;&nbsp; 11 = 8 + 3 &nbsp;&nbsp;|&nbsp;&nbsp; 3 + 8 = 11 &nbsp;&nbsp;|&nbsp;&nbsp; 1 + 10 = 11<br>
                11 = 8 + 3 &nbsp;&nbsp;|&nbsp;&nbsp; 11 = 6 + 5 &nbsp;&nbsp;|&nbsp;&nbsp; 5 + 6 = 11 &nbsp;&nbsp;|&nbsp;&nbsp; 4 + 7 = 11<br>
                11 = 7 + 4 &nbsp;&nbsp;|&nbsp;&nbsp; 11 = 4 + 7 &nbsp;&nbsp;|&nbsp;&nbsp; 8 + 3 = 11 &nbsp;&nbsp;|&nbsp;&nbsp; 6 + 5 = 11<br>
                11 = 6 + 5 &nbsp;&nbsp;|&nbsp;&nbsp; 11 = 2 + 9 &nbsp;&nbsp;|&nbsp;&nbsp; 7 + 4 = 11 &nbsp;&nbsp;|&nbsp;&nbsp; 9 + 2 = 11<br>
                11 = 5 + 5 + 1 &nbsp;|&nbsp; 11 = 1 + 10 &nbsp;|&nbsp; 2 + 9 = 11 &nbsp;|&nbsp; 5 + 6 = 11
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_methode_boscher, "← Revenir à la Méthode Boscher")

    def creer_page_boscher_fr(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#0284C7; color:#fff; font-size:14pt; font-weight:bold; padding:6px 16px; border-radius:12px;">Méthode Boscher</span></p>
            <p style="font-size:11pt; color:#64748B; font-weight:bold; margin:4px 0;">eu. vr. un. ou. pr. oi. br. on. dr. an. on.</p>
            <p style="font-size:19pt; font-weight:900; color:#D90429; margin:6px 0;">sous la grêle.</p>
            <p style="font-size:26pt; font-weight:900; color:#E11D48; margin:4px 0;">fr. &nbsp; tr. &nbsp; cr. &nbsp; gr.</p>
            
            <div style="background:#FFFFFF; border:3px solid #80DEEA; border-radius:14px; padding:12px; font-size:13pt; font-weight:bold; color:#0F172A; line-height:2.2;">
                <span style="color:#C026D3; font-size:15pt;">croi. tre. grin. frè. tran. gré. crin.</span><br><br>
                la grê le. un a bri. du cha grin. un li tre. un fri pon.<br>
                vi tre. sou fre. é cri tu re. cru che. gran di. dé grin go lé.<br>
                tran che. fri tu re. gri ve. fre lon. croû ton. su cre. croî tre.<br>
                la fou dre gron de. mon frè re é cri ra à no tre tan te.<br>
                je bro de seu le u ne cra va te. ou vre la fe nê tre.<br>
                vo tre ca ma ra de a sa li la gra vu re de son li vre.
            </div>

            <p style="font-size:14pt; font-weight:bold; color:#991B1B; margin-top:12px;">✍️ Écriture courante (cursive) :</p>
            <div style="background:#FEF2F2; border:2px dashed #DC2626; border-radius:12px; padding:12px; font-size:12pt; font-style:italic; font-weight:bold; color:#991B1B; line-height:2.1; text-align:left;">
                la friture. du pétrole. un croûton. de la grêle.<br>
                votre jeune frère a du chagrin. la cravate brune.<br>
                la montre de votre neveu a un joli cadran.
            </div>

            <p style="font-size:14pt; font-weight:bold; color:#D97706; margin-top:12px;">🍓 Objets & Calculs :</p>
            <div style="background:#FFFBEB; border:2px dashed #D97706; border-radius:12px; padding:10px; font-size:11pt; font-weight:bold; color:#B45309; line-height:2;">
                ✦ une cravate &nbsp;|&nbsp; ✦ une grive &nbsp;|&nbsp; ✦ un frelon &nbsp;|&nbsp; ✦ une montre &nbsp;|&nbsp; ✦ framboises<br>
                <b>11 - 1 = 10</b><br>
                11 - 2 = 9 &nbsp;&nbsp;|&nbsp;&nbsp; 11 - 7 = 4 &nbsp;&nbsp;|&nbsp;&nbsp; 11 - 4 = 7 &nbsp;&nbsp;|&nbsp;&nbsp; 5 + 5 = 10<br>
                11 - 5 = 6 &nbsp;&nbsp;|&nbsp;&nbsp; 11 - 6 = 5 &nbsp;&nbsp;|&nbsp;&nbsp; 11 - 6 = 5 &nbsp;&nbsp;|&nbsp;&nbsp; 11 - 7 = 4<br>
                11 - 3 = 8 &nbsp;&nbsp;|&nbsp;&nbsp; 11 - 8 = 3 &nbsp;&nbsp;|&nbsp;&nbsp; 11 - 8 = 3 &nbsp;&nbsp;|&nbsp;&nbsp; 7 + 4 = 11<br>
                11 - 6 = 5 &nbsp;&nbsp;|&nbsp;&nbsp; 11 - 4 = 7 &nbsp;&nbsp;|&nbsp;&nbsp; 11 - 5 = 6 &nbsp;&nbsp;|&nbsp;&nbsp; 9 + 2 = 11<br>
                11 - 8 = 3 &nbsp;&nbsp;|&nbsp;&nbsp; 11 - 9 = 2 &nbsp;&nbsp;|&nbsp;&nbsp; 11 - 9 = 2 &nbsp;&nbsp;|&nbsp;&nbsp; 11 - 5 = 6
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_methode_boscher, "← Revenir à la Méthode Boscher")

    def creer_page_boscher_bl(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#0284C7; color:#fff; font-size:14pt; font-weight:bold; padding:6px 16px; border-radius:12px;">Méthode Boscher</span></p>
            <p style="font-size:11pt; color:#64748B; font-weight:bold; margin:4px 0;">in. eu. an. tr. gr. in. oi. dr. pr. on. ou. br.</p>
            <p style="font-size:19pt; font-weight:900; color:#D90429; margin:6px 0;">andré joue de la flûte.</p>
            <p style="font-size:26pt; font-weight:900; color:#E11D48; margin:4px 0;">bl. &nbsp; pl. &nbsp; fl.</p>
            
            <div style="background:#FFFFFF; border:3px solid #80DEEA; border-radius:14px; padding:12px; font-size:13pt; font-weight:bold; color:#0F172A; line-height:2.2;">
                <span style="color:#C026D3; font-size:15pt;">pla. blé. fleu. bli. plan. flo. plu. flé.</span><br><br>
                plan che. meu ble. éta bli. ta ble. flû te. plu me.<br>
                trè fle. fla con. pla ta ne. o bli gai toi re. blon de. flé tri.<br>
                un fleu ve. u ne fa ble. je pleu re. je plan te un pin.<br>
                le feu ron fle. du sa ble fin. la plan te fleu ri ra.<br>
                la meu niè re mou dra le blé. de la dou blu re blan che.<br>
                flo ra a trou vé son pro blè me seu le. bra vo flo ra.
            </div>

            <p style="font-size:14pt; font-weight:bold; color:#065F46; margin-top:12px;">✍️ Écriture courante (cursive) :</p>
            <div style="background:#ECFDF5; border:2px dashed #059669; border-radius:12px; padding:12px; font-size:12pt; font-style:italic; font-weight:bold; color:#065F46; line-height:2.1; text-align:left;">
                le flacon. la planche. du plâtre. je plante un pin.<br>
                flora a du ruban bleu. de la doublure neuve.<br>
                andré a semé du trèfle. planté un platane.
            </div>

            <p style="font-size:14pt; font-weight:bold; color:#2563EB; margin-top:12px;">🎶 Objets & Calculs :</p>
            <div style="background:#EFF6FF; border:2px dashed #2563EB; border-radius:12px; padding:10px; font-size:11pt; font-weight:bold; color:#1E40AF; line-height:2;">
                ✦ une flûte &nbsp;|&nbsp; ✦ un flacon &nbsp;|&nbsp; ✦ platane &nbsp;|&nbsp; ✦ trèfle<br>
                12 = 6 + 6 &nbsp;&nbsp;|&nbsp;&nbsp; 12 = 5 + 7 &nbsp;&nbsp;|&nbsp;&nbsp; 8 + 4 = 12 &nbsp;&nbsp;|&nbsp;&nbsp; 9 + 3 = 12<br>
                12 = 10 + 2 &nbsp;&nbsp;|&nbsp;&nbsp; 12 = 4 + 8 &nbsp;&nbsp;|&nbsp;&nbsp; 5 + 7 = 12 &nbsp;&nbsp;|&nbsp;&nbsp; 4 + 8 = 12<br>
                12 = 9 + 3 &nbsp;&nbsp;|&nbsp;&nbsp; 12 = 3 + 9 &nbsp;&nbsp;|&nbsp;&nbsp; 6 + 6 = 12 &nbsp;&nbsp;|&nbsp;&nbsp; 10 + 2 = 12<br>
                12 = 8 + 4 &nbsp;&nbsp;|&nbsp;&nbsp; 12 = 10 + 2 &nbsp;|&nbsp; 3 + 9 = 12 &nbsp;&nbsp;|&nbsp;&nbsp; 6 + 6 = 12<br>
                12 = 7 + 5 &nbsp;&nbsp;|&nbsp;&nbsp; 12 = 2 + 10 &nbsp;|&nbsp; 7 + 5 = 12 &nbsp;&nbsp;|&nbsp;&nbsp; 5 + 7 = 12<br>
                <b>6 fois 2 = 12 &nbsp;|&nbsp; 2 fois 6 = 12 &nbsp;|&nbsp; 3 fois 4 = 12</b>
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_methode_boscher, "← Revenir à la Méthode Boscher")

    def creer_page_boscher_cl(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#0284C7; color:#fff; font-size:14pt; font-weight:bold; padding:6px 16px; border-radius:12px;">Méthode Boscher</span></p>
            <p style="font-size:11pt; color:#64748B; font-weight:bold; margin:4px 0;">fr. un. tr. pl. on. an. bl. oi. eu. fr. ou. in.</p>
            <p style="font-size:19pt; font-weight:900; color:#D90429; margin:6px 0;">la demeure de mon oncle.</p>
            <p style="font-size:26pt; font-weight:900; color:#E11D48; margin:4px 0;">cl. &nbsp; gl.</p>
            
            <div style="background:#FFFFFF; border:3px solid #80DEEA; border-radius:14px; padding:12px; font-size:13pt; font-weight:bold; color:#0F172A; line-height:2.2;">
                <span style="color:#C026D3; font-size:15pt;">glan. clé. glou. clo. gloi. cla. cloi.</span><br><br>
                clô tu re. é glan ti ne. bou cle. on gle. ré cla mé.<br>
                gloi re. glo be. clé ma ti te. trin gle. cla po té. clo re.<br>
                un clou. l'é pin gle. le glou ton. la clo che. je gla ne.<br>
                le glou glou du fla con. mon on cle a un é ta bli.<br>
                la voi le du na vi re se gon fle. la fou dre é cla te.<br>
                la clé ma ti te cou vre la clô tu re du jar din.
            </div>

            <p style="font-size:14pt; font-weight:bold; color:#581C87; margin-top:12px;">✍️ Écriture courante (cursive) :</p>
            <div style="background:#FAF5FF; border:2px dashed #9333EA; border-radius:12px; padding:12px; font-size:12pt; font-style:italic; font-weight:bold; color:#581C87; line-height:2.1; text-align:left;">
                un clou. une glande. la cloche. une épingle.<br>
                votre frère réclame à boire. coupe ton ongle.<br>
                léon a retrouvé la clé de l'étable de son oncle.
            </div>

            <p style="font-size:14pt; font-weight:bold; color:#B45309; margin-top:12px;">🔔 Objets & Calculs :</p>
            <div style="background:#FFFBEB; border:2px dashed #D97706; border-radius:12px; padding:10px; font-size:11pt; font-weight:bold; color:#B45309; line-height:2;">
                ✦ clôture &nbsp;|&nbsp; ✦ cloche &nbsp;|&nbsp; ✦ glands &nbsp;|&nbsp; ✦ clématite &nbsp;|&nbsp; ✦ églantines<br>
                12 - 6 = 6 &nbsp;&nbsp;|&nbsp;&nbsp; 12 - 10 = 2 &nbsp;|&nbsp; 12 - 4 = 8 &nbsp;&nbsp;|&nbsp;&nbsp; 8 + 4 = 12<br>
                12 - 9 = 3 &nbsp;&nbsp;|&nbsp;&nbsp; 12 - 5 = 7 &nbsp;&nbsp;|&nbsp; 12 - 7 = 5 &nbsp;&nbsp;|&nbsp;&nbsp; 12 - 2 = 10<br>
                12 - 8 = 4 &nbsp;&nbsp;|&nbsp;&nbsp; 12 - 3 = 9 &nbsp;&nbsp;|&nbsp; 12 - 9 = 3 &nbsp;&nbsp;|&nbsp;&nbsp; 12 - 6 = 6<br>
                12 - 4 = 8 &nbsp;&nbsp;|&nbsp;&nbsp; 12 - 2 = 10 &nbsp;|&nbsp; 12 - 6 = 6 &nbsp;&nbsp;|&nbsp;&nbsp; 9 + 3 = 12<br>
                12 - 7 = 5 &nbsp;&nbsp;|&nbsp;&nbsp; 12 - 1 = 11 &nbsp;|&nbsp; 12 - 3 = 9 &nbsp;&nbsp;|&nbsp;&nbsp; 7 + 5 = 12
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_methode_boscher, "← Revenir à la Méthode Boscher")

    def creer_page_boscher_ar(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#0284C7; color:#fff; font-size:14pt; font-weight:bold; padding:6px 16px; border-radius:12px;">Méthode Boscher</span></p>
            <p style="font-size:11pt; color:#64748B; font-weight:bold; margin:4px 0;">oi. fl. an. vr. pl. in. cr. el. eu. bl. on. dr.</p>
            <p style="font-size:19pt; font-weight:900; color:#D90429; margin:6px 0;">le fleuve déborde.</p>
            <p style="font-size:26pt; font-weight:900; color:#E11D48; margin:4px 0;">ar. &nbsp; or. &nbsp; ir. &nbsp; ur.</p>
            
            <div style="background:#FFFFFF; border:3px solid #80DEEA; border-radius:14px; padding:12px; font-size:13pt; font-weight:bold; color:#0F172A; line-height:2.2;">
                <span style="color:#C026D3; font-size:15pt;">char. cor. gar. por. sur. bor. vrir.</span><br><br>
                jar din. ar bre. por te. bor du re. cor ne. ou vrir. sor tir.<br>
                mar ché. mar mi te. sar di ne. char don. é cor ché. bar bu.<br>
                la cor de. du char bon. u ne ar moi re. dor mir. mor dre.<br>
                mar ti ne re gar de sur la por te. mé dor te mor dra.<br>
                le fleu ve a dé bor dé sur le jar din plan té.<br>
                por te la mou tar de, le su cre, la crè me sur la ta ble.
            </div>

            <p style="font-size:14pt; font-weight:bold; color:#0F172A; margin-top:12px;">✍️ Écriture courante (cursive) :</p>
            <div style="background:#F8FAFC; border:2px dashed #64748B; border-radius:12px; padding:12px; font-size:12pt; font-style:italic; font-weight:bold; color:#1E293B; line-height:2.1; text-align:left;">
                une virgule. un torchon. du marbre. le marché.<br>
                émile a bu du vin pur. aline partira jeudi.<br>
                ton oncle va venir, va ouvrir la porte du jardin.
            </div>

            <p style="font-size:14pt; font-weight:bold; color:#16A34A; margin-top:12px;">🌳 Objets & Calculs :</p>
            <div style="background:#F0FDF4; border:2px dashed #16A34A; border-radius:12px; padding:10px; font-size:11pt; font-weight:bold; color:#15803D; line-height:2;">
                ✦ un arbre &nbsp;|&nbsp; ✦ cornes &nbsp;|&nbsp; ✦ une tortue &nbsp;|&nbsp; ✦ sardines &nbsp;|&nbsp; ✦ chardons<br>
                13 = 10 + 3 &nbsp;&nbsp;|&nbsp;&nbsp; 13 = 6 + 6 + 1 &nbsp;|&nbsp; 5 + 8 = 13 &nbsp;&nbsp;|&nbsp;&nbsp; 2 + 9 = 11<br>
                13 = 9 + 4 &nbsp;&nbsp;|&nbsp;&nbsp; 13 = 5 + 8 &nbsp;&nbsp;&nbsp;&nbsp;|&nbsp; 9 + 4 = 13 &nbsp;&nbsp;|&nbsp;&nbsp; 10 + 3 = 13<br>
                13 = 8 + 5 &nbsp;&nbsp;|&nbsp;&nbsp; 13 = 3 + 10 &nbsp;&nbsp;&nbsp;|&nbsp; 7 + 6 = 13 &nbsp;&nbsp;|&nbsp;&nbsp; 8 + 4 = 12<br>
                13 = 7 + 6 &nbsp;&nbsp;|&nbsp;&nbsp; 13 = 6 + 7 &nbsp;&nbsp;&nbsp;&nbsp;|&nbsp; 6 + 7 = 13 &nbsp;&nbsp;|&nbsp;&nbsp; 4 + 9 = 13<br>
                13 = 11 + 2 &nbsp;|&nbsp;&nbsp; 13 = 4 + 9 &nbsp;&nbsp;&nbsp;&nbsp;|&nbsp; 3 + 10 = 13 &nbsp;|&nbsp;&nbsp; 5 + 7 = 12
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_methode_boscher, "← Revenir à la Méthode Boscher")

    def creer_page_boscher_al(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#0284C7; color:#fff; font-size:14pt; font-weight:bold; padding:6px 16px; border-radius:12px;">Méthode Boscher</span></p>
            <p style="font-size:11pt; color:#64748B; font-weight:bold; margin:4px 0;">vr. ir. in. cl. or. an. gr. un. ur. bl. ar. eu.</p>
            <p style="font-size:19pt; font-weight:900; color:#D90429; margin:6px 0;">le maréchal ferre le cheval.</p>
            <p style="font-size:26pt; font-weight:900; color:#E11D48; margin:4px 0;">al. &nbsp; il. &nbsp; ol. &nbsp; ul.</p>
            
            <div style="background:#FFFFFF; border:3px solid #80DEEA; border-radius:14px; padding:12px; font-size:13pt; font-weight:bold; color:#0F172A; line-height:2.2;">
                <span style="color:#C026D3; font-size:15pt;">bal. col. fil. bol. mal. vol. nul. val.</span><br><br>
                a ni mal. bo cal. cal cul. a vril. ré col te. cou til.<br>
                car na val. ca nal. in sul te. bru tal. ma ti nal. un bal.<br>
                un vol can. un gril. u ne cul bu te. un bol. je val se.<br>
                jean bri de son che val. mon lo cal se ra a gré a ble.<br>
                clo til de boi ra un bol de crè me. j'a chè ve mon cal cul.<br>
                le ma ré chal cou pe la cor ne du che val.
            </div>

            <p style="font-size:14pt; font-weight:bold; color:#0369A1; margin-top:12px;">✍️ Écriture courante (cursive) :</p>
            <div style="background:#F0F9FF; border:2px dashed #0284C7; border-radius:12px; padding:12px; font-size:12pt; font-style:italic; font-weight:bold; color:#075985; line-height:2.1; text-align:left;">
                un maréchal. du tumulte. une salle de bal.<br>
                je coupe le crin du cheval. médor va à son chenil.<br>
                la voiture de la bouchère a culbuté à côté du fleuve.
            </div>

            <p style="font-size:14pt; font-weight:bold; color:#D97706; margin-top:12px;">🎈 Objets & Calculs :</p>
            <div style="background:#FFFBEB; border:2px dashed #D97706; border-radius:12px; padding:10px; font-size:11pt; font-weight:bold; color:#B45309; line-height:2;">
                ✦ un bocal &nbsp;|&nbsp; ✦ un bol &nbsp;|&nbsp; ✦ un gril &nbsp;|&nbsp; ✦ des ballons<br>
                13 - 3 = 10 &nbsp;&nbsp;|&nbsp;&nbsp; 13 - 2 = 11 &nbsp;|&nbsp; 13 - 7 = 6 &nbsp;&nbsp;|&nbsp;&nbsp; 13 - 8 = 5<br>
                13 - 1 = 12 &nbsp;&nbsp;|&nbsp;&nbsp; 13 - 5 = 8 &nbsp;&nbsp;|&nbsp; 13 - 5 = 8 &nbsp;&nbsp;|&nbsp;&nbsp; 11 - 4 = 7<br>
                13 - 4 = 9 &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp; 13 - 10 = 3 &nbsp;|&nbsp; 13 - 6 = 7 &nbsp;&nbsp;|&nbsp;&nbsp; 10 - 5 = 5<br>
                13 - 6 = 7 &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp; 13 - 9 = 4 &nbsp;&nbsp;|&nbsp; 13 - 10 = 3 &nbsp;|&nbsp;&nbsp; 12 - 6 = 6<br>
                13 - 8 = 5 &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp; 13 - 7 = 6 &nbsp;&nbsp;|&nbsp; 13 - 4 = 9 &nbsp;&nbsp;|&nbsp;&nbsp; 13 - 5 = 8
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_methode_boscher, "← Revenir à la Méthode Boscher")

    def creer_page_boscher_en(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#0284C7; color:#fff; font-size:15pt; font-weight:bold; padding:6px 16px; border-radius:12px;">Méthode Boscher</span></p>
            <p style="font-size:18pt; font-weight:900; color:#D90429; margin-top:8px;">Le vent souffle.</p>
            <p style="font-size:26pt; font-weight:900; color:#E11D48;">en = en</p>

            <div style="background:#FFFFFF; border:3px solid #80DEEA; border-radius:14px; padding:12px; font-size:14pt; font-weight:bold; color:#0F172A; line-height:2.4;">
                pen . gen . men . chen . ben . ten . ren .<br>
                le ven t . la den te . un ser pen t . la gen tian e .<br>
                une cen taine . un quen ouille . la tor ren te .<br>
                <span style="color:#2563EB;">le ven t souf fle for t sur le gran d sa pin .</span>
            </div>

            <p style="font-size:14pt; font-weight:bold; color:#16A34A; margin-top:14px;">✍️ Écriture et phrase :</p>
            <div style="background:#F0FDF4; border:2px dashed #16A34A; border-radius:12px; padding:10px; font-size:12pt; font-weight:bold; color:#15803D; line-height:2.2;">
                ✦ <i>le vent . une dent . un serpent .</i><br>
                ✦ <i>jules a peur du grand serpent vert .</i>
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_methode_boscher, "← Revenir à la Méthode Boscher")

    # =========================================================================
    # SECTION COURS
    # =========================================================================
    def creer_page_cours(self):
        page = QWidget()
        self.style_fond(page)
        l = QVBoxLayout(page)
        l.setContentsMargins(12, 12, 12, 12)

        cadre = QFrame()
        cadre.setStyleSheet("QFrame { background-color: transparent; border: 3px solid #80DEEA; border-radius: 20px; }")
        cadre_l = QVBoxLayout(cadre)

        self.titre_cours = self.creer_titre("Cours\nChoisissez une leçon")
        cadre_l.addWidget(self.titre_cours, 1)

        self.groupe_cours = QButtonGroup(self)
        self.groupe_cours.setExclusive(True)

        self.boutons_cours = [
            self.creer_bouton_rose_3d("1-Pose et effectue"),
            self.creer_bouton_rose_3d("1-Décompose")
        ]

        for b in self.boutons_cours:
            self.groupe_cours.addButton(b)
            cadre_l.addWidget(b, 2)
            b.clicked.connect(lambda checked=False, btn=b: self.selectionner_cours(btn.text()))

        self.bouton_choose_cours = self.creer_bouton_choose("Choose")
        self.bouton_choose_cours.clicked.connect(self.confirmer_choix_cours)
        cadre_l.addWidget(self.bouton_choose_cours, 1)

        btn_ret = QPushButton("← Revenir au choix")
        btn_ret.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ret.setStyleSheet("QPushButton { background-color: #6C757D; color: white; font-size: 15px; font-weight: bold; border-radius: 12px; padding: 6px; }")
        btn_ret.clicked.connect(self.retour_au_choix)
        cadre_l.addWidget(btn_ret)

        l.addWidget(cadre)
        return page

    def creer_page_cours_pose_effectue(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#4361EE; color:#fff; font-size:14pt; font-weight:bold; padding:6px 16px; border-radius:12px;">📅 Mercredi 07 Octobre 2026</span></p>
            <p style="font-size:16pt; font-weight:800; color:#FF2E93; margin-top:10px;">📖 Arithmétique : 1- Pose et effectue</p>
            
            <table width="100%" border="0" cellspacing="10" cellpadding="8" style="font-family:'Courier New', monospace; font-size:13pt; font-weight:bold;">
                <tr>
                    <td width="33%" align="center" style="background:#FFFFFF; border:2px solid #80DEEA; border-radius:12px;">
                        <span style="color:#0D47A1;">15 + 13 = 28</span><br><br>
                        &nbsp;&nbsp;1 5<br>
                        + 1 3<br>
                        -------<br>
                        &nbsp;&nbsp;2 8
                    </td>
                    <td width="33%" align="center" style="background:#FFFFFF; border:2px solid #80DEEA; border-radius:12px;">
                        <span style="color:#0D47A1;">36 + 32 = 68</span><br><br>
                        &nbsp;&nbsp;3 6<br>
                        + 3 2<br>
                        -------<br>
                        &nbsp;&nbsp;6 8
                    </td>
                    <td width="33%" align="center" style="background:#FFFFFF; border:2px solid #80DEEA; border-radius:12px;">
                        <span style="color:#0D47A1;">40 + 55 = 95</span><br><br>
                        &nbsp;&nbsp;4 0<br>
                        + 5 5<br>
                        -------<br>
                        &nbsp;&nbsp;9 5
                    </td>
                </tr>
            </table>

            <p style="font-size:14pt; font-weight:800; color:#2E7D32; margin-top:15px;">✍️ 3- Écris en lettres :</p>
            <div style="background:#FFFFFF; border:2px dashed #4CAF50; border-radius:12px; padding:10px; font-size:12pt; font-weight:bold; color:#1B5E20; text-align:left; line-height:2;">
                ✦ <b>2</b> = deux &nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;&nbsp; ✦ <b>5</b> = cinq &nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;&nbsp; ✦ <b>10</b> = dix<br>
                ✦ <b>0</b> = zéro &nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;&nbsp; ✦ <b>7</b> = sept
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_cours, "← Revenir aux Cours")

    def creer_page_cours_decompose(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#4361EE; color:#fff; font-size:14pt; font-weight:bold; padding:6px 16px; border-radius:12px;">📅 Mercredi 14 Octobre 2026</span></p>
            <p style="font-size:16pt; font-weight:800; color:#FF2E93; margin-top:10px;">📖 Arithmétique : 1- Décompose & Compose</p>
            
            <p align="left" style="font-size:13pt; font-weight:bold; color:#0D47A1; margin-top:10px;">1) Décompose :</p>
            <div style="background:#FFFFFF; border:2px solid #80DEEA; border-radius:12px; padding:12px; font-size:12pt; font-weight:bold; color:#333333; text-align:left; line-height:2.2;">
                ✦ 24 = <b style="color:#D81B60;">2 d 4 u</b><br>
                ✦ 15 = <b style="color:#D81B60;">1 d 5 u</b><br>
                ✦ 3 &nbsp;= <b style="color:#D81B60;">3 u</b><br>
                ✦ 56 = <b style="color:#D81B60;">5 d 6 u</b><br>
                ✦ 78 = <b style="color:#D81B60;">7 d 8 u</b><br>
                ✦ 49 = <b style="color:#D81B60;">4 d 9 u</b>
            </div>

            <table width="100%" border="0" cellspacing="10" cellpadding="8" style="font-family:'Courier New', monospace; font-size:13pt; font-weight:bold; margin-top:8px;">
                <tr>
                    <td width="33%" align="center" style="background:#F0F4FF; border:2px solid #80DEEA; border-radius:12px;">
                        <span style="color:#C2185B;">46 + 36 = 82</span><br><br>
                        &nbsp;&nbsp;4 6<br>
                        + 3 6<br>
                        -------<br>
                        &nbsp;&nbsp;8 2
                    </td>
                    <td width="33%" align="center" style="background:#F0F4FF; border:2px solid #80DEEA; border-radius:12px;">
                        <span style="color:#C2185B;">17 + 4 = 21</span><br><br>
                        &nbsp;&nbsp;1 7<br>
                        + &nbsp;&nbsp;4<br>
                        -------<br>
                        &nbsp;&nbsp;2 1
                    </td>
                    <td width="33%" align="center" style="background:#F0F4FF; border:2px solid #80DEEA; border-radius:12px;">
                        <span style="color:#C2185B;">22 + 19 = 41</span><br><br>
                        &nbsp;&nbsp;2 2<br>
                        + 1 9<br>
                        -------<br>
                        &nbsp;&nbsp;4 1
                    </td>
                </tr>
            </table>

            <p align="left" style="font-size:13pt; font-weight:bold; color:#1B5E20; margin-top:14px;">2) Compose :</p>
            <div style="background:#E8F5E9; border:2px dashed #4CAF50; border-radius:12px; padding:12px; font-size:12pt; font-weight:bold; color:#1B5E20; text-align:left; line-height:2.2;">
                ✦ 3 d 5 u = <b style="color:#0D47A1;">35</b><br>
                ✦ 5 u &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;= <b style="color:#0D47A1;">5</b><br>
                ✦ 2 d 8 u = <b style="color:#0D47A1;">28</b><br>
                ✦ 9 u &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;= <b style="color:#0D47A1;">9</b><br>
                ✦ 7 d 2 u = <b style="color:#0D47A1;">72</b>
            </div>

            <p align="left" style="font-size:12pt; font-weight:bold; color:#E65100; margin-top:14px;">✍️ Écriture :</p>
            <div style="background:#FFF9C4; border-radius:12px; padding:10px; font-size:12pt; font-style:italic; color:#4E342E; text-align:left; line-height:2;">
                • Maman va au marché.<br>
                • Marius plante une fleur.
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_cours, "← Revenir aux Cours")

    # =========================================================================
    # MENUS FRANÇAIS (LEÇONS & EXERCICES)
    # =========================================================================
    def creer_page_fr_lecons(self):
        page = QWidget()
        self.style_fond(page)
        l = QVBoxLayout(page)
        l.setContentsMargins(12, 12, 12, 12)

        cadre = QFrame()
        cadre.setStyleSheet("QFrame { background-color: transparent; border: 3px solid #80DEEA; border-radius: 20px; }")
        cadre_l = QVBoxLayout(cadre)

        self.titre_fr_lecons = self.creer_titre("Français — Leçons\nChoisissez une matière")
        cadre_l.addWidget(self.titre_fr_lecons, 1)

        self.groupe_fr_lecons = QButtonGroup(self)
        self.groupe_fr_lecons.setExclusive(True)

        self.boutons_fr_lecons = [
            self.creer_bouton_rose_3d("Orthographe"),
            self.creer_bouton_rose_3d("Conjugaison"),
            self.creer_bouton_rose_3d("Grammaire"),
            self.creer_bouton_rose_3d("Vocabulaire")
        ]

        for b in self.boutons_fr_lecons:
            self.groupe_fr_lecons.addButton(b)
            cadre_l.addWidget(b, 2)
            b.clicked.connect(lambda checked=False, btn=b: self.selectionner_lecon_fr(btn.text()))

        self.bouton_choose_fr_lec = self.creer_bouton_choose("Choose")
        self.bouton_choose_fr_lec.clicked.connect(self.confirmer_lecon_fr)
        cadre_l.addWidget(self.bouton_choose_fr_lec, 1)

        btn_ret = QPushButton("← Revenir")
        btn_ret.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ret.setStyleSheet("QPushButton { background-color: #6C757D; color: white; font-size: 15px; font-weight: bold; border-radius: 12px; padding: 6px; }")
        btn_ret.clicked.connect(self.retour_a_programme)
        cadre_l.addWidget(btn_ret)

        l.addWidget(cadre)
        return page

    def creer_page_fr_exercices(self):
        page = QWidget()
        self.style_fond(page)
        l = QVBoxLayout(page)
        l.setContentsMargins(12, 12, 12, 12)

        cadre = QFrame()
        cadre.setStyleSheet("QFrame { background-color: transparent; border: 3px solid #80DEEA; border-radius: 20px; }")
        cadre_l = QVBoxLayout(cadre)

        self.titre_fr_exercices = self.creer_titre("Français — Exercices\nChoisissez une option")
        cadre_l.addWidget(self.titre_fr_exercices, 1)

        self.groupe_fr_ex = QButtonGroup(self)
        self.groupe_fr_ex.setExclusive(True)

        self.boutons_fr_exercices = [
            self.creer_bouton_rose_3d("Orthographe"),
            self.creer_bouton_rose_3d("Conjugaison"),
            self.creer_bouton_rose_3d("Grammaire"),
            self.creer_bouton_rose_3d("Dictée préparée")
        ]

        for b in self.boutons_fr_exercices:
            self.groupe_fr_ex.addButton(b)
            cadre_l.addWidget(b, 2)
            b.clicked.connect(lambda checked=False, btn=b: self.selectionner_exercice_fr(btn.text()))

        self.bouton_choose_fr_ex = self.creer_bouton_choose("Choose")
        self.bouton_choose_fr_ex.clicked.connect(self.confirmer_exercice_fr)
        cadre_l.addWidget(self.bouton_choose_fr_ex, 1)

        btn_ret = QPushButton("← Revenir")
        btn_ret.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ret.setStyleSheet("QPushButton { background-color: #6C757D; color: white; font-size: 15px; font-weight: bold; border-radius: 12px; padding: 6px; }")
        btn_ret.clicked.connect(self.retour_a_programme)
        cadre_l.addWidget(btn_ret)

        l.addWidget(cadre)
        return page

    # =========================================================================
    # SOUS-MENUS DES LEÇONS DE FRANÇAIS
    # =========================================================================
    def creer_page_lecons_orthographe(self):
        page = QWidget()
        self.style_fond(page)
        l = QVBoxLayout(page)
        l.setContentsMargins(12, 12, 12, 12)

        cadre = QFrame()
        cadre.setStyleSheet("QFrame { background-color: transparent; border: 3px solid #80DEEA; border-radius: 20px; }")
        cadre_l = QVBoxLayout(cadre)

        self.titre_lecons_ortho = self.creer_titre("Leçons d'Orthographe\nChoisissez une leçon")
        cadre_l.addWidget(self.titre_lecons_ortho, 1)

        self.groupe_lecons_ortho = QButtonGroup(self)
        self.groupe_lecons_ortho.setExclusive(True)

        self.boutons_lecons_ortho = [
            self.creer_bouton_rose_3d('Le son "i".'),
            self.creer_bouton_rose_3d('Le son "e".'),
            self.creer_bouton_rose_3d("Le son ar")
        ]

        for b in self.boutons_lecons_ortho:
            self.groupe_lecons_ortho.addButton(b)
            cadre_l.addWidget(b, 2)
            b.clicked.connect(lambda checked=False, btn=b: self.selectionner_option_lecon_ortho(btn.text()))

        self.bouton_choose_lec_ortho = self.creer_bouton_choose("Choose")
        self.bouton_choose_lec_ortho.clicked.connect(self.confirmer_choix_lecon_ortho)
        cadre_l.addWidget(self.bouton_choose_lec_ortho, 1)

        btn_ret = QPushButton("← Revenir aux leçons de Français")
        btn_ret.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ret.setStyleSheet("QPushButton { background-color: #6C757D; color: white; font-size: 15px; font-weight: bold; border-radius: 12px; padding: 6px; }")
        btn_ret.clicked.connect(self.retour_a_fr_lecons)
        cadre_l.addWidget(btn_ret)

        l.addWidget(cadre)
        return page

    def creer_page_lecons_conjugaison(self):
        page = QWidget()
        self.style_fond(page)
        l = QVBoxLayout(page)
        l.setContentsMargins(12, 12, 12, 12)

        cadre = QFrame()
        cadre.setStyleSheet("QFrame { background-color: transparent; border: 3px solid #80DEEA; border-radius: 20px; }")
        cadre_l = QVBoxLayout(cadre)

        self.titre_lecons_conj = self.creer_titre("Leçons de Conjugaison\nChoisissez une leçon")
        cadre_l.addWidget(self.titre_lecons_conj, 1)

        self.groupe_lecons_conj = QButtonGroup(self)
        self.groupe_lecons_conj.setExclusive(True)

        self.boutons_lecons_conj = [
            self.creer_bouton_rose_3d("Les pronoms personnels sujets au singuliers"),
            self.creer_bouton_rose_3d("Les PPS aux pluriels")
        ]

        for b in self.boutons_lecons_conj:
            self.groupe_lecons_conj.addButton(b)
            cadre_l.addWidget(b, 2)
            b.clicked.connect(lambda checked=False, btn=b: self.selectionner_option_lecon_conj(btn.text()))

        self.bouton_choose_lec_conj = self.creer_bouton_choose("Choose")
        self.bouton_choose_lec_conj.clicked.connect(self.confirmer_choix_lecon_conj)
        cadre_l.addWidget(self.bouton_choose_lec_conj, 1)

        btn_ret = QPushButton("← Revenir aux leçons de Français")
        btn_ret.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ret.setStyleSheet("QPushButton { background-color: #6C757D; color: white; font-size: 15px; font-weight: bold; border-radius: 12px; padding: 6px; }")
        btn_ret.clicked.connect(self.retour_a_fr_lecons)
        cadre_l.addWidget(btn_ret)

        l.addWidget(cadre)
        return page

    def creer_page_lecons_grammaire(self):
        page = QWidget()
        self.style_fond(page)
        l = QVBoxLayout(page)
        l.setContentsMargins(12, 12, 12, 12)

        cadre = QFrame()
        cadre.setStyleSheet("QFrame { background-color: transparent; border: 3px solid #80DEEA; border-radius: 20px; }")
        cadre_l = QVBoxLayout(cadre)

        self.titre_lecons_gramm = self.creer_titre("Leçons de Grammaire\nChoisissez une leçon")
        cadre_l.addWidget(self.titre_lecons_gramm, 1)

        self.groupe_lecons_gramm = QButtonGroup(self)
        self.groupe_lecons_gramm.setExclusive(True)

        self.boutons_lecons_gramm = [
            self.creer_bouton_rose_3d("Les 26 lettres de l'alphabet francais"),
            self.creer_bouton_rose_3d("Les syllabes"),
            self.creer_bouton_rose_3d("les noms")
        ]

        for b in self.boutons_lecons_gramm:
            self.groupe_lecons_gramm.addButton(b)
            cadre_l.addWidget(b, 2)
            b.clicked.connect(lambda checked=False, btn=b: self.selectionner_option_lecon_gramm(btn.text()))

        self.bouton_choose_lec_gramm = self.creer_bouton_choose("Choose")
        self.bouton_choose_lec_gramm.clicked.connect(self.confirmer_choix_lecon_gramm)
        cadre_l.addWidget(self.bouton_choose_lec_gramm, 1)

        btn_ret = QPushButton("← Revenir aux leçons de Français")
        btn_ret.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ret.setStyleSheet("QPushButton { background-color: #6C757D; color: white; font-size: 15px; font-weight: bold; border-radius: 12px; padding: 6px; }")
        btn_ret.clicked.connect(self.retour_a_fr_lecons)
        cadre_l.addWidget(btn_ret)

        l.addWidget(cadre)
        return page

    def creer_page_lecons_vocabulaire(self):
        page = QWidget()
        self.style_fond(page)
        l = QVBoxLayout(page)
        l.setContentsMargins(12, 12, 12, 12)

        cadre = QFrame()
        cadre.setStyleSheet("QFrame { background-color: transparent; border: 3px solid #80DEEA; border-radius: 20px; }")
        cadre_l = QVBoxLayout(cadre)

        self.titre_lecons_vocab = self.creer_titre("Leçons de Vocabulaire\nChoisissez une leçon")
        cadre_l.addWidget(self.titre_lecons_vocab, 1)

        self.groupe_lecons_vocab = QButtonGroup(self)
        self.groupe_lecons_vocab.setExclusive(True)

        self.boutons_lecons_vocab = [
            self.creer_bouton_rose_3d("La propreté du corps"),
            self.creer_bouton_rose_3d("La propreté de l'environnement"),
            self.creer_bouton_rose_3d("L'école")
        ]

        for b in self.boutons_lecons_vocab:
            self.groupe_lecons_vocab.addButton(b)
            cadre_l.addWidget(b, 2)
            b.clicked.connect(lambda checked=False, btn=b: self.selectionner_option_lecon_vocab(btn.text()))

        self.bouton_choose_lec_vocab = self.creer_bouton_choose("Choose")
        self.bouton_choose_lec_vocab.clicked.connect(self.confirmer_choix_lecon_vocab)
        cadre_l.addWidget(self.bouton_choose_lec_vocab, 1)

        btn_ret = QPushButton("← Revenir aux leçons de Français")
        btn_ret.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ret.setStyleSheet("QPushButton { background-color: #6C757D; color: white; font-size: 15px; font-weight: bold; border-radius: 12px; padding: 6px; }")
        btn_ret.clicked.connect(self.retour_a_fr_lecons)
        cadre_l.addWidget(btn_ret)

        l.addWidget(cadre)
        return page

    # =========================================================================
    # PAGES DE LEÇONS FRANÇAIS
    # =========================================================================
    def creer_page_lecon_ortho_son_i(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#4361EE; color:#fff; font-size:14pt; font-weight:bold; padding:6px 16px; border-radius:12px;">📅 Jeudi 17 Septembre 2026</span></p>
            <p style="font-size:16pt; font-weight:800; color:#FF2E93; margin-top:10px;">📖 Orthographe : Le son « i »</p>
            <div style="background:#ffffff; border:3px solid #80DEEA; border-radius:14px; padding:14px; text-align:left; font-size:12pt; line-height:2.2;">
                ✦ <b>i :</b> une amie &nbsp;—&nbsp; une épicerie &nbsp;—&nbsp; la pluie &nbsp;—&nbsp; la chemise<br>
                ✦ <b>y :</b> <b style="color:#0D47A1;">Lyon</b> &nbsp;—&nbsp; le <b style="color:#0D47A1;">paddy</b> &nbsp;—&nbsp; la <b style="color:#0D47A1;">pyramide</b> &nbsp;—&nbsp; le <b style="color:#0D47A1;">pyjama</b><br>
                ✦ <b>it :</b> le <b style="color:#D81B60;">lit</b> &nbsp;—&nbsp; un hab<b style="color:#D81B60;">it</b> &nbsp;—&nbsp; la nu<b style="color:#D81B60;">it</b> &nbsp;—&nbsp; le fru<b style="color:#D81B60;">it</b><br>
                ✦ <b>ie :</b> la v<b style="color:#1B5E20;">ie</b> &nbsp;—&nbsp; Mar<b style="color:#1B5E20;">ie</b> &nbsp;—&nbsp; le paraplu<b style="color:#1B5E20;">ie</b><br>
                ✦ <b>î :</b> une <b style="color:#E65100;">île</b> &nbsp;—&nbsp; une ab<b style="color:#E65100;">î</b>me<br>
                ✦ <b>is :</b> la sour<b style="color:#6A1B9A;">is</b> &nbsp;—&nbsp; Par<b style="color:#6A1B9A;">is</b> &nbsp;—&nbsp; un tap<b style="color:#6A1B9A;">is</b><br>
                ✦ <b>id :</b> le n<b style="color:#00838F;">id</b> &nbsp;&nbsp;|&nbsp;&nbsp; ✦ <b>iz :</b> le r<b style="color:#00838F;">iz</b><br>
                ✦ <b>h (muet) :</b> un <b style="color:#C2185B;">hibou</b> &nbsp;—&nbsp; l'<b style="color:#C2185B;">hirondelle</b>
            </div>
            <div style="background:#E1F5FE; border-radius:12px; padding:10px; margin-top:12px; font-size:11pt; color:#0D47A1; font-weight:bold; text-align:left;">
                💡 <b>Règle :</b> Le son « i » peut s'écrire simplement <i>i</i> ou <i>y</i>, mais aussi avec des lettres muettes finales comme <i>it, is, id, iz, ie</i> !
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_lecons_ortho, "← Revenir aux Leçons d'Orthographe")

    def creer_page_lecon_ortho_son_e(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#4361EE; color:#fff; font-size:14pt; font-weight:bold; padding:6px 16px; border-radius:12px;">📅 Lundi 12 Octobre 2026</span></p>
            <p style="font-size:16pt; font-weight:800; color:#FF2E93; margin-top:10px;">📖 Orthographe : Le son « e »</p>
            <div style="background:#ffffff; border:3px solid #80DEEA; border-radius:14px; padding:14px; text-align:left; font-size:12pt; line-height:2.2;">
                ✦ <b>e :</b> l<b style="color:#0D47A1;">e</b> m<b style="color:#0D47A1;">e</b>nu &nbsp;—&nbsp; la capitain<b style="color:#0D47A1;">e</b> &nbsp;—&nbsp; p<b style="color:#0D47A1;">e</b>tit<b style="color:#0D47A1;">e</b> prom<b style="color:#0D47A1;">e</b>nad<b style="color:#0D47A1;">e</b><br>
                ✦ <b>eu :</b> le j<b style="color:#D81B60;">eu</b> &nbsp;—&nbsp; nev<b style="color:#D81B60;">eu</b> &nbsp;—&nbsp; av<b style="color:#D81B60;">eu</b>gle &nbsp;—&nbsp; fl<b style="color:#D81B60;">eu</b>ve &nbsp;—&nbsp; je pl<b style="color:#D81B60;">eu</b>re<br>
                ✦ <b>oeu :</b> un <b style="color:#1B5E20;">oeu</b>f &nbsp;—&nbsp; un b<b style="color:#1B5E20;">oeu</b>f &nbsp;—&nbsp; le n<b style="color:#1B5E20;">oeu</b>d &nbsp;—&nbsp; une s<b style="color:#1B5E20;">oeu</b>r &nbsp;—&nbsp; un c<b style="color:#1B5E20;">oeu</b>r<br>
                ✦ <b>oei :</b> un <b style="color:#E65100;">oei</b>l
            </div>
            <div style="background:#FFF9C4; border-radius:12px; padding:10px; margin-top:12px; font-size:11pt; color:#E65100; font-weight:bold; text-align:left;">
                🔍 <b>Remarque :</b> Les graphies <i>eu</i> et <i>oeu</i> se prononcent de façon semblable comme dans le jeu, la soeur et le noeud !
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_lecons_ortho, "← Revenir aux Leçons d'Orthographe")

    def creer_page_lecon_ortho_son_ar(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#4361EE; color:#fff; font-size:14pt; font-weight:bold; padding:6px 16px; border-radius:12px;">📅 Mardi 27 Octobre 2026</span></p>
            <p style="font-size:18pt; font-weight:800; color:#FF2E93; margin-top:8px;">📖 Le son « ar »</p>
            
            <div style="background:#ffffff; border:3px solid #80DEEA; border-radius:14px; padding:16px; text-align:left; font-size:13pt; line-height:2.4;">
                ✦ <b style="color:#D90429; font-size:15pt;">ar :</b> &nbsp;&nbsp;la <b style="color:#0D47A1;">carte</b> &nbsp;—&nbsp; un <b style="color:#0D47A1;">armoire</b><br><br>
                ✦ ✦ <b style="color:#16A34A; font-size:15pt;">are :</b> &nbsp;&nbsp;la <b style="color:#047857;">mare</b> &nbsp;—&nbsp; un <b style="color:#047857;">arc</b> &nbsp;—&nbsp; la <b style="color:#047857;">tare</b>.
            </div>

            <div style="background:#F0FDF4; border:2px dashed #16A34A; border-radius:12px; padding:12px; margin-top:14px; font-size:12pt; color:#15803D; font-weight:bold; text-align:left; line-height:2;">
                💡 <b>Mots à retenir :</b><br>
                • <i>la carte</i> &nbsp;|&nbsp; • <i>une armoire</i><br>
                • <i>la mare</i> &nbsp;|&nbsp; • <i>un arc</i> &nbsp;|&nbsp; • <i>la tare</i>
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_lecons_ortho, "← Revenir aux Leçons d'Orthographe")

    def creer_page_lecon_conj_singulier(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#4361EE; color:#fff; font-size:14pt; font-weight:bold; padding:6px 16px; border-radius:12px;">📅 Lundi 21 Septembre 2026</span></p>
            <p style="font-size:15pt; font-weight:800; color:#FF2E93; margin-top:8px;">📖 Les Pronoms Personnels Sujets au Singulier</p>
            <div style="background:#ffffff; border:3px solid #80DEEA; border-radius:14px; padding:14px; text-align:left; font-size:12pt; line-height:2.2;">
                ✦ <b style="color:#0D47A1;">Je</b> dessine une fleur.<br>
                ✦ <b style="color:#0D47A1;">Tu</b> marches doucement.<br>
                <div style="background:#E8F5E9; border-left:4px solid #2E7D32; padding:6px 10px; margin:6px 0; font-size:11pt;">
                    ➔ <b>Je</b> et <b>Tu</b> sont des pronoms personnels sujets toujours employés pour <u>une seule personne</u>.
                </div>
                ✦ Allah est gentil. ➔ <b style="color:#D81B60;">Il</b> est gentil.<br>
                ✦ Le coq chante. ➔ <b style="color:#D81B60;">Il</b> chante.<br>
                ✦ Fatou prend le livre. ➔ <b style="color:#D81B60;">Elle</b> prend le livre.<br>
                <div style="background:#FFF3E0; border-left:4px solid #E65100; padding:6px 10px; margin:6px 0; font-size:11pt;">
                    ➔ On emploie <b>Il</b> ou <b>Elle</b> quand on parle d'une autre personne, d'un animal ou d'une chose.
                </div>
            </div>
            <p align="left" style="font-weight:bold; color:#1B5E20; margin-top:10px;">📋 Tableau récapitulatif :</p>
            <table border="1" cellpadding="6" style="width:100%; border-collapse:collapse; text-align:center; background:#fff; font-size:11pt;">
                <tr style="background:#B3E5FC; font-weight:bold; color:#0D47A1;"><td>Pronom</td><td>Personne</td></tr>
                <tr><td><b>Je</b></td><td>1ère personne du singulier</td></tr>
                <tr><td><b>Tu</b></td><td>2ème personne du singulier</td></tr>
                <tr><td><b>Il / Elle</b></td><td>3ème personne du singulier</td></tr>
            </table>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_lecons_conj, "← Revenir aux Leçons de Conjugaison")

    def creer_page_lecon_conj_pluriel(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#4361EE; color:#fff; font-size:14pt; font-weight:bold; padding:6px 16px; border-radius:12px;">📅 Mercredi 14 Octobre 2026</span></p>
            <p style="font-size:15pt; font-weight:800; color:#FF2E93; margin-top:8px;">📖 Les Pronoms Personnels Sujets aux Pluriels</p>
            <div style="background:#ffffff; border:3px solid #80DEEA; border-radius:14px; padding:14px; text-align:left; font-size:12pt; line-height:2.2;">
                Les pronoms personnels sujets au pluriel sont :<br>
                ✦ <b style="color:#0D47A1;">Nous</b> (1ère personne du pluriel)<br>
                ✦ <b style="color:#0D47A1;">Vous</b> (2ème personne du pluriel)<br>
                ✦ <b style="color:#D81B60;">Ils</b> (3ème personne du pluriel masculin)<br>
                ✦ <b style="color:#D81B60;">Elles</b> (3ème personne du pluriel féminin)
            </div>
            <div style="background:#E8F5E9; border-radius:12px; padding:12px; margin-top:10px; font-size:11pt; color:#1B5E20; font-weight:bold; text-align:left; line-height:1.9;">
                ✦ On emploie <b style="color:#D81B60;">Ils</b> quand il s'agit de 2 ou plusieurs garçons, personnes masculines ou animaux.<br>
                <i>Exemple :</i> Luc et Paul vont à l'école. ➔ <b style="color:#0D47A1;">Ils</b> vont à l'école.<br><br>
                ✦ On emploie <b style="color:#D81B60;">Elles</b> quand il s'agit de 2 ou plusieurs filles, personnes féminines ou animaux.<br>
                <i>Exemple :</i> Amina et Marie jouent. ➔ <b style="color:#0D47A1;">Elles</b> jouent.
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_lecons_conj, "← Revenir aux Leçons de Conjugaison")

    def creer_page_lecon_gramm_26_lettres(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#4361EE; color:#fff; font-size:14pt; font-weight:bold; padding:6px 16px; border-radius:12px;">📅 Lundi 21 Septembre 2026</span></p>
            <p style="font-size:15pt; font-weight:800; color:#FF2E93; margin-top:8px;">📖 Les 26 Lettres de l'Alphabet Français</p>
            <div style="background:#ffffff; border:3px solid #80DEEA; border-radius:14px; padding:12px; text-align:center; font-size:12pt; line-height:2;">
                <b style="color:#0D47A1; letter-spacing:1px;">a - b - c - d - e - f - g - h - i - j - k - l - m<br>
                n - o - p - q - r - s - t - u - v - w - x - y - z</b>
            </div>
            <div style="background:#E1F5FE; border-radius:12px; padding:12px; margin-top:12px; text-align:left; font-size:11pt; line-height:2;">
                ✦ Dans l'alphabet français, il y a exactement <b style="color:#D81B60;">26 lettres</b>.<br>
                ✦ Il y a <b style="color:#1B5E20;">6 voyelles :</b> <b>a - e - i - o - u - y</b>.<br>
                ✦ Il y a <b style="color:#0D47A1;">20 consonnes :</b> <b>b - c - d - f - g - h - j - k - l - m - n - p - q - r - s - t - v - w - x - z</b>.
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_lecons_gramm, "← Revenir aux Leçons de Grammaire")

    def creer_page_lecon_gramm_syllabes(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#4361EE; color:#fff; font-size:14pt; font-weight:bold; padding:6px 16px; border-radius:12px;">📅 Mercredi 07 Octobre 2026</span></p>
            <p style="font-size:15pt; font-weight:800; color:#FF2E93; margin-top:8px;">📖 Les Syllabes</p>
            <div style="background:#ffffff; border:3px solid #80DEEA; border-radius:14px; padding:12px; text-align:left; font-size:11pt; line-height:2;">
                ✦ Une <b>syllabe</b> est une partie de mot que l'on prononce d'un seul coup de voix, contient une voyelle prononcée.<br>
                ✦ En frappant dans les mains, on peut compter et séparer les syllabes d'un mot.
            </div>
            <p align="left" style="font-weight:bold; color:#1B5E20; margin-top:10px;">Exemples de séparation et de comptage :</p>
            <div style="background:#FFF9C4; border-radius:12px; padding:12px; font-size:11pt; line-height:2.2; text-align:left; font-weight:bold; color:#3E2723;">
                • pa - pa = <b>2 syllabes</b><br>
                • mou - le = <b>2 syllabes</b><br>
                • vil - la - ge = <b>3 syllabes</b><br>
                • ma - la - de = <b>3 syllabes</b><br>
                • pro - me - na - de = <b>4 syllabes</b><br>
                • py - ra - mi - de = <b>4 syllabes</b><br>
                • lo - co - mo - ti - ve = <b>5 syllabes</b>
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_lecons_gramm, "← Revenir aux Leçons de Grammaire")

    def creer_page_lecon_gramm_noms(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#4361EE; color:#fff; font-size:14pt; font-weight:bold; padding:6px 16px; border-radius:12px;">📖 Grammaire : Les Noms</span></p>

            <p align="left" style="font-size:13pt; font-weight:bold; color:#0D47A1; margin-top:10px;">1) Qu'est-ce qu'un nom ?</p>
            <div style="background:#ffffff; border:3px solid #80DEEA; border-radius:14px; padding:12px; text-align:left; font-size:11pt; line-height:2;">
                Le nom est un mot qui sert à nommer une <b>personne</b>, un <b>animal</b> ou une <b>chose</b>.
            </div>
            <div style="background:#E8F5E9; border-radius:12px; padding:12px; margin-top:8px; font-size:11pt; line-height:2.2; text-align:left;">
                ✦ <b style="color:#0D47A1;">Noms de personnes :</b> Marius, Claudette, le maître, maman, Jean, le bébé.<br>
                ✦ <b style="color:#2E7D32;">Noms d'animaux :</b> le chat, la crevette, le boeuf, le papillon, le mouton.<br>
                ✦ <b style="color:#D81B60;">Noms de choses :</b> le stylo, la gourde, le tableau, la table, la trousse.
            </div>

            <div style="margin-top:16px; background:#FEF2F2; border:3px solid #EF4444; border-radius:14px; padding:14px; text-align:left;">
                <p style="text-align:center; margin:0 0 8px 0;">
                    <span style="background:#DC2626; color:#ffffff; font-size:12pt; font-weight:bold; padding:4px 12px; border-radius:10px;">
                        📅 Mardi 27 Octobre 2026 — Suite les noms
                    </span>
                </p>
                <p style="font-size:13pt; font-weight:bold; color:#991B1B; margin:6px 0;">✨ Les noms propres :</p>
                <div style="background:#ffffff; border-radius:10px; padding:12px; font-size:12pt; line-height:2.2; color:#1F2937;">
                    ✦ <b>Un nom propre</b> commence toujours par une <b>lettre majuscule</b>.<br>
                    ✦ Il appartient à :
                    <ul style="margin:4px 0; padding-left:22px;">
                        <li><b>une seule personne</b> (ex : <i>Marius, Claudette</i>),</li>
                        <li><b>une seule chose</b>,</li>
                        <li><b>un quartier</b> (ex : <i>Mandroseza</i>),</li>
                        <li><b>un pays</b> (ex : <i>Madagascar, France</i>).</li>
                    </ul>
                </div>
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_lecons_gramm, "← Revenir aux Leçons de Grammaire")

    def creer_page_lecon_vocab_corps(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#4361EE; color:#fff; font-size:14pt; font-weight:bold; padding:6px 16px; border-radius:12px;">📅 Jeudi 01 Octobre 2026</span></p>
            <p style="font-size:15pt; font-weight:800; color:#FF2E93; margin-top:8px;">📖 Vocabulaire : La propreté du corps</p>
            <div style="background:#ffffff; border:3px solid #80DEEA; border-radius:14px; padding:12px; text-align:left; font-size:11pt; line-height:2.2;">
                Pour être propre et en bonne santé :<br>
                ✦ On doit se <b>brosser les dents</b> après chaque repas.<br>
                ✦ On doit se <b>laver le visage</b> et les yeux chaque matin.<br>
                ✦ Pour entretenir le corps : couper ses <b>ongles</b>, laver les <b>pieds</b> et protéger la <b>peau</b>.
            </div>
            <p align="left" style="font-weight:bold; color:#0D47A1; margin-top:10px;">🚿 Comment prendre une douche ?</p>
            <div style="background:#E1F5FE; border-radius:12px; padding:12px; font-size:11pt; line-height:2.1; text-align:left; color:#01579B;">
                1. On a besoin de <b>l'eau</b> et du <b>savon</b>.<br>
                2. On verse de l'eau sur le corps.<br>
                3. On savonne bien le corps.<br>
                4. On frotte bien le corps pour enlever toute la saleté.<br>
                5. On se lave les mains et on s'essuie avec une serviette propre.
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_lecons_vocab, "← Revenir aux Leçons de Vocabulaire")

    def creer_page_lecon_vocab_environnement(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#4361EE; color:#fff; font-size:14pt; font-weight:bold; padding:6px 16px; border-radius:12px;">📅 Mardi 06 Octobre 2026</span></p>
            <p style="font-size:15pt; font-weight:800; color:#FF2E93; margin-top:8px;">📖 Vocabulaire : La propreté de l'environnement</p>
            <div style="background:#ffffff; border:3px solid #80DEEA; border-radius:14px; padding:12px; text-align:left; font-size:11pt; line-height:2.2;">
                ✦ On <b>ne jette pas par terre</b> les ordures comme les bouts de papiers, les bouts de craie, les sachets.<br>
                ✦ <b>Il est interdit</b> de salir l'environnement.<br>
                ✦ Avant de prendre un sachet ou une boîte, on doit toujours se laver les mains.<br>
                ✦ L'élève est <b>responsable</b> de la propreté de sa classe et de sa cour.<br>
                ✦ Il faut <b>donner le bon exemple</b> à ses camarades en déposant les déchets dans la poubelle.
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_lecons_vocab, "← Revenir aux Leçons de Vocabulaire")

    def creer_page_lecon_vocab_ecole(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#4361EE; color:#fff; font-size:14pt; font-weight:bold; padding:6px 16px; border-radius:12px;">📅 Mardi 20 Octobre 2026</span></p>
            <p style="font-size:16pt; font-weight:800; color:#FF2E93; margin-top:8px;">📖 Vocabulaire : L'école</p>

            <p align="left" style="font-weight:bold; color:#0D47A1; margin-top:8px;">🏫 À l'école, on trouve :</p>
            <div style="background:#ffffff; border:2px solid #80DEEA; border-radius:12px; padding:10px; text-align:left; font-size:11pt; line-height:2;">
                ✦ <b>La directrice</b><br>
                ✦ <b>Les maîtresses</b><br>
                ✦ <b>Les écoliers</b>
            </div>

            <p align="left" style="font-weight:bold; color:#1B5E20; margin-top:8px;">🪑 Les effets scolaires dans la classe :</p>
            <div style="background:#E8F5E9; border-radius:12px; padding:10px; text-align:left; font-size:11pt; line-height:2;">
                Le tableau &nbsp;—&nbsp; la règle &nbsp;—&nbsp; les tables-bancs &nbsp;—&nbsp; la craie.
            </div>

            <p align="left" style="font-weight:bold; color:#D81B60; margin-top:8px;">🎒 Les fournitures scolaires de l'écolier :</p>
            <div style="background:#FFF3E0; border-radius:12px; padding:10px; text-align:left; font-size:11pt; line-height:2;">
                Les cahiers &nbsp;—&nbsp; les stylos &nbsp;—&nbsp; les livres &nbsp;—&nbsp; le crayon &nbsp;—&nbsp; la gomme &nbsp;—&nbsp; la trousse &nbsp;—&nbsp; le taille-crayon &nbsp;—&nbsp; les feutres &nbsp;—&nbsp; les crayons de couleur &nbsp;—&nbsp; la paire de ciseaux.
            </div>

            <div style="margin-top:16px; background:#EFF6FF; border:3px solid #3B82F6; border-radius:14px; padding:14px; text-align:left;">
                <p style="text-align:center; margin:0 0 8px 0;">
                    <span style="background:#1D4ED8; color:#ffffff; font-size:12pt; font-weight:bold; padding:4px 12px; border-radius:10px;">
                        📅 Mardi 27 Octobre 2026 — Suite à l'école
                    </span>
                </p>
                <div style="background:#ffffff; border-radius:10px; padding:12px; font-size:12pt; line-height:2.2; color:#1E3A8A; font-weight:bold;">
                    ✦ Notre école s'appelle : <span style="color:#D90429;">Mon enfance</span>.<br>
                    ✦ Elle est dirigée par : <span style="color:#D90429;">Madame Razafindrazaza Marcelline</span>.<br>
                    ✦ C'est une école <b>privée</b>.<br>
                    ✦ Elle se trouve à : <span style="color:#047857;">Mandroseza</span>.<br>
                    ✦ Les classes qui existent sont :
                    <ul style="margin:4px 0; padding-left:24px; color:#111827;">
                        <li><span style="color:#7C3AED;">préscolaire</span>.</li>
                        <li><span style="color:#7C3AED;">primaire</span>.</li>
                    </ul>
                </div>
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_lecons_vocab, "← Revenir aux Leçons de Vocabulaire")

    # =========================================================================
    # DICTÉES PRÉPARÉES & EXERCICES DE FRANÇAIS
    # =========================================================================
    def creer_page_exercices_dictee(self):
        page = QWidget()
        self.style_fond(page)
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(12, 12, 12, 12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        conteneur = QWidget()
        cadre_layout = QVBoxLayout(conteneur)

        self.titre_exercices_dictee = self.creer_titre("Dictée préparée\nChoisissez une dictée")
        cadre_layout.addWidget(self.titre_exercices_dictee)

        self.groupe_exercices_dictee = QButtonGroup(self)
        self.groupe_exercices_dictee.setExclusive(True)

        self.boutons_exercices_dictee = [
            self.creer_bouton_rose_3d("1-Vendredi 02 Octobre (Je porte un pyjama bleu...)"),
            self.creer_bouton_rose_3d("1-Vendredi 09 Octobre (Je plante un pin...)"),
            self.creer_bouton_rose_3d("1-Vendredi 16 Octobre (Il brosse seul les dents...)"),
            self.creer_bouton_rose_3d("1-Jeudi 22 Octobre (La propreté est bon pour nous...)"),
            self.creer_bouton_rose_3d("1-Ils montrent la carte de l'étudiant.")
        ]

        for b in self.boutons_exercices_dictee:
            self.groupe_exercices_dictee.addButton(b)
            cadre_layout.addWidget(b)
            b.clicked.connect(lambda checked=False, btn=b: self.selectionner_exercice_dictee(btn.text()))

        self.bouton_choose_ex_dictee = self.creer_bouton_choose("Choose")
        self.bouton_choose_ex_dictee.clicked.connect(self.confirmer_choix_exercice_dictee)
        cadre_layout.addWidget(self.bouton_choose_ex_dictee)

        btn_ret = QPushButton("← Revenir aux exercices de Français")
        btn_ret.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ret.setStyleSheet("QPushButton { background-color: #6C757D; color: white; font-size: 15px; font-weight: bold; border-radius: 12px; padding: 6px; }")
        btn_ret.clicked.connect(self.retour_a_fr_exercices)
        cadre_layout.addWidget(btn_ret)

        scroll.setWidget(conteneur)
        page_layout.addWidget(scroll)
        return page

    def creer_page_ex_dictee_02_oct(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#4361EE; color:#fff; font-size:14pt; font-weight:bold; padding:6px 16px; border-radius:12px;">📅 Vendredi 02 Octobre 2026</span></p>
            <p style="font-size:16pt; font-weight:800; color:#FF2E93;">✏️ Dictée préparée</p>
            <div style="background:#ffffff; border:3px solid #80DEEA; border-radius:14px; padding:16px; text-align:left; font-size:13pt; line-height:2.4;">
                ✦ <b style="color:#0D47A1;">Je porte un pyjama bleu.</b><br>
                ✦ <b style="color:#0D47A1;">Tu mange le riz.</b><br>
                ✦ <b style="color:#0D47A1;">Marius coupe ses ongles vendredi.</b><br>
                ✦ <b style="color:#0D47A1;">Elle lave le visage de mon neveu.</b><br>
                ✦ <b style="color:#0D47A1;">Il est à Paris.</b>
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_exercices_dictee, "← Revenir aux Dictées préparées")

    def creer_page_ex_dictee_09_oct(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#4361EE; color:#fff; font-size:14pt; font-weight:bold; padding:6px 16px; border-radius:12px;">📅 Vendredi 09 Octobre 2026</span></p>
            <p style="font-size:16pt; font-weight:800; color:#FF2E93;">✏️ Dictée préparée</p>
            <div style="background:#ffffff; border:3px solid #80DEEA; border-radius:14px; padding:16px; text-align:left; font-size:13pt; line-height:2.4;">
                ✦ <b style="color:#0D47A1;">Je plante un pin.</b><br>
                ✦ <b style="color:#0D47A1;">Elle adore la propreté.</b><br>
                ✦ <b style="color:#0D47A1;">Tu porte un habit propre.</b><br>
                ✦ <b style="color:#0D47A1;">Maman regarde le prix du riz.</b><br>
                ✦ <b style="color:#0D47A1;">Il est sur l'île verte.</b>
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_exercices_dictee, "← Revenir aux Dictées préparées")

    def creer_page_ex_dictee_16_oct(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#4361EE; color:#fff; font-size:14pt; font-weight:bold; padding:6px 16px; border-radius:12px;">📅 Vendredi 16 Octobre 2026</span></p>
            <p style="font-size:16pt; font-weight:800; color:#FF2E93;">✏️ Dictée préparée</p>
            <div style="background:#ffffff; border:3px solid #80DEEA; border-radius:14px; padding:16px; text-align:left; font-size:13pt; line-height:2.4;">
                ✦ <b style="color:#0D47A1;">Il brosse seule les dents.</b><br>
                ✦ <b style="color:#0D47A1;">Nous gardons la salle propre.</b><br>
                ✦ <b style="color:#0D47A1;">Vous avez une jolie fleur dans le jardin.</b><br>
                ✦ <b style="color:#0D47A1;">Je suis dans la cour.</b><br>
                ✦ <b style="color:#0D47A1;">Élise adore Fanny.</b>
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_exercices_dictee, "← Revenir aux Dictées préparées")

    def creer_page_ex_dictee_22_oct(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#4361EE; color:#fff; font-size:14pt; font-weight:bold; padding:6px 16px; border-radius:12px;">📅 Jeudi 22 Octobre 2026</span></p>
            <p style="font-size:16pt; font-weight:800; color:#FF2E93;">✏️ Dictée préparée</p>
            <div style="background:#ffffff; border:3px solid #80DEEA; border-radius:14px; padding:16px; text-align:left; font-size:13pt; line-height:2.4;">
                ✦ <b style="color:#0D47A1;">La propreté est est bon pour nous.</b><br>
                ✦ <b style="color:#0D47A1;">Nous gardons la salle propre.</b><br>
                ✦ <b style="color:#0D47A1;">Médor te mordra.</b><br>
                ✦ <b style="color:#0D47A1;">Aline prépare le déjeuner.</b><br>
                ✦ <b style="color:#0D47A1;">Elles ont des jolis noeuds.</b>
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_exercices_dictee, "← Revenir aux Dictées préparées")

    def creer_page_ex_dictee_30_oct(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#4361EE; color:#fff; font-size:14pt; font-weight:bold; padding:6px 16px; border-radius:12px;">📅 Vendredi 30 Octobre 2026</span></p>
            <p style="font-size:16pt; font-weight:800; color:#FF2E93;">✏️ Dictée préparée</p>
            <div style="background:#ffffff; border:3px solid #80DEEA; border-radius:14px; padding:16px; text-align:left; font-size:13pt; line-height:2.4;">
                ✦ <b style="color:#0D47A1;">Ils montrent la carte de l'étudiant.</b><br>
                ✦ <b style="color:#0D47A1;">Une écolière surveille les élèves.</b><br>
                ✦ <b style="color:#0D47A1;">Nous cultivons un are de riz.</b><br>
                ✦ <b style="color:#0D47A1;">Le fleuve a débordé sur le jardin planté.</b><br>
                ✦ <b style="color:#0D47A1;">La clématite couvre la clôture du jardin.</b>
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_exercices_dictee, "← Revenir aux Dictées préparées")

    def creer_page_exercices_orthographe(self):
        page = QWidget()
        self.style_fond(page)
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(12, 12, 12, 12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        conteneur = QWidget()
        cadre_layout = QVBoxLayout(conteneur)

        self.titre_exercices_ortho = self.creer_titre("Exercices d'Orthographe\nChoisissez un exercice")
        cadre_layout.addWidget(self.titre_exercices_ortho)

        self.groupe_exercices_ortho = QButtonGroup(self)
        self.groupe_exercices_ortho.setExclusive(True)

        self.boutons_exercices_ortho = [
            self.creer_bouton_rose_3d("1-Complete par ie, y , it."),
            self.creer_bouton_rose_3d("1-Complete par is, id, iz."),
            self.creer_bouton_rose_3d("1-Complete par î , isc."),
            self.creer_bouton_rose_3d("1-Complete par e, eu."),
            self.creer_bouton_rose_3d("1-Complete par oeu, oei."),
            self.creer_bouton_rose_3d("1-Dictée.")
        ]

        for b in self.boutons_exercices_ortho:
            self.groupe_exercices_ortho.addButton(b)
            cadre_layout.addWidget(b)
            b.clicked.connect(lambda checked=False, btn=b: self.selectionner_exercice_ortho(btn.text()))

        self.bouton_choose_ex_ortho = self.creer_bouton_choose("Choose")
        self.bouton_choose_ex_ortho.clicked.connect(self.confirmer_choix_exercice_ortho)
        cadre_layout.addWidget(self.bouton_choose_ex_ortho)

        btn_ret = QPushButton("← Revenir aux exercices de Français")
        btn_ret.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ret.setStyleSheet("QPushButton { background-color: #6C757D; color: white; font-size: 15px; font-weight: bold; border-radius: 12px; padding: 6px; }")
        btn_ret.clicked.connect(self.retour_a_fr_exercices)
        cadre_layout.addWidget(btn_ret)

        scroll.setWidget(conteneur)
        page_layout.addWidget(scroll)
        return page

    def creer_page_ex_ortho_ie_y_it(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#4361EE; color:#fff; font-size:14pt; font-weight:bold; padding:6px 16px; border-radius:12px;">📅 Mardi 22 Septembre 2026</span></p>
            <p style="font-size:15pt; font-weight:800; color:#FF2E93;">✏️ Orthographe — Exercices</p>
            <p align="left" style="font-weight:bold; color:#0D47A1;">1) Il y a combien de lettres dans l'alphabet français ?</p>
            <div style="background:#E1F5FE; border-radius:10px; padding:8px; font-weight:bold; color:#1B5E20; text-align:left;">
                Il y a 26 lettres.
            </div>
            <p align="left" style="font-weight:bold; color:#0D47A1;">2) Complète par : ie , y , it :</p>
            <div style="background:#fff; border:2px solid #80DEEA; border-radius:10px; padding:10px; text-align:left; font-size:12pt; line-height:2;">
                ✦ le l<b>it</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp; le padd<b>y</b><br>
                ✦ Marie &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp; un pyjama<br>
                ✦ la nu<b>it</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp; le st<b>y</b>lo<br>
                ✦ la v<b>ie</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp; le paraplu<b>ie</b>
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_exercices_ortho, "← Revenir aux exercices d'Orthographe")

    def creer_page_ex_ortho_is_id_iz(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#4361EE; color:#fff; font-size:14pt; font-weight:bold; padding:6px 16px; border-radius:12px;">📅 Lundi 14 Septembre 2026</span></p>
            <p style="font-size:15pt; font-weight:800; color:#FF2E93;">✏️ Orthographe — Exercices</p>
            <p align="left" style="font-weight:bold; color:#0D47A1;">1) Complète par : is , id , iz :</p>
            <div style="background:#fff; border:2px solid #80DEEA; border-radius:10px; padding:10px; text-align:left; font-size:12pt; line-height:2;">
                ✦ le r<b>iz</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp; le tap<b>is</b><br>
                ✦ une sour<b>is</b> &nbsp;|&nbsp;&nbsp; le n<b>id</b><br>
                ✦ le l<b>it</b>
            </div>
            <p align="left" style="font-weight:bold; color:#0D47A1;">2) Cherche 2 mots qui contiennent « is » :</p>
            <div style="background:#E1F5FE; border-radius:10px; padding:8px; font-weight:bold; color:#0D47A1; text-align:left;">
                ✦ tapis &nbsp;&nbsp;|&nbsp;&nbsp; ✦ souris
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_exercices_ortho, "← Revenir aux exercices d'Orthographe")

    def creer_page_ex_ortho_i_isc(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#4361EE; color:#fff; font-size:14pt; font-weight:bold; padding:6px 16px; border-radius:12px;">📅 Mardi 06 Octobre 2026</span></p>
            <p style="font-size:15pt; font-weight:800; color:#FF2E93;">✏️ Orthographe — Exercices</p>
            <p align="left" style="font-weight:bold; color:#0D47A1;">1) Complète par : î , isc :</p>
            <div style="background:#fff; border:2px solid #80DEEA; border-radius:10px; padding:10px; text-align:left; font-size:12pt; line-height:2;">
                ✦ l'<b>î</b>le &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp; une ab<b>î</b>me<br>
                ✦ la perdrix &nbsp;&nbsp;|&nbsp;&nbsp; le h<b>isc</b>
            </div>
            <p align="left" style="font-weight:bold; color:#0D47A1;">2) Donne 1 mot qui contient « h » :</p>
            <div style="background:#E1F5FE; border-radius:10px; padding:8px; font-weight:bold; color:#1B5E20; text-align:left;">
                ✦ hibou
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_exercices_ortho, "← Revenir aux exercices d'Orthographe")

    def creer_page_ex_ortho_e_eu(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p style="font-size:15pt; font-weight:800; color:#FF2E93;">✏️ Orthographe — Exercices</p>
            <p align="left" style="font-weight:bold; color:#0D47A1;">1) Complète par : e , eu :</p>
            <div style="background:#fff; border:2px solid #80DEEA; border-radius:10px; padding:10px; text-align:left; font-size:12pt; line-height:2;">
                ✦ promenade &nbsp;|&nbsp; fl<b>eu</b>ve<br>
                ✦ petite &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|&nbsp; le j<b>eu</b>
            </div>
            <p align="left" style="font-weight:bold; color:#0D47A1;">2) Cherche 2 mots qui contiennent « eu » :</p>
            <div style="background:#E1F5FE; border-radius:10px; padding:8px; font-weight:bold; color:#0D47A1; text-align:left;">
                ✦ le jeu &nbsp;&nbsp;|&nbsp;&nbsp; ✦ fleuve
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_exercices_ortho, "← Revenir aux exercices d'Orthographe")

    def creer_page_ex_ortho_oeu_oei(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#4361EE; color:#fff; font-size:14pt; font-weight:bold; padding:6px 16px; border-radius:12px;">📅 Mardi 15 Octobre 2026</span></p>
            <p style="font-size:15pt; font-weight:800; color:#FF2E93;">✏️ Orthographe — Exercices</p>
            <p align="left" style="font-weight:bold; color:#0D47A1;">1) Complète par : oeu , oei :</p>
            <div style="background:#fff; border:2px solid #80DEEA; border-radius:10px; padding:10px; text-align:left; font-size:12pt; line-height:2;">
                ✦ un n<b>oeu</b>d &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp; une s<b>oeu</b>r<br>
                ✦ l'<b>oei</b>l &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp; le b<b>oeu</b>f
            </div>
            <p align="left" style="font-weight:bold; color:#0D47A1;">2) Cherche 2 mots qui contiennent « oeu » :</p>
            <div style="background:#E1F5FE; border-radius:10px; padding:8px; font-weight:bold; color:#0D47A1; text-align:left;">
                ✦ boeuf &nbsp;&nbsp;|&nbsp;&nbsp; ✦ soeur
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_exercices_ortho, "← Revenir aux exercices d'Orthographe")

    def creer_page_ex_ortho_dictee_ar(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#4361EE; color:#fff; font-size:14pt; font-weight:bold; padding:6px 16px; border-radius:12px;">📅 Mardi 27 Octobre 2026</span></p>
            <p style="font-size:16pt; font-weight:800; color:#FF2E93;">✏️ Orthographe — Dictée & Exercices</p>

            <p align="left" style="font-weight:bold; color:#0D47A1; margin-top:8px;">1) Dictée :</p>
            <div style="background:#fff; border:2px solid #80DEEA; border-radius:10px; padding:10px; font-size:12pt; font-weight:bold; color:#1E3A8A; text-align:left;">
                une armoire &nbsp;—&nbsp; un are &nbsp;—&nbsp; un mare &nbsp;—&nbsp; la carte
            </div>

            <p align="left" style="font-weight:bold; color:#0D47A1; margin-top:10px;">2) Complète par : are - ar :</p>
            <div style="background:#fff; border:2px solid #80DEEA; border-radius:10px; padding:10px; font-size:12pt; text-align:left; line-height:2;">
                ✦ la t<b style="color:#D81B60;">are</b> &nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp; p<b style="color:#D81B60;">ar</b><br>
                ✦ un c<b style="color:#D81B60;">ar</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp; la m<b style="color:#D81B60;">are</b>
            </div>

            <p align="left" style="font-weight:bold; color:#0D47A1; margin-top:10px;">3) Trouves 1 mot contenant « are » :</p>
            <div style="background:#E1F5FE; border-radius:10px; padding:8px; font-size:12pt; font-weight:bold; color:#15803D; text-align:left;">
                ✦ la mare
            </div>

            <p align="left" style="font-weight:bold; color:#0D47A1; margin-top:10px;">4) Cherche 2 mots qui contient « ar » :</p>
            <div style="background:#E1F5FE; border-radius:10px; padding:8px; font-size:12pt; font-weight:bold; color:#15803D; text-align:left;">
                ✦ par &nbsp;&nbsp;|&nbsp;&nbsp; ✦ car
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_exercices_ortho, "← Revenir aux exercices d'Orthographe")

    def creer_page_exercices_conjugaison(self):
        page = QWidget()
        self.style_fond(page)
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(12, 12, 12, 12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        conteneur = QWidget()
        cadre_layout = QVBoxLayout(conteneur)

        self.titre_exercices_conj = self.creer_titre("Exercices de Conjugaison\nChoisissez un exercice")
        cadre_layout.addWidget(self.titre_exercices_conj)

        self.groupe_exercices_conj = QButtonGroup(self)
        self.groupe_exercices_conj.setExclusive(True)

        self.boutons_exercices_conj = [
            self.creer_bouton_rose_3d("1-Remplace par les pronoms personnels sujet je ou Tu..."),
            self.creer_bouton_rose_3d("1-Remplace les mots soulignés par Il ou Elle.."),
            self.creer_bouton_rose_3d("1-Remplace les mots soulignés par les PPS au sigulier."),
            self.creer_bouton_rose_3d("1-Remplace par les PPS Nous, Vous"),
            self.creer_bouton_rose_3d("1-Remplace par les mots soulignés par les PPS au pluriels"),
            self.creer_bouton_rose_3d("1-Remplace les mots soulignés.")
        ]

        for b in self.boutons_exercices_conj:
            self.groupe_exercices_conj.addButton(b)
            cadre_layout.addWidget(b)
            b.clicked.connect(lambda checked=False, btn=b: self.selectionner_exercice_conj(btn.text()))

        self.bouton_choose_ex_conj = self.creer_bouton_choose("Choose")
        self.bouton_choose_ex_conj.clicked.connect(self.confirmer_choix_exercice_conj)
        cadre_layout.addWidget(self.bouton_choose_ex_conj)

        btn_ret = QPushButton("← Revenir aux exercices de Français")
        btn_ret.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ret.setStyleSheet("QPushButton { background-color: #6C757D; color: white; font-size: 15px; font-weight: bold; border-radius: 12px; padding: 6px; }")
        btn_ret.clicked.connect(self.retour_a_fr_exercices)
        cadre_layout.addWidget(btn_ret)

        scroll.setWidget(conteneur)
        page_layout.addWidget(scroll)
        return page

    def creer_page_ex_conj_je_tu(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#4361EE; color:#fff; font-size:14pt; font-weight:bold; padding:6px 16px; border-radius:12px;">📅 Jeudi 24 Septembre 2026</span></p>
            <p style="font-size:15pt; font-weight:800; color:#FF2E93;">✏️ Conjugaison — Exercices</p>
            <p align="left" style="font-weight:bold; color:#0D47A1;">1) Remplace par « Je » ou « Tu » :</p>
            <div style="background:#fff; border:2px solid #80DEEA; border-radius:10px; padding:12px; text-align:left; font-size:12pt; line-height:2.2;">
                ✦ Moi joue dans la cour. ➔ <b style="color:#1B5E20;">Je</b> joue dans la cour.<br>
                ✦ Toi vas à l'école. ➔ <b style="color:#1B5E20;">Tu</b> vas à l'école.<br>
                ✦ Moi dessine un chapeau. ➔ <b style="color:#1B5E20;">Je</b> dessine un chapeau.<br>
                ✦ Toi as un stylo. ➔ <b style="color:#1B5E20;">Tu</b> as un stylo.
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_exercices_conj, "← Revenir aux exercices de Conjugaison")

    def creer_page_ex_conj_il_elle(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p style="font-size:15pt; font-weight:800; color:#FF2E93;">✏️ Conjugaison — Exercices</p>
            <p align="left" style="font-weight:bold; color:#0D47A1;">1) Remplace les mots soulignés par « Il » ou « Elle » :</p>
            <div style="background:#fff; border:2px solid #80DEEA; border-radius:10px; padding:12px; text-align:left; font-size:12pt; line-height:2.2;">
                ✦ <u>René</u> continue son devoir. ➔ <b style="color:#1B5E20;">Il</b> continue son devoir.<br>
                ✦ <u>Julie</u> est malade. ➔ <b style="color:#1B5E20;">Elle</b> est malade.<br>
                ✦ <u>Ma tante</u> va au marché. ➔ <b style="color:#1B5E20;">Elle</b> va au marché.<br>
                ✦ <u>Mathis</u> est gentil. ➔ <b style="color:#1B5E20;">Il</b> est gentil.
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_exercices_conj, "← Revenir aux exercices de Conjugaison")

    def creer_page_ex_conj_singulier(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p style="font-size:15pt; font-weight:800; color:#FF2E93;">✏️ Conjugaison — Exercices</p>
            <p align="left" style="font-weight:bold; color:#0D47A1;">1) Remplace les mots soulignés par les PPS au singulier :</p>
            <div style="background:#fff; border:2px solid #80DEEA; border-radius:10px; padding:12px; text-align:left; font-size:12pt; line-height:2.2;">
                ✦ <u>Le garçon</u> mange du chocolat. ➔ <b style="color:#1B5E20;">Il</b> mange du chocolat.<br>
                ✦ <u>Amina</u> dort seule. ➔ <b style="color:#1B5E20;">Elle</b> dort seule.<br>
                ✦ <u>Max</u> joue au ballon. ➔ <b style="color:#1B5E20;">Il</b> joue au ballon.<br>
                ✦ <u>Mon frère</u> lit la leçon. ➔ <b style="color:#1B5E20;">Il</b> lit la leçon.
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_exercices_conj, "← Revenir aux exercices de Conjugaison")

    def creer_page_ex_conj_nous_vous(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#4361EE; color:#fff; font-size:14pt; font-weight:bold; padding:6px 16px; border-radius:12px;">📅 Jeudi 15 Octobre 2026</span></p>
            <p style="font-size:15pt; font-weight:800; color:#FF2E93;">✏️ Conjugaison — Exercices</p>
            <p align="left" style="font-weight:bold; color:#0D47A1;">1) Remplace par les PPS « Nous » et « Vous » :</p>
            <div style="background:#fff; border:2px solid #80DEEA; border-radius:10px; padding:12px; text-align:left; font-size:12pt; line-height:2.2;">
                ✦ Toi et moi regardons la télévision. ➔ <b style="color:#1B5E20;">Nous</b> regardons la télévision.<br>
                ✦ Toi et mon maître allez à Rome. ➔ <b style="color:#1B5E20;">Vous</b> allez à Rome.<br>
                ✦ Moi et maman achetons un stylo. ➔ <b style="color:#1B5E20;">Nous</b> achetons un stylo.<br>
                ✦ Toi et Lucie avez un joli cartable. ➔ <b style="color:#1B5E20;">Vous</b> avez un joli cartable.
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_exercices_conj, "← Revenir aux exercices de Conjugaison")

    def creer_page_ex_conj_pluriels(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#4361EE; color:#fff; font-size:14pt; font-weight:bold; padding:6px 16px; border-radius:12px;">📅 Mardi 20 Octobre 2026</span></p>
            <p style="font-size:15pt; font-weight:800; color:#FF2E93;">✏️ Conjugaison — Exercices</p>
            <p align="left" style="font-weight:bold; color:#0D47A1;">1) Remplace par les PPS au pluriel :</p>
            <div style="background:#fff; border:2px solid #80DEEA; border-radius:10px; padding:12px; text-align:left; font-size:12pt; line-height:2.2;">
                ✦ <u>Toi et Marie</u> avez mal au coeur. ➔ <b style="color:#1B5E20;">Vous</b> avez mal au coeur.<br>
                ✦ <u>Moi et papa</u> adorons le thé. ➔ <b style="color:#1B5E20;">Nous</b> adorons le thé.<br>
                ✦ <u>Les filles</u> entrent dans la salle. ➔ <b style="color:#1B5E20;">Elles</b> entrent dans la salle.<br>
                ✦ <u>Mathieu et Jules</u> jouent à la corde. ➔ <b style="color:#1B5E20;">Ils</b> jouent à la corde.
            </div>
        </body></html>
        """
        return self.creer_page_affichage(html, self.retour_a_exercices_conj, "← Revenir aux exercices de Conjugaison")

    def creer_page_ex_conj_remplace_soulignes(self):
        html = """
        <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
            <p><span style="background:#4361EE; color:#fff; font-size:14pt; font-weight:bold; padding:6px 16px; border-radius:12px;">📅 Lundi 26 Octobre 2026</span></p>
            <p style="font-size:16pt; font-weight:800; color:#FF2E93;">✏️ Conjugaison — Exercices</p>

            <p align="left" style="font-weight:bold; color:#0D47A1;">1) Remplace les mots soulignés par : Ils, Elles, Nous, Vous :</p>
            <div style="background:#fff; border:2px solid #80DEEA; border-radius:10px; padding:12px; font-size:12pt; line-height:2.3; text-align:left;">
                ✦ <u>Marie et Clara</u> étudient bien.<br>
                &nbsp;&nbsp;&nbsp;➔ <b style="color:#15803D;">Elles</b><br><br>
                ✦ <u>Jonathan et André</u> utilisent une moule.<br>
                &nbsp;&nbsp;&nbsp;➔ <b style="color:#15803D;">Ils</b><br><br>
                ✦ <u>Moi et Jean</u> assoyons près de la mare.<br>
                &nbsp;&nbsp;&nbsp;➔ <b style="color:#15803D;">Nous</b><br><br>
                ✦ <u>Toi et Victor</u> avez votre stylo.<br>
                &nbsp;&nbsp;&nbsp;➔ <b style="color:#15803D;">Vous</b><br><br>
                ✦ <u>Max et Maxime</u> montrent la carte.<br>
                &nbsp;&nbsp;&nbsp;➔ <b style="color:#15803D;"> 
                Ils</b>
        </div>

        <p align="left" style="font-weight:bold; color:#0D47A1; margin-top:12px;">2) Cite les PPS :</p>
        <div style="background:#F0FDF4; border:2px dashed #16A34A; border-radius:10px; padding:10px; font-size:12pt; font-weight:bold; color:#166534; text-align:left;">
            - je, Tu, Il, Elle, Nous, Vous, Ils, Elles
        </div>
    </body></html>
    """
        return self.creer_page_affichage(html, self.retour_a_exercices_conj, "← Revenir aux exercices de Conjugaison")

    def creer_page_exercices_grammaire(self):
        page = QWidget()
        self.style_fond(page)
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(12, 12, 12, 12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        conteneur = QWidget()
        cadre_layout = QVBoxLayout(conteneur)

        self.titre_exercices_gramm = self.creer_titre("Exercices de Grammaire\nChoisissez un exercice")
        cadre_layout.addWidget(self.titre_exercices_gramm)

        self.groupe_exercices_gramm = QButtonGroup(self)
        self.groupe_exercices_gramm.setExclusive(True)

        self.boutons_exercices_gramm = [
            self.creer_bouton_rose_3d("1-Quels sont les 26 lettres de l'alphabet.."),
            self.creer_bouton_rose_3d("1-Combien y a t-il de voyelles..."),
            self.creer_bouton_rose_3d("1-Sépare les syllabes et donne ses nombres.."),
            self.creer_bouton_rose_3d("1-Compte et sépare les syllabes.."),
            self.creer_bouton_rose_3d("1-Complète par  animal-chose-personne.."),
            self.creer_bouton_rose_3d("1-Souligne la bonne réponse.")
        ]

        for b in self.boutons_exercices_gramm:
            self.groupe_exercices_gramm.addButton(b)
            cadre_layout.addWidget(b)
            b.clicked.connect(lambda checked=False, btn=b: self.selectionner_exercice_gramm(btn.text()))

        self.bouton_choose_ex_gramm = self.creer_bouton_choose("Choose")
        self.bouton_choose_ex_gramm.clicked.connect(self.confirmer_choix_exercice_gramm)
        cadre_layout.addWidget(self.bouton_choose_ex_gramm)

        btn_ret = QPushButton("← Revenir aux exercices de Français")
        btn_ret.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ret.setStyleSheet("QPushButton { background-color: #6C757D; color: white; font-size: 15px; font-weight: bold; border-radius: 12px; padding: 6px; }")
        btn_ret.clicked.connect(self.retour_a_fr_exercices)
        cadre_layout.addWidget(btn_ret)

        scroll.setWidget(conteneur)
        page_layout.addWidget(scroll)
        return page

    def creer_page_ex_gramm_26_lettres(self):
        html = """
    <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
        <p><span style="background:#4361EE; color:#fff; font-size:14pt; font-weight:bold; padding:6px 16px; border-radius:12px;">📅 Lundi 21 Septembre 2026</span></p>
        <p style="font-size:15pt; font-weight:800; color:#FF2E93;">✏️ Grammaire — Exercices</p>
        <p align="left" style="font-weight:bold; color:#0D47A1;">1) Quels sont les 26 lettres de l'alphabet français ?</p>
        <div style="background:#fff; border:2px solid #80DEEA; border-radius:10px; padding:12px; font-size:12pt; line-height:2; text-align:left;">
            <b style="color:#D81B60;">a - b - c - d - e - f - g - h - i - j - k - l - m - n - o - p - q - r - s - t - u - v - w - x - y - z</b>
        </div>
        <p align="left" style="font-weight:bold; color:#0D47A1;">2) Il y a combien de lettres dans l'alphabet français ?</p>
        <div style="background:#E1F5FE; border-radius:10px; padding:10px; font-size:12pt; font-weight:bold; color:#1B5E20; text-align:left;">
            Il y a 26 lettres.
        </div>
    </body></html>
    """
        return self.creer_page_affichage(html, self.retour_a_exercices_gramm, "← Revenir aux exercices de Grammaire")

    def creer_page_ex_gramm_voyelles(self):
        html = """
    <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
        <p><span style="background:#4361EE; color:#fff; font-size:14pt; font-weight:bold; padding:6px 16px; border-radius:12px;">📅 Mardi 29 Septembre 2026</span></p>
        <p style="font-size:15pt; font-weight:800; color:#FF2E93;">✏️ Grammaire — Voyelles et Consonnes</p>
        <p align="left" style="font-weight:bold; color:#0D47A1;">1) Combien y a-t-il de voyelles ?</p>
        <div style="background:#E1F5FE; border-radius:10px; padding:8px; font-size:12pt; font-weight:bold; color:#1B5E20; text-align:left;">
            Il y a 6 voyelles. (a - e - i - u - y - o)
        </div>
        <p align="left" style="font-weight:bold; color:#0D47A1;">2) Combien de consonnes y a-t-il ?</p>
        <div style="background:#E1F5FE; border-radius:10px; padding:8px; font-size:12pt; font-weight:bold; color:#1B5E20; text-align:left;">
            Il y a 20 consonnes.
        </div>
    </body></html>
    """
        return self.creer_page_affichage(html, self.retour_a_exercices_gramm, "← Revenir aux exercices de Grammaire")

    def creer_page_ex_gramm_separe_syllabes(self):
        html = """
    <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
        <p><span style="background:#4361EE; color:#fff; font-size:14pt; font-weight:bold; padding:6px 16px; border-radius:12px;">📅 Mercredi 07 Octobre 2026</span></p>
        <p style="font-size:15pt; font-weight:800; color:#FF2E93;">✏️ Grammaire — Exercices</p>
        <p align="left" style="font-weight:bold; color:#0D47A1;">1) Sépare les syllabes et donne ses nombres :</p>
        <div style="background:#fff; border:2px solid #80DEEA; border-radius:10px; padding:12px; font-size:12pt; line-height:2.2; text-align:left;">
            ✦ papa = <b style="color:#1B5E20;">pa - pa</b> = 2 syllabes<br>
            ✦ camarade = <b style="color:#1B5E20;">ca - ma - ra - de</b> = 4 syllabes<br>
            ✦ village = <b style="color:#1B5E20;">vi - lla - ge</b> = 3 syllabes<br>
            ✦ locomotive = <b style="color:#1B5E20;">lo - co - mo - ti - ve</b> = 5 syllabes<br>
            ✦ promenade = <b style="color:#1B5E20;">pro - me - na - de</b> = 4 syllabes
        </div>
    </body></html>
    """
        return self.creer_page_affichage(html, self.retour_a_exercices_gramm, "← Revenir aux exercices de Grammaire")

    def creer_page_ex_gramm_compte_syllabes(self):
        html = """
    <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
        <p><span style="background:#4361EE; color:#fff; font-size:14pt; font-weight:bold; padding:6px 16px; border-radius:12px;">📅 Lundi 12 Octobre 2026</span></p>
        <p style="font-size:15pt; font-weight:800; color:#FF2E93;">✏️ Grammaire — Exercices</p>
        <p align="left" style="font-weight:bold; color:#0D47A1;">1) Compte et sépare les syllabes :</p>
        <div style="background:#fff; border:2px solid #80DEEA; border-radius:10px; padding:12px; font-size:12pt; line-height:2.2; text-align:left;">
            ✦ chaloupe = <b style="color:#1B5E20;">cha - lou - pe</b> = 3 syllabes<br>
            ✦ moule = <b style="color:#1B5E20;">mou - le</b> = 2 syllabes<br>
            ✦ couture = <b style="color:#1B5E20;">cou - tu - re</b> = 3 syllabes<br>
            ✦ chicane = <b style="color:#1B5E20;">chi - ca - ne</b> = 3 syllabes<br>
            ✦ pyramide = <b style="color:#1B5E20;">py - ra - mi - de</b> = 4 syllabes
        </div>
    </body></html>
    """
        return self.creer_page_affichage(html, self.retour_a_exercices_gramm, "← Revenir aux exercices de Grammaire")

    def creer_page_ex_gramm_animal_chose_pers(self):
        html = """
    <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
        <p style="font-size:15pt; font-weight:800; color:#FF2E93;">✏️ Grammaire — Exercices</p>
        <p align="left" style="font-weight:bold; color:#0D47A1;">1) Complète par : animal — chose — personne :</p>
        <div style="background:#fff; border:2px solid #80DEEA; border-radius:10px; padding:12px; font-size:12pt; line-height:2.2; text-align:left;">
            ✦ Le stylo est un nom d'<b style="color:#1B5E20;">une chose</b>.<br>
            ✦ Marius est un nom d'<b style="color:#1B5E20;">une personne</b>.<br>
            ✦ Le chat est un nom d'<b style="color:#1B5E20;">un animal</b>.<br>
            ✦ La crevette est un nom d'<b style="color:#1B5E20;">un animal</b>.<br>
            ✦ Le tableau est un nom d'<b style="color:#1B5E20;">une chose</b>.
        </div>
    </body></html>
    """
        return self.creer_page_affichage(html, self.retour_a_exercices_gramm, "← Revenir aux exercices de Grammaire")

    def creer_page_ex_gramm_souligne_bonne_rep(self):
        html = """
    <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
        <p><span style="background:#4361EE; color:#fff; font-size:14pt; font-weight:bold; padding:6px 16px; border-radius:12px;">📅 Mercredi 28 Octobre 2026</span></p>
        <p style="font-size:16pt; font-weight:800; color:#FF2E93;">✏️ Grammaire — Souligne la bonne réponse</p>

        <p align="left" style="font-weight:bold; color:#0D47A1; margin-top:10px;">1) Soulignes la bonne réponse :</p>
        <div style="background:#fff; border:2px solid #80DEEA; border-radius:10px; padding:12px; font-size:12pt; line-height:2.4; text-align:left;">
            • Les noms propres commencent par :<br>
            &nbsp;&nbsp;&nbsp;&nbsp;- une lettre minuscule<br>
            &nbsp;&nbsp;&nbsp;&nbsp;- <b style="color:#15803D; text-decoration:underline;">une lettre majuscule</b> ✓<br><br>
            • Maman est un nom qui appartient à :<br>
            &nbsp;&nbsp;&nbsp;&nbsp;- <b style="color:#15803D; text-decoration:underline;">tout le monde</b> ✓<br>
            &nbsp;&nbsp;&nbsp;&nbsp;- une seule personne
        </div>

        <p align="left" style="font-weight:bold; color:#0D47A1; margin-top:12px;">2) Entoures les intrus :</p>
        <div style="background:#EFF6FF; border:2px dashed #3B82F6; border-radius:10px; padding:12px; font-size:12pt; text-align:left; line-height:2.2;">
            Paris &nbsp;—&nbsp; <span style="border:2px solid #DC2626; border-radius:8px; padding:2px 6px; color:#DC2626; font-weight:bold;">Marie</span> &nbsp;—&nbsp; Mandroseza &nbsp;—&nbsp; <span style="border:2px solid #DC2626; border-radius:8px; padding:2px 6px; color:#DC2626; font-weight:bold;">Madagascar</span> &nbsp;—&nbsp; Milou &nbsp;—&nbsp; Babi
        </div>
        <div style="background:#EFF6FF; border:2px dashed #3B82F6; border-radius:10px; padding:12px; font-size:12pt; text-align:left; line-height:2.2;">
            Yvon &nbsp;—&nbsp; <span style="border:2px solid #DC2626; border-radius:8px; padding:2px 6px; color:#DC2626; font-weight:bold;">Capeline</span> &nbsp;—&nbsp; Luca &nbsp;—&nbsp; <span style="border:2px solid #DC2626; border-radius:8px; padding:2px 6px; color:#DC2626; font-weight:bold;">Max</span> &nbsp;—&nbsp; Rose &nbsp;—&nbsp; une Tulipe
        </div>

        <p align="left" style="font-weight:bold; color:#0D47A1; margin-top:12px;">3) Donnes 4 noms propres :</p>
        <div style="background:#F0FDF4; border:2px dashed #16A34A; border-radius:10px; padding:10px; font-size:12pt; font-weight:bold; color:#166534; text-align:left;">
            ✦ Bady &nbsp;|&nbsp; ✦ Paris &nbsp;|&nbsp; ✦ Diego &nbsp;|&nbsp; ✦ Tamatave
        </div>
    </body></html>
    """
        return self.creer_page_affichage(html, self.retour_a_exercices_gramm, "← Revenir aux exercices de Grammaire")

    # =========================================================================
    # LEÇONS & EXERCICES DE MATHÉMATIQUES
    # =========================================================================
    def creer_page_math_lecons(self):
        page = QWidget()
        self.style_fond(page)
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(12, 12, 12, 12)

        cadre = QFrame()
        cadre.setStyleSheet("QFrame { background-color: transparent; border: 3px solid #80DEEA; border-radius: 20px; }")
        cadre_layout = QVBoxLayout(cadre)

        self.titre_math_lecons = self.creer_titre("Mathématiques\nChoisissez une leçon")
        cadre_layout.addWidget(self.titre_math_lecons, 1)

        self.groupe_math = QButtonGroup(self)
        self.groupe_math.setExclusive(True)

        self.bouton_arithmetique = self.creer_bouton_rose_3d("Arithmétiques")
        self.bouton_geometrie = self.creer_bouton_rose_3d("Géométrie")
        self.bouton_metrique = self.creer_bouton_rose_3d("Systeme métrique")

        self.boutons_math = [self.bouton_arithmetique, self.bouton_geometrie, self.bouton_metrique]
        for b in self.boutons_math:
            self.groupe_math.addButton(b)
            cadre_layout.addWidget(b, 2)
            b.clicked.connect(lambda checked=False, btn=b: self.selectionner_lecon_math(btn.text()))

        self.bouton_choose_math = self.creer_bouton_choose("Choose")
        self.bouton_choose_math.clicked.connect(self.confirmer_lecon_math)
        cadre_layout.addWidget(self.bouton_choose_math, 1)

        btn_ret = QPushButton("← Revenir")
        btn_ret.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ret.setStyleSheet("QPushButton { background-color: #6C757D; color: white; font-size: 15px; font-weight: bold; border-radius: 12px; padding: 6px; }")
        btn_ret.clicked.connect(self.retour_a_programme)
        cadre_layout.addWidget(btn_ret)

        page_layout.addWidget(cadre)
        return page

    def creer_page_math_exercices(self):
        page = QWidget()
        self.style_fond(page)
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(12, 12, 12, 12)

        cadre = QFrame()
        cadre.setStyleSheet("QFrame { background-color: transparent; border: 3px solid #80DEEA; border-radius: 20px; }")
        cadre_layout = QVBoxLayout(cadre)

        self.titre_math_exercices = self.creer_titre("Exercices de Mathématiques\nChoisissez une option")
        cadre_layout.addWidget(self.titre_math_exercices, 1)

        self.groupe_math_ex = QButtonGroup(self)
        self.groupe_math_ex.setExclusive(True)

        self.bouton_ex_arithmetique = self.creer_bouton_rose_3d("Arithmétiques")
        self.bouton_ex_geometrie = self.creer_bouton_rose_3d("Géométrie")
        self.bouton_ex_metrique = self.creer_bouton_rose_3d("Systeme métrique")

        self.boutons_math_exercices = [self.bouton_ex_arithmetique, self.bouton_ex_geometrie, self.bouton_ex_metrique]
        for b in self.boutons_math_exercices:
            self.groupe_math_ex.addButton(b)
            cadre_layout.addWidget(b, 2)
            b.clicked.connect(lambda checked=False, btn=b: self.selectionner_exercice_math(btn.text()))

        self.bouton_choose_math_ex = self.creer_bouton_choose("Choose")
        self.bouton_choose_math_ex.clicked.connect(self.confirmer_exercice_math)
        cadre_layout.addWidget(self.bouton_choose_math_ex, 1)

        btn_ret = QPushButton("← Revenir")
        btn_ret.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ret.setStyleSheet("QPushButton { background-color: #6C757D; color: white; font-size: 15px; font-weight: bold; border-radius: 12px; padding: 6px; }")
        btn_ret.clicked.connect(self.retour_a_programme)
        cadre_layout.addWidget(btn_ret)

        page_layout.addWidget(cadre)
        return page

    def creer_page_arithmetique(self):
        page = QWidget()
        self.style_fond(page)
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(12, 12, 12, 12)

        cadre = QFrame()
        cadre.setStyleSheet("QFrame { background-color: transparent; border: 3px solid #80DEEA; border-radius: 20px; }")
        cadre_layout = QVBoxLayout(cadre)

        self.titre_arithmetique = self.creer_titre("Arithmétique\nChoisissez une leçon")
        cadre_layout.addWidget(self.titre_arithmetique, 1)

        self.groupe_arithmetique = QButtonGroup(self)
        self.groupe_arithmetique.setExclusive(True)

        self.boutons_arithmetique = [
            self.creer_bouton_rose_3d("Comptage de 1 en 1 de 0 à 10"),
            self.creer_bouton_rose_3d("Comptage de 1 en 1 de 0 à 49"),
            self.creer_bouton_rose_3d("Addition sans retenue"),
            self.creer_bouton_rose_3d("Addition avec retenue"),
            self.creer_bouton_rose_3d("Comptage de 1 en 1 de 80 à 119")
        ]
        for b in self.boutons_arithmetique:
            self.groupe_arithmetique.addButton(b)
            cadre_layout.addWidget(b, 2)
            b.clicked.connect(lambda checked=False, btn=b: self.selectionner_option_arithmetique(btn.text()))

        self.bouton_choose_arith = self.creer_bouton_choose("Choose")
        self.bouton_choose_arith.clicked.connect(self.confirmer_choix_arithmetique)
        cadre_layout.addWidget(self.bouton_choose_arith, 1)

        btn_ret = QPushButton("← Revenir aux leçons de Mathématiques")
        btn_ret.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ret.setStyleSheet("QPushButton { background-color: #6C757D; color: white; font-size: 15px; font-weight: bold; border-radius: 12px; padding: 6px; }")
        btn_ret.clicked.connect(self.retour_a_math_lecons)
        cadre_layout.addWidget(btn_ret)

        page_layout.addWidget(cadre)
        return page

    def creer_page_lecon_comptage_10(self):
        html = """
    <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
        <p><span style="background-color:#4361EE; color:#fff; font-size:14pt; font-weight:bold; padding:6px 14px; border-radius:12px;">📅 Jeudi 17 Septembre 2026</span></p>
        <p style="font-size:15pt; font-weight:800; color:#FF2E93; margin-top:12px;">✨ Comptage de 1 en 1 de 0 à 10 ✨</p>
        <div style="background-color:#E8F5E9; border:2px dashed #4CAF50; border-radius:14px; padding:12px; font-size:13pt; font-weight:bold; color:#2E7D32;">
            0 ➔ 1 ➔ 2 ➔ 3 ➔ 4 ➔ 5 ➔ 6 ➔ 7 ➔ 8 ➔ 9 ➔ 10
        </div>
    </body></html>
    """
        return self.creer_page_affichage(html, self.retour_a_arithmetique, "← Revenir aux leçons d'Arithmétique")

    def creer_page_lecon_comptage_49(self):
        chiffres_49 = " ➔ ".join(str(i) for i in range(50))
        chiffres_79 = " - ".join(str(i) for i in range(50, 80))
        html = f"""
    <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
        <p><span style="background-color:#4361EE; color:#fff; font-size:14pt; font-weight:bold; padding:6px 14px; border-radius:12px;">📅 Lundi 28 Septembre 2026</span></p>
        <p style="font-size:14pt; font-weight:800; color:#FF2E93; margin-top:10px;">✨ Comptage de 1 en 1 de 0 à 49 ✨</p>
        <div style="background-color:#E8F5E9; border:2px dashed #4CAF50; border-radius:12px; padding:10px; line-height:1.8; font-size:11pt; color:#2E7D32;">
            {chiffres_49}
        </div>
        <p style="font-size:13pt; font-weight:800; color:#FF2E93; margin-top:15px;">✍️ Écriture littérale de 0 à 10</p>
        <div style="background:#fff; border-radius:10px; padding:8px; font-size:11pt; font-weight:bold; color:#5D4037;">
            0=zéro | 1=un | 2=deux | 3=trois | 4=quatre | 5=cinq | 6=six | 7=sept | 8=huit | 9=neuf | 10=dix
        </div>

        <div style="margin-top:16px; background:#F0F9FF; border:3px solid #0284C7; border-radius:14px; padding:14px; text-align:center;">
            <p style="margin:0 0 8px 0;">
                <span style="background:#0284C7; color:#ffffff; font-size:12pt; font-weight:bold; padding:4px 12px; border-radius:10px;">
                    📅 Lundi 12 Octobre 2026 — Suite de la leçon
                </span>
            </p>
            <p style="font-size:13pt; font-weight:800; color:#0369A1; margin:6px 0;">✨ Comptage de 1 en 1 de 50 à 79 ✨</p>
            <div style="background:#ffffff; border-radius:10px; padding:10px; font-size:11pt; font-weight:bold; color:#0F172A; line-height:2;">
                {chiffres_79}
            </div>
        </div>
    </body></html>
    """
        return self.creer_page_affichage(html, self.retour_a_arithmetique, "← Revenir aux leçons d'Arithmétique")

    def creer_page_lecon_comptage_119(self):
        chiffres_119 = " - ".join(str(i) for i in range(80, 120))
        html = f"""
    <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
        <p><span style="background-color:#4361EE; color:#fff; font-size:14pt; font-weight:bold; padding:6px 14px; border-radius:12px;">📅 Lundi 26 Octobre 2026</span></p>
        <p style="font-size:16pt; font-weight:800; color:#FF2E93; margin-top:10px;">✨ Comptage de 1 en 1 de 80 à 119 ✨</p>

        <div style="background-color:#FFFFFF; border:3px solid #80DEEA; border-radius:14px; padding:12px; line-height:2.2; font-size:12pt; font-weight:bold; color:#0F172A;">
            {chiffres_119}
        </div>

        <p style="font-size:14pt; font-weight:800; color:#16A34A; margin-top:16px;">📊 Tableau de numération (110) :</p>
        <table border="2" cellpadding="8" cellspacing="0" style="width:65%; margin:auto; border-collapse:collapse; text-align:center; font-size:14pt; font-weight:bold; background:#fff; border-color:#0284C7;">
            <tr style="background:#E0F2FE; color:#0369A1;">
                <td width="33%">c</td>
                <td width="33%">d</td>
                <td width="33%">u</td>
            </tr>
            <tr style="color:#D90429; font-size:16pt;">
                <td>1</td>
                <td>1</td>
                <td>0</td>
            </tr>
        </table>
        <p style="font-size:12pt; font-weight:bold; color:#0369A1; margin-top:8px;">110 = 1 centaine, 1 dizaine, 0 unité</p>
    </body></html>
    """
        return self.creer_page_affichage(html, self.retour_a_arithmetique, "← Revenir aux leçons d'Arithmétique")

    def creer_page_lecon_addition_sans(self):
        html = """
    <html><body style="font-family:'Segoe UI','Comic Sans MS',sans-serif; text-align:center;">
        <p><span style="background-color:#FFE0B2; color:#B71C1C; font-size:14pt; font-weight:bold; padding:6px 14px; border-radius:12px;">Addition Sans Retenue</span></p>
        <p style="color:#0D47A1; font-size:12pt; font-weight:600;">📅 Lundi 05 Octobre 2026</p>
        <div style="background-color:#E8F5E9; border-left:5px solid #2E7D32; padding:10px; border-radius:8px; text-align:left; font-size:11pt;">
            <b>Règle :</b> Le signe de l'addition est le <b style="color:#1B5E20; font-size:14pt;">+</b>
        </div>
        <div style="background-color:#B3E5FC; border-radius:12px; padding:12px; margin-top:10px; font-family:monospace; font-size:14pt; font-weight:bold; color:#1A237E;">
            5 + 3 = 8 &nbsp;&nbsp;|&nbsp;&nbsp; 13 + 5 = 18 &nbsp;&nbsp;|&nbsp;&nbsp; 31 + 16 = 47
        </div>
    </body></html>
    """
        return self.creer_page_affichage(html, self.retour_a_arithmetique, "← Revenir aux leçons d'Arithmétique")

    def creer_page_lecon_addition_avec(self):
        html = """
    <html><body style="font-family:'Segoe UI','Comic Sans MS',sans-serif; text-align:center;">
        <p><span style="background-color:#FFE0B2; color:#B71C1C; font-size:14pt; font-weight:bold; padding:6px 14px; border-radius:12px;">Addition Avec Retenue</span></p>
        <p style="color:#0D47A1; font-size:12pt; font-weight:600;">📅 Mercredi 21 Octobre 2026</p>
        <div style="background-color:#E1BEE7; border-radius:12px; padding:12px; margin-top:10px; font-family:monospace; font-size:14pt; font-weight:bold; color:#4A148C;">
            26 + 37 = 63 &nbsp;&nbsp;|&nbsp;&nbsp; 15 + 26 = 41
        </div>
    </body></html>
    """
        return self.creer_page_affichage(html, self.retour_a_arithmetique, "← Revenir aux leçons d'Arithmétique")

    def creer_page_geometrie(self):
        page = QWidget()
        self.style_fond(page)
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(12, 12, 12, 12)

        cadre = QFrame()
        cadre.setStyleSheet("QFrame { background-color: transparent; border: 3px solid #80DEEA; border-radius: 20px; }")
        cadre_layout = QVBoxLayout(cadre)

        self.titre_geometrie = self.creer_titre("Géométrie\nChoisissez une leçon")
        cadre_layout.addWidget(self.titre_geometrie, 1)

        self.groupe_geometrie = QButtonGroup(self)
        self.groupe_geometrie.setExclusive(True)

        self.boutons_geometrie = [
            self.creer_bouton_rose_3d("Les points"),
            self.creer_bouton_rose_3d("Les lignes")
        ]
        for b in self.boutons_geometrie:
            self.groupe_geometrie.addButton(b)
            cadre_layout.addWidget(b, 2)
            b.clicked.connect(lambda checked=False, btn=b: self.selectionner_option_geometrie(btn.text()))

        self.bouton_choose_geo = self.creer_bouton_choose("Choose")
        self.bouton_choose_geo.clicked.connect(self.confirmer_choix_geometrie)
        cadre_layout.addWidget(self.bouton_choose_geo, 1)

        btn_ret = QPushButton("← Revenir")
        btn_ret.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ret.setStyleSheet("QPushButton { background-color: #6C757D; color: white; font-size: 15px; font-weight: bold; border-radius: 12px; padding: 6px; }")
        btn_ret.clicked.connect(self.retour_a_math_lecons)
        cadre_layout.addWidget(btn_ret)

        page_layout.addWidget(cadre)
        return page

    def creer_page_lecon_point(self):
        html = """
    <html><body style="font-family:'Segoe UI','Comic Sans MS',sans-serif; text-align:center;">
        <p><span style="background-color:#FFE0B2; color:#B71C1C; font-size:14pt; font-weight:bold; padding:6px 14px; border-radius:12px;">Le Point</span></p>
        <p style="color:#0D47A1; font-size:12pt; font-weight:600;">📅 Jeudi 17 Septembre 2026</p>
        <div style="background-color:#E8F5E9; border-left:5px solid #1B5E20; padding:12px; border-radius:8px; text-align:left; font-size:12pt; color:#1B5E20;">
            ✦ Un point est une figure géométrique sans dimension (on ne peut pas mesurer).
        </div>
        <p style="margin-top:25px; font-size:24pt; color:#D81B60;">● Point A</p>
    </body></html>
    """
        return self.creer_page_affichage(html, self.retour_a_geometrie, "← Revenir à la Géométrie")

    def creer_page_lecon_lignes(self):
        elements = [
            {"type": "texte_enonce", "texte": "Il y a 5 sortes de lignes :"},
            {"type": "formes_lignes"}
        ]
        return self.creer_page_cahier_visuel(
            "Jeudi 13 Octobre 2026",
            "📖 Géométrie — Les 5 sortes de lignes",
            elements,
            self.retour_a_geometrie,
            "← Revenir à la Géométrie",
            hauteur_min=460
        )

    def creer_page_metrique(self):
        page = QWidget()
        self.style_fond(page)
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(12, 12, 12, 12)

        cadre = QFrame()
        cadre.setStyleSheet("QFrame { background-color: transparent; border: 3px solid #80DEEA; border-radius: 20px; }")
        cadre_layout = QVBoxLayout(cadre)

        self.titre_metrique = self.creer_titre("Système métrique\nChoisissez une leçon")
        cadre_layout.addWidget(self.titre_metrique, 1)

        self.groupe_metrique = QButtonGroup(self)
        self.groupe_metrique.setExclusive(True)

        self.boutons_metrique = [
            self.creer_bouton_rose_3d("Mesurer avec un règle graduée"),
            self.creer_bouton_rose_3d("Mesurer un segment")
        ]
        for b in self.boutons_metrique:
            self.groupe_metrique.addButton(b)
            cadre_layout.addWidget(b, 2)
            b.clicked.connect(lambda checked=False, btn=b: self.selectionner_option_metrique(btn.text()))

        self.bouton_choose_metrique = self.creer_bouton_choose("Choose")
        self.bouton_choose_metrique.clicked.connect(self.confirmer_choix_metrique)
        cadre_layout.addWidget(self.bouton_choose_metrique, 1)

        btn_ret = QPushButton("← Revenir")
        btn_ret.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ret.setStyleSheet("QPushButton { background-color: #6C757D; color: white; font-size: 15px; font-weight: bold; border-radius: 12px; padding: 6px; }")
        btn_ret.clicked.connect(self.retour_a_math_lecons)
        cadre_layout.addWidget(btn_ret)

        page_layout.addWidget(cadre)
        return page

    def creer_page_lecon_regle(self):
        elements = [
            {"type": "texte_enonce", "texte": "1. Poser le 0 de la règle sur le point de départ."},
            {"type": "texte_enonce", "texte": "2. Marquer la graduation voulue (ex: 4 cm) et relier."},
            {"type": "regle_graduee", "cm": 4}
        ]
        return self.creer_page_cahier_visuel(
            "Mardi 23 Septembre 2026",
            "📏 Système métrique — Mesurer avec une règle graduée",
            elements,
            self.retour_a_metrique,
            "← Revenir au Système métrique",
            hauteur_min=380
        )

    def creer_page_lecon_segment(self):
        elements = [
            {"type": "texte_enonce", "texte": "✦ Le segment est une ligne limitée qui a un début et une fin :"},
            {"type": "geometrie", "genre": "segment", "orientation": "horizontale", "cm": 6, "p1": "A", "p2": "B", "mesure": "Segment [AB]"},
            {"type": "texte_enonce", "texte": "✦ La demi-droite est limitée d'un seul côté par son origine :"},
            {"type": "geometrie", "genre": "demi_droite", "orientation": "horizontale", "cm": 6, "p1": "A", "p2": "", "mesure": "Demi-droite [Ax)"},
            {"type": "texte_enonce", "texte": "✦ La droite n'a pas de limites :"},
            {"type": "geometrie", "genre": "droite", "orientation": "horizontale", "cm": 6, "p1": "", "p2": "", "mesure": "Droite (d)"}
        ]
        return self.creer_page_cahier_visuel(
            "Jeudi 08 Octobre 2026",
            "📖 Système métrique — Mesurer un segment",
            elements,
            self.retour_a_metrique,
            "← Revenir au Système métrique",
            hauteur_min=450
        )

    def creer_page_exercices_arithmetique(self):
        page = QWidget()
        self.style_fond(page)
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(12, 12, 12, 12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        conteneur = QWidget()
        cadre_layout = QVBoxLayout(conteneur)

        self.titre_exercices_arith = self.creer_titre("Exercices d'Arithmétique\nChoisissez un exercice")
        cadre_layout.addWidget(self.titre_exercices_arith)

        self.groupe_exercices_arith = QButtonGroup(self)
        self.groupe_exercices_arith.setExclusive(True)

        self.boutons_exercices_arith = [
            self.creer_bouton_rose_3d("1-Compte de 1 en 1 de 0 à 10."),
            self.creer_bouton_rose_3d("1-Compte de 1 en 1 de 30 à 49."),
            self.creer_bouton_rose_3d("1-Ecris en lettres."),
            self.creer_bouton_rose_3d("1-Compte de 1 en 1 de 55 à 75."),
            self.creer_bouton_rose_3d("1-Pose et effectue."),
            self.creer_bouton_rose_3d("1-Ecris")
        ]
        for b in self.boutons_exercices_arith:
            self.groupe_exercices_arith.addButton(b)
            cadre_layout.addWidget(b)
            b.clicked.connect(lambda checked=False, btn=b: self.selectionner_exercice_arithmetique(btn.text()))

        self.bouton_choose_ex_arith = self.creer_bouton_choose("Choose")
        self.bouton_choose_ex_arith.clicked.connect(self.confirmer_choix_exercice_arithmetique)
        cadre_layout.addWidget(self.bouton_choose_ex_arith)

        btn_ret = QPushButton("← Revenir")
        btn_ret.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ret.setStyleSheet("QPushButton { background-color: #6C757D; color: white; font-size: 15px; font-weight: bold; border-radius: 12px; padding: 6px; }")
        btn_ret.clicked.connect(self.retour_a_math_exercices)
        cadre_layout.addWidget(btn_ret)

        scroll.setWidget(conteneur)
        page_layout.addWidget(scroll)
        return page

    def creer_page_ex_comptage_10(self):
        html = """
    <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
        <p><span style="background:#4361EE; color:#fff; font-size:14pt; font-weight:bold; padding:6px 16px; border-radius:12px;">📅 Lundi 21 Septembre 2026</span></p>
        <p style="font-size:15pt; font-weight:800; color:#FF2E93;">✏️ Arithmétiques — Exercices</p>
        <p align="left" style="font-weight:bold; color:#0D47A1;">1) Compte de 1 en 1 de 0 à 10 :</p>
        <div style="background:#fff; border:2px solid #80DEEA; border-radius:10px; padding:8px;">0 - 1 - 2 - 3 - 4 - 5 - 6 - 7 - 8 - 9 - 10</div>
        <p align="left" style="font-weight:bold; color:#0D47A1;">2) Complète les pointillés :</p>
        <div style="background:#fff; border:2px solid #80DEEA; border-radius:10px; padding:8px;">2 - 3 - 4 - 5 - 6 - 7 - <b style="color:red;">. . .</b> - 9 - 10</div>
        <p align="left" style="font-weight:bold; color:#0D47A1;">3) Dictée :</p>
        <div style="background:#fff; border:2px solid #80DEEA; border-radius:10px; padding:8px; color:#D81B60; font-weight:bold;">9 - 2 - 10 - 3 - 8</div>
    </body></html>
    """
        return self.creer_page_affichage(html, self.retour_a_exercices_arith, "← Revenir aux exercices d'Arithmétique")

    def creer_page_ex_comptage_49(self):
        html = """
    <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
        <p><span style="background:#4361EE; color:#fff; font-size:14pt; font-weight:bold; padding:6px 16px; border-radius:12px;">📅 Mardi 29 Septembre 2026</span></p>
        <p style="font-size:15pt; font-weight:800; color:#FF2E93;">✏️ Arithmétique — Exercices</p>
        <p align="left" style="font-weight:bold; color:#0D47A1;">1) Compte de 1 en 1 de 30 à 49 :</p>
        <div style="background:#fff; border:2px solid #80DEEA; border-radius:10px; padding:8px; line-height:1.7;">
            30 - 31 - 32 - 33 - 34 - 35 - 36 - 37 - 38<br>39 - 40 - 41 - 42 - 43 - 44 - 45 - 46 - 47<br>48 - 49
        </div>
        <p align="left" style="font-weight:bold; color:#0D47A1;">2) Écrire en lettre :</p>
        <div style="background:#fff; border:2px solid #80DEEA; border-radius:10px; padding:8px; text-align:left;">
            1 = un &nbsp;&nbsp;|&nbsp;&nbsp; 5 = cinq<br>0 = zéro &nbsp;|&nbsp;&nbsp; 2 = deux
        </div>
        <p align="left" style="font-weight:bold; color:#0D47A1;">3) Dictée :</p>
        <div style="background:#fff; border:2px solid #80DEEA; border-radius:10px; padding:8px; color:#D81B60; font-weight:bold;">42 - 18 - 30 - 5 - 44 - 25 - 3</div>
    </body></html>
    """
        return self.creer_page_affichage(html, self.retour_a_exercices_arith, "← Revenir aux exercices d'Arithmétique")

    def creer_page_ex_ecris_lettres(self):
        html = """
    <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
        <p style="font-size:15pt; font-weight:800; color:#FF2E93;">✏️ Arithmétique — Écris en lettres</p>
        <p align="left" style="font-weight:bold; color:#0D47A1;">1) Écris en lettres :</p>
        <div style="background:#fff; border:2px solid #80DEEA; border-radius:10px; padding:8px; text-align:left;">
            10 = dix &nbsp;&nbsp;|&nbsp;&nbsp; 8 = huit<br>2 = deux &nbsp;|&nbsp;&nbsp; 6 = six<br>5 = cinq
        </div>
        <p align="left" style="font-weight:bold; color:#0D47A1;">2) Pose et effectue :</p>
        <div style="background:#E1F5FE; border-radius:10px; padding:8px; font-family:monospace; font-size:13pt; font-weight:bold;">
            7 + 2 = 9 &nbsp;&nbsp;|&nbsp;&nbsp; 23 + 15 = 38<br>11 + 8 = 19 &nbsp;|&nbsp;&nbsp; 34 + 14 = 48
        </div>
    </body></html>
    """
        return self.creer_page_affichage(html, self.retour_a_exercices_arith, "← Revenir aux exercices d'Arithmétique")

    def creer_page_ex_comptage_75(self):
        html = """
    <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
        <p><span style="background:#4361EE; color:#fff; font-size:14pt; font-weight:bold; padding:6px 16px; border-radius:12px;">📅 Lundi 12 Octobre 2026</span></p>
        <p style="font-size:15pt; font-weight:800; color:#FF2E93;">✏️ Arithmétique — Exercices</p>
        <p align="left" style="font-weight:bold; color:#0D47A1;">1) Compte de 1 en 1 de 55 à 75 :</p>
        <div style="background:#fff; border:2px solid #80DEEA; border-radius:10px; padding:8px; line-height:1.7;">
            55 - 56 - 57 - 58 - 59 - 60 - 61 - 62 - 63 - 64<br>65 - 66 - 67 - 68 - 69 - 70 - 71 - 72 - 73 - 74 - 75
        </div>
        <p align="left" style="font-weight:bold; color:#0D47A1;">2) Décompose :</p>
        <div style="background:#fff; border:2px solid #80DEEA; border-radius:10px; padding:8px; text-align:left; color:#B71C1C; font-weight:bold;">
            24 = 2 d 4 u &nbsp;&nbsp;|&nbsp;&nbsp; 67 = 6 d 7 u<br>3 = 3 u &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp; 15 = 1 d 5 u
        </div>
        <p align="left" style="font-weight:bold; color:#0D47A1;">3) Pose et effectue :</p>
        <div style="background:#E1F5FE; border-radius:10px; padding:8px; font-family:monospace; font-size:13pt; font-weight:bold;">
            46 + 23 = 69 &nbsp;|&nbsp; 23 + 2 = 25<br>50 + 49 = 99 &nbsp;|&nbsp; 18 + 21 = 39
        </div>
    </body></html>
    """
        return self.creer_page_affichage(html, self.retour_a_exercices_arith, "← Revenir aux exercices d'Arithmétique")

    def creer_page_ex_pose_effectue(self):
        html = """
    <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
        <p><span style="background:#4361EE; color:#fff; font-size:14pt; font-weight:bold; padding:6px 16px; border-radius:12px;">📅 Mercredi 21 Octobre 2026</span></p>
        <p style="font-size:15pt; font-weight:800; color:#FF2E93;">✏️ Arithmétique — Pose et Effectue (Avec retenue)</p>
        <div style="background:#E1F5FE; border-radius:10px; padding:8px; font-family:monospace; font-size:13pt; font-weight:bold;">
            54 + 16 = 70 &nbsp;|&nbsp; 28 + 35 = 63<br>46 + 26 = 72 &nbsp;|&nbsp; 12 + 5 = 17<br>36 + 28 = 64 &nbsp;|&nbsp; 33 + 15 = 48
        </div>
        <p align="left" style="font-weight:bold; color:#0D47A1;">2) Décompose :</p>
        <div style="background:#fff; border:2px solid #80DEEA; border-radius:10px; padding:8px; text-align:left; color:#B71C1C; font-weight:bold;">
            57 = 5 d 7 u &nbsp;&nbsp;|&nbsp;&nbsp; 8 = 8 u &nbsp;&nbsp;|&nbsp;&nbsp; 62 = 6 d 2 u
        </div>
    </body></html>
    """
        return self.creer_page_affichage(html, self.retour_a_exercices_arith, "← Revenir aux exercices d'Arithmétique")

    def creer_page_ex_arith_ecris(self):
        html = """
    <html><body style="font-family:'Comic Sans MS',sans-serif; text-align:center;">
        <p><span style="background:#4361EE; color:#fff; font-size:14pt; font-weight:bold; padding:6px 16px; border-radius:12px;">📅 Lundi 26 Octobre 2026</span></p>
        <p style="font-size:16pt; font-weight:800; color:#FF2E93;">✏️ Arithmétique — Écris & Décompose</p>

        <p align="left" style="font-weight:bold; color:#0D47A1; margin-top:10px;">1) Écris en lettres :</p>
        <div style="background:#fff; border:2px solid #80DEEA; border-radius:10px; padding:10px; font-size:12pt; font-weight:bold; line-height:2.2; text-align:left;">
            ✦ <b>6</b> = six<br>
            ✦ <b>8</b> = huit<br>
            ✦ <b>0</b> = zéro<br>
            ✦ <b>10</b> = dix
        </div>

        <p align="left" style="font-weight:bold; color:#0D47A1; margin-top:12px;">2) Compte de 1 en 1 de 87 à 107 :</p>
        <div style="background:#F0F9FF; border:2px dashed #0284C7; border-radius:10px; padding:10px; font-size:11pt; font-weight:bold; color:#0369A1; line-height:2;">
            87 - 88 - 89 - 90 - 91 - 92 - 93 - 94 - 95 - 96 - 97 - 98 - 99 - 100 - 101 - 102 - 103 - 104 - 105 - 106 - 107.
        </div>

        <p align="left" style="font-weight:bold; color:#0D47A1; margin-top:12px;">3) Décompose :</p>
        <div style="background:#fff; border:2px solid #80DEEA; border-radius:10px; padding:10px; font-size:12pt; font-weight:bold; line-height:2.2; text-align:left;">
            ✦ 85 = <b style="color:#D81B60;">8 d 5 u</b><br>
            ✦ 92 = <b style="color:#D81B60;">9 d 2 u</b><br>
            ✦ 5 &nbsp;= <b style="color:#D81B60;">5 u</b><br>
            ✦ 113 = <b style="color:#D81B60;">1 c 1 d 3 u</b><br>
            ✦ 7 &nbsp;= <b style="color:#D81B60;">7 u</b><br>
            ✦ 119 = <b style="color:#D81B60;">1 c 1 d 9 u</b>
        </div>
    </body></html>
    """
        return self.creer_page_affichage(html, self.retour_a_exercices_arith, "← Revenir aux exercices d'Arithmétique")

    # =========================================================================
    # GÉOMÉTRIE & SYSTÈME MÉTRIQUE
    # =========================================================================
    def creer_page_exercices_geometrie(self):
        page = QWidget()
        self.style_fond(page)
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(12, 12, 12, 12)

        cadre = QFrame()
        cadre.setStyleSheet("QFrame { background-color: transparent; border: 3px solid #80DEEA; border-radius: 20px; }")
        cadre_layout = QVBoxLayout(cadre)

        self.titre_exercices_geo = self.creer_titre("Exercices de Géométrie\nChoisissez un exercice")
        cadre_layout.addWidget(self.titre_exercices_geo)

        self.groupe_exercices_geo = QButtonGroup(self)
        self.groupe_exercices_geo.setExclusive(True)

        self.boutons_exercices_geo = [
            self.creer_bouton_rose_3d("1-Trace une ligne droite horizontale de 6cm."),
            self.creer_bouton_rose_3d("1-Souligne la bonne réponse.")
        ]
        for b in self.boutons_exercices_geo:
            self.groupe_exercices_geo.addButton(b)
            cadre_layout.addWidget(b)
            b.clicked.connect(lambda checked=False, btn=b: self.selectionner_exercice_geo(btn.text()))

        self.bouton_choose_ex_geo = self.creer_bouton_choose("Choose")
        self.bouton_choose_ex_geo.clicked.connect(self.confirmer_choix_exercice_geo)
        cadre_layout.addWidget(self.bouton_choose_ex_geo)

        btn_ret = QPushButton("← Revenir")
        btn_ret.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ret.setStyleSheet("QPushButton { background-color: #6C757D; color: white; font-size: 15px; font-weight: bold; border-radius: 12px; padding: 6px; }")
        btn_ret.clicked.connect(self.retour_a_math_exercices)
        cadre_layout.addWidget(btn_ret)

        page_layout.addWidget(cadre)
        return page

    def creer_page_ex_geo_ligne_6cm(self):
        elements = [
            {
                "type": "geometrie",
                "titre": "1) Trace une ligne droite horizontale de 6 cm :",
                "genre": "droite",
                "orientation": "horizontale",
                "cm": 6,
                "mesure": "6 cm",
                "couleur": "#1E3A8A"
            },
            {
                "type": "geometrie",
                "titre": "2) Trace une ligne droite verticale de 4 cm :",
                "genre": "droite",
                "orientation": "verticale",
                "cm": 4,
                "mesure": "4 cm",
                "couleur": "#1E3A8A"
            }
        ]
        return self.creer_page_cahier_visuel(
            "",
            "✏️ Géométrie — Lignes de 6 cm et 4 cm",
            elements,
            self.retour_a_exercices_geo,
            "← Revenir aux exercices de Géométrie",
            hauteur_min=420
        )

    def creer_page_ex_geo_souligne(self):
        elements = [
            {"type": "texte_enonce", "texte": "1) Souligne la bonne réponse :"},
            {
                "type": "souligne_reponse",
                "options": ["2 sortes de lignes", "6 sortes de lignes", "5 sortes de lignes"],
                "bonne": 2
            },
            {
                "type": "geometrie",
                "titre": "2) Trace une ligne droite horizontale :",
                "genre": "droite",
                "orientation": "horizontale",
                "cm": 6,
                "mesure": "Ligne horizontale",
                "couleur": "#0284C7"
            },
            {
                "type": "geometrie",
                "titre": "3) Trace une ligne droite oblique :",
                "genre": "droite",
                "orientation": "oblique",
                "cm": 5,
                "mesure": "Ligne oblique",
                "couleur": "#0284C7"
            },
            {
                "type": "geometrie",
                "titre": "4) Trace une ligne verticale :",
                "genre": "droite",
                "orientation": "verticale",
                "cm": 4,
                "mesure": "Ligne verticale",
                "couleur": "#0284C7"
            }
        ]
        return self.creer_page_cahier_visuel(
            "Mercredi 14 Octobre 2026",
            "✏️ Géométrie — Souligne la bonne réponse & Tracés",
            elements,
            self.retour_a_exercices_geo,
            "← Revenir aux exercices de Géométrie",
            hauteur_min=560
        )

    def creer_page_exercices_metrique(self):
        page = QWidget()
        self.style_fond(page)
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(12, 12, 12, 12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        conteneur = QWidget()
        cadre_layout = QVBoxLayout(conteneur)

        self.titre_exercices_metrique = self.creer_titre("Exercices Système Métrique\nChoisissez un exercice")
        cadre_layout.addWidget(self.titre_exercices_metrique)

        self.groupe_exercices_metrique = QButtonGroup(self)
        self.groupe_exercices_metrique.setExclusive(True)

        self.boutons_exercices_metrique = [
            self.creer_bouton_rose_3d("1-Trace une ligne horizontale."),
            self.creer_bouton_rose_3d("1-Trace une ligne horizontale de 7cm."),
            self.creer_bouton_rose_3d("1-Trace le segment [AB]."),
            self.creer_bouton_rose_3d("1-Trace un demi droite."),
            self.creer_bouton_rose_3d("1-Trace [IJ] = 4cm."),
            self.creer_bouton_rose_3d("1-Trace un segment [AB] de 6 cm.")
        ]
        for b in self.boutons_exercices_metrique:
            self.groupe_exercices_metrique.addButton(b)
            cadre_layout.addWidget(b)
            b.clicked.connect(lambda checked=False, btn=b: self.selectionner_exercice_metrique(btn.text()))

        self.bouton_choose_ex_metrique = self.creer_bouton_choose("Choose")
        self.bouton_choose_ex_metrique.clicked.connect(self.confirmer_choix_exercice_metrique)
        cadre_layout.addWidget(self.bouton_choose_ex_metrique)

        btn_ret = QPushButton("← Revenir")
        btn_ret.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ret.setStyleSheet("QPushButton { background-color: #6C757D; color: white; font-size: 15px; font-weight: bold; border-radius: 12px; padding: 6px; }")
        btn_ret.clicked.connect(self.retour_a_math_exercices)
        cadre_layout.addWidget(btn_ret)

        scroll.setWidget(conteneur)
        page_layout.addWidget(scroll)
        return page

    def creer_page_ex_met_ligne_horiz(self):
        elements = [
            {
                "type": "geometrie",
                "titre": "1) Ligne horizontale de 5 cm :",
                "genre": "droite",
                "orientation": "horizontale",
                "cm": 5,
                "mesure": "5 cm",
                "couleur": "#1E3A8A"
            },
            {
                "type": "geometrie",
                "titre": "2) Ligne verticale de 8 cm :",
                "genre": "droite",
                "orientation": "verticale",
                "cm": 8,
                "mesure": "8 cm",
                "couleur": "#1E3A8A"
            },
            {
                "type": "geometrie",
                "titre": "3) Ligne oblique de 3 cm :",
                "genre": "droite",
                "orientation": "oblique",
                "cm": 3,
                "mesure": "3 cm",
                "couleur": "#1E3A8A"
            }
        ]
        return self.creer_page_cahier_visuel(
            "Mardi 22 Septembre 2026",
            "✏️ Système Métrique — Ligne horizontale 5 cm, verticale 8 cm, oblique 3 cm",
            elements,
            self.retour_a_exercices_metrique,
            "← Revenir aux exercices de Système Métrique",
            hauteur_min=580
        )

    def creer_page_ex_met_ligne_7cm(self):
        elements = [
            {
                "type": "geometrie",
                "titre": "1) Ligne horizontale de 7 cm :",
                "genre": "droite",
                "orientation": "horizontale",
                "cm": 7,
                "mesure": "7 cm",
                "couleur": "#0F172A"
            },
            {
                "type": "geometrie",
                "titre": "2) Ligne verticale de 4 cm :",
                "genre": "droite",
                "orientation": "verticale",
                "cm": 4,
                "mesure": "4 cm",
                "couleur": "#0F172A"
            },
            {
                "type": "geometrie",
                "titre": "3) Ligne oblique de 5 cm :",
                "genre": "droite",
                "orientation": "oblique",
                "cm": 5,
                "mesure": "5 cm",
                "couleur": "#0F172A"
            }
        ]
        return self.creer_page_cahier_visuel(
            "Lundi 29 Septembre 2026",
            "✏️ Système Métrique — Ligne horizontale 7 cm, verticale 4 cm, oblique 5 cm",
            elements,
            self.retour_a_exercices_metrique,
            "← Revenir aux exercices de Système Métrique",
            hauteur_min=540
        )

    def creer_page_ex_met_segment_ab(self):
        elements = [
            {"type": "texte_enonce", "texte": "1) Trace les segments en ligne horizontale :"},
            {
                "type": "geometrie",
                "genre": "segment",
                "orientation": "horizontale",
                "cm": 5,
                "p1": "A",
                "p2": "B",
                "mesure": "[AB] = 5 cm",
                "couleur": "#1E3A8A"
            },
            {
                "type": "geometrie",
                "genre": "segment",
                "orientation": "horizontale",
                "cm": 7,
                "p1": "D",
                "p2": "E",
                "mesure": "[DE] = 7 cm",
                "couleur": "#1E3A8A"
            },
            {
                "type": "geometrie",
                "genre": "segment",
                "orientation": "horizontale",
                "cm": 3,
                "p1": "A",
                "p2": "C",
                "mesure": "[AC] = 3 cm",
                "couleur": "#1E3A8A"
            },
            {
                "type": "geometrie",
                "genre": "segment",
                "orientation": "horizontale",
                "cm": 8,
                "p1": "F",
                "p2": "H",
                "mesure": "[FH] = 8 cm",
                "couleur": "#1E3A8A"
            }
        ]
        return self.creer_page_cahier_visuel(
            "Jeudi 08 Octobre 2026",
            "✏️ Système Métrique — Trace les segments [AB], [DE], [AC], [FH]",
            elements,
            self.retour_a_exercices_metrique,
            "← Revenir aux exercices de Système Métrique",
            hauteur_min=460
        )

    def creer_page_ex_met_demi_droite(self):
        elements = [
            {
                "type": "geometrie",
                "titre": "1) Trace la demi-droite [CD[ = 3 cm en ligne horizontale :",
                "genre": "demi_droite",
                "orientation": "horizontale",
                "cm": 3,
                "p1": "C",
                "p2": "D",
                "mesure": "3 cm",
                "couleur": "#1E3A8A"
            },
            {
                "type": "geometrie",
                "titre": "2) Trace [HD] = 6 cm en ligne verticale :",
                "genre": "segment",
                "orientation": "verticale",
                "cm": 6,
                "p1": "H",
                "p2": "D",
                "mesure": "6 cm",
                "couleur": "#1E3A8A"
            },
            {
                "type": "geometrie",
                "titre": "3) Trace [EF] en ligne oblique de 4 cm :",
                "genre": "segment",
                "orientation": "oblique",
                "cm": 4,
                "p1": "E",
                "p2": "F",
                "mesure": "4 cm",
                "couleur": "#1E3A8A"
            }
        ]
        return self.creer_page_cahier_visuel(
            "Mardi 13 Octobre 2026",
            "✏️ Système Métrique — Tracé de Segments et Demi-droites",
            elements,
            self.retour_a_exercices_metrique,
            "← Revenir aux exercices de Système Métrique",
            hauteur_min=530
        )

    def creer_page_ex_met_ij_4cm(self):
        elements = [
            {
                "type": "geometrie",
                "titre": "1) Trace [IJ] = 4 cm en ligne verticale :",
                "genre": "segment",
                "orientation": "verticale",
                "cm": 4,
                "p1": "I",
                "p2": "J",
                "mesure": "4 cm",
                "couleur": "#1E3A8A"
            },
            {
                "type": "geometrie",
                "titre": "2) Trace [AC] = 7 cm en ligne oblique :",
                "genre": "segment",
                "orientation": "oblique",
                "cm": 7,
                "p1": "A",
                "p2": "C",
                "mesure": "7 cm",
                "couleur": "#1E3A8A"
            },
            {
                "type": "geometrie",
                "titre": "3) Trace [EP] = 5 cm en ligne horizontale :",
                "genre": "segment",
                "orientation": "horizontale",
                "cm": 5,
                "p1": "E",
                "p2": "P",
                "mesure": "5 cm",
                "couleur": "#1E3A8A"
            }
        ]
        return self.creer_page_cahier_visuel(
            "Vendredi 16 Octobre 2026",
            "✏️ Système Métrique — Segments [IJ] = 4cm, [AC] = 7cm, [EP] = 5cm",
            elements,
            self.retour_a_exercices_metrique,
            "← Revenir aux exercices de Système Métrique",
            hauteur_min=540
        )

    def creer_page_ex_met_segment_ab_6cm(self):
        elements = [
            {
                "type": "geometrie",
                "titre": "1) Trace un segment [AB] = 6 cm en ligne oblique :",
                "genre": "segment",
                "orientation": "oblique",
                "cm": 6,
                "p1": "B",
                "p2": "A",
                "mesure": "6 cm",
                "couleur": "#1E3A8A"
            },
            {
                "type": "geometrie",
                "titre": "2) Traces une demi-droite [BC) = 4 cm en ligne verticale :",
                "genre": "demi_droite",
                "orientation": "verticale",
                "cm": 4,
                "p1": "B",
                "p2": "C",
                "mesure": "4 cm",
                "couleur": "#1E3A8A"
            },
            {
                "type": "geometrie",
                "titre": "3) Traces un segment [CD] = 7 cm en ligne horizontale :",
                "genre": "segment",
                "orientation": "horizontale",
                "cm": 7,
                "p1": "C",
                "p2": "D",
                "mesure": "7 cm",
                "couleur": "#1E3A8A"
            }
        ]
        return self.creer_page_cahier_visuel(
            "Jeudi 29 Octobre 2026",
            "✏️ Système Métrique — Segments et demi-droite ([AB]=6cm, [BC)=4cm, [CD]=7cm)",
            elements,
            self.retour_a_exercices_metrique,
            "← Revenir aux exercices de Système Métrique",
            hauteur_min=580
        )

    # =========================================================================
    # NAVIGATION & SLOTS
    # =========================================================================
    def selectionner_matiere(self, nom):
        self.matiere_choisie = nom
        self.titre_choix.setText(f"Programme en 11 eme\n{nom}")

    def confirmer_matiere(self):
        if not self.matiere_choisie or self.matiere_choisie not in ("Francais", "Mathematiques", "Cours", "Dessin", "Methode boscher", "Lecons de chose"):
            QMessageBox.information(self, "Choisir", "Disponible pour Français, Mathématiques, Cours, Dessin, Méthode boscher et Leçons de chose.")
            return

        self.label_matiere_chargement.setText(self.matiere_choisie)
        self.label_chargement.setText("Chargement en cours...")
        self.label_gif.clear()
        self.arreter_gif()

        noms_gif = ("loading.gif", "Loading.gif", "Loading(1).gif", "loading(1).gif")
        chemin_gif = next((dossier_application() / nom for nom in noms_gif if (dossier_application() / nom).is_file()), None)

        if chemin_gif is not None:
            movie = QMovie(str(chemin_gif))
            if movie.isValid():
                movie.setCacheMode(QMovie.CacheMode.CacheAll)
                movie.setScaledSize(QSize(150, 150))
                self.movie = movie
                self.label_gif.setMovie(movie)
                movie.start()
        self.pages.setCurrentWidget(self.page_chargement)
        QTimer.singleShot(1500, self.ouvrir_interface_suivante)

    def arreter_gif(self):
        if self.movie is not None:
            self.movie.stop()
            self.movie = None

    def ouvrir_interface_suivante(self):
        self.arreter_gif()
        if self.matiere_choisie == "Dessin":
            self.pages.setCurrentWidget(self.page_dessin)
        elif self.matiere_choisie == "Cours":
            self.pages.setCurrentWidget(self.page_cours)
        elif self.matiere_choisie == "Methode boscher":
            self.pages.setCurrentWidget(self.page_methode_boscher)
        elif self.matiere_choisie == "Lecons de chose":
            self.pages.setCurrentWidget(self.page_lecons_de_chose)
        else:
            self.titre_programme.setText(f"{self.matiere_choisie}\nLecons ou Exercices")
            self.texte_programme.setText(f"Matière choisie : {self.matiere_choisie}\nSélectionnez Lecons ou Exercices.")
            self.pages.setCurrentWidget(self.page_programme)

    def ouvrir_contenu(self, type_contenu):
        if self.matiere_choisie == "Mathematiques":
            if type_contenu == "Lecons":
                self.pages.setCurrentWidget(self.page_math_lecons)
            elif type_contenu == "Exercices":
                self.pages.setCurrentWidget(self.page_math_exercices)
        elif self.matiere_choisie == "Francais":
            if type_contenu == "Lecons":
                self.pages.setCurrentWidget(self.page_fr_lecons)
            elif type_contenu == "Exercices":
                self.pages.setCurrentWidget(self.page_fr_exercices)

    # --- Leçons de chose Choix ---
    def selectionner_chose(self, nom):
        self.option_chose_choisie = nom
        self.titre_lecons_de_chose.setText(f"Leçons de chose\n{nom}")

    def confirmer_choix_chose(self):
        if not self.option_chose_choisie:
            return
        m = {
            "LES ANIMAUX QUI NAGENT.": self.page_chose_nagent,
            "LES ANIMAUX QUI VOLENT.": self.page_chose_volent,
            "LES ANIMAUX QUI  MARCHENT.": self.page_chose_marchent,
            "LES ANIMAUX QUI RAMPENT.": self.page_chose_rampent
            
            
            
            
            }
        if self.option_chose_choisie in m:
            self.pages.setCurrentWidget(m[self.option_chose_choisie])

    def retour_a_lecons_de_chose(self):
        self.pages.setCurrentWidget(self.page_lecons_de_chose)

    # --- Méthode Boscher Choix ---
    def selectionner_boscher(self, nom):
        self.option_boscher_choisie = nom
        self.titre_boscher.setText(f"Méthode Boscher\n{nom}")

    def confirmer_choix_boscher(self):
        if not self.option_boscher_choisie:
            return
        mapping = {
            "i - u": self.page_boscher_iu,
            "o - a": self.page_boscher_oa,
            "e": self.page_boscher_e,
            "p": self.page_boscher_p,
            "t": self.page_boscher_t,
            "r": self.page_boscher_r,
            "n": self.page_boscher_n,
            "m": self.page_boscher_m,
            "l": self.page_boscher_l,
            "c": self.page_boscher_c,
            "d": self.page_boscher_d,
            "v": self.page_boscher_v,
            "s": self.page_boscher_s,
            "b": self.page_boscher_b,
            "f": self.page_boscher_f,
            "j": self.page_boscher_j,
            "g": self.page_boscher_g,
            "ch": self.page_boscher_ch,
            "ou": self.page_boscher_ou,
            "on": self.page_boscher_on,
            "oi": self.page_boscher_oi,
            "an": self.page_boscher_an,
            "in": self.page_boscher_in,
            "br": self.page_boscher_br,
            "fr": self.page_boscher_fr,
            "bl": self.page_boscher_bl,
            "cl": self.page_boscher_cl,
            "ar": self.page_boscher_ar,
            "al": self.page_boscher_al,
            "en": self.page_boscher_en
        }
        if self.option_boscher_choisie in mapping:
            self.pages.setCurrentWidget(mapping[self.option_boscher_choisie])

    def retour_a_methode_boscher(self):
        self.pages.setCurrentWidget(self.page_methode_boscher)

    # --- Cours Choix ---
    def selectionner_cours(self, nom):
        self.option_cours_choisie = nom
        self.titre_cours.setText(f"Cours\n{nom}")

    def confirmer_choix_cours(self):
        if not self.option_cours_choisie:
            return
        if self.option_cours_choisie == "1-Pose et effectue":
            self.pages.setCurrentWidget(self.page_cours_pose_effectue)
        elif self.option_cours_choisie == "1-Décompose":
            self.pages.setCurrentWidget(self.page_cours_decompose)

    def retour_a_cours(self):
        self.pages.setCurrentWidget(self.page_cours)

    # --- Français Leçons Choix ---
    def selectionner_lecon_fr(self, nom):
        self.lecon_fr_choisie = nom
        self.titre_fr_lecons.setText(f"Français — Leçons\n{nom}")

    def confirmer_lecon_fr(self):
        if not self.lecon_fr_choisie:
            return
        if self.lecon_fr_choisie == "Orthographe":
            self.pages.setCurrentWidget(self.page_lecons_orthographe)
        elif self.lecon_fr_choisie == "Conjugaison":
            self.pages.setCurrentWidget(self.page_lecons_conjugaison)
        elif self.lecon_fr_choisie == "Grammaire":
            self.pages.setCurrentWidget(self.page_lecons_grammaire)
        elif self.lecon_fr_choisie == "Vocabulaire":
            self.pages.setCurrentWidget(self.page_lecons_vocabulaire)

    def selectionner_option_lecon_ortho(self, nom): self.option_lecon_ortho_choisie = nom
    def confirmer_choix_lecon_ortho(self):
        if self.option_lecon_ortho_choisie == 'Le son "i".':
            self.pages.setCurrentWidget(self.page_lecon_ortho_son_i)
        elif self.option_lecon_ortho_choisie == 'Le son "e".':
            self.pages.setCurrentWidget(self.page_lecon_ortho_son_e)
        elif self.option_lecon_ortho_choisie == "Le son ar":
            self.pages.setCurrentWidget(self.page_lecon_ortho_son_ar)

    def selectionner_option_lecon_conj(self, nom): self.option_lecon_conj_choisie = nom
    def confirmer_choix_lecon_conj(self):
        if self.option_lecon_conj_choisie == "Les pronoms personnels sujets au singuliers":
            self.pages.setCurrentWidget(self.page_lecon_conj_singulier)
        elif self.option_lecon_conj_choisie == "Les PPS aux pluriels":
            self.pages.setCurrentWidget(self.page_lecon_conj_pluriel)

    def selectionner_option_lecon_gramm(self, nom): self.option_lecon_gramm_choisie = nom
    def confirmer_choix_lecon_gramm(self):
        if self.option_lecon_gramm_choisie == "Les 26 lettres de l'alphabet francais":
            self.pages.setCurrentWidget(self.page_lecon_gramm_26_lettres)
        elif self.option_lecon_gramm_choisie == "Les syllabes":
            self.pages.setCurrentWidget(self.page_lecon_gramm_syllabes)
        elif self.option_lecon_gramm_choisie == "les noms":
            self.pages.setCurrentWidget(self.page_lecon_gramm_noms)

    def selectionner_option_lecon_vocab(self, nom): self.option_lecon_vocab_choisie = nom
    def confirmer_choix_lecon_vocab(self):
        if self.option_lecon_vocab_choisie == "La propreté du corps":
            self.pages.setCurrentWidget(self.page_lecon_vocab_corps)
        elif self.option_lecon_vocab_choisie == "La propreté de l'environnement":
            self.pages.setCurrentWidget(self.page_lecon_vocab_environnement)
        elif self.option_lecon_vocab_choisie == "L'école":
            self.pages.setCurrentWidget(self.page_lecon_vocab_ecole)

    # --- Français Exercices Choix ---
    def selectionner_exercice_fr(self, nom):
        self.exercice_fr_choisi = nom
        self.titre_fr_exercices.setText(f"Français — Exercices\n{nom}")

    def confirmer_exercice_fr(self):
        if not self.exercice_fr_choisi:
            return
        if self.exercice_fr_choisi == "Orthographe":
            self.pages.setCurrentWidget(self.page_exercices_orthographe)
        elif self.exercice_fr_choisi == "Conjugaison":
            self.pages.setCurrentWidget(self.page_exercices_conjugaison)
        elif self.exercice_fr_choisi == "Grammaire":
            self.pages.setCurrentWidget(self.page_exercices_grammaire)
        elif self.exercice_fr_choisi == "Dictée préparée":
            self.pages.setCurrentWidget(self.page_exercices_dictee)

    def selectionner_exercice_dictee(self, nom): self.option_exercice_dictee_choisie = nom
    def confirmer_choix_exercice_dictee(self):
        m = {
            "1-Vendredi 02 Octobre (Je porte un pyjama bleu...)": self.page_ex_dictee_02_oct,
            "1-Vendredi 09 Octobre (Je plante un pin...)": self.page_ex_dictee_09_oct,
            "1-Vendredi 16 Octobre (Il brosse seul les dents...)": self.page_ex_dictee_16_oct,
            "1-Jeudi 22 Octobre (La propreté est bon pour nous...)": self.page_ex_dictee_22_oct,
            "1-Ils montrent la carte de l'étudiant.": self.page_ex_dictee_30_oct
        }
        if self.option_exercice_dictee_choisie in m:
            self.pages.setCurrentWidget(m[self.option_exercice_dictee_choisie])

    def selectionner_exercice_ortho(self, nom): self.option_exercice_ortho_choisie = nom
    def confirmer_choix_exercice_ortho(self):
        m = {
            "1-Complete par ie, y , it.": self.page_ex_ortho_ie_y_it,
            "1-Complete par is, id, iz.": self.page_ex_ortho_is_id_iz,
            "1-Complete par î , isc.": self.page_ex_ortho_i_isc,
            "1-Complete par e, eu.": self.page_ex_ortho_e_eu,
            "1-Complete par oeu, oei.": self.page_ex_ortho_oeu_oei,
            "1-Dictée.": self.page_ex_ortho_dictee_ar
        }
        if self.option_exercice_ortho_choisie in m:
            self.pages.setCurrentWidget(m[self.option_exercice_ortho_choisie])

    def selectionner_exercice_conj(self, nom): self.option_exercice_conj_choisie = nom
    def confirmer_choix_exercice_conj(self):
        m = {
            "1-Remplace par les pronoms personnels sujet je ou Tu...": self.page_ex_conj_je_tu,
            "1-Remplace les mots soulignés par Il ou Elle..": self.page_ex_conj_il_elle,
            "1-Remplace les mots soulignés par les PPS au sigulier.": self.page_ex_conj_singulier,
            "1-Remplace par les PPS Nous, Vous": self.page_ex_conj_nous_vous,
            "1-Remplace par les mots soulignés par les PPS au pluriels": self.page_ex_conj_pluriels,
            "1-Remplace les mots soulignés.": self.page_ex_conj_remplace_soulignes
        }
        if self.option_exercice_conj_choisie in m:
            self.pages.setCurrentWidget(m[self.option_exercice_conj_choisie])

    def selectionner_exercice_gramm(self, nom): self.option_exercice_gramm_choisie = nom
    def confirmer_choix_exercice_gramm(self):
        m = {
            "1-Quels sont les 26 lettres de l'alphabet..": self.page_ex_gramm_26_lettres,
            "1-Combien y a t-il de voyelles...": self.page_ex_gramm_voyelles,
            "1-Sépare les syllabes et donne ses nombres..": self.page_ex_gramm_separe_syllabes,
            "1-Compte et sépare les syllabes..": self.page_ex_gramm_compte_syllabes,
            "1-Complète par  animal-chose-personne..": self.page_ex_gramm_animal_chose_pers,
            "1-Souligne la bonne réponse.": self.page_ex_gramm_souligne_bonne_rep
        }
        if self.option_exercice_gramm_choisie in m:
            self.pages.setCurrentWidget(m[self.option_exercice_gramm_choisie])

    # --- Mathématiques Sélections & Confirmations ---
    def selectionner_lecon_math(self, nom):
        self.lecon_math_choisie = nom
        self.titre_math_lecons.setText(f"Mathématiques\n{nom}")

    def confirmer_lecon_math(self):
        if not self.lecon_math_choisie:
            return
        if self.lecon_math_choisie == "Arithmétiques":
            self.pages.setCurrentWidget(self.page_arithmetique)
        elif self.lecon_math_choisie == "Géométrie":
            self.pages.setCurrentWidget(self.page_geometrie)
        elif self.lecon_math_choisie == "Systeme métrique":
            self.pages.setCurrentWidget(self.page_metrique)

    def selectionner_exercice_math(self, nom):
        self.exercice_math_choisi = nom
        self.titre_math_exercices.setText(f"Exercices de Mathématiques\n{nom}")

    def confirmer_exercice_math(self):
        if not self.exercice_math_choisi:
            return
        if self.exercice_math_choisi == "Arithmétiques":
            self.pages.setCurrentWidget(self.page_exercices_arithmetique)
        elif self.exercice_math_choisi == "Géométrie":
            self.pages.setCurrentWidget(self.page_exercices_geometrie)
        elif self.exercice_math_choisi == "Systeme métrique":
            self.pages.setCurrentWidget(self.page_exercices_metrique)

    def selectionner_exercice_arithmetique(self, nom): self.option_exercice_arith_choisie = nom
    def confirmer_choix_exercice_arithmetique(self):
        m = {
            "1-Compte de 1 en 1 de 0 à 10.": self.page_ex_comptage_10,
            "1-Compte de 1 en 1 de 30 à 49.": self.page_ex_comptage_49,
            "1-Ecris en lettres.": self.page_ex_ecris_lettres,
            "1-Compte de 1 en 1 de 55 à 75.": self.page_ex_comptage_75,
            "1-Pose et effectue.": self.page_ex_pose_effectue,
            "1-Ecris": self.page_ex_arith_ecris
        }
        if self.option_exercice_arith_choisie in m:
            self.pages.setCurrentWidget(m[self.option_exercice_arith_choisie])

    def selectionner_exercice_geo(self, nom): self.option_exercice_geo_choisie = nom
    def confirmer_choix_exercice_geo(self):
        if self.option_exercice_geo_choisie == "1-Trace une ligne droite horizontale de 6cm.":
            self.pages.setCurrentWidget(self.page_ex_geo_ligne_6cm)
        elif self.option_exercice_geo_choisie == "1-Souligne la bonne réponse.":
            self.pages.setCurrentWidget(self.page_ex_geo_souligne)

    def selectionner_exercice_metrique(self, nom): self.option_exercice_metrique_choisie = nom
    def confirmer_choix_exercice_metrique(self):
        m = {
            "1-Trace une ligne horizontale.": self.page_ex_met_ligne_horiz,
            "1-Trace une ligne horizontale de 7cm.": self.page_ex_met_ligne_7cm,
            "1-Trace le segment [AB].": self.page_ex_met_segment_ab,
            "1-Trace un demi droite.": self.page_ex_met_demi_droite,
            "1-Trace [IJ] = 4cm.": self.page_ex_met_ij_4cm,
            "1-Trace un segment [AB] de 6 cm.": self.page_ex_met_segment_ab_6cm
        }
        if self.option_exercice_metrique_choisie in m:
            self.pages.setCurrentWidget(m[self.option_exercice_metrique_choisie])

    def selectionner_option_arithmetique(self, nom): self.option_arithmetique_choisie = nom
    def confirmer_choix_arithmetique(self):
        m = {
            "Comptage de 1 en 1 de 0 à 10": self.page_lecon_comptage_10,
            "Comptage de 1 en 1 de 0 à 49": self.page_lecon_comptage_49,
            "Addition sans retenue": self.page_lecon_addition_sans,
            "Addition avec retenue": self.page_lecon_addition_avec,
            "Comptage de 1 en 1 de 80 à 119": self.page_lecon_comptage_119
        }
        if self.option_arithmetique_choisie in m:
            self.pages.setCurrentWidget(m[self.option_arithmetique_choisie])

    def selectionner_option_geometrie(self, nom): self.option_geometrie_choisie = nom
    def confirmer_choix_geometrie(self):
        m = {
            "Les points": self.page_lecon_point,
            "Les lignes": self.page_lecon_lignes
        }
        if self.option_geometrie_choisie in m:
            self.pages.setCurrentWidget(m[self.option_geometrie_choisie])

    def selectionner_option_metrique(self, nom): self.option_metrique_choisie = nom
    def confirmer_choix_metrique(self):
        m = {
            "Mesurer avec un règle graduée": self.page_lecon_regle,
            "Mesurer un segment": self.page_lecon_segment
        }
        if self.option_metrique_choisie in m:
            self.pages.setCurrentWidget(m[self.option_metrique_choisie])

    # --- Callbacks Retours ---
    def retour_a_arithmetique(self): self.pages.setCurrentWidget(self.page_arithmetique)
    def retour_a_geometrie(self): self.pages.setCurrentWidget(self.page_geometrie)
    def retour_a_metrique(self): self.pages.setCurrentWidget(self.page_metrique)
    def retour_a_math_lecons(self): self.pages.setCurrentWidget(self.page_math_lecons)
    def retour_a_math_exercices(self): self.pages.setCurrentWidget(self.page_math_exercices)
    def retour_a_exercices_arith(self): self.pages.setCurrentWidget(self.page_exercices_arithmetique)
    def retour_a_exercices_geo(self): self.pages.setCurrentWidget(self.page_exercices_geometrie)
    def retour_a_exercices_metrique(self): self.pages.setCurrentWidget(self.page_exercices_metrique)

    def retour_a_fr_lecons(self): self.pages.setCurrentWidget(self.page_fr_lecons)
    def retour_a_fr_exercices(self): self.pages.setCurrentWidget(self.page_fr_exercices)
    def retour_a_lecons_ortho(self): self.pages.setCurrentWidget(self.page_lecons_orthographe)
    def retour_a_lecons_conj(self): self.pages.setCurrentWidget(self.page_lecons_conjugaison)
    def retour_a_lecons_gramm(self): self.pages.setCurrentWidget(self.page_lecons_grammaire)
    def retour_a_lecons_vocab(self): self.pages.setCurrentWidget(self.page_lecons_vocabulaire)

    def retour_a_exercices_ortho(self): self.pages.setCurrentWidget(self.page_exercices_orthographe)
    def retour_a_exercices_conj(self): self.pages.setCurrentWidget(self.page_exercices_conjugaison)
    def retour_a_exercices_gramm(self): self.pages.setCurrentWidget(self.page_exercices_grammaire)
    def retour_a_exercices_dictee(self): self.pages.setCurrentWidget(self.page_exercices_dictee)

    def retour_a_programme(self): self.pages.setCurrentWidget(self.page_programme)
    def retour_au_choix(self):
        self.arreter_gif()
        self.matiere_choisie = None
        self.pages.setCurrentWidget(self.page_choix)

    # =========================================================================
    # RESPONSIVE
    # =========================================================================
    def resizeEvent(self, event):
        super().resizeEvent(event)
        largeur = max(1, self.width())
        hauteur = max(1, self.height())
        taille_bouton = 12 if (largeur < 380 or hauteur < 540) else (14 if largeur < 650 else 16)

        for nom, bouton in self.boutons_choix.items():
            bouton.setStyleSheet(f"""
                                 QPushButton {{
                                 background-color: #4CC9F0;
                                 color: white;
                                 font-size: {taille_bouton}px;
                                 font-weight: bold;
                                 border-radius: 14px;
                                 border: 3px solid #4361EE;
                                 border-bottom: 5px solid #3A0CA3;
                                 padding: 4px;
                                 }}
                                 QPushButton:hover {{ background-color: #38B6FF; border-color: #3A0CA3; }}
                                 QPushButton:checked {{ background-color: #7209B7; border-color: #560FA0; }}
                                 QPushButton:pressed {{ background-color: #3A0CA3; border-bottom-width: 2px; }}
                                 """)

        tous_roses = (
            self.boutons_dessin +
            self.boutons_cours +
            self.boutons_methode_boscher +
            self.boutons_lecons_de_chose +
            self.boutons_math + self.boutons_math_exercices +
            self.boutons_fr_lecons + self.boutons_fr_exercices +
            self.boutons_lecons_ortho + self.boutons_lecons_conj +
            self.boutons_lecons_gramm + self.boutons_lecons_vocab +
            self.boutons_exercices_arith + self.boutons_exercices_geo +
            self.boutons_exercices_metrique + self.boutons_arithmetique +
            self.boutons_geometrie + self.boutons_metrique +
            self.boutons_exercices_ortho + self.boutons_exercices_conj +
            self.boutons_exercices_gramm + self.boutons_exercices_dictee
        )
        for b in tous_roses:
            b.setStyleSheet(f"""
                            QPushButton {{
                            background-color: #F0F2F5;
                            color: #FF2E93;
                            border: 3px solid #FF2E93;
                            border-bottom: 5px solid #C40058;
                            border-radius: 14px;
                            font-size: {taille_bouton}px;
                            font-weight: 800;
                            padding: 4px;
                            }}
                            QPushButton:hover {{ background-color: #E5E9F0; color: #FF0040; border-color: #FF0040; border-bottom-color: #B3002D; }}
                            QPushButton:checked {{ background-color: #FF2E93; color: white; border-color: #C40058; border-bottom: 5px solid #85003A; }}
                            QPushButton:pressed {{ background-color: #D8DCE2; border-bottom: 2px solid #B3002D; padding-top: 8px; }}
                            """)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    fenetre = Programme11eme()
    fenetre.showMaximized()
    sys.exit(app.exec())
