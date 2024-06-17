import streamlit as st
from snowflake.snowpark import Session
import re
from snowflake.snowpark.exceptions import SnowparkSQLException

# Establish Snowflake session
@st.cache_resource
def create_session():
    return Session.builder.configs(st.secrets.snowflake).create()

session = create_session()

def get_sql(text):
    sql_match = re.search(r"```sql\n(.*)\n```", text, re.DOTALL)
    return sql_match.group(1) if sql_match else None

# Load data table
@st.cache_data
def load_data(table_name, lmt=100):
    try:
        # Ensure the session uses the correct database and schema
        session.sql("USE DATABASE pet_store_db").collect()
        session.sql("USE SCHEMA pet_store_schema").collect()

        # Read in data table
        st.write(f"Here's the data from `{table_name}`:")
        table = session.table(table_name)
        
        # Do some computation on it
        table = table.limit(lmt)
        
        # Collect the results. This will run the query and download the data
        table = table.collect()
        return table
    except Exception as e:
        st.error(f"An error occurred while loading the table `{table_name}`: {str(e)}")
        return None

def execute_sql(query, session, retries=2):
    if re.match(r"^\s*(drop|alter|truncate|delete|insert|update)\s", query, re.I):
        st.write("Sorry, I can't execute queries that can modify the database.")
        return None
    try:
        return session.sql(query).collect()
    except SnowparkSQLException as e:
        st.write(f"An error occurred while executing the SQL query: {str(e)}")
        return None

st.title("☃️ Frosty")

# Reset chat
if st.sidebar.button("Reset Chat"):
    for key in st.session_state.keys():
        del st.session_state[key]
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help?"}]
    st.session_state["history"] = []

# Initialize the chat messages history
if "messages" not in st.session_state.keys():
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help?"}]

# Sidebar for table selection
table_names = ["customers", "pets", "favorite_icecream"]
selected_table = st.sidebar.selectbox("Select Table", table_names)

# Load and display example data from the selected table
if st.sidebar.button("Load Data"):
    data = load_data(selected_table)
    if data:
        st.write(data)

# Prompt for user input and save
if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})

# Display the existing chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# If the last message is not from the assistant, we need to generate a new response
if st.session_state.messages[-1]["role"] != "assistant":
    # Call LLM
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Ensure the session uses the correct database and schema
                session.sql("USE DATABASE pet_store_db").collect()
                session.sql("USE SCHEMA pet_store_schema").collect()

                # Include the selected table in the query
                query = f"Table: {selected_table}, Query: {prompt}"
                response = session.sql(f"select snowflake.cortex.complete('snowflake-arctic', '{query}')").collect()[0][0]
                st.write(response)

                # Attempt to execute the SQL if found in the response
                sql_query = get_sql(response)
                print("sql_query" + sql_query)
                if sql_query:
                    data = execute_sql(sql_query, session)
                    if data:
                        st.write(data)

                message = {"role": "assistant", "content": response}
                st.session_state.messages.append(message)

            except Exception as e:
                st.error(f"An error occurred while processing the query: {str(e)}")
                message = {"role": "assistant", "content": "Sorry, an error occurred while processing your request."}
                st.session_state.messages.append(message)
