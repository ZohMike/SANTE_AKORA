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
from database import DatabaseManager
import uuid

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT


# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    layout="wide", 
    page_title="Assur Defender - Cotation Santé +",
    page_icon="🛡️",
    initial_sidebar_state="collapsed"
)

# --- INITIALISATION DES VARIABLES SESSION_STATE ---
# Initialiser toutes les variables nécessaires dès le début
if 'baremes_selectionnes_list' not in st.session_state:
    st.session_state.baremes_selectionnes_list = []
if 'resultats_part_multi' not in st.session_state:
    st.session_state.resultats_part_multi = {}
if 'configurations_baremes' not in st.session_state:
    st.session_state.configurations_baremes = {}
if 'principal_data' not in st.session_state:
    st.session_state.principal_data = {}
if 'trop_percu_part_multi' not in st.session_state:
    st.session_state.trop_percu_part_multi = 0.0

# Initialisation du gestionnaire de base de données Supabase
if 'db_manager' not in st.session_state:
    try:
        st.session_state.db_manager = DatabaseManager()
    except Exception as e:
        st.session_state.db_manager = None
        # st.warning(f"⚠️ Connexion Supabase non disponible : {e}")

def generer_numero_devis(type_marche: str = "PART") -> str:
    """Génère un numéro de devis unique."""
    date_str = datetime.now().strftime('%Y%m%d')
    unique_id = uuid.uuid4().hex[:6].upper()
    return f"{type_marche}-{date_str}-{unique_id}"

