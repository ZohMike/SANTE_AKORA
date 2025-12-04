from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date

# --- 1. DONNÉES ET CONSTANTES ---

# Taux de taxe par marché
TAUX_TAXE_CORPORATE = 0.03
TAUX_TAXE_PARTICULIER = 0.08
SURPRIME_FORFAITAIRE_GROSSESSE = 400000 
SURPRIME_AGE_PLUS_51 = 25  # Surprime de 25% pour les personnes de plus de 51 ans

# Configuration limites
MAX_ENFANTS_SUPPLEMENTAIRES = 10
MAX_REDUCTION_COMMERCIALE_PART = 10
MAX_REDUCTION_COMMERCIALE_CORP = 20
MAX_SURPRIME_RISQUE_CORP = 20

# --- Tableau des affections et taux de majoration ---
TAUX_MAJORATION_MEDICALE = {
    "Hypertension artérielle": 40, "Diabète": 40, "Drépanocytose": 40, "Épilepsie": 40,
    "Cataracte": 40, "Glaucome": 40, "Goutte": 40, "Hépatite virale": 50,
    "Hyperthyroïdie": 40, "Adénome de la prostate": 60, "Asthme": 45,
    "Affections rhumatismales (arthrose)": 45, "Fibrome utérin": 60, "Adénomyose": 45,
    "Kyste ovarien": 60, "Hypercholestérolémie": 40
}
AFF_EXCLUES = ["Cancer", "AVC"]
LISTE_AFFECTIONS = list(TAUX_MAJORATION_MEDICALE.keys())

# --- DONNÉES TARIFS PARTICULIERS ---
TARIFS_PARTICULIERS = {
    '70_CI_SAPHIR': {
        'name': '70% CI SAPHIR', 
        'taux': 70, 
        'type': 'CI', 
        'personne_seule': {
            'prime_nette': 175378, 
            'accessoires': 10000, 
            'prime_lsp': 20000, 
            'prime_assist_psy': 35000
        }, 
        'famille': {
            'prime_nette': 701510, 
            'accessoires': 10000, 
            'prime_lsp': 20000, 
            'prime_assist_psy': 35000
        }, 
        'enfant_supplementaire': {
            'prime_nette': 105227, 
            'accessoires': 5000, 
            'prime_lsp': 0, 
            'prime_assist_psy': 0
        }
    },
    '80_CI_RUBIS': {
        'name': '80% CI RUBIS', 
        'taux': 80, 
        'type': 'CI', 
        'personne_seule': {
            'prime_nette': 324266, 
            'accessoires': 10000, 
            'prime_lsp': 20000, 
            'prime_assist_psy': 35000
        }, 
        'famille': {
            'prime_nette': 1057066, 
            'accessoires': 10000, 
            'prime_lsp': 20000, 
            'prime_assist_psy': 35000
        }, 
        'enfant_supplementaire': {
            'prime_nette': 194560, 
            'accessoires': 5000, 
            'prime_lsp': 0, 
            'prime_assist_psy': 0
        }
    },
    '90_CI_EMERAUDE': {
        'name': '90% CI EMERAUDE', 
        'taux': 90, 
        'type': 'CI', 
        'personne_seule': {
            'prime_nette': 430933, 
            'accessoires': 10000, 
            'prime_lsp': 20000, 
            'prime_assist_psy': 35000
        }, 
        'famille': {
            'prime_nette': 1723733, 
            'accessoires': 10000, 
            'prime_lsp': 20000, 
            'prime_assist_psy': 35000
        }, 
        'enfant_supplementaire': {
            'prime_nette': 258560, 
            'accessoires': 5000, 
            'prime_lsp': 0, 
            'prime_assist_psy': 0
        }
    },
    '100_CI_DIAMANT': {
        'name': '100% CI DIAMANT', 
        'taux': 100, 
        'type': 'CI', 
        'personne_seule': {
            'prime_nette': 875378, 
            'accessoires': 10000, 
            'prime_lsp': 20000, 
            'prime_assist_psy': 35000
        }, 
        'famille': {
            'prime_nette': 3059822, 
            'accessoires': 10000, 
            'prime_lsp': 20000, 
            'prime_assist_psy': 35000
        }, 
        'enfant_supplementaire': {
            'prime_nette': 525227, 
            'accessoires': 5000, 
            'prime_lsp': 0, 
            'prime_assist_psy': 0
        }
    },
}

# Créer le dictionnaire avec "Barème Spécial" en première position
PRODUITS_PARTICULIERS_UI = {'bareme_special': 'BARÈME SPÉCIAL'}
PRODUITS_PARTICULIERS_UI.update({k: v['name'] for k, v in TARIFS_PARTICULIERS.items()})

