import streamlit as st
from snowflake.snowpark.context import get_active_session
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
rag = st.sidebar.checkbox('Use RAG?')

# Establish Snowflake session
session = get_active_session()

def get_sql(text):
    # Regular expression to find SQL code block or inline SQL queries
    sql_match = re.search(r"(SELECT .*?;|INSERT .*?;|UPDATE .*?;|DELETE .*?;|CREATE .*?;|DROP .*?;|ALTER .*?;|WITH .*?;|```sql\s+(.*?)\s+```)", text, re.DOTALL | re.IGNORECASE)
    
    if sql_match:
        sql_code = sql_match.group(1) or sql_match.group(2)
        return sql_code.strip()  # Remove any leading/trailing whitespace
    return None

# Load data table
def load_data(table_name, lmt=100):
    try:
        # Read in data table
        st.write(f"Here's the data from `{table_name}`:")
        table = session.table(f"GSDATASET.DATAS.{table_name}")
        
        # Do some computation on it
        table = table.limit(lmt)
        
        # Collect the results. This will run the query and download the data
        table = table.collect()
        return table
    except Exception as e:
        st.error(f"An error occurred while loading the table `{table_name}`: {str(e)}")
        return None

def clean_query(query):
    # Remove any backslashes followed by an asterisk
    query = query.replace('\\*', '*')
    # Remove any remaining backslashes (optional, depends on the context)
    query = query.replace('\\', '')
    # Replace smart quotes with standard quotes
    query = query.replace('\u2018', "'").replace('\u2019', "'").replace('\u201C', '"').replace('\u201D', '"')
    return query.strip()  # Remove any leading/trailing whitespace

def execute_sql(query, session, retries=2):
    try:
        # Clean the query string
        query = clean_query(query)

        # Ensure it's a safe query
        if re.match(r"^\s*(drop|alter|truncate|delete|insert|update)\s", query, re.I):
            st.write("Sorry, I can't execute queries that can modify the database.")
            return None
        
        result = session.sql(query).collect()
        return result
    except SnowparkSQLException as e:
        st.write(f"An error occurred while executing the SQL query: {str(e)}")
        return None

# New functions
num_chunks = 3

def create_prompt(myquestion, rag):
    if rag == 1:
        # A similarity search to look for the closest Q&A pair and provide it as context in the prompt
        cmd = """
         with results as
         (SELECT QUESTION, SQL_STRING,
           VECTOR_COSINE_SIMILARITY(
             SNOWFLAKE.CORTEX.EMBED_TEXT_768('e5-base-v2', docs_qna_table.question),
             SNOWFLAKE.CORTEX.EMBED_TEXT_768('e5-base-v2', ?)
           ) as similarity
         from docs_qna_table
         order by similarity desc
         limit ?)
         select QUESTION, SQL_STRING from results 
         """
    
        df_context = session.sql(cmd, params=[myquestion, num_chunks]).to_pandas()      
        
        context_length = len(df_context)

        prompt_context = ""
        for i in range(context_length):
            prompt_context += f"Q: {df_context._get_value(i, 'QUESTION')}\nA: {df_context._get_value(i, 'SQL_STRING')}\n"

        prompt_context = prompt_context.replace("'", "")
    
        prompt = f"""
          'You are an expert assistance extracting information from context provided. 
           Answer the question based on the context. Be concise and do not hallucinate. 
           If you don't have the information just say so.
          Context: {prompt_context}
          Question:  
           {myquestion} 
           Answer: '
           """
    else:
        prompt = f"""
         'Question:  
           {myquestion} 
           Answer: '
           """
        
    return prompt

def complete(myquestion, model_name, rag=1):
    prompt = create_prompt(myquestion, rag)
    cmd = f"""
             select SNOWFLAKE.CORTEX.COMPLETE(?,?) as response
           """
    df_response = session.sql(cmd, params=[model_name, prompt]).collect()
    return df_response

def display_response(question, model, rag=0):
    response = complete(question, model, rag)
    res_text = response[0].RESPONSE
    # Attempt to execute the SQL if found in the response
    st.markdown(res_text)
    sql_query = get_sql(res_text)
    # st.write("Extracted SQL Query: " + str(sql_query))
    if sql_query:
        # Ensure the SQL query is clean
        sql_query = sql_query.replace('\u2018', "'").replace('\u2019', "'").replace('\u201C', '"').replace('\u201D', '"')
        # st.write("Cleaned SQL Query: " + sql_query)
        data = execute_sql(sql_query, session)
        # st.write("Query Result: " + str(data))
        if data:
            st.write(data)

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
                question = st.session_state.messages[-1]["content"]

                # Use RAG if selected
                rag_option = 1 if rag else 0
                display_response(question, model, rag_option)

                message = {"role": "assistant", "content": "Response generated and displayed."}
                st.session_state.messages.append(message)

            except Exception as e:
                st.error(f"An error occurred while processing the query: {str(e)}")
                message = {"role": "assistant", "content": "Sorry, an error occurred while processing your request."}
                st.session_state.messages.append(message)
