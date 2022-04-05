import asyncio
import asyncpg
from json_handler import jLoad


CONFIG = jLoad('config.json')


async def createDB(conn):
    topics_table = """
    CREATE TABLE IF NOT EXISTS topics (
        topic_id SERIAL PRIMARY KEY,
        channel_id BIGINT,
        topic_name TEXT,
        channel_name TEXT,
        topic_description TEXT,
        class_name TEXT,
        topic_tags TEXT[],
        dt_created TIMESTAMP,
        dt_closed TIMESTAMP DEFAULT null,
        creator_id BIGINT,
        upvotes BIGINT[],
        downvotes BIGINT[],
        archive_channel_id BIGINT DEFAULT null,
        archive_dt_created TIMESTAMP DEFAULT null,
        archive_creator_id BIGINT DEFAULT null
    )
    """

    threads_table = """
    CREATE TABLE IF NOT EXISTS threads(
        topic_id SERIAL REFERENCES topics (topic_id),
        message_id BIGINT PRIMARY KEY,
        sender_id BIGINT,
        dt_sent TIMESTAMP,
        is_tutor BOOLEAN,
        message_content TEXT,
        file_links TEXT[]
    )
    """

    await conn.execute(topics_table)
    await conn.execute(threads_table)
