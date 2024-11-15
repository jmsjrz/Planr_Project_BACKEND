# Planr Backend

## Introduction

Welcome to the Planr Backend, the backbone of the social event management platform designed for individuals and professionals. This Django-based backend manages user profiles, events, and provides APIs for features like event recommendations, real-time updates, and secure user authentication.

Read more about the development journey of Planr in our final **[project blog article](https://medium.com/@8708/43b05f073db8)**.
**Author:** [James Jarosz on LinkedIn](https://www.linkedin.com/in/james-jarosz-fr/)

## Installation

To set up the project locally, follow these steps:

1. Clone the repository:

   ```bash
   git clone https://github.com/jamesjarosz/planr_backend.git
   ```

2. Navigate to the project directory:

   ```bash
   cd planr_backend
   ```

3. Create a virtual environment:

   ```bash
   python3 -m venv venv
   ```

4. Activate the virtual environment:

   ```bash
   source venv/bin/activate
   ```

5. Install dependencies from `venv_packages.txt`:

   ```bash
   pip install -r venv_packages.txt
   ```

6. Create an `.env` file with the required environment variables:

   ```bash
   touch .env
   ```

   Example `.env` file:

   ```env
   DB_NAME=
   DB_USER=
   DB_PASSWORD=
   DB_HOST=
   DB_PORT=
   SECRET_KEY=
   DEBUG=True  # ou False en production
   BASE_URL=http://localhost:8000
   FRONTEND_URL=http://localhost:5173
   ```

1) Apply migrations:

   ```bash
   python3 manage.py migrate
   ```

2) Start the development server:

   ```bash
   python3 manage.py runserver
   ```

The application will be accessible at `http://127.0.0.1:8000`.

## Usage

- This backend provides RESTful APIs for managing user profiles, events, and registrations.
- It also includes functionalities for user authentication, event registration, wishlist management, and location-based features using Google Maps.

## Contributing

We welcome contributions! Please follow these steps to contribute:

1. Fork the repository.
2. Create a new branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. Commit your changes:
   ```bash
   git commit -m "Add your message here"
   ```
4. Push to the branch:
   ```bash
   git push origin feature/your-feature-name
   ```
5. Create a Pull Request.

## Related Projects

- [Planr Frontend](https://github.com/jamesjarosz/planr_frontend)
- [Planr Blog](https://medium.com/@8708/43b05f073db8)

## Licensing

This project is not curently under any licensing.
