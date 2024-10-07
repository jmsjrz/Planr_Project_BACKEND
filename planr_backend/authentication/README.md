# Authentification & Gestion des Utilisateurs

## OVERVIEW

Ce document fournit une description complète et détaillée de la fonctionnalité d'authentification et de gestion des utilisateurs de l'application. Il inclut les fonctionnalités, le fonctionnement général, les différents endpoints disponibles, leurs paramètres, et les recommandations pour renforcer la sécurité.

## Fonctionnalité

La fonctionnalité d'authentification permet aux utilisateurs de s'inscrire, de se connecter, de vérifier leur identité via OTP (One-Time Password), et de réinitialiser leur mot de passe. Cette fonctionnalité est construite sur une API REST, sécurisée par JWT (JSON Web Token), et comprend des mesures de sécurité renforcées telles que des verrous de compte en cas de tentatives échouées répétées et des alertes de connexion suspectes.

1. **Inscription** : Enregistrement de nouveaux utilisateurs via e-mail ou numéro de téléphone.
2. **Vérification OTP** : Envoi d'un OTP (One-Time Password) pour vérifier les nouveaux utilisateurs ou réinitialiser un mot de passe.
3. **Connexion** : Authentification des utilisateurs via e-mail et mot de passe.
4. **Réinitialisation du mot de passe** : Envoi d'un lien de réinitialisation du mot de passe.
5. **Déconnexion** : Blacklist des tokens pour invalider les sessions en cours.
6. **Gestion des Verrous** : Verrouillage temporaire des comptes après plusieurs tentatives échouées.
7. **Tokens Invités** : Utilisation d'un token temporaire pour les utilisateurs non vérifiés afin de permettre des opérations limitées, notamment la validation de son compte.

## ENDPOINTS DISPONIBLES

| Endpoint                         | Méthode | Permission      | Description                                                                     | Paramètres                                                                                                                                               | Réponse                                                                                       |
| -------------------------------- | ------- | --------------- | ------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| `/users/register/`               | POST    | AllowAny        | Permet à un utilisateur de s'inscrire via e-mail ou numéro de téléphone         | `email` : Adresse e-mail (optionnel) <br> `phone_number` : Numéro de téléphone (optionnel) <br> `password` : Mot de passe (requis si `email` est fourni) | `guest_token` : Token temporaire <br> `message` : Confirmation d'inscription et envoi d'OTP   |
| `/users/verify-otp/`             | POST    | AllowAny        | Vérifie l'identité de l'utilisateur avec un OTP                                 | Headers: `Authorization` : `Bearer {guest_token}` <br> `otp` : Code OTP envoyé à l'utilisateur                                                           | `message` : Confirmation de vérification <br> `refresh` : Token JWT <br> `access` : Token JWT |
| `/users/login/`                  | POST    | AllowAny        | Authentifie l'utilisateur par e-mail et mot de passe                            | `email` : Adresse e-mail <br> `password` : Mot de passe                                                                                                  | `refresh` : Token JWT <br> `access` : Token JWT                                               |
| `/users/resend-otp/`             | POST    | AllowAny        | Renvoyer un OTP si non validé                                                   | Headers: `Authorization` : `Bearer {guest_token}`                                                                                                        | `message` : Confirmation de renvoi d'OTP                                                      |
| `/users/logout/`                 | POST    | IsAuthenticated | Déconnecte un utilisateur en blacklistant le refresh token                      | `refresh_token` : Token de rafraîchissement à blacklister                                                                                                | `message` : Confirmation de déconnexion                                                       |
| `/users/request-password-reset/` | POST    | AllowAny        | Demande de réinitialisation de mot de passe via un lien envoyé par e-mail       | `email` : Adresse e-mail de l'utilisateur                                                                                                                | `message` : Confirmation d'envoi d'e-mail de réinitialisation                                 |
| `/users/reset-password/{token}/` | POST    | AllowAny        | Réinitialise le mot de passe via un lien contenant un token de réinitialisation | `new_password` : Nouveau mot de passe                                                                                                                    | `message` : Confirmation de réinitialisation du mot de passe                                  |

## POINTS PARTICULIER POUR L'INTÉGRATION FRONT-END

### AUTHENTIFICATION

- **Inscription et Connexion** : Après l'inscription, un `guest_token` est retourné. Ce token doit être utilisé pour valider l'utilisateur en fournissant l'OTP.
- **Gestion des Tokens** : Une fois l'OTP validé, les tokens `refresh` et `access` sont générés. Il faut les stocker de manière sécurisée (par exemple, dans le stockage sécurisé du navigateur).
- **Renvoi de l'OTP** : Si un OTP expire, il faut utiliser le `guest_token` pour demander un renvoi.
- **Réinitialisation de Mot de Passe** : Après avoir demandé la réinitialisation, il faut rediriger l'utilisateur vers un formulaire pour entrer un nouveau mot de passe.

### SÉCURITÉ

- **Protection CSRF** : Toutes les requêtes sécurisées doivent utilisent un header `Authorization` contenant le `Bearer` token approprié.
- **Expiration des Tokens** : L'`access token` expire après 15 minutes. Le `refresh token` peut être utilisé pour obtenir un nouvel `access token` jusqu'à son expiration (1 jour).
- **Verrouillage du Compte** : Après plusieurs tentatives échouées (3 pour l'OTP, 5 pour la connexion), le compte sera verrouillé pendant 10 minutes.

## RENFORCEMENTS ENVISAGEABLES

1. **Double Facteur d'Authentification (2FA)** : Ajouter une validation 2FA avec Google Authenticator ou en envoyant un second OTP.
2. **Rate Limiting** : Utiliser un mécanisme de rate limiting pour éviter les attaques par force brute sur les endpoints d'inscription, de connexion et de réinitialisation de mot de passe.
3. **Sessions Concurrentes** : Empêcher la connexion simultanée depuis plusieurs appareils en limitant à une session active par utilisateur.
4. **Validation de Lieu et d'Appareil** : Notifier les utilisateurs lorsque de nouvelles connexions sont détectées à partir de nouveaux lieux ou appareils.
5. **Protocole OAuth2/OpenID Connect** : Pour une authentification centralisée, envisager l'implémentation d'OAuth2 ou OpenID Connect.
6. **Audit et Journaux d'Accès** : Enregistrer les tentatives de connexion, les réinitialisations de mot de passe, et les connexions depuis des IP ou appareils non reconnus.
7. **Protection contre l'énumération des comptes** : Remplacer les messages d'erreur explicites par des messages génériques pour éviter l'énumération des comptes.
8. **Implémentation de Django Rate Limit en production** : Ajouter les configurations nécessaires pour le rate-limiting de Django afin de limiter le nombre de requêtes par utilisateur et renforcer la sécurité.
