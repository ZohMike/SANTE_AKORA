pip install supabase-py
import streamlit as st
import pandas as pd
from supabase import create_client, Client
import io 
from datetime import datetime

# --- Configuration et Dépendances ---
# Utilisation du mode 'wide' pour exploiter toute la largeur de l'écran
st.set_page_config(page_title="Gestion et Audit des Barèmes Santé (Desktop)", layout="wide")

# =========================================================================
# === STYLES CSS PERSONNALISÉS (Légers et Modernes) ===
# =========================================================================

CUSTOM_CSS = """
<style>
/* 1. Amélioration de l'aspect des cartes/conteneurs (Desktop Look) */
div[data-testid="stVerticalBlock"] > div:not(:first-child) > div {
    /* Retrait des marges internes excessives pour un look plus desktop */
    padding: 15px; 
    border-radius: 10px;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05); /* Ombre douce */
    margin-bottom: 25px;
    border: 1px solid #e0e0e0;
}

/* 2. Style des titres de section pour une meilleure hiérarchie */
h3 {
    border-left: 5px solid #007bff; /* Accent bleu */
    padding-left: 10px;
    margin-top: 25px !important;
    font-size: 1.5rem; /* Taille de police plus lisible */
}

/* 3. Style pour mettre en valeur la version active */
.active-version-card {
    background-color: #f8f9fa; /* Gris très clair */
    border: 1px solid #007bff !important;
    padding: 15px !important;
    border-radius: 8px !important;
    margin: 10px 0;
    font-size: 1.1em;
    color: #333;
}

/* 4. Bouton primaire accentué (Enregistrer, Importer) */
button[data-testid="stFormSubmitButton"] > div {
    background-color: #28a745; /* Vert pour l'action positive */
    border-radius: 6px;
    font-weight: bold;
    color: white !important;
}

/* 5. Ajustement de l'Uploader de Fichiers (plus compact) */
div[data-testid="stFileUploader"] {
    padding: 5px;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# =========================================================================
# === CONFIGURATION SUPABASE ===
# =========================================================================

# Valeurs par défaut pour le test (NE PAS UTILISER EN PRODUCTION)
SUPABASE_URL_DEFAULT = "https://ikfkfanfnbdlemkkcwnl.supabase.co"
SUPABASE_KEY_DEFAULT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlrZmtmYW5mbmJkbGVta2tjd25sIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA2ODQ0MTksImV4cCI6MjA3NjI2MDQxOX0.Z-_emTDVVbuJ1roPBMRS8ElJG6-QB3ZmRk12O0Qvb4"


@st.cache_resource
def init_supabase() -> Client:
    """Initialise la connexion à Supabase en utilisant les secrets Streamlit ou les valeurs par défaut."""
    
    supabase_url = None
    supabase_key = None
    
    try:
        supabase_url = st.secrets["supabase"]["url"]
        supabase_key = st.secrets["supabase"]["key"]
    except KeyError:
        supabase_url = SUPABASE_URL_DEFAULT
        supabase_key = SUPABASE_KEY_DEFAULT
        st.sidebar.warning("⚠️ Utilisation des clés par défaut. Configurez .streamlit/secrets.toml pour la production.")


    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        st.sidebar.success("✅ Connecté à Supabase")
        return supabase
        
    except Exception as e:
        st.error(f"❌ Erreur de connexion à Supabase: {e}")
        st.stop()

def init_database(supabase: Client):
    """Vérifie que les tables existent (Polices, Baremes et Effectifs)"""
    try:
        supabase.table('polices').select("id").limit(1).execute()
        supabase.table('baremes').select("id").limit(1).execute()
        supabase.table('effectifs').select("id").limit(1).execute()
    except Exception as e:
        st.error("❌ Erreur de schéma : Tables non trouvées ou colonnes manquantes.")
        st.info("📋 Assurez-vous d'avoir créé les tables 'polices', 'baremes' (avec nom_bareme/nom_fichier_source) et 'effectifs' (avec toutes les colonnes requises) dans votre projet Supabase.")
        st.stop()

# =========================================================================
# === FONCTIONS CRUD SUPABASE ===
# =========================================================================

# --- Fonctions Polices ---

def get_polices_existantes(supabase: Client):
    """Récupère la liste des polices existantes"""
    try:
        response = supabase.table('polices').select('*').order('nom_police').execute()
        
        if not response.data:
            return pd.DataFrame(columns=['id', 'numero_police', 'nom_police', 'date_creation'])
        
        df = pd.DataFrame(response.data)
        df['id'] = df['id'].astype(int) 
        df['display_name'] = df['numero_police'].astype(str) + ' - ' + df['nom_police'].astype(str)
        return df
        
    except Exception as e:
        st.error(f"❌ Erreur lors de la récupération des polices : {e}")
        return pd.DataFrame()

def creer_police(supabase: Client, numero, nom):
    """Crée une nouvelle police"""
    try:
        response = supabase.table('polices').insert({
            'numero_police': numero,
            'nom_police': nom
        }).execute()
        
        return response.data[0]['id']
        
    except Exception as e:
        if 'unique' in str(e).lower() or 'duplicate' in str(e).lower():
            raise ValueError("Ce numéro de police existe déjà.")
        else:
            st.error(f"❌ Erreur lors de la création : {e}")
            return None

def supprimer_police(supabase: Client, id_police):
    """Supprime une police et tous les barèmes et effectifs associés"""
    try:
        supabase.table('polices').delete().eq('id', id_police).execute()
    except Exception as e:
        st.error(f"❌ Erreur lors de la suppression de la police : {e}")

# --- Fonctions Barèmes ---

def get_bareme_versions_existantes(supabase: Client, id_police):
    """Récupère tous les noms de barème (versions) pour une police donnée en utilisant Pandas."""
    try:
        response = supabase.table('baremes') \
                           .select('nom_bareme') \
                           .eq('id_police', id_police) \
                           .execute()
        
        if not response.data:
            return []
        
        df = pd.DataFrame(response.data)
        versions = df['nom_bareme'].dropna().unique().tolist()
        
        return sorted(versions)
    
    except Exception as e:
        st.error(f"❌ Erreur de récupération des versions de barème : {e}")
        return []

def inserer_bareme(supabase: Client, id_police, nom_bareme, nom_fichier_source, rubrique, sous_garantie, taux_prive, 
                   taux_public, statut, plafond, plafond_pers, plafond_fam):
    """Insert une nouvelle ligne de barème manuellement (avec nom et source)"""
    try:
        supabase.table('baremes').insert({
            'id_police': id_police,
            'nom_bareme': nom_bareme,
            'nom_fichier_source': nom_fichier_source,
            'rubrique': rubrique,
            'sous_garantie': sous_garantie,
            'taux_couverture_prive': taux_prive,
            'taux_couverture_public': taux_public,
            'statut': statut,
            'plafond': plafond,
            'plafond_personne': plafond_pers,
            'plafond_famille': plafond_fam
        }).execute()
    except Exception as e:
        st.error(f"❌ Erreur lors de l'insertion de la ligne : {e}")

def inserer_bareme_en_masse(id_police, nom_bareme, nom_fichier_source, df_import):
    """Insert un DataFrame complet de barèmes par lots (Supabase) (avec nom et source)"""
    
    df_import = df_import.copy()
    
    required_template_cols = ['Rubrique', 'Sous-Garantie']
    if not all(col in df_import.columns for col in required_template_cols):
        raise ValueError("Le fichier doit contenir les colonnes 'Rubrique' et 'Sous-Garantie'.")
    
    df_import.rename(columns={
        'Rubrique': 'rubrique', 'Sous-Garantie': 'sous_garantie', 'Taux Privé (%)': 'taux_couverture_prive',
        'Taux Public (%)': 'taux_couverture_public', 'Statut': 'statut', 'Plafond': 'plafond',
        'Plafond/pers.': 'plafond_personne', 'Plafond/fam.': 'plafond_famille'
    }, inplace=True)
    
    db_cols = [
        'id_police', 'nom_bareme', 'nom_fichier_source', 'rubrique', 'sous_garantie', 
        'taux_couverture_prive', 'taux_couverture_public', 'statut', 'plafond', 
        'plafond_personne', 'plafond_famille'
    ]
    
    df_import = df_import.fillna({
        'plafond': '', 'statut': 'Garanti', 
        'plafond_personne': 0.0, 'plafond_famille': 0.0,
        'taux_couverture_prive': 0.0, 'taux_couverture_public': 0.0
    })
    
    try:
        for col in ['taux_couverture_prive', 'taux_couverture_public', 'plafond_personne', 'plafond_famille']:
            df_import[col] = df_import[col].astype(float)
    except Exception as e:
        raise ValueError(f"Erreur de type dans les colonnes numériques : {e}. Vérifiez le format.")

    # Assignation des colonnes de traçabilité
    df_import['id_police'] = id_police
    df_import['nom_bareme'] = nom_bareme
    df_import['nom_fichier_source'] = nom_fichier_source
    
    records = df_import.reindex(columns=db_cols).to_dict('records')
    
    total_inserted = 0
    batch_size = 100 
    
    try:
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            supabase.table('baremes').insert(batch).execute()
            total_inserted += len(batch)
        
        return total_inserted
    
    except Exception as e:
        raise Exception(f"Erreur d'insertion en masse Supabase : {e}")

def get_baremes_par_police_id(supabase: Client, id_police, nom_bareme):
    """Récupère toutes les lignes de barème pour une VERSION et une police données."""
    try:
        # Utilisation des parenthèses englobantes pour garantir l'indentation
        response = (
            supabase.table('baremes') 
            .select('*') 
            .eq('id_police', id_police) 
            .eq('nom_bareme', nom_bareme) 
            .order('id') 
            .execute()
        )
        
        if not response.data:
            return pd.DataFrame()
        
        df = pd.DataFrame(response.data)
        df['id'] = df['id'].astype(int) 
        return df
        
    except Exception as e:
        st.error(f"❌ Erreur lors de la récupération du barème : {e}")
        return pd.DataFrame()

def supprimer_ligne_bareme(supabase: Client, id_ligne):
    """Supprime une ligne spécifique de barème"""
    try:
        supabase.table('baremes').delete().eq('id', id_ligne).execute()
    except Exception as e:
        st.error(f"❌ Erreur lors de la suppression de la ligne : {e}")

def supprimer_tous_baremes_version(supabase: Client, id_police, nom_bareme):
    """Supprime toutes les lignes d'une version de barème spécifique."""
    try:
        # Utilisation des parenthèses englobantes pour garantir l'indentation
        (
            supabase.table('baremes')
            .delete()
            .eq('id_police', id_police)
            .eq('nom_bareme', nom_bareme)
            .execute()
        )
    except Exception as e:
        st.error(f"❌ Erreur lors de la suppression du barème : {e}")

