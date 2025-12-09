import streamlit as st
import math
import pandas as pd
import io
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date
from data import *

def format_currency(amount: float) -> str:
    """Formate un montant en FCFA avec arrondi mathématique standard."""
    return f"{round(amount):,.0f} FCFA".replace(",", " ")

def calculer_age(date_naissance: date) -> int:
    """Calcule l'âge à partir de la date de naissance."""
    aujourd_hui = datetime.now().date()
    age = aujourd_hui.year - date_naissance.year
    
    # Ajuster si l'anniversaire n'est pas encore passé cette année
    if (aujourd_hui.month, aujourd_hui.day) < (date_naissance.month, date_naissance.day):
        age -= 1
    
    return age

def calculer_surprime_age(date_naissance: date) -> float:
    """
    Calcule la surprime d'âge pour une personne.
    Retourne 25% si l'âge est supérieur à 51 ans, sinon 0.
    """
    age = calculer_age(date_naissance)
    return SURPRIME_AGE_PLUS_51 if age > 51 else 0

def calculer_surprime_age_famille(date_naissance_principale: Optional[date], 
                                   date_naissance_conjoint: Optional[date],
                                   prime_nette_base: float) -> Tuple[float, float]:
    """
    Calcule la surprime d'âge pour une famille.
    Si l'un des adultes a plus de 51 ans, la prime nette est multipliée par 1.0675.
    
    Returns:
        Tuple[float, float]: (prime_nette_ajustée, taux_surprime_appliqué)
    """
    adulte_plus_51 = False
    
    if date_naissance_principale:
        age_principal = calculer_age(date_naissance_principale)
        if age_principal > 51:
            adulte_plus_51 = True
    
    if date_naissance_conjoint:
        age_conjoint = calculer_age(date_naissance_conjoint)
        if age_conjoint > 51:
            adulte_plus_51 = True
    
    if adulte_plus_51:
        prime_ajustee = prime_nette_base * 1.0675
        taux_surprime = 6.75  # 6.75% de surprime
        return prime_ajustee, taux_surprime
    else:
        return prime_nette_base, 0.0

def valider_age_enfant(date_naissance: date, nom_enfant: str = "", numero_enfant: int = 0) -> Tuple[bool, str]:
    """
    Valide que l'âge d'un enfant ne dépasse pas 25 ans pour une cotation famille.
    """
    age = calculer_age(date_naissance)
    
    if age > 25:
        if nom_enfant:
            enfant_label = f"L'enfant {nom_enfant}"
        elif numero_enfant > 0:
            enfant_label = f"L'enfant n°{numero_enfant}"
        else:
            enfant_label = "Un enfant"
        
        message = f"⚠️ {enfant_label} a {age} ans, ce qui dépasse la limite de 25 ans pour une cotation famille."
        return False, message
    
    return True, ""

def calculer_imc(poids_kg: float, taille_cm: float) -> Tuple[float, str]:
    """
    Calcule l'IMC et retourne l'interprétation selon les catégories médicales standard.
    """
    if taille_cm <= 0 or poids_kg <= 0:
        return 0.0, "Données invalides"
    
    taille_m = taille_cm / 100
    imc = poids_kg / (taille_m ** 2)
    
    if imc < 18.5:
        interpretation = "Maigreur"
    elif 18.5 <= imc < 25.0:
        interpretation = "Corpulence normale"
    elif 25.0 <= imc < 30.0:
        interpretation = "Surpoids"
    elif 30.0 <= imc < 35.0:
        interpretation = "Obésité classe I"
    elif 35.0 <= imc < 40.0:
        interpretation = "Obésité classe II"
    else:  # imc >= 40.0
        interpretation = "Obésité classe III"
    
    return round(imc, 1), interpretation

