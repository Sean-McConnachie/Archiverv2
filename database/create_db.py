from simplicity.json_handler import jLoad
import os


INITIAL_DATA = jLoad(os.path.join("database", "on_create.json"))
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

    role_data_table = """
    CREATE TABLE IF NOT EXISTS role_data (
        role_id BIGINT PRIMARY KEY,
        is_admin BOOLEAN,
        is_moderator BOOLEAN,
        is_tutor BOOLEAN,
        is_class BOOLEAN
    )
    """

    category_data_table = """
    CREATE TABLE IF NOT EXISTS category_data (
        category_id BIGINT PRIMARY KEY,
        category_name TEXT,
        class_role_id BIGINT REFERENCES role_data (role_id),
        active_category BOOLEAN
    )    
    """

    await conn.execute(topics_table)
    await conn.execute(threads_table)
    await conn.execute(role_data_table)
    await conn.execute(category_data_table)

    for item in INITIAL_DATA["role_data"]:
        try:
            query = """INSERT INTO role_data (
                role_id, is_admin, is_moderator, is_tutor, is_class
            )
            VALUES (
                $1, $2, $3, $4, $5
            )
            """
            await conn.execute(query, *list(item.values()))
        except:
            pass

    for item in INITIAL_DATA["category_data"]:
        try:
            query = """INSERT INTO category_data (
                category_id, category_name, class_role_id, active_category
            )
            VALUES (
                $1, $2, $3, $4
            )
            """
            await conn.execute(query, *list(item.values()))
        except:
            pass
