## User - /user/:

- **Register**: `POST /user`
    
    - Registration of new user account
    - Sends verification email
    - Receive new jwt token

    _Roles_: All

    _Request Body_:
    ```json
    {
      "photo": <@file.jpg>, // Optional
      "email": "user@email.com",
      "name": "User Name",
      "about": "Brief about the user", // Optional
      "password": "securEp4ssword23",
    }
    ```
    _Response_:
    ```json
    {
      "token": "generated_jwt_token"
    }
    ```

- **Update User's Basic Details**: `PUT /user`
    
    - Updates profile details
    
    _Roles_: User, Verified, Moderator

    _Request Body_:
    ```json
    {
      "name": "New Name",
      "about": "Updated about me.",
      "photo": <@file.jpg>
    }
    ```

- **Delete User Account**: `DELETE /user`
    
    - Deletes account
    - Deletes associated content 
    
    _Roles_: User, Verified, Moderator

- **Toggle User's Moderator Status**: `PUT /user/change-moderator/<user_id>`
    
    - Changes regular user to moderator and vice versa
    
    _Roles_: Admin

- **Report User**: `POST /user/report/<user_id>`
    
    - Reports specified user

    _Roles_: User, Verified, Moderator

- **Ban User**: `POST /user/ban/<user_id>`
    
    - Disables user account
    - Deletes associated content
    
    _Roles_: Admin, Moderator (if user is not moderator)

- **Dismiss User Reports**: `DELETE /user/dismiss-reports/<user_id>`
    
    - Dismisses reports for user

    _Roles_: Admin, Moderator (if user is not moderator)

- **Get User's Details**: `GET /user/detail/<user_id>`

    _Roles_: All

    _Response_:
    ```json
    {
      "id": 1,
      "photo": "URL/to/photo",
      "name": "Jane",
      "created_at": "2023-03-11T00:00:00Z",
      "about": "I love baking.",
      "rating_count": 3, // Written by
      "recipe_count": 5,
      "avg_rating": 3.53, // Written by
      // If role is Admin or Moderator:
      "email": "Jane321@examplemail.com",
      "moderator": true,
      "report_count": 3
    }
    ```

- **Get Logged-In User's Details**: `GET /user/self-detail`
    
    _Roles_: User, Verified, Moderator

    _Response_:
    ```json
    {
      "id": 2,
      "photo": "URL/to/photo",
      "name": "John",
      "created_at": "2022-01-12T00:01:32Z",
      "about": null,
      "rating_count": 3, // Written by
      "recipe_count": 2,
      "avg_rating": 4.22, // Written by
      "email": "John321@examplemail.com",
      "moderator": false,
      "verified": true
    }
    ```

- **Filter and Search Users**: `GET /user/filter/paged`
    
    - Filters and orders users by criteria
    - Receive paginated response

    _Roles_: All

    _Ordering Parameters_:
    ```json
    [
      "name", 
      "recipe_count", 
      "avg_rating", // Written by
      // If role is Admin or Moderator:
      "report_count"
    ]
    ```
    _Query Parameters_:
    ```json
    {
      "search_string": "Michael",
      "order_by": ["-recipe_count", "name"],
      "order_time_window": 7, // In days
      "page": 1,
      "page_size": 10,
      // If role is Admin:
      "moderator": true
    }
    ```
    _Response_:
    ```json
    {
      "count": 20, // From all pages
      "page": 1,
      "page_size": 25,
      "results": [
        {
          "id": 1,
          "photo": "URL/to/photo",
          "name": "Jane",
          "created_at": "2023-03-11T00:00:00Z",
          "rating_count": 3, // Written by
          "recipe_count": 5,
          "avg_rating": 3.53, // Written by
          // If role is Admin or Moderator:
          "moderator": true,
          "report_count": 3
        },
        ...
      ]
    }
    ```

## Authentication - /auth/:

- **Regenerate JWT Token**: `POST /auth/token`
    
    - Receive new jwt token

    _Roles_: User, Verified, Moderator
    
    _Response_:
    ```json
    {
      "token": "generated_jwt_token"
    }
    ```

- **Login**: `POST /auth/login`

    - Receive new jwt token

    _Roles_: All

    _Request Body_:
    ```json
    {
      "email": "John323@examplemail.com",
      "password": "securEp4ssword645"
    }
    ```
    _Response_:
    ```json
    {
      "token": "generated_jwt_token"
    }
    ```

- **Update Authentication Details**: `PUT /auth/update`
    
    - Updates password and (or) email
    - Invalidates old tokens
    - If email is updated resends verification email
    - Receive new jwt token

    _Roles_: User, Verified, Moderator

    _Request Body_:
    ```json
    {
      "password": "P4ssword5325",
      // At least one must be provided:
      "new_password": "newP4ssword5325",
      "email": "newemail@example.com"
    }
    ```
    _Response_:
    ```json
    {
      "token": "generated_jwt_token"
    }
    ```

- **Send Email Verification**: `POST /auth/email-verification`
    
    - Resends verification email with link to verify email
    
    _Roles_: User, Verified, Moderator

- **Verify Email**: `PUT /auth/email-verification/<code>`
    
    - Confirms email using the verification code
    
    _Roles_: User, Verified, Moderator

- **Send Password Reset Email**: `POST /auth/password-reset`
    
    - Sends email with link to reset password

    _Roles_: All

    _Request Body_:
    ```json
    {
      "email": "John@examplemail.com"
    }
    ```

- **Check Password Reset Code**: `GET /auth/password-reset/<user_id>/<code>`

    - Checks if the provided password reset code is valid

    _Roles_: All

- **Reset Password**: `PUT /auth/password-reset/<user_id>/<code>`
    
    - Updates password
    - Invalidates old tokens
    - Receive new jwt token

    _Roles_: All

    _Request Body_:
    ```json
    {
      "password": "newP4ssword424",
    }
    ```
    _Response_:
    ```json
    {
      "token": "generated_jwt_token"
    }
    ```