# --- Fonctions Effectifs ---

def inserer_effectif_en_masse(supabase: Client, id_police, df_import):
    """Insert un DataFrame complet d'effectifs dans la table 'effectifs'."""
    
    df_import = df_import.copy()
    
    df_import.rename(columns={
        'No Client': 'no_client', 'Souscripteur': 'souscripteur', 'Intermediaire': 'intermediaire', 
        'Id Police': 'id_police_source', 'No Police': 'no_police', 'Libelle Police': 'libelle_police', 
        'Id College': 'id_college', 'college': 'college', 'Date Effet': 'date_effet', 
        'Echéance': 'echeance', 'No Adhérent': 'no_adherent', 'Adhérent': 'adherent', 
        'No Bénéficiaire': 'no_beneficiaire', 'Nom': 'nom', 'Prénoms': 'prenoms', 
        'Lien Parenté': 'lien_parente', 'Sexe': 'sexe', 'Naissance': 'naissance', 
        'Tél Portable': 'tel_portable', 'Entrée': 'entree', 'Date effet': 'date_effet_beneficiaire'
    }, inplace=True)
    
    db_cols = [
        'id_police', 'no_client', 'souscripteur', 'intermediaire', 'no_police', 'libelle_police', 
        'id_college', 'college', 'date_effet', 'echeance', 'no_adherent', 'adherent', 
        'no_beneficiaire', 'nom', 'prenoms', 'lien_parente', 'sexe', 'naissance', 
        'tel_portable', 'entree', 'date_effet_beneficiaire'
    ]
    
    date_cols = ['date_effet', 'echeance', 'naissance', 'entree', 'date_effet_beneficiaire']
    for col in date_cols:
        if col in df_import.columns:
            df_import[col] = pd.to_datetime(df_import[col], errors='coerce').dt.date

    df_import['id_police'] = id_police # Clé étrangère
    df_import = df_import.reindex(columns=db_cols)
    
    records = df_import.to_dict('records')
    
    total_inserted = 0
    batch_size = 100 
    
    try:
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            batch_clean = [{k: (v.isoformat() if isinstance(v, datetime.date) else v) for k, v in row.items()} for row in batch]
            supabase.table('effectifs').insert(batch_clean).execute()
            total_inserted += len(batch)
        
        return total_inserted
    
    except Exception as e:
        raise Exception(f"Erreur d'insertion en masse de l'effectif Supabase : {e}")


