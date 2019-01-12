'''
Database connection
'''

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base


from config import DB_NAME, DB_ENGINE, DB_PASS, DB_HOST, DB_USER

engine = create_engine('{}://{}:{}@{}/{}'.format(DB_ENGINE,
                                                 DB_USER,
                                                 DB_PASS,
                                                 DB_HOST,
                                                 DB_NAME))

db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()


def init_db():
    import models
    Base.metadata.create_all(bind=engine)
