import streamlit as st
from datetime import datetime
from calculations import calculer_imc, afficher_imc_detaille
from data import LISTE_AFFECTIONS, AFF_EXCLUES, TAUX_MAJORATION_MEDICALE

def display_member_form(member_type: str, key_suffix: str, is_principal: bool = False, is_expanded: bool = False):
    """
    Affiche un formulaire dynamique pour un membre (adulte ou enfant).
    
    Args:
        member_type (str): "Adulte" ou "Enfant".
        key_suffix (str): Suffixe unique pour les clés des widgets Streamlit.
        is_principal (bool): S'il s'agit de l'assuré principal.
        is_expanded (bool): Si l'expander doit être ouvert par défaut.
        
    Returns:
        dict: Un dictionnaire contenant les informations saisies pour le membre.
    """
    
    title = f"👤 {member_type}"
    if is_principal:
        title += " (Assuré Principal)"
    elif member_type == "Adulte":
        title += " (Conjoint)"

    with st.expander(title, expanded=is_expanded):
        st.markdown("**Informations Personnelles**")
        
        col_nom1, col_nom2 = st.columns(2)
        nom = col_nom1.text_input("Nom", key=f"nom_{key_suffix}")
        prenom = col_nom2.text_input("Prénom(s)", key=f"prenom_{key_suffix}")
        
        col_info1, col_info2, col_info3 = st.columns(3)
        default_birth_date = datetime(1980, 1, 1).date() if member_type == "Adulte" else datetime(2010, 1, 1).date()
        date_naissance = col_info1.date_input("Date de naissance", value=default_birth_date, min_value=datetime(1900, 1, 1).date(), max_value=datetime.now().date(), key=f"date_naiss_{key_suffix}")
        lieu_naissance = col_info2.text_input("Lieu de naissance", key=f"lieu_{key_suffix}")
        contact = col_info3.text_input("Contact", key=f"contact_{key_suffix}", placeholder="+225 XX XX XX XX XX")

        col_info4, col_info5, col_info6 = st.columns(3)
        numero_cnam = col_info4.text_input("Numéro CNAM", key=f"cnam_{key_suffix}")
        nationalite = col_info5.text_input("Nationalité", value="Ivoirienne", key=f"nat_{key_suffix}")
        
        if member_type == "Adulte":
            etat_civil = col_info6.selectbox("État civil", ["Célibataire", "Marié(e)", "Divorcé(e)", "Conjoint de fait", "Veuf/veuve"], key=f"etat_{key_suffix}")
        else:
            sexe = col_info6.selectbox("Sexe", ["Masculin", "Féminin"], key=f"sexe_{key_suffix}")

        col_info7, col_info8, col_info9 = st.columns(3)
        default_taille = 170 if member_type == "Adulte" else 140
        default_poids = 70 if member_type == "Adulte" else 35
        taille = col_info7.number_input("Taille (cm)", 50, 250, default_taille, key=f"taille_{key_suffix}")
        poids = col_info8.number_input("Poids (kg)", 20, 250, default_poids, key=f"poids_{key_suffix}")
        
        imc, interp = calculer_imc(poids, taille)
        details_imc = afficher_imc_detaille(col_info9, imc, interp, key_suffix)
        
        if details_imc:
            st.info(
                f"**{details_imc['couleur']} IMC : {details_imc['categorie']}** (Tranche : {details_imc['tranche']})\n\n"
                f"{details_imc['description']}\n\n"
                f"⚠️ **{details_imc['risque']}**"
            )

        default_tension = "12/8" if member_type == "Adulte" else "10/6"
        tension = st.text_input("Tension artérielle", value=default_tension, key=f"tension_{key_suffix}", placeholder=default_tension)
        
        if member_type == "Adulte":
            emploi = st.text_input("Emploi actuel", key=f"emploi_{key_suffix}")

        st.markdown("---")
        st.markdown("**Informations Médicales**")
        col_med1, col_med2 = st.columns(2)
        
        affections = col_med1.multiselect("Affections Chroniques", LISTE_AFFECTIONS, key=f"affections_{key_suffix}")
        if affections:
            taux_maj = sum(TAUX_MAJORATION_MEDICALE[aff] for aff in affections)
            col_med1.success(f"✓ Surprime affections : **{taux_maj}%**")
        
        exclusion = col_med2.checkbox(f"Affection Bloquante ({', '.join(AFF_EXCLUES)})", key=f"exclusion_{key_suffix}")
        
        grossesse = False
        montant_grossesse = 0
        if member_type == "Adulte" and not is_principal: # Grossesse pour conjoint uniquement dans ce formulaire
             grossesse = col_med2.checkbox("Grossesse en cours", key=f"grossesse_{key_suffix}")
             if grossesse:
                from data import SURPRIME_FORFAITAIRE_GROSSESSE # Eviter circular import
                montant_grossesse = col_med2.number_input(
                    "Montant Grossesse (FCFA)", 
                    min_value=0.0, 
                    value=float(SURPRIME_FORFAITAIRE_GROSSESSE), 
                    step=10000.0, 
                    key=f"montant_gross_{key_suffix}",
                    help="Montant forfaitaire à ajouter pour la grossesse"
                )

    member_data = {
        "nom": nom, "prenom": prenom, "date_naissance": date_naissance, "lieu_naissance": lieu_naissance,
        "contact": contact, "numero_cnam": numero_cnam, "nationalite": nationalite, "taille": taille, "poids": poids,
        "tension_arterielle": tension, "affections": affections, "exclusion": exclusion, "type": member_type
    }

    if member_type == "Adulte":
        member_data.update({"etat_civil": etat_civil, "emploi_actuel": emploi, "grossesse": grossesse, "montant_grossesse": montant_grossesse})
    else:
        member_data.update({"sexe": sexe})
        
    return member_data