def sauvegarder_cotation_supabase(
    type_marche: str,
    produit: str,
    resultat: Dict[str, Any],
    client_info: Dict[str, Any],
    duree_contrat: int = 12,
    reduction_commerciale: float = 0,
    pdf_options_data: List[Dict] = None,
    pdf_principal_data: Dict = None,
    pdf_bytes: bytes = None  # PDF binaire pour stockage direct
) -> bool:
    """
    Sauvegarde une cotation dans Supabase avec le PDF BINAIRE pour téléchargement IDENTIQUE.
    
    Args:
        pdf_bytes: Le PDF généré en bytes - sera stocké en base64 pour téléchargement identique
    
    Returns:
        bool: True si sauvegarde réussie, False sinon
    """
    if st.session_state.db_manager is None:
        st.error("❌ Base de données non connectée")
        return False
    
    try:
        import base64
        
        numero_devis = generer_numero_devis("PART" if type_marche == "Particulier" else "CORP")
        
        # Convertir le PDF en base64 pour stockage
        pdf_base64 = None
        if pdf_bytes:
            pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
        
        # Stocker TOUTES les données + le PDF binaire
        devis_data = {
            'numero_devis': numero_devis,
            'type_marche': type_marche,
            'produit': produit,
            'nom_client': f"{client_info.get('nom', '')} {client_info.get('prenom', '')}".strip(),
            'entreprise': client_info.get('entreprise', ''),
            'secteur': client_info.get('secteur', ''),
            'type_couverture': client_info.get('type_couverture', ''),
            'nb_adultes': client_info.get('nb_adultes', 1),
            'nb_enfants': client_info.get('nb_enfants', 0),
            'nb_enfants_supplementaires': resultat.get('nombre_enfants_supp', 0),
            'prime_nette': resultat.get('prime_nette_finale', 0),
            'accessoires': resultat.get('accessoires', 0),
            'services': resultat.get('prime_lsp', 0) + resultat.get('prime_assist_psy', 0),
            'taxe': resultat.get('taxe', 0),
            'prime_ttc': resultat.get('prime_ttc_totale', 0),
            'prime_finale': resultat.get('prime_ttc_totale', 0),
            'reduction_commerciale': reduction_commerciale,
            'surprime_medicale': resultat.get('surprime_risques_taux', 0),
            'surprime_age': resultat.get('surprime_age_taux', 0),
            'duree_contrat': duree_contrat,
            'statut': 'En attente',
            'pdf_data': pdf_base64,  # PDF STOCKÉ EN BASE64
            'details': {
                'prime_nette_base': resultat.get('prime_nette_base', 0),
                'prime_nette_finale': resultat.get('prime_nette_finale', 0),
                'accessoires': resultat.get('accessoires', 0),
                'taxe': resultat.get('taxe', 0),
                'prime_ttc_taxable': resultat.get('prime_ttc_taxable', 0),
                'prime_ttc_totale': resultat.get('prime_ttc_totale', 0),
                'prime_lsp': resultat.get('prime_lsp', 0),
                'prime_assist_psy': resultat.get('prime_assist_psy', 0),
                'surprime_grossesse': resultat.get('surprime_grossesse', 0),
                'surprime_risques_taux': resultat.get('surprime_risques_taux', 0),
                'surprime_age_taux': resultat.get('surprime_age_taux', 0),
                'surprime_totale_taux': resultat.get('surprime_totale_taux', 0),
                'affections_declarees': resultat.get('affections_declarees', []),
                'facteurs': resultat.get('facteurs', {}),
                'bareme_special': resultat.get('bareme_special', False),
                'accessoire_plus': resultat.get('accessoire_plus', 0),
                'client_info': client_info,
                'pdf_options_data': pdf_options_data,
                'pdf_principal_data': pdf_principal_data
            }
        }
        
        result = st.session_state.db_manager.sauvegarder_devis(devis_data)
        
        if result:
            st.session_state['dernier_devis_sauvegarde'] = numero_devis
            return True
        return False
        
    except Exception as e:
        st.error(f"❌ Erreur lors de la sauvegarde : {str(e)}")
        return False

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
            <span style="font-size: 12px; color: #28a745; margin-left: 10px;">v2.3-REGROUPEMENT</span>
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
    surprime_manuelle_pourcent: float = 0.0,
    prime_lsp_manuelle: Optional[float] = None,
    prime_assist_psy_manuelle: Optional[float] = None
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
        prime_lsp_manuelle=prime_lsp_manuelle,
        prime_assist_psy_manuelle=prime_assist_psy_manuelle,
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
    accessoire_plus: float = 0,
    prime_lsp_manuelle: Optional[float] = None,
    prime_assist_psy_manuelle: Optional[float] = None
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
        prime_lsp_manuelle=prime_lsp_manuelle,
        prime_assist_psy_manuelle=prime_assist_psy_manuelle,
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
    """Génère un PDF professionnel complet sur 4 pages."""
    from reportlab.platypus import Image
    import os
    
    buffer = io.BytesIO()
    
    # Fonction pour ajouter le bas de page à chaque page
    def ajouter_bas_de_page(canvas_obj, doc):
        """Ajoute le bas de page à chaque page du document."""
        canvas_obj.saveState()
        
        # Vérifier si l'image du bas de page existe
        if os.path.exists('bas_de_page.png'):
            try:
                # Positionner l'image en bas de page sur toute la largeur
                page_width, page_height = A4
                img_width = page_width  # Toute la largeur de la page
                img_height = 0.5*cm  # Hauteur de l'image
                x_position = 0  # Commencer depuis le bord gauche
                y_position = 0  # Position depuis le bas (bord inférieur)
                
                canvas_obj.drawImage('bas_de_page.png', 
                                   x_position, 
                                   y_position, 
                                   width=img_width, 
                                   height=img_height,
                                   preserveAspectRatio=False,  # Étirer pour prendre toute la largeur
                                   mask='auto')
            except Exception as e:
                # En cas d'erreur, ne rien afficher
                pass
        
        canvas_obj.restoreState()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=0.4*cm,  # Réduire davantage la marge du haut
        bottomMargin=2.5*cm  # Marge du bas pour le footer pleine largeur
    )
    
    styles = getSampleStyleSheet()
    
    # Styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontSize=11,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=10,
        spaceBefore=15,
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#333333'),
        leading=12,
        alignment=TA_JUSTIFY
    )
    
    bullet_style = ParagraphStyle(
        'BulletStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#333333'),
        leading=12,
        leftIndent=20,
        bulletIndent=10
    )
    
    # Style pour les cellules avec retours à la ligne
    cell_style = ParagraphStyle(
        'CellStyle',
        parent=styles['Normal'],
        fontSize=8,
        alignment=TA_CENTER,
        fontName='Helvetica',
        leading=10
    )
    
    elements = []
    
    # ==================== PAGE 1 ====================
    
    # Logo en haut à droite (première page seulement) - bien dimensionné
    if os.path.exists('leadway logo all formats big-02.png'):
        try:
            # Créer une table pour positionner le logo à droite
            logo_img = Image('leadway logo all formats big-02.png', width=3.5*cm, height=3*cm)
            logo_table = Table([[logo_img]], colWidths=[18*cm])
            logo_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'RIGHT'),
                ('VALIGN', (0, 0), (0, 0), 'TOP'),
            ]))
            elements.append(logo_table)
            elements.append(Spacer(1, 0.2*cm))  # Réduire l'espace
        except:
            pass
    
    # En-tête orange avec titre (sans logo)
    header_table_data = [[
        Paragraph("<b>PROPOSITION D'ASSURANCE SANTÉ</b>", 
                 ParagraphStyle('HeaderTitle', parent=styles['Normal'], 
                              fontSize=20, textColor=colors.whitesmoke, 
                              fontName='Helvetica-Bold', alignment=TA_CENTER))
    ]]
    
    header_table = Table(header_table_data, colWidths=[18*cm])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#E67E22')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 18),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 18),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    
    elements.append(header_table)
    elements.append(Spacer(1, 0.3*cm))  # Réduire l'espace
    
    # En-tête avec références
    ref_data = st.session_state.get('principal_data', {})
    ref_table_data = [
        ['REFERENCE:', ref_data.get('reference', 'LWA-00082-10-0735'), 'APPORTEUR:', ref_data.get('apporteur', 'ZOH BI')],
        ['PROSPECT:', ref_data.get('prospect', 'SOCIETE AKORA'), '', '']
    ]
    
    ref_table = Table(ref_table_data, colWidths=[3*cm, 5*cm, 3*cm, 5*cm])
    ref_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1a1a1a')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
        ('BACKGROUND', (2, 0), (2, 0), colors.HexColor('#f0f0f0')),
    ]))
    
    elements.append(ref_table)
    elements.append(Spacer(1, 0.5*cm))
    
    # I. OBJET DE LA COUVERTURE
    elements.append(Paragraph("<b>I. OBJET DE LA COUVERTURE</b>", section_title_style))
    elements.append(Paragraph(
        "La présente proposition constitue la complémentaire au régime de santé obligatoire de base : "
        "la Couverture Maladie Universelle (CMU). Elle a pour objet la couverture des dépenses d'ordre "
        "médical et chirurgical engagées à la suite de maladie, d'accident ou de maternité du souscripteur "
        "et des personnes désignées sous le vocable « personnes assurées » conformément au barème choisi "
        "par lui et mentionné aux conditions particulières.",
        normal_style
    ))
    elements.append(Spacer(1, 0.3*cm))
    
    # II. MODE DE GESTION
    elements.append(Paragraph("<b>II. MODE DE GESTION</b>", section_title_style))
    
    elements.append(Paragraph(
        "<b>• Tiers payant :</b> Il est offert au titre de la formule du TIERS PAYANT un système d'identification "
        "des assurés par carte à photo (Carte d'accès). Cette carte permettra au bénéficiaire de justifier de sa "
        "qualité d'assuré, tant auprès des centres de santé conventionnés qu'auprès des services compétents de la "
        "société. Sur présentation de la carte dans un établissement conventionné, à l'exception des actes nécessitant "
        "des accords préalables de l'assureur, l'assuré bénéficiera des prestations puis règlera le montant à sa charge "
        "(ticket modérateur).",
        bullet_style
    ))
    elements.append(Spacer(1, 0.2*cm))
    
    elements.append(Paragraph(
        "<b>• Système de remboursement :</b> Pour les prestations exécutées en dehors du réseau de centres conventionnés, "
        "le gestionnaire mandaté par l'Assureur, ANKARA SERVICE, s'engagera à procéder aux remboursements des frais dans "
        "un délai maximum de 30 jours selon les dispositions du barème de remboursement sur présentation des originaux des justificatifs.",
        bullet_style
    ))
    elements.append(Spacer(1, 0.3*cm))
    
    # III. AGE LIMITE DE SOUSCRIPTION
    elements.append(Paragraph("<b>III. AGE LIMITE DE SOUSCRIPTION</b>", section_title_style))
    elements.append(Paragraph(
        "<b>• Adultes :</b> 65 ans, avec une surprime âge à partir de 51 ans / Au-delà, garanti sur accord du directeur médical",
        bullet_style
    ))
    elements.append(Paragraph(
        "<b>• Enfants :</b> 21 ans, Jusqu'à 25 ans en cas de continuité de scolarité sous réserve de justificatifs.",
        bullet_style
    ))
    elements.append(Spacer(1, 0.3*cm))
    
    # IV. COMPOSITION FAMILIALE
    elements.append(Paragraph("<b>IV. COMPOSITION FAMILIALE</b>", section_title_style))
    elements.append(Paragraph(
        "La famille est réputée se composer de 05 personnes maximum (Adhérent principal + Conjoint légal ou non + 03 enfants). "
        "On appelle \"Enfant supplémentaire\" tout enfant au-delà du 3ème enfant. Si enfant non biologique, fournir un certificat "
        "de tutelle pour la prise en charge. Un questionnaire doit être impérativement renseigné et de bonne foi afin de déterminer "
        "avec exactitude la prime correspondante.",
        normal_style
    ))
    elements.append(Spacer(1, 0.3*cm))
    
    # V. DELAI DE CARENCE
    elements.append(Paragraph("<b>V. DELAI DE CARENCE</b>", section_title_style))
    elements.append(Paragraph("• 1 mois après la souscription pour les soins ordinaires ;", bullet_style))
    elements.append(Paragraph("• 6 mois pour la lunetterie et les prothèses ;", bullet_style))
    elements.append(Paragraph("• 9 mois pour les frais de maternité et d'accouchement ;", bullet_style))
    elements.append(Paragraph("• 12 mois pour les maladies chroniques survenant pour la première fois pendant le contrat ;", bullet_style))
    elements.append(Paragraph("• Abrogés en cas de continuité d'assurance, avec preuve à l'appui.", bullet_style))
    
    # Saut de page
    elements.append(PageBreak())
    
    # ==================== PAGE 2 ====================
    
    # VI. PAIEMENT DE LA PRIME
    elements.append(Paragraph("<b>VI. PAIEMENT DE LA PRIME (ARTICLE 13 CODE CIMA)</b>", section_title_style))
    elements.append(Paragraph(
        "La prime est payable au domicile de l'assureur ou de l'intermédiaire. La prise d'effet du contrat est subordonnée "
        "au paiement de la prime par le souscripteur.",
        normal_style
    ))
    elements.append(Spacer(1, 0.2*cm))
    elements.append(Paragraph(
        "Il est interdit aux entreprises d'assurance, sous peine des sanctions prévues à l'article 312, de souscrire un contrat "
        "d'assurance dont la prime n'est pas payée ou de renouveler un contrat d'assurance dont la prime n'a pas été payée.",
        normal_style
    ))
    elements.append(Spacer(1, 0.2*cm))
    elements.append(Paragraph(
        "Lorsqu'un chèque ou un effet remis en paiement de la prime revient impayé, l'assuré est mis en demeure de régulariser "
        "le paiement dans un délai de huit jours ouvrés à compter de la réception de l'acte ou de la lettre de mise en demeure. "
        "A l'expiration de ce délai, si la régularisation n'est pas effectuée, le contrat est résilié de plein droit.",
        normal_style
    ))
    elements.append(Spacer(1, 0.2*cm))
    elements.append(Paragraph(
        "La portion de prime courue reste acquise à l'assureur, sans préjudice des éventuels frais de poursuite et de recouvrement.",
        normal_style
    ))
    elements.append(Spacer(1, 0.4*cm))
    
    # VII. SOUSCRIPTION
    elements.append(Paragraph("<b>VII. SOUSCRIPTION</b>", section_title_style))
    elements.append(Paragraph("Les pièces à fournir pour la mise en place de la police sont les suivantes :", normal_style))
    elements.append(Spacer(1, 0.2*cm))
    elements.append(Paragraph("• La liste des personnes à assurer ;", bullet_style))
    elements.append(Paragraph("• Les questionnaires médicaux renseignés pour chaque adhérent et les membres de sa famille ;", bullet_style))
    elements.append(Paragraph("• Les copies des cartes CMU (ou les récépissés d'enrôlement en cas d'indisponibilité des cartes) ;", bullet_style))
    elements.append(Paragraph("• Les CNI pour les adultes et les extraits de naissance pour les enfants ;", bullet_style))
    elements.append(Paragraph("• Une photo couleur pour chaque personne ;", bullet_style))
    elements.append(Paragraph("• La copie du paiement (Espèces, chèque ou virement) ;", bullet_style))
    elements.append(Paragraph("• La preuve d'assurance antérieure afin de lever les délais de carence et assurer la continuité d'assurance.", bullet_style))
    elements.append(Spacer(1, 0.4*cm))
    
    # VIII. AUTRES DISPOSITIONS
    elements.append(Paragraph("<b>VIII. AUTRES DISPOSITIONS</b>", section_title_style))
    elements.append(Paragraph(
        "• L'acceptation définitive du risque est soumise à l'analyse du questionnaire médical dument renseigné et signé par le prospect ;",
        bullet_style
    ))
    elements.append(Paragraph(
        "• La cotation santé a été faite sous réserve de l'acceptation et de la souscription à d'autres risques d'accompagnement "
        "(Auto, MRH, RC, MRP, etc...) ;",
        bullet_style
    ))
    elements.append(Paragraph(
        "• Fournir obligatoirement les statistiques antérieures avant toute souscription (client ayant bénéficié d'une couverture "
        "sante sans interruption au cours de l'année N-1)",
        bullet_style
    ))
    elements.append(Paragraph("• Validité de la cotation : 03 Mois", bullet_style))
    elements.append(Spacer(1, 0.5*cm))
    
    # Date et signature
    date_signature = Paragraph(
        f"<b>Fait à Abidjan le {datetime.now().strftime('%d %B %Y')}</b>",
        ParagraphStyle('DateStyle', parent=normal_style, alignment=TA_RIGHT, fontName='Helvetica-Bold')
    )
    elements.append(date_signature)
    elements.append(Spacer(1, 0.3*cm))
    
    # Signature
    signature_paragraph = Paragraph(
        "<b>Pour L'ASSUREUR</b>",
        ParagraphStyle('SignatureLabel', parent=normal_style, alignment=TA_RIGHT, fontName='Helvetica-Bold', fontSize=10)
    )
    elements.append(signature_paragraph)
    elements.append(Spacer(1, 0.1*cm))  # Réduire l'espace pour coller la signature
    
    # Image de la signature
    if os.path.exists('signature.png'):
        try:
            signature_img = Image('signature.png', width=4*cm, height=2.5*cm)  # Réduire légèrement la hauteur
            signature_table = Table([[signature_img]], colWidths=[18*cm])  # Utiliser toute la largeur
            signature_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'RIGHT'),
                ('VALIGN', (0, 0), (0, 0), 'TOP'),
            ]))
            elements.append(signature_table)
        except:
            pass
    
    # Saut de page
    elements.append(PageBreak())
    
    # ==================== PAGE 3 - TABLEAU COMPARATIF ====================
    
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
                cell_value = str(row[col_name])
                if '\n' in cell_value:
                    cell_value_html = cell_value.replace('\n', '<br/>')
                    row_data.append(Paragraph(cell_value_html, cell_style))
                else:
                    row_data.append(cell_value)
        table_data.append(row_data)
    
    table = Table(table_data, colWidths=col_widths)
    
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a1a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#f8f9fa')),
        ('TEXTCOLOR', (0, 1), (0, -1), colors.HexColor('#495057')),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (0, -1), 8),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('FONTNAME', (1, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (1, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#1a1a1a')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (1, 1), (-1, -1), [colors.white, colors.HexColor('#f8f8f8')]),
    ])
    
    for idx, row in data_frame.iterrows():
        row_idx = idx + 1
        
        if row['Désignation'] in ['PRIME NETTE / PERSONNE', 'PRIME NETTE TOTALE']:
            table_style.add('BACKGROUND', (0, row_idx), (-1, row_idx), colors.HexColor('#f2e8d9'))
            table_style.add('FONTNAME', (0, row_idx), (-1, row_idx), 'Helvetica-Bold')
        
        if row['Désignation'] == 'PRIME TTC ANNUELLE':
            table_style.add('BACKGROUND', (0, row_idx), (-1, row_idx), colors.HexColor('#754015'))
            table_style.add('TEXTCOLOR', (0, row_idx), (-1, row_idx), colors.whitesmoke)
            table_style.add('FONTNAME', (0, row_idx), (-1, row_idx), 'Helvetica-Bold')
        
        if row['Désignation'] == 'MONTANT TOTAL À PAYER':
            table_style.add('BACKGROUND', (0, row_idx), (-1, row_idx), colors.HexColor('#145d33'))
            table_style.add('TEXTCOLOR', (0, row_idx), (-1, row_idx), colors.whitesmoke)
            table_style.add('FONTNAME', (0, row_idx), (-1, row_idx), 'Helvetica-Bold')
            table_style.add('FONTSIZE', (0, row_idx), (-1, row_idx), 10)
    
    table.setStyle(table_style)
    elements.append(table)
    elements.append(Spacer(1, 0.5*cm))
    
    # Note en bas de page 3
    note_text = Paragraph(
        "<i>Note : Les montants sont exprimés en FCFA. Proposition valable 3 mois.</i>",
        ParagraphStyle('NoteStyle', parent=normal_style, fontSize=8, textColor=colors.HexColor('#666666'), alignment=TA_CENTER)
    )
    elements.append(note_text)
    
    # Saut de page pour le barème
    elements.append(PageBreak())
    
    # ==================== PAGE 4 - IMAGE DU BAREME ====================
    
    elements.append(Paragraph("BARÈME DE REMBOURSEMENT", title_style))
    elements.append(Spacer(1, 0.5*cm))
    
    # Récupérer l'image du barème depuis session_state
    bareme_image_bytes = st.session_state.get('bareme_image_bytes', None)
    
    if bareme_image_bytes:
        # Créer un buffer temporaire pour l'image
        import io as io_lib
        img_buffer = io_lib.BytesIO(bareme_image_bytes)
        try:
            bareme_img = Image(img_buffer, width=16*cm, height=22*cm)
            elements.append(bareme_img)
        except:
            # Si erreur, afficher le placeholder
            placeholder_text = Paragraph(
                "<i>[Erreur de chargement de l'image du barème]</i>",
                ParagraphStyle('PlaceholderStyle', parent=normal_style, fontSize=10, textColor=colors.HexColor('#cc0000'), alignment=TA_CENTER)
            )
            elements.append(Spacer(1, 3*cm))
            elements.append(placeholder_text)
            elements.append(Spacer(1, 3*cm))
    else:
        # Pas d'image uploadée
        placeholder_text = Paragraph(
            "<i>[Image du barème de remboursement à insérer via l'interface]</i>",
            ParagraphStyle('PlaceholderStyle', parent=normal_style, fontSize=10, textColor=colors.HexColor('#999999'), alignment=TA_CENTER)
        )
        elements.append(Spacer(1, 3*cm))
        elements.append(placeholder_text)
        elements.append(Spacer(1, 3*cm))
        
        instruction_text = Paragraph(
            "Pour ajouter l'image du barème, veuillez la télécharger dans la section '📸 Image du Barème' avant de générer le PDF.",
            ParagraphStyle('InstructionStyle', parent=normal_style, fontSize=9, textColor=colors.HexColor('#666666'), alignment=TA_CENTER, fontName='Helvetica-Oblique')
        )
        elements.append(instruction_text)
    
    # Construire le PDF avec le bas de page sur chaque page
    doc.build(elements, onFirstPage=ajouter_bas_de_page, onLaterPages=ajouter_bas_de_page)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes


# ==============================================================================
# MODIFICATIONS 1 & 2: Fonction generer_recapitulatif_particulier modifiée
# ==============================================================================

def generer_recapitulatif_particulier(resultats_multi: Dict[int, Dict], baremes_affiches: List[str]):
    """Génère un récapitulatif comparatif intelligent avec regroupement automatique."""
    from collections import defaultdict
    import uuid
    from datetime import datetime
    
    # Récupérer les configurations et infos principales
    configurations_baremes = st.session_state.get('configurations_baremes', {})
    principal_data = st.session_state.get('principal_data', {})
    trop_percu = st.session_state.get('trop_percu_part_multi', 0.0)
    
    # === REGROUPEMENT INTELLIGENT ===
    # Grouper par (produit_name, type_couverture)
    groupes = defaultdict(list)
    
    for idx in range(len(baremes_affiches)):
        bareme_key = baremes_affiches[idx]
        resultat_data = resultats_multi[idx]
        resultat = resultat_data['resultat']
        config = configurations_baremes.get(idx, {})
        
        type_couv = config.get('type_couverture', 'Personne seule')
        produit_name = PRODUITS_PARTICULIERS_UI.get(bareme_key, bareme_key)
        
        # Clé de regroupement
        key = (produit_name, type_couv)
        
        groupes[key].append({
            'idx': idx,
            'bareme_key': bareme_key,
            'resultat': resultat,
            'config': config,
            'type_couverture': type_couv
        })
    
    # === CONSTRUCTION DES DONNÉES POUR LE PDF ===
    options_data = []
    groupes_tries = sorted(groupes.items(), key=lambda x: (x[0][0], x[0][1]))
    
    for (produit_name, type_couv), items in groupes_tries:
        # Déterminer les plafonds et garanties
        premier_item = items[0]
        bareme_key = premier_item['bareme_key']
        
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
        elif '70%' in produit_name or 'P70' in bareme_key or '70' in bareme_key or 'SAPHIR' in produit_name.upper():
            garantie = '70%'
            plafond_pers = format_currency(1_000_000)
            plafond_famille = format_currency(3_000_000)
        elif '80%' in produit_name or 'P80' in bareme_key or '80' in bareme_key or 'RUBIS' in produit_name.upper():
            garantie = '80%'
            plafond_pers = format_currency(2_500_000)
            plafond_famille = format_currency(7_500_000)
        elif '90%' in produit_name or 'P90' in bareme_key or '90' in bareme_key or 'ÉMERAUDE' in produit_name.upper():
            garantie = '90%'
            plafond_pers = format_currency(3_500_000)
            plafond_famille = format_currency(10_500_000)
        elif '100%' in produit_name or 'DIAMANT' in produit_name.upper():
            garantie = '100%'
            plafond_pers = format_currency(5_000_000)
            plafond_famille = format_currency(15_000_000)
        
        # Calculer les totaux et détails pour ce groupe
        population = len(items)
        type_proposition_label = "Individuel" if type_couv == 'Personne seule' else "Famille"
        
        # Fonction pour formater avec détail
        def format_avec_detail(values):
            # TOUJOURS afficher uniquement le total
            return format_currency(sum(values))
        
        # Collecter les valeurs
        primes_nettes = [item['resultat']['prime_nette_finale'] for item in items]
        surprimes_affection = []
        for item in items:
            res = item['resultat']
            prime_base = res.get('prime_nette_finale', 0)
            surprime_taux = res.get('surprime_risques_taux', 0)
            if surprime_taux > 0:
                surprime = prime_base * (surprime_taux / (100 + surprime_taux))
            else:
                surprime = 0
            surprimes_affection.append(surprime)
        
        surprimes_grossesse = [item['resultat'].get('surprime_grossesse', 0) for item in items]
        primes_lsp = [item['resultat'].get('prime_lsp', 0) for item in items]
        primes_assist_psy = [item['resultat'].get('prime_assist_psy', 0) for item in items]
        accessoires = [item['resultat']['accessoires'] for item in items]
        taxes = [item['resultat']['taxe'] for item in items]
        primes_ttc = [item['resultat']['prime_ttc_totale'] for item in items]
        
        # Prime nette annuelle totale
        prime_nette_annuelle_totale = sum(primes_nettes) + sum(surprimes_affection) + sum(surprimes_grossesse)
        
        # Montant total = Prime TTC + Trop perçu
        montant_total = sum(primes_ttc) + trop_percu
        
        options_data.append({
            'plafond_annuel_pers': plafond_pers,
            'plafond_annuel_famille': plafond_famille,
            'garanties': garantie,
            'type_proposition': type_proposition_label,
            'population': str(population),
            'enfants_supp': 'N/A',
            'prime_nette_personne': format_avec_detail(primes_nettes),
            'surprime_affection': format_avec_detail(surprimes_affection),
            'surprime_grossesse': format_avec_detail(surprimes_grossesse),
            'prime_totale_couverture_deces': format_avec_detail(primes_lsp),
            'assistance_psychologique': format_avec_detail(primes_assist_psy),
            'prime_nette_annuelle_totale': format_currency(prime_nette_annuelle_totale),
            'accessoires': format_avec_detail(accessoires),
            'taxes': format_currency(sum(taxes)),
            'prime_ttc_annuelle': format_currency(sum(primes_ttc)),
            'trop_percu': format_currency(trop_percu) if trop_percu > 0 else "0 FCFA",
            'montant_total': format_currency(montant_total)
        })
    
    # === CONSTRUCTION DU DATAFRAME ===
    designations = [
        'PLAFOND ANNUEL / PERS',
        'PLAFOND ANNUEL / FAM',
        'GESTIONNAIRE', 
        'TERRITORIALITÉ', 
        'GARANTIES', 
        'TYPE DE PROPOSITION', 
        'POPULATION', 
        'PRIME NETTE / PERSONNE',
        'SURPRIME AFFECTION',
        'SURPRIME GROSSESSE',
        'PRIME TOTALE LSP',
        'PRIME ASSISTANCE PSY',
        'PRIME NETTE TOTALE',
        'ACCESSOIRES',
        'TAXES',
        'PRIME TTC ANNUELLE',
        'TROP PERÇU',
        'MONTANT TOTAL À PAYER'
    ]
    
    nb_options = len(options_data)
    df_dict = {'Désignation': designations}
    
    for i in range(nb_options):
        option_values = [
            options_data[i]['plafond_annuel_pers'],
            options_data[i]['plafond_annuel_famille'],
            'ANKARA SERVICE', 
            'COTE D\'IVOIRE', 
            options_data[i]['garanties'], 
            options_data[i]['type_proposition'], 
            options_data[i]['population'], 
            options_data[i]['prime_nette_personne'], 
            options_data[i]['surprime_affection'], 
            options_data[i]['surprime_grossesse'], 
            options_data[i]['prime_totale_couverture_deces'], 
            options_data[i]['assistance_psychologique'], 
            options_data[i]['prime_nette_annuelle_totale'], 
            options_data[i]['accessoires'], 
            options_data[i]['taxes'], 
            options_data[i]['prime_ttc_annuelle'],
            options_data[i]['trop_percu'],
            options_data[i]['montant_total']
        ]
        df_dict[f'OPTION {i+1}'] = option_values
    
    data_frame = pd.DataFrame(df_dict)
    
    pdf_bytes = generer_pdf_proposition(data_frame, options_data, nb_options)
    
    st.success(f"✅ Proposition commerciale générée avec succès ({nb_options} option{'s' if nb_options > 1 else ''}) !")
    
    # Stocker les données PDF dans session_state pour sauvegarde ultérieure
    st.session_state['pdf_options_data'] = options_data
    st.session_state['pdf_principal_data'] = principal_data
    st.session_state['pdf_bytes_generated'] = pdf_bytes
    st.session_state['pdf_nb_options'] = nb_options
    
    col_dl, col_save = st.columns(2)
    
    with col_dl:
        st.download_button(
            label="📥 TÉLÉCHARGER LA PROPOSITION (PDF)",
            data=pdf_bytes,
            file_name=f"Proposition_Sante_Particulier_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )
    
    with col_save:
        if st.session_state.db_manager is not None:
            if st.button("💾 ENREGISTRER AVEC PDF", type="secondary", use_container_width=True, key="btn_save_with_pdf"):
                # Récupérer le PDF depuis session_state (car pdf_bytes n'existe plus après rerun)
                pdf_bytes_to_save = st.session_state.get('pdf_bytes_generated')
                saved_options_data = st.session_state.get('pdf_options_data')
                saved_principal_data = st.session_state.get('pdf_principal_data')
                if not pdf_bytes_to_save:
                    st.error("❌ Aucun PDF généré. Cliquez d'abord sur 'GÉNÉRER PROPOSITION COMMERCIALE'.")
                else:
                    try:
                        nb_saved = 0
                        errors = []
                        
                        for idx in range(len(baremes_affiches)):
                            bareme_key = baremes_affiches[idx]
                            resultat = resultats_multi[idx]['resultat']
                            config = configurations_baremes.get(idx, {})
                            
                            client_info = {
                                'nom': saved_principal_data.get('prospect', '') if saved_principal_data else '',
                                'prenom': '',
                                'type_couverture': config.get('type_couverture', 'Personne seule'),
                                'nb_adultes': 2 if config.get('type_couverture') == 'Famille' else 1,
                                'nb_enfants': 3 + config.get('enfants_supp', 0) if config.get('type_couverture') == 'Famille' else 0
                            }
                            
                            success = sauvegarder_cotation_supabase(
                                type_marche="Particulier",
                                produit=PRODUITS_PARTICULIERS_UI[bareme_key],
                                resultat=resultat,
                                client_info=client_info,
                                duree_contrat=resultat.get('facteurs', {}).get('duree_contrat', 12),
                                reduction_commerciale=resultat.get('facteurs', {}).get('reduction', 0),
                                pdf_options_data=saved_options_data,
                                pdf_principal_data=saved_principal_data,
                                pdf_bytes=pdf_bytes_to_save
                            )
                            
                            if success:
                                nb_saved += 1
                            else:
                                errors.append(PRODUITS_PARTICULIERS_UI[bareme_key])
                        
                        if nb_saved > 0:
                            st.balloons()
                            st.success(f"✅ {nb_saved} cotation(s) enregistrée(s) avec le PDF !")
                        
                        if errors:
                            st.error(f"❌ Échec pour: {', '.join(errors)}")
                            
                    except Exception as e:
                        st.error(f"❌ Erreur: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())

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
    
    # Charger les polices depuis Supabase
    polices_data = []
    
    try:
        from supabase_config import db
        polices_list = db.lister_polices(limite=100)
        
        for police in polices_list:
            date_effet = police.get('date_effet', '')
            date_echeance = police.get('date_echeance', '')
            
            polices_data.append({
                'id': police.get('id'),
                'N° Police': police.get('numero_police', 'N/A'),
                'Assuré': police.get('assure_principal', 'N/A'),
                'Type': police.get('type_police', 'N/A').capitalize(),
                'Produit': police.get('produit', 'N/A'),
                'Date effet': date_effet[:10] if date_effet else 'N/A',
                'Date échéance': date_echeance[:10] if date_echeance else 'N/A',
                'Prime annuelle': f"{int(police.get('prime_annuelle', 0) or 0):,} FCFA".replace(',', ' '),
                'Statut': police.get('statut', 'en_cours').replace('_', ' ').capitalize(),
                '_prime': police.get('prime_annuelle', 0) or 0
            })
    except Exception as e:
        st.error(f"Erreur chargement polices : {e}")
    
    # === BARRE DE RECHERCHE ===
    with st.container(border=True):
        col_s1, col_s2, col_s3, col_s4 = st.columns([2, 1, 1, 1])
        
        with col_s1:
            search_police = st.text_input("🔍 Rechercher", placeholder="N° police, assuré...", key="search_police")
        
        with col_s2:
            filter_type_police = st.selectbox("Type", ["Tous", "Particulier", "Corporate"], key="filter_type_police")
        
        with col_s3:
            filter_statut_police = st.selectbox("Statut", ["Tous", "En cours", "Suspendue", "Résiliée"], key="filter_statut_police")
        
        with col_s4:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔄 Rafraîchir", key="btn_refresh_polices", use_container_width=True):
                st.rerun()
    
    st.markdown("---")
    
    # === FILTRAGE ===
    polices_filtered = polices_data.copy()
    
    if search_police:
        polices_filtered = [p for p in polices_filtered if 
            search_police.lower() in p['N° Police'].lower() or
            search_police.lower() in p['Assuré'].lower()
        ]
    
    if filter_type_police != "Tous":
        polices_filtered = [p for p in polices_filtered if p['Type'].lower() == filter_type_police.lower()]
    
    if filter_statut_police != "Tous":
        polices_filtered = [p for p in polices_filtered if p['Statut'].lower() == filter_statut_police.lower()]
    
    # === STATISTIQUES ===
    col_p1, col_p2, col_p3, col_p4 = st.columns(4)
    
    with col_p1:
        st.metric("📋 Total Polices", len(polices_filtered))
    
    with col_p2:
        nb_actives = len([p for p in polices_filtered if p['Statut'] == 'En cours'])
        st.metric("✅ Actives", nb_actives)
    
    with col_p3:
        nb_suspendues = len([p for p in polices_filtered if p['Statut'] in ['Suspendue', 'Résiliée']])
        st.metric("⏸️ Suspendues", nb_suspendues)
    
    with col_p4:
        total_primes = sum([p['_prime'] for p in polices_filtered])
        st.metric("💰 Primes", f"{total_primes/1000000:.1f}M" if total_primes >= 1000000 else f"{int(total_primes):,}".replace(',', ' '))
    
    st.markdown("---")
    
    # === TABLEAU DES POLICES ===
    if len(polices_filtered) == 0:
        st.info("📭 Aucune police trouvée. Les polices sont créées à partir des cotations finalisées.")
    else:
        df_polices = pd.DataFrame(polices_filtered)
        colonnes_police = ['N° Police', 'Assuré', 'Type', 'Produit', 'Date effet', 'Date échéance', 'Prime annuelle', 'Statut']
        
        st.dataframe(
            df_polices[colonnes_police],
            use_container_width=True,
            hide_index=True
        )
        
        # === ACTIONS SUR UNE POLICE ===
        st.markdown("---")
        st.subheader("⚡ Actions sur Police")
        
        with st.container(border=True):
            col_sel_p, col_act_p = st.columns([2, 1])
            
            with col_sel_p:
                options_polices = [f"{p['N° Police']} - {p['Assuré']}" for p in polices_filtered]
                police_selectionnee = st.selectbox("Sélectionner une police", options_polices, key="select_police_action")
            
            idx_police = options_polices.index(police_selectionnee) if police_selectionnee and options_polices else 0
            police_data = polices_filtered[idx_police] if polices_filtered else None
            
            with col_act_p:
                action_police = st.selectbox("Action", ["📄 Voir détails", "📥 Télécharger attestation", "✏️ Modifier statut"], key="action_police")
            
            col_act1, col_act2 = st.columns(2)
            
            with col_act1:
                if action_police == "📄 Voir détails" and police_data:
                    if st.button("👁️ Afficher", type="primary", use_container_width=True):
                        st.markdown("### Détails de la Police")
                        col_d1, col_d2 = st.columns(2)
                        with col_d1:
                            st.write(f"**N° Police:** {police_data['N° Police']}")
                            st.write(f"**Assuré:** {police_data['Assuré']}")
                            st.write(f"**Type:** {police_data['Type']}")
                            st.write(f"**Produit:** {police_data['Produit']}")
                        with col_d2:
                            st.write(f"**Date effet:** {police_data['Date effet']}")
                            st.write(f"**Date échéance:** {police_data['Date échéance']}")
                            st.write(f"**Prime annuelle:** {police_data['Prime annuelle']}")
                            st.write(f"**Statut:** {police_data['Statut']}")
            
            with col_act2:
                if action_police == "✏️ Modifier statut" and police_data:
                    new_statut_police = st.selectbox("Nouveau statut", ["en_cours", "suspendue", "resiliee"], key="new_statut_police")
                    if st.button("✅ Appliquer", type="primary", use_container_width=True, key="btn_update_police"):
                        try:
                            result = db.mettre_a_jour_police(police_data['id'], {'statut': new_statut_police})
                            if result.get('success'):
                                st.success("✅ Statut mis à jour !")
                                st.rerun()
                            else:
                                st.error(f"Erreur : {result.get('error')}")
                        except Exception as e:
                            st.error(f"Erreur : {e}")

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
        
        # === BARRE DE RECHERCHE ===
        with st.container(border=True):
            col_search1, col_search2, col_search3, col_search4 = st.columns([2, 1, 1, 1])
            
            with col_search1:
                search_text = st.text_input("🔍 Rechercher", placeholder="N° cotation, client, produit...", key="search_cotation")
            
            with col_search2:
                filter_branche = st.selectbox("Branche", ["Toutes", "Particulier", "Corporate"], key="filter_branche")
            
            with col_search3:
                filter_statut = st.selectbox("Statut", ["Tous", "En attente", "En cours", "Finalisé", "Annulé"], key="filter_statut")
            
            with col_search4:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🔄 Rafraîchir", key="btn_refresh_list", use_container_width=True):
                    st.rerun()
        
        st.markdown("---")
        
        # Charger les données réelles depuis Supabase
        data_cotations = []
        devis_bruts = []  # Pour stocker les données brutes
        
        if st.session_state.db_manager is not None:
            try:
                devis_list = st.session_state.db_manager.recuperer_devis(limit=100)
                devis_bruts = devis_list  # Garder les données brutes
                
                for devis in devis_list:
                    date_creation = devis.get('date_creation', '')
                    if date_creation:
                        try:
                            dt = datetime.fromisoformat(date_creation.replace('Z', '+00:00'))
                            date_str = dt.strftime("%d/%m/%Y")
                        except:
                            date_str = date_creation[:10] if len(date_creation) >= 10 else date_creation
                    else:
                        date_str = "N/A"
                    
                    prime_nette = devis.get('prime_nette', 0) or 0
                    prime_finale = devis.get('prime_finale', 0) or 0
                    
                    data_cotations.append({
                        "id": devis.get('id', 0),
                        "N° Cotation": devis.get('numero_devis', 'N/A'),
                        "Branche": devis.get('type_marche', 'N/A'),
                        "Nom client": devis.get('nom_client', '') or devis.get('entreprise', 'N/A'),
                        "Produit": devis.get('produit', 'N/A'),
                        "Durée": f"{devis.get('duree_contrat', 12)} mois",
                        "Prime TTC": f"{int(prime_finale):,} FCFA".replace(',', ' '),
                        "Créé le": date_str,
                        "Statut": devis.get('statut', 'En attente'),
                        # Données brutes pour PDF
                        "_prime_nette": prime_nette,
                        "_prime_finale": prime_finale,
                        "_accessoires": devis.get('accessoires', 0) or 0,
                        "_taxe": devis.get('taxe', 0) or 0,
                        "_services": devis.get('services', 0) or 0,
                        "_type_couverture": devis.get('type_couverture', ''),
                        "_duree": devis.get('duree_contrat', 12),
                        "_details": devis.get('details', {}),
                        "_pdf_data": devis.get('pdf_data')  # PDF stocké en base64
                    })
                    
            except Exception as e:
                st.error(f"❌ Erreur lors du chargement : {str(e)}")
        else:
            st.warning("⚠️ Connexion Supabase non disponible.")
        
        # === FILTRAGE ===
        df_cotations_filtered = data_cotations.copy()
        
        # Filtre par texte
        if search_text:
            df_cotations_filtered = [c for c in df_cotations_filtered if 
                search_text.lower() in c['N° Cotation'].lower() or
                search_text.lower() in c['Nom client'].lower() or
                search_text.lower() in c['Produit'].lower()
            ]
        
        # Filtre par branche
        if filter_branche != "Toutes":
            df_cotations_filtered = [c for c in df_cotations_filtered if c['Branche'] == filter_branche]
        
        # Filtre par statut
        if filter_statut != "Tous":
            df_cotations_filtered = [c for c in df_cotations_filtered if c['Statut'] == filter_statut]
        
        # === STATISTIQUES ===
        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        total_cotations = len(df_cotations_filtered)
        
        with col_stat1:
            st.metric("📊 Total", total_cotations)
        with col_stat2:
            nb_finalise = len([c for c in df_cotations_filtered if c['Statut'] == 'Finalisé'])
            st.metric("✅ Finalisées", nb_finalise)
        with col_stat3:
            nb_en_attente = len([c for c in df_cotations_filtered if c['Statut'] in ['En cours', 'En attente']])
            st.metric("⏳ En attente", nb_en_attente)
        with col_stat4:
            try:
                prime_totale = sum([c['_prime_finale'] for c in df_cotations_filtered])
                st.metric("💰 Volume", f"{prime_totale/1000000:.1f}M" if prime_totale >= 1000000 else f"{int(prime_totale):,}".replace(',', ' '))
            except:
                st.metric("💰 Volume", "0")
        
        st.markdown("---")
        
        # === TABLEAU ===
        if len(df_cotations_filtered) == 0:
            st.info("📭 Aucune cotation trouvée.")
        else:
            # Créer DataFrame pour affichage
            df_display = pd.DataFrame(df_cotations_filtered)
            colonnes_affichage = ['N° Cotation', 'Branche', 'Nom client', 'Produit', 'Durée', 'Prime TTC', 'Créé le', 'Statut']
            
            st.dataframe(
                df_display[colonnes_affichage],
                use_container_width=True,
                hide_index=True
            )
            
            # === ACTIONS SUR UNE COTATION ===
            st.markdown("---")
            st.subheader("⚡ Actions")
            
            with st.container(border=True):
                col_select, col_action = st.columns([2, 1])
                
                with col_select:
                    options_cotations = [f"{c['N° Cotation']} - {c['Nom client']}" for c in df_cotations_filtered]
                    cotation_selectionnee = st.selectbox(
                        "Sélectionner une cotation",
                        options_cotations,
                        key="select_cotation_action"
                    )
                
                # Trouver la cotation sélectionnée
                idx_selected = options_cotations.index(cotation_selectionnee) if cotation_selectionnee else 0
                cotation_data = df_cotations_filtered[idx_selected] if df_cotations_filtered else None
                
                with col_action:
                    action_type = st.selectbox(
                        "Action",
                        ["📥 Télécharger PDF", "📋 Convertir en Police", "✏️ Modifier statut", "🗑️ Supprimer"],
                        key="action_type_cotation"
                    )
                
                # Bouton d'exécution
                col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)
                
                with col_btn1:
                    if action_type == "📥 Télécharger PDF":
                        if cotation_data and st.button("📥 Télécharger PDF", type="primary", use_container_width=True):
                            try:
                                import base64
                                
                                # SOLUTION RADICALE : Récupérer le PDF BINAIRE stocké
                                pdf_base64 = cotation_data.get('_pdf_data')
                                
                                if pdf_base64:
                                    # Décoder le PDF stocké en base64
                                    pdf_bytes = base64.b64decode(pdf_base64)
                                    
                                    st.download_button(
                                        "⬇️ Télécharger le PDF ORIGINAL",
                                        data=pdf_bytes,
                                        file_name=f"Proposition_{cotation_data['N° Cotation']}.pdf",
                                        mime="application/pdf"
                                    )
                                    st.success("✅ PDF 100% identique à l'original !")
                                else:
                                    # Fallback pour anciennes cotations sans PDF stocké
                                    st.warning("⚠️ Pas de PDF stocké. Recréez la cotation avec 'ENREGISTRER AVEC PDF'.")
                                    
                                    # Essayer de régénérer avec les données disponibles
                                    details = cotation_data.get('_details', {})
                                    pdf_options_data = details.get('pdf_options_data')
                                    
                                    if pdf_options_data:
                                        designations = [
                                            'PLAFOND ANNUEL / PERS', 'PLAFOND ANNUEL / FAM', 'GESTIONNAIRE', 
                                            'TERRITORIALITÉ', 'GARANTIES', 'TYPE DE PROPOSITION', 'POPULATION', 
                                            'PRIME NETTE / PERSONNE', 'SURPRIME AFFECTION', 'SURPRIME GROSSESSE',
                                            'PRIME TOTALE LSP', 'PRIME ASSISTANCE PSY', 'PRIME NETTE TOTALE',
                                            'ACCESSOIRES', 'TAXES', 'PRIME TTC ANNUELLE', 'TROP PERÇU', 'MONTANT TOTAL À PAYER'
                                        ]
                                        
                                        nb_options = len(pdf_options_data)
                                        df_dict = {'Désignation': designations}
                                        
                                        for i in range(nb_options):
                                            opt = pdf_options_data[i]
                                            option_values = [
                                                opt.get('plafond_annuel_pers', 'N/A'),
                                                opt.get('plafond_annuel_famille', 'N/A'),
                                                'ANKARA SERVICE', "COTE D'IVOIRE",
                                                opt.get('garanties', 'N/A'),
                                                opt.get('type_proposition', 'N/A'),
                                                opt.get('population', '1'),
                                                opt.get('prime_nette_personne', '0 FCFA'),
                                                opt.get('surprime_affection', '0 FCFA'),
                                                opt.get('surprime_grossesse', '0 FCFA'),
                                                opt.get('prime_totale_couverture_deces', '0 FCFA'),
                                                opt.get('assistance_psychologique', '0 FCFA'),
                                                opt.get('prime_nette_annuelle_totale', '0 FCFA'),
                                                opt.get('accessoires', '0 FCFA'),
                                                opt.get('taxes', '0 FCFA'),
                                                opt.get('prime_ttc_annuelle', '0 FCFA'),
                                                opt.get('trop_percu', '0 FCFA'),
                                                opt.get('montant_total', '0 FCFA')
                                            ]
                                            df_dict[f'OPTION {i+1}'] = option_values
                                        
                                        data_frame = pd.DataFrame(df_dict)
                                        pdf_bytes = generer_pdf_proposition(data_frame, pdf_options_data, nb_options)
                                        
                                        st.download_button(
                                            "⬇️ Télécharger (régénéré)",
                                            data=pdf_bytes,
                                            file_name=f"Proposition_{cotation_data['N° Cotation']}.pdf",
                                            mime="application/pdf"
                                        )
                            except Exception as e:
                                st.error(f"Erreur PDF : {e}")
                
                with col_btn2:
                    if action_type == "📋 Convertir en Police":
                        if cotation_data and st.button("📋 Créer Police", type="primary", use_container_width=True):
                            if cotation_data['Statut'] != 'Finalisé':
                                st.warning("⚠️ Seules les cotations finalisées peuvent être converties en police.")
                            else:
                                try:
                                    # Générer numéro de police
                                    numero_police = f"POL-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
                                    
                                    # Créer la police dans Supabase via SupabaseManager
                                    from supabase_config import db
                                    
                                    police_data = {
                                        'numero_police': numero_police,
                                        'cotation_id': cotation_data['id'],
                                        'assure_principal': cotation_data['Nom client'],
                                        'type_police': cotation_data['Branche'].lower(),
                                        'produit': cotation_data['Produit'],
                                        'date_effet': datetime.now().strftime('%Y-%m-%d'),
                                        'date_echeance': (datetime.now().replace(year=datetime.now().year + 1)).strftime('%Y-%m-%d'),
                                        'prime_annuelle': cotation_data['_prime_finale'],
                                        'statut': 'en_cours'
                                    }
                                    
                                    result = db.creer_police(police_data)
                                    
                                    if result.get('success'):
                                        st.success(f"✅ Police **{numero_police}** créée avec succès !")
                                        st.balloons()
                                    else:
                                        st.error(f"Erreur : {result.get('error')}")
                                except Exception as e:
                                    st.error(f"Erreur : {e}")
                
                with col_btn3:
                    if action_type == "✏️ Modifier statut":
                        nouveau_statut = st.selectbox("Nouveau statut", ["En attente", "En cours", "Finalisé", "Annulé"], key="new_status")
                        if cotation_data and st.button("✅ Appliquer", type="primary", use_container_width=True):
                            try:
                                success = st.session_state.db_manager.mettre_a_jour_statut_devis(
                                    cotation_data['N° Cotation'],
                                    nouveau_statut
                                )
                                if success:
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Erreur : {e}")
                
                with col_btn4:
                    if action_type == "🗑️ Supprimer":
                        st.warning("⚠️ Action irréversible")
                        if cotation_data:
                            # Confirmation de suppression
                            confirm_key = f"confirm_delete_{cotation_data['N° Cotation']}"
                            if st.checkbox("Je confirme la suppression", key=confirm_key):
                                if st.button("🗑️ SUPPRIMER", type="primary", use_container_width=True):
                                    try:
                                        success = st.session_state.db_manager.supprimer_devis(
                                            cotation_data['N° Cotation']
                                        )
                                        if success:
                                            st.success("✅ Cotation supprimée !")
                                            st.rerun()
                                        else:
                                            st.error("❌ Échec de la suppression")
                                    except Exception as e:
                                        st.error(f"Erreur : {e}")

    # --- PARCOURS PARTICULIER ---
    with tab_particulier:
        
        # === STYLES DES SECTIONS ===
        st.markdown("""
        <style>
        .section-header {
            background: linear-gradient(135deg, #6A0DAD 0%, #8B5CF6 100%);
            color: white;
            padding: 12px 20px;
            border-radius: 10px;
            margin: 20px 0 15px 0;
            font-size: 18px;
            font-weight: 600;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # === SECTION 1: INFORMATIONS DE RÉFÉRENCE ===
        st.markdown('<div class="section-header">📋 ÉTAPE 1 : Informations de Référence</div>', unsafe_allow_html=True)
        with st.container(border=True):
            col_ref1, col_ref2 = st.columns(2)
            
            with col_ref1:
                reference = st.text_input(
                    "Référence",
                    value=st.session_state.get('reference_cotation', 'LWA-00082-10-0735'),
                    key="reference_cotation",
                    help="Numéro de référence de la cotation"
                )
                prospect = st.text_input(
                    "Prospect / Société",
                    value=st.session_state.get('prospect_cotation', 'SOCIETE AKORA'),
                    key="prospect_cotation",
                    help="Nom du prospect ou de la société"
                )
            
            with col_ref2:
                apporteur = st.text_input(
                    "Apporteur",
                    value=st.session_state.get('apporteur_cotation', 'ZOH BI'),
                    key="apporteur_cotation",
                    help="Nom de l'apporteur d'affaires"
                )
            
            # Stocker dans session_state
            if 'principal_data' not in st.session_state:
                st.session_state.principal_data = {}
            
            st.session_state.principal_data['reference'] = reference
            st.session_state.principal_data['prospect'] = prospect
            st.session_state.principal_data['apporteur'] = apporteur
        
        # === SECTION 2: PROFIL & DONNÉES DE COUVERTURE ===
        st.markdown('<div class="section-header">👤 ÉTAPE 2 : Profil & Données de Couverture</div>', unsafe_allow_html=True)
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
                        
        # === SECTION 3: ANALYSE MÉDICALE ===
        st.markdown('<div class="section-header">🏥 ÉTAPE 3 : Analyse Médicale & Surprimes</div>', unsafe_allow_html=True)
        
        # Structure pour stocker les infos médicales par barème
        infos_medicales_par_bareme = {}
        # Mode médical par barème activé automatiquement pour "différentes propositions"
        mode_medical_par_bareme = (type_cotation == "Une cotation, différentes propositions")
        
        # CAS SPÉCIAL : MODE PAR BARÈME
        if mode_medical_par_bareme:
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
        
        # === SECTION 4: CALCUL FINAL ===
        st.markdown('<div class="section-header">💰 ÉTAPE 4 : Calcul Final de la Prime</div>', unsafe_allow_html=True)
        
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
                        
                        col_man3, col_man4 = st.columns(2)
                        
                        prime_lsp_manuelle = col_man3.number_input(
                            "Prime LSP (FCFA)",
                            min_value=0.0,
                            value=20000.0,
                            step=1000.0,
                            key=f"prime_lsp_manuel_{bareme_key}",
                            help="Prime Lettre de Sortie Provisoire"
                        )
                        
                        prime_assist_psy_manuelle = col_man4.number_input(
                            "Prime Assistance Psychologique (FCFA)",
                            min_value=0.0,
                            value=35000.0,
                            step=1000.0,
                            key=f"prime_assist_psy_manuel_{bareme_key}",
                            help="Prime d'assistance psychologique"
                        )
                        
                        st.session_state.baremes_speciaux_info[bareme_key] = {
                            'plafond_personne': plafond_personne,
                            'plafond_famille': plafond_famille,
                            'taux_couverture': taux_couverture,
                            'prime_lsp': prime_lsp_manuelle,
                            'prime_assist_psy': prime_assist_psy_manuelle
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
                                    
                                    # Récupérer les primes LSP et Assistance Psy pour barème spécial
                                    prime_lsp_man = None
                                    prime_assist_psy_man = None
                                    if bareme_key == 'bareme_special':
                                        bareme_info = st.session_state.baremes_speciaux_info.get(bareme_key, {})
                                        prime_lsp_man = bareme_info.get('prime_lsp')
                                        prime_assist_psy_man = bareme_info.get('prime_assist_psy')
                                    
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
                                        surprime_manuelle_pourcent=surprime_globale_pourcent,
                                        prime_lsp_manuelle=prime_lsp_man,
                                        prime_assist_psy_manuelle=prime_assist_psy_man
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
                        # Stocker les résultats pour persistence
                        st.session_state['resultats_multi_saved'] = resultats_multi
                        st.session_state['baremes_affiches_saved'] = baremes_affiches
                        
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
                        
                        # Bouton de génération du récapitulatif pour option unique
                        st.markdown("---")
                        if st.button("📝 GÉNÉRER PROPOSITION COMMERCIALE", key="btn_generer_prop_simple", type="secondary"):
                            st.session_state['proposition_generee'] = True
                            generer_recapitulatif_particulier(resultats_multi, baremes_affiches)
                        
                        # Afficher les boutons si la proposition a déjà été générée (persistence)
                        if st.session_state.get('proposition_generee') and st.session_state.get('pdf_bytes_generated'):
                            st.markdown("---")
                            col_dl2, col_save2 = st.columns(2)
                            
                            with col_dl2:
                                st.download_button(
                                    label="📥 TÉLÉCHARGER LE PDF",
                                    data=st.session_state['pdf_bytes_generated'],
                                    file_name=f"Proposition_Sante_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                                    mime="application/pdf",
                                    type="primary",
                                    use_container_width=True,
                                    key="dl_btn_persist"
                                )
                            
                            with col_save2:
                                if st.button("💾 ENREGISTRER AVEC PDF", type="secondary", use_container_width=True, key="btn_save_persist"):
                                    pdf_bytes_to_save = st.session_state.get('pdf_bytes_generated')
                                    saved_options_data = st.session_state.get('pdf_options_data')
                                    saved_principal_data = st.session_state.get('pdf_principal_data')
                                    saved_resultats = st.session_state.get('resultats_multi_saved', resultats_multi)
                                    saved_baremes = st.session_state.get('baremes_affiches_saved', baremes_affiches)
                                    configs_baremes = st.session_state.get('configurations_baremes', {})
                                    
                                    if pdf_bytes_to_save:
                                        try:
                                            for idx in range(len(saved_baremes)):
                                                bareme_key = saved_baremes[idx]
                                                resultat = saved_resultats[idx]['resultat']
                                                config = configs_baremes.get(idx, {})
                                                
                                                client_info = {
                                                    'nom': saved_principal_data.get('prospect', '') if saved_principal_data else '',
                                                    'prenom': '',
                                                    'type_couverture': config.get('type_couverture', 'Personne seule'),
                                                    'nb_adultes': 2 if config.get('type_couverture') == 'Famille' else 1,
                                                    'nb_enfants': 3 + config.get('enfants_supp', 0) if config.get('type_couverture') == 'Famille' else 0
                                                }
                                                
                                                success = sauvegarder_cotation_supabase(
                                                    type_marche="Particulier",
                                                    produit=PRODUITS_PARTICULIERS_UI.get(bareme_key, bareme_key),
                                                    resultat=resultat,
                                                    client_info=client_info,
                                                    duree_contrat=resultat.get('facteurs', {}).get('duree_contrat', 12),
                                                    reduction_commerciale=resultat.get('facteurs', {}).get('reduction', 0),
                                                    pdf_options_data=saved_options_data,
                                                    pdf_principal_data=saved_principal_data,
                                                    pdf_bytes=pdf_bytes_to_save
                                                )
                                            
                                            st.balloons()
                                            st.success("✅ Cotation enregistrée avec le PDF !")
                                            # Réinitialiser l'état
                                            st.session_state['proposition_generee'] = False
                                        except Exception as e:
                                            st.error(f"❌ Erreur: {e}")
                                    else:
                                        st.error("❌ Aucun PDF en mémoire")
                        
                        # === BOUTON SAUVEGARDE SUPABASE (1 barème) ===
                        st.markdown("---")
                        with st.container(border=True):
                            if st.session_state.db_manager is not None:
                                if st.button("💾 ENREGISTRER LA COTATION", key="btn_save_supabase_single", type="primary", use_container_width=True):
                                    principal_data = st.session_state.get('principal_data', {})
                                    configs_baremes = st.session_state.get('configurations_baremes', {})
                                    config = configs_baremes.get(0, {})
                                    
                                    client_info = {
                                        'nom': principal_data.get('prospect', ''),
                                        'prenom': '',
                                        'type_couverture': config.get('type_couverture', 'Personne seule'),
                                        'nb_adultes': 2 if config.get('type_couverture') == 'Famille' else 1,
                                        'nb_enfants': 3 + config.get('enfants_supp', 0) if config.get('type_couverture') == 'Famille' else 0
                                    }
                                    
                                    success = sauvegarder_cotation_supabase(
                                        type_marche="Particulier",
                                        produit=PRODUITS_PARTICULIERS_UI[bareme_key],
                                        resultat=resultat,
                                        client_info=client_info,
                                        duree_contrat=resultat.get('facteurs', {}).get('duree_contrat', 12),
                                        reduction_commerciale=resultat.get('facteurs', {}).get('reduction', 0)
                                    )
                                    if success:
                                        st.balloons()
                            else:
                                st.warning("⚠️ Connexion Supabase non disponible.")
                    
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
                                    
                                    col_force1, col_force2 = st.columns(2)
                                    
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
                                    
                                    col_force3, col_force4 = st.columns(2)
                                    
                                    prime_lsp_originale = resultat_original.get('prime_lsp', 20000)
                                    prime_assist_psy_originale = resultat_original.get('prime_assist_psy', 35000)
                                    
                                    with col_force3:
                                        prime_lsp_forcee = st.number_input(
                                            "Prime LSP Forcée (FCFA)",
                                            min_value=0.0,
                                            value=float(prime_lsp_originale),
                                            step=1000.0,
                                            key=f"prime_lsp_forcee_part_{idx}",
                                            help="Prime Lettre de Sortie Provisoire"
                                        )
                                    
                                    with col_force4:
                                        prime_assist_psy_forcee = st.number_input(
                                            "Prime Assistance Psy Forcée (FCFA)",
                                            min_value=0.0,
                                            value=float(prime_assist_psy_originale),
                                            step=1000.0,
                                            key=f"prime_assist_psy_forcee_part_{idx}",
                                            help="Prime d'assistance psychologique"
                                        )
                                    
                                    # Afficher les valeurs originales
                                    st.markdown("**Valeurs Originales**")
                                    col_orig1, col_orig2, col_orig3, col_orig4 = st.columns(4)
                                    with col_orig1:
                                        st.metric("Prime Nette", format_currency(prime_nette_originale))
                                    with col_orig2:
                                        st.metric("Accessoires", format_currency(accessoires_originaux))
                                    with col_orig3:
                                        st.metric("LSP", format_currency(prime_lsp_originale))
                                    with col_orig4:
                                        st.metric("Assist Psy", format_currency(prime_assist_psy_originale))
                                    
                                    primes_forcees[idx] = {
                                        'prime_nette': prime_nette_forcee,
                                        'accessoires': accessoires_forces,
                                        'prime_lsp': prime_lsp_forcee,
                                        'prime_assist_psy': prime_assist_psy_forcee
                                    }
                                    
                                    st.markdown("---")
                                
                                if st.button("✅ APPLIQUER LES PRIMES FORCÉES", type="primary", use_container_width=True):
                                    for idx in primes_forcees:
                                        prime_nette_f = primes_forcees[idx]['prime_nette']
                                        accessoires_f = primes_forcees[idx]['accessoires']
                                        prime_lsp_f = primes_forcees[idx]['prime_lsp']
                                        prime_assist_psy_f = primes_forcees[idx]['prime_assist_psy']
                                        
                                        resultat = resultats_multi[idx]['resultat']
                                        
                                        resultat['prime_nette_finale'] = prime_nette_f
                                        resultat['accessoires'] = accessoires_f
                                        resultat['prime_lsp'] = prime_lsp_f
                                        resultat['prime_assist_psy'] = prime_assist_psy_f
                                        
                                        prime_ttc_taxable = prime_nette_f + accessoires_f
                                        taxe = prime_ttc_taxable * TAUX_TAXE_PARTICULIER
                                        resultat['taxe'] = taxe
                                        resultat['prime_ttc_taxable'] = prime_ttc_taxable + taxe
                                        
                                        resultat['prime_ttc_totale'] = resultat['prime_ttc_taxable'] + prime_lsp_f + prime_assist_psy_f
                                        resultat['prime_forcee'] = True
                                    
                                    st.session_state['resultats_part_multi'] = resultats_multi
                                    st.success("✅ Primes forcées appliquées avec succès !")
                                    st.rerun()

                        st.markdown("---")
                        
                        # Champ Trop perçu
                        st.markdown("### 💰 Trop Perçu (Optionnel)")
                        col_tp1, col_tp2 = st.columns([3, 1])
                        
                        trop_percu = col_tp1.number_input(
                            "Montant du trop perçu (FCFA)",
                            min_value=0.0,
                            value=0.0,
                            step=1000.0,
                            key="trop_percu_part_multi",
                            help="Montant à ajouter à la prime TTC (non taxé)"
                        )
                        
                        if trop_percu > 0:
                            col_tp2.metric("Trop perçu", f"{format_currency(trop_percu)}", delta="Non taxé")
                        
                        st.markdown("---")
                        
                        # Upload image du barème
                        st.markdown("### 📸 Image du Barème (Page 4)")
                        bareme_image = st.file_uploader(
                            "Joindre l'image du barème de remboursement",
                            type=['png', 'jpg', 'jpeg'],
                            key="bareme_image_upload",
                            help="Cette image apparaîtra en page 4 du PDF"
                        )
                        
                        if bareme_image:
                            st.success(f"✅ Image chargée : {bareme_image.name}")
                            # Stocker dans session_state
                            st.session_state['bareme_image_bytes'] = bareme_image.read()
                            bareme_image.seek(0)  # Reset pour réutilisation
                        
                        st.markdown("---")
                        if st.button("📝 GÉNÉRER LA PROPOSITION COMMERCIALE", key="btn_generer_prop", type="secondary", use_container_width=True):
                            generer_recapitulatif_particulier(resultats_multi, baremes_affiches)
                        
                        # === BOUTON SAUVEGARDE SUPABASE ===
                        st.markdown("---")
                        with st.container(border=True):
                            if st.session_state.db_manager is not None:
                                if st.button("💾 ENREGISTRER LA COTATION", key="btn_save_supabase_part", type="primary", use_container_width=True):
                                    # Préparer les infos client
                                    principal_data = st.session_state.get('principal_data', {})
                                    configs_baremes = st.session_state.get('configurations_baremes', {})
                                    
                                    # Sauvegarder chaque barème séparément
                                    nb_saved = 0
                                    for idx, bareme_key in enumerate(baremes_affiches):
                                        resultat = resultats_multi[idx]['resultat']
                                        config = configs_baremes.get(idx, {})
                                        
                                        client_info = {
                                            'nom': principal_data.get('prospect', ''),
                                            'prenom': '',
                                            'entreprise': '',
                                            'type_couverture': config.get('type_couverture', 'Personne seule'),
                                            'nb_adultes': 2 if config.get('type_couverture') == 'Famille' else 1,
                                            'nb_enfants': 3 + config.get('enfants_supp', 0) if config.get('type_couverture') == 'Famille' else 0
                                        }
                                        
                                        success = sauvegarder_cotation_supabase(
                                            type_marche="Particulier",
                                            produit=PRODUITS_PARTICULIERS_UI[bareme_key],
                                            resultat=resultat,
                                            client_info=client_info,
                                            duree_contrat=resultat.get('facteurs', {}).get('duree_contrat', 12),
                                            reduction_commerciale=resultat.get('facteurs', {}).get('reduction', 0)
                                        )
                                        if success:
                                            nb_saved += 1
                                    
                                    if nb_saved > 0:
                                        st.balloons()
                                        st.success(f"✅ {nb_saved} cotation(s) enregistrée(s) avec succès !")
                            else:
                                st.warning("⚠️ Connexion à la base de données non disponible. Vérifiez la configuration Supabase.")
    
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
                            
                            col_man3, col_man4 = st.columns(2)
                            
                            prime_lsp_formule = col_man3.number_input(
                                "Prime LSP Totale (FCFA)",
                                min_value=0.0,
                                value=20000.0,
                                step=1000.0,
                                key=f"prime_lsp_manuel_formule_{i}",
                                help="Prime Lettre de Sortie Provisoire totale"
                            )
                            
                            prime_assist_psy_formule = col_man4.number_input(
                                "Prime Assistance Psy Totale (FCFA)",
                                min_value=0.0,
                                value=35000.0,
                                step=1000.0,
                                key=f"prime_assist_psy_manuel_formule_{i}",
                                help="Prime d'assistance psychologique totale"
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
                                    'accessoires_manuels': accessoires_formule,
                                    'prime_lsp_manuelle': prime_lsp_formule,
                                    'prime_assist_psy_manuelle': prime_assist_psy_formule
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
                                    accessoire_plus=accessoire_plus_corp,
                                    prime_lsp_manuelle=formule.get('prime_lsp_manuelle'),
                                    prime_assist_psy_manuelle=formule.get('prime_assist_psy_manuelle')
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
                            services_originaux = sum(
                                f.get('prime_lsp', 0) + f.get('prime_assist_psy', 0) 
                                for f in resultats['formules']
                            )
                            prime_ttc_originale = resultats['prime_ttc_finale']
                            
                            st.markdown("**Saisissez la Prime Nette, les Accessoires et les Services :**")
                            
                            col_force1, col_force2 = st.columns(2)
                            
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
                            
                            col_force3, col_force4 = st.columns(2)
                            
                            with col_force3:
                                prime_lsp_forcee_rapide = st.number_input(
                                    "Prime LSP Totale Forcée (FCFA)",
                                    min_value=0.0,
                                    value=float(services_originaux / 2),
                                    step=1000.0,
                                    key="prime_lsp_forcee_corp_rapide",
                                    help="Prime LSP totale pour tous les assurés"
                                )
                            
                            with col_force4:
                                prime_assist_psy_forcee_rapide = st.number_input(
                                    "Prime Assistance Psy Totale Forcée (FCFA)",
                                    min_value=0.0,
                                    value=float(services_originaux / 2),
                                    step=1000.0,
                                    key="prime_assist_psy_forcee_corp_rapide",
                                    help="Prime d'assistance psychologique totale"
                                )
                            
                            # Afficher les valeurs originales
                            st.markdown("**Valeurs Originales**")
                            col_orig1, col_orig2, col_orig3 = st.columns(3)
                            with col_orig1:
                                st.metric("Prime Nette", format_currency(prime_nette_originale))
                            with col_orig2:
                                st.metric("Accessoires", format_currency(accessoires_originaux))
                            with col_orig3:
                                st.metric("Services", format_currency(services_originaux))
                            
                            prime_ttc_taxable_forcee = prime_nette_forcee_rapide + accessoires_forces_rapide
                            taxe_forcee = prime_ttc_taxable_forcee * TAUX_TAXE_CORPORATE
                            prime_ttc_taxable_avec_taxe = prime_ttc_taxable_forcee + taxe_forcee
                            
                            services_totaux_forces = prime_lsp_forcee_rapide + prime_assist_psy_forcee_rapide
                            prime_ttc_totale_forcee = prime_ttc_taxable_avec_taxe + services_totaux_forces
                            
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
                            services_originaux = resultat_micro.get('services', 0)
                            prime_ttc_originale = resultat_micro['prime_ttc_totale']
                            prime_finale_originale = prime_ttc_originale * (100 - reduction_finale) / 100
                            
                            st.markdown("**Saisissez la Prime Nette, les Accessoires et les Services :**")
                            
                            col_force1, col_force2 = st.columns(2)
                            
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
                            
                            col_force3, col_force4 = st.columns(2)
                            
                            with col_force3:
                                prime_lsp_forcee = st.number_input(
                                    "Prime LSP Totale Forcée (FCFA)",
                                    min_value=0.0,
                                    value=float(services_originaux / 2),  # Approximation: services / 2
                                    step=1000.0,
                                    key="prime_lsp_forcee_corp",
                                    help="Prime LSP totale pour tous les assurés"
                                )
                            
                            with col_force4:
                                prime_assist_psy_forcee = st.number_input(
                                    "Prime Assistance Psy Totale Forcée (FCFA)",
                                    min_value=0.0,
                                    value=float(services_originaux / 2),  # Approximation: services / 2
                                    step=1000.0,
                                    key="prime_assist_psy_forcee_corp",
                                    help="Prime d'assistance psychologique totale pour tous les assurés"
                                )
                            
                            # Afficher les valeurs originales
                            st.markdown("**Valeurs Originales**")
                            col_orig1, col_orig2, col_orig3 = st.columns(3)
                            with col_orig1:
                                st.metric("Prime Nette Originale", format_currency(prime_nette_originale))
                            with col_orig2:
                                st.metric("Accessoires Originaux", format_currency(accessoires_originaux))
                            with col_orig3:
                                st.metric("Services Originaux", format_currency(services_originaux))
                            
                            prime_ttc_taxable_forcee = prime_nette_forcee + accessoires_forces
                            taxe_forcee = prime_ttc_taxable_forcee * TAUX_TAXE_CORPORATE
                            prime_ttc_taxable_avec_taxe = prime_ttc_taxable_forcee + taxe_forcee
                            
                            services_totaux_forces = prime_lsp_forcee + prime_assist_psy_forcee
                            prime_ttc_totale_forcee = prime_ttc_taxable_avec_taxe + services_totaux_forces
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
                                    resultat_micro['services'] = services_totaux_forces
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