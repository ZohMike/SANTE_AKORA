"""
Module de génération de documents PDF pour les cotations
Assur Defender - Cotation Santé +
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from datetime import datetime
import io
from typing import Dict, Any, List, Optional


class PDFGenerator:
    """Classe principale pour générer les PDF de cotation"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Configure les styles personnalisés pour le document"""
        
        # Style titre principal
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1d29'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Style sous-titre
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2196F3'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))
        
        # Style section
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading3'],
            fontSize=14,
            textColor=colors.HexColor('#145d33'),
            spaceAfter=10,
            spaceBefore=15,
            fontName='Helvetica-Bold'
        ))
        
        # Style normal amélioré
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#495057'),
            alignment=TA_JUSTIFY
        ))
        
        # Style pour les montants importants
        self.styles.add(ParagraphStyle(
            name='BigAmount',
            parent=self.styles['Normal'],
            fontSize=18,
            textColor=colors.HexColor('#2196F3'),
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            spaceAfter=10
        ))
        
        # Style pour les informations
        self.styles.add(ParagraphStyle(
            name='InfoText',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#6c757d'),
            leading=12
        ))
    
    def _add_header(self, canvas_obj, doc):
        """Ajoute l'en-tête personnalisé sur chaque page"""
        canvas_obj.saveState()
        
        # Rectangle d'en-tête
        canvas_obj.setFillColor(colors.HexColor('#f8f9fa'))
        canvas_obj.rect(0, A4[1] - 80, A4[0], 80, fill=True, stroke=False)
        
        # Logo (placeholder - remplacer par votre logo)
        canvas_obj.setFont('Helvetica-Bold', 20)
        canvas_obj.setFillColor(colors.HexColor('#1a1d29'))
        canvas_obj.drawString(40, A4[1] - 50, "🛡️ ASSUR DEFENDER")
        
        # Sous-titre
        canvas_obj.setFont('Helvetica', 10)
        canvas_obj.setFillColor(colors.HexColor('#6c757d'))
        canvas_obj.drawString(40, A4[1] - 65, "Cotation Santé +")
        
        # Date
        canvas_obj.setFont('Helvetica', 9)
        date_str = datetime.now().strftime("%d/%m/%Y")
        canvas_obj.drawRightString(A4[0] - 40, A4[1] - 50, f"Date: {date_str}")
        
        # Ligne de séparation
        canvas_obj.setStrokeColor(colors.HexColor('#e9ecef'))
        canvas_obj.setLineWidth(2)
        canvas_obj.line(0, A4[1] - 85, A4[0], A4[1] - 85)
        
        canvas_obj.restoreState()
    
    def _add_footer(self, canvas_obj, doc):
        """Ajoute le pied de page sur chaque page"""
        canvas_obj.saveState()
        
        # Ligne de séparation
        canvas_obj.setStrokeColor(colors.HexColor('#e9ecef'))
        canvas_obj.setLineWidth(1)
        canvas_obj.line(40, 50, A4[0] - 40, 50)
        
        # Numéro de page
        canvas_obj.setFont('Helvetica', 9)
        canvas_obj.setFillColor(colors.HexColor('#6c757d'))
        page_num = canvas_obj.getPageNumber()
        canvas_obj.drawCentredString(A4[0] / 2, 35, f"Page {page_num}")
        
        # Informations de contact
        canvas_obj.setFont('Helvetica', 8)
        canvas_obj.drawString(40, 35, "www.assurdefender.ci")
        canvas_obj.drawRightString(A4[0] - 40, 35, "contact@assurdefender.ci")
        
        canvas_obj.restoreState()
    
    def _format_currency(self, amount: float) -> str:
        """Formate un montant en FCFA"""
        return f"{int(round(amount)):,} FCFA".replace(",", " ")
    
    def _create_info_table(self, data: List[List[str]], col_widths: List[float] = None) -> Table:
        """Crée un tableau d'informations stylisé"""
        if col_widths is None:
            col_widths = [8*cm, 8*cm]
        
        table = Table(data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#495057')),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        return table
    
    def _create_amount_table(self, data: List[List[str]]) -> Table:
        """Crée un tableau de décomposition des montants"""
        table = Table(data, colWidths=[12*cm, 4*cm])
        
        # Style de base
        base_style = [
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#495057')),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]
        
        # Style pour l'en-tête
        if len(data) > 0:
            base_style.extend([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#145d33')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
            ])
        
        # Style pour le total (dernière ligne)
        if len(data) > 1:
            base_style.extend([
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e3f2fd')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, -1), (-1, -1), 12),
                ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor('#2196F3')),
            ])
        
        # Grille
        base_style.append(('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')))
        
        table.setStyle(TableStyle(base_style))
        return table
    
    def generer_pdf_particulier(
        self,
        resultat: Dict[str, Any],
        produit_name: str,
        client_info: Dict[str, Any],
        numero_devis: str = None
    ) -> bytes:
        """
        Génère un PDF de cotation pour un client particulier.
        
        Args:
            resultat: Dictionnaire contenant les résultats du calcul de prime
            produit_name: Nom du produit sélectionné
            client_info: Informations du client (nom, prénom, contact, etc.)
            numero_devis: Numéro de devis (optionnel)
        
        Returns:
            bytes: Contenu du PDF généré
        """
        buffer = io.BytesIO()
        
        # Création du document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=40,
            leftMargin=40,
            topMargin=100,
            bottomMargin=60,
        )
        
        # Conteneur pour les éléments du document
        story = []
        
        # === TITRE PRINCIPAL ===
        titre = f"PROPOSITION DE COTATION SANTÉ"
        story.append(Paragraph(titre, self.styles['CustomTitle']))
        story.append(Spacer(1, 10))
        
        # Numéro de devis
        if numero_devis:
            story.append(Paragraph(
                f"<b>Devis N° :</b> {numero_devis}",
                self.styles['CustomBody']
            ))
            story.append(Spacer(1, 20))
        
        # === INFORMATIONS CLIENT ===
        story.append(Paragraph("INFORMATIONS CLIENT", self.styles['SectionHeader']))
        
        client_data = [
            ["Nom et Prénom", f"{client_info.get('nom', '')} {client_info.get('prenom', '')}"],
            ["Contact", client_info.get('contact', 'Non renseigné')],
            ["Type de couverture", client_info.get('type_couverture', 'Non renseigné')],
            ["Produit sélectionné", produit_name],
        ]
        
        if client_info.get('nb_enfants', 0) > 0:
            client_data.append(["Nombre d'enfants", str(client_info.get('nb_enfants', 0))])
        
        story.append(self._create_info_table(client_data))
        story.append(Spacer(1, 20))
        
        # === DÉTAIL DE LA PRIME ===
        story.append(Paragraph("DÉTAIL DE LA PRIME", self.styles['SectionHeader']))
        
        # Construction du tableau de détail
        detail_data = [
            ["Désignation", "Montant"]
        ]
        
        # Prime nette
        prime_nette_label = "Prime Nette de Base"
        if resultat.get('bareme_special'):
            prime_nette_label += " (Barème Spécial)"
        detail_data.append([prime_nette_label, self._format_currency(resultat.get('prime_nette_finale', 0))])
        
        # Accessoires
        detail_data.append(["Accessoires", self._format_currency(resultat.get('accessoires', 0))])
        
        # Surprimes si présentes
        surprime_grossesse = resultat.get('surprime_grossesse', 0)
        if surprime_grossesse > 0:
            detail_data.append(["Surprime Grossesse", self._format_currency(surprime_grossesse)])
        
        surprime_age = resultat.get('surprime_age_taux', 0)
        if surprime_age > 0:
            detail_data.append([f"Surprime Âge ({surprime_age}%)", "Inclus dans prime nette"])
        
        surprime_medicale = resultat.get('surprime_risques_taux', 0)
        if surprime_medicale > 0:
            detail_data.append([f"Surprime Médicale ({surprime_medicale}%)", "Inclus dans prime nette"])
        
        # Sous-total HT
        prime_ht = resultat.get('prime_nette_finale', 0) + resultat.get('accessoires', 0)
        detail_data.append(["<b>Sous-total HT</b>", f"<b>{self._format_currency(prime_ht)}</b>"])
        
        # Taxe
        taxe_pourcent = resultat.get('facteurs', {}).get('taux_taxe', 0.08) * 100
        detail_data.append([f"Taxe ({taxe_pourcent}%)", self._format_currency(resultat.get('taxe', 0))])
        
        # Services
        prime_lsp = resultat.get('prime_lsp', 0)
        if prime_lsp > 0:
            detail_data.append(["Prime LSP", self._format_currency(prime_lsp)])
        
        prime_assist = resultat.get('prime_assist_psy', 0)
        if prime_assist > 0:
            detail_data.append(["Prime Assistance Psychologique", self._format_currency(prime_assist)])
        
        # Total
        detail_data.append(["PRIME TOTALE TTC", self._format_currency(resultat.get('prime_ttc_totale', 0))])
        
        story.append(self._create_amount_table(detail_data))
        story.append(Spacer(1, 20))
        
        # === MONTANT FINAL EN GRAND ===
        story.append(Paragraph(
            f"<b>MONTANT TOTAL À PAYER</b>",
            self.styles['CustomSubtitle']
        ))
        story.append(Paragraph(
            self._format_currency(resultat.get('prime_ttc_totale', 0)),
            self.styles['BigAmount']
        ))
        story.append(Spacer(1, 20))
        
        # === DURÉE DU CONTRAT ===
        duree = resultat.get('facteurs', {}).get('duree_contrat', 12)
        story.append(Paragraph(
            f"<b>Durée du contrat :</b> {duree} mois",
            self.styles['CustomBody']
        ))
        story.append(Spacer(1, 30))
        
        # === CONDITIONS ET NOTES ===
        story.append(Paragraph("CONDITIONS PARTICULIÈRES", self.styles['SectionHeader']))
        
        conditions = [
            "✓ Cette cotation est valable 30 jours à compter de sa date d'émission.",
            "✓ La souscription est soumise à l'acceptation du questionnaire médical.",
            "✓ Les garanties prennent effet dès le paiement de la première prime.",
            "✓ Les plafonds de remboursement sont détaillés dans les conditions générales.",
        ]
        
        # Ajout de notes spécifiques
        if resultat.get('bareme_special'):
            conditions.append("✓ Cotation établie selon un barème spécial personnalisé.")
        
        if surprime_medicale > 0:
            affections = resultat.get('affections_declarees', [])
            if affections:
                conditions.append(f"⚠ Surprime médicale appliquée pour : {', '.join(affections)}.")
        
        for condition in conditions:
            story.append(Paragraph(condition, self.styles['CustomBody']))
            story.append(Spacer(1, 5))
        
        story.append(Spacer(1, 20))
        
        # === MENTIONS LÉGALES ===
        story.append(Paragraph(
            "<b>MENTIONS LÉGALES</b>",
            self.styles['InfoText']
        ))
        story.append(Spacer(1, 5))
        
        mentions = (
            "Ce document constitue une proposition de cotation et n'engage ni l'assureur ni le client "
            "tant que le contrat n'est pas signé et la première prime payée. Les garanties détaillées "
            "sont disponibles dans les conditions générales du contrat."
        )
        story.append(Paragraph(mentions, self.styles['InfoText']))
        
        # Génération du PDF
        doc.build(
            story,
            onFirstPage=self._add_header,
            onLaterPages=self._add_header,
            canvasmaker=lambda *args, **kwargs: self._add_footer_to_canvas(
                canvas.Canvas(*args, **kwargs)
            )
        )
        
        # Récupération du contenu
        pdf_content = buffer.getvalue()
        buffer.close()
        
        return pdf_content
    
    def _add_footer_to_canvas(self, canvas_obj):
        """Helper pour ajouter le footer"""
        original_showPage = canvas_obj.showPage
        
        def custom_showPage():
            self._add_footer(canvas_obj, None)
            original_showPage()
        
        canvas_obj.showPage = custom_showPage
        return canvas_obj


    def generer_pdf_corporate(
        self,
        resultat: Dict[str, Any],
        produit_name: str,
        entreprise_info: Dict[str, Any],
        numero_devis: str = None
    ) -> bytes:
        """
        Génère un PDF de cotation pour une entreprise (Corporate).
        
        Args:
            resultat: Dictionnaire contenant les résultats du calcul
            produit_name: Nom du produit sélectionné
            entreprise_info: Informations de l'entreprise
            numero_devis: Numéro de devis (optionnel)
        
        Returns:
            bytes: Contenu du PDF généré
        """
        buffer = io.BytesIO()
        
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=40,
            leftMargin=40,
            topMargin=100,
            bottomMargin=60,
        )
        
        story = []
        
        # === TITRE ===
        story.append(Paragraph("PROPOSITION COMMERCIALE", self.styles['CustomTitle']))
        story.append(Paragraph("Assurance Santé Collective", self.styles['CustomSubtitle']))
        story.append(Spacer(1, 10))
        
        if numero_devis:
            story.append(Paragraph(
                f"<b>Devis N° :</b> {numero_devis}",
                self.styles['CustomBody']
            ))
            story.append(Spacer(1, 20))
        
        # === INFORMATIONS ENTREPRISE ===
        story.append(Paragraph("INFORMATIONS ENTREPRISE", self.styles['SectionHeader']))
        
        entreprise_data = [
            ["Raison sociale", entreprise_info.get('nom', 'Non renseigné')],
            ["Secteur d'activité", entreprise_info.get('secteur', 'Non renseigné')],
            ["Produit sélectionné", produit_name],
        ]
        
        # Ajouter les effectifs si disponibles
        if 'nb_familles' in resultat:
            entreprise_data.append(["Nombre de familles", str(resultat.get('nb_familles', 0))])
        if 'nb_personnes_seules' in resultat:
            entreprise_data.append(["Personnes seules", str(resultat.get('nb_personnes_seules', 0))])
        if 'nb_enfants_supplementaires' in resultat and resultat.get('nb_enfants_supplementaires', 0) > 0:
            entreprise_data.append(["Enfants supplémentaires", str(resultat.get('nb_enfants_supplementaires', 0))])
        
        # Total bénéficiaires
        total_beneficiaires = (
            resultat.get('nb_familles', 0) + 
            resultat.get('nb_personnes_seules', 0) + 
            resultat.get('nb_enfants_supplementaires', 0)
        )
        if total_beneficiaires > 0:
            entreprise_data.append(["<b>Total unités de couverture</b>", f"<b>{total_beneficiaires}</b>"])
        
        story.append(self._create_info_table(entreprise_data))
        story.append(Spacer(1, 20))
        
        # === DÉTAIL DE LA PRIME ===
        story.append(Paragraph("DÉTAIL DE LA COTISATION", self.styles['SectionHeader']))
        
        detail_data = [["Désignation", "Montant"]]
        
        # Prime nette
        detail_data.append(["Prime Nette Totale", self._format_currency(resultat.get('prime_nette_finale', 0))])
        
        # Accessoires
        detail_data.append(["Accessoires", self._format_currency(resultat.get('accessoires', 0))])
        
        # Sous-total HT
        prime_ht = resultat.get('prime_nette_finale', 0) + resultat.get('accessoires', 0)
        detail_data.append(["<b>Sous-total HT</b>", f"<b>{self._format_currency(prime_ht)}</b>"])
        
        # Taxe (Corporate = 3%)
        taxe_pourcent = resultat.get('facteurs', {}).get('taux_taxe', 0.03) * 100
        detail_data.append([f"Taxe ({taxe_pourcent}%)", self._format_currency(resultat.get('taxe', 0))])
        
        # Services
        prime_lsp = resultat.get('prime_lsp', 0)
        if prime_lsp > 0:
            detail_data.append(["Prime LSP", self._format_currency(prime_lsp)])
        
        prime_assist = resultat.get('prime_assist_psy', 0)
        if prime_assist > 0:
            detail_data.append(["Prime Assistance Psychologique", self._format_currency(prime_assist)])
        
        # Total
        detail_data.append(["COTISATION ANNUELLE TTC", self._format_currency(resultat.get('prime_ttc_totale', 0))])
        
        story.append(self._create_amount_table(detail_data))
        story.append(Spacer(1, 20))
        
        # === MONTANT FINAL ===
        story.append(Paragraph("COTISATION ANNUELLE", self.styles['CustomSubtitle']))
        story.append(Paragraph(
            self._format_currency(resultat.get('prime_ttc_totale', 0)),
            self.styles['BigAmount']
        ))
        story.append(Spacer(1, 10))
        
        # Coût par employé si disponible
        if total_beneficiaires > 0:
            cout_unitaire = resultat.get('prime_ttc_totale', 0) / total_beneficiaires
            story.append(Paragraph(
                f"<i>Soit environ {self._format_currency(cout_unitaire)} par unité de couverture</i>",
                self.styles['InfoText']
            ))
        
        story.append(Spacer(1, 30))
        
        # === GARANTIES ===
        story.append(Paragraph("PRINCIPALES GARANTIES", self.styles['SectionHeader']))
        
        garanties = [
            "✓ Consultation et soins médicaux selon le taux de couverture",
            "✓ Hospitalisation et chirurgie",
            "✓ Pharmacie et analyses médicales",
            "✓ Maternité (selon conditions)",
            "✓ Dentaire et optique",
            "✓ Assistance rapatriement sanitaire",
        ]
        
        for garantie in garanties:
            story.append(Paragraph(garantie, self.styles['CustomBody']))
            story.append(Spacer(1, 5))
        
        story.append(Spacer(1, 20))
        
        # === CONDITIONS ===
        story.append(Paragraph("CONDITIONS DE SOUSCRIPTION", self.styles['SectionHeader']))
        
        conditions = [
            "✓ Cette proposition est valable 30 jours à compter de sa date d'émission.",
            "✓ Questionnaire médical obligatoire pour tous les bénéficiaires.",
            "✓ Effet de la garantie dès paiement de la première cotisation.",
            "✓ Tarif garanti pour une durée de 12 mois.",
            "✓ Possibilité de paiement fractionné (mensuel, trimestriel, semestriel).",
        ]
        
        if resultat.get('type_calcul') == 'estimation_rapide':
            conditions.append(
                "⚠ <b>ESTIMATION INDICATIVE</b> - Une micro-tarification sera nécessaire pour l'offre ferme."
            )
        
        for condition in conditions:
            story.append(Paragraph(condition, self.styles['CustomBody']))
            story.append(Spacer(1, 5))
        
        story.append(Spacer(1, 20))
        
        # === PROCHAINES ÉTAPES ===
        story.append(Paragraph("PROCHAINES ÉTAPES", self.styles['SectionHeader']))
        
        etapes = [
            "1. <b>Validation de la proposition</b> par votre entreprise",
            "2. <b>Collecte des informations</b> - Questionnaires médicaux de tous les bénéficiaires",
            "3. <b>Analyse médicale</b> - Étude des dossiers par notre service médical",
            "4. <b>Offre ferme</b> - Émission de la proposition définitive",
            "5. <b>Signature du contrat</b> et mise en place des garanties",
        ]
        
        for etape in etapes:
            story.append(Paragraph(etape, self.styles['CustomBody']))
            story.append(Spacer(1, 5))
        
        story.append(Spacer(1, 30))
        
        # === CONTACT ===
        story.append(Paragraph("VOTRE INTERLOCUTEUR", self.styles['SectionHeader']))
        
        contact_text = (
            "Pour toute question ou complément d'information, "
            "n'hésitez pas à contacter votre conseiller Assur Defender."
        )
        story.append(Paragraph(contact_text, self.styles['CustomBody']))
        story.append(Spacer(1, 10))
        
        contact_info = [
            ["Contact", "contact@assurdefender.ci"],
            ["Téléphone", "+225 XX XX XX XX XX"],
            ["Site web", "www.assurdefender.ci"],
        ]
        story.append(self._create_info_table(contact_info))
        
        story.append(Spacer(1, 20))
        
        # === MENTIONS LÉGALES ===
        story.append(Paragraph("MENTIONS LÉGALES", self.styles['InfoText']))
        story.append(Spacer(1, 5))
        
        mentions = (
            "Cette proposition commerciale est établie à titre indicatif et n'engage ni l'assureur "
            "ni le souscripteur. Elle est susceptible de modifications suite à l'analyse médicale "
            "des bénéficiaires. Les garanties détaillées sont disponibles dans les conditions "
            "générales du contrat qui vous seront remises lors de la souscription."
        )
        story.append(Paragraph(mentions, self.styles['InfoText']))
        
        # Génération
        doc.build(
            story,
            onFirstPage=self._add_header,
            onLaterPages=self._add_header,
            canvasmaker=lambda *args, **kwargs: self._add_footer_to_canvas(
                canvas.Canvas(*args, **kwargs)
            )
        )
        
        pdf_content = buffer.getvalue()
        buffer.close()
        
        return pdf_content


