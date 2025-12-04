import streamlit as st
import math
import pandas as pd
import io
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date
import random
from data import * # Assurez-vous que le fichier data.py existe et contient les constantes nécessaires
from calculations import ( # Assurez-vous que le fichier calculations.py existe et contient toutes les fonctions importées.
    format_currency,
    calculer_age,
    calculer_surprime_age,
    calculer_surprime_age_famille,
    valider_age_enfant,
    calculer_imc,
    afficher_imc_detaille,
    valider_affections,
    calculer_prime_particuliers as calc_calculer_prime_particuliers,
    calculer_prime_corporate_rapide as calc_calculer_prime_corporate_rapide,
    valider_fichier_excel as calc_valider_fichier_excel,
    traiter_ligne_assure as calc_traiter_ligne_assure,
    micro_tarification_excel as calc_micro_tarification_excel,
    generer_template_excel as calc_generer_template_excel,
)
from ui_components import display_member_form

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER


# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    layout="wide", 
    page_title="Assur Defender - Cotation Santé +",
    page_icon="🛡️",
    initial_sidebar_state="collapsed"
)

def load_css(file_name):
    """Charge un fichier CSS et l'injecte dans l'application Streamlit."""
    try:
        with open(file_name, "r") as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        # st.error(f"Le fichier CSS '{file_name}' n'a pas été trouvé.") # Commenté pour éviter l'erreur si styles.css n'est pas fourni
        pass

# Charger le CSS externe
load_css("styles.css")

# Header avec logo et utilisateur - THÈME CLAIR + ICÔNES
st.markdown("""
    <div class="main-header">
        <div class="header-logo">
            <i class="fas fa-shield-alt" style="color: #1a1d29;"></i>
            <span>Assur Defender</span>
        </div>
        <div class="user-info">
            <i class="fas fa-user" style="color: #495057;"></i> Utilisateur connecté
        </div>
    </div>
""", unsafe_allow_html=True)

# --- 1. DONNÉES ET CONSTANTES ---

# Les constantes sont supposées être importées depuis data.py
# Exemple de constantes nécessaires pour que le code fonctionne:
# TAUX_TAXE_PARTICULIER = 0.08
# TAUX_TAXE_CORPORATE = 0.03
# MAX_ENFANTS_SUPPLEMENTAIRES = 5
# AFF_EXCLUES = ["Cancer", "AVC"]
# SURPRIME_FORFAITAIRE_GROSSESSE = 300000
# MAX_SURPRIME_RISQUE_CORP = 100
# LISTE_AFFECTIONS = ["Diabète", "Hypertension", "Asthme"]
# TAUX_MAJORATION_MEDICALE = {"Diabète": 10, "Hypertension": 5, "Asthme": 5}
# PRODUITS_PARTICULIERS_UI = {"P70": "Garantie 70%", "P80": "Garantie 80%", "P90": "Garantie 90%", "bareme_special": "Barème Spécial"}
# PRODUITS_CORPORATE_UI = {"C70": "Corporate 70%", "C80": "Corporate 80%", "bareme_special": "Barème Spécial"}
# TARIFS_PARTICULIERS = { ... }
# TARIFS_CORPORATE = { ... }

# --- 2. FONCTIONS D'AFFICHAGE ET UTILITAIRES ---

def calculer_prime_particuliers(
    produit_key: str, 
    type_couverture: str, 
    enfants_supplementaires: int = 0, 
    affections_declarees: Optional[List[str]] = None, 
    grossesse: bool = False, 
    reduction_commerciale: float = 0, 
    duree_contrat: int = 12,
    date_naissance_principale: Optional[date] = None,
    date_naissance_conjoint: Optional[date] = None,
    prime_nette_manuelle: Optional[float] = None,
    accessoires_manuels: Optional[float] = None,
    accessoire_plus: float = 0,
    montant_grossesse_manuel: Optional[float] = None,
    surprime_manuelle_pourcent: float = 0.0
) -> Dict[str, Any]:
    """Wrapper vers calculations.calculer_prime_particuliers."""
    return calc_calculer_prime_particuliers(
        produit_key=produit_key,
        type_couverture=type_couverture,
        enfants_supplementaires=enfants_supplementaires,
        affections_declarees=affections_declarees,
        grossesse=grossesse,
        reduction_commerciale=reduction_commerciale,
        duree_contrat=duree_contrat,
        date_naissance_principale=date_naissance_principale,
        date_naissance_conjoint=date_naissance_conjoint,
        prime_nette_manuelle=prime_nette_manuelle,
        accessoires_manuels=accessoires_manuels,
        accessoire_plus=accessoire_plus,
        montant_grossesse_manuel=montant_grossesse_manuel,
        surprime_manuelle_pourcent=surprime_manuelle_pourcent,
    )

def calculer_prime_corporate_rapide(
    produit_key: str, 
    nb_familles: int = 0, 
    nb_personnes_seules: int = 0,
    nb_enfants_supplementaires: int = 0,
    surprime_risques: float = 0, 
    reduction_commerciale: float = 0, 
    duree_contrat: int = 12,
    prime_nette_manuelle: Optional[float] = None,
    accessoires_manuels: Optional[float] = None,
    accessoire_plus: float = 0
) -> Dict[str, Any]:
    """Wrapper vers calculations.calculer_prime_corporate_rapide."""
    return calc_calculer_prime_corporate_rapide(
        produit_key=produit_key,
        nb_familles=nb_familles,
        nb_personnes_seules=nb_personnes_seules,
        nb_enfants_supplementaires=nb_enfants_supplementaires,
        surprime_risques=surprime_risques,
        reduction_commerciale=reduction_commerciale,
        duree_contrat=duree_contrat,
        prime_nette_manuelle=prime_nette_manuelle,
        accessoires_manuels=accessoires_manuels,
        accessoire_plus=accessoire_plus,
    )


def valider_fichier_excel(df: pd.DataFrame) -> Tuple[bool, Optional[str], Optional[pd.DataFrame]]:
    """Wrapper vers calculations.valider_fichier_excel."""
    return calc_valider_fichier_excel(df)


def traiter_ligne_assure(
    ligne: pd.Series,
    produit_key: str,
    duree_contrat: int
) -> Dict[str, Any]:
    """Wrapper vers calculations.traiter_ligne_assure."""
    return calc_traiter_ligne_assure(
        ligne=ligne,
        produit_key=produit_key,
        duree_contrat=duree_contrat,
    )


def micro_tarification_excel(
    df: pd.DataFrame,
    produit_key: str,
    duree_contrat: int
) -> Dict[str, Any]:
    """Wrapper vers calculations.micro_tarification_excel."""
    return calc_micro_tarification_excel(
        df=df,
        produit_key=produit_key,
        duree_contrat=duree_contrat,
    )


def generer_template_excel() -> bytes:
    """Wrapper vers calculations.generer_template_excel."""
    return calc_generer_template_excel()


def _afficher_details_resultat(resultat: Dict[str, Any], taux_taxe: float):
    """Affiche les détails du résultat (utilisé à l'intérieur d'expanders)."""
    st.markdown("**Composition de la Prime :**")
    col_det1, col_det2 = st.columns(2)
    
    # Colonne 1 : Détails des primes
    col_det1.metric(
        "Prime Nette de Base (Initiale)", 
        format_currency(resultat['prime_nette_base'])
    )
    
    if resultat.get('surprime_grossesse', 0) > 0:
        col_det1.metric(
            "└─ dont Surprime Grossesse", 
            format_currency(resultat['surprime_grossesse'])
        )
    
    col_det1.metric("Accessoires", format_currency(resultat['accessoires']))
    col_det1.metric(
        "Prime Nette Finale (Après Ajustements)", 
        format_currency(resultat['prime_nette_finale'])
    )
    col_det1.metric(
        f"Taxe ({taux_taxe*100:.0f}%)", 
        format_currency(resultat['taxe'])
    )
    col_det1.metric(
        "Prime TTC Taxable", 
        format_currency(resultat['prime_ttc_taxable'])
    )
    
    # Colonne 2 : Services optionnels
    col_det2.markdown("#### Services Optionnels (Hors Taxe)")
    col_det2.metric("Prime LSP", format_currency(resultat['prime_lsp']))
    col_det2.metric("Prime Assist-Psy", format_currency(resultat['prime_assist_psy']))
    
    st.markdown("---")
    st.markdown("**Facteurs d'Ajustement Appliqués :**")
    col_f1, col_f2 = st.columns(2)
    
    facteurs = resultat['facteurs']
    taux_surprime_risques = resultat.get('surprime_risques_taux', 0)
    taux_surprime_age = resultat.get('surprime_age_taux', 0)
    taux_surprime_totale = resultat.get('surprime_totale_taux', facteurs['surprime'])
    
    col_f1.metric("Réduction Commerciale", f"{facteurs['reduction']}%")
    col_f1.metric("└─ Facteur Appliqué", f"{facteurs['facteur_reduction']:.2f}")
    
    if taux_surprime_risques > 0:
        col_f1.metric("Surprime Risques Médicaux", f"{taux_surprime_risques}%")
    
    if taux_surprime_age > 0:
        col_f1.metric("Surprime Âge (>51 ans)", f"{taux_surprime_age}%")
    
    if taux_surprime_totale > 0:
        col_f1.metric("Surprime Totale", f"{taux_surprime_totale}%")
        col_f1.metric("└─ Facteur Appliqué", f"{facteurs['facteur_surprime']:.2f}")
    
    col_f2.metric("Durée du Contrat", f"{facteurs['duree_contrat']} mois")
    col_f2.metric("└─ Facteur Durée", f"{facteurs['facteur_duree']:.2f}")
    
    # Affichage des affections si présentes
    if resultat.get('affections_declarees'):
        st.markdown("---")
        st.markdown("**Affections Déclarées :**")
        for aff in resultat['affections_declarees']:
            taux = TAUX_MAJORATION_MEDICALE[aff]
            st.caption(f"• {aff} (Majoration : {taux}%)")


def afficher_resultat(resultat: Dict[str, Any], tarif_name: str, taux_taxe: float):
    """Affiche les résultats du calcul de prime de manière structurée."""
    st.markdown(
        f"### **Montant Total à Payer (TTC) : {format_currency(resultat['prime_ttc_totale'])}** 💰"
    )
    st.caption(
        f"Calcul basé sur le produit **{tarif_name}** "
        f"et un Taux de Taxe de **{taux_taxe*100:.0f}%**."
    )
    
    with st.expander("📊 Voir le Détail du Calcul et des Facteurs"):
        _afficher_details_resultat(resultat, taux_taxe)


def afficher_resultat_simple(resultat: Dict[str, Any], tarif_name: str, taux_taxe: float):
    """Affiche les résultats sans expander (pour usage dans un expander parent)."""
    st.markdown(
        f"### **Montant Total à Payer (TTC) : {format_currency(resultat['prime_ttc_totale'])}** 💰"
    )
    st.caption(
        f"Calcul basé sur le produit **{tarif_name}** "
        f"et un Taux de Taxe de **{taux_taxe*100:.0f}%**."
    )
    st.markdown("---")
    _afficher_details_resultat(resultat, taux_taxe)


def afficher_resultat_micro_tarification(
    resultat_micro: Dict[str, Any],
    produit_name: str,
    reduction_commerciale: float = 0
):
    """Affiche les résultats de la micro-tarification Excel."""
    
    # Calcul de la prime finale après réduction commerciale
    prime_avant_reduction = resultat_micro['prime_ttc_totale']
    facteur_reduction = (100 - reduction_commerciale) / 100
    prime_finale = prime_avant_reduction * facteur_reduction
    economie = prime_avant_reduction - prime_finale if reduction_commerciale > 0 else 0
    
    # Affichage principal
    st.markdown(f"### **Prime Totale TTC Ferme : {format_currency(prime_finale)}** 💼")
    
    if reduction_commerciale > 0:
        col_red1, col_red2 = st.columns(2)
        col_red1.metric("Prime avant réduction", format_currency(prime_avant_reduction))
        col_red2.metric(f"Économie ({reduction_commerciale}%)", format_currency(economie), delta=f"-{reduction_commerciale}%")
    
    st.caption(f"Produit : **{produit_name}** | Taxe Corporate : **3%**")
    
    # Résumé des assurés
    st.markdown("---")
    st.markdown("### 📋 Analyse du Portefeuille")
    
    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
    
    col_stat1.metric(
        "👥 Total Assurés",
        resultat_micro['nb_total'],
        help="Nombre total de lignes dans le fichier"
    )
    col_stat2.metric(
        "✅ Éligibles",
        resultat_micro['nb_eligibles'],
        delta=f"{(resultat_micro['nb_eligibles']/resultat_micro['nb_total']*100):.1f}%",
        delta_color="normal"
    )
    col_stat3.metric(
        "⛔ Exclusions",
        resultat_micro['nb_exclus'],
        delta=f"{(resultat_micro['nb_exclus']/resultat_micro['nb_total']*100):.1f}%" if resultat_micro['nb_exclus'] > 0 else None,
        delta_color="inverse"
    )
    col_stat4.metric(
        "⚠️ Erreurs",
        resultat_micro['nb_erreurs'],
        delta=f"{(resultat_micro['nb_erreurs']/resultat_micro['nb_total']*100):.1f}%" if resultat_micro['nb_erreurs'] > 0 else None,
        delta_color="inverse"
    )
    
    # Information sur les enfants supplémentaires
    if resultat_micro.get('nb_enfants_supplementaires', 0) > 0:
        st.info(
            f"👶 **{resultat_micro['nb_enfants_supplementaires']} Enfant(s) Supplémentaire(s)** détecté(s) "
            f"(à partir du 4ème enfant) - Facturation additionnelle appliquée"
        )
    
    # Alertes pour exclusions et erreurs
    if resultat_micro['nb_exclus'] > 0:
        st.error(f"⛔ **{resultat_micro['nb_exclus']} Assuré(s) Exclu(s)** - Affections bloquantes détectées")
        with st.expander("Voir les assurés exclus"):
            for assure in resultat_micro['assures_exclus']:
                st.warning(f"**{assure['nom']} {assure['prenom']}** : {assure['raison']}")
            st.info("💡 Ces dossiers nécessitent une soumission manuelle et une analyse médicale approfondie.")
    
    if resultat_micro['nb_erreurs'] > 0:
        st.warning(f"⚠️ **{resultat_micro['nb_erreurs']} Erreur(s) de Validation**")
        with st.expander("Voir les erreurs"):
            for assure in resultat_micro['assures_erreurs']:
                st.error(f"**{assure['nom']} {assure['prenom']}** : {assure['raison']}")
    
    # Détail de la composition
    st.markdown("---")
    with st.expander("💰 Détail de la Composition de la Prime"):
        col_comp1, col_comp2 = st.columns(2)
        
        col_comp1.metric("Prime Nette Totale (Groupe)", format_currency(resultat_micro['prime_nette_totale']))
        col_comp1.metric("Accessoires", format_currency(resultat_micro['accessoires']))
        col_comp1.metric("Taxe Corporate (3%)", format_currency(resultat_micro['taxe']))
        col_comp1.metric("Prime TTC Taxable", format_currency(resultat_micro['prime_ttc_taxable']))
        
        col_comp2.markdown("#### Services Optionnels")
        col_comp2.metric("Services (LSP + Assist-Psy)", format_currency(resultat_micro['services']))
        col_comp2.metric("Prime TTC Totale", format_currency(prime_avant_reduction))
        
        if reduction_commerciale > 0:
            col_comp2.metric(f"Réduction ({reduction_commerciale}%)", f"-{format_currency(economie)}", delta_color="inverse")
            col_comp2.metric("**Prime Finale**", format_currency(prime_finale))
        
        # Statistiques par assuré
        prime_moyenne = prime_finale / resultat_micro['nb_eligibles'] if resultat_micro['nb_eligibles'] > 0 else 0
        st.markdown("---")
        st.metric("📊 Prime Moyenne par Assuré Éligible", format_currency(prime_moyenne))


def reset_results():
    """Réinitialise les résultats en session state."""
    if 'resultat_part' in st.session_state:
        del st.session_state['resultat_part']
    if 'resultat_corp_rapide' in st.session_state:
        del st.session_state['resultat_corp_rapide']
    if 'resultat_corp_excel' in st.session_state:
        del st.session_state['resultat_corp_excel']
    if 'df_corporate' in st.session_state:
        del st.session_state['df_corporate']



# ==============================================================================
# MODIFICATION 3: Fonctions de sauvegarde/chargement des informations client
# ==============================================================================

