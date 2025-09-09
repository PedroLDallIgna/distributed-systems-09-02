import flask
from flask import jsonify
import mysql.connector
from mysql.connector import pooling
import time

app = flask.Flask(__name__)
app.config["DEBUG"] = True

dbconfig = {
  "host": "mysql",
  "user": "user",
  "password": "password",
  "database": "messages"
}

pool = pooling.MySQLConnectionPool(pool_name="mypool", pool_size=5, **dbconfig)

def get_conn():
    return pool.get_connection()

CREATE_EVENT_QUERY = "INSERT INTO Events (id, valor) VALUES (%s, \"\")"
GET_ALL_EVENTS = "SELECT id, valor FROM Events"
GET_EVENT_BY_ID = "SELECT valor FROM Events WHERE id = %s"
GET_STATUS_ID = "SELECT * FROM DBStatus"
UPDATE_STATUS_ID = "UPDATE DBStatus SET id = %s"

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('x-service-language', 'python')
    return response

@app.route('/', methods=['GET'])
def get_events():
    '''
    get all events
    '''
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(GET_STATUS_ID)
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    return jsonify({ "events": result[0] })

@app.route('/<int:id>', methods=['GET'])
def get_event_by_id(id):
    '''
    get a specific event by id
    '''
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(GET_EVENT_BY_ID, (id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    if result:
        return jsonify({"valor": result[1]})
    return jsonify({"message": "Event not found"}), 404


def execute_create_event():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(GET_STATUS_ID)
    last_id_row = cursor.fetchone()
    last_id = last_id_row[0] if last_id_row else 0
    new_id = last_id + 1
    cursor.execute(CREATE_EVENT_QUERY, (new_id,))
    cursor.execute(UPDATE_STATUS_ID, (new_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return new_id


@app.route('/create-sync', methods=['POST'])
def create_event_sync():
    '''
    create a new event synchronously
    '''
    try:
        event_id = execute_create_event()
        value = ''

        conn = get_conn()

        while True:
            cursor = conn.cursor()
            cursor.execute(GET_EVENT_BY_ID, (event_id,))
            event = cursor.fetchone()
            conn.commit()
            cursor.close()

            if event and event[1] != '':
                value = event[1]
                break
            
            time.sleep(0.1)

        return jsonify({"valor": value}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route('/create-async', methods=['POST'])
def create_event_async():
    '''
    create a new event asynchronously
    '''
    event_id = execute_create_event()
    return jsonify({"message": "Event created on demand", "id": event_id}), 201


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
