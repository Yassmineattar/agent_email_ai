from database.db import get_connection

def insert_case(data: dict):
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        INSERT INTO knowledge_base 
        (logiciel, question, reponse, mots_cles, source_email_id, image_paths, source_folder, date_reception)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    values = (
        data['logiciel'],
        data['question'],
        data['reponse'],
        data.get('mots_cles'),
        data.get('source_email_id'),
        data.get('image_paths'),
        data.get('source_folder'),
        data.get('date_reception')
    )
    cursor.execute(query, values)
    conn.commit()
    conn.close()
