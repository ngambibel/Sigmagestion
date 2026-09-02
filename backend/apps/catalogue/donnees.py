"""Catalogue de démarrage proposé au propriétaire lors de l'installation.

Prix par défaut modifiables — repères de terrain (secrétariat camerounais).
"""

SERVICES_DEFAUT = [
    {"nom": "Photocopie N&B", "categorie": "Reprographie", "unite_facturation": "page", "prix": 25, "consomme_stock": True},
    {"nom": "Impression N&B", "categorie": "Impression", "unite_facturation": "page", "prix": 50, "consomme_stock": True},
    {"nom": "Impression couleur", "categorie": "Impression", "unite_facturation": "page", "prix": 250, "consomme_stock": True},
    {"nom": "Reliure spirale", "categorie": "Finition", "unite_facturation": "document", "prix": 500, "consomme_stock": True},
    {"nom": "Plastification", "categorie": "Finition", "unite_facturation": "piece", "prix": 500, "consomme_stock": True},
    {"nom": "Saisie de document", "categorie": "Bureautique", "unite_facturation": "page", "prix": 200, "consomme_stock": False},
    {"nom": "Numérisation (scan)", "categorie": "Bureautique", "unite_facturation": "page", "prix": 100, "consomme_stock": False},
    {"nom": "Envoi e-mail / transfert", "categorie": "Services annexes", "unite_facturation": "forfait", "prix": 200, "consomme_stock": False},
    {"nom": "Recherche internet", "categorie": "Services annexes", "unite_facturation": "forfait", "prix": 300, "consomme_stock": False},
]