def get_imc_details(imc: float) -> dict:
    """
    Retourne les détails complets d'une catégorie IMC.
    """
    if imc < 18.5:
        return {
            'categorie': 'Maigreur', 'tranche': '< 18,5',
            'description': 'Le poids est considéré comme insuffisant pour la taille, ce qui peut indiquer une dénutrition ou d\'autres problèmes de santé.',
            'risque': 'Risque modéré', 'couleur': '🟡'
        }
    elif 18.5 <= imc < 25.0:
        return {
            'categorie': 'Corpulence normale', 'tranche': '18,5 – 24,9',
            'description': 'C\'est la fourchette idéale. Elle est statistiquement associée au plus faible risque de maladies chroniques.',
            'risque': 'Risque faible', 'couleur': '🟢'
        }
    elif 25.0 <= imc < 30.0:
        return {
            'categorie': 'Surpoids', 'tranche': '25,0 – 29,9',
            'description': 'Le poids est supérieur à ce qui est considéré comme sain pour la taille. Le risque de problèmes de santé augmente.',
            'risque': 'Risque accru', 'couleur': '🟠'
        }
    elif 30.0 <= imc < 35.0:
        return {
            'categorie': 'Obésité classe I', 'tranche': '30,0 – 34,9',
            'description': 'L\'excès de poids est significatif et le risque de maladies (diabète, hypertension, problèmes cardiaques) est élevé.',
            'risque': 'Risque élevé', 'couleur': '🔴'
        }
    elif 35.0 <= imc < 40.0:
        return {
            'categorie': 'Obésité classe II', 'tranche': '35,0 – 39,9',
            'description': 'Le risque pour la santé est très élevé.',
            'risque': 'Risque très élevé', 'couleur': '🔴'
        }
    else:  # imc >= 40.0
        return {
            'categorie': 'Obésité classe III', 'tranche': '≥ 40,0',
            'description': 'Aussi appelée obésité morbide. Le risque de décès prématuré et de maladies graves est extrêmement élevé.',
            'risque': 'Risque extrême', 'couleur': '⚫'
        }

def afficher_imc_detaille(col, imc: float, interpretation: str, key_suffix: str = ""):
    """
    Affiche l'IMC avec détails complets dans une colonne Streamlit.
    """
    details = get_imc_details(imc)
    col.metric("IMC", f"{imc}", interpretation)
    if imc < 18.5 or imc >= 25.0:
        return details
    return None

def valider_affections(affections: List[str]) -> Tuple[bool, Optional[str]]:
    """Valide la liste des affections déclarées."""
    if not affections:
        return True, None
    affections_invalides = [aff for aff in affections if aff not in TAUX_MAJORATION_MEDICALE]
    if affections_invalides:
        return False, f"Affections non reconnues : {', '.join(affections_invalides)}"
    return True, None

