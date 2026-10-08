import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from rag_agent.db.database import Base
from rag_agent.db.models import DocumentChunk
from rag_agent.retrieval.vector import build_vector_search_query