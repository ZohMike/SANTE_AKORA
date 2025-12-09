# ==============================================================================
# INTÉGRATION DU GÉNÉRATEUR PDF DANS SANTECOTATION.PY
# ==============================================================================

"""
Ce fichier montre comment intégrer le générateur PDF dans votre fichier principal.
Copiez ces sections dans santecotation.py aux emplacements appropriés.
"""

# ------------------------------------------------------------------------------
# 1. IMPORTS À AJOUTER AU DÉBUT DU FICHIER (après les autres imports)
# ------------------------------------------------------------------------------

from pdf_generator import generer_pdf_cotation_particulier
import uuid

# ------------------------------------------------------------------------------
# 2. CODE À AJOUTER APRÈS L'AFFICHAGE DES RÉSULTATS PARTICULIERS
# ------------------------------------------------------------------------------

# Exemple de placement : après avoir affiché le résultat de calcul
# Dans la section "Cotation Particuliers", après "afficher_resultat()"

# Générer un numéro de devis unique
if 'numero_devis_part' not in st.session_state:
    st.session_state['numero_devis_part'] = f"PART-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

numero_devis = st.session_state['numero_devis_part']

# Section de téléchargement du PDF
st.markdown("---")
st.markdown("### 📄 Générer le Document de Cotation")