def calculer_prime_avec_parametres(
    prime_nette_base: float, 
    accessoires: float, 
    prime_lsp: float, 
    prime_assist_psy: float,
    reduction: float = 0, 
    surprime: float = 0, 
    duree_contrat: int = 12, 
    taux_taxe: float = 0.03
) -> Dict[str, Any]:
    """Calcule la prime finale avec application des facteurs d'ajustement."""
    # Validation des entrées
    if not 0 <= reduction <= 100:
        raise ValueError(f"Réduction invalide : {reduction}%. Doit être entre 0 et 100.")
    if surprime < 0:
        raise ValueError(f"Surprime invalide : {surprime}%. Ne peut pas être négative.")
    if not 1 <= duree_contrat <= 12:
        raise ValueError(f"Durée invalide : {duree_contrat} mois. Doit être entre 1 et 12.")
    
    # Calcul des facteurs
    facteur_reduction = (100 - reduction) / 100
    facteur_surprime = (100 + surprime) / 100
    facteur_duree = 0.52 if duree_contrat <= 6 else 1.0
    
    # Application des facteurs sur la prime nette
    prime_nette_finale = prime_nette_base * facteur_reduction * facteur_surprime * facteur_duree
    
    # Calcul de la taxe (sur prime nette + accessoires)
    taxe = (prime_nette_finale + accessoires) * taux_taxe
    
    # Prime TTC taxable
    prime_ttc_taxable = prime_nette_finale + accessoires + taxe
    
    # Prime TTC totale (ajout des services hors taxe)
    prime_ttc_totale = prime_ttc_taxable + prime_lsp + prime_assist_psy
    
    return {
        'prime_nette_base': prime_nette_base,
        'prime_nette_finale': prime_nette_finale,
        'accessoires': accessoires,
        'taxe': taxe,
        'prime_ttc_taxable': prime_ttc_taxable,
        'prime_lsp': prime_lsp,
        'prime_assist_psy': prime_assist_psy,
        'prime_ttc_totale': prime_ttc_totale,
        'facteurs': {
            'reduction': reduction,
            'surprime': surprime,
            'duree_contrat': duree_contrat,
            'taux_taxe': taux_taxe,
            'facteur_reduction': facteur_reduction,
            'facteur_surprime': facteur_surprime,
            'facteur_duree': facteur_duree
        }
    }

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
    """Calcule la prime pour un contrat particulier avec toutes les surcharges applicables."""
    
    # CAS SPÉCIAL : Barème Spécial avec saisie manuelle
    if produit_key == 'bareme_special':
        if prime_nette_manuelle is None or prime_nette_manuelle == 0:
            raise ValueError("Pour un barème spécial, la prime nette doit être saisie manuellement.")
        
        prime_nette_ajustee = prime_nette_manuelle
        
        # Calculer la surprime d'âge si applicable (nouvelle logique pour famille)
        surprime_age_taux = 0
        if type_couverture == 'Famille':
            # Pour famille : si un adulte a > 51 ans, prime nette × 1.0675
            prime_nette_ajustee, surprime_age_taux = calculer_surprime_age_famille(
                date_naissance_principale,
                date_naissance_conjoint,
                prime_nette_manuelle
            )
        else:
            # Pour personne seule : surprime de 25% si > 51 ans
            if date_naissance_principale:
                surprime_age_taux = calculer_surprime_age(date_naissance_principale)
        
        # Calculer la surprime risque si applicable
        surprime_risques = 0
        if affections_declarees:
            is_valid, error_msg = valider_affections(affections_declarees)
            if not is_valid:
                raise ValueError(error_msg)
            taux_cumulatif = sum(TAUX_MAJORATION_MEDICALE[aff] for aff in affections_declarees)
            surprime_risques = taux_cumulatif
        
        # Surprime totale (pour personne seule seulement)
        surprime_totale = surprime_risques + (surprime_age_taux if type_couverture != 'Famille' else 0)
        
        # Ajout de la surprime grossesse forfaitaire
        surprime_forfaitaire_nette = 0
        if grossesse:
            surprime_forfaitaire_nette = SURPRIME_FORFAITAIRE_GROSSESSE
            prime_nette_ajustee += surprime_forfaitaire_nette
        
        # Utiliser les valeurs manuelles pour les accessoires
        accessoires_finaux = accessoires_manuels if accessoires_manuels is not None else 10000
        # Ajouter les accessoires supplémentaires
        accessoires_finaux += accessoire_plus
        
        # Utiliser les valeurs manuelles pour LSP et Assistance Psy
        prime_lsp_finale = prime_lsp_manuelle if prime_lsp_manuelle is not None else 20000
        prime_assist_psy_finale = prime_assist_psy_manuelle if prime_assist_psy_manuelle is not None else 35000
        
        # Calcul final avec les valeurs manuelles
        resultat = calculer_prime_avec_parametres(
            prime_nette_base=prime_nette_ajustee,
            accessoires=accessoires_finaux,
            prime_lsp=prime_lsp_finale,
            prime_assist_psy=prime_assist_psy_finale,
            reduction=reduction_commerciale,
            surprime=surprime_totale,
            duree_contrat=duree_contrat,
            taux_taxe=TAUX_TAXE_PARTICULIER
        )
        
        # Ajout des informations spécifiques
        resultat['surprime_grossesse'] = surprime_forfaitaire_nette
        resultat['surprime_risques_taux'] = surprime_risques
        resultat['surprime_age_taux'] = surprime_age_taux
        resultat['surprime_totale_taux'] = surprime_totale if type_couverture != 'Famille' else surprime_risques
        resultat['nombre_enfants_supp'] = enfants_supplementaires
        resultat['affections_declarees'] = affections_declarees or []
        resultat['bareme_special'] = True
        resultat['accessoire_plus'] = accessoire_plus
        
        return resultat
    
    # CAS NORMAL : Utilisation des barèmes prédéfinis
    # Validation du produit
    if produit_key not in TARIFS_PARTICULIERS:
        raise ValueError(
            f"Produit '{produit_key}' non trouvé. "
            f"Produits disponibles : {list(TARIFS_PARTICULIERS.keys())}"
        )
    
    # Validation du type de couverture
    if type_couverture not in ['Personne seule', 'Famille']:
        raise ValueError(f"Type de couverture invalide : '{type_couverture}'")
    
    # Validation des enfants supplémentaires
    if enfants_supplementaires < 0:
        raise ValueError(f"Nombre d'enfants négatif : {enfants_supplementaires}")
    if enfants_supplementaires > MAX_ENFANTS_SUPPLEMENTAIRES:
        raise ValueError(
            f"Nombre d'enfants trop élevé : {enfants_supplementaires}. "
            f"Maximum autorisé : {MAX_ENFANTS_SUPPLEMENTAIRES}"
        )
    
    # Validation des affections
    if affections_declarees:
        is_valid, error_msg = valider_affections(affections_declarees)
        if not is_valid:
            raise ValueError(error_msg)
    
    tarif = TARIFS_PARTICULIERS[produit_key]
    
    # 1. Détermination de la surprime risque (%)
    surprime_risques = 0
    if affections_declarees:
        taux_cumulatif = sum(TAUX_MAJORATION_MEDICALE[aff] for aff in affections_declarees)
        surprime_risques = taux_cumulatif
    
    # 2. Agrégation des primes de base selon le type de couverture
    config = tarif['famille'] if type_couverture == 'Famille' else tarif['personne_seule']
    prime_nette_totale = config['prime_nette']
    accessoires_totaux = config['accessoires']
    prime_lsp_totale = config['prime_lsp']
    prime_assist_psy_totale = config['prime_assist_psy']
    surprime_forfaitaire_nette = 0

    # Ajout des enfants supplémentaires (seulement pour Famille)
    if type_couverture == 'Famille' and enfants_supplementaires > 0:
        enfant_config = tarif['enfant_supplementaire']
        prime_nette_totale += enfant_config['prime_nette'] * enfants_supplementaires
        accessoires_totaux += enfant_config['accessoires'] * enfants_supplementaires
    
    # 1.bis Calcul de la surprime d'âge (nouvelle logique pour famille)
    surprime_age_taux = 0
    if type_couverture == 'Famille':
        # Pour famille : si un adulte a > 51 ans, prime nette × 1.0675
        prime_nette_totale, surprime_age_taux = calculer_surprime_age_famille(
            date_naissance_principale, 
            date_naissance_conjoint,
            prime_nette_totale
        )
    else:
        # Pour personne seule : surprime de 25% si > 51 ans
        if date_naissance_principale:
            surprime_age_taux = calculer_surprime_age(date_naissance_principale)
    
    # Combinaison des surprimes (pour personne seule seulement) + surprime manuelle
    surprime_totale = surprime_risques + (surprime_age_taux if type_couverture != 'Famille' else 0) + surprime_manuelle_pourcent
    
    # 3. Ajout de la surprime grossesse forfaitaire à la prime nette de base
    if grossesse:
        if montant_grossesse_manuel is not None and montant_grossesse_manuel > 0:
            surprime_forfaitaire_nette = montant_grossesse_manuel
        else:
            surprime_forfaitaire_nette = SURPRIME_FORFAITAIRE_GROSSESSE
        prime_nette_totale += surprime_forfaitaire_nette
    
    # 3.bis Ajout des accessoires supplémentaires
    accessoires_totaux += accessoire_plus
    
    # 4. Calcul final avec application des facteurs
    resultat = calculer_prime_avec_parametres(
        prime_nette_base=prime_nette_totale,
        accessoires=accessoires_totaux,
        prime_lsp=prime_lsp_totale,
        prime_assist_psy=prime_assist_psy_totale,
        reduction=reduction_commerciale,
        surprime=surprime_totale,  # Surprime en % (pour personne seule) + surprime manuelle
        duree_contrat=duree_contrat,
        taux_taxe=TAUX_TAXE_PARTICULIER
    )
    
    # Ajout des informations spécifiques au particulier
    resultat['surprime_grossesse'] = surprime_forfaitaire_nette
    resultat['surprime_risques_taux'] = surprime_risques
    resultat['surprime_manuelle_taux'] = surprime_manuelle_pourcent
    resultat['surprime_age_taux'] = surprime_age_taux
    resultat['surprime_totale_taux'] = surprime_totale if type_couverture != 'Famille' else surprime_risques
    resultat['nombre_enfants_supp'] = enfants_supplementaires
    resultat['affections_declarees'] = affections_declarees or []
    resultat['accessoire_plus'] = accessoire_plus
    
    return resultat

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
    """Calcule une ESTIMATION RAPIDE pour un contrat corporate (aide à la vente uniquement)."""
    
    # CAS SPÉCIAL : Barème Spécial avec saisie manuelle
    if produit_key == 'bareme_special':
        if prime_nette_manuelle is None or prime_nette_manuelle == 0:
            raise ValueError("Pour un barème spécial, la prime nette doit être saisie manuellement.")
        
        # Utiliser les valeurs manuelles pour les accessoires
        accessoires_finaux = accessoires_manuels if accessoires_manuels is not None else 10000
        # Ajouter les accessoires supplémentaires
        accessoires_finaux += accessoire_plus
        
        # Utiliser les valeurs manuelles pour LSP et Assistance Psy
        prime_lsp_finale = prime_lsp_manuelle if prime_lsp_manuelle is not None else 20000
        prime_assist_psy_finale = prime_assist_psy_manuelle if prime_assist_psy_manuelle is not None else 35000
        
        # Calcul final avec les valeurs manuelles
        resultat = calculer_prime_avec_parametres(
            prime_nette_base=prime_nette_manuelle,
            accessoires=accessoires_finaux,
            prime_lsp=prime_lsp_finale,
            prime_assist_psy=prime_assist_psy_finale,
            reduction=reduction_commerciale,
            surprime=surprime_risques,
            duree_contrat=duree_contrat,
            taux_taxe=TAUX_TAXE_CORPORATE
        )
        
        # Ajout des informations spécifiques
        resultat['nb_familles'] = nb_familles
        resultat['nb_personnes_seules'] = nb_personnes_seules
        resultat['nb_enfants_supplementaires'] = nb_enfants_supplementaires
        resultat['type_calcul'] = 'estimation_rapide'
        resultat['bareme_special'] = True
        resultat['accessoire_plus'] = accessoire_plus
        
        return resultat
    
    # CAS NORMAL : Utilisation des barèmes prédéfinis
    if produit_key not in TARIFS_CORPORATE:
        raise ValueError(
            f"Produit corporate '{produit_key}' non trouvé. "
            f"Produits disponibles : {list(TARIFS_CORPORATE.keys())}"
        )
    
    if nb_familles < 0 or nb_personnes_seules < 0 or nb_enfants_supplementaires < 0:
        raise ValueError("Les effectifs ne peuvent pas être négatifs")
    
    if nb_familles == 0 and nb_personnes_seules == 0 and nb_enfants_supplementaires == 0:
        raise ValueError("Au moins une famille, une personne seule ou un enfant supplémentaire doit être assuré")
    
    tarif = TARIFS_CORPORATE[produit_key]
    
    prime_nette_totale = (
        tarif['famille']['prime_nette'] * nb_familles + 
        tarif['personne_seule']['prime_nette'] * nb_personnes_seules +
        tarif['enfant_supplementaire']['prime_nette'] * nb_enfants_supplementaires
    )
    
    accessoires_totaux = (
        tarif['famille']['accessoires'] * nb_familles + 
        tarif['personne_seule']['accessoires'] * nb_personnes_seules +
        tarif['enfant_supplementaire']['accessoires'] * nb_enfants_supplementaires
    )
    
    accessoires_totaux += accessoire_plus
    
    prime_lsp_totale = (
        tarif['famille']['prime_lsp'] * nb_familles + 
        tarif['personne_seule']['prime_lsp'] * nb_personnes_seules +
        tarif['enfant_supplementaire']['prime_lsp'] * nb_enfants_supplementaires
    )
    
    prime_assist_psy_totale = (
        tarif['famille']['prime_assist_psy'] * nb_familles + 
        tarif['personne_seule']['prime_assist_psy'] * nb_personnes_seules +
        tarif['enfant_supplementaire']['prime_assist_psy'] * nb_enfants_supplementaires
    )
    
    resultat = calculer_prime_avec_parametres(
        prime_nette_base=prime_nette_totale,
        accessoires=accessoires_totaux,
        prime_lsp=prime_lsp_totale,
        prime_assist_psy=prime_assist_psy_totale,
        reduction=reduction_commerciale,
        surprime=surprime_risques,
        duree_contrat=duree_contrat,
        taux_taxe=TAUX_TAXE_CORPORATE
    )
    
    resultat['nb_familles'] = nb_familles
    resultat['nb_personnes_seules'] = nb_personnes_seules
    resultat['nb_enfants_supplementaires'] = nb_enfants_supplementaires
    resultat['type_calcul'] = 'estimation_rapide'
    resultat['accessoire_plus'] = accessoire_plus
    
    return resultat

