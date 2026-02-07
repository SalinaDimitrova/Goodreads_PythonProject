from fastapi import FastAPI

from .db_init import init_db
from .api import (
    auth,
    users,
    books,
    genres,
    reviews,
    collections,
    tags,
    friends,
    recommendations,
)

from fastapi import FastAPI

app = FastAPI(
    title="Goodreads for X",
    version="1.0.0",
)

@app.on_event("startup")
def on_startup():
    init_db()

# 🔐 AUTH
app.include_router(auth.api)

# 👤 USERS
app.include_router(users.api)

# 📚 BOOKS
app.include_router(books.api)

# 🏷 GENRES
app.include_router(genres.api)

# 📝 REVIEWS
app.include_router(reviews.api)

# 📂 COLLECTIONS
app.include_router(collections.api)

# 🏷 TAGS
app.include_router(tags.api)

# 🤝 FRIENDS
app.include_router(friends.api)

# 🎯 RECOMMENDATIONS
app.include_router(recommendations.api)