with st.container(border=True):
    st.info("💡 Générez un document PDF professionnel avec tous les détails de la cotation.")
    
    col_pdf1, col_pdf2 = st.columns([2, 1])
    
    with col_pdf1:
        st.markdown(f"**Numéro de devis :** `{numero_devis}`")
        st.markdown(f"**Client :** {principal_data['nom']} {principal_data['prenom']}")
        st.markdown(f"**Produit :** {PRODUITS_PARTICULIERS_UI[produit_key_part]}")
    
    with col_pdf2:
        # Préparer les informations client
        client_info = {
            'nom': principal_data.get('nom', ''),
            'prenom': principal_data.get('prenom', ''),
            'contact': principal_data.get('contact', ''),
            'type_couverture': type_couverture_part,
            'nb_enfants': nb_enfants_part if type_couverture_part == "Famille" else 0
        }
        
        # Générer le PDF
        try:
            pdf_bytes = generer_pdf_cotation_particulier(
                resultat=resultat,
                produit_name=PRODUITS_PARTICULIERS_UI[produit_key_part],
                client_info=client_info,
                numero_devis=numero_devis
            )
            
            # Bouton de téléchargement
            st.download_button(
                label="📥 Télécharger le PDF",
                data=pdf_bytes,
                file_name=f"Cotation_{numero_devis}.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )
            
            st.success("✅ PDF prêt à télécharger")
            
        except Exception as e:
            st.error(f"❌ Erreur lors de la génération du PDF : {str(e)}")

# ------------------------------------------------------------------------------
# 3. EXEMPLE COMPLET D'INTÉGRATION DANS UNE SECTION
# ------------------------------------------------------------------------------

# Voici un exemple complet de code à insérer après le calcul de la prime

"""
# APRÈS LE CALCUL ET L'AFFICHAGE DU RÉSULTAT

if 'resultat_part' in st.session_state:
    resultat = st.session_state['resultat_part']
    
    # Affichage du résultat
    afficher_resultat(
        resultat, 
        PRODUITS_PARTICULIERS_UI[produit_key_part], 
        TAUX_TAXE_PARTICULIER
    )
    
    # === GÉNÉRATION DU PDF ===
    st.markdown("---")
    st.markdown("### 📄 Document de Cotation")
    
    # Générer un numéro de devis unique si pas déjà fait
    if 'numero_devis_part' not in st.session_state:
        st.session_state['numero_devis_part'] = f"PART-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    
    numero_devis = st.session_state['numero_devis_part']
    
    with st.container(border=True):
        col_info1, col_info2 = st.columns([3, 1])
        
        with col_info1:
            st.markdown(f"**📋 Devis N° :** `{numero_devis}`")
            st.markdown(f"**👤 Client :** {principal_data['nom']} {principal_data['prenom']}")
            st.markdown(f"**📦 Produit :** {PRODUITS_PARTICULIERS_UI[produit_key_part]}")
            st.markdown(f"**💰 Prime TTC :** {format_currency(resultat['prime_ttc_totale'])}")
        
        with col_info2:
            # Préparer les informations
            client_info = {
                'nom': principal_data.get('nom', ''),
                'prenom': principal_data.get('prenom', ''),
                'contact': principal_data.get('contact', ''),
                'type_couverture': type_couverture_part,
                'nb_enfants': nb_enfants_part if type_couverture_part == "Famille" else 0
            }
            
            # Générer le PDF
            try:
                pdf_bytes = generer_pdf_cotation_particulier(
                    resultat=resultat,
                    produit_name=PRODUITS_PARTICULIERS_UI[produit_key_part],
                    client_info=client_info,
                    numero_devis=numero_devis
                )
                
                # Bouton de téléchargement
                st.download_button(
                    label="📥 Télécharger PDF",
                    data=pdf_bytes,
                    file_name=f"Cotation_{numero_devis}.pdf",
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True
                )
                
            except Exception as e:
                st.error(f"Erreur PDF : {str(e)}")
    
    st.success("✅ Cotation prête - Document disponible en téléchargement")
"""

# ------------------------------------------------------------------------------
# 4. POUR LES COTATIONS MULTIPLES (COMPARAISON DE BARÈMES)
# ------------------------------------------------------------------------------

"""
Si vous avez plusieurs barèmes comparés, vous pouvez générer un PDF pour chacun :

for idx, bareme_key in enumerate(baremes_affiches):
    resultat_data = resultats_multi[idx]
    resultat = resultat_data['resultat']
    
    # Générer un numéro de devis unique pour ce barème
    numero_devis = f"PART-{datetime.now().strftime('%Y%m%d')}-{idx+1:02d}-{uuid.uuid4().hex[:4].upper()}"
    
    # Préparer les infos
    client_info = {
        'nom': principal_data.get('nom', ''),
        'prenom': principal_data.get('prenom', ''),
        'contact': principal_data.get('contact', ''),
        'type_couverture': type_couverture_part,
        'nb_enfants': nb_enfants_part
    }
    
    # Générer le PDF
    pdf_bytes = generer_pdf_cotation_particulier(
        resultat=resultat,
        produit_name=PRODUITS_PARTICULIERS_UI[bareme_key],
        client_info=client_info,
        numero_devis=numero_devis
    )
    
    # Bouton de téléchargement
    st.download_button(
        label=f"📥 PDF - {PRODUITS_PARTICULIERS_UI[bareme_key]}",
        data=pdf_bytes,
        file_name=f"Cotation_{PRODUITS_PARTICULIERS_UI[bareme_key]}_{numero_devis}.pdf",
        mime="application/pdf",
        key=f"download_pdf_{idx}"
    )
"""

# ------------------------------------------------------------------------------
# 5. NOTES D'IMPLÉMENTATION
# ------------------------------------------------------------------------------

"""
IMPORTANT :

1. Assurez-vous que pdf_generator.py est dans le même dossier que santecotation.py

2. Les dépendances nécessaires sont déjà dans requirements.txt :
   - reportlab>=4.0.0
   - Pillow>=10.0.0

3. Structure des données requises :
   
   resultat = {
       'prime_nette_finale': float,
       'accessoires': float,
       'taxe': float,
       'prime_lsp': float,
       'prime_assist_psy': float,
       'prime_ttc_totale': float,
       'surprime_grossesse': float (optionnel),
       'surprime_age_taux': float (optionnel),
       'surprime_risques_taux': float (optionnel),
       'affections_declarees': list (optionnel),
       'bareme_special': bool (optionnel),
       'facteurs': {
           'duree_contrat': int,
           'taux_taxe': float
       }
   }
   
   client_info = {
       'nom': str,
       'prenom': str,
       'contact': str,
       'type_couverture': str,
       'nb_enfants': int
   }

4. Personnalisation :
   - Modifiez les couleurs dans _setup_custom_styles()
   - Ajoutez votre logo dans _add_header()
   - Personnalisez les mentions légales
   - Ajustez les conditions particulières

5. Pour tester localement :
   streamlit run santecotation.py
   
   Le bouton de téléchargement PDF apparaîtra après le calcul de la prime.
"""