def valider_fichier_excel(df: pd.DataFrame) -> Tuple[bool, Optional[str], Optional[pd.DataFrame]]:
    """
    Valide la structure et le contenu du fichier Excel importé.
    
    Returns:
        Tuple: (is_valid, error_message, cleaned_df)
    """
    colonnes_manquantes = [col for col in COLONNES_EXCEL_REQUISES if col not in df.columns]
    if colonnes_manquantes:
        return False, f"Colonnes manquantes : {', '.join(colonnes_manquantes)}", None
    
    df_clean = df.dropna(subset=['nom', 'prenom'], how='all')
    if df_clean.empty:
        return False, "Aucune donnée valide trouvée dans le fichier", None
    
    types_valides = ['Personne seule', 'Famille']
    types_invalides = df_clean[~df_clean['type_couverture'].isin(types_valides)]
    if not types_invalides.empty:
        return False, f"Types de couverture invalides détectés (lignes {types_invalides.index.tolist()})", None
    
    df_clean['grossesse'] = df_clean['grossesse'].fillna(False).astype(bool)
    df_clean['nombre_enfants'] = df_clean['nombre_enfants'].fillna(0).astype(int)
    df_clean['affections'] = df_clean['affections'].fillna('')
    
    return True, None, df_clean


def traiter_ligne_assure(
    ligne: pd.Series,
    produit_key: str,
    duree_contrat: int
) -> Dict[str, Any]:
    """
    Traite une ligne d'assuré du fichier Excel et calcule sa prime individuelle.
    Applique la micro-tarification avec toutes les règles.
    
    Note: Pour les familles, jusqu'à 3 enfants sont inclus dans le tarif famille.
    À partir du 4ème enfant, chaque enfant supplémentaire est facturé.
    """
    affections_str = str(ligne['affections']).strip()
    affections = [aff.strip() for aff in affections_str.split(',') if aff.strip()] if affections_str else []
    
    affections_exclues = [aff for aff in affections if aff in AFF_EXCLUES]
    if affections_exclues:
        return {
            'statut': 'exclu',
            'raison': f"Affection(s) bloquante(s) : {', '.join(affections_exclues)}",
            'prime': 0,
            'ligne': ligne.to_dict()
        }
    
    is_valid, error_msg = valider_affections(affections)
    if not is_valid:
        return {
            'statut': 'erreur',
            'raison': error_msg,
            'prime': 0,
            'ligne': ligne.to_dict()
        }
    
    nb_enfants_total = int(ligne['nombre_enfants'])
    enfants_supplementaires = max(0, nb_enfants_total - 3) if ligne['type_couverture'] == 'Famille' else 0
    
    if ligne['type_couverture'] == 'Famille' and nb_enfants_total > 0:
        for i in range(1, nb_enfants_total + 1):
            col_name = f'enfant{i}_date_naissance'
            if col_name in ligne and pd.notna(ligne[col_name]):
                try:
                    if isinstance(ligne[col_name], str):
                        date_naiss_enfant = datetime.strptime(ligne[col_name], '%d/%m/%Y').date()
                    else:
                        date_naiss_enfant = ligne[col_name]
                    
                    nom_enfant = ""
                    if f'enfant{i}_nom' in ligne and pd.notna(ligne[f'enfant{i}_nom']):
                        nom_enfant = str(ligne[f'enfant{i}_nom'])
                    if f'enfant{i}_prenom' in ligne and pd.notna(ligne[f'enfant{i}_prenom']):
                        prenom = str(ligne[f'enfant{i}_prenom'])
                        nom_enfant = f"{prenom} {nom_enfant}".strip()
                    
                    is_valid_age, error_msg = valider_age_enfant(
                        date_naiss_enfant, 
                        nom_enfant=nom_enfant,
                        numero_enfant=i
                    )
                    if not is_valid_age:
                        return {
                            'statut': 'exclu',
                            'raison': error_msg,
                            'prime': 0,
                            'ligne': ligne.to_dict()
                        }
                except Exception:
                    pass
    
    date_naiss_principale = None
    date_naiss_conjoint = None
    
    if 'date_naissance' in ligne and pd.notna(ligne['date_naissance']):
        try:
            if isinstance(ligne['date_naissance'], str):
                date_naiss_principale = datetime.strptime(ligne['date_naissance'], '%d/%m/%Y').date()
            else:
                date_naiss_principale = ligne['date_naissance']
        except Exception:
            pass
    
    if ligne['type_couverture'] == 'Famille' and 'conjoint_date_naissance' in ligne and pd.notna(ligne['conjoint_date_naissance']):
        try:
            if isinstance(ligne['conjoint_date_naissance'], str):
                date_naiss_conjoint = datetime.strptime(ligne['conjoint_date_naissance'], '%d/%m/%Y').date()
            else:
                date_naiss_conjoint = ligne['conjoint_date_naissance']
        except Exception:
            pass
    
    try:
        resultat = calculer_prime_particuliers(
            produit_key=produit_key,
            type_couverture=ligne['type_couverture'],
            enfants_supplementaires=enfants_supplementaires,
            affections_declarees=affections if affections else None,
            grossesse=bool(ligne['grossesse']),
            reduction_commerciale=0,
            duree_contrat=duree_contrat,
            date_naissance_principale=date_naiss_principale,
            date_naissance_conjoint=date_naiss_conjoint
        )
        
        return {
            'statut': 'eligible',
            'prime': resultat['prime_ttc_totale'],
            'prime_nette': resultat['prime_nette_finale'],
            'surprime_risque': resultat.get('surprime_risques_taux', 0),
            'surprime_age': resultat.get('surprime_age_taux', 0),
            'surprime_totale': resultat.get('surprime_totale_taux', 0),
            'affections': affections,
            'nb_enfants_total': nb_enfants_total,
            'nb_enfants_supp': enfants_supplementaires,
            'ligne': ligne.to_dict()
        }
    except Exception as e:
        return {
            'statut': 'erreur',
            'raison': str(e),
            'prime': 0,
            'ligne': ligne.to_dict()
        }


