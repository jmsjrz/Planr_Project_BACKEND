# Fonctionnalité d'Authentification - Documentation

## OVERVIEW

Cette fonctionnalité d'authentification a été développée pour offrir un système de gestion des utilisateurs sécurisé et complet, intégrant des fonctionnalités d'inscription, de connexion, de réinitialisation de mot de passe, et de vérification OTP. Le système est conçu en utilisant Django et Django REST Framework, tout en respectant les bonnes pratiques de sécurité et de modularisation.

## STRUCTURE

Voici les principaux fichiers utilisés pour implémenter cette fonctionnalité d'authentification :

- **models.py** : Contient les modèles `User` et `PasswordResetAttempt`, qui représentent respectivement les utilisateurs et les tentatives de réinitialisation de mot de passe.
- **serializers.py** : Contient les sérialiseurs `UserSerializer` et `PasswordResetAttemptSerializer` pour convertir les objets du modèle en JSON et vice-versa.
- **views.py** : Contient le `UserViewSet` qui gère toutes les actions possibles sur les utilisateurs, comme l'inscription, la vérification OTP, la connexion, et la réinitialisation du mot de passe.
- **notifications.py** : Fichier utilitaire dédié à l'envoi de notifications, incluant l'envoi de codes OTP par e-mail et SMS, ainsi que des alertes de connexion.
- **utils.py** : Contient la fonction `generate_otp`, qui génère un code OTP et le hache pour garantir la sécurité.
- **urls.py** : Fichier qui configure les routes pour accéder aux différentes fonctionnalités liées à l'authentification.

## ENDPOINTS

Voici les endpoints disponibles pour cette fonctionnalité d'authentification :

- `POST /users/register/` : Inscription d'un utilisateur via e-mail ou numéro de téléphone.
- `POST /users/verify-otp/` : Vérification du code OTP reçu.
- `POST /users/login/` : Connexion d'un utilisateur avec e-mail et mot de passe ou numéro de téléphone.
- `POST /users/logout/` : Déconnexion d'un utilisateur en révoquant le token de rafraîchissement.
- `POST /users/request-password-reset/` : Demande de réinitialisation de mot de passe par e-mail.
- `POST /users/reset-password/<token>/` : Réinitialisation du mot de passe avec un token de réinitialisation.

## FEATURES

### 1. Inscription

- Les utilisateurs peuvent s'inscrire en utilisant soit un e-mail, soit un numéro de téléphone.
- Un mot de passe est requis pour l'inscription par e-mail.
- Un code OTP (One-Time Password) est envoyé à l'utilisateur pour vérifier l'inscription. Ce code est envoyé par e-mail ou par SMS selon la méthode choisie.

### 2. Vérification OTP

- L'utilisateur doit entrer le code OTP reçu pour activer son compte.
- Le code OTP est valide pendant 10 minutes et est sécurisé par un hachage SHA256.
- Après 3 tentatives de saisie incorrecte du code OTP, le compte est temporairement verrouillé pour 10 minutes.

### 3. Connexion

- Les utilisateurs peuvent se connecter en utilisant leur e-mail et leur mot de passe, ou leur numéro de téléphone.

- Lors de la connexion avec un numéro de téléphone, un nouveau code OTP est envoyé pour validation.

- Après 5 tentatives de connexion incorrecte, le compte est temporairement verrouillé pour 10 minutes.

- Si une connexion est effectuée depuis un nouvel appareil ou une nouvelle adresse IP, une alerte est envoyée à l'utilisateur par e-mail pour assurer la sécurité.

### 4. Réinitialisation de Mot de Passe

- Les utilisateurs peuvent demander une réinitialisation de mot de passe en fournissant leur e-mail.
- Un lien de réinitialisation est envoyé par e-mail et est valide pendant 1 heure.
- Une fois le mot de passe réinitialisé, le token de réinitialisation est invalidé.

### 5. Déconnexion

- Les utilisateurs peuvent se déconnecter en révoquant leur token de rafraîchissement JWT, ce qui empêche toute utilisation ultérieure du token.

## TECHNOLOGIES

- **Django & Django REST Framework** : Ces frameworks ont été utilisés pour gérer les utilisateurs et fournir une API RESTful. Le choix de Django est motivé par sa robustesse et sa sécurité intégrée, tandis que Django REST Framework simplifie la création d'API.
- **JWT (JSON Web Token)** : Utilisé pour l'authentification et la gestion des sessions. Les tokens de rafraîchissement permettent de prolonger les sessions utilisateur sans nécessiter une nouvelle connexion fréquente.
- **bcrypt & hashlib** : Utilisés pour le hachage des mots de passe et des OTP. `bcrypt` est utilisé pour les mots de passe des utilisateurs, offrant une sécurité renforcée, tandis que `hashlib` est utilisé pour hacher les OTP de manière plus légère.
- **Email & SMS Notifications** : Les notifications sont gérées via le module `notifications.py`, et incluent des e-mails de vérification et des alertes de sécurité.

## SÉCURITÉ

La sécurité est un aspect crucial de cette fonctionnalité d'authentification. Voici quelques mesures prises :

- **Verrouillage de Compte** : Après plusieurs tentatives incorrectes (OTP ou mot de passe), le compte est verrouillé temporairement pour empêcher des attaques par force brute.
- **Hachage des Données Sensibles** : Les mots de passe et les codes OTP sont toujours hachés avant d'être stockés, afin de garantir leur confidentialité.
- **Alerte de Connexion** : Une alerte est envoyée à l'utilisateur lorsque sa connexion est effectuée depuis un nouvel appareil ou une nouvelle adresse IP, afin de prévenir les connexions non autorisées.

## AMÉLIORATIONS ENVISAGÉES (06/10/2024)

- **Tests Unitaires** : Bien que le code soit fonctionnel, il serait bénéfique d'ajouter des tests unitaires complets, notamment pour les fonctionnalités critiques comme la vérification OTP et la réinitialisation de mot de passe.
- **Gestion des Exceptions** : Certains points pourraient être améliorés pour mieux gérer les erreurs, en particulier lors de l'envoi de notifications, afin de proposer une meilleure expérience utilisateur en cas d'échec.
- **Notifications via un Service Tiers** : Actuellement, l'envoi de SMS est simulé. En production, il serait préférable d'intégrer un service comme Twilio pour les notifications par SMS.
