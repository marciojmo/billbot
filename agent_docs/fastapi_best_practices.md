# FastAPI Best Practices

A concise guide to writing clean, maintainable FastAPI applications following Google-inspired conventions.

---

## Project Structure

```
app/
├── main.py              # Application entry point
├── api/
│   ├── routes/          # Route handlers by domain
│   └── dependencies.py  # Shared dependencies
├── core/
│   ├── config.py        # Settings and configuration
│   └── security.py      # Auth utilities
├── models/              # Pydantic models (schemas)
├── services/            # Business logic
└── db/                  # Database layer
```

---

## Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Route files | `lower_snake_case` | `user_routes.py` |
| Route functions | `lower_snake_case` | `get_user_by_id()` |
| Path parameters | `lower_snake_case` | `/users/{user_id}` |
| Pydantic models | `PascalCase` | `UserCreate`, `UserResponse` |
| Dependencies | `lower_snake_case` | `get_current_user` |

---

## Routes

### Use Routers for Organization

```python
from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/{user_id}")
async def get_user(user_id: int) -> UserResponse:
    ...
```

### Use Descriptive HTTP Methods

```python
@router.get("/")        # List/Read
@router.post("/")       # Create
@router.put("/{id}")    # Full update
@router.patch("/{id}")  # Partial update
@router.delete("/{id}") # Delete
```

### Always Define Response Models

```python
@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int) -> UserResponse:
    ...
```

---

## Pydantic Models

### Separate Input and Output Models

```python
class UserCreate(BaseModel):
    """Schema for creating a user."""
    email: str
    password: str

class UserResponse(BaseModel):
    """Schema for user API responses."""
    id: int
    email: str
    
    model_config = ConfigDict(from_attributes=True)
```

### Use Field Validation

```python
from pydantic import BaseModel, Field, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    age: int = Field(..., ge=0, le=150)
```

---

## Dependencies

### Use Dependency Injection

```python
from fastapi import Depends

async def get_db() -> AsyncGenerator[Session, None]:
    async with async_session() as session:
        yield session

@router.get("/users")
async def list_users(db: Session = Depends(get_db)):
    ...
```

### Create Reusable Dependencies

```python
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    ...

async def get_current_active_user(
    user: User = Depends(get_current_user),
) -> User:
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user
```

---

## Error Handling

### Use HTTPException

```python
from fastapi import HTTPException, status

@router.get("/{user_id}")
async def get_user(user_id: int) -> UserResponse:
    user = await user_service.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user
```

### Create Custom Exception Handlers

```python
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(CustomError)
async def custom_error_handler(request: Request, exc: CustomError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )
```

---

## Configuration

### Use Pydantic Settings

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "MyApp"
    database_url: str
    secret_key: str
    
    model_config = ConfigDict(env_file=".env")

settings = Settings()
```

---

## Async Best Practices

### Use Async for I/O Operations

```python
# Do: async for I/O-bound operations
@router.get("/users")
async def list_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    return result.scalars().all()

# Do: sync for CPU-bound operations
@router.get("/compute")
def compute_heavy() -> int:
    return expensive_calculation()
```

### Don't Block the Event Loop

```python
# Don't: blocking call in async function
async def bad_example():
    time.sleep(5)  # Blocks the event loop

# Do: use async alternatives
async def good_example():
    await asyncio.sleep(5)
```

---

## Documentation

### Add OpenAPI Metadata

```python
@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    description="Creates a new user with the provided email and password.",
)
async def create_user(user: UserCreate) -> UserResponse:
    ...
```

### Document with Docstrings

```python
@router.get("/{user_id}")
async def get_user(user_id: int) -> UserResponse:
    """Retrieve a user by ID.
    
    Args:
        user_id: The unique identifier of the user.
    
    Returns:
        The user data.
    
    Raises:
        HTTPException: If user is not found.
    """
    ...
```

---

## Quick Reference

### Do

✅ Use routers to organize endpoints  
✅ Define response models for all endpoints  
✅ Use dependency injection  
✅ Validate input with Pydantic  
✅ Use async for I/O operations  
✅ Handle errors with HTTPException  
✅ Use environment variables for config  

### Don't

❌ Put all routes in `main.py`  
❌ Return raw dictionaries without models  
❌ Hardcode configuration values  
❌ Block the event loop with sync calls  
❌ Catch exceptions silently  
❌ Skip input validation  

---

*Last updated: January 2026*