def sauvegarder_infos_client():
    """Sauvegarde les informations client actuelles dans session_state pour réutilisation."""
    if 'infos_clients_sauvegardees' not in st.session_state:
        st.session_state['infos_clients_sauvegardees'] = {}
    
    type_couv = st.session_state.get('type_couverture_part', 'Personne seule')
    
    if type_couv == 'Personne seule':
        st.session_state['infos_clients_sauvegardees']['ps'] = {
            'nom': st.session_state.get('nom_ps', ''),
            'prenom': st.session_state.get('prenom_ps', ''),
            'date_naissance': st.session_state.get('date_naissance_ps'),
            'lieu_naissance': st.session_state.get('lieu_naissance_ps', ''),
            'contact': st.session_state.get('contact_ps', ''),
            'numero_cnam': st.session_state.get('numero_cnam_ps', ''),
            'nationalite': st.session_state.get('nationalite_ps', 'Ivoirienne'),
            'etat_civil': st.session_state.get('etat_civil_ps', 'Célibataire'),
            'taille': st.session_state.get('taille_ps', 170),
            'poids': st.session_state.get('poids_ps', 70),
            'tension': st.session_state.get('tension_ps', '12/8'),
            'emploi': st.session_state.get('emploi_ps', ''),
            'affections': st.session_state.get('affections_ps', []),
            'grossesse': st.session_state.get('grossesse_ps', False),
        }
    else:
        st.session_state['infos_clients_sauvegardees']['famille'] = {
            'adulte1': {
                'nom': st.session_state.get('nom_adulte1', ''),
                'prenom': st.session_state.get('prenom_adulte1', ''),
                'date_naissance': st.session_state.get('date_naissance_adulte1'),
                'lieu_naissance': st.session_state.get('lieu_naissance_adulte1', ''),
                'contact': st.session_state.get('contact_adulte1', ''),
                'numero_cnam': st.session_state.get('numero_cnam_adulte1', ''),
                'nationalite': st.session_state.get('nationalite_adulte1', 'Ivoirienne'),
                'etat_civil': st.session_state.get('etat_civil_adulte1', 'Célibataire'),
                'taille': st.session_state.get('taille_adulte1', 170),
                'poids': st.session_state.get('poids_adulte1', 70),
                'tension': st.session_state.get('tension_adulte1', '12/8'),
                'emploi': st.session_state.get('emploi_adulte1', ''),
                'affections': st.session_state.get('affections_adulte1', []),
                'grossesse': st.session_state.get('grossesse_adulte1', False),
            },
            'adulte2': {
                'nom': st.session_state.get('nom_adulte2', ''),
                'prenom': st.session_state.get('prenom_adulte2', ''),
                'date_naissance': st.session_state.get('date_naissance_adulte2'),
                'lieu_naissance': st.session_state.get('lieu_naissance_adulte2', ''),
                'contact': st.session_state.get('contact_adulte2', ''),
                'numero_cnam': st.session_state.get('numero_cnam_adulte2', ''),
                'nationalite': st.session_state.get('nationalite_adulte2', 'Ivoirienne'),
                'etat_civil': st.session_state.get('etat_civil_adulte2', 'Marié(e)'),
                'taille': st.session_state.get('taille_adulte2', 165),
                'poids': st.session_state.get('poids_adulte2', 65),
                'tension': st.session_state.get('tension_adulte2', '12/8'),
                'emploi': st.session_state.get('emploi_adulte2', ''),
                'affections': st.session_state.get('affections_adulte2', []),
                'grossesse': st.session_state.get('grossesse_adulte2', False),
            }
        }


def charger_infos_client(type_couv: str):
    """Charge les informations client sauvegardées dans les champs de saisie."""
    if 'infos_clients_sauvegardees' not in st.session_state:
        return False
    
    infos = st.session_state['infos_clients_sauvegardees']
    
    if type_couv == 'Personne seule' and 'ps' in infos:
        donnees = infos['ps']
        for key, value in donnees.items():
            if key != 'date_naissance':
                st.session_state[f'{key}_ps'] = value
            else:
                st.session_state['date_naissance_ps'] = value if value else datetime(1990, 1, 1).date()
        return True
    
    elif type_couv == 'Famille' and 'famille' in infos:
        donnees = infos['famille']
        
        if 'adulte1' in donnees:
            for key, value in donnees['adulte1'].items():
                if key != 'date_naissance':
                    st.session_state[f'{key}_adulte1'] = value
                else:
                    st.session_state['date_naissance_adulte1'] = value if value else datetime(1990, 1, 1).date()
        
        if 'adulte2' in donnees:
            for key, value in donnees['adulte2'].items():
                if key != 'date_naissance':
                    st.session_state[f'{key}_adulte2'] = value
                else:
                    st.session_state['date_naissance_adulte2'] = value if value else datetime(1985, 1, 1).date()
        
        return True
    
    return False


# ==============================================================================
# MODIFICATION 1: Nouvelle fonction de génération PDF
# ==============================================================================

def generer_pdf_proposition(data_frame: pd.DataFrame, options_data: List[Dict], nb_options: int) -> bytes:
    """Génère un PDF professionnel à partir du DataFrame de proposition."""
    buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#495057'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    normal_style = styles['Normal']
    elements = []
    
    title = Paragraph("OFFRE SANTÉ - RÉCAPITULATIF", title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.5*cm))
    
    table_data = []
    
    if nb_options == 1:
        table_data.append(['Désignation', 'OPTION 1'])
        col_widths = [8*cm, 7*cm]
    elif nb_options == 2:
        table_data.append(['Désignation', 'OPTION 1', 'OPTION 2'])
        col_widths = [6*cm, 4.5*cm, 4.5*cm]
    else:
        table_data.append(['Désignation', 'OPTION 1', 'OPTION 2', 'OPTION 3'])
        col_widths = [5*cm, 4*cm, 4*cm, 4*cm]
    
    for idx, row in data_frame.iterrows():
        row_data = [str(row['Désignation'])]
        for i in range(nb_options):
            col_name = f'OPTION {i+1}'
            if col_name in row:
                row_data.append(str(row[col_name]))
        table_data.append(row_data)
    
    table = Table(table_data, colWidths=col_widths)
    
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a1a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#f8f9fa')),
        ('TEXTCOLOR', (0, 1), (0, -1), colors.HexColor('#495057')),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('FONTNAME', (1, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (1, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#1a1a1a')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (1, 1), (-1, -1), [colors.white, colors.HexColor('#f8f8f8')]),
    ])
    
    for idx, row in data_frame.iterrows():
        row_idx = idx + 1
        
        if row['Désignation'] in ['PRIME NETTE / PERSONNE', 'PRIME NETTE ANNUELLE TOTALE']:
            table_style.add('BACKGROUND', (0, row_idx), (-1, row_idx), colors.HexColor('#f2e8d9'))
            table_style.add('FONTNAME', (0, row_idx), (-1, row_idx), 'Helvetica-Bold')
        
        if row['Désignation'] == 'PRIME TTC ANNUELLE':
            table_style.add('BACKGROUND', (0, row_idx), (-1, row_idx), colors.HexColor('#754015'))
            table_style.add('TEXTCOLOR', (0, row_idx), (-1, row_idx), colors.whitesmoke)
            table_style.add('FONTNAME', (0, row_idx), (-1, row_idx), 'Helvetica-Bold')
    
    table.setStyle(table_style)
    elements.append(table)
    elements.append(Spacer(1, 1*cm))
    
    date_text = f"Date de la proposition : {datetime.now().strftime('%d/%m/%Y')}"
    elements.append(Paragraph(date_text, normal_style))
    elements.append(Spacer(1, 0.3*cm))
    
    contact_text = "Contact commercial : [À RENSEIGNER]"
    elements.append(Paragraph(contact_text, normal_style))
    elements.append(Spacer(1, 0.5*cm))
    
    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=normal_style,
        fontSize=9,
        textColor=colors.HexColor('#dc3545'),
        fontName='Helvetica-Oblique'
    )
    disclaimer_text = "Ce document est une proposition commerciale et n'a pas valeur de contrat tant qu'il n'est pas signé par les deux parties."
    elements.append(Paragraph(disclaimer_text, disclaimer_style))
    
    doc.build(elements)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes


# ==============================================================================
# MODIFICATIONS 1 & 2: Fonction generer_recapitulatif_particulier modifiée
# ==============================================================================

def generer_recapitulatif_particulier(resultats_multi: Dict[int, Dict], baremes_affiches: List[str]):
    """Génère un récapitulatif comparatif des 3 premières options sous forme de PDF."""
    
    configurations_baremes = st.session_state.get('configurations_baremes', {})
    options_data = []
    
    nb_options = len(baremes_affiches)
    options_data = []
    
    for idx in range(nb_options):
        bareme_key = baremes_affiches[idx]
        resultat_data = resultats_multi[idx]
        resultat = resultat_data['resultat']
        config = configurations_baremes.get(idx, {})

        type_couv = config.get('type_couverture', 'Personne seule')
        nb_enfants_supp = config.get('enfants_supp', 0)
        
        type_proposition_label = "Individuel" if type_couv == 'Personne seule' else "Famille"
        population_value = '1'
        enfants_supp_value = str(nb_enfants_supp) if type_couv == 'Famille' else 'N/A' 
        
        produit_ui_name = PRODUITS_PARTICULIERS_UI.get(bareme_key, bareme_key)
        garantie = 'N/A'
        plafond_pers = 'N/A'
        plafond_famille = 'N/A'
        
        if bareme_key == 'bareme_special':
            baremes_speciaux_info = st.session_state.get('baremes_speciaux_info', {})
            info_bareme_special = baremes_speciaux_info.get(bareme_key, {})
            
            plafond_pers_val = info_bareme_special.get('plafond_personne', 0)
            plafond_famille_val = info_bareme_special.get('plafond_famille', 0)
            taux_couv_val = info_bareme_special.get('taux_couverture', 0)
            
            if plafond_pers_val > 0:
                plafond_pers = format_currency(plafond_pers_val)
            if plafond_famille_val > 0:
                plafond_famille = format_currency(plafond_famille_val)
            if taux_couv_val > 0:
                garantie = f"{taux_couv_val:.0f}%"
        elif '70%' in produit_ui_name or 'P70' in bareme_key or '70' in bareme_key:
            garantie = '70%'
            plafond_pers = format_currency(1_000_000)
            plafond_famille = format_currency(3_000_000)
        elif '80%' in produit_ui_name or 'P80' in bareme_key or '80' in bareme_key:
            garantie = '80%'
            plafond_pers = format_currency(2_500_000)
            plafond_famille = format_currency(7_500_000)
        elif '90%' in produit_ui_name or 'P90' in bareme_key or '90' in bareme_key:
            garantie = '90%'
            plafond_pers = format_currency(3_500_000)
            plafond_famille = format_currency(10_500_000)
        
        prime_nette_finale = resultat['prime_nette_finale']
        surprime_affection = resultat.get('surprime_risques_montant', 0)
        surprime_grossesse = resultat.get('surprime_grossesse', 0)
        prime_nette_annuelle_totale = prime_nette_finale + surprime_affection + surprime_grossesse

        options_data.append({
            'plafond_annuel_pers': plafond_pers,
            'plafond_annuel_famille': plafond_famille,
            'garanties': garantie,
            'type_proposition': type_proposition_label,
            'population': population_value,
            'enfants_supp': enfants_supp_value,
            'prime_nette_personne': format_currency(prime_nette_finale),
            'surprime_affection': format_currency(surprime_affection),
            'surprime_grossesse': format_currency(surprime_grossesse),
            'prime_totale_couverture_deces': format_currency(resultat.get('prime_lsp', 0)),
            'assistance_psychologique': format_currency(resultat.get('prime_assist_psy', 0)),
            'prime_nette_annuelle_totale': format_currency(prime_nette_annuelle_totale),
            'accessoires': format_currency(resultat['accessoires']),
            'taxes': format_currency(resultat['taxe']),
            'prime_ttc_annuelle': format_currency(resultat['prime_ttc_totale'])
        })


    designations = [
        'PLAFOND ANNUEL / PERS',
        'PLAFOND ANNUEL / FAMILLE',
        'GESTIONNAIRE', 
        'TERRITORIALITÉ', 
        'GARANTIES', 
        'TYPE DE PROPOSITION', 
        'POPULATION', 
        'PRIME NETTE / PERSONNE',
        'SURPRIME AFFECTION',
        'SURPRIME GROSSESSE',
        'PRIME TOTALE COUVERTURE DECES',
        'ASSISTANCE PSYCHOLOGIQUE',
        'PRIME NETTE ANNUELLE TOTALE',
        'ACCESSOIRES',
        'TAXES',
        'PRIME TTC ANNUELLE'
    ]
    
    df_dict = {'Désignation': designations}
    
    for i in range(nb_options):
        option_values = [
            options_data[i]['plafond_annuel_pers'],
            options_data[i]['plafond_annuel_famille'],
            'ANKARA SERVICE', 'COTE D\'IVOIRE', options_data[i]['garanties'], 
            options_data[i]['type_proposition'], options_data[i]['population'], 
            options_data[i]['prime_nette_personne'], options_data[i]['surprime_affection'], 
            options_data[i]['surprime_grossesse'], options_data[i]['prime_totale_couverture_deces'], 
            options_data[i]['assistance_psychologique'], options_data[i]['prime_nette_annuelle_totale'], 
            options_data[i]['accessoires'], options_data[i]['taxes'], options_data[i]['prime_ttc_annuelle']
        ]
        df_dict[f'OPTION {i+1}'] = option_values
    
    has_famille_option = any(d['type_proposition'] == 'Famille' for d in options_data)
    if has_famille_option:
        try:
            insert_index = designations.index('POPULATION') + 1
            designations.insert(insert_index, 'ENFANTS SUPPLEMENTAIRES')
            for i in range(nb_options):
                df_dict[f'OPTION {i+1}'].insert(insert_index, options_data[i]['enfants_supp'])
        except ValueError:
            pass

    data_frame = pd.DataFrame(df_dict)
    
    pdf_bytes = generer_pdf_proposition(data_frame, options_data, nb_options)
    
    st.success(f"✅ Proposition commerciale générée avec succès ({nb_options} option{'s' if nb_options > 1 else ''}) !")
    
    st.download_button(
        label="📥 TÉLÉCHARGER LA PROPOSITION (PDF)",
        data=pdf_bytes,
        file_name=f"Proposition_Sante_Particulier_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
        mime="application/pdf",
        type="primary",
        use_container_width=True
    )

# --- 3. INTERFACE STREAMLIT ---

# Tabs horizontaux pour la navigation
tab_dashboard, tab_cotation, tab_polices, tab_parametrages = st.tabs([
    "Dashboard",
    "Cotation", 
    "Polices",
    "Paramétrages"
])

# ============================================
# TAB DASHBOARD
# ============================================
with tab_dashboard:
    st.title("📊 Dashboard")
    st.markdown("---")
    
    # Métriques principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Cotations ce mois",
            value="0",
            delta="0"
        )
    
    with col2:
        st.metric(
            label="Polices actives",
            value="0",
            delta="0"
        )
    
    with col3:
        st.metric(
            label="Prime totale",
            value="0 FCFA",
            delta="0%"
        )
    
    with col4:
        st.metric(
            label="Taux de conversion",
            value="0%",
            delta="0%"
        )
    
    st.markdown("---")
    
    # Graphiques (placeholder)
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("📈 Évolution des cotations")
        st.info("Graphique à venir - Intégration en cours")
    
    with col_right:
        st.subheader("🎯 Répartition par type")
        st.info("Graphique à venir - Intégration en cours")
    
    st.markdown("---")
    
    st.subheader("📋 Dernières activités")
    st.info("Liste des dernières cotations à venir")

# ============================================
# TAB POLICES
# ============================================
with tab_polices:
    st.title("📋 Gestion des Polices")
    st.markdown("---")
    
    # Onglets pour différentes vues
    tab_list, tab_search, tab_stats = st.tabs(["Liste des polices", "Recherche", "Statistiques"])
    
    with tab_list:
        st.subheader("Liste des polices")
        st.info("📝 Module de gestion des polices à venir")
        st.markdown("""
        Ce module permettra de :
        - Voir toutes les polices créées
        - Filtrer par statut (actif, expiré, en attente)
        - Modifier une police
        - Générer des documents
        """)
    
    with tab_search:
        st.subheader("Recherche de polices")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.text_input("Numéro de police")
        with col2:
            st.text_input("Nom du client")
        with col3:
            st.date_input("Date de création")
        
        st.button("🔍 Rechercher", type="primary", use_container_width=True)
        
        st.info("Aucune police trouvée")
    
    with tab_stats:
        st.subheader("Statistiques des polices")
        st.info("📊 Statistiques à venir")

# ============================================
# TAB PARAMÉTRAGES
# ============================================
with tab_parametrages:
    st.title("⚙️ Paramétrages")
    st.markdown("---")
    
    # Onglets de configuration
    tab_tarifs, tab_users, tab_system = st.tabs(["Tarifs & Barèmes", "Utilisateurs", "Système"])
    
    with tab_tarifs:
        st.subheader("Configuration des tarifs")
        st.info("🔧 Module de configuration des tarifs à venir")
        st.markdown("""
        Ce module permettra de :
        - Modifier les tarifs des barèmes
        - Ajouter de nouveaux barèmes
        - Configurer les taux de taxe
        - Gérer les surprimes
        """)
    
    with tab_users:
        st.subheader("Gestion des utilisateurs")
        st.info("👥 Module de gestion des utilisateurs à venir")
    
    with tab_system:
        st.subheader("Configuration système")
        st.info("⚙️ Paramètres système à venir")