# --- DONNÉES TARIFS CORPORATE (Grille complète) ---
TARIFS_CORPORATE = {
    '70_eco': {
        'name': '70% ECO',
        'taux': 70,
        'type': 'ECO',
        'plafond_personne': 1000000,
        'plafond_famille': 1500000,
        'personne_seule': {
            'prime_nette': 109111,
            'accessoires': 10000,
            'prime_lsp': 20000,
            'prime_assist_psy': 35000
        },
        'famille': {
            'prime_nette': 356111,
            'accessoires': 10000,
            'prime_lsp': 20000,
            'prime_assist_psy': 35000
        },
        'enfant_supplementaire': {
            'prime_nette': 71222,
            'accessoires': 5000,
            'prime_lsp': 0,
            'prime_assist_psy': 0
        }
    },
    '70_ci': {
        'name': '70% CI',
        'taux': 70,
        'type': 'CI',
        'plafond_personne': 2500000,
        'plafond_famille': 5000000,
        'personne_seule': {
            'prime_nette': 338358,
            'accessoires': 10000,
            'prime_lsp': 20000,
            'prime_assist_psy': 35000
        },
        'famille': {
            'prime_nette': 1015075,
            'accessoires': 10000,
            'prime_lsp': 20000,
            'prime_assist_psy': 35000
        },
        'enfant_supplementaire': {
            'prime_nette': 203015,
            'accessoires': 5000,
            'prime_lsp': 0,
            'prime_assist_psy': 0
        }
    },
    '80_eco': {
        'name': '80% ECO',
        'taux': 80,
        'type': 'ECO',
        'plafond_personne': 1000000,
        'plafond_famille': 1750000,
        'personne_seule': {
            'prime_nette': 196400,
            'accessoires': 10000,
            'prime_lsp': 20000,
            'prime_assist_psy': 35000
        },
        'famille': {
            'prime_nette': 641000,
            'accessoires': 10000,
            'prime_lsp': 20000,
            'prime_assist_psy': 35000
        },
        'enfant_supplementaire': {
            'prime_nette': 117840,
            'accessoires': 5000,
            'prime_lsp': 0,
            'prime_assist_psy': 0
        }
    },
    '80_eco_plus': {
        'name': '80% ECO+',
        'taux': 80,
        'type': 'ECO+',
        'plafond_personne': 2000000,
        'plafond_famille': 3500000,
        'personne_seule': {
            'prime_nette': 316223,
            'accessoires': 10000,
            'prime_lsp': 20000,
            'prime_assist_psy': 35000
        },
        'famille': {
            'prime_nette': 948668,
            'accessoires': 10000,
            'prime_lsp': 20000,
            'prime_assist_psy': 35000
        },
        'enfant_supplementaire': {
            'prime_nette': 189734,
            'accessoires': 5000,
            'prime_lsp': 0,
            'prime_assist_psy': 0
        }
    },
    '80_ci': {
        'name': '80% CI',
        'taux': 80,
        'type': 'CI',
        'plafond_personne': 5000000,
        'plafond_famille': 10000000,
        'personne_seule': {
            'prime_nette': 466242,
            'accessoires': 10000,
            'prime_lsp': 20000,
            'prime_assist_psy': 35000
        },
        'famille': {
            'prime_nette': 1398727,
            'accessoires': 10000,
            'prime_lsp': 20000,
            'prime_assist_psy': 35000
        },
        'enfant_supplementaire': {
            'prime_nette': 279745,
            'accessoires': 5000,
            'prime_lsp': 0,
            'prime_assist_psy': 0
        }
    },
    '85_ci': {
        'name': '85% CI',
        'taux': 85,
        'type': 'CI',
        'plafond_personne': 7000000,
        'plafond_famille': 12000000,
        'personne_seule': {
            'prime_nette': 575711,
            'accessoires': 10000,
            'prime_lsp': 20000,
            'prime_assist_psy': 35000
        },
        'famille': {
            'prime_nette': 1578601,
            'accessoires': 10000,
            'prime_lsp': 20000,
            'prime_assist_psy': 35000
        },
        'enfant_supplementaire': {
            'prime_nette': 315720,
            'accessoires': 5000,
            'prime_lsp': 0,
            'prime_assist_psy': 0
        }
    },
    '90_ci': {
        'name': '90% CI',
        'taux': 90,
        'type': 'CI',
        'plafond_personne': 8000000,
        'plafond_famille': 16000000,
        'personne_seule': {
            'prime_nette': 685180,
            'accessoires': 10000,
            'prime_lsp': 20000,
            'prime_assist_psy': 35000
        },
        'famille': {
            'prime_nette': 1758474,
            'accessoires': 10000,
            'prime_lsp': 20000,
            'prime_assist_psy': 35000
        },
        'enfant_supplementaire': {
            'prime_nette': 351695,
            'accessoires': 5000,
            'prime_lsp': 0,
            'prime_assist_psy': 0
        }
    },
    '100_ci': {
        'name': '100% CI',
        'taux': 100,
        'type': 'CI',
        'plafond_personne': 10000000,
        'plafond_famille': 20000000,
        'personne_seule': {
            'prime_nette': 808513,
            'accessoires': 10000,
            'prime_lsp': 20000,
            'prime_assist_psy': 35000
        },
        'famille': {
            'prime_nette': 2055541,
            'accessoires': 10000,
            'prime_lsp': 20000,
            'prime_assist_psy': 35000
        },
        'enfant_supplementaire': {
            'prime_nette': 411108,
            'accessoires': 5000,
            'prime_lsp': 0,
            'prime_assist_psy': 0
        }
    },
}
# Créer les dictionnaires avec "Barème Spécial" en première position
PRODUITS_CORPORATE_UI = {'bareme_special': 'BARÈME SPÉCIAL'}
PRODUITS_CORPORATE_UI.update({k: v['name'] for k, v in TARIFS_CORPORATE.items()})

# --- Structure Excel attendue ---
COLONNES_EXCEL_REQUISES = [
    'nom', 'prenom', 'date_naissance', 'type_couverture', 
    'nombre_enfants', 'grossesse', 'affections'
]
