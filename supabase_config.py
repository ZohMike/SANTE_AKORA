"""
Configuration et connexion à Supabase pour l'application Assur Defender
"""
import os
from supabase import create_client, Client
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

# Configuration Supabase
SUPABASE_URL = "https://wzrgcuapmdosgwnymsvi.supabase.co"
SUPABASE_KEY = "sb_secret_pp_K106G8v5u4gc8FSWM9g_3K9VmEO0"

# Créer le client Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


class SupabaseManager:
    """Gestionnaire pour toutes les opérations Supabase"""
    
    def __init__(self):
        self.client = supabase
    
    # ==================== COTATIONS ====================
    
    def creer_cotation(self, data: Dict[str, Any]) -> Dict:
        """
        Créer une nouvelle cotation
        
        Args:
            data: Dictionnaire contenant les données de la cotation
                - reference (str): Référence unique de la cotation
                - type_client (str): 'particulier' ou 'corporate'
                - prospect (str): Nom du prospect/entreprise
                - apporteur (str): Nom de l'apporteur
                - produit (str): Produit sélectionné
                - type_couverture (str): Type de couverture
                - prime_nette (float): Prime nette
                - prime_ttc (float): Prime TTC
                - accessoires (float): Montant des accessoires
                - taxe (float): Montant de la taxe
                - reduction_commerciale (float): Réduction appliquée (%)
                - duree_contrat (int): Durée en mois
                - statut (str): 'brouillon', 'validee', 'signee'
                - details (dict): Détails complets de la cotation (JSON)
        
        Returns:
            Dict: Résultat de l'insertion
        """
        try:
            cotation_data = {
                "reference": data.get("reference"),
                "type_client": data.get("type_client"),
                "prospect": data.get("prospect"),
                "apporteur": data.get("apporteur"),
                "produit": data.get("produit"),
                "type_couverture": data.get("type_couverture"),
                "prime_nette": data.get("prime_nette"),
                "prime_ttc": data.get("prime_ttc"),
                "accessoires": data.get("accessoires", 0),
                "taxe": data.get("taxe", 0),
                "reduction_commerciale": data.get("reduction_commerciale", 0),
                "duree_contrat": data.get("duree_contrat", 12),
                "statut": data.get("statut", "brouillon"),
                "details": json.dumps(data.get("details", {})),
                "date_creation": datetime.now().isoformat(),
                "date_modification": datetime.now().isoformat()
            }
            
            result = self.client.table("cotations").insert(cotation_data).execute()
            return {"success": True, "data": result.data}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def obtenir_cotation(self, cotation_id: int) -> Optional[Dict]:
        """Obtenir une cotation par son ID"""
        try:
            result = self.client.table("cotations").select("*").eq("id", cotation_id).execute()
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            print(f"Erreur lors de la récupération de la cotation: {e}")
            return None
    
    def obtenir_cotation_par_reference(self, reference: str) -> Optional[Dict]:
        """Obtenir une cotation par sa référence"""
        try:
            result = self.client.table("cotations").select("*").eq("reference", reference).execute()
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            print(f"Erreur lors de la récupération de la cotation: {e}")
            return None
    
    def lister_cotations(self, filtre: Optional[Dict] = None, limite: int = 50) -> List[Dict]:
        """
        Lister les cotations avec filtres optionnels
        
        Args:
            filtre: Dictionnaire de filtres (statut, type_client, apporteur, etc.)
            limite: Nombre maximum de résultats
        """
        try:
            query = self.client.table("cotations").select("*")
            
            if filtre:
                if "statut" in filtre:
                    query = query.eq("statut", filtre["statut"])
                if "type_client" in filtre:
                    query = query.eq("type_client", filtre["type_client"])
                if "apporteur" in filtre:
                    query = query.eq("apporteur", filtre["apporteur"])
            
            result = query.order("date_creation", desc=True).limit(limite).execute()
            return result.data
        except Exception as e:
            print(f"Erreur lors du listage des cotations: {e}")
            return []
    
    def mettre_a_jour_cotation(self, cotation_id: int, data: Dict) -> Dict:
        """Mettre à jour une cotation existante"""
        try:
            data["date_modification"] = datetime.now().isoformat()
            if "details" in data and isinstance(data["details"], dict):
                data["details"] = json.dumps(data["details"])
            
            result = self.client.table("cotations").update(data).eq("id", cotation_id).execute()
            return {"success": True, "data": result.data}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def supprimer_cotation(self, cotation_id: int) -> Dict:
        """Supprimer une cotation"""
        try:
            result = self.client.table("cotations").delete().eq("id", cotation_id).execute()
            return {"success": True, "data": result.data}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== POLICES ====================
    
    def creer_police(self, data: Dict[str, Any]) -> Dict:
        """
        Créer une nouvelle police d'assurance
        
        Args:
            data: Dictionnaire contenant les données de la police
                - numero_police (str): Numéro unique de police
                - cotation_id (int): ID de la cotation associée
                - assure_principal (str): Nom de l'assuré principal
                - type_police (str): 'particulier' ou 'corporate'
                - produit (str): Produit souscrit
                - date_effet (str): Date d'effet
                - date_echeance (str): Date d'échéance
                - prime_annuelle (float): Prime annuelle
                - statut (str): 'en_cours', 'suspendue', 'resiliee'
                - beneficiaires (list): Liste des bénéficiaires
                - documents (dict): Documents associés (JSON)
        """
        try:
            police_data = {
                "numero_police": data.get("numero_police"),
                "cotation_id": data.get("cotation_id"),
                "assure_principal": data.get("assure_principal"),
                "type_police": data.get("type_police"),
                "produit": data.get("produit"),
                "date_effet": data.get("date_effet"),
                "date_echeance": data.get("date_echeance"),
                "prime_annuelle": data.get("prime_annuelle"),
                "statut": data.get("statut", "en_cours"),
                "beneficiaires": json.dumps(data.get("beneficiaires", [])),
                "documents": json.dumps(data.get("documents", {})),
                "date_creation": datetime.now().isoformat(),
                "date_modification": datetime.now().isoformat()
            }
            
            result = self.client.table("polices").insert(police_data).execute()
            return {"success": True, "data": result.data}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def obtenir_police(self, police_id: int) -> Optional[Dict]:
        """Obtenir une police par son ID"""
        try:
            result = self.client.table("polices").select("*").eq("id", police_id).execute()
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            print(f"Erreur lors de la récupération de la police: {e}")
            return None
    
    def obtenir_police_par_numero(self, numero_police: str) -> Optional[Dict]:
        """Obtenir une police par son numéro"""
        try:
            result = self.client.table("polices").select("*").eq("numero_police", numero_police).execute()
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            print(f"Erreur lors de la récupération de la police: {e}")
            return None
    
    def lister_polices(self, filtre: Optional[Dict] = None, limite: int = 50) -> List[Dict]:
        """Lister les polices avec filtres optionnels"""
        try:
            query = self.client.table("polices").select("*")
            
            if filtre:
                if "statut" in filtre:
                    query = query.eq("statut", filtre["statut"])
                if "type_police" in filtre:
                    query = query.eq("type_police", filtre["type_police"])
                if "assure_principal" in filtre:
                    query = query.ilike("assure_principal", f"%{filtre['assure_principal']}%")
            
            result = query.order("date_creation", desc=True).limit(limite).execute()
            return result.data
        except Exception as e:
            print(f"Erreur lors du listage des polices: {e}")
            return []
    
    def mettre_a_jour_police(self, police_id: int, data: Dict) -> Dict:
        """Mettre à jour une police existante"""
        try:
            data["date_modification"] = datetime.now().isoformat()
            if "beneficiaires" in data and isinstance(data["beneficiaires"], list):
                data["beneficiaires"] = json.dumps(data["beneficiaires"])
            if "documents" in data and isinstance(data["documents"], dict):
                data["documents"] = json.dumps(data["documents"])
            
            result = self.client.table("polices").update(data).eq("id", police_id).execute()
            return {"success": True, "data": result.data}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== CLIENTS ====================
    
    def creer_client(self, data: Dict[str, Any]) -> Dict:
        """
        Créer un nouveau client
        
        Args:
            data: Dictionnaire contenant les données du client
                - nom (str): Nom du client
                - type_client (str): 'particulier' ou 'entreprise'
                - email (str): Email
                - telephone (str): Téléphone
                - adresse (str): Adresse
                - ville (str): Ville
                - pays (str): Pays
                - informations_supplementaires (dict): Infos supplémentaires (JSON)
        """
        try:
            client_data = {
                "nom": data.get("nom"),
                "type_client": data.get("type_client"),
                "email": data.get("email"),
                "telephone": data.get("telephone"),
                "adresse": data.get("adresse"),
                "ville": data.get("ville", "Abidjan"),
                "pays": data.get("pays", "Côte d'Ivoire"),
                "informations_supplementaires": json.dumps(data.get("informations_supplementaires", {})),
                "date_creation": datetime.now().isoformat(),
                "date_modification": datetime.now().isoformat()
            }
            
            result = self.client.table("clients").insert(client_data).execute()
            return {"success": True, "data": result.data}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def obtenir_client(self, client_id: int) -> Optional[Dict]:
        """Obtenir un client par son ID"""
        try:
            result = self.client.table("clients").select("*").eq("id", client_id).execute()
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            print(f"Erreur lors de la récupération du client: {e}")
            return None
    
    def rechercher_clients(self, terme: str) -> List[Dict]:
        """Rechercher des clients par nom, email ou téléphone"""
        try:
            result = self.client.table("clients").select("*").or_(
                f"nom.ilike.%{terme}%,email.ilike.%{terme}%,telephone.ilike.%{terme}%"
            ).execute()
            return result.data
        except Exception as e:
            print(f"Erreur lors de la recherche de clients: {e}")
            return []
    
    def lister_clients(self, limite: int = 50) -> List[Dict]:
        """Lister tous les clients"""
        try:
            result = self.client.table("clients").select("*").order("date_creation", desc=True).limit(limite).execute()
            return result.data
        except Exception as e:
            print(f"Erreur lors du listage des clients: {e}")
            return []
    
    # ==================== SINISTRES ====================
    
    def creer_sinistre(self, data: Dict[str, Any]) -> Dict:
        """
        Créer une déclaration de sinistre
        
        Args:
            data: Dictionnaire contenant les données du sinistre
                - numero_sinistre (str): Numéro unique du sinistre
                - police_id (int): ID de la police concernée
                - date_sinistre (str): Date du sinistre
                - type_sinistre (str): Type de sinistre
                - description (str): Description
                - montant_declare (float): Montant déclaré
                - montant_indemnise (float): Montant indemnisé
                - statut (str): 'en_cours', 'clos', 'refuse'
                - documents (dict): Documents du sinistre (JSON)
        """
        try:
            sinistre_data = {
                "numero_sinistre": data.get("numero_sinistre"),
                "police_id": data.get("police_id"),
                "date_sinistre": data.get("date_sinistre"),
                "type_sinistre": data.get("type_sinistre"),
                "description": data.get("description"),
                "montant_declare": data.get("montant_declare"),
                "montant_indemnise": data.get("montant_indemnise", 0),
                "statut": data.get("statut", "en_cours"),
                "documents": json.dumps(data.get("documents", {})),
                "date_creation": datetime.now().isoformat(),
                "date_modification": datetime.now().isoformat()
            }
            
            result = self.client.table("sinistres").insert(sinistre_data).execute()
            return {"success": True, "data": result.data}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def lister_sinistres_police(self, police_id: int) -> List[Dict]:
        """Lister tous les sinistres d'une police"""
        try:
            result = self.client.table("sinistres").select("*").eq("police_id", police_id).order("date_sinistre", desc=True).execute()
            return result.data
        except Exception as e:
            print(f"Erreur lors du listage des sinistres: {e}")
            return []
    
    # ==================== STATISTIQUES ====================
    
    def obtenir_statistiques_generales(self) -> Dict:
        """Obtenir les statistiques générales du portefeuille"""
        try:
            # Nombre de cotations
            cotations = self.client.table("cotations").select("*", count="exact").execute()
            nb_cotations = cotations.count if cotations.count else 0
            
            # Nombre de polices actives
            polices_actives = self.client.table("polices").select("*", count="exact").eq("statut", "en_cours").execute()
            nb_polices_actives = polices_actives.count if polices_actives.count else 0
            
            # Nombre de clients
            clients = self.client.table("clients").select("*", count="exact").execute()
            nb_clients = clients.count if clients.count else 0
            
            # Nombre de sinistres en cours
            sinistres_en_cours = self.client.table("sinistres").select("*", count="exact").eq("statut", "en_cours").execute()
            nb_sinistres_en_cours = sinistres_en_cours.count if sinistres_en_cours.count else 0
            
            return {
                "nb_cotations": nb_cotations,
                "nb_polices_actives": nb_polices_actives,
                "nb_clients": nb_clients,
                "nb_sinistres_en_cours": nb_sinistres_en_cours
            }
        except Exception as e:
            print(f"Erreur lors du calcul des statistiques: {e}")
            return {
                "nb_cotations": 0,
                "nb_polices_actives": 0,
                "nb_clients": 0,
                "nb_sinistres_en_cours": 0
            }


# Instance globale du gestionnaire
db = SupabaseManager()
