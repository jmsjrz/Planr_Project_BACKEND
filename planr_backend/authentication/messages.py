class ErrorMessages:
    # Erreurs liées à l'inscription et la gestion des utilisateurs
    EMAIL_ALREADY_EXISTS = "Cet e-mail est déjà utilisé."
    PHONE_ALREADY_EXISTS = "Ce numéro de téléphone est déjà utilisé."
    EMAIL_OR_PHONE_REQUIRED = "Un e-mail ou un numéro de téléphone est requis."
    PASSWORD_REQUIRED = "Un mot de passe est requis pour l'inscription par e-mail."
    PASSWORD_TOO_WEAK = "Le mot de passe est trop faible. Il doit contenir au moins 8 caractères, avec des lettres et des chiffres."
    
    # OTP (One-Time Password)
    OTP_EXPIRED = "Votre code OTP a expiré."
    OTP_INVALID = "Le code OTP est invalide."
    OTP_RESEND_LIMIT = "Vous devez attendre avant de renvoyer un autre OTP."
    OTP_MAX_ATTEMPTS = "Vous avez atteint le nombre maximum de tentatives OTP. Compte verrouillé temporairement."
    
    # Connexion et verrouillage de compte
    INVALID_CREDENTIALS = "Les informations d'identification sont incorrectes."
    ACCOUNT_LOCKED = "Le compte est verrouillé après plusieurs tentatives échouées."
    USER_NOT_FOUND = "Utilisateur non trouvé."
    USER_INACTIVE = "Le compte utilisateur est inactif, vérification OTP requise."
    PASSWORD_MISMATCH = "Mot de passe incorrect."
    LOGIN_REQUIRED = "Un e-mail ou un numéro de téléphone est requis pour se connecter."
    UNAUTHORIZED_ACCESS = "Accès non autorisé."
    SESSION_EXPIRED = "Session expirée. Veuillez vous reconnecter."
    
    # Réinitialisation du mot de passe
    RESET_TOKEN_INVALID = "Le jeton de réinitialisation est invalide ou expiré."
    PASSWORD_RESET_FAILED = "Échec de la réinitialisation du mot de passe. Le jeton est invalide ou expiré."
    RESET_LIMIT_REACHED = "Une demande de réinitialisation a déjà été faite récemment. Patientez 15 minutes."

    # Tokens et autorisation
    JWT_REQUIRED = "Le token JWT est requis."
    TOKEN_INVALID = "Le jeton JWT est invalide ou a expiré."

    # Validation des formats d'email et de téléphone
    EMAIL_FORMAT_INVALID = "Le format de l'adresse e-mail est invalide."
    PHONE_FORMAT_INVALID = "Le format du numéro de téléphone est invalide."

    # Autres erreurs générales
    TOO_MANY_REQUESTS = "Trop de tentatives. Veuillez attendre et réessayer."
    INTERNAL_SERVER_ERROR = "Une erreur interne est survenue. Veuillez réessayer plus tard."
    ACTION_NOT_ALLOWED = "Cette action n'est pas autorisée."

class SuccessMessages:
    # Succès liés à l'inscription et la gestion des utilisateurs
    REGISTRATION_SUCCESS = "Inscription réussie. Un OTP a été envoyé pour vérification."
    
    # Succès liés à la connexion et à la déconnexion
    LOGIN_SUCCESS = "Connexion réussie."
    LOGOUT_SUCCESS = "Déconnexion réussie."

    # OTP (One-Time Password)
    OTP_SENT = "Un OTP a été envoyé pour vérification."
    OTP_VERIFICATION_SUCCESS = "Vérification de l'OTP réussie. Compte activé."
    OTP_RESEND_SUCCESS = "Un nouvel OTP a été envoyé."

    # Réinitialisation du mot de passe
    PASSWORD_RESET_EMAIL_SENT = "Un e-mail de réinitialisation a été envoyé."
    PASSWORD_RESET_SUCCESS = "Mot de passe réinitialisé avec succès."

    # Autres succès généraux
    PASSWORD_UPDATE_SUCCESS = "Mot de passe mis à jour avec succès."
    REQUEST_PROCESSED = "Votre demande a été traitée avec succès."
    DATA_SAVED = "Les données ont été enregistrées avec succès."
