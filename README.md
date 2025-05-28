# Auth Service

## 🌟 Overview

![image-scenario](./assets/scenario.png)

The **Auth Service** is a microservice responsible for handling user authentication, authorization, and role-based access control (RBAC) in a distributed system. It provides a centralized solution for user management, token-based authentication using JSON Web Tokens (JWT), and access control for multiple API services. The service supports user sign-up, sign-in, sign-out, multi-factor authentication (MFA), and token revocation, ensuring secure access to protected resources.

### 🏗️ Architecture
The system consists of three main components:
- **Frontend (A)**: The client application where users log in, sign up, or access protected resources.
- **Auth Service**: The core service that manages authentication, issues JWTs, and enforces RBAC.
- **API Services (B)**: Backend services that provide protected resources, accessible using JWTs issued by the Auth Service. These services verify the JWTs via `POST /api/v1/auth/verify-token` endpoint to check user access and roles.

### 🚀 Usage Scenario
1. A user logs in via the frontend by sending credentials to the Auth Service.
2. The Auth Service validates the credentials and issues a JWT containing the user’s details and a list of accessible services with their roles.
3. The frontend sends the JWT to an API Service to access a protected resource.
4. The API Services verifies the JWT using a `POST /api/v1/auth/verify-token` endpoint by give passing token jwt from the frontend and the service UUID.
   - The Auth Service checks the token's validity, expiration, and revocation status.
   - It also verifies if the user has access to the requested service and role.
   - The Auth Service returns the user details and service access information.
5. If the token is valid and the user has access, the API Service grants the request; otherwise, it denies it.
6. Revoked tokens (e.g., after sign-out) are stored in Redis, accessible to all services for blacklist checks.

## Development 🧑‍💻

#### Prerequisites

- Docker and Docker Compose for containerized development.
- uv installed for dependency management.

#### Running the Service

1. Clone the repository:
2. Running the service:
    ```bash
    make up
    ```
3. Running the migrations:
    ```bash
    make exec
    # loc: /code/src
    alembic upgrade head
    ```

#### Project Structure
```bash
├── src/                    # Main code lives here! ❤️
│   ├── alembic.ini             # 🛠️ Config for database migrations.
│   ├── app/                    # 🚀 FastAPI app code—your API!
│   ├── frontend/               # 🌐 Frontend files (if any). [Not used yet]
│   ├── migrations/             # 📜 Database migration scripts.
│   ├── tests/                  # ✅ Tests using pytest.
│   └── worker/                 # ⚙️ Background task code. [Not used yet]
├── assets/                 # Static files like images.
├── README.md               # 📖 Project info and guide.
├── Dockerfile              # 🐳 Builds the app’s Docker image.
├── Dockerfile.dev          # 🐳 Docker setup for development.
├── docker-compose.yaml     # 🎻  Runs multiple services together.
├── Makefile                # 📋 Shortcuts for common tasks.
├── pyproject.toml          # 🐍 Python tool and dependency config.
├── ruff.toml               # 🧹 Linter settings for clean code.
└── uv.lock                 # 🔒 Locks dependency versions.
```

## Features

### Authentication 🔑
- `POST /api/v1/auth/sign-up`: Register a new user.
- `POST /api/v1/auth/sign-in`: Authenticate a user and issue a JWT.
- `DELETE /api/v1/auth/sign-out`: Invalidate a user’s session (sign out) and add the token to a Redis blacklist.
- `POST /api/v1/auth/verify-mfa`: Verify multi-factor authentication codes.
- `POST /api/v1/auth/refresh`: Refresh an expired JWT using a refresh token.
- `POST /api/v1/auth/verify-token`: Verify a JWT and check its validity.
- `POST /api/v1/auth/forgot-password`: Initiate the password reset process.
- `POST /api/v1/auth/reset-password`: Reset a user’s password using a reset token.
- `GET /api/v1/auth/reset-password` : Provide a page for resetting the password (e.g., a link to the frontend).

### User Management (Admin) 👤
- `GET /api/v1/admin/users`: Retrieve a list of all users (admin only).
- `GET /api/v1/admin/users/{user_uuid}`: Get details of a specific user (admin only).
- `PUT /api/v1/admin/users/{user_uuid}`: Update a user's details (admin only).
- `DELETE /api/v1/admin/users/{user_uuid}`: Delete a user (admin only).
- `PUT /api/v1/admin/users/{user_uuid}/services`: Update service mappings for a user, replacing all existing mappings (admin only).