# ============================================
# TAB COTATION (TOUT LE CONTENU ACTUEL)
# ============================================
with tab_cotation:
    st.title("Cotation Santé +")

    tab_liste, tab_particulier, tab_corporate = st.tabs([
        "Liste des cotations",
        "Parcours Particulier (Taxe 8%)", 
        "Parcours Corporate (Taxe 3%)"
    ])
    
    # --- LISTE DES COTATIONS ---
    with tab_liste:
        st.subheader("📋 Liste des Cotations")
        st.markdown("Toutes les cotations effectuées")
        st.markdown("---")
        
        # Données fictives réalistes
        import pandas as pd
        from datetime import datetime, timedelta
        import random
        
        # Générer 20 cotations fictives
        data_cotations = []
        
        noms_clients_part = [
            "Kouassi Jean-Baptiste", "Yao Marie-Louise", "Diabaté Ibrahim",
            "N'Guessan Aya", "Koné Abdoulaye", "Traoré Aminata",
            "Bamba Sylvie", "Ouattara Moussa", "Séka Patricia"
        ]
        
        noms_clients_corp = [
            "SARL IVOIRE TECH", "Entreprise BATIMAT CI", "SCI IMMOBILIÈRE PLUS",
            "SA DISTRIBUTION EXPORT", "SARL AGRO BUSINESS", "Société LOGISTIQUE EXPRESS",
            "Entreprise BTP CONSTRUCTION", "SA TELECOM SERVICES"
        ]
        
        courtiers = [
            "ABC Courtage", "XYZ Assurances Conseil", "DEF Brokers International",
            "GHI Assurance Partners", "JKL Courtage Plus", "MNO Insurance Group"
        ]
        
        utilisateurs = ["Alice Kouadio", "Bernard Sanogo", "Christine Yao", "David Koné"]
        
        statuts = ["Finalisé", "En cours", "Finalisé", "Finalisé", "En attente", "Annulé"]
        
        # Générer les données
        for i in range(20):
            is_corporate = i % 3 == 0  # 1/3 corporate, 2/3 particulier
            
            if is_corporate:
                branche = "Corporate"
                client = random.choice(noms_clients_corp)
                nb_beneficiaires = random.randint(5, 50)
                prime_base = random.randint(800000, 5000000)
            else:
                branche = "Particulier"
                client = random.choice(noms_clients_part)
                nb_beneficiaires = random.choice([1, 4, 5, 6])
                prime_base = random.randint(150000, 3000000)
            
            duree = random.choice([6, 9, 12])
            date_creation = datetime.now() - timedelta(days=random.randint(1, 90))
            statut = random.choice(statuts)
            
            # Prix sans taxe
            prix_ht = int(prime_base * 0.92)
            
            data_cotations.append({
                "id": i,
                "N° Cotation": f"COT-2025-{1100 + i:04d}",
                "Branche": branche,
                "Nom client": client,
                "Courtier": random.choice(courtiers),
                "Utilisateur": random.choice(utilisateurs),
                "Durée": f"{duree} mois",
                "Prix": f"{prix_ht:,} FCFA",
                "Coût Total": f"{prime_base:,} FCFA",
                "Créé le": date_creation.strftime("%d/%m/%Y"),
                "Statut": statut
            })
        
        # Statistiques en haut
        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        
        with col_stat1:
            st.metric("📊 Total", len(data_cotations), "20 cotations")
        
        with col_stat2:
            nb_finalise = len([c for c in data_cotations if c['Statut'] == 'Finalisé'])
            st.metric("✅ Finalisées", nb_finalise, f"{int(nb_finalise/len(data_cotations)*100)}%")
        
        with col_stat3:
            nb_en_cours = len([c for c in data_cotations if c['Statut'] == 'En cours'])
            st.metric("⏳ En cours", nb_en_cours, f"{int(nb_en_cours/len(data_cotations)*100)}%")
        
        with col_stat4:
            prime_totale = sum([int(c['Coût Total'].replace(',', '').replace(' FCFA', '')) for c in data_cotations])
            st.metric("💰 Volume Total", f"{prime_totale/1000000:.1f}M FCFA")
        
        st.markdown("---")
        
        # CSS pour le tableau personnalisé
        st.markdown("""
            <style>
            /* Table container */
            .custom-table-container {
                max-height: 600px;
                overflow-y: auto;
                border: 1px solid #dee2e6;
                border-radius: 0.5rem;
            }
            
            /* Table */
            .custom-table {
                width: 100%;
                border-collapse: collapse;
                font-size: 10px; /* Taille par défaut pour les en-têtes */
            }
            
            /* Headers - Fond personnalisé */
            .custom-table thead tr {
                background-color: #145d33; /* Couleur verte foncée */
                color: white;
                position: sticky;
                top: 0;
                z-index: 10;
            }
            
            .custom-table thead th {
                padding: 12px 8px;
                text-align: left;
                font-weight: 600;
                border-bottom: 2px solid #dee2e6;
            }
            
            /* Lignes - Alternance */
            .custom-table tbody tr:nth-child(odd) {
                background-color: #ffffff;
            }
            
            .custom-table tbody tr:nth-child(even) {
                background-color: #f8f9fa;
            }
            
            /* Hover */
            .custom-table tbody tr:hover {
                background-color: #e3f2fd;
            }
            
            /* Cellules du contenu - AJUSTEMENT DE LA TAILLE ICI */
            .custom-table tbody td {
                padding: 10px 8px;
                color: #495057;
                border-bottom: 1px solid #e9ecef;
                font-size: 8px; /* <-- TAILLE PLUS PETITE POUR LE CONTENU */
            }
            
            /* Style des selectbox dans le tableau */
            .custom-table select {
                padding: 4px 8px;
                border: 1px solid #ced4da;
                border-radius: 0.25rem;
                background-color: white;
                font-size: 0.8rem;
                cursor: pointer;
                min-width: 160px;
            }
            
            .custom-table select:hover {
                border-color: #2196F3;
            }
            
            .custom-table select:focus {
                outline: none;
                border-color: #2196F3;
                box-shadow: 0 0 0 0.2rem rgba(33, 150, 243, 0.25);
            }
            
            /* Badges de statut */
            .badge-finalise {
                background-color: #28a745;
                color: white;
                padding: 4px 8px;
                border-radius: 0.25rem;
                font-size: 0.75rem;
                font-weight: 500;
            }
            
            .badge-en-cours {
                background-color: #ffc107;
                color: #000;
                padding: 4px 8px;
                border-radius: 0.25rem;
                font-size: 0.75rem;
                font-weight: 500;
            }
            
            .badge-en-attente {
                background-color: #17a2b8;
                color: white;
                padding: 4px 8px;
                border-radius: 0.25rem;
                font-size: 0.75rem;
                font-weight: 500;
            }
            
            .badge-annule {
                background-color: #dc3545;
                color: white;
                padding: 4px 8px;
                border-radius: 0.25rem;
                font-size: 0.75rem;
                font-weight: 500;
            }
            </style>
        """, unsafe_allow_html=True)
        
        # Afficher le tableau avec selectbox par ligne
        st.markdown('<div class="custom-table-container">', unsafe_allow_html=True)
        st.markdown("""
            <table class="custom-table">
                <thead>
                    <tr>
                        <th>N° Cotation</th>
                        <th>Branche</th>
                        <th>Nom client</th>
                        <th>Courtier</th>
                        <th>Utilisateur</th>
                        <th>Durée</th>
                        <th>Prix</th>
                        <th>Coût Total</th>
                        <th>Créé le</th>
                        <th>Statut</th>
                        <th>Options</th>
                    </tr>
                </thead>
            </table>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Afficher les lignes avec actions interactives
        for idx, cotation in enumerate(data_cotations):
            with st.container():
                cols = st.columns([1.2, 0.8, 1.5, 1.2, 1.2, 0.7, 1.2, 1.2, 0.9, 0.9, 1.5])
                
                # Appliquer l'alternance de couleur
                bg_color = "#ffffff" if idx % 2 == 0 else "#f8f9fa"
                
                with cols[0]:
                    st.markdown(f"<div style='background-color: {bg_color}; padding: 10px 8px;'>{cotation['N° Cotation']}</div>", unsafe_allow_html=True)
                
                with cols[1]:
                    st.markdown(f"<div style='background-color: {bg_color}; padding: 10px 8px;'>{cotation['Branche']}</div>", unsafe_allow_html=True)
                
                with cols[2]:
                    st.markdown(f"<div style='background-color: {bg_color}; padding: 10px 8px;'>{cotation['Nom client']}</div>", unsafe_allow_html=True)
                
                with cols[3]:
                    st.markdown(f"<div style='background-color: {bg_color}; padding: 10px 8px;'>{cotation['Courtier']}</div>", unsafe_allow_html=True)
                
                with cols[4]:
                    st.markdown(f"<div style='background-color: {bg_color}; padding: 10px 8px;'>{cotation['Utilisateur']}</div>", unsafe_allow_html=True)
                
                with cols[5]:
                    st.markdown(f"<div style='background-color: {bg_color}; padding: 10px 8px;'>{cotation['Durée']}</div>", unsafe_allow_html=True)
                
                with cols[6]:
                    st.markdown(f"<div style='background-color: {bg_color}; padding: 10px 8px;'>{cotation['Prix']}</div>", unsafe_allow_html=True)
                
                with cols[7]:
                    st.markdown(f"<div style='background-color: {bg_color}; padding: 10px 8px;'>{cotation['Coût Total']}</div>", unsafe_allow_html=True)
                
                with cols[8]:
                    st.markdown(f"<div style='background-color: {bg_color}; padding: 10px 8px;'>{cotation['Créé le']}</div>", unsafe_allow_html=True)
                
                with cols[9]:
                    # Badge de statut
                    statut = cotation['Statut']
                    if statut == "Finalisé":
                        badge_class = "badge-finalise"
                        icon = "✅"
                    elif statut == "En cours":
                        badge_class = "badge-en-cours"
                        icon = "⏳"
                    elif statut == "En attente":
                        badge_class = "badge-en-attente"
                        icon = "⏸️"
                    else:  # Annulé
                        badge_class = "badge-annule"
                        icon = "❌"
                    
                    st.markdown(f"<div style='background-color: {bg_color}; padding: 10px 8px;'><span class='{badge_class}'>{icon} {statut}</span></div>", unsafe_allow_html=True)
                
                with cols[10]:
                    # Liste déroulante d'actions pour cette ligne
                    action = st.selectbox(
                        "Action",
                        ["-- Choisir --", "💳 Paiement", "📥 Télécharger", "✏️ Modifier"],
                        key=f"action_{cotation['id']}",
                        label_visibility="collapsed"
                    )
                    
                    # Traiter l'action si sélectionnée
                    if action != "-- Choisir --":
                        if action == "💳 Paiement":
                            st.success(f"Paiement {cotation['N° Cotation']}")
                            st.info(f"Montant: {cotation['Coût Total']}")
                        elif action == "📥 Télécharger":
                            st.success(f"Téléchargement {cotation['N° Cotation']}")
                        elif action == "✏️ Modifier":
                            st.warning(f"Modification {cotation['N° Cotation']}")
        
        # Légende des statuts en bas
        st.markdown("---")
        st.markdown("### Légende des statuts")
        col_leg1, col_leg2, col_leg3, col_leg4 = st.columns(4)
        
        with col_leg1:
            st.markdown("**✅ Finalisé** : Cotation validée et envoyée au client")
        
        with col_leg2:
            st.markdown("**⏳ En cours** : Cotation en cours de traitement")
        
        with col_leg3:
            st.markdown("**⏸️ En attente** : En attente d'informations complémentaires")
        
        with col_leg4:
            st.markdown("**❌ Annulé** : Cotation annulée par le client ou l'utilisateur")

    # --- PARCOURS PARTICULIER ---
    with tab_particulier:
        st.markdown("---")
        
        st.markdown("<h3 style='color: #6A0DAD;'>1. Profil & Données de Couverture</h3>", unsafe_allow_html=True)
        with st.container(border=True):
            col_a, col_b, col_c = st.columns([1.5, 1, 1])
            
            # Système d'ajout de barèmes pour les deux types de cotation
            st.markdown("**Gestion des Barèmes**")
            
            # Initialiser la liste des barèmes dans session_state si nécessaire
            if 'baremes_selectionnes_list' not in st.session_state:
                st.session_state.baremes_selectionnes_list = []
            
            # Interface d'ajout
            col_select, col_add = st.columns([3, 1])
            
            with col_select:
                bareme_a_ajouter = st.selectbox(
                    "Sélectionner un barème à ajouter",
                    list(PRODUITS_PARTICULIERS_UI.keys()),
                    format_func=lambda x: PRODUITS_PARTICULIERS_UI[x],
                    key="bareme_a_ajouter"
                )
            
            with col_add:
                st.markdown("<br>", unsafe_allow_html=True)  # Espaceur pour alignement
                if st.button("➕ Ajouter", key="btn_add_bareme", use_container_width=True):
                    st.session_state.baremes_selectionnes_list.append(bareme_a_ajouter)
                    st.rerun()
            
            # Affichage de la liste des barèmes sélectionnés
            if st.session_state.baremes_selectionnes_list:
                st.markdown("**Barèmes Sélectionnés :**")
                
                baremes_a_supprimer = []
                for idx, bareme_key in enumerate(st.session_state.baremes_selectionnes_list):
                    col_bareme, col_btn = st.columns([4, 1])
                    with col_bareme:
                        st.markdown(f"{idx + 1}. **{PRODUITS_PARTICULIERS_UI[bareme_key]}**")
                    with col_btn:
                        if st.button("🗑️", key=f"btn_remove_{idx}", help="Supprimer ce barème"):
                            baremes_a_supprimer.append(idx)
                
                # Supprimer les barèmes marqués
                for idx in sorted(baremes_a_supprimer, reverse=True):
                    st.session_state.baremes_selectionnes_list.pop(idx)
                    st.rerun()
                
                st.success(f"✓ **{len(st.session_state.baremes_selectionnes_list)} barème(s)** → Propositions séparées")
                
                baremes_selectionnes = st.session_state.baremes_selectionnes_list
            else:
                st.warning("⚠️ Aucun barème sélectionné. Cliquez sur '➕ Ajouter' pour commencer.")
                baremes_selectionnes = []
        
        # Configuration spécifique par barème (pour les deux types de cotation)
        configurations_baremes = {}
        
        type_cotation = "Une cotation, différentes propositions"
        
        if baremes_selectionnes and len(baremes_selectionnes) > 0:
            
            st.markdown("---")
            st.markdown("**⚙️ Configuration par Barème**")
            st.caption("Choisissez le type de couverture et le nombre d'enfants supplémentaires pour chaque barème")
            
            for idx, produit_key in enumerate(baremes_selectionnes):
                with st.expander(f"🔹 **{idx+1}. {PRODUITS_PARTICULIERS_UI[produit_key]}**", expanded=True):
                    col_conf1, col_conf2 = st.columns(2)
                    
                    type_couv_bareme = col_conf1.selectbox(
                        "Type de Couverture",
                        options=["Personne seule", "Famille"],
                        index=0,
                        key=f"couverture_bareme_{idx}",
                    )
                    
                    enfants_supp_bareme = 0
                    if type_couv_bareme == "Famille":
                        enfants_supp_bareme = col_conf2.number_input(
                            "Enfants Supplémentaires",
                            min_value=0,
                            max_value=MAX_ENFANTS_SUPPLEMENTAIRES,
                            step=1,
                            value=0,
                            key=f"enfants_bareme_{idx}",
                        )
                    
                    # Stocker la configuration (utiliser index comme clé)
                    configurations_baremes[idx] = {
                        'produit_key': produit_key,
                        'type_couverture': type_couv_bareme,
                        'enfants_supp': enfants_supp_bareme
                    }
                    
                    # Afficher l'estimation
                    if produit_key == 'bareme_special':
                        st.info("💡 Saisie manuelle de la prime nette requise")
                    else:
                        tarif_part = TARIFS_PARTICULIERS[produit_key]
                        config_part = tarif_part['famille'] if type_couv_bareme == 'Famille' else tarif_part['personne_seule']
                        prime_nette_base_simu = config_part['prime_nette']
                        
                        if enfants_supp_bareme > 0:
                            prime_nette_base_simu += tarif_part['enfant_supplementaire']['prime_nette'] * enfants_supp_bareme
                        
                        type_label = "Famille" if type_couv_bareme == "Famille" else "Personne seule"
                        enfants_label = f" + {enfants_supp_bareme} enfant(s) supp." if enfants_supp_bareme > 0 else ""
                        
                        st.success(
                            f"💡 **{type_label}{enfants_label}** : "
                            f"{format_currency(prime_nette_base_simu)} (avant ajustements)"
                        )
        
        # Pour le mode simple, créer une configuration unique
        if type_cotation == "Une cotation, une proposition":
            
            if baremes_selectionnes:
                produit_key = baremes_selectionnes[0]
                
                config_temp = configurations_baremes.get(0, {'type_couverture': 'Personne seule', 'enfants_supp': 0})
                type_couverture = config_temp['type_couverture']
                enfants_supp = config_temp['enfants_supp']

                configurations_baremes = {
                    0: {
                        'produit_key': produit_key,
                        'type_couverture': type_couverture,
                        'enfants_supp': enfants_supp
                    }
                }
                
                if produit_key == 'bareme_special':
                    st.info(
                        "💡 **BARÈME SPÉCIAL** : Vous saisirez manuellement la prime nette et les accessoires "
                        "à la fin du processus, avant le calcul de la prime TTC."
                    )
                else:
                    tarif_part = TARIFS_PARTICULIERS[produit_key]
                    config_part = tarif_part['famille'] if type_couverture == 'Famille' else tarif_part['personne_seule']
                    prime_nette_base_simu = config_part['prime_nette']
                    
                    if enfants_supp > 0:
                        prime_nette_base_simu += tarif_part['enfant_supplementaire']['prime_nette'] * enfants_supp
                        
                        st.info(
                            f"💡 Prime Nette de Base : **{format_currency(prime_nette_base_simu)}** "
                            f"(avant ajustements risque/grossesse/durée)"
                        )
        
        # 2. Analyse Médicale & Surprimes
        st.markdown("<h3 style='color: #6A0DAD;'>2. Analyse Médicale & Surprimes</h3>", unsafe_allow_html=True)
        
        # Structure pour stocker les infos médicales par barème
        infos_medicales_par_bareme = {}
        # Mode médical par barème activé automatiquement pour "différentes propositions"
        mode_medical_par_bareme = (type_cotation == "Une cotation, différentes propositions")
        
        # CAS SPÉCIAL : MODE PAR BARÈME
        if mode_medical_par_bareme:
            st.info("📋 **Mode Personnalisé** : Questionnaire médical complet et détaillé adapté pour chaque barème")
            st.caption("⏱️ Ce mode nécessite plus de temps mais permet une cotation précise par barème")
            
            for idx, produit_key in enumerate(baremes_selectionnes):
                config_bareme = configurations_baremes.get(idx, {})
                type_couv_b = config_bareme.get('type_couverture', 'Personne seule')
                enfants_supp_b = config_bareme.get('enfants_supp', 0)
                
                st.markdown("---")
                st.markdown(f"### 🩺 Barème {idx + 1} : {PRODUITS_PARTICULIERS_UI[produit_key]}")

                # ============================================================================
                # MODIFICATION 3 AMÉLIORÉE: Case à cocher pour réutiliser les infos entre barèmes
                # ============================================================================
                
                # Case à cocher pour réutiliser les infos du barème précédent
                if idx > 0:  # À partir du barème 2
                    st.markdown("---")
                    
                    # Vérifier si des infos existent pour le barème précédent
                    config_precedent = configurations_baremes.get(idx-1, {})
                    type_couv_precedent = config_precedent.get('type_couverture', 'Personne seule')
                    infos_precedent = infos_medicales_par_bareme.get(idx-1, {})
                    
                    # Vérifier la compatibilité des types de couverture
                    if type_couv_precedent == type_couv_b:
                        # Initialiser la clé de copie si elle n'existe pas
                        copy_key = f"copie_effectuee_b{idx}"
                        if copy_key not in st.session_state:
                            st.session_state[copy_key] = False
                        
                        # Case à cocher pour copier les infos
                        copier_infos = st.checkbox(
                            f"📥 Copier les informations de l'assuré du Barème {idx} ({type_couv_precedent})",
                            key=f"checkbox_copier_bareme_{idx}",
                            help=f"Cochez pour pré-remplir automatiquement avec les informations médicales de l'assuré du Barème {idx}",
                            value=st.session_state[copy_key]
                        )
                        
                        # Si la case vient d'être cochée (changement d'état)
                        if copier_infos and not st.session_state[copy_key]:
                            if infos_precedent:
                                # Marquer la copie comme effectuée
                                st.session_state[copy_key] = True
                                
                                # Copier les informations dans infos_medicales_par_bareme
                                infos_medicales_par_bareme[idx] = infos_precedent.copy()
                                
                                # Copier dans session_state pour pré-remplir les champs
                                if type_couv_b == "Personne seule":
                                    # Copier TOUS les champs personne seule (identité + médical)
                                    champs_a_copier = [
                                        'nom', 'prenom', 'date_naissance', 'lieu_naissance',
                                        'contact', 'numero_cnam', 'nationalite', 'etat_civil',
                                        'taille', 'poids', 'imc', 'tension', 'emploi',
                                        'affections', 'grossesse', 'montant_grossesse'
                                    ]
                                    for key in champs_a_copier:
                                        old_key = f"{key}_ps_b{idx-1}"
                                        new_key = f"{key}_ps_b{idx}"
                                        if old_key in st.session_state:
                                            st.session_state[new_key] = st.session_state[old_key]
                                
                                elif type_couv_b == "Famille":
                                    # Copier TOUS les champs de tous les membres de la famille
                                    champs_a_copier = [
                                        'nom', 'prenom', 'date_naissance', 'lieu_naissance',
                                        'contact', 'numero_cnam', 'nationalite', 'etat_civil',
                                        'taille', 'poids', 'imc', 'tension', 'emploi',
                                        'affections', 'grossesse', 'montant_grossesse'
                                    ]
                                    
                                    # Adultes 1 et 2
                                    for adulte_num in [1, 2]:
                                        for key in champs_a_copier:
                                            old_key = f"{key}_a{adulte_num}_b{idx-1}"
                                            new_key = f"{key}_a{adulte_num}_b{idx}"
                                            if old_key in st.session_state:
                                                st.session_state[new_key] = st.session_state[old_key]
                                    
                                    # Enfants (tous les champs sauf grossesse/montant_grossesse)
                                    nb_enfants = 3 + enfants_supp_b
                                    champs_enfants = [
                                        'nom', 'prenom', 'date_naissance', 'lieu_naissance',
                                        'contact', 'numero_cnam', 'nationalite', 'etat_civil',
                                        'taille', 'poids', 'imc', 'tension', 'emploi', 'affections'
                                    ]
                                    for enfant_num in range(1, nb_enfants + 1):
                                        for key in champs_enfants:
                                            old_key = f"{key}_e{enfant_num}_b{idx-1}"
                                            new_key = f"{key}_e{enfant_num}_b{idx}"
                                            if old_key in st.session_state:
                                                st.session_state[new_key] = st.session_state[old_key]
                                
                                st.success(f"✅ Toutes les informations de l'assuré du Barème {idx} ont été copiées (identité + infos médicales)")
                                st.rerun()  # Recharger pour afficher les champs copiés
                            else:
                                st.warning(f"⚠️ Veuillez d'abord saisir les informations de l'assuré dans le Barème {idx}")
                        
                        # Si la case est cochée, afficher un message
                        elif copier_infos and st.session_state[copy_key]:
                            st.info("ℹ️ Les informations du barème précédent sont utilisées. Vous pouvez les modifier si nécessaire.")
                    else:
                        st.info(
                            f"ℹ️ Le Barème {idx} est '{type_couv_precedent}' et le Barème {idx+1} est '{type_couv_b}'. "
                            f"La réutilisation n'est possible qu'entre barèmes de même type."
                        )
                    
                    st.markdown("---")
                
                # ============================================================================

                st.markdown(f"**Configuration :** {type_couv_b}" + (f" avec {enfants_supp_b} enfant(s) supplémentaire(s)" if enfants_supp_b > 0 else ""))
                
                # Collecter les infos médicales pour ce barème
                membres_bareme = []
                affections_bareme = []
                grossesse_bareme = False
                
                if type_couv_b == "Famille":
                    # QUESTIONNAIRE FAMILLE COMPLET
                    nb_enfants_total = 3 + enfants_supp_b
                    st.info(f"👥 **Composition :** 2 adultes + {nb_enfants_total} enfants")
                    st.markdown("#### Questionnaires Médicaux Individuels")
                    
                    # ADULTE 1
                    adulte1_data = display_member_form("Adulte", f"a1_b{idx}", is_principal=True, is_expanded=True)
                    if adulte1_data["exclusion"]:
                            st.error(f"⛔ **EXCLUSION** - {PRODUITS_PARTICULIERS_UI[produit_key]}")
                            st.stop()
                    affections_bareme.extend(adulte1_data["affections"])
                    
                    # ADULTE 2
                    adulte2_data = display_member_form("Adulte", f"a2_b{idx}")
                    if adulte2_data["exclusion"]:
                            st.error(f"⛔ **EXCLUSION** - {PRODUITS_PARTICULIERS_UI[produit_key]}")
                            st.stop()
                    affections_bareme.extend(adulte2_data["affections"])
                    if adulte2_data["grossesse"]:
                        grossesse_bareme = True
                        montant_grossesse_a2 = adulte2_data["montant_grossesse"]
                    
                    # ENFANTS
                    for num_enfant in range(1, nb_enfants_total + 1):
                        enfant_data = display_member_form("Enfant", f"e{num_enfant}_b{idx}")
                            # Validation de l'âge
                        age_e = calculer_age(enfant_data['date_naissance'])
                        if age_e > 25:
                                st.error(f"⚠️ **ATTENTION** : L'enfant {num_enfant} a {age_e} ans, ce qui dépasse la limite de 25 ans pour une cotation famille.")
                                st.stop()
                            
                        if enfant_data["exclusion"]:
                                st.error(f"⛔ **EXCLUSION** - {PRODUITS_PARTICULIERS_UI[produit_key]}")
                                st.stop()
                        affections_bareme.extend(enfant_data["affections"])
                
                else:
                    # QUESTIONNAIRE PERSONNE SEULE COMPLET
                    st.info("👤 **Composition :** 1 personne seule")
                    with st.container(border=True):
                        ps_data = display_member_form("Adulte", f"ps_b{idx}", is_principal=True)
                        if ps_data["exclusion"]:
                            st.error(f"⛔ **EXCLUSION** - {PRODUITS_PARTICULIERS_UI[produit_key]}")
                            st.stop()
                        affections_bareme.extend(ps_data["affections"])
                
                # Calculer le montant grossesse pour ce barème
                montant_grossesse_total = 0
                
                if type_couv_b == "Famille":
                    # Montant grossesse si applicable
                    if grossesse_bareme:
                        montant_grossesse_total = montant_grossesse_a2
                
                # Stocker les infos pour ce barème (utiliser index)
                infos_medicales_par_bareme[idx] = {
                    'produit_key': produit_key,
                    'affections': affections_bareme,
                    'grossesse': grossesse_bareme,
                    'montant_grossesse': montant_grossesse_total,
                    'type_couverture': type_couv_b,
                    'enfants_supp': enfants_supp_b
                }
            
            # Champ Surprime Globale (appliquée à la prime nette finale)
            st.markdown("---")
            st.markdown("### 📊 Ajustement Final")
            
            col_surprime1, col_surprime2 = st.columns([2, 1])
            surprime_globale = col_surprime1.number_input(
                "Surprime Globale (%)",
                min_value=0.0,
                max_value=100.0,
                value=0.0,
                step=0.5,
                key="surprime_globale_multi",
                help="Taux de surprime appliqué à l'ensemble de la prime nette (après toutes les autres majorations)"
            )
            if surprime_globale > 0:
                col_surprime2.metric("Surprime", f"+{surprime_globale}%", delta="Appliquée au total")
            
            # Résumé global
            st.markdown("---")
            st.markdown("### 📋 Résumé Global des Configurations Médicales")
            resume_data = []
            for idx, infos in infos_medicales_par_bareme.items():
                produit_key = infos['produit_key']
                nb_affections = len(infos['affections'])
                resume_data.append({
                    'N°': idx + 1,
                    'Barème': PRODUITS_PARTICULIERS_UI[produit_key],
                    'Type Couverture': infos['type_couverture'],
                    'Nb Affections': nb_affections,
                    'Grossesse': "Oui" if infos['grossesse'] else "Non",
                    'Surprime Estimée': f"{sum(TAUX_MAJORATION_MEDICALE.get(aff, 0) for aff in infos['affections'])}%" +
                                       (f" + {SURPRIME_GROSSESSE}%" if infos['grossesse'] else "")
                })
            
            if resume_data:
                df_resume = pd.DataFrame(resume_data)
                st.dataframe(df_resume, use_container_width=True, hide_index=True)
                
                # Alerte si beaucoup d'affections
                total_affections = sum(len(infos['affections']) for infos in infos_medicales_par_bareme.values())
                if total_affections > 5:
                    st.warning(f"⚠️ **Attention** : {total_affections} affection(s) chronique(s) déclarée(s) au total. Les surprimes pourraient être significatives.")
        
        # CAS NORMAL : MODE CLASSIQUE (Code existant inchangé)
        else:
            # Déterminer le type de couverture pour la section médicale
            if baremes_selectionnes:
                config_initial = configurations_baremes.get(0, {'type_couverture': 'Personne seule', 'enfants_supp': 0})
                type_couverture_medical = config_initial['type_couverture']
                enfants_supp_medical = config_initial['enfants_supp']
            else:
                type_couverture_medical = "Personne seule"
                enfants_supp_medical = 0

            # Déterminer le nombre de membres de la famille
            nb_adultes = 2 if type_couverture_medical == "Famille" else 1
            # Pour les familles, on a toujours 3 enfants inclus dans le tarif famille de base
            nb_enfants_famille = 3 if type_couverture_medical == "Famille" else 0
            nb_total_membres = nb_adultes + nb_enfants_famille + enfants_supp_medical
            
            if type_couverture_medical == "Famille":
                st.info(
                    f"👥 **Composition de la famille :** {nb_adultes} adulte(s) + "
                    f"{nb_enfants_famille} enfant(s) inclus" +
                    (f" + {enfants_supp_medical} enfant(s) supplémentaire(s)" if enfants_supp_medical > 0 else "")
                )
            
            # Collecter les informations médicales de chaque membre
            membres_famille = []
            affections_globales = []
            grossesse_detectee = False
            
            # Si Famille : questionnaires individuels
            if type_couverture_medical == "Famille":
                st.markdown("#### Questionnaires Médicaux Individuels")
                st.caption("Remplissez le questionnaire pour chaque membre de la famille (⚠️ Enfants : 25 ans maximum)")
    
                
                # Adulte 1
                with st.expander("👤 Adulte 1 (Assuré Principal)", expanded=True):
                    st.markdown("**Informations Personnelles**")
                    col_nom1, col_nom2 = st.columns(2)
                    
                    nom_a1 = col_nom1.text_input(
                        "Nom",
                        key="nom_adulte1",
                        help="Nom de famille de l'assuré"
                    )
                    
                    prenom_a1 = col_nom2.text_input(
                        "Prénom(s)",
                        key="prenom_adulte1",
                        help="Prénom(s) de l'assuré"
                    )
                    
                    col_info1, col_info2, col_info3 = st.columns(3)
                    
                    date_naissance_a1 = col_info1.date_input(
                        "Date de naissance",
                        value=datetime(1980, 1, 1).date(),
                        min_value=datetime(1900, 1, 1).date(),
                        max_value=datetime.now().date(),
                        key="date_naissance_adulte1",
                        help="Sélectionnez la date de naissance"
                    )
                    
                    lieu_naissance_a1 = col_info2.text_input(
                        "Lieu de naissance",
                        key="lieu_naissance_adulte1",
                        help="Ville ou lieu de naissance"
                    )
                    
                    contact_a1 = col_info3.text_input(
                        "Contact",
                        key="contact_adulte1",
                        help="Numéro de téléphone",
                        placeholder="+225 XX XX XX XX XX"
                    )
                    
                    col_info4, col_info5, col_info6 = st.columns(3)
                    
                    numero_cnam_a1 = col_info4.text_input(
                        "Numéro CNAM",
                        key="numero_cnam_adulte1",
                        help="Numéro d'identification CNAM"
                    )
                    
                    nationalite_a1 = col_info5.text_input(
                        "Nationalité",
                        key="nationalite_adulte1",
                        value="Ivoirienne",
                        help="Nationalité de l'assuré"
                    )
                    
                    etat_civil_a1 = col_info6.selectbox(
                        "État civil",
                        options=["Célibataire", "Marié(e)", "Divorcé(e)", "Conjoint de fait", "Veuf/veuve"],
                        key="etat_civil_adulte1",
                        help="Situation matrimoniale"
                    )
                    
                    col_info7, col_info8, col_info9 = st.columns(3)
                    
                    taille_a1 = col_info7.number_input(
                        "Taille (cm)",
                        min_value=50,
                        max_value=250,
                        value=170,
                        key="taille_adulte1",
                        help="Taille en centimètres"
                    )
                    
                    poids_a1 = col_info8.number_input(
                        "Poids (kg)",
                        min_value=20,
                        max_value=250,
                        value=70,
                        key="poids_adulte1",
                        help="Poids en kilogrammes"
                    )
                    
                    # Calcul et affichage de l'IMC
                    imc_a1, interpretation_imc_a1 = calculer_imc(poids_a1, taille_a1)
                    col_info9.metric(
                        "IMC",
                        f"{imc_a1}",
                        interpretation_imc_a1
                    )
                    
                    tension_a1 = st.text_input(
                        "Tension artérielle",
                        key="tension_adulte1",
                        value="12/8",
                        help="Format: 12/8",
                        placeholder="12/8"
                    )
                    
                    emploi_a1 = st.text_input(
                        "Emploi actuel",
                        key="emploi_adulte1",
                        help="Poste ou profession actuelle",
                        placeholder="Ex: Directeur Commercial"
                    )
                    
                    st.markdown("---")
                    st.markdown("**Informations Médicales**")
                    col_a1_1, col_a1_2 = st.columns(2)
                    
                    affections_a1 = col_a1_1.multiselect(
                        "Affections Chroniques Déclarées",
                        options=LISTE_AFFECTIONS,
                        key="affections_adulte1",
                        help="Sélectionnez toutes les affections applicables",
                        on_change=reset_results
                    )
                    
                    if affections_a1:
                        taux_cumul_a1 = sum(TAUX_MAJORATION_MEDICALE[aff] for aff in affections_a1)
                        col_a1_1.success(f"✓ Surprime cumulative : **{taux_cumul_a1}%**")
                        affections_globales.extend(affections_a1)
                    
                    exclusion_a1 = col_a1_2.checkbox(
                        f"Affection Bloquante ({', '.join(AFF_EXCLUES)})",
                        key="exclusion_adulte1",
                        help="Cancer ou AVC nécessitent une soumission manuelle"
                    )
                    
                    if exclusion_a1:
                        st.error("⛔ **EXCLUSION DÉTECTÉE** pour l'Adulte 1")
                        st.stop()
                    
                    grossesse_a1 = col_a1_2.checkbox(
                        "Grossesse en cours",
                        key="grossesse_adulte1",
                        help=f"Ajout forfaitaire de {format_currency(SURPRIME_FORFAITAIRE_GROSSESSE)}"
                    )
                    
                    if grossesse_a1:
                        grossesse_detectee = True
                    
                    membres_famille.append({
                        'type': 'Adulte 1',
                        'affections': affections_a1,
                        'grossesse': grossesse_a1,
                        'exclusion': exclusion_a1
                    })
                
                # Adulte 2
                with st.expander("👤 Adulte 2 (Conjoint)", expanded=True):
                    st.markdown("**Informations Personnelles**")
                    col_nom1, col_nom2 = st.columns(2)
                    
                    nom_a2 = col_nom1.text_input(
                        "Nom",
                        key="nom_adulte2",
                        help="Nom de famille du conjoint"
                    )
                    
                    prenom_a2 = col_nom2.text_input(
                        "Prénom(s)",
                        key="prenom_adulte2",
                        help="Prénom(s) du conjoint"
                    )
                    
                    col_info1, col_info2, col_info3 = st.columns(3)
                    
                    date_naissance_a2 = col_info1.date_input(
                        "Date de naissance",
                        value=datetime(1985, 1, 1).date(),
                        min_value=datetime(1900, 1, 1).date(),
                        max_value=datetime.now().date(),
                        key="date_naissance_adulte2",
                        help="Sélectionnez la date de naissance"
                    )
                    
                    lieu_naissance_a2 = col_info2.text_input(
                        "Lieu de naissance",
                        key="lieu_naissance_adulte2",
                        help="Ville ou lieu de naissance"
                    )
                    
                    contact_a2 = col_info3.text_input(
                        "Contact",
                        key="contact_adulte2",
                        help="Numéro de téléphone",
                        placeholder="+225 XX XX XX XX XX"
                    )
                    
                    col_info4, col_info5, col_info6 = st.columns(3)
                    
                    numero_cnam_a2 = col_info4.text_input(
                        "Numéro CNAM",
                        key="numero_cnam_adulte2",
                        help="Numéro d'identification CNAM"
                    )
                    
                    nationalite_a2 = col_info5.text_input(
                        "Nationalité",
                        key="nationalite_adulte2",
                        value="Ivoirienne",
                        help="Nationalité de l'assuré"
                    )
                    
                    etat_civil_a2 = col_info6.selectbox(
                        "État civil",
                        options=["Célibataire", "Marié(e)", "Divorcé(e)", "Conjoint de fait", "Veuf/veuve"],
                        index=1,  # Par défaut "Marié(e)" pour le conjoint
                        key="etat_civil_adulte2",
                        help="Situation matrimoniale"
                    )
                    
                    col_info7, col_info8, col_info9 = st.columns(3)
                    
                    taille_a2 = col_info7.number_input(
                        "Taille (cm)",
                        min_value=50,
                        max_value=250,
                        value=165,
                        key="taille_adulte2",
                        help="Taille en centimètres"
                    )
                    
                    poids_a2 = col_info8.number_input(
                        "Poids (kg)",
                        min_value=20,
                        max_value=250,
                        value=65,
                        key="poids_adulte2",
                        help="Poids en kilogrammes"
                    )
                    
                    # Calcul et affichage de l'IMC
                    imc_a2, interpretation_imc_a2 = calculer_imc(poids_a2, taille_a2)
                    col_info9.metric(
                        "IMC",
                        f"{imc_a2}",
                        interpretation_imc_a2
                    )
                    
                    tension_a2 = st.text_input(
                        "Tension artérielle",
                        key="tension_adulte2",
                        value="12/8",
                        help="Format: 12/8",
                        placeholder="12/8"
                    )
                    
                    emploi_a2 = st.text_input(
                        "Emploi actuel",
                        key="emploi_adulte2",
                        help="Poste ou profession actuelle",
                        placeholder="Ex: Enseignant(e)"
                    )
                    
                    st.markdown("---")
                    st.markdown("**Informations Médicales**")
                    col_a2_1, col_a2_2 = st.columns(2)
                    
                    affections_a2 = col_a2_1.multiselect(
                        "Affections Chroniques Déclarées",
                        options=LISTE_AFFECTIONS,
                        key="affections_adulte2",
                        help="Sélectionnez toutes les affections applicables",
                        on_change=reset_results
                    )
                    
                    if affections_a2:
                        taux_cumul_a2 = sum(TAUX_MAJORATION_MEDICALE[aff] for aff in affections_a2)
                        col_a2_1.success(f"✓ Surprime cumulative : **{taux_cumul_a2}%**")
                        affections_globales.extend(affections_a2)
                    
                    exclusion_a2 = col_a2_2.checkbox(
                        f"Affection Bloquante ({', '.join(AFF_EXCLUES)})",
                        key="exclusion_adulte2",
                        help="Cancer ou AVC nécessitent une soumission manuelle"
                    )
                    
                    if exclusion_a2:
                        st.error("⛔ **EXCLUSION DÉTECTÉE** pour l'Adulte 2")
                        st.stop()
                    
                    grossesse_a2 = col_a2_2.checkbox(
                        "Grossesse en cours",
                        key="grossesse_adulte2",
                        help=f"Ajout forfaitaire de {format_currency(SURPRIME_FORFAITAIRE_GROSSESSE)}"
                    )
                    
                    if grossesse_a2:
                        grossesse_detectee = True
                    
                    membres_famille.append({
                        'type': 'Adulte 2',
                        'affections': affections_a2,
                        'grossesse': grossesse_a2,
                        'exclusion': exclusion_a2
                    })
                
                # Enfants (inclus + supplémentaires)
                total_enfants = nb_enfants_famille + enfants_supp_medical
                if total_enfants > 0:
                    for i in range(total_enfants):
                        num_enfant = i + 1
                        type_enfant = "Inclus" if i < nb_enfants_famille else "Supplémentaire"
                        
                        with st.expander(f"👶 Enfant {num_enfant} ({type_enfant})", expanded=(i < 2)):
                            st.markdown("**Informations Personnelles**")
                            col_nom1, col_nom2 = st.columns(2)
                            
                            nom_enfant = col_nom1.text_input(
                                "Nom",
                                key=f"nom_enfant{num_enfant}",
                                help="Nom de famille de l'enfant"
                            )
                            
                            prenom_enfant = col_nom2.text_input(
                                "Prénom(s)",
                                key=f"prenom_enfant{num_enfant}",
                                help="Prénom(s) de l'enfant"
                            )
                            
                            col_info1, col_info2, col_info3 = st.columns(3)
                            
                            date_naissance_enfant = col_info1.date_input(
                                "Date de naissance",
                                value=datetime(2015, 1, 1).date(),
                                min_value=datetime(1990, 1, 1).date(),
                                max_value=datetime.now().date(),
                                key=f"date_naissance_enfant{num_enfant}",
                                help="Sélectionnez la date de naissance"
                            )
                            
                            # Validation de l'âge de l'enfant (max 25 ans)
                            is_valid_age, error_msg = valider_age_enfant(
                                date_naissance_enfant, 
                                nom_enfant=f"{prenom_enfant} {nom_enfant}" if (prenom_enfant or nom_enfant) else "",
                                numero_enfant=num_enfant
                            )
                            if not is_valid_age:
                                st.error(error_msg)
                            
                            lieu_naissance_enfant = col_info2.text_input(
                                "Lieu de naissance",
                                key=f"lieu_naissance_enfant{num_enfant}",
                                help="Ville ou lieu de naissance"
                            )
                            
                            contact_enfant = col_info3.text_input(
                                "Contact (optionnel)",
                                key=f"contact_enfant{num_enfant}",
                                help="Numéro de téléphone si applicable",
                                placeholder="+225 XX XX XX XX XX"
                            )
                            
                            col_info4, col_info5 = st.columns(2)
                            
                            numero_cnam_enfant = col_info4.text_input(
                                "Numéro CNAM",
                                key=f"numero_cnam_enfant{num_enfant}",
                                help="Numéro d'identification CNAM"
                            )
                            
                            niveau_etude_enfant = col_info5.selectbox(
                                "Niveau d'étude",
                                options=["Aucun", "Maternelle", "Primaire", "Collège", "Lycée", "Université"],
                                key=f"niveau_etude_enfant{num_enfant}",
                                help="Niveau scolaire actuel"
                            )
                            
                            col_info6, col_info7, col_info8 = st.columns(3)
                            
                            taille_enfant = col_info6.number_input(
                                "Taille (cm)",
                                min_value=40,
                                max_value=200,
                                value=100,
                                key=f"taille_enfant{num_enfant}",
                                help="Taille en centimètres"
                            )
                            
                            poids_enfant = col_info7.number_input(
                                "Poids (kg)",
                                min_value=5,
                                max_value=150,
                                value=20,
                                key=f"poids_enfant{num_enfant}",
                                help="Poids en kilogrammes"
                            )
                            
                            # Calcul et affichage de l'IMC pour l'enfant
                            imc_enfant, interpretation_imc_enfant = calculer_imc(poids_enfant, taille_enfant)
                            col_info8.metric(
                                "IMC",
                                f"{imc_enfant}",
                                interpretation_imc_enfant
                            )
                            
                            tension_enfant = st.text_input(
                                "Tension artérielle",
                                key=f"tension_enfant{num_enfant}",
                                value="10/6",
                                help="Format: 10/6",
                                placeholder="10/6"
                            )
                            
                            st.markdown("---")
                            st.markdown("**Informations Médicales**")
                            col_e1, col_e2 = st.columns(2)
                            
                            affections_enfant = col_e1.multiselect(
                                "Affections Chroniques Déclarées",
                                options=LISTE_AFFECTIONS,
                                key=f"affections_enfant{num_enfant}",
                                help="Sélectionnez toutes les affections applicables",
                                on_change=reset_results
                            )
                            
                            if affections_enfant:
                                taux_cumul_e = sum(TAUX_MAJORATION_MEDICALE[aff] for aff in affections_enfant)
                                col_e1.success(f"✓ Surprime cumulative : **{taux_cumul_e}%**")
                                affections_globales.extend(affections_enfant)
                            
                            exclusion_enfant = col_e2.checkbox(
                                f"Affection Bloquante ({', '.join(AFF_EXCLUES)})",
                                key=f"exclusion_enfant{num_enfant}",
                                help="Cancer ou AVC nécessitent une soumission manuelle"
                            )
                            
                            if exclusion_enfant:
                                st.error(f"⛔ **EXCLUSION DÉTECTÉE** pour l'Enfant {num_enfant}")
                                st.stop()
                            
                            membres_famille.append({
                                'type': f'Enfant {num_enfant}',
                                'affections': affections_enfant,
                                'grossesse': False,
                                'exclusion': exclusion_enfant
                            })
                
                # Résumé global des affections
                if affections_globales:
                    st.markdown("---")
                    st.markdown("#### 📊 Résumé des Affections Déclarées")
                    
                    # Compter les affections par membre
                    nb_membres_avec_affections = sum(1 for m in membres_famille if m['affections'])
                    
                    col_res1, col_res2 = st.columns(2)
                    col_res1.metric("Membres avec affections", f"{nb_membres_avec_affections}/{nb_total_membres}")
                    
                    # Calculer la surprime maximale (on prend le taux le plus élevé)
                    taux_cumul_global = sum(TAUX_MAJORATION_MEDICALE[aff] for aff in affections_globales)
                    col_res2.metric("Surprime Cumulative Appliquée", f"{taux_cumul_global}%")
                    
                    st.info(
                        "ℹ️ **Note :** La somme des taux de majoration de tous les membres "
                        "sera appliqué à la prime globale de la famille."
                    )
                
                # Utiliser les affections globales pour le calcul
                affections_declarees = affections_globales  # Dédupliquer
                grossesse = grossesse_detectee
                
            # Si Personne Seule : questionnaire unique
            else:
                with st.container(border=True):
                    ps_data = display_member_form("Adulte", "ps", is_principal=True, is_expanded=True)
                    date_naissance_ps = ps_data["date_naissance"]
                    affections_declarees = ps_data["affections"]
                    
                    if ps_data["exclusion"]:
                        st.error(
                            "⛔ **EXCLUSION DÉTECTÉE :** La souscription est bloquée (Cancer/AVC). "
                            "Ce dossier nécessite une soumission manuelle et une analyse médicale approfondie."
                        )
                        st.stop()
                    
                    grossesse = ps_data["grossesse"]
                    if grossesse:
                         st.info(f"Une surprime forfaitaire de {format_currency(SURPRIME_FORFAITAIRE_GROSSESSE)} sera appliquée.")
        
        # Durée du contrat (commune à tous les modes)
        st.markdown("---")
        with st.container(border=True):
            st.markdown("#### ⏱️ Durée du Contrat")
            duree_contrat = st.selectbox(
                "Durée du Contrat (Mois)",
                options=list(range(1, 13)),
                index=11,
                key="duree_part",
                help="≤6 mois : facteur 0.52 | >6 mois : facteur 1.0",
                on_change=reset_results
            )
        
        st.markdown("---")
            
        # 3. Calcul Final
        st.markdown("<h3 style='color: #6A0DAD;'>3. Calcul Final de la Prime</h3>", unsafe_allow_html=True)
        
        # Vérification: au moins un barème sélectionné
        if type_cotation == "Une cotation, différentes propositions" and not baremes_selectionnes:
            st.warning("⚠️ Veuillez sélectionner au moins un barème pour calculer les primes")
        else:
            # Gestion des barèmes spéciaux (saisie manuelle)
            primes_nettes_manuelles = {}
            accessoires_manuels_dict = {}
            
            # Vérifier si des barèmes spéciaux sont dans la sélection
            baremes_speciaux = [b for b in baremes_selectionnes if b == 'bareme_special']
            
            if baremes_speciaux:
                with st.container(border=True):
                    st.markdown("#### 💼 Saisie Manuelle des Informations (Barèmes Spéciaux)")
                    st.info(
                        "Pour les barèmes spéciaux, veuillez saisir manuellement toutes les informations requises."
                    )
                    
                    if 'baremes_speciaux_info' not in st.session_state:
                        st.session_state.baremes_speciaux_info = {}
                    
                    for bareme_key in baremes_speciaux:
                        st.markdown(f"**{PRODUITS_PARTICULIERS_UI[bareme_key]}**")
                        
                        st.markdown("**Informations de Garantie**")
                        col_plaf1, col_plaf2, col_taux = st.columns(3)
                        
                        plafond_personne = col_plaf1.number_input(
                            "Plafond par Personne (FCFA)",
                            min_value=0.0,
                            value=st.session_state.baremes_speciaux_info.get(bareme_key, {}).get('plafond_personne', 0.0),
                            step=100000.0,
                            key=f"plafond_personne_{bareme_key}",
                            help="Plafond annuel par personne"
                        )
                        
                        plafond_famille = col_plaf2.number_input(
                            "Plafond par Famille (FCFA)",
                            min_value=0.0,
                            value=st.session_state.baremes_speciaux_info.get(bareme_key, {}).get('plafond_famille', 0.0),
                            step=100000.0,
                            key=f"plafond_famille_{bareme_key}",
                            help="Plafond annuel par famille"
                        )
                        
                        taux_couverture = col_taux.number_input(
                            "Taux de Couverture (%)",
                            min_value=0.0,
                            max_value=100.0,
                            value=st.session_state.baremes_speciaux_info.get(bareme_key, {}).get('taux_couverture', 0.0),
                            step=5.0,
                            key=f"taux_couverture_{bareme_key}",
                            help="Taux de couverture en pourcentage"
                        )
                        
                        st.markdown("**Montants de Prime**")
                        col_man1, col_man2 = st.columns(2)
                        
                        prime_manuelle = col_man1.number_input(
                            "Prime Nette (FCFA)",
                            min_value=0.0,
                            value=0.0,
                            step=1000.0,
                            key=f"prime_nette_manuel_{bareme_key}",
                            help="Saisissez la prime nette calculée"
                        )
                        
                        accessoire_manuel = col_man2.number_input(
                            "Accessoires (FCFA)",
                            min_value=0.0,
                            value=10000.0,
                            step=1000.0,
                            key=f"accessoires_manuel_{bareme_key}",
                            help="Frais accessoires"
                        )
                        
                        st.session_state.baremes_speciaux_info[bareme_key] = {
                            'plafond_personne': plafond_personne,
                            'plafond_famille': plafond_famille,
                            'taux_couverture': taux_couverture
                        }
                        
                        primes_nettes_manuelles[bareme_key] = prime_manuelle
                        accessoires_manuels_dict[bareme_key] = accessoire_manuel
                        
                        if prime_manuelle == 0:
                            st.warning(f"⚠️ Veuillez saisir une prime nette pour {PRODUITS_PARTICULIERS_UI[bareme_key]}")
                        if plafond_personne == 0 or plafond_famille == 0 or taux_couverture == 0:
                            st.warning(f"⚠️ Veuillez compléter toutes les informations de garantie pour {PRODUITS_PARTICULIERS_UI[bareme_key]}")
                        
                        st.markdown("---")
            
            with st.container(border=True):
                reduction_commerciale = st.number_input(
                    "Réduction Commerciale (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=0.0,
                    step=0.5,
                    format="%.1f",
                    key="reduction_part",
                    help="Saisissez le pourcentage de réduction (nécessite une validation hiérarchique si > 10%)",
                    on_change=reset_results
                )
                
                if reduction_commerciale > 0:
                    if reduction_commerciale > 20:
                        st.error(
                            f"🚨 **RÉDUCTION EXCEPTIONNELLE DE {reduction_commerciale}%** - "
                            "**VALIDATION DIRECTION GÉNÉRALE OBLIGATOIRE**"
                        )
                    elif reduction_commerciale > 10:
                        st.warning(
                            f"⚠️ Réduction de {reduction_commerciale}% appliquée. "
                            "**VALIDATION MANAGER OBLIGATOIRE** avant finalisation."
                        )
                    else:
                        st.warning(
                            f"⚠️ Réduction de {reduction_commerciale}% appliquée. "
                            "Validation manager requise avant finalisation."
                        )
            
            # Champ Accessoire + (frais supplémentaires)
            with st.container(border=True):
                accessoire_plus = st.number_input(
                    "Accessoire + (FCFA)",
                    min_value=0.0,
                    value=0.0,
                    step=1000.0,
                    format="%.0f",
                    key="accessoire_plus_part",
                    help="Frais accessoires supplémentaires à ajouter au calcul (ex: frais de dossier, frais administratifs)",
                    on_change=reset_results
                )
                
                if accessoire_plus > 0:
                    st.info(f"ℹ️ Accessoire supplémentaire de {format_currency(accessoire_plus)} sera ajouté au calcul.")
                
                # Bouton vert avec CSS personnalisé
                st.markdown("""
                    <style>
                    #btn-calc-particulier button {
                        background-color: #28a745 !important;
                        color: white !important;
                        border: none !important;
                        padding: 0.75rem !important;
                        border-radius: 0.5rem !important;
                        font-weight: 600 !important;
                        width: 100% !important;
                        cursor: pointer !important;
                    }
                    #btn-calc-particulier button:hover {
                        background-color: #218838 !important;
                    }
                    </style>
                """, unsafe_allow_html=True)
                
                # Créer le bouton dans un conteneur avec ID
                col_btn = st.container()
                with col_btn:
                    st.markdown('<div id="btn-calc-particulier">', unsafe_allow_html=True)
                    calc_button = st.button("🧮 CALCULER LA PRIME PARTICULIER", use_container_width=True, key="btn_calc_part")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                if calc_button:
                    # Validation pour les barèmes spéciaux
                    erreurs_validation = []
                    for bareme_key in baremes_selectionnes:
                        if bareme_key == 'bareme_special':
                            prime_man = primes_nettes_manuelles.get(bareme_key, 0)
                            if prime_man == 0:
                                erreurs_validation.append(f"{PRODUITS_PARTICULIERS_UI[bareme_key]} : prime nette manquante")
                    
                    if erreurs_validation:
                        st.error("❌ Erreurs de validation :\n" + "\n".join(f"- {e}" for e in erreurs_validation))
                    else:
                        try:
                            # Récupérer la surprime globale
                            surprime_globale_pourcent = st.session_state.get('surprime_globale_multi', 0.0)
                            
                            with st.spinner("Calcul en cours pour tous les barèmes..."):
                                # Calculer pour chaque barème sélectionné avec sa configuration spécifique
                                resultats_multi = {}
                                for idx, bareme_key in enumerate(baremes_selectionnes):
                                    # Récupérer la configuration spécifique à ce barème (utiliser index)
                                    config_bareme = configurations_baremes.get(idx, {})
                                    type_couv_bareme = config_bareme.get('type_couverture', 'Personne seule')
                                    enfants_supp_bareme = config_bareme.get('enfants_supp', 0)
                                    
                                    # Récupérer les informations médicales selon le mode
                                    montant_grossesse_man = None
                                    
                                    if mode_medical_par_bareme:
                                        # Mode "plusieurs types" : infos médicales par barème (utiliser index)
                                        infos_med = infos_medicales_par_bareme.get(idx, {})
                                        affections_declarees_b = infos_med.get('affections', [])
                                        grossesse_b = infos_med.get('grossesse', False)
                                        montant_grossesse_man = infos_med.get('montant_grossesse', None)
                                    else:
                                        # Mode classique : infos médicales communes
                                        affections_declarees_b = affections_globales
                                        grossesse_b = grossesse_detectee
                                    
                                    # Récupérer les dates de naissance selon le type de couverture
                                    date_naiss_principale = None
                                    date_naiss_conj = None
                                    
                                    if type_couv_bareme == "Personne seule":
                                        date_naiss_principale = st.session_state.get('date_naissance_ps')
                                    else:  # Famille
                                        date_naiss_principale = st.session_state.get('date_naissance_adulte1')
                                        date_naiss_conj = st.session_state.get('date_naissance_adulte2')
                                    
                                    prime_nette_man = primes_nettes_manuelles.get(bareme_key, None)
                                    accessoires_man = accessoires_manuels_dict.get(bareme_key, None)
                                    
                                    resultat = calculer_prime_particuliers(
                                        produit_key=bareme_key,
                                        type_couverture=type_couv_bareme,
                                        enfants_supplementaires=enfants_supp_bareme,
                                        affections_declarees=affections_declarees_b,
                                        grossesse=grossesse_b,
                                        reduction_commerciale=reduction_commerciale,
                                        duree_contrat=duree_contrat,
                                        date_naissance_principale=date_naiss_principale,
                                        date_naissance_conjoint=date_naiss_conj,
                                        prime_nette_manuelle=prime_nette_man,
                                        accessoires_manuels=accessoires_man,
                                        accessoire_plus=accessoire_plus,
                                        montant_grossesse_manuel=montant_grossesse_man,
                                        surprime_manuelle_pourcent=surprime_globale_pourcent
                                    )
                                    # Stocker avec index comme clé
                                    resultats_multi[idx] = {
                                        'produit_key': bareme_key,
                                        'resultat': resultat
                                    }
                                
                                st.session_state['resultats_part_multi'] = resultats_multi
                                st.session_state['baremes_selectionnes'] = baremes_selectionnes
                                st.session_state['configurations_baremes'] = configurations_baremes
                                st.rerun()
                        except ValueError as e:
                            st.error(f"❌ Erreur de validation : {str(e)}")
                        except Exception as e:
                            st.error(f"❌ Erreur inattendue : {str(e)}")
                
                # Affichage des résultats
                if 'resultats_part_multi' in st.session_state and st.session_state.get('baremes_selectionnes'):
                    st.markdown("---")
                    
                    resultats_multi = st.session_state['resultats_part_multi']
                    baremes_affiches = st.session_state['baremes_selectionnes']
                    type_cotation_resultats = st.session_state.get('type_cotation_part', "Une cotation, différentes propositions")
                    
                    if type_cotation_resultats == "Une cotation, une proposition":
                        # MODE COMBINÉ : Additionner toutes les primes TTC
                        st.markdown("### 💰 Prime Globale Combinée")
                        st.info(f"📋 {len(baremes_affiches)} barème(s) combiné(s) en une seule prime")
                        
                        # Calculer les totaux
                        prime_nette_totale = 0
                        accessoires_totaux = 0
                        lsp_total = 0
                        assist_psy_total = 0
                        taxe_totale = 0
                        prime_ttc_totale = 0
                        
                        # Tableau détaillé des composants
                        st.markdown("**📊 Détail par Barème**")
                        data_detail = []
                        
                        for idx, bareme_key in enumerate(baremes_affiches):
                            resultat_data = resultats_multi[idx]
                            resultat = resultat_data['resultat']
                            
                            prime_nette_totale += resultat['prime_nette_finale']
                            accessoires_totaux += resultat['accessoires']
                            lsp_total += resultat['prime_lsp']
                            assist_psy_total += resultat['prime_assist_psy']
                            taxe_totale += resultat['taxe']
                            prime_ttc_totale += resultat['prime_ttc_totale']
                            
                            data_detail.append({
                                'N°': idx + 1,
                                'Barème': PRODUITS_PARTICULIERS_UI[bareme_key],
                                'Prime TTC': format_currency(resultat['prime_ttc_totale']),
                            })
                        
                        df_detail = pd.DataFrame(data_detail)
                        st.dataframe(df_detail, use_container_width=True, hide_index=True)
                        
                        # Affichage de la prime combinée
                        st.markdown("---")
                        st.markdown("### 🎯 PRIME FINALE COMBINÉE")
                        
                        col_recap1, col_recap2, col_recap3 = st.columns(3)
                        
                        with col_recap1:
                            st.metric("Prime Nette Totale", format_currency(prime_nette_totale))
                            st.metric("Accessoires", format_currency(accessoires_totaux))
                        
                        with col_recap2:
                            st.metric("LSP", format_currency(lsp_total))
                            st.metric("Assistance Psy", format_currency(assist_psy_total))
                        
                        with col_recap3:
                            prime_ht_totale = prime_nette_totale + accessoires_totaux
                            st.metric("Prime HT", format_currency(prime_ht_totale))
                            st.metric("Taxe (8%)", format_currency(taxe_totale))
                        
                        # Prime TTC finale en grand
                        st.markdown("---")
                        st.markdown(
                            f"<div style='text-align: center; padding: 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px;'>"
                            f"<h1 style='color: white; margin: 0; font-size: 3em;'>{format_currency(prime_ttc_totale)}</h1>"
                            f"<p style='color: white; margin-top: 10px; font-size: 1.5em;'>Prime TTC Totale</p>"
                            f"</div>",
                            unsafe_allow_html=True
                        )
                        
                        st.success("✅ Contrat combiné prêt à être finalisé.")
                        
                        # Bouton de génération du récapitulatif pour l'option unique
                        st.markdown("---")
                        if st.button("📝 GÉNÉRER PROPOSITION COMMERCIALE", key="btn_generer_prop_simple", type="secondary"):
                            # Créer un résultat combiné unique pour l'affichage simple
                            resultat_combine = {
                                'prime_ttc_totale': prime_ttc_totale,
                                'prime_nette_base': sum(resultats_multi[idx]['resultat']['prime_nette_base'] for idx in resultats_multi),
                                'surprime_grossesse': sum(resultats_multi[idx]['resultat'].get('surprime_grossesse', 0) for idx in resultats_multi),
                                'accessoires': accessoires_totaux,
                                'prime_nette_finale': prime_nette_totale,
                                'taxe': taxe_totale,
                                'prime_ttc_taxable': sum(resultats_multi[idx]['resultat']['prime_ttc_taxable'] for idx in resultats_multi),
                                'prime_lsp': lsp_total,
                                'prime_assist_psy': assist_psy_total,
                                'facteurs': resultats_multi[0]['resultat']['facteurs'] if resultats_multi else {},
                                'surprime_risques_montant': sum(resultats_multi[idx]['resultat'].get('surprime_risques_montant', 0) for idx in resultats_multi),
                            }
                            bareme_name = f"COMBINÉ ({len(baremes_affiches)} barèmes)"
                            generer_recapitulatif_particulier({0: {'resultat': resultat_combine}}, [bareme_name])
                    
                    elif len(baremes_affiches) == 1:
                        # Une seule proposition : affichage détaillé normal
                        st.markdown("### 📊 Résultat de la Cotation")
                        bareme_key = baremes_affiches[0]
                        resultat_data = resultats_multi[0]
                        resultat = resultat_data['resultat']
                        afficher_resultat(
                            resultat, 
                            PRODUITS_PARTICULIERS_UI[bareme_key], 
                            TAUX_TAXE_PARTICULIER
                        )
                        st.success("✅ Contrat prêt à être finalisé.")
                        
                        # Bouton de génération du récapitulatif pour option unique
                        st.markdown("---")
                        if st.button("📝 GÉNÉRER PROPOSITION COMMERCIALE", key="btn_generer_prop_simple", type="secondary"):
                            generer_recapitulatif_particulier(resultats_multi, baremes_affiches)
                    
                    else:
                        # MODE COMPARAISON : Plusieurs propositions séparées
                        st.markdown("### 📊 Comparaison des Primes par Barème")
                        st.info(f"📋 {len(baremes_affiches)} barème(s) comparé(s)")
                        
                        # Récupérer les configurations
                        configs_affichees = st.session_state.get('configurations_baremes', {})
                        
                        # Créer le tableau comparatif
                        data_comparaison = []
                        for idx, bareme_key in enumerate(baremes_affiches):
                            resultat_data = resultats_multi[idx]
                            resultat = resultat_data['resultat']
                            config = configs_affichees.get(idx, {})
                            type_couv = config.get('type_couverture', 'N/A')
                            enfants = config.get('enfants_supp', 0)
                            
                            # Calculer Prime HT = Prime Nette + Accessoires
                            prime_ht = resultat['prime_nette_finale'] + resultat['accessoires']
                            
                            # Label de couverture
                            couverture_label = type_couv
                            if type_couv == "Famille" and enfants > 0:
                                couverture_label = f"Famille (+{enfants})"
                            
                            data_comparaison.append({
                                'N°': idx + 1,
                                'Barème': PRODUITS_PARTICULIERS_UI[bareme_key],
                                'Type': couverture_label,
                                'Prime Nette': format_currency(resultat['prime_nette_finale']),
                                'Accessoires': format_currency(resultat['accessoires']),
                                'LSP': format_currency(resultat['prime_lsp']),
                                'Assistance Psy': format_currency(resultat['prime_assist_psy']),
                                'Prime HT': format_currency(prime_ht),
                                'Taxe (8%)': format_currency(resultat['taxe']),
                                'Prime TTC': format_currency(resultat['prime_ttc_totale']),
                            })
                        
                        df_comparaison = pd.DataFrame(data_comparaison)
                        
                        # Afficher le tableau
                        st.dataframe(
                            df_comparaison,
                            use_container_width=True,
                            hide_index=True
                        )
                        
                        # Afficher les détails de chaque barème dans des expanders
                        st.markdown("---")
                        st.markdown("### 📋 Détails par Barème")
                        
                        for idx, bareme_key in enumerate(baremes_affiches):
                            resultat_data = resultats_multi[idx]
                            resultat = resultat_data['resultat']
                            config = configs_affichees.get(idx, {})
                            type_couv = config.get('type_couverture', 'N/A')
                            enfants = config.get('enfants_supp', 0)
                            
                            # Label pour l'expander
                            couverture_label = type_couv
                            if type_couv == "Famille" and enfants > 0:
                                couverture_label = f"Famille + {enfants} enfant(s) supp."
                            
                            with st.expander(f"🔹 {idx+1}. {PRODUITS_PARTICULIERS_UI[bareme_key]} - {couverture_label}"):
                                afficher_resultat_simple(
                                    resultat, 
                                    PRODUITS_PARTICULIERS_UI[bareme_key], 
                                    TAUX_TAXE_PARTICULIER
                                )
                        
                        st.success("✅ Comparaison complète. Sélectionnez le barème qui convient le mieux au client.")

                        st.markdown("---")
                        st.markdown("### 📄 Choix du Format de l'Offre")
                        
                        with st.container(border=True):
                            type_offre = st.radio(
                                "Comment souhaitez-vous présenter cette offre au client ?",
                                options=[
                                    "Offres Distinctes (Comparaison)",
                                    "Offre Combinée (Prime Totale)"
                                ],
                                key="type_offre_final",
                                help="Offres Distinctes : chaque barème est présenté séparément pour comparaison | Offre Combinée : tous les barèmes sont regroupés avec une prime totale unique"
                            )
                            
                            offre_combinee = (type_offre == "Offre Combinée (Prime Totale)")
                            
                            if offre_combinee:
                                st.info("📋 **Offre Combinée** : Un document unique avec la somme de toutes les primes")
                                
                                prime_totale_combinee = sum(
                                    resultats_multi[idx]['resultat']['prime_ttc_totale']
                                    for idx in range(len(baremes_affiches))
                                )
                                
                                st.markdown(f"### **Prime Totale Combinée : {format_currency(prime_totale_combinee)}** 💰")
                                
                                with st.expander("📊 Détail de la Prime Combinée"):
                                    for idx, bareme_key in enumerate(baremes_affiches):
                                        resultat = resultats_multi[idx]['resultat']
                                        prime_ttc = resultat['prime_ttc_totale']
                                        st.markdown(f"**{PRODUITS_PARTICULIERS_UI[bareme_key]}** : {format_currency(prime_ttc)}")
                                    
                                    st.markdown("---")
                                    st.markdown(f"**TOTAL** : {format_currency(prime_totale_combinee)}")
                            
                            else:
                                st.info("📊 **Offres Distinctes** : Chaque barème est présenté séparément pour comparaison")

                        st.markdown("---")
                        st.markdown("### ⚙️ Forçage Manuel des Primes (Optionnel)")
                        
                        with st.container(border=True):
                            st.warning("⚠️ **Attention** : Cette option permet de forcer manuellement les primes finales. À utiliser uniquement dans des cas exceptionnels.")
                            
                            activer_forcage = st.checkbox("Activer le forçage manuel des primes", key="forcage_manuel_part")
                            
                            if activer_forcage:
                                st.markdown("**Saisissez la Prime Nette et les Accessoires pour chaque barème :**")
                                
                                primes_forcees = {}
                                for idx, bareme_key in enumerate(baremes_affiches):
                                    resultat_original = resultats_multi[idx]['resultat']
                                    prime_nette_originale = resultat_original['prime_nette_finale']
                                    accessoires_originaux = resultat_original['accessoires']
                                    prime_ttc_originale = resultat_original['prime_ttc_totale']
                                    
                                    st.markdown(f"**{PRODUITS_PARTICULIERS_UI[bareme_key]}**")
                                    
                                    col_force1, col_force2, col_force3 = st.columns([1, 1, 1])
                                    
                                    with col_force1:
                                        prime_nette_forcee = st.number_input(
                                            "Prime Nette Forcée (FCFA)",
                                            min_value=0.0,
                                            value=float(prime_nette_originale),
                                            step=1000.0,
                                            key=f"prime_nette_forcee_part_{idx}",
                                            help="Saisissez la prime nette que vous souhaitez appliquer"
                                        )
                                    
                                    with col_force2:
                                        accessoires_forces = st.number_input(
                                            "Accessoires Forcés (FCFA)",
                                            min_value=0.0,
                                            value=float(accessoires_originaux),
                                            step=1000.0,
                                            key=f"accessoires_forces_part_{idx}",
                                            help="Saisissez les accessoires que vous souhaitez appliquer"
                                        )
                                    
                                    with col_force3:
                                        st.metric("Prime Nette Originale", format_currency(prime_nette_originale))
                                        st.metric("Accessoires Originaux", format_currency(accessoires_originaux))
                                        st.metric("Prime TTC Originale", format_currency(prime_ttc_originale))
                                    
                                    primes_forcees[idx] = {
                                        'prime_nette': prime_nette_forcee,
                                        'accessoires': accessoires_forces
                                    }
                                    
                                    st.markdown("---")
                                
                                if st.button("✅ APPLIQUER LES PRIMES FORCÉES", type="primary", use_container_width=True):
                                    for idx in primes_forcees:
                                        prime_nette_f = primes_forcees[idx]['prime_nette']
                                        accessoires_f = primes_forcees[idx]['accessoires']
                                        
                                        resultat = resultats_multi[idx]['resultat']
                                        
                                        resultat['prime_nette_finale'] = prime_nette_f
                                        resultat['accessoires'] = accessoires_f
                                        
                                        prime_ttc_taxable = prime_nette_f + accessoires_f
                                        taxe = prime_ttc_taxable * TAUX_TAXE_PARTICULIER
                                        resultat['taxe'] = taxe
                                        resultat['prime_ttc_taxable'] = prime_ttc_taxable + taxe
                                        
                                        prime_lsp = resultat.get('prime_lsp', 0)
                                        prime_assist_psy = resultat.get('prime_assist_psy', 0)
                                        
                                        resultat['prime_ttc_totale'] = resultat['prime_ttc_taxable'] + prime_lsp + prime_assist_psy
                                        resultat['prime_forcee'] = True
                                    
                                    st.session_state['resultats_part_multi'] = resultats_multi
                                    st.success("✅ Primes forcées appliquées avec succès !")
                                    st.rerun()

                        st.markdown("---")
                        if st.button("📝 GÉNÉRER LA PROPOSITION COMMERCIALE", key="btn_generer_prop", type="secondary", use_container_width=True):
                            generer_recapitulatif_particulier(resultats_multi, baremes_affiches)
    
    # --- PARCOURS CORPORATE ---
    with tab_corporate:
        
        # Choix de la méthode de tarification
        st.markdown("<h3 style='color: #6A0DAD;'>Choix de la Méthode de Tarification</h3>", unsafe_allow_html=True)
        
        methode_tarif = st.selectbox(
            "Sélectionnez votre méthode",
            ["Cotation Rapide (Estimation)", "Workflow Excel (Cotation Définitive)"],
            key="methode_corp",
            on_change=reset_results,
            help="Cotation Rapide = Aide à la vente | Workflow Excel = Offre ferme obligatoire"
        )
        
        st.markdown("---")
        
        # --- MÉTHODE 1 : COTATION RAPIDE ---
        if methode_tarif == "Cotation Rapide (Estimation)":
            st.markdown("###Cotation Rapide (Estimation Indicative)")
            st.warning(
                "⚠️ **ATTENTION :** Cette estimation est un outil d'aide à la vente uniquement. "
                "Elle ne tient PAS compte des risques médicaux individuels. "
                "Pour une offre ferme, utilisez le **Workflow Excel**."
            )
            
            # ÉTAPE 1 : Nombre de formules
            st.markdown("#### Étape 1 : Configuration des Formules")
            with st.container(border=True):
                nb_formules = st.number_input(
                    "Combien de formules de couverture différentes souhaitez-vous proposer ?",
                    min_value=1,
                    max_value=5,
                    value=1,
                    key="nb_formules_rapide",
                    help="Vous pouvez proposer jusqu'à 5 formules différentes pour différents groupes d'employés"
                )
                
                duree_contrat_rapide = st.selectbox(
                    "Durée du Contrat (Mois)",
                    options=list(range(1, 13)),
                    index=11,
                    key="duree_rapide",
                    help="Durée appliquée à toutes les formules"
                )
            
            # ÉTAPE 2 : Configuration de chaque formule
            st.markdown("---")
            st.markdown("#### Étape 2 : Détails de Chaque Formule")
            
            # Initialiser la structure de données pour les formules
            if 'formules_config' not in st.session_state:
                st.session_state['formules_config'] = []
            
            formules_config = []
            prime_totale_estimee = 0
            
            for i in range(nb_formules):
                with st.expander(f"📋 Formule {i+1}", expanded=(i==0)):
                    col_form1, col_form2 = st.columns(2)
                    
                    # Choix du produit pour cette formule
                    produit_formule = col_form1.selectbox(
                        "Produit",
                        options=list(PRODUITS_CORPORATE_UI.keys()),
                        format_func=lambda x: PRODUITS_CORPORATE_UI[x],
                        key=f"produit_formule_{i}",
                        help="Sélectionnez le produit pour cette formule"
                    )
                    
                    # Afficher un message pour le barème spécial
                    if produit_formule == 'bareme_special':
                        st.info("💼 **BARÈME SPÉCIAL** : Vous devrez saisir manuellement la prime nette avant le calcul.")
                    
                    # Nom de la formule (optionnel)
                    nom_formule = col_form2.text_input(
                        "Nom de la formule (optionnel)",
                        placeholder=f"Ex: Cadres, Employés, Direction...",
                        key=f"nom_formule_{i}"
                    )
                    
                    st.markdown("**Effectifs**")
                    col_eff1, col_eff2, col_eff3 = st.columns(3)
                    
                    nb_familles = col_eff1.number_input(
                        "Nombre de Familles",
                        min_value=0,
                        value=5 if i == 0 else 0,
                        key=f"nb_famille_formule_{i}",
                        help="Famille = Couple + max 3 enfants"
                    )
                    
                    nb_seuls = col_eff2.number_input(
                        "Nombre de Personnes Seules",
                        min_value=0,
                        value=3 if i == 0 else 0,
                        key=f"nb_seul_formule_{i}"
                    )
                    
                    nb_enfants_supp = col_eff3.number_input(
                        "Enfants Supplémentaires",
                        min_value=0,
                        value=0,
                        key=f"nb_enfants_supp_formule_{i}",
                        help="À partir du 4ème enfant"
                    )
                    
                    # Calcul estimation pour cette formule
                    if nb_familles > 0 or nb_seuls > 0 or nb_enfants_supp > 0:
                        # Pour barème spécial, permettre la saisie manuelle
                        if produit_formule == 'bareme_special':
                            st.markdown("**Saisie Manuelle (Barème Spécial)**")
                            col_man1, col_man2 = st.columns(2)
                            
                            prime_formule = col_man1.number_input(
                                "Prime Nette Totale (FCFA)",
                                min_value=0.0,
                                value=0.0,
                                step=10000.0,
                                key=f"prime_manuel_formule_{i}",
                                help="Saisissez la prime nette calculée selon votre barème spécial"
                            )
                            
                            accessoires_formule = col_man2.number_input(
                                "Accessoires Totaux (FCFA)",
                                min_value=0.0,
                                value=10000.0,
                                step=1000.0,
                                key=f"accessoires_manuel_formule_{i}",
                                help="Frais accessoires totaux"
                            )
                            
                            if prime_formule == 0:
                                st.warning("⚠️ Veuillez saisir une prime nette pour continuer")
                            else:
                                total_assures_formule = nb_familles + nb_seuls + nb_enfants_supp
                                prime_totale_estimee += prime_formule
                                
                                st.success(
                                    f"💡 Prime Nette Saisie : **{format_currency(prime_formule)}** "
                                    f"({total_assures_formule} unités de couverture)"
                                )
                                
                                # Sauvegarder la configuration avec les valeurs manuelles
                                formules_config.append({
                                    'produit_key': produit_formule,
                                    'nom': nom_formule if nom_formule else f"Formule {i+1}",
                                    'nb_familles': nb_familles,
                                    'nb_seuls': nb_seuls,
                                    'nb_enfants_supp': nb_enfants_supp,
                                    'prime_nette': prime_formule,
                                    'prime_nette_manuelle': prime_formule,
                                    'accessoires_manuels': accessoires_formule
                                })
                        else:
                            # Calcul normal avec barème prédéfini
                            tarif_formule = TARIFS_CORPORATE[produit_formule]
                            prime_formule = (
                                tarif_formule['famille']['prime_nette'] * nb_familles +
                                tarif_formule['personne_seule']['prime_nette'] * nb_seuls +
                                tarif_formule['enfant_supplementaire']['prime_nette'] * nb_enfants_supp
                            )
                            
                            total_assures_formule = nb_familles + nb_seuls + nb_enfants_supp
                            prime_totale_estimee += prime_formule
                            
                            st.success(
                                f"💡 Prime Nette Estimée pour cette formule : **{format_currency(prime_formule)}** "
                                f"({total_assures_formule} unités de couverture)"
                            )
                            
                            # Sauvegarder la configuration
                            formules_config.append({
                                'produit_key': produit_formule,
                                'nom': nom_formule if nom_formule else f"Formule {i+1}",
                                'nb_familles': nb_familles,
                                'nb_seuls': nb_seuls,
                                'nb_enfants_supp': nb_enfants_supp,
                                'prime_nette': prime_formule
                            })
            
            # ÉTAPE 3 : Ajustements globaux
            if formules_config:
                st.markdown("---")
                st.markdown("#### Étape 3 : Ajustements Globaux")
                
                with st.container(border=True):
                    st.info(f"💰 **Prime Nette Totale Estimée (toutes formules) :** {format_currency(prime_totale_estimee)}")
                    
                    col_aj1, col_aj2 = st.columns(2)
                    
                    surprime_rapide = col_aj1.number_input(
                        "Surprime Risque Globale Estimée (%)",
                        min_value=0.0,
                        max_value=float(MAX_SURPRIME_RISQUE_CORP),
                        value=0.0,
                        step=0.5,
                        format="%.1f",
                        key="surprime_rapide_global",
                        help="Saisissez le pourcentage de surprime estimé (sans analyse médicale détaillée)"
                    )
                    
                    reduction_rapide = col_aj2.number_input(
                        "Réduction Commerciale (%)",
                        min_value=0.0,
                        max_value=100.0,
                        value=0.0,
                        step=0.5,
                        format="%.1f",
                        key="reduction_rapide_global",
                        help="Saisissez le pourcentage de réduction commerciale (nécessite validation hiérarchique si > 20%)"
                    )
                    
                    # Champ Accessoire + (frais supplémentaires)
                    accessoire_plus_corp = st.number_input(
                        "Accessoire + (FCFA)",
                        min_value=0.0,
                        value=0.0,
                        step=1000.0,
                        format="%.0f",
                        key="accessoire_plus_corp_rapide",
                        help="Frais accessoires supplémentaires à ajouter au calcul (ex: frais de dossier, frais administratifs)"
                    )
                    
                    if accessoire_plus_corp > 0:
                        st.info(f"ℹ️ Accessoire supplémentaire de {format_currency(accessoire_plus_corp)} sera ajouté au calcul.")
                
                # ÉTAPE 4 : Génération de l'estimation
                st.markdown("---")
                if st.button("📊 GÉNÉRER L'ESTIMATION COMPLÈTE", type="primary", use_container_width=True):
                    try:
                        with st.spinner("Calcul de l'estimation multi-formules..."):
                            # Calculer chaque formule
                            resultats_formules = []
                            prime_nette_totale = 0
                            prime_ttc_totale = 0
                            
                            for formule in formules_config:
                                resultat = calc_calculer_prime_corporate_rapide(
                                    produit_key=formule['produit_key'],
                                    nb_familles=formule['nb_familles'],
                                    nb_personnes_seules=formule['nb_seuls'],
                                    nb_enfants_supplementaires=formule['nb_enfants_supp'],
                                    surprime_risques=surprime_rapide,
                                    reduction_commerciale=0,  # Appliquée globalement après
                                    duree_contrat=duree_contrat_rapide,
                                    prime_nette_manuelle=formule.get('prime_nette_manuelle'),
                                    accessoires_manuels=formule.get('accessoires_manuels'),
                                    accessoire_plus=accessoire_plus_corp
                                )
                                
                                resultat['nom_formule'] = formule['nom']
                                resultat['produit_name'] = PRODUITS_CORPORATE_UI[formule['produit_key']]
                                resultats_formules.append(resultat)
                                
                                prime_nette_totale += resultat['prime_nette_finale'] 
                                prime_ttc_totale += resultat['prime_ttc_totale']
                            
                            # Appliquer la réduction commerciale globale
                            prime_ttc_finale = prime_ttc_totale * (100 - reduction_rapide) / 100
                            
                            # Sauvegarder les résultats
                            st.session_state['resultats_multi_formules'] = {
                                'formules': resultats_formules,
                                'prime_nette_totale': prime_nette_totale,
                                'prime_ttc_totale': prime_ttc_totale,
                                'reduction_commerciale': reduction_rapide,
                                'prime_ttc_finale': prime_ttc_finale,
                                'duree_contrat': duree_contrat_rapide
                            }
                            st.rerun()
                            
                    except ValueError as e:
                        st.error(f"❌ Erreur : {str(e)}")
                
                # Affichage des résultats
                if 'resultats_multi_formules' in st.session_state:
                    st.markdown("---")
                    resultats = st.session_state['resultats_multi_formules']
                    
                    st.markdown("### 📊 Résultats de l'Estimation Multi-Formules")
                    st.info("ℹ️ **ESTIMATION INDICATIVE** - Non contractuelle")
                    
                    # Résumé global
                    st.markdown("#### Synthèse Globale")
                    col_synth1, col_synth2, col_synth3 = st.columns(3)
                    
                    col_synth1.metric(
                        "Prime Nette Totale",
                        format_currency(resultats['prime_nette_totale'])
                    )
                    
                    col_synth2.metric(
                        "Prime TTC (avant réduction)",
                        format_currency(resultats['prime_ttc_totale'])
                    )
                    
                    col_synth3.metric(
                        "Prime TTC Finale",
                        format_currency(resultats['prime_ttc_finale']),
                        delta=f"-{resultats['reduction_commerciale']}%" if resultats['reduction_commerciale'] > 0 else None
                    )
                    
                    # Détail par formule
                    st.markdown("---")
                    st.markdown("#### Détail par Formule")
                    
                    for i, formule in enumerate(resultats['formules']):
                        with st.expander(f"📋 {formule['nom_formule']} - {formule['produit_name']}", expanded=True):
                            afficher_resultat_simple(
                                formule,
                                formule['produit_name'],
                                TAUX_TAXE_CORPORATE
                            )
                    
                    st.markdown("---")
                    st.markdown("### ⚙️ Forçage Manuel de la Prime (Optionnel)")
                    
                    with st.container(border=True):
                        st.warning("⚠️ **Attention** : Cette option permet de forcer manuellement la prime finale. À utiliser uniquement dans des cas exceptionnels.")
                        
                        activer_forcage_rapide = st.checkbox("Activer le forçage manuel de la prime", key="forcage_manuel_corp_rapide")
                        
                        if activer_forcage_rapide:
                            prime_nette_originale = resultats['prime_nette_totale']
                            
                            accessoires_originaux = sum(
                                f.get('accessoires', 0) for f in resultats['formules']
                            )
                            prime_ttc_originale = resultats['prime_ttc_finale']
                            
                            st.markdown("**Saisissez la Prime Nette et les Accessoires :**")
                            
                            col_force1, col_force2, col_force3 = st.columns([1, 1, 1])
                            
                            with col_force1:
                                prime_nette_forcee_rapide = st.number_input(
                                    "Prime Nette Totale Forcée (FCFA)",
                                    min_value=0.0,
                                    value=float(prime_nette_originale),
                                    step=10000.0,
                                    key="prime_nette_forcee_corp_rapide",
                                    help="Saisissez la prime nette totale que vous souhaitez appliquer"
                                )
                            
                            with col_force2:
                                accessoires_forces_rapide = st.number_input(
                                    "Accessoires Totaux Forcés (FCFA)",
                                    min_value=0.0,
                                    value=float(accessoires_originaux),
                                    step=1000.0,
                                    key="accessoires_forces_corp_rapide",
                                    help="Saisissez les accessoires totaux que vous souhaitez appliquer"
                                )
                            
                            with col_force3:
                                st.metric("Prime Nette Originale", format_currency(prime_nette_originale))
                                st.metric("Accessoires Originaux", format_currency(accessoires_originaux))
                                st.metric("Prime TTC Originale", format_currency(prime_ttc_originale))
                            
                            prime_ttc_taxable_forcee = prime_nette_forcee_rapide + accessoires_forces_rapide
                            taxe_forcee = prime_ttc_taxable_forcee * TAUX_TAXE_CORPORATE
                            prime_ttc_taxable_avec_taxe = prime_ttc_taxable_forcee + taxe_forcee
                            
                            services_totaux = sum(
                                f.get('prime_lsp', 0) + f.get('prime_assist_psy', 0) 
                                for f in resultats['formules']
                            )
                            prime_ttc_totale_forcee = prime_ttc_taxable_avec_taxe + services_totaux
                            
                            reduction_commerciale = resultats.get('reduction_commerciale', 0)
                            prime_finale_forcee = prime_ttc_totale_forcee * (100 - reduction_commerciale) / 100
                            
                            st.info(f"**Prime TTC Finale Calculée (après forçage) :** {format_currency(prime_finale_forcee)}")
                            
                            if abs(prime_finale_forcee - prime_ttc_originale) > 1:
                                difference = prime_finale_forcee - prime_ttc_originale
                                pourcent = (difference / prime_ttc_originale * 100) if prime_ttc_originale > 0 else 0
                                st.metric("Écart avec Prime Originale", format_currency(abs(difference)), delta=f"{pourcent:+.1f}%")
                            
                            if st.button("✅ APPLIQUER LA PRIME FORCÉE", type="primary", use_container_width=True):
                                resultats['prime_nette_totale'] = prime_nette_forcee_rapide
                                resultats['prime_ttc_totale'] = prime_ttc_totale_forcee
                                resultats['prime_ttc_finale'] = prime_finale_forcee
                                resultats['prime_forcee'] = True
                                st.session_state['resultats_multi_formules'] = resultats
                                st.success("✅ Prime forcée appliquée avec succès !")
                                st.rerun()
                    
                    st.markdown("---")
                    st.warning(
                        "⚠️ Cette estimation ne constitue pas une offre ferme. "
                        "Passez au **Workflow Excel** pour obtenir un devis définitif avec micro-tarification."
                    )
        
    
    
        # --- MÉTHODE 2 : WORKFLOW EXCEL ---
        else:
            st.markdown("### 📊 Workflow Excel (Cotation Définitive)")
            st.success(
                "✅ **Méthode Obligatoire** pour toute soumission d'offre ferme. "
                "Inclut la micro-tarification et l'analyse médicale complète."
            )
            
            # Étape 1 : Sélection du barème
            st.markdown("#### Étape 1 : Sélection du barème")
            with st.container(border=True):
                produit_key_corp = st.selectbox(
                    "Formule de Couverture",
                    list(PRODUITS_CORPORATE_UI.keys()),
                    format_func=lambda x: PRODUITS_CORPORATE_UI[x],
                    key="produit_corp_excel",
                    help="Sélectionnez le produit pour le devis Excel"
                )
                
                # Affichage des plafonds (seulement pour les barèmes standards)
                if produit_key_corp != 'bareme_special':
                    tarif_selected = TARIFS_CORPORATE[produit_key_corp]
                    col_plaf1, col_plaf2 = st.columns(2)
                    col_plaf1.metric(
                        "💳 Plafond par Personne",
                        format_currency(tarif_selected['plafond_personne'])
                    )
                    col_plaf2.metric(
                        "👨‍👩‍👧‍👦 Plafond par Famille",
                        format_currency(tarif_selected['plafond_famille'])
                    )
                else:
                    st.error(
                        "⚠️ **ATTENTION** : Le barème spécial n'est pas compatible avec le workflow Excel. "
                        "Veuillez utiliser la **'Cotation Rapide'** pour les barèmes spéciaux, "
                        "ou sélectionner un barème standard pour continuer avec le workflow Excel."
                    )
                    st.stop()  # Arrêter l'exécution ici
                
                st.info(
                    f"📋 Produit sélectionné : **{PRODUITS_CORPORATE_UI[produit_key_corp]}** "
                    f"({tarif_selected['type']}) - Barèmes chargés"
                )
                
                st.caption(
                    "ℹ️ **Option Famille :** Couple + jusqu'à 3 enfants inclus (maximum 25 ans par enfant). "
                    "À partir du 4ème enfant : facturation supplémentaire par enfant."
                )
            
            st.markdown("---")
            
            # Étape 2 : Téléchargement du template
            st.markdown("#### Étape 2 : Télécharger le Template Excel")
            with st.container(border=True):
                st.markdown(
                    "Téléchargez le template Excel, remplissez les données de tous les employés "
                    "et dépendants (informations démographiques + Questionnaire Médical complet)."
                )
                
                template_bytes = calc_generer_template_excel()
                st.download_button(
                    label="📥 TÉLÉCHARGER LE TEMPLATE EXCEL",
                    data=template_bytes,
                    file_name="LEADWAY_Template_Corporate.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                
                with st.expander("ℹ️ Instructions de Remplissage"):
                    st.markdown(f"""
                    **Colonnes Obligatoires pour l'Assuré Principal :**
                    - `nom` : Nom de l'assuré
                    - `prenom` : Prénom(s) de l'assuré
                    - `date_naissance` : Format DD/MM/YYYY
                    - `lieu_naissance` : Lieu de naissance
                    - `contact` : Numéro de téléphone
                    - `numero_cnam` : Numéro d'identification CNAM
                    - `nationalite` : Nationalité
                    - `taille` : Taille en cm
                    - `poids` : Poids en kg
                    - `tension_arterielle` : Format 12/8
                    - `etat_civil` : Célibataire, Marié(e), Divorcé(e), Conjoint de fait, Veuf/veuve
                    - `emploi_actuel` : Poste ou profession actuelle
                    - `type_couverture` : "Personne seule" ou "Famille"
                    - `nombre_enfants` : 0 pour personne seule, 1-3 pour famille (max 3 enfants inclus), à partir du 4ème = enfant supplémentaire
                    - `grossesse` : True ou False
                    - `affections` : Liste séparée par virgules
                    
                    **Pour le Conjoint (si type_couverture = Famille) :**
                    - `conjoint_nom` : Nom du conjoint
                    - `conjoint_prenom` : Prénom(s) du conjoint
                    - `conjoint_date_naissance`, `conjoint_lieu_naissance`, `conjoint_contact`, `conjoint_numero_cnam`
                    - `conjoint_nationalite`, `conjoint_taille`, `conjoint_poids`, `conjoint_tension_arterielle`
                    - `conjoint_etat_civil`, `conjoint_emploi_actuel`
                    
                    **Pour les Enfants (selon nombre_enfants) :**
                    - `enfantX_nom` : Nom de l'enfant
                    - `enfantX_prenom` : Prénom(s) de l'enfant
                    - `enfantX_date_naissance`, `enfantX_lieu_naissance`, `enfantX_contact`, `enfantX_numero_cnam`
                    - `enfantX_taille`, `enfantX_poids`, `enfantX_tension_arterielle`, `enfantX_niveau_etude`
                    - (Remplacer X par 1, 2, 3, etc.)
                    
                    **⚠️ Note importante :** L'option Famille couvre le couple + jusqu'à 3 enfants. 
                    À partir du 4ème enfant, chaque enfant supplémentaire est facturé séparément.
                    
                    **👶 Limite d'Âge Enfants :** Les enfants doivent avoir 25 ans maximum pour être éligibles à une cotation famille. 
                    Au-delà de cet âge, une cotation personne seule est requise.
                    
                    **💡 Surprime d'Âge :** Une surprime de 25% est automatiquement appliquée pour toute personne de plus de 51 ans.
                    
                    **Affections Reconnues :** {', '.join(LISTE_AFFECTIONS)}
                    
                    **⛔ Affections Bloquantes :** {', '.join(AFF_EXCLUES)} (exclusion automatique)
                    """)
            
            st.markdown("---")
            
            # Étape 3 : Import du fichier
            st.markdown("#### Étape 3 : Importer le Fichier Rempli")
            with st.container(border=True):
                uploaded_file = st.file_uploader(
                    "Sélectionnez votre fichier Excel rempli",
                    type=['xlsx', 'xls'],
                    key="upload_corp",
                    help="Le fichier sera validé automatiquement"
                )
                
                if uploaded_file is not None:
                    try:
                        with st.spinner("Lecture et validation du fichier..."):
                            df = pd.read_excel(uploaded_file)
                            is_valid, error_msg, df_clean = calc_valider_fichier_excel(df)
                            
                            if not is_valid:
                                st.error(f"❌ **Erreur de Validation :** {error_msg}")
                                st.stop()
                            
                            st.session_state['df_corporate'] = df_clean
                            st.success(f"✅ Fichier validé : **{len(df_clean)}** lignes détectées")
                            
                            # Aperçu des données
                            with st.expander("👀 Aperçu des Données Importées"):
                                st.dataframe(df_clean.head(10), use_container_width=True)
                    
                    except Exception as e:
                        st.error(f"❌ Erreur lors de la lecture du fichier : {str(e)}")
            
            # Étape 4 : Micro-Tarification
            if 'df_corporate' in st.session_state:
                st.markdown("---")
                st.markdown("#### Étape 4 : Micro-Tarification et Gestion du Risque")
                
                with st.container(border=True):
                    duree_contrat_excel = st.selectbox(
                        "Durée du Contrat (Mois)",
                        options=list(range(1, 13)),
                        index=11,
                        key="duree_excel",
                        help="Appliqué uniformément à tous les assurés"
                    )
                    
                    if st.button("⚙️ LANCER LA MICRO-TARIFICATION", type="primary", use_container_width=True):
                        try:
                            with st.spinner("Analyse ligne par ligne en cours..."):
                                resultat_micro = calc_micro_tarification_excel(
                                    st.session_state['df_corporate'],
                                    produit_key_corp,
                                    duree_contrat_excel
                                )
                                st.session_state['resultat_corp_excel'] = resultat_micro
                                st.rerun()
                        except Exception as e:
                            st.error(f"❌ Erreur lors de la micro-tarification : {str(e)}")
                
                # Affichage des résultats de micro-tarification
                if 'resultat_corp_excel' in st.session_state:
                    st.markdown("---")
                    st.markdown("#### Étape 5 : Finalisation et Ajustement Commercial")
                    
                    resultat_micro = st.session_state['resultat_corp_excel']
                    
                    # Saisie des informations administratives
                    with st.container(border=True):
                        st.markdown("**Informations Entreprise**")
                        col_ent1, col_ent2 = st.columns(2)
                        
                        nom_entreprise = col_ent1.text_input("Nom de l'Entreprise", key="nom_ent")
                        secteur = col_ent2.text_input("Secteur d'Activité", key="secteur_ent")
                    
                    # Ajustement commercial final
                    with st.container(border=True):
                        st.markdown("**Ajustement Commercial Final**")
                        
                        reduction_finale = st.number_input(
                            "Réduction Commerciale Négociée (%)",
                            min_value=0.0,
                            max_value=100.0,
                            value=0.0,
                            step=0.5,
                            format="%.1f",
                            key="reduction_excel_finale",
                            help="Saisissez le pourcentage de réduction (nécessite validation hiérarchique si > 20% - sera tracée pour audit)"
                        )
                        
                        if reduction_finale > 0:
                            if reduction_finale > 30:
                                st.error(
                                    f"🚨 **RÉDUCTION EXCEPTIONNELLE DE {reduction_finale}%** - "
                                    "**VALIDATION DIRECTION GÉNÉRALE + COMITÉ OBLIGATOIRE** avant signature."
                                )
                            elif reduction_finale > 20:
                                st.error(
                                    f"⚠️ Réduction de {reduction_finale}% appliquée. "
                                    "**VALIDATION DIRECTION OBLIGATOIRE** avant signature."
                                )
                            else:
                                st.warning(
                                    f"⚠️ Réduction de {reduction_finale}% appliquée. "
                                    "**VALIDATION MANAGER OBLIGATOIRE** avant signature."
                                )
                            
                            col_valid1, col_valid2 = st.columns(2)
                            validateur = col_valid1.text_input("Nom du Validateur", key="validateur")
                            motif = col_valid2.text_area("Motif de la Réduction", key="motif_reduction")
                    
                    # Affichage du résultat final
                    st.markdown("---")
                    afficher_resultat_micro_tarification(
                        resultat_micro,
                        PRODUITS_CORPORATE_UI[produit_key_corp],
                        reduction_finale
                    )
                    
                    st.markdown("---")
                    st.markdown("### ⚙️ Forçage Manuel de la Prime (Optionnel)")
                    
                    with st.container(border=True):
                        st.warning("⚠️ **Attention** : Cette option permet de forcer manuellement la prime finale. À utiliser uniquement dans des cas exceptionnels avec validation hiérarchique.")
                        
                        activer_forcage_corp = st.checkbox("Activer le forçage manuel de la prime", key="forcage_manuel_corp")
                        
                        if activer_forcage_corp:
                            prime_nette_originale = resultat_micro['prime_nette_totale']
                            accessoires_originaux = resultat_micro['accessoires']
                            prime_ttc_originale = resultat_micro['prime_ttc_totale']
                            prime_finale_originale = prime_ttc_originale * (100 - reduction_finale) / 100
                            
                            st.markdown("**Saisissez la Prime Nette et les Accessoires :**")
                            
                            col_force1, col_force2, col_force3 = st.columns([1, 1, 1])
                            
                            with col_force1:
                                prime_nette_forcee = st.number_input(
                                    "Prime Nette Totale Forcée (FCFA)",
                                    min_value=0.0,
                                    value=float(prime_nette_originale),
                                    step=10000.0,
                                    key="prime_nette_forcee_corp",
                                    help="Saisissez la prime nette totale que vous souhaitez appliquer"
                                )
                            
                            with col_force2:
                                accessoires_forces = st.number_input(
                                    "Accessoires Totaux Forcés (FCFA)",
                                    min_value=0.0,
                                    value=float(accessoires_originaux),
                                    step=1000.0,
                                    key="accessoires_forces_corp",
                                    help="Saisissez les accessoires totaux que vous souhaitez appliquer"
                                )
                            
                            with col_force3:
                                st.metric("Prime Nette Originale", format_currency(prime_nette_originale))
                                st.metric("Accessoires Originaux", format_currency(accessoires_originaux))
                                st.metric("Prime TTC Originale", format_currency(prime_finale_originale))
                            
                            prime_ttc_taxable_forcee = prime_nette_forcee + accessoires_forces
                            taxe_forcee = prime_ttc_taxable_forcee * TAUX_TAXE_CORPORATE
                            prime_ttc_taxable_avec_taxe = prime_ttc_taxable_forcee + taxe_forcee
                            
                            services_totaux = resultat_micro.get('services', 0)
                            prime_ttc_totale_forcee = prime_ttc_taxable_avec_taxe + services_totaux
                            prime_finale_forcee = prime_ttc_totale_forcee * (100 - reduction_finale) / 100
                            
                            st.info(f"**Prime TTC Totale Calculée (après forçage) :** {format_currency(prime_finale_forcee)}")
                            
                            if abs(prime_finale_forcee - prime_finale_originale) > 1:
                                difference = prime_finale_forcee - prime_finale_originale
                                pourcent = (difference / prime_finale_originale * 100) if prime_finale_originale > 0 else 0
                                st.metric("Écart avec Prime Originale", format_currency(abs(difference)), delta=f"{pourcent:+.1f}%")
                            
                            col_motif1, col_motif2 = st.columns(2)
                            motif_forcage = col_motif1.text_area(
                                "Motif du forçage (obligatoire)",
                                key="motif_forcage_corp",
                                help="Expliquez la raison du forçage de la prime"
                            )
                            validateur_forcage = col_motif2.text_input(
                                "Validateur (obligatoire)",
                                key="validateur_forcage_corp",
                                help="Nom du responsable validant ce forçage"
                            )
                            
                            if st.button("✅ APPLIQUER LA PRIME FORCÉE", type="primary", use_container_width=True):
                                if not motif_forcage or not validateur_forcage:
                                    st.error("❌ Le motif et le validateur sont obligatoires pour le forçage manuel")
                                else:
                                    resultat_micro['prime_nette_totale'] = prime_nette_forcee
                                    resultat_micro['accessoires'] = accessoires_forces
                                    resultat_micro['taxe'] = taxe_forcee
                                    resultat_micro['prime_ttc_taxable'] = prime_ttc_taxable_avec_taxe
                                    resultat_micro['prime_ttc_totale'] = prime_ttc_totale_forcee
                                    resultat_micro['prime_forcee'] = True
                                    resultat_micro['motif_forcage'] = motif_forcage
                                    resultat_micro['validateur_forcage'] = validateur_forcage
                                    
                                    st.session_state['resultat_corp_excel'] = resultat_micro
                                    st.success("✅ Prime forcée appliquée avec succès !")
                                    st.rerun()
                    
                    st.markdown("---")
                    col_final1, col_final2 = st.columns([3, 1])
                    
                    if col_final2.button("✅ FINALISER LE DEVIS", type="primary", use_container_width=True):
                        if reduction_finale > 0 and (not nom_entreprise or not validateur or not motif):
                            st.error("❌ Informations de validation manquantes pour la réduction commerciale")
                        else:
                            st.success("🎉 **DEVIS CORPORATE FINALISÉ** - Prêt pour signature du contrat")
                            st.balloons()
                            
                            prime_finale_display = resultat_micro['prime_ttc_totale'] * (100 - reduction_finale) / 100
                            
                            with st.expander("📄 Récapitulatif du Devis"):
                                recap_text = f"""
                                **Entreprise :** {nom_entreprise if nom_entreprise else "Non renseignée"}  
                                **Secteur :** {secteur if secteur else "Non renseigné"}  
                                **Produit :** {PRODUITS_CORPORATE_UI[produit_key_corp]}  
                                **Durée :** {duree_contrat_excel} mois  
                                **Nombre d'assurés éligibles :** {resultat_micro['nb_eligibles']}  
                                **Prime TTC Finale :** {format_currency(prime_finale_display)}  
                                
                                {f"**Réduction Appliquée :** {reduction_finale}%" if reduction_finale > 0 else ""}  
                                {f"**Validé par :** {validateur}" if reduction_finale > 0 and validateur else ""}  
                                {f"**Motif :** {motif}" if reduction_finale > 0 and motif else ""}
                                """
                                
                                if resultat_micro.get('prime_forcee'):
                                    recap_text += f"""
                                    
                                    **⚠️ PRIME FORCÉE MANUELLEMENT**  
                                    **Validateur du forçage :** {resultat_micro.get('validateur_forcage', 'N/A')}  
                                    **Motif du forçage :** {resultat_micro.get('motif_forcage', 'N/A')}
                                    """
                                
                                st.markdown(recap_text)