# === FONCTIONS D'INTERFACE ===

def generer_pdf_cotation_particulier(
    resultat: Dict[str, Any],
    produit_name: str,
    client_info: Dict[str, Any],
    numero_devis: str = None
) -> bytes:
    """
    Fonction principale pour générer un PDF de cotation particulier.
    
    Args:
        resultat: Résultat du calcul de prime
        produit_name: Nom du produit
        client_info: Informations du client
        numero_devis: Numéro de devis optionnel
    
    Returns:
        bytes: Contenu du PDF
    """
    generator = PDFGenerator()
    return generator.generer_pdf_particulier(resultat, produit_name, client_info, numero_devis)


def generer_pdf_cotation_corporate(
    resultat: Dict[str, Any],
    produit_name: str,
    entreprise_info: Dict[str, Any],
    numero_devis: str = None
) -> bytes:
    """
    Fonction principale pour générer un PDF de cotation corporate.
    
    Args:
        resultat: Résultat du calcul
        produit_name: Nom du produit
        entreprise_info: Informations de l'entreprise
        numero_devis: Numéro de devis optionnel
    
    Returns:
        bytes: Contenu du PDF
    """
    generator = PDFGenerator()
    return generator.generer_pdf_corporate(resultat, produit_name, entreprise_info, numero_devis)
