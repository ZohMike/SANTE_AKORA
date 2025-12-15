# ==============================================================================
# INTÉGRATION DU PDF COMPARATIF DANS SANTECOTATION.PY
# ==============================================================================

"""
Ce fichier montre comment intégrer le générateur PDF comparatif intelligent
dans santecotation.py pour les cotations multi-barèmes Particuliers.
"""

# ------------------------------------------------------------------------------
# 1. IMPORT À AJOUTER (en plus de l'import existant)
# ------------------------------------------------------------------------------

from pdf_generator import (
    generer_pdf_cotation_particulier,
    generer_pdf_comparatif_particulier  # ← NOUVEAU
)

# ------------------------------------------------------------------------------
# 2. INTÉGRATION DANS LA SECTION MULTI-BARÈMES PARTICULIERS
# ------------------------------------------------------------------------------

"""
Cherchez dans santecotation.py la section où vous affichez les résultats 
des cotations multi-barèmes (après le calcul de plusieurs barèmes).

Typiquement autour de la ligne 2450-2650 où vous avez :
    if 'resultats_part_multi' in st.session_state:
        resultats_multi = st.session_state['resultats_part_multi']
"""

# CODE À INSÉRER APRÈS L'AFFICHAGE DES RÉSULTATS MULTI-BARÈMES

# === GÉNÉRATION DU PDF COMPARATIF ===
st.markdown("---")
st.markdown("### 📄 Document Comparatif PDF")

# Générer un numéro de devis unique
if 'numero_devis_comparatif' not in st.session_state:
    st.session_state['numero_devis_comparatif'] = f"COMP-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

numero_devis = st.session_state['numero_devis_comparatif']

