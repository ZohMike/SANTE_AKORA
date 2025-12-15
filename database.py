from typing import Dict, Any, List, Optional
from datetime import datetime, date
import streamlit as st
from supabase_config import get_supabase_client
import json


class DatabaseManager:
    """Gestionnaire de base de données pour Assur Defender."""
    
    def __init__(self):
        self.client = get_supabase_client()
    
    # ==================== DEVIS ====================
    
    def sauvegarder_devis(self, devis_data: Dict[str, Any]) -> Optional[Dict]:
        """
        Sauvegarde un devis dans la base de données.
        
        Args:
            devis_data: Dictionnaire contenant toutes les informations du devis
            
        Returns:
            Le devis créé ou None en cas d'erreur
        """
        try:
            # Préparer les données pour Supabase
            data = {
                'numero_devis': devis_data.get('numero_devis'),
                'type_marche': devis_data.get('type_marche'),  # 'Particulier' ou 'Corporate'
                'produit': devis_data.get('produit'),
                'nom_client': devis_data.get('nom_client'),
                'entreprise': devis_data.get('entreprise'),  # Pour Corporate
                'secteur': devis_data.get('secteur'),  # Pour Corporate
                'type_couverture': devis_data.get('type_couverture'),
                'nb_adultes': devis_data.get('nb_adultes', 1),
                'nb_enfants': devis_data.get('nb_enfants', 0),
                'nb_enfants_supplementaires': devis_data.get('nb_enfants_supplementaires', 0),
                'prime_nette': devis_data.get('prime_nette', 0),
                'accessoires': devis_data.get('accessoires', 0),
                'services': devis_data.get('services', 0),
                'taxe': devis_data.get('taxe', 0),
                'prime_ttc': devis_data.get('prime_ttc', 0),
                'prime_finale': devis_data.get('prime_finale', 0),
                'reduction_commerciale': devis_data.get('reduction_commerciale', 0),
                'surprime_medicale': devis_data.get('surprime_medicale', 0),
                'surprime_age': devis_data.get('surprime_age', 0),
                'duree_contrat': devis_data.get('duree_contrat', 12),
                'statut': devis_data.get('statut', 'En attente'),  # En attente, Finalisé, Annulé
                'validateur': devis_data.get('validateur'),
                'motif_reduction': devis_data.get('motif_reduction'),
                'details': json.dumps(devis_data.get('details', {})),  # JSON pour infos complémentaires
                'pdf_data': devis_data.get('pdf_data'),  # PDF stocké en base64
                'created_by': devis_data.get('created_by', 'Système'),
                'date_creation': datetime.now().isoformat()
            }
            
            response = self.client.table('devis').insert(data).execute()
            
            if response.data:
                st.success(f"✅ Devis {data['numero_devis']} sauvegardé avec succès !")
                return response.data[0]
            else:
                st.error("❌ Erreur lors de la sauvegarde du devis")
                return None
                
        except Exception as e:
            st.error(f"❌ Erreur lors de la sauvegarde : {str(e)}")
            return None
    
    def recuperer_devis(self, numero_devis: str = None, limit: int = 100) -> List[Dict]:
        """
        Récupère les devis depuis la base de données.
        
        Args:
            numero_devis: Numéro spécifique de devis (optionnel)
            limit: Nombre maximum de résultats
            
        Returns:
            Liste des devis
        """
        try:
            query = self.client.table('devis').select("*")
            
            if numero_devis:
                query = query.eq('numero_devis', numero_devis)
            
            query = query.order('date_creation', desc=True).limit(limit)
            response = query.execute()
            
            if response.data:
                # Convertir les détails JSON en dict
                for devis in response.data:
                    if devis.get('details'):
                        devis['details'] = json.loads(devis['details'])
                return response.data
            return []
            
        except Exception as e:
            st.error(f"❌ Erreur lors de la récupération : {str(e)}")
            return []
    
    def mettre_a_jour_statut_devis(self, numero_devis: str, nouveau_statut: str) -> bool:
        """
        Met à jour le statut d'un devis.
        
        Args:
            numero_devis: Numéro du devis
            nouveau_statut: Nouveau statut (En attente, Finalisé, Annulé)
            
        Returns:
            True si succès, False sinon
        """
        try:
            response = self.client.table('devis').update({
                'statut': nouveau_statut,
                'date_modification': datetime.now().isoformat()
            }).eq('numero_devis', numero_devis).execute()
            
            if response.data:
                st.success(f"✅ Statut du devis {numero_devis} mis à jour : {nouveau_statut}")
                return True
            return False
            
        except Exception as e:
            st.error(f"❌ Erreur lors de la mise à jour : {str(e)}")
            return False
    
    def supprimer_devis(self, numero_devis: str) -> bool:
        """
        Supprime un devis de la base de données.
        
        Args:
            numero_devis: Numéro du devis à supprimer
            
        Returns:
            True si succès, False sinon
        """
        try:
            response = self.client.table('devis').delete().eq('numero_devis', numero_devis).execute()
            
            if response.data:
                return True
            return False
            
        except Exception as e:
            st.error(f"❌ Erreur lors de la suppression : {str(e)}")
            return False
    
    # ==================== ASSURÉS ====================
    
    def sauvegarder_assure(self, assure_data: Dict[str, Any]) -> Optional[Dict]:
        """
        Sauvegarde les informations d'un assuré.
        
        Args:
            assure_data: Dictionnaire avec les infos de l'assuré
            
        Returns:
            L'assuré créé ou None en cas d'erreur
        """
        try:
            data = {
                'numero_devis': assure_data.get('numero_devis'),
                'type_assure': assure_data.get('type_assure'),  # Principal, Conjoint, Enfant
                'nom': assure_data.get('nom'),
                'prenom': assure_data.get('prenom'),
                'date_naissance': assure_data.get('date_naissance').isoformat() if isinstance(assure_data.get('date_naissance'), date) else assure_data.get('date_naissance'),
                'lieu_naissance': assure_data.get('lieu_naissance'),
                'contact': assure_data.get('contact'),
                'numero_cnam': assure_data.get('numero_cnam'),
                'nationalite': assure_data.get('nationalite'),
                'etat_civil': assure_data.get('etat_civil'),
                'emploi_actuel': assure_data.get('emploi_actuel'),
                'taille': assure_data.get('taille'),
                'poids': assure_data.get('poids'),
                'imc': assure_data.get('imc'),
                'tension_arterielle': assure_data.get('tension_arterielle'),
                'affections': json.dumps(assure_data.get('affections', [])),
                'grossesse': assure_data.get('grossesse', False),
                'sexe': assure_data.get('sexe'),
                'details': json.dumps(assure_data.get('details', {})),
                'date_creation': datetime.now().isoformat()
            }
            
            response = self.client.table('assures').insert(data).execute()
            
            if response.data:
                return response.data[0]
            return None
            
        except Exception as e:
            st.error(f"❌ Erreur lors de la sauvegarde de l'assuré : {str(e)}")
            return None
    
    def recuperer_assures_par_devis(self, numero_devis: str) -> List[Dict]:
        """Récupère tous les assurés d'un devis."""
        try:
            response = self.client.table('assures').select("*").eq('numero_devis', numero_devis).execute()
            
            if response.data:
                for assure in response.data:
                    if assure.get('affections'):
                        assure['affections'] = json.loads(assure['affections'])
                    if assure.get('details'):
                        assure['details'] = json.loads(assure['details'])
                return response.data
            return []
            
        except Exception as e:
            st.error(f"❌ Erreur lors de la récupération des assurés : {str(e)}")
            return []
    
    # ==================== COTATIONS CORPORATE EXCEL ====================
    
    def sauvegarder_cotation_excel(self, cotation_data: Dict[str, Any]) -> Optional[Dict]:
        """Sauvegarde une cotation Excel (micro-tarification)."""
        try:
            data = {
                'numero_devis': cotation_data.get('numero_devis'),
                'entreprise': cotation_data.get('entreprise'),
                'produit': cotation_data.get('produit'),
                'nb_total_lignes': cotation_data.get('nb_total_lignes'),
                'nb_eligibles': cotation_data.get('nb_eligibles'),
                'nb_exclus': cotation_data.get('nb_exclus'),
                'nb_erreurs': cotation_data.get('nb_erreurs'),
                'prime_nette_totale': cotation_data.get('prime_nette_totale'),
                'prime_ttc_totale': cotation_data.get('prime_ttc_totale'),
                'prime_finale': cotation_data.get('prime_finale'),
                'reduction_commerciale': cotation_data.get('reduction_commerciale', 0),
                'duree_contrat': cotation_data.get('duree_contrat', 12),
                'statut': cotation_data.get('statut', 'En cours'),
                'resultats_detailles': json.dumps(cotation_data.get('resultats_detailles', {})),
                'date_creation': datetime.now().isoformat()
            }
            
            response = self.client.table('cotations_excel').insert(data).execute()
            
            if response.data:
                st.success(f"✅ Cotation Excel sauvegardée !")
                return response.data[0]
            return None
            
        except Exception as e:
            st.error(f"❌ Erreur lors de la sauvegarde de la cotation : {str(e)}")
            return None
    
    # ==================== STATISTIQUES ====================
    
    def get_statistiques_globales(self) -> Dict[str, Any]:
        """Récupère les statistiques globales."""
        try:
            # Total devis
            total_devis = self.client.table('devis').select("*", count='exact').execute()
            
            # Devis par statut
            devis_finalises = self.client.table('devis').select("*", count='exact').eq('statut', 'Finalisé').execute()
            devis_en_attente = self.client.table('devis').select("*", count='exact').eq('statut', 'En attente').execute()
            
            # Devis par type
            devis_particuliers = self.client.table('devis').select("*", count='exact').eq('type_marche', 'Particulier').execute()
            devis_corporate = self.client.table('devis').select("*", count='exact').eq('type_marche', 'Corporate').execute()
            
            # Total primes
            all_devis = self.client.table('devis').select("prime_finale").execute()
            total_primes = sum(d.get('prime_finale', 0) for d in all_devis.data) if all_devis.data else 0
            
            return {
                'total_devis': total_devis.count if hasattr(total_devis, 'count') else 0,
                'devis_finalises': devis_finalises.count if hasattr(devis_finalises, 'count') else 0,
                'devis_en_attente': devis_en_attente.count if hasattr(devis_en_attente, 'count') else 0,
                'devis_particuliers': devis_particuliers.count if hasattr(devis_particuliers, 'count') else 0,
                'devis_corporate': devis_corporate.count if hasattr(devis_corporate, 'count') else 0,
                'total_primes': total_primes
            }
            
        except Exception as e:
            st.error(f"❌ Erreur lors de la récupération des statistiques : {str(e)}")
            return {}
    
    # ==================== RECHERCHE ====================
    
    def rechercher_devis(self, 
                        type_marche: str = None,
                        statut: str = None,
                        date_debut: str = None,
                        date_fin: str = None,
                        nom_client: str = None) -> List[Dict]:
        """Recherche avancée de devis avec filtres."""
        try:
            query = self.client.table('devis').select("*")
            
            if type_marche:
                query = query.eq('type_marche', type_marche)
            
            if statut:
                query = query.eq('statut', statut)
            
            if date_debut:
                query = query.gte('date_creation', date_debut)
            
            if date_fin:
                query = query.lte('date_creation', date_fin)
            
            if nom_client:
                query = query.ilike('nom_client', f'%{nom_client}%')
            
            response = query.order('date_creation', desc=True).execute()
            
            if response.data:
                for devis in response.data:
                    if devis.get('details'):
                        devis['details'] = json.loads(devis['details'])
                return response.data
            return []
            
        except Exception as e:
            st.error(f"❌ Erreur lors de la recherche : {str(e)}")
            return []
