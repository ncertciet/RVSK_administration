from psycopg2.pool import ThreadedConnectionPool

from app.config.settings import get_settings
from app.utils.logger import logger

settings = get_settings()

connection_pool = None


def initialize_connection_pool():

    global connection_pool

    if connection_pool is None:

        connection_pool = ThreadedConnectionPool(

            minconn=settings.DB_MIN_CONNECTIONS,

            maxconn=settings.DB_MAX_CONNECTIONS,

            host=settings.DB_HOST,

            port=settings.DB_PORT,

            database=settings.DB_NAME,

            user=settings.DB_USER,

            password=settings.DB_PASSWORD

        )

        logger.info("PostgreSQL connection pool initialized.")


def get_connection():

    if connection_pool is None:

        initialize_connection_pool()

    return connection_pool.getconn()


def release_connection(connection):

    if connection_pool:

        connection_pool.putconn(connection)


def close_connection_pool():

    global connection_pool

    if connection_pool:

        connection_pool.closeall()

        logger.info("PostgreSQL connection pool closed.")