def micro_tarification_excel(
    df: pd.DataFrame,
    produit_key: str,
    duree_contrat: int
) -> Dict[str, Any]:
    """
    Effectue la micro-tarification complète du fichier Excel.
    Analyse chaque assuré ligne par ligne.
    """
    resultats_lignes = []
    total_prime_nette = 0
    total_accessoires = 0
    total_services = 0
    nb_eligibles = 0
    nb_exclus = 0
    nb_erreurs = 0
    nb_enfants_supplementaires_total = 0
    
    assures_exclus = []
    assures_erreurs = []
    
    for _, ligne in df.iterrows():
        resultat_ligne = traiter_ligne_assure(ligne, produit_key, duree_contrat)
        resultats_lignes.append(resultat_ligne)
        
        if resultat_ligne['statut'] == 'eligible':
            nb_eligibles += 1
            total_prime_nette += resultat_ligne['prime_nette']
            nb_enfants_supplementaires_total += resultat_ligne.get('nb_enfants_supp', 0)
        elif resultat_ligne['statut'] == 'exclu':
            nb_exclus += 1
            assures_exclus.append({
                'nom': ligne['nom'],
                'prenom': ligne['prenom'],
                'raison': resultat_ligne['raison']
            })
        elif resultat_ligne['statut'] == 'erreur':
            nb_erreurs += 1
            assures_erreurs.append({
                'nom': ligne['nom'],
                'prenom': ligne['prenom'],
                'raison': resultat_ligne['raison']
            })
    
    if produit_key == 'bareme_special':
        raise ValueError(
            "Le workflow Excel n'est pas compatible avec le barème spécial. "
            "Veuillez utiliser la 'Cotation Rapide' pour les barèmes spéciaux."
        )
    
    tarif = TARIFS_CORPORATE[produit_key]
    
    for resultat in resultats_lignes:
        if resultat['statut'] == 'eligible':
            ligne = resultat['ligne']
            if ligne['type_couverture'] == 'Famille':
                config = tarif['famille']
                nb_enfants_supp = resultat.get('nb_enfants_supp', 0)
                total_accessoires += config['accessoires'] + (tarif['enfant_supplementaire']['accessoires'] * nb_enfants_supp)
                total_services += config['prime_lsp'] + config['prime_assist_psy']
            else:
                config = tarif['personne_seule']
                total_accessoires += config['accessoires']
                total_services += config['prime_lsp'] + config['prime_assist_psy']
    
    taxe = (total_prime_nette + total_accessoires) * TAUX_TAXE_CORPORATE
    prime_ttc_taxable = total_prime_nette + total_accessoires + taxe
    prime_ttc_totale = prime_ttc_taxable + total_services
    
    return {
        'nb_total': len(df),
        'nb_eligibles': nb_eligibles,
        'nb_exclus': nb_exclus,
        'nb_erreurs': nb_erreurs,
        'nb_enfants_supplementaires': nb_enfants_supplementaires_total,
        'assures_exclus': assures_exclus,
        'assures_erreurs': assures_erreurs,
        'prime_nette_totale': total_prime_nette,
        'accessoires': total_accessoires,
        'taxe': taxe,
        'prime_ttc_taxable': prime_ttc_taxable,
        'services': total_services,
        'prime_ttc_totale': prime_ttc_totale,
        'resultats_lignes': resultats_lignes
    }


