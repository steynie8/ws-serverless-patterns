# Serverless Users API

A serverless REST API for user management built with AWS SAM, featuring JWT authentication via Amazon Cognito and Lambda authorizers.

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       │ HTTPS + JWT Token
       ▼
┌─────────────────────────────────────────────┐
│          API Gateway (REST API)             │
│                  /Prod                      │
└──────┬──────────────────────────┬───────────┘
       │                          │
       │ Authorize                │ Forward Request
       ▼                          ▼
┌──────────────────┐      ┌──────────────────┐
│   Authorizer     │      │  UsersFunction   │
│   Lambda         │      │    (Lambda)      │
│                  │      │                  │
│ Validates JWT    │      │  CRUD Operations │
│ Checks Groups    │      └────────┬─────────┘
└──────┬───────────┘               │
       │                           │ Read/Write
       │ Verify                    ▼
       ▼                    ┌─────────────────┐
┌──────────────────┐        │   UsersTable    │
│  Cognito User    │        │   (DynamoDB)    │
│      Pool        │        │                 │
│                  │        │  PK: userid     │
│ - User Auth      │        └─────────────────┘
│ - JWT Tokens     │
│ - Admin Groups   │
└──────────────────┘
```

## Components

### API Endpoints

| Method | Path              | Description           | Auth Required |
|--------|-------------------|-----------------------|---------------|
| GET    | `/users`          | List all users        | Yes           |
| PUT    | `/users`          | Create new user       | Yes           |
| GET    | `/users/{userid}` | Get user by ID        | Yes           |
| PUT    | `/users/{userid}` | Update user           | Yes           |
| DELETE | `/users/{userid}` | Delete user           | Yes           |

### AWS Resources

- **API Gateway**: REST API with Lambda authorizer
- **Lambda Functions**:
  - `UsersFunction`: Handles user CRUD operations
  - `AuthorizerFunction`: Validates JWT tokens and permissions
- **DynamoDB**: `UsersTable` with `userid` as partition key
- **Cognito User Pool**: User authentication and JWT token generation
- **Cognito User Pool Client**: OAuth 2.0 configuration

## Authentication Flow

```
1. User Login
   └─> Cognito User Pool
       └─> Returns JWT Access Token

2. API Request with Token
   └─> API Gateway
       └─> Lambda Authorizer
           ├─> Validates JWT with Cognito
           ├─> Checks user group membership
           └─> Returns IAM Policy (Allow/Deny)
               └─> UsersFunction (if allowed)
                   └─> DynamoDB Operations
```

## Deployment

```bash
sam build
sam deploy --guided
```

## Configuration

### Parameters

- `UserPoolAdminGroupName`: Cognito group for API administrators (default: `apiAdmins`)

### Environment Variables

**UsersFunction**:
- `USERS_TABLE`: DynamoDB table name

**AuthorizerFunction**:
- `USER_POOL_ID`: Cognito User Pool ID
- `APPLICATION_CLIENT_ID`: Cognito Client ID
- `ADMIN_GROUP_NAME`: Admin group name

## Usage

### 1. Authenticate

```bash
aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id <UserPoolClient> \
  --auth-parameters USERNAME=<email>,PASSWORD=<password> \
  --query 'AuthenticationResult.AccessToken' \
  --output text
```

### 2. Call API

```bash
curl -X GET \
  https://<api-id>.execute-api.<region>.amazonaws.com/Prod/users \
  -H "Authorization: <access-token>"
```

## Security Features

- JWT token validation via Cognito
- Lambda authorizer for fine-grained access control
- Admin group-based permissions
- API Gateway with AWS X-Ray tracing enabled
- DynamoDB encryption at rest (default)

## Outputs

After deployment, the stack provides:
- API Gateway endpoint URL
- Cognito User Pool ID and Client ID
- Cognito hosted UI login URL
- Authentication CLI command template
