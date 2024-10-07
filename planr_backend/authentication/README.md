# AUTHENTIFICATION DE L'APPLICATION BACK-END

## OVERVIEW

Ce document fournit une description complète et détaillée de la fonctionnalité d'authentification et de gestion des utilisateurs de l'application. Il inclut les fonctionnalités, le fonctionnement général, les différents endpoints disponibles, leurs paramètres, et les recommandations pour renforcer la sécurité.

## FONCTIONNALITÉS

La fonctionnalité d'authentification permet aux utilisateurs de s'inscrire, de se connecter, de vérifier leur identité via OTP (One-Time Password), et de réinitialiser leur mot de passe. Cette fonctionnalité est construite sur une API REST, sécurisée par JWT (JSON Web Token), et comprend des mesures de sécurité renforcées telles que des verrous de compte en cas de tentatives échouées répétées et des alertes de connexion suspectes.

1. **Inscription** : Enregistrement de nouveaux utilisateurs via e-mail ou numéro de téléphone.
2. **Vérification OTP** : Envoi d'un OTP (One-Time Password) pour vérifier les nouveaux utilisateurs ou réinitialiser un mot de passe.
3. **Connexion** : Authentification des utilisateurs via e-mail, numéro de téléphone et mot de passe ou OTP.
4. **Réinitialisation du mot de passe** : Envoi d'un lien de réinitialisation du mot de passe.
5. **Déconnexion** : Blacklist des tokens pour invalider les sessions en cours.
6. **Gestion des verrous et notifications** : Verrouillage temporaire des comptes après plusieurs tentatives échouées et envoi de notifications en cas de connexions suspectes.
7. **Tokens invités** : Utilisation d'un token temporaire pour les utilisateurs non vérifiés afin de permettre des opérations limitées, notamment la validation de leur compte.
8. **Renvoi automatique de l'OTP** : Lorsqu'un utilisateur se connecte sans mot de passe, c'est à dire à l'aide de son téléphone, un OTP est généré et envoyé automatiquement pour vérifier son identité.

## ENDPOINTS

| Endpoint                         | Méthode | Permission      | Description                                                                      | Paramètres                                                                                                                                     | Réponse                                                                                   |
| -------------------------------- | ------- | --------------- | -------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| `/users/register/`               | POST    | AllowAny        | Permet à un utilisateur de s'inscrire via e-mail ou numéro de téléphone          | `email` : Adresse e-mail (optionnel) `phone_number` : Numéro de téléphone (optionnel) `password` : Mot de passe (requis si `email` est fourni) | `guest_token` : Token temporaire `message` : Confirmation d'inscription et envoi d'OTP    |
| `/users/verify-otp/`             | POST    | AllowAny        | Vérifie l'identité de l'utilisateur avec un OTP                                  | Headers: `Authorization` : `Bearer {guest_token}` `otp` : Code OTP envoyé à l'utilisateur                                                      | `message` : Confirmation de vérification `refresh` : Token JWT `access` : Token JWT       |
| `/users/login/`                  | POST    | AllowAny        | Authentifie l'utilisateur par e-mail, numéro de téléphone et mot de passe ou OTP | `email` : Adresse e-mail `phone_number` : Numéro de téléphone `password` : Mot de passe (optionnel)                                            | `refresh` : Token JWT `access` : Token JWT `guest_token` : Token temporaire si OTP requis |
| `/users/resend-otp/`             | POST    | AllowAny        | Renvoyer un OTP si non validé                                                    | Headers: `Authorization` : `Bearer {guest_token}`                                                                                              | `message` : Confirmation de renvoi d'OTP                                                  |
| `/users/logout/`                 | POST    | IsAuthenticated | Déconnecte un utilisateur en blacklistant le refresh token                       | `refresh_token` : Token de rafraîchissement à blacklister                                                                                      | `message` : Confirmation de déconnexion                                                   |
| `/users/request-password-reset/` | POST    | AllowAny        | Demande de réinitialisation de mot de passe via un lien envoyé par e-mail        | `email` : Adresse e-mail de l'utilisateur                                                                                                      | `message` : Confirmation d'envoi d'e-mail de réinitialisation                             |
| `/users/reset-password/{token}/` | POST    | AllowAny        | Réinitialise le mot de passe via un lien contenant un token de réinitialisation  | `new_password` : Nouveau mot de passe                                                                                                          | `message` : Confirmation de réinitialisation du mot de passe                              |

