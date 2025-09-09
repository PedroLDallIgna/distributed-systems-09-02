import mysql.connector
import time
import requests

def get_random_word():
    response = requests.get('https://random-words-api.kushcreates.com/api?language=pt-br&words=1')
    if response.status_code == 200:
        return response.json()[0]['word']
    return None

def main():
    conn = mysql.connector.connect(
      host="localhost",
      user="user",
      password="password",
      database="messages"
    )

    print("Listening for new events...")
    while (True):
        cursor = conn.cursor()
        conn.start_transaction()
        cursor.execute("""
            SELECT id FROM Events
            WHERE (valor IS NULL OR valor = '') AND (processing IS NULL OR processing = 0)
            ORDER BY id LIMIT 1
            FOR UPDATE
        """)
        event = cursor.fetchone()
        if not event:
            conn.commit()
            cursor.close()
            time.sleep(0.1)
            continue

        event_id = event[0]
        cursor.execute("""
            UPDATE Events
            SET processing = 1
            WHERE id = %s
        """ , (event_id,))
        conn.commit()
        cursor.close()

        cursor = conn.cursor()
        cursor.execute("""
            SELECT id FROM Events
            WHERE id = %s AND processing = 1 AND (valor IS NULL OR valor = '')
            ORDER BY id LIMIT 1
        """, (event_id,))
        locked_event = cursor.fetchone()

        try:
            if locked_event:
                event_id = locked_event[0]
                random_word = get_random_word()
                if random_word:
                    cursor.execute("UPDATE Events SET valor = %s, processing = 0 WHERE id = %s", (random_word, event_id))
                    print(f'Inserted value \'{random_word}\' in record ID {event_id}')
                    conn.commit()
        except Exception as e:
            print(f"Error: {e}")
            break
        finally:
            cursor.close()
      
        time.sleep(0.1)


if __name__ == "__main__":
    print("Starting consumer...")
    main()
