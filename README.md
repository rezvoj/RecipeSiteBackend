# Recipe Site Backend in Django Rest Framework

![License](https://img.shields.io/badge/license-MIT-blue.svg) ![Python Version](https://img.shields.io/badge/python-3.11-blue)


## Table of Contents

- [Introduction](#introduction)
- [Dependencies](#dependencies)
- [Installation](#installation)
- [Roles](#roles)
- [Endpoints](#endpoints)
- [Error Codes](#error-codes)
- [Usage](#usage)
- [License](#license)


## Introduction

This project is a REST API for a food recipe content-based site. It offers authentication and email verification, content publishing and moderation, various features such as managing your ingredient inventory, advanced searching and filtering (e.g., searching for recipes that the user has sufficient quantities of ingredients for), and other functionalities.


## Dependencies

Ensure you're using Python version 3.11 or higher.

Install the required dependencies with:
```bash
pip install -r requirements.txt
```

Dependencies used:
- Django
- Django Rest Framework
- PyJWT
- Pillow


## Installation

To get the project started, follow the steps below:

1. Clone the repository and navigate to the project directory:
    ```bash
    git clone https://github.com/rezvoj/RecipeSiteBackend.git
    cd RecipeSiteBackend
    ```

2. *(Optional)* Run the tests:
    ```bash
    python manage.py test
    ```

3. Configure the application's database, media backend and other stuff in [**`settings.py`**](recipeAPI/settings.py) and [**`apps.py`**](recipeAPIapp/apps.py).

4. If you choose to continue with the default local setup for media and database, you will need to create `media` and `database` directories in the base directory:
    ```bash
    mkdir media
    mkdir database
    ```

5. Set up database schema:
    ```bash
    python manage.py migrate recipeAPIapp
    ```

6. Ensure all necessary environmental variables like `APP_SECRET_KEY` and `APP_ADMIN_CODE` are set.

7. Run the development server (for local testing and development):
    ```bash
    python manage.py runserver $PORT_NUMBER
    ```

8. Run the application in a production environment (using Gunicorn as a WSGI server):
    ```bash
    gunicorn --workers 3 --bind 0.0.0.0:$PORT_NUMBER recipeAPI.wsgi:application
    ```


## Roles

- **Anon**: Jwt user token invalid or not provided in authorization header.
- **User**: Valid jwt user token provided in authorization header.
- **Verified**: User that has successfully verified his email address.
- **Moderator**: User that has been named moderator by administrator
- **Admin**: Valid 'ADMINCODE' authorization header mathing the one in [**`settings.py`**](recipeAPI/settings.py).


## Endpoints

- **Endpoints**: The API provides a variety of endpoints. For detailed information about each endpoint, please refer to the [ENDPOINTS](ENDPOINTS.md) file.

- **Media Serving**: When using the default local media storage settings, media files are served with the `/media/` URL prefix.

- **Date and Time Handling**: All datetime values returned by the API are in UTC. Any datetime values received by the API are also expected to be in UTC.


## Error Codes

Error codes and messages returned by the API.

- **Http 400 Bad Request**:

    - Any type of invalid data in request body or query parameters

    _Response_:
    ```json
    {
      "detail": {
        "name": ["has to be longer then 3 characters."],
        "non_field_errors": ["invalid email or password."],
        ...
      }
    }
    ```
    
    - User has reached the limit for creating certain content

    _Response_:
    ```json
    {
      "detail": {
        "limit": 10, 
        "hours": 1
      }
    }
    ```

- **Http 401 Unauthorized**:

    - User does not have permission to access this endpoint 

- **Http 403 Forbidden**:

    - User has been banned by admin or moderator 

    _Response_:
    ```json
    {
      "detail": "You have been banned."
    }
    ```

- **Http 404 Not Found**:

    - Object referenced by path id does not exist, or user does not have rights for it


## Usage

Examples on how to use the API.

### Requesting Details for Recipe

```bash
curl -X GET http://localhost:8080/recipe/detail/23 \ 
    -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Creating Rating for Recipe

```bash
curl -X POST http://localhost:8080/rating/3 \ 
    -H "Authorization: Bearer YOUR_JWT_TOKEN" \ 
    -F "photo=@path/to/file.jpg" \ 
    -F "stars=5" \ 
    -F "content=I really liked this."
```


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