## POINTS PARTICULIERS POUR LE FRONT-END

### Authentification

- **Inscription et Connexion** : Après l'inscription, un `guest_token` est retourné. Ce token doit être utilisé pour valider l'utilisateur en fournissant l'OTP.
- **Gestion des Tokens** : Une fois l'OTP validé, les tokens `refresh` et `access` sont générés. Il faut les stocker de manière sécurisée (par exemple, dans le stockage sécurisé du navigateur).
- **Renvoi de l'OTP** : Si un OTP expire, il faut utiliser le `guest_token` pour demander un renvoi.
- **Connexion avec OTP automatique** : Si un utilisateur se connecte sans mot de passe, un OTP est automatiquement généré et envoyé pour vérifier son identité.
- **Réinitialisation de Mot de Passe** : Après avoir demandé la réinitialisation, il faut rediriger l'utilisateur vers un formulaire pour entrer un nouveau mot de passe.

### Sécurité

- **Protection CSRF** : Toutes les requêtes sécurisées doivent utiliser un header `Authorization` contenant le `Bearer` token approprié.
- **Expiration des Tokens** : L'`access token` expire après 15 minutes. Le `refresh token` peut être utilisé pour obtenir un nouvel `access token` jusqu'à son expiration (1 jour).
- **Verrouillage du Compte** : Après plusieurs tentatives échouées (3 pour l'OTP, 5 pour la connexion), le compte sera verrouillé pendant 10 minutes.

## FLUX UTILISATEUR

### Utilisateur avec Numéro de Téléphone

1. **Inscription** : L'utilisateur s'inscrit en fournissant son numéro de téléphone. Il reçoit un `guest_token` et un OTP par SMS.
2. **Vérification OTP** : L'utilisateur utilise l'OTP reçu pour vérifier son identité. Une fois l'OTP validé, des tokens `refresh` et `access` sont générés.
3. **Connexion** : Lorsqu'il se déconnecte, l'utilisateur peut se reconnecter en demandant un nouvel OTP, qui lui est automatiquement envoyé après avoir saisi son numéro de téléphone.
4. **Renvoi d'OTP** : Si l'OTP expire, l'utilisateur peut demander un renvoi en utilisant le `guest_token`.

### Utilisateur avec E-mail

1. **Inscription** : L'utilisateur s'inscrit en fournissant son adresse e-mail et un mot de passe. Il reçoit un `guest_token` et un OTP par e-mail.
2. **Vérification OTP** : L'utilisateur saisit l'OTP pour vérifier son identité et activer son compte. Des tokens `refresh` et `access` sont générés.
3. **Connexion** : L'utilisateur se connecte en utilisant son e-mail et son mot de passe. S'il oublie son mot de passe, il peut demander une réinitialisation.
4. **Réinitialisation de Mot de Passe** : L'utilisateur reçoit un lien par e-mail pour réinitialiser son mot de passe et peut ensuite se reconnecter.

## RENFORCEMENTS ENVISAGÉS

1. **Double Facteur d'Authentification (2FA)** : Ajouter une validation 2FA avec Google Authenticator ou un service similaire.
2. **Rate Limiting** : Utiliser un mécanisme de rate limiting pour éviter les attaques par force brute sur les endpoints d'inscription, de connexion et de réinitialisation de mot de passe.
3. **Protection contre l'énumération des comptes** : Remplacer les messages d'erreur explicites par des messages génériques pour éviter l'énumération des comptes.
4. **Implémentation de Django Rate Limit en production** : Ajouter les configurations nécessaires pour le rate-limiting de Django afin de limiter le nombre de requêtes par utilisateur et renforcer la sécurité.