with st.container(border=True):
    st.info("💡 Générez un document PDF comparatif intelligent avec tableau récapitulatif")
    
    col_pdf1, col_pdf2 = st.columns([3, 1])
    
    with col_pdf1:
        st.markdown(f"**📋 Devis N° :** `{numero_devis}`")
        st.markdown(f"**👤 Client :** {principal_data['nom']} {principal_data['prenom']}")
        
        # Compter les options
        nb_baremes = len(baremes_affiches)
        st.markdown(f"**📊 Nombre de cotations :** {nb_baremes}")
        
        # Afficher un aperçu des barèmes
        baremes_uniques = set(baremes_affiches)
        st.caption(f"Produits : {', '.join([PRODUITS_PARTICULIERS_UI[b] for b in baremes_uniques])}")
    
    with col_pdf2:
        # Préparer les informations client
        client_info = {
            'nom': principal_data.get('nom', ''),
            'prenom': principal_data.get('prenom', ''),
            'contact': principal_data.get('contact', ''),
        }
        
        # Préparer la liste des résultats au format attendu
        resultats_list = []
        
        for idx, bareme_key in enumerate(baremes_affiches):
            # Récupérer le résultat pour ce barème
            resultat_data = resultats_multi[idx]
            resultat = resultat_data['resultat']
            
            # Récupérer la configuration du barème
            config_bareme = configurations_baremes.get(idx, {})
            type_couv = config_bareme.get('type_couverture', 'Personne seule')
            
            # Ajouter à la liste
            resultats_list.append({
                'resultat': resultat,
                'produit_key': bareme_key,
                'produit_name': PRODUITS_PARTICULIERS_UI[bareme_key],
                'type_couverture': type_couv
            })
        
        # Générer le PDF comparatif
        try:
            pdf_bytes = generer_pdf_comparatif_particulier(
                resultats_list=resultats_list,
                client_info=client_info,
                numero_devis=numero_devis
            )
            
            # Bouton de téléchargement
            st.download_button(
                label="📥 PDF Comparatif",
                data=pdf_bytes,
                file_name=f"Comparatif_{numero_devis}.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )
            
            st.success("✅ PDF prêt !")
            
        except Exception as e:
            st.error(f"❌ Erreur PDF : {str(e)}")
            import traceback
            st.code(traceback.format_exc())

# ------------------------------------------------------------------------------
# 3. EXEMPLE COMPLET AVEC CONTEXTE
# ------------------------------------------------------------------------------

"""
Voici un exemple complet de l'endroit où insérer ce code dans santecotation.py :
"""

# APRÈS LE BOUTON "GÉNÉRER LA PROPOSITION COMMERCIALE"
# Typiquement autour de la ligne 2730

"""
if 'resultats_part_multi' in st.session_state:
    resultats_multi = st.session_state['resultats_part_multi']
    baremes_affiches = st.session_state['baremes_selectionnes']
    
    # ... Affichage des résultats individuels ...
    
    # === FORÇAGE MANUEL (si présent) ===
    # ... code du forçage manuel ...
    
    # === GÉNÉRATION DU PDF COMPARATIF === ⭐ INSÉRER ICI
    st.markdown("---")
    st.markdown("### 📄 Document Comparatif PDF")
    
    if 'numero_devis_comparatif' not in st.session_state:
        st.session_state['numero_devis_comparatif'] = f"COMP-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    
    numero_devis = st.session_state['numero_devis_comparatif']
    
    with st.container(border=True):
        st.info("💡 PDF comparatif intelligent - Regroupe automatiquement les cotations similaires")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"**Devis :** `{numero_devis}`")
            st.markdown(f"**Client :** {principal_data['nom']} {principal_data['prenom']}")
            
            # Compter combien de groupes seront créés
            from collections import defaultdict
            groupes = defaultdict(list)
            for idx, bareme_key in enumerate(baremes_affiches):
                config = configurations_baremes.get(idx, {})
                type_couv = config.get('type_couverture', 'Personne seule')
                key = (PRODUITS_PARTICULIERS_UI[bareme_key], type_couv)
                groupes[key].append(idx)
            
            st.markdown(f"**Options dans le PDF :** {len(groupes)}")
            
            # Afficher le détail des groupes
            for (produit, type_c), indices in groupes.items():
                st.caption(f"• {produit} ({type_c}) : {len(indices)} cotation(s)")
        
        with col2:
            # Préparer les données
            client_info = {
                'nom': principal_data.get('nom', ''),
                'prenom': principal_data.get('prenom', ''),
                'contact': principal_data.get('contact', ''),
            }
            
            resultats_list = []
            for idx, bareme_key in enumerate(baremes_affiches):
                resultat_data = resultats_multi[idx]
                config = configurations_baremes.get(idx, {})
                
                resultats_list.append({
                    'resultat': resultat_data['resultat'],
                    'produit_key': bareme_key,
                    'produit_name': PRODUITS_PARTICULIERS_UI[bareme_key],
                    'type_couverture': config.get('type_couverture', 'Personne seule')
                })
            
            # Générer le PDF
            try:
                pdf_bytes = generer_pdf_comparatif_particulier(
                    resultats_list=resultats_list,
                    client_info=client_info,
                    numero_devis=numero_devis
                )
                
                st.download_button(
                    label="📥 Télécharger",
                    data=pdf_bytes,
                    file_name=f"Comparatif_{numero_devis}.pdf",
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True
                )
                
            except Exception as e:
                st.error(f"Erreur : {str(e)}")
"""

# ------------------------------------------------------------------------------
# 4. FORMAT DES DONNÉES REQUISES
# ------------------------------------------------------------------------------

"""
Structure attendue pour resultats_list :

resultats_list = [
    {
        'resultat': {
            'prime_nette_finale': 350000.0,
            'accessoires': 10000.0,
            'taxe': 28800.0,
            'prime_lsp': 20000.0,
            'prime_assist_psy': 35000.0,
            'prime_ttc_totale': 443800.0,
            'surprime_risques_taux': 15.0,  # Optionnel
            'surprime_age_taux': 0.0,       # Optionnel
            'affections_declarees': [],     # Optionnel
            # ... autres champs du résultat
        },
        'produit_key': 'rubis_80',
        'produit_name': '80% CI RUBIS',
        'type_couverture': 'Personne seule'
    },
    # ... autres cotations
]

Structure client_info :

client_info = {
    'nom': 'KOUAME',
    'prenom': 'Jean',
    'contact': '+225 07 12 34 56 78'
}
"""

# ------------------------------------------------------------------------------
# 5. LOGIQUE DE REGROUPEMENT AUTOMATIQUE
# ------------------------------------------------------------------------------

"""
Le PDF regroupe automatiquement par (Produit, Type de Couverture) :

EXEMPLE 1 : Même produit, différentes personnes
─────────────────────────────────────────────────
Input : 
- 80% CI RUBIS - Personne seule - Prime 350k
- 80% CI RUBIS - Personne seule - Prime 360k
- 80% CI RUBIS - Famille - Prime 800k

Output PDF :
┌──────────────────┬──────────────────┐
│ OPTION 1 (80%)   │ OPTION 2 (80%)   │
│ Personne seule   │ Famille          │
├──────────────────┼──────────────────┤
│ Population: 2    │ Population: 1    │
│ Prime: 350,000   │ Prime: 800,000   │
│      + 360,000   │                  │
│      = 710,000   │                  │
└──────────────────┴──────────────────┘

EXEMPLE 2 : Produits différents
─────────────────────────────────
Input :
- 70% CI SAPHIR - Personne seule - Prime 280k
- 80% CI RUBIS - Personne seule - Prime 350k
- 80% CI RUBIS - Famille - Prime 800k

Output PDF :
┌──────────────┬──────────────┬──────────────┐
│ OPTION 1     │ OPTION 2     │ OPTION 3     │
│ (70%)        │ (80%)        │ (80%)        │
│ Pers. seule  │ Pers. seule  │ Famille      │
├──────────────┼──────────────┼──────────────┤
│ Pop: 1       │ Pop: 1       │ Pop: 1       │
│ 280,000      │ 350,000      │ 800,000      │
└──────────────┴──────────────┴──────────────┘
"""

# ------------------------------------------------------------------------------
# 6. PLACEMENT DANS SANTECOTATION.PY
# ------------------------------------------------------------------------------

"""
EMPLACEMENT PRÉCIS :

1. Cherchez la ligne contenant :
   st.markdown("---")
   if st.button("📝 GÉNÉRER LA PROPOSITION COMMERCIALE"...

2. JUSTE AVANT ce bouton, ajoutez le code du PDF comparatif

3. Structure finale :
   
   # Affichage des résultats multi-barèmes
   for idx, bareme_key in enumerate(baremes_affiches):
       # ... affichage ...
   
   # Section Forçage Manuel (si présente)
   st.markdown("### ⚙️ Forçage Manuel...")
   # ... code forçage ...
   
   # ⭐ NOUVEAU : PDF COMPARATIF (INSÉRER ICI)
   st.markdown("---")
   st.markdown("### 📄 Document Comparatif PDF")
   # ... code PDF comparatif ...
   
   # Bouton proposition commerciale existant
   st.markdown("---")
   if st.button("📝 GÉNÉRER LA PROPOSITION COMMERCIALE"...
"""

# ------------------------------------------------------------------------------
# 7. NOTES IMPORTANTES
# ------------------------------------------------------------------------------

"""
✅ AVANTAGES :
- Regroupement automatique intelligent
- Réduction du nombre de colonnes
- Affichage du détail + total
- Format professionnel tableau comparatif
- Population comptée automatiquement

⚠️ ATTENTION :
- Nécessite que configurations_baremes contienne 'type_couverture' pour chaque barème
- Les résultats doivent contenir tous les champs nécessaires (voir format ci-dessus)
- Tester avec différents scénarios avant déploiement

🧪 TESTS RECOMMANDÉS :
1. 1 barème seul
2. 2 barèmes identiques, même type
3. 2 barèmes identiques, types différents
4. 3+ barèmes mixtes
5. Barème spécial

📊 DÉPENDANCES :
- reportlab (déjà dans requirements.txt)
- pdf_generator.py (nouveau module)
- data.py (pour TARIFS_PARTICULIERS)
"""
