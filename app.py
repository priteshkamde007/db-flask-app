"""
    Oracle DB connectivity with Flask
    Pritesh K
"""
import cx_Oracle

# ---------
from flask import Flask, render_template, make_response, request, redirect, url_for
app = Flask(__name__)
app.config['SECRET_KEY'] = 'godspeed'

cx_Oracle.init_oracle_client(lib_dir=r"C:\\oracle\\instantclient_21_12")
dns = """
    (DESCRIPTION = 
        (ADDRESS_LIST = 
            (ADDRESS = (PROTOCOL = TCP)
                        (HOST = navydb.artg.arizona.edu)
                        (PORT = 1521)
            )
        )
        (CONNECT_DATA =
            (SID = ORCL) 
        )
    )
"""
print("Establish connection")
def connect_with_db():
    connection = cx_Oracle.connect("mis531groupS2O", "", dsn=dns)
    return connection
print("Establish connection Done")

@app.template_filter('length')
def length_filter(iterable):
    return len(iterable)

@app.route('/')
def get_home():
    return render_template('index.html', table_name=None, columns=None, data=None, err_msg=None)

@app.route('/lms')
def get_lms():
    return render_template('lms.html', table_name=None, columns=None, data=None, err_msg=None)

@app.route('/')
def get_data_from_table(table_name):
    try:
        # Get a cursor
        connection = connect_with_db()
        cursor = connection.cursor()

        # table_name = "DUMMY_TABLE"
        query = f"SELECT * FROM {table_name}"
        cursor.execute(query)

        columns = [description[0] for description in cursor.description]
        data = cursor.fetchall()

        # debug here
        # print("columns ", columns)
        # print("data ", data)

        # Close the cursor and connection
        # cursor.close()
        # connection.close()
        return table_name, columns, data, None

    except cx_Oracle.DatabaseError as e:
        # Handle the case where the table does not exist
        print(f"Error: {e}")
        return None, None, None, e

@app.route('/<table_name>')
def hello(table_name):
    table_name, columns, data, err_msg = get_data_from_table(table_name)

    if columns is None or data is None:
        return render_template('index.html', columns=None, data=None, err_msg=err_msg)

    return render_template('index.html', table_name=table_name,columns=columns, data=data, err_msg=None)

def delete_row_from_table(table_name, column_name, column_value):
    # Get a cursor
    connection = connect_with_db()
    cursor = connection.cursor()

    try:
        # column_value = str(column_value)
        query = f"DELETE FROM {table_name} WHERE {column_name} = '{str(column_value)}'"
        print("query =", query)
        cursor.execute(query)
        connection.commit()

    except cx_Oracle.OperationalError as e:
        print(f"Error: {e}")

    finally:
        cursor.close()
        connection.close()

@app.route('/<table_name>/delete/<column_name>/<column_value>', methods=['POST'])
def delete_row(table_name, column_name, column_value):
    print("table_name", table_name)
    print("column_name", column_name)
    print("column_value", column_value)

    delete_row_from_table(table_name, column_name, column_value)
    return redirect(url_for('hello', table_name=table_name))

@app.route('/<table_name>/update/<row_id>', methods=['POST'])
def update_row(table_name, row_id):
    # Extract the updated values from the form
    updated_values = {key: request.form[key] for key in request.form.keys() if key != 'row_id'}

    # Update the row in the database
    update_row_in_table(table_name, row_id, updated_values)

    return redirect(url_for('hello', table_name=table_name))

def update_row_in_table(table_name, row_id, new_values):
    connection = connect_with_db()
    cursor = connection.cursor()

    print("table_name",table_name)
    print("row_id", row_id)
    print("new_values",new_values)
    parent_key = next(iter(new_values))

    print("key determine ", parent_key)

    try:
        set_values = ', '.join(f"{key} = '{val.strip()}'" for key, val in new_values.items())
        query = f"UPDATE {table_name} SET {set_values} WHERE {parent_key} = '{row_id}'"

        print("update query:", query)

        cursor.execute(query)
        connection.commit()

    except cx_Oracle.OperationalError as e:
        print(f"Error: {e}")

    finally:
        cursor.close()
        connection.close()

@app.route('/add_entry/<table_name>', methods=['POST'])
def add_entry(table_name):
    if request.method == 'POST':
        # Extract the updated values from the form
        updated_values = {key: request.form[key] for key in request.form.keys()}

        connection = connect_with_db()
        cursor = connection.cursor()

        try:
            # Join the keys and values for the columns and values in the query
            columns = ', '.join(updated_values.keys())
            values = ', '.join(f"'{val.strip()}'" for val in updated_values.values())

            query = f"INSERT INTO {table_name} ({columns}) VALUES ({values})"
            print("Insert query:", query)

            cursor.execute(query)
            connection.commit()

        except cx_Oracle.OperationalError as e:
            print(f"Error: {e}")

        finally:
            cursor.close()
            connection.close()

        return redirect(url_for('hello',table_name=table_name))