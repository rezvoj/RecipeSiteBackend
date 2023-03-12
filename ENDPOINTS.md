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

## Category - /category/:

- **Create Category**: `POST /category`
    
    _Roles_: Admin, Moderator

    _Request Body_:
    ```json
    {
      "photo": <@file.jpg>,
      "name": "Category Name",
      "about": "A category." // Optional
    }
    ```

- **Update Category**: `PUT /category/<category_id>`
    
    _Roles_: Admin, Moderator

    _Request Body_:
    ```json
    {
      "photo": <@file.jpg>,
      "name": "New Category Name",
      "about": "A new category."
    }
    ```

- **Delete Category**: `DELETE /category/<category_id>`

    _Roles_: Admin, Moderator (if the category isn't listed in any recipe)

- **Toggle Category Favoured Status**: `POST /category/change-favourite/<category_id>`

    - Adds the category to user's favourites and vice versa

    _Roles_: Verified

- **Filter and Search for Categories**: `GET /category/filter/paged`

    - Filters and orders categories by criteria
    - Receive paginated response

    _Roles_: All

    _Ordering Parameters_:
    ```json
    [
      "name",
      "recipe_count",
      "self_recipe_count"
    ]
    ```
    _Query Parameters_:
    ```json
    {
      "favoured": false, // False -> All
      "search_string": "Spanish",
      "order_by": ["name", "-recipe_count"],
      "order_time_window": 7, // In days
      "page": 1,
      "page_size": 50
    }
    ```
    _Response_:
    ```json
    {
      "count": 20, // From all pages
      "page": 1,
      "page_size": 50,
      "results": [
        {
          "id": 1,
          "photo": "URL/to/photo",
          "name": "Category Name",
          "about": "This is a category.",
          "recipe_count": 20,
          "self_recipe_count": 3,
          "favoured": true
        },
        ...
      ]
    }
    ```

## Ingredient - /ingredient/:

- **Create Ingredient**: `POST /ingredient`
    
    _Roles_: Admin, Moderator

    _Request Body_:
    ```json
    {
      "photo": <@file.jpg>,
      "name": "Ingredient Name",
      "unit": "g",
      "about": "An ingredient." // Optional
    }
    ```

- **Update Ingredient**: `PUT /ingredient/<ingredient_id>`
    
    _Roles_: Admin, Moderator

    _Request Body_:
    ```json
    {
      "photo": <@file.jpg>,
      "name": "Ingredient New Name",
      "unit": "Kg",
      "about": "A new ingredient."
    }
    ```

- **Delete Ingredient**: `DELETE /ingredient/<ingredient_id>`
    
    _Roles_: Admin, Moderator (if the ingredient isn't used in any recipe)

- **Add Ingredient to Inventory**: `POST /ingredient/inventory/<ingredient_id>`

    - Adds, adds amount, subtracts amount or removes ingredient from user's inventory
    - Inventory is for searching recipes user has sufficient ingredients for

    _Roles_: Verified

    _Request Body_:
    ```json
    {
      "amount": 10.50
    }
    ```

- **Remove Ingredient from Inventory**: `DELETE /ingredient/inventory/<ingredient_id>`
    
    - Remove ingredient completely from user's inventory

    _Roles_: Verified

- **Filter and Search for Ingredients**: `GET /ingredient/filter/paged`

    - Filters and orders ingredients by criteria
    - Receive paginated response

    _Roles_: All

    _Ordering Parameters_:
    ```json
    [
      "name", 
      "recipe_count", 
      "self_recipe_count"
    ]
    ```
    _Query Parameters_:
    ```json
    {
      "owned": false, // False -> All
      "used": true, // False -> All
      "search_string": "Red Tomato",
      "order_by": ["-self_recipe_count", "name"],
      "order_time_window": 7, // In days
      "page": 1,
      "page_size": 50
    }
    ```
    _Response_:
    ```json
    {
      "count": 43, // From all pages
      "page": 1,
      "page_size": 50,
      "results": [
        {
          "id": 1,
          "photo": "URL/to/photo",
          "name": "Ingredient Name",
          "unit": "Kg",
          "about": "An ingredient.",
          "self_recipe_count": 5,
          "recipe_count": 20,
          "self_amount": 1.50
        },
        ...
      ]
    }
    ```

## Recipe - /recipe/:

- **Create Recipe**: `POST /recipe`

    _Roles_: Verified

    _Request Body_:
    ```json
    {
      "categories": [1, 2], // List of IDs
      "name": "Recipe Name",
      "title": "Recipe Title",
      "prep_time": 30,
      "calories": 1350,
    }
    ```

- **Update Recipe**: `PUT /recipe/<recipe_id>`
    
    _Roles_: Verified (creator of the recipe)

    _Request Body_:
    ```json
    {
      "categories": [2, 3], // List of IDs
      "name": "Recipe New Name",
      "title": "Recipe New Title",
      "prep_time": 25,
      "calories": 1500,
    }
    ```

- **Delete Recipe**: `DELETE /recipe/<recipe_id>`

    _Roles_: Verified (creator of the recipe)

- **Add Recipe Photo**: `POST /recipe/photo/<recipe_id>`

    _Roles_: Verified (creator of the recipe)

    _Request Body_:
    ```json
    {
      "photo": <@file.jpg>,
      "number": 1,
    }
    ```

- **Update Recipe Photo**: `PUT /recipe/photo/<photo_id>`
    
    _Roles_: Verified (creator of the recipe)

    _Request Body_:
    ```json
    {
      "photo": <@file.jpg>,
      "number": 2,
    }
    ```

- **Remove Recipe Photo**: `DELETE /recipe/photo/<photo_id>`

    _Roles_: Verified (creator of the recipe)

- **Add Recipe Instruction**: `POST /recipe/photo/<recipe_id>`

    _Roles_: Verified (creator of the recipe)

    _Request Body_:
    ```json
    {
      "photo": <@file.jpg>,
      "number": 1,
      "title": "Instruction Title", 
      "content": "Instruction Content"
    }
    ```

- **Update Recipe Instruction**: `PUT /recipe/instruction/<instruction_id>`

    _Roles_: Verified (creator of the recipe)

    _Request Body_:
    ```json
    {
      "photo": <@file.jpg>,
      "number": 2,
      "title": "New Instruction Title", 
      "content": "New Instruction Content"
    }
    ```

- **Remove Recipe Instruction**: `DELETE /recipe/instruction/<instruction_id>`

    _Roles_: Verified (creator of the recipe)

- **Add Ingredient to Recipe**: `POST /recipe/ingredient/<recipe_id>/<ingredient_id>`

    - Adds, adds amount, subtracts amount or removes ingredient from recipe

    _Roles_: Verified (creator of the recipe)

    _Request Body_:
    ```json
    {
      "amount": 10.50
    }
    ```

- **Remove Ingredient from Recipe**: `DELETE /recipe/ingredient/<recipe_id>/<ingredient_id>`

    - Remove ingredient completely from recipe

    _Roles_: Verified (creator of the recipe)

- **Submit Recipe**: `PUT /recipe/submit/<recipe_id>`

    - Checks if needed instruction etc. are present and recipe is unsubmitted
    - Submits recipe to be accepted or denied by moderators
    - If submitted by moderator then gets automatically accepted

    _Roles_: Verified (creator of the recipe)

- **Accept Recipe Submission**: `PUT /recipe/accept/<recipe_id>`

    - Makes recipe publicly visible 

    _Roles_: Admin, Moderator

- **Deny Recipe Submission**: `PUT /recipe/deny/<recipe_id>`

    - Removes recipe from submitted to be edited

    _Roles_: Admin, Moderator

- **"Cook" Recipe**: `POST /recipe/cook/<recipe_id>`
    
    - Removes amount of ingredients needed to cook the recipe from the user's ingredient inventory

    _Roles_: Verified

    _Request Body_:
    ```json
    {
      "servings": 3 // Optional
    }
    ```

- **Toggle Recipe Favoured Status**: `POST /recipe/change-favourite/<recipe_id>`
    
    - Adds the recipe to user's favourites and vice versa

    _Roles_: Verified

- **Get Recipe Detail**: `GET /recipe/detail/<recipe_id>`

    - Receive detail of visible recipe

    _Roles_: All

    _Response_:
    ```json
    {
      "id": 2,
      "submit_status": 1,
      "deny_message": null,
      "user": {
        "id": 1,
        "photo": "URL/to/photo",
        "name": "Jane",
        "created_at": "2023-03-11T00:00:00Z",
      },
      "name": "Recipe Name",
      "title": "Recipe Title",
      "prep_time": 25,
      "calories": 1240,
      "created_at": "2023-07-11T00:00:00Z",
      "rating_count": 1355,
      "avg_rating": 3.24,
      "favoured": false,
      "photo": "URL/to/photo",
      "cookable_portions": 3,
      "favoured_count": 124,
      "categories": [
        {
          "id": 1,
          "photo": "URL/to/photo",
          "name": "Italian",
        },
        ...
      ],
      "ingredients": [
        {
          "ingredient": {
            "id": 2,
            "photo": ,
            "unit": "Kg",
            "name": "Tomatoes"
          },
          "amount": 10.50
        },
        ...
      ],
      "photos": [
        {
          "id": 1,
          "photo": "URL/to/photo"
        },
        ...
      ],
      "instructions": [
        {
          "id": 1,
          "photo": "URL/to/photo",
          "title": "Title of instruction",
          "content": "Content of instruction"
        },
        ...
      ],
    }
    ```

- **Filter and Search for Recipes**: `GET /recipe/filter/paged`

    - Filters and orders visible recipes by criteria
    - Receive paginated response

    _Roles_: All

    _Ordering Parameters_:
    ```json
    [
      "name", 
      "rating_count", 
      "avg_rating", 
      "prep_time", 
      "calories", 
      "created_at"
    ]
    ```
    _Query Parameters_:
    ```json
    {
      "categories": [1, 4, 65, 221], // List IDs, has to have all
      "user": 234,
      "calories_limit": 112,
      "servings": 12, // For calories_limit and sufficient_ingredients
      "prep_time_limit": 30,
      "favourite_category": false, // False -> All
      "sufficient_ingredients": false, // False -> All, inventory items
      "favoured": true, // False -> All
      "search_string": "Italian Pizza",
      "order_by": ["name", "-created_at"],
      "order_time_window": 7, // In days
      "page": 1,
      "page_size": 25
    }
    ```
    _Response_:
    ```json
    {
      "count": 50, // From all pages
      "page": 1,
      "page_size": 25,
      "results": [
        {
          "id": 2,
          "submit_status": 1,
          "deny_message": null,
          "user": {
            "id": 1,
            "photo": "URL/to/photo",
            "name": "Jane",
            "created_at": "2023-03-11T00:00:00Z",
          },
          "name": "Recipe Name",
          "title": "Recipe Title",
          "prep_time": 25,
          "calories": 1240,
          "created_at": "2023-07-11T00:00:00Z",
          "rating_count": 1355,
          "avg_rating": 3.24,
          "favoured": false,
          "photo": "URL/to/photo",
        },
        ...
      ]
    }
    ```