### Member Profile Management 🧑‍💻
- `GET /api/v1/me`: Retrieve the authenticated user’s details.
- `PUT /api/v1/me`: Update the authenticated user’s profile.
- `PUT /api/v1/me/password`: Update the user’s password.
- `PUT /api/v1/me/mfa`: Enable or update MFA settings.
- `GET /api/v1/me/mfa/qrcode`: Generate a QR code for MFA setup.

### Role Management 🎭
- `GET /api/v1/roles`: Retrieve all roles (admin only).
- `POST /api/v1/roles`: Create a new role (admin only).
- `GET /api/v1/roles/{role_id}`: Get details of a specific role (admin only).
- `PUT /api/v1/roles/{role_id}`: Update a role (admin only).
- `DELETE /api/v1/roles/{role_id}`: Delete a role (admin only).

### Business Role Management 💼
- `GET /api/v1/business-roles`: Retrieve all business roles with pagination (admin only).
- `POST /api/v1/business-roles`: Create a new business role (admin only).
- `GET /api/v1/business-roles/{business_role_id}`: Get details of a specific business role (admin only).
- `PUT /api/v1/business-roles/{business_role_id}`: Update a business role (admin only).
- `DELETE /api/v1/business-roles/{business_role_id}`: Delete a business role (admin only).

### Service Management 🛠️
- `GET /api/v1/services`: Retrieve all services (admin only).
- `POST /api/v1/services`: Create a new service (admin only).
- `GET /api/v1/services/{service_uuid}`: Get details of a specific service (admin only).
- `PUT /api/v1/services/{service_uuid}`: Update a service (admin only).
- `DELETE /api/v1/services/{service_uuid}`: Delete a service (admin only).

## Security Features
- **JWT Authentication**: Uses JSON Web Tokens for stateless authentication, signed with a shared secret.
- **Rate-Limiting**: All API endpoints are rate-limited to prevent brute-force attacks.
- **Password Hashing**: Passwords are stored in the database as hashed values using a secure algorithm.
- **Token Revocation**: Revoked tokens are stored in Redis, accessible to all services for blacklist checks.
- **RBAC**: Role-based access control ensures users can only access endpoints permitted by their roles.
- **MFA**: Multi-factor authentication is supported for added security.

## Example JWT Payload
Below is a simplified example of a decoded JWT payload issued by the Auth Service.

```json
{
  "sub": "0195d896-b211-7db2-9e8c-7cab26057e96",
  "exp": 1747760510.3977315,
  "iat": 1747758710.3977315
}
```

To get user details, the access token is sent to using `POST /api/v1/auth/verify-token` endpoint, which returns the user details and the services they have access to.

```json
{
  "data": {
    "uuid": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "username": "string",
    "email": "user@example.com",
    "firstname": "string",
    "midname": "string", // Optional
    "lastname": "string", // Optional
    "phone": "string", // Optional
    "telegram": "string", // Optional
    "role": "string", 
    "is_active": true,
    "mfa_enabled": true,
    "service_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "service_name": "string",
    "service_valid": true,
    "service_role": "string",
    "service_status": "string"
  },
  "message": "string",
  "success": true,
  "meta": null,
  "status_code": 0
}
```

### Notes on Current JWT
The current JWT payload includes more data, such as `email`, `phone`, and a `services` array with the user’s accessible services and roles. This has been simplified in the example above to reduce token size and improve security, as sensitive data should not be stored in the JWT.

## ✅ Things to Improve
- [X] **Standardize Error Responses**: Implement a consistent error response format across all endpoints for better client-side handling.
- [X] **Improve Verification Access to from Auth Service to API Services**: Implement a more secure method for API Services to verify JWTs.
- [X] **Simplify JWT Payload**: Remove sensitive data (e.g., `email`, `phone`) and the `services` array from the JWT to reduce its size and minimize data exposure risks.
- [X] **Maybe, Centralize Validate Token**: Store service access and roles in a database (cached in Redis) and create an endpoint (e.g., `GET /api/v1/auth/verify-token`) for services to dynamically check user access and roles.
- [X] **Implement Logging and Monitoring**: Add logging for all authentication and authorization events to enable auditing and monitoring of access attempts.
- [X] **Add Forgot Password and Reset Password**: Implement endpoints for initiating and completing the password reset process.
- [ ] **Build a Frontend**: Create a simple frontend application to demonstrate the Auth Service's functionality and provide a user-friendly interface for authentication and user management.
- [ ] **Add Tests**: Implement unit and integration tests to ensure the reliability and correctness of the Auth Service.
- [ ] **Improve Documentation**: Enhance the README and API documentation to provide clearer instructions and examples for developers using the Auth Service.