def get_effectifs_par_police(supabase: Client, id_police):
    """Récupère l'effectif actuel pour une police donnée."""
    try:
        response = (
            supabase.table('effectifs') 
            .select('*') 
            .eq('id_police', id_police) 
            .order('id', desc=True) 
            .limit(500) 
            .execute()
        )
        
        if not response.data:
            return pd.DataFrame()
        
        df = pd.DataFrame(response.data)
        return df
        
    except Exception as e:
        st.error(f"❌ Erreur lors de la récupération des effectifs : {e}")
        return pd.DataFrame()

def supprimer_effectifs_police(supabase: Client, id_police):
    """Supprime tous les effectifs d'une police (nécessaire avant un nouvel import si on veut écraser)."""
    try:
        supabase.table('effectifs').delete().eq('id_police', id_police).execute()
    except Exception as e:
        st.error(f"❌ Erreur lors de la suppression des effectifs : {e}")


# =========================================================================
# === LOGIQUE D'AUDIT DES SINISTRES (Inchangée) ===
# =========================================================================

def executer_audit_sinistres(df_sinistres, df_baremes_selectionne):
    """Effectue l'audit des données sinistres par rapport au barème."""
    
    required_cols = ['Rubrique', 'Sous-Garantie', 'Montant_Réclamé', 'Montant_Remboursé']
    if not all(col in df_sinistres.columns for col in required_cols):
        st.error(f"❌ Les données sinistres doivent contenir les colonnes : {', '.join(required_cols)}")
        return pd.DataFrame(), pd.DataFrame()
        
    df_audit = df_sinistres.copy()

    df_audit['Rubrique'] = df_audit['Rubrique'].astype(str)
    df_audit['Sous-Garantie'] = df_audit['Sous-Garantie'].astype(str)
    
    baremes_cols = df_baremes_selectionne[['rubrique', 'sous_garantie', 'taux_couverture_prive', 'plafond_personne', 'statut']].copy()
    
    df_audit = df_audit.merge(
        baremes_cols,
        left_on=['Rubrique', 'Sous-Garantie'], 
        right_on=['rubrique', 'sous_garantie'], 
        how='left'
    )
    
    df_audit['Anomalie_Description'] = ""
    df_audit['Statut_Audit'] = 'OK'
    
    # Règle 1: Barème manquant
    condition_bareme_manquant = df_audit['rubrique'].isna()
    df_audit.loc[condition_bareme_manquant, 'Statut_Audit'] = 'ANOMALIE'
    df_audit.loc[condition_bareme_manquant, 'Anomalie_Description'] += 'Barème non trouvé ; '
    
    # Règle 2: Remboursement sur-taux
    taux_applicable = df_audit['taux_couverture_prive'] / 100
    maximum_theorique = df_audit['Montant_Réclamé'] * taux_applicable
    
    condition_sur_taux = (
        df_audit['Montant_Remboursé'] > maximum_theorique
    ) & (~condition_bareme_manquant)
    
    df_audit.loc[condition_sur_taux, 'Statut_Audit'] = 'ANOMALIE'
    df_audit.loc[condition_sur_taux, 'Anomalie_Description'] += "Remboursement > Taux max couvert ; "
        
    # Règle 3: Statut "Non garanti"
    condition_non_garanti = (df_audit['statut'] == 'Non garanti')
    df_audit.loc[condition_non_garanti, 'Statut_Audit'] = 'ANOMALIE'
    df_audit.loc[condition_non_garanti, 'Anomalie_Description'] += "Acte/Rubrique non garanti(e) ; "
    
    # Règle 4: Remboursement > Montant Réclamé
    condition_sur_reclamation = (df_audit['Montant_Remboursé'] > df_audit['Montant_Réclamé'])
    df_audit.loc[condition_sur_reclamation, 'Statut_Audit'] = 'ANOMALIE'
    df_audit.loc[condition_sur_reclamation, 'Anomalie_Description'] += "Remboursement > Réclamation ; "
    
    df_anomalies = df_audit[df_audit['Statut_Audit'] == 'ANOMALIE'].copy()
    
    cols_to_drop = ['rubrique', 'sous_garantie', 'taux_couverture_prive', 'plafond_personne', 'statut']
    df_anomalies.drop(columns=[col for col in cols_to_drop if col in df_anomalies.columns], errors='ignore', inplace=True)
    
    df_anomalies['Anomalie_Description'] = df_anomalies['Anomalie_Description'].str.replace(r' ; $', '', regex=True)

    return df_audit, df_anomalies

