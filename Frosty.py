import streamlit as st
from snowflake.snowpark import Session
import re
from snowflake.snowpark.exceptions import SnowparkSQLException

# Here you can choose what LLM to use. Please note that they will have different cost & performance
model = st.sidebar.selectbox('Select your model:', (
    'mixtral-8x7b',
    'snowflake-arctic',
    'mistral-large',
    'llama3-8b',
    'llama3-70b',
    'reka-flash',
    'mistral-7b',
    'llama2-70b-chat',
    'gemma-7b'))

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
        session.sql("USE DATABASE GSDATASET").collect()
        session.sql("USE SCHEMA DATAS").collect()

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
table_names = ["Regions", "Systems", "Revenue"]
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
                session.sql("USE DATABASE GSDATASET").collect()
                session.sql("USE SCHEMA DATAS").collect()

                # Include the selected table and model in the query
                query = f"Table: {selected_table}, Query: {prompt}"
                st.write(f"Query sent to LLM: {query}")  # Log the query for debugging

                response = session.sql(f"select snowflake.cortex.complete('{model}', $$ {query} $$)").collect()[0][0]
                st.write(f"LLM response: {response}")  # Log the response for debugging

                # Attempt to execute the SQL if found in the response
                sql_query = get_sql(response)
                if sql_query:
                    st.write(f"SQL query extracted: {sql_query}")  # Log the extracted SQL query for debugging
                    data = execute_sql(sql_query, session)
                    if data:
                        st.write(data)

                message = {"role": "assistant", "content": response}
                st.session_state.messages.append(message)

            except Exception as e:
                st.error(f"An error occurred while processing the query: {str(e)}")
                message = {"role": "assistant", "content": "Sorry, an error occurred while processing your request."}
                st.session_state.messages.append(message)