def generer_template_excel() -> bytes:
    """Génère un template Excel pour la saisie des données Corporate."""
    df_template = pd.DataFrame({
        'nom': ['KOUAME', 'TOURE', 'N\'GUESSAN'],
        'prenom': ['Jean', 'Marie', 'Fatou'],
        'date_naissance': ['01/01/1985', '15/06/1990', '20/03/1988'],
        'lieu_naissance': ['Abidjan', 'Bouaké', 'Yamoussoukro'],
        'contact': ['+225 07 12 34 56 78', '+225 05 98 76 54 32', '+225 01 23 45 67 89'],
        'numero_cnam': ['CNAM123456', 'CNAM789012', 'CNAM345678'],
        'nationalite': ['Ivoirienne', 'Ivoirienne', 'Ivoirienne'],
        'taille': [175, 165, 170],
        'poids': [75, 60, 68],
        'tension_arterielle': ['12/8', '11/7', '13/9'],
        'etat_civil': ['Marié(e)', 'Célibataire', 'Marié(e)'],
        'emploi_actuel': ['Directeur Commercial', 'Comptable', 'Responsable RH'],
        'type_couverture': ['Famille', 'Personne seule', 'Famille'],
        'nombre_enfants': [2, 0, 1],
        'grossesse': [False, False, True],
        'affections': ['Hypertension artérielle', '', 'Diabète, Asthme'],
        'conjoint_nom': ['KOUAME', '', 'N\'GUESSAN'],
        'conjoint_prenom': ['Aya', '', 'Konan'],
        'conjoint_date_naissance': ['15/08/1987', '', '10/05/1989'],
        'conjoint_lieu_naissance': ['Korhogo', '', 'Daloa'],
        'conjoint_contact': ['+225 07 11 22 33 44', '', '+225 05 55 66 77 88'],
        'conjoint_numero_cnam': ['CNAM654321', '', 'CNAM876543'],
        'conjoint_nationalite': ['Ivoirienne', '', 'Ivoirienne'],
        'conjoint_taille': [168, '', 162],
        'conjoint_poids': [65, '', 58],
        'conjoint_tension_arterielle': ['12/7', '', '11/8'],
        'conjoint_emploi_actuel': ['Enseignante', '', 'Infirmière'],
        'enfant1_nom': ['KOUAME', '', 'N\'GUESSAN'],
        'enfant1_prenom': ['Junior', '', 'Amani'],
        'enfant1_date_naissance': ['10/03/2015', '', '05/07/2018'],
        'enfant1_lieu_naissance': ['Abidjan', '', 'Yamoussoukro'],
        'enfant1_numero_cnam': ['CNAM111111', '', 'CNAM222222'],
        'enfant1_taille': [130, '', 105],
        'enfant1_poids': [28, '', 18],
        'enfant1_tension_arterielle': ['10/6', '', '9/6'],
        'enfant1_niveau_etude': ['Primaire', '', 'Maternelle'],
        'enfant2_nom': ['KOUAME', '', ''],
        'enfant2_prenom': ['Sarah', '', ''],
        'enfant2_date_naissance': ['20/09/2017', '', ''],
        'enfant2_lieu_naissance': ['Abidjan', '', ''],
        'enfant2_numero_cnam': ['CNAM333333', '', ''],
        'enfant2_taille': [115, '', ''],
        'enfant2_poids': [22, '', ''],
        'enfant2_tension_arterielle': ['9/6', '', ''],
        'enfant2_niveau_etude': ['Maternelle', '', ''],
        'enfant3_nom': ['', '', ''],
        'enfant3_prenom': ['', '', ''],
        'enfant3_date_naissance': ['', '', ''],
        'enfant3_lieu_naissance': ['', '', ''],
        'enfant3_numero_cnam': ['', '', ''],
        'enfant3_taille': ['', '', ''],
        'enfant3_poids': ['', '', ''],
        'enfant3_tension_arterielle': ['', '', ''],
        'enfant3_niveau_etude': ['', '', '']
    })
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_template.to_excel(writer, index=False, sheet_name='Assures')
        instructions = pd.DataFrame({
            'Instructions': [
                "=== COLONNES OBLIGATOIRES POUR L'ASSURÉ PRINCIPAL ===",
                'nom, prenom, date_naissance, lieu_naissance, contact, numero_cnam, nationalite',
                'taille (en cm), poids (en kg), tension_arterielle (format: 12/8)',
                'etat_civil : Célibataire, Marié(e), Divorcé(e), Conjoint de fait, Veuf/veuve',
                'emploi_actuel : Poste ou profession actuelle',
                '',
                '=== INFORMATIONS DE COUVERTURE ===',
                'type_couverture : "Personne seule" ou "Famille"',
                'nombre_enfants : 0 pour personne seule, nombre pour famille (max 3 inclus)',
                'grossesse : True ou False',
                f'affections : Liste séparée par virgules parmi : {", ".join(LISTE_AFFECTIONS)}',
                f'Affections bloquantes : {", ".join(AFF_EXCLUES)} (nécessitent soumission manuelle)',
                '',
                '=== INFORMATIONS CONJOINT (si type_couverture = Famille) ===',
                'conjoint_nom, conjoint_prenom',
                'conjoint_date_naissance, conjoint_lieu_naissance, conjoint_contact, conjoint_numero_cnam',
                'conjoint_nationalite, conjoint_taille, conjoint_poids, conjoint_tension_arterielle',
                'conjoint_etat_civil, conjoint_emploi_actuel',
                '',
                '=== INFORMATIONS ENFANTS (si nombre_enfants > 0) ===',
                'Pour chaque enfant (enfant1, enfant2, enfant3...) :',
                'enfantX_nom, enfantX_prenom',
                'enfantX_date_naissance, enfantX_lieu_naissance, enfantX_contact, enfantX_numero_cnam',
                'enfantX_taille, enfantX_poids, enfantX_tension_arterielle, enfantX_niveau_etude',
                '',
                '⚠️ Les enfants à partir du 4ème sont facturés en supplément'
            ]
        })
        instructions.to_excel(writer, index=False, sheet_name='Instructions')
    
    output.seek(0)
    return output.getvalue()
