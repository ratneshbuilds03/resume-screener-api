import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock
from app.main import app
from app.database import Base, get_db
from app.models.user import User
from app.models.analysis import Analysis, AnalysisStatus


SQLALCHEMY_TEST_URL = "sqlite:///./test.db"
test_engine = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False}
)
TestSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine
)

def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()

class MockMongoDB:
    def __init__(self):
        self.analyses = MockCollection()

class MockCollection:
    def __init__(self):
        self._data = []

    async def insert_one(self, doc):
        self._data.append(doc)
        return MagicMock(inserted_id="mock_id")

    async def find_one(self, query):
        for doc in self._data:
            match = all(
                doc.get(k) == v
                for k, v in query.items()
            )
            if match:
                return {**doc, "_id": "mock_id"}
        return None

    def find(self, query=None, projection=None):
        return MockCursor(self._data)

    async def count_documents(self, query):
        return len(self._data)

    def aggregate(self, pipeline):
        return MockCursor([])

    async def create_index(self, keys):
        pass

class MockCursor:
    def __init__(self, data):
        self._data = data

    def sort(self, *args):
        return self

    def skip(self, n):
        return self

    def limit(self, n):
        return self

    async def to_list(self, length=None):
        return self._data[:length] if length else self._data

mock_mongo = MockMongoDB()

def override_get_mongodb():
    return mock_mongo

@pytest.fixture(scope="session")
def client():
    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = override_get_db
    from app.mongodb import get_mongodb
    app.dependency_overrides[get_mongodb] = override_get_mongodb

    with TestClient(app) as c:
        yield c

    Base.metadata.drop_all(bind=test_engine)
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()
        db.close()

@pytest.fixture
def test_user(db):
    from passlib.context import CryptContext
    pwd = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
    user = User(
        name="Test User",
        email="test@example.com",
        password_hash=pwd.hash("testpass123"),
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def auth_token(client, test_user):
    response = client.post("/auth/login", data={
        "username": "test@example.com",
        "password": "testpass123"
    })
    assert response.status_code == 200
    return response.json()["access_token"]

@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}

@pytest.fixture
def sample_pdf():
    pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]
/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length 200 >>
stream
BT
/F1 12 Tf
50 750 Td
(Python Developer Resume) Tj
0 -20 Td
(Skills: Python, FastAPI, MySQL, MongoDB, Docker, AWS, Redis) Tj
0 -20 Td
(Experience: 3 years Python development) Tj
0 -20 Td
(Education: B.Tech Computer Science) Tj
ET
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
trailer
<< /Size 6 /Root 1 0 R >>
startxref
500
%%EOF"""
    return pdf_content