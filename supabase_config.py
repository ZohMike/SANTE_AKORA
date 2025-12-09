import os
from supabase import create_client, Client
import streamlit as st

def get_supabase_client() -> Client:
    """
    Crée et retourne un client Supabase.
    Les credentials sont récupérés depuis les secrets Streamlit.
    """
    try:
        # En production (Streamlit Cloud), utiliser st.secrets
        if hasattr(st, 'secrets') and 'supabase' in st.secrets:
            supabase_url = st.secrets["supabase"]["url"]
            supabase_key = st.secrets["supabase"]["key"]
        else:
            # En développement local, utiliser des variables d'environnement
            supabase_url = os.environ.get("SUPABASE_URL")
            supabase_key = os.environ.get("SUPABASE_KEY")
            
            if not supabase_url or not supabase_key:
                raise ValueError(
                    "Les credentials Supabase ne sont pas configurés. "
                    "Ajoutez-les dans .streamlit/secrets.toml ou comme variables d'environnement."
                )
        
        supabase: Client = create_client(supabase_url, supabase_key)
        return supabase
    
    except Exception as e:
        st.error(f"❌ Erreur de connexion à Supabase : {str(e)}")
        return None


def test_connexion_supabase() -> bool:
    """Teste la connexion à Supabase."""
    try:
        client = get_supabase_client()
        if client is None:
            return False
        
        # Tester une requête simple
        response = client.table('devis').select("*").limit(1).execute()
        return True
    
    except Exception as e:
        st.error(f"❌ Test de connexion échoué : {str(e)}")
        return False