# =========================================================================
# === INTERFACE UTILISATEUR (STREAMLIT) ===
# =========================================================================

# Initialisation Supabase
supabase = init_supabase()
init_database(supabase)

st.title("🛡️ Outil de Gestion et d'Audit Assurance Santé")
st.caption("💾 Base de données : Supabase (PostgreSQL)")

# Menu latéral pour la navigation principale (Desktop Style)
with st.sidebar:
    st.header("Navigation")
    module_selection = st.radio(
        "Modules :", 
        ["⚙️ Paramétrage", "🔎 Audit"],
        index=0,
        key="main_module_select"
    )

# Affichage des contenus basé sur la sélection du sidebar
if module_selection == "⚙️ Paramétrage":
    
    st.header("Gestion des Polices et de leurs Composantes")

    df_polices = get_polices_existantes(supabase)
    
    st.subheader("1. Création ou Sélection de la Police")
    
    col_mode, col_select = st.columns([1, 2])
    
    mode_police = col_mode.radio("Mode :", ["Créer une nouvelle police", "Sélectionner une police existante"], key="mode_police")

    selected_police_id = None
    selected_police_name = None

    # Bloc de création/sélection de la police
    with st.container():
        if mode_police == "Créer une nouvelle police":
            col_num, col_nom = st.columns(2)
            new_num = col_num.text_input("Numéro de la nouvelle police", key="new_num")
            new_nom = col_nom.text_input("Nom de la police", key="new_nom")
            
            if st.button("💾 Créer cette police"):
                if new_num and new_nom:
                    try:
                        creer_police(supabase, new_num, new_nom)
                        st.success(f"✅ Police **{new_num} - {new_nom}** créée avec succès!")
                        st.rerun()
                    except ValueError as ve:
                        st.error(f"❌ Erreur: {ve}")
                    except Exception as e:
                        st.error(f"❌ Erreur lors de la création : {e}")
                else:
                    st.warning("Veuillez renseigner le numéro et le nom.")
        else:
            if not df_polices.empty:
                col_select_drop, col_delete_btn = st.columns([3, 1])
                
                police_selectionnee_display = col_select_drop.selectbox(
                    "Choisir une police existante :",
                    df_polices['display_name'].tolist(),
                    key="select_police"
                )
                
                if police_selectionnee_display:
                    selected_police_id = df_polices[df_polices['display_name'] == police_selectionnee_display]['id'].iloc[0]
                    selected_police_name = df_polices[df_polices['display_name'] == police_selectionnee_display]['nom_police'].iloc[0]
                    
                    if col_delete_btn.button(f"🗑️ Supprimer", type="secondary"):
                        supprimer_police(supabase, selected_police_id)
                        st.success(f"La police **{police_selectionnee_display}** a été supprimée.")
                        st.rerun()

            else:
                st.info("Aucune police existante. Veuillez en créer une d'abord.")


    st.markdown("---")
    
    # --- GESTION DE L'EFFECTIF ET DES BARÈMES DANS DES SOUS-ONGLETS ---
    if selected_police_id is not None:
        
        st.subheader(f"2. Gestion des Données pour : **{selected_police_name}**")
        
        tab_effectif, tab_baremes = st.tabs(["👥 Gérer l'Effectif", "📋 Gérer les Barèmes"])
        
        
        # =============================================================
        # === SOUS-ONGLET EFFECTIF ===
        # =============================================================
        with tab_effectif:
            st.markdown("### Importation des Données d'Effectif")

            # 1. TEMPLATE EXCEL EFFECTIF
            effectif_template_data = {
                'No Client': ['C001'], 'Souscripteur': ['STE AZUR'], 'Intermediaire': ['COURTIER X'], 
                'Id Police': [selected_police_id], 'No Police': ['POL987'], 'Libelle Police': ['Option Standard'], 
                'Id College': ['CAD'], 'college': ['Cadres'], 'Date Effet': ['2024-01-01'], 
                'Echéance': ['2024-12-31'], 'No Adhérent': ['AD001'], 'Adhérent': ['M. Dupont'], 
                'No Bénéficiaire': ['BEN001'], 'Nom': ['DUPONT'], 'Prénoms': ['Jean'], 
                'Lien Parenté': ['Principal'], 'Sexe': ['M'], 'Naissance': ['1980-05-15'], 
                'Tél Portable': ['0700112233'], 'Entrée': ['2024-01-01'], 'Date effet': ['2024-01-01']
            }
            effectif_df_template = pd.DataFrame(effectif_template_data)
            
            buffer_eff = io.BytesIO()
            with pd.ExcelWriter(buffer_eff, engine='xlsxwriter') as writer:
                 effectif_df_template.to_excel(writer, index=False, sheet_name='Effectif')
            
            st.download_button(
                label="⬇️ Télécharger le TEMPLATE Effectif XLSX",
                data=buffer_eff.getvalue(),
                file_name='template_effectif_sante.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )
            
            # 2. UPLOADER EFFECTIF
            uploaded_file_effectif = st.file_uploader(
                "Chargez le fichier Effectif (Excel/CSV)",
                type=['csv', 'xlsx'],
                key="upload_effectif"
            )

            if 'df_effectif_temp' not in st.session_state:
                st.session_state.df_effectif_temp = None
                
            if uploaded_file_effectif:
                try:
                    if uploaded_file_effectif.name.endswith('.csv'):
                        df_import_eff_temp = pd.read_csv(uploaded_file_effectif)
                    else:
                        df_import_eff_temp = pd.read_excel(uploaded_file_effectif)
                    
                    st.session_state.df_effectif_temp = df_import_eff_temp
                    st.success(f"Fichier **{uploaded_file_effectif.name}** chargé pour l'effectif. {len(df_import_eff_temp)} lignes.")
                    
                except Exception as e:
                    st.error(f"❌ Erreur lors de la lecture du fichier effectif : {e}")
                    st.session_state.df_effectif_temp = None 
            
            # 3. Aperçu et bouton d'insertion
            if st.session_state.df_effectif_temp is not None:
                st.markdown("##### Aperçu de l'Effectif à Importer")
                st.dataframe(st.session_state.df_effectif_temp.head(10), use_container_width=True)
                
                if st.button("💥 Écraser & Importer l'Effectif", type="primary", key="import_effectif_btn"):
                    with st.spinner("Suppression de l'ancien effectif et importation du nouveau en cours..."):
                        try:
                            supprimer_effectifs_police(supabase, selected_police_id)
                            lignes_inserees = inserer_effectif_en_masse(supabase, selected_police_id, st.session_state.df_effectif_temp)
                            
                            st.success(f"🎉 **{lignes_inserees}** personnes de l'effectif importées avec succès!")
                            st.session_state.df_effectif_temp = None
                            st.rerun()
                        
                        except Exception as e:
                            st.error(f"❌ Erreur lors de l'insertion de l'effectif : {e}")

            st.markdown("---")
            
            # 4. Affichage de l'effectif actuel
            df_current_effectif = get_effectifs_par_police(supabase, selected_police_id)
            if not df_current_effectif.empty:
                st.subheader("Effectif Actuel Lié à la Police")
                
                st.metric("Total Personnes Enregistrées", len(df_current_effectif))
                
                cols_to_display_eff = ['no_adherent', 'adherent', 'no_beneficiaire', 'nom', 'prenoms', 'lien_parente', 'naissance', 'sexe']
                st.dataframe(df_current_effectif[cols_to_display_eff], use_container_width=True)
            else:
                st.info("Aucune donnée d'effectif enregistrée pour cette police.")

        
        
        # =============================================================
        # === SOUS-ONGLET BARÈMES (Versionnalisation) ===
        # =============================================================
        with tab_baremes:
            
            st.subheader("Gestion des Versions de Barème")
            
            versions_existantes = get_bareme_versions_existantes(supabase, selected_police_id)
            
            selected_bareme_name = None
            
            # Bloc de sélection/création de version (plus compact)
            with st.container():
                
                if versions_existantes:
                    col_mode, col_select_v, col_new_v = st.columns([1, 2, 2])
                    
                    mode_version = col_mode.radio("Mode :", ["Existant", "Nouveau"], key="mode_version")
                    
                    if mode_version == "Existant":
                        selected_bareme_name = col_select_v.selectbox(
                            "Modifier/Afficher la version :",
                            versions_existantes,
                            key="selected_bareme_name"
                        )
                    else:
                        new_bareme_name = col_new_v.text_input(
                            "Nom de la NOUVELLE Version",
                            placeholder="Ex: Barème 2025 - V2.1",
                            key="new_bareme_name"
                        )
                        if new_bareme_name:
                            if new_bareme_name in versions_existantes:
                                col_new_v.error("Ce nom existe déjà.")
                                selected_bareme_name = None
                            else:
                                selected_bareme_name = new_bareme_name
                        else:
                            selected_bareme_name = None 
                else:
                    st.warning("⚠️ Aucune version de barème n'existe pour cette police. Veuillez en créer une.")
                    selected_bareme_name = st.text_input(
                        "Nom de la Première Version du Barème",
                        placeholder="Ex: Barème Standard V1.0",
                        key="first_bareme_name"
                    )
            
            # Affichage de la version active
            if selected_bareme_name:
                st.markdown(f'<div class="active-version-card">Version Active: 🏷️ <strong>{selected_bareme_name}</strong></div>', unsafe_allow_html=True)
            else:
                st.info("Veuillez sélectionner ou nommer une version du barème.")
            
            st.markdown("---")

            
            if selected_bareme_name:
                
                # --- Importation par fichier Excel/CSV ---
                st.markdown("#### 📥 Importation de Lignes de Barème")
                
                col_template, col_uploader = st.columns([1, 2])
                
                # 1. TEMPLATE EXCEL (.xlsx)
                exemple_df = pd.DataFrame({
                    "Rubrique": ["Consultations", "Hospitalisation"],
                    "Sous-Garantie": ["Généralistes", "Chambre commune"],
                    "Taux Privé (%)": [80, 100],
                    "Taux Public (%)": [80, 100],
                    "Statut": ["Garanti", "Plafonné"],
                    "Plafond": ["Max 25000", "Selon le tarif"],
                    "Plafond/pers.": [0, 500000],
                    "Plafond/fam.": [0, 1000000]
                })
                
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    exemple_df.to_excel(writer, index=False, sheet_name='Barèmes')
                
                col_template.markdown("##### Fichier Source")
                col_template.download_button(
                    label="⬇️ Télécharger le TEMPLATE XLSX",
                    data=buffer.getvalue(),
                    file_name='template_bareme_sante.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                )
                
                # 2. UPLOADER ET LOGIQUE D'IMPORT
                uploaded_file_bareme = col_uploader.file_uploader(
                    "Chargez les lignes pour cette version :",
                    type=['csv', 'xlsx'],
                    key="upload_bareme_lines"
                )
                
                if 'df_bareme_temp' not in st.session_state:
                    st.session_state.df_bareme_temp = None

                if uploaded_file_bareme:
                    try:
                        if st.session_state.get('uploaded_filename_bareme') != uploaded_file_bareme.name:
                            st.session_state.df_bareme_temp = None
                            st.session_state.uploaded_filename_bareme = uploaded_file_bareme.name
                            
                        if uploaded_file_bareme.name.endswith('.csv'):
                            df_import_temp = pd.read_csv(uploaded_file_bareme)
                        else:
                            df_import_temp = pd.read_excel(uploaded_file_bareme)
                        
                        st.session_state.df_bareme_temp = df_import_temp
                        st.success(f"Fichier **{uploaded_file_bareme.name}** chargé. Aperçu ci-dessous.")
                        
                    except Exception as e:
                        st.error(f"❌ Erreur lors de la lecture du fichier : {e}")
                        st.session_state.df_bareme_temp = None 
                
                
                # --- Affichage de l'aperçu et bouton d'import ---
                if st.session_state.df_bareme_temp is not None:
                    st.markdown("##### Aperçu des Lignes à Importer")
                    st.info(f"Lignes à insérer : **{len(st.session_state.df_bareme_temp)}**")
                    
                    st.dataframe(st.session_state.df_bareme_temp.head(), use_container_width=True)
                    
                    # Bouton d'importation (séparé)
                    if st.button(f"📥 Importer {len(st.session_state.df_bareme_temp)} lignes", type="primary", key="import_bareme_btn"):
                        with st.spinner("Importation et validation en cours..."):
                            try:
                                lignes_inserees = inserer_bareme_en_masse(
                                    selected_police_id, 
                                    selected_bareme_name, 
                                    st.session_state.uploaded_filename_bareme, 
                                    st.session_state.df_bareme_temp
                                )
                                st.success(f"🎉 **{lignes_inserees}** lignes importées avec succès!")
                                st.session_state.df_bareme_temp = None
                                st.rerun()

                            except ValueError as ve:
                                st.error(f"❌ Erreur de formatage : {ve}")
                            except Exception as e:
                                st.error(f"❌ Erreur lors de l'insertion en base : {e}") 

                st.markdown("---")

                # --- Formulaire d'ajout d'un barème détaillé (Manuelle) ---
                st.markdown("#### ➕ Ajouter une ligne manuellement")

                with st.form("formulaire_bareme", clear_on_submit=True):
                    col1, col2, col3 = st.columns(3)
                    rubrique = col1.text_input("Rubrique", placeholder="Consultations")
                    sous_garantie = col2.text_input("Sous-garantie", placeholder="Généralistes")
                    statut = col3.selectbox("Statut", ["Garanti", "Non garanti", "Plafonné"])

                    col4, col5, col6 = st.columns(3)
                    taux_prive = col4.number_input("Taux Privé (%)", 0, 100, 80)
                    plafond_pers = col5.number_input("Plafond/pers. (FCFA)", 0.0, step=1000.0)
                    plafond = col6.text_input("Plafond (Texte)", value="Selon tarif")


                    if st.form_submit_button("💾 Enregistrer la ligne"):
                        if rubrique and sous_garantie:
                            inserer_bareme(
                                supabase, selected_police_id, 
                                selected_bareme_name, "Manuel", 
                                rubrique, sous_garantie, 
                                taux_prive, 80, statut, plafond, plafond_pers, 0 # Taux public/Plafond famille par défaut
                            )
                            st.success("✅ Ligne enregistrée!")
                            st.rerun()
                        else:
                            st.warning("⚠️ Remplissez la rubrique et sous-garantie.")

                st.markdown("---")

                # --- Affichage et gestion des barèmes enregistrés ---
                st.subheader(f"3. 📋 Lignes actuelles de la Version : {selected_bareme_name}")
                
                baremes_df = get_baremes_par_police_id(supabase, int(selected_police_id), selected_bareme_name)

                if not baremes_df.empty:
                    display_df = baremes_df.rename(columns={
                        "nom_bareme": "Nom Version", "nom_fichier_source": "Fichier Source",
                        "rubrique": "Rubrique", "sous_garantie": "Sous-Garantie", 
                        "taux_couverture_prive": "Taux Privé (%)", "taux_couverture_public": "Taux Public (%)", 
                        "statut": "Statut", "plafond": "Plafond", "plafond_personne": "Plafond/pers.", 
                        "plafond_famille": "Plafond/fam.", "date_creation": "Créé le"
                    })
                    
                    cols_to_display = ["id", "Nom Version", "Fichier Source", "Rubrique", "Sous-Garantie", "Taux Privé (%)", "Plafond/pers.", "Créé le"]
                    st.dataframe(display_df[cols_to_display], use_container_width=True)

                    col1, col2, col3 = st.columns([2, 2, 3])
                    
                    with col1:
                        if st.button(f"🗑️ Supprimer TOUTES les lignes de '{selected_bareme_name}'", type="secondary"):
                            supprimer_tous_baremes_version(supabase, selected_police_id, selected_bareme_name)
                            st.success(f"🚮 Version '{selected_bareme_name}' supprimée.")
                            st.rerun()

                    with col2:
                        csv = display_df.drop(columns=["id_police", "date_creation"], errors='ignore').to_csv(index=False).encode("utf-8")
                        st.download_button("⬇️ CSV", csv, f"bareme_{selected_bareme_name}.csv", "text/csv")

                    with col3:
                        st.caption("Supprimer une ligne par ID")
                        initial_id = int(baremes_df["id"].iloc[0]) if not baremes_df.empty else 1
                        id_suppr = st.number_input("ID", min_value=1, value=initial_id, step=1)
                        
                        if st.button("🗑️ Supprimer la ligne"):
                            if id_suppr in baremes_df["id"].values:
                                supprimer_ligne_bareme(supabase, id_suppr)
                                st.success(f"✅ Ligne {id_suppr} supprimée.")
                                st.rerun()
                            else:
                                st.error("❌ ID introuvable.")
                else:
                    st.info(f"Aucune ligne dans la version '{selected_bareme_name}'.")
            else:
                st.warning("Veuillez sélectionner ou créer une version de barème.")

    else:
        st.info("👆 Créez ou sélectionnez une police.")

# --- MODULE AUDIT (Sélectionné via Sidebar) ---

elif module_selection == "🔎 Audit":
    st.header("Analyse de Conformité des Sinistres")
    
    df_polices_audit = get_polices_existantes(supabase)
    
    if df_polices_audit.empty:
        st.warning("⚠️ Aucune police. Créez-en une d'abord.")
    else:
        # 1. Sélection de la Police pour l'audit
        col_police, col_version = st.columns(2)

        police_audit_display = col_police.selectbox(
            "Police à auditer :",
            df_polices_audit['display_name'].tolist(),
            key="select_police_audit"
        )
        
        id_police_audit = df_polices_audit[df_polices_audit['display_name'] == police_audit_display]['id'].iloc[0]
        
        # 2. Sélection de la Version de Barème à utiliser pour l'audit
        versions_audit = get_bareme_versions_existantes(supabase, id_police_audit)

        if not versions_audit:
             col_version.warning(f"⚠️ Aucun barème n'existe pour la police **{police_audit_display}**.")
             st.stop()

        selected_version_audit = col_version.selectbox(
            "Version de Barème à appliquer pour l'audit :",
            versions_audit,
            key="selected_version_audit"
        )

        # Récupération des lignes de cette version
        df_baremes_audit = get_baremes_par_police_id(supabase, int(id_police_audit), selected_version_audit)


        if df_baremes_audit.empty:
            st.warning(f"⚠️ La version **{selected_version_audit}** est vide. L'audit ne peut pas être lancé.")
        else:
            st.markdown("---")
            st.subheader("Chargement des Sinistres")
            
            uploaded_sinistres = st.file_uploader(
                "Fichier Sinistres (CSV/Excel)",
                type=['csv', 'xlsx'],
                key="upload_sinistres"
            )

            if uploaded_sinistres:
                try:
                    if uploaded_sinistres.name.endswith('.csv'):
                        df_sinistres = pd.read_csv(uploaded_sinistres)
                    else: 
                        df_sinistres = pd.read_excel(uploaded_sinistres)
                    
                    st.success(f"✅ {len(df_sinistres)} lignes chargées.")
                    
                    with st.expander("Aperçu"):
                        st.dataframe(df_sinistres.head(), use_container_width=True)

                    st.markdown("---")
                    
                    if st.button(f"🚀 Lancer l'Audit", type="primary"):
                        with st.spinner("Analyse..."):
                            df_resultat, df_anomalies = executer_audit_sinistres(df_sinistres, df_baremes_audit)
                            
                            st.subheader("Résultats")
                            total = len(df_resultat)
                            anomalies = len(df_anomalies)
                            
                            col1, col2, col3 = st.columns(3)
                            col1.metric("Total", total)
                            col2.metric("Anomalies", anomalies)
                            col3.metric("Conformité", f"{((total - anomalies) / total * 100):.1f}%")

                            if anomalies > 0:
                                st.error(f"🚨 **{anomalies} Anomalies**")
                                st.dataframe(df_anomalies, use_container_width=True)
                                
                                csv_anom = df_anomalies.to_csv(index=False).encode('utf-8')
                                st.download_button(
                                    "⬇️ Télécharger Anomalies",
                                    csv_anom,
                                    f"anomalies_audit_{police_audit_display.replace(' ', '_')}_{selected_version_audit.replace(' ', '_')}.csv",
                                    "text/csv"
                                )
                            else:
                                st.success("✅ Aucune anomalie détectée.")
                    
                except Exception as e:
                    st.error(f"❌ Erreur : {e}")

# Footer (Affiché une seule fois)
st.markdown("---")

st.caption("💡 Application de gestion et d'audit des barèmes d'assurance santé - Propulsée par Supabase")
