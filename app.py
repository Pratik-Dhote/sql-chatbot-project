import streamlit as st
from langchain.agents import create_sql_agent
from langchain.sql_database import SQLDatabase
from langchain.agents.agent_types import AgentType
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.callbacks import StreamlitCallbackHandler
from sqlalchemy import create_engine
import sqlite3
from langchain_groq import ChatGroq
from urllib.parse import quote_plus

st.set_page_config(page_title="LangChai:Chat with SQL DB", page_icon="🦜" )
st.title("🦜 Langchain: Chat with SQL DB")

radio_opt=["Connect to your MySQL Database"]

selected_opt=st.sidebar.radio(label="Choose the DB you want to connect and chat",options=radio_opt)

if selected_opt.index(selected_opt)==0:
    mysql_host=st.sidebar.text_input("Provide MySQL Host")
    mysql_user=st.sidebar.text_input("MySQL user")
    mysql_password=st.sidebar.text_input("MySQL password",type="password")
    mysql_db=st.sidebar.text_input("MySQL database")
else:
    st.info("provide dabase information")    

api_key=st.sidebar.text_input(label="Enter GROQ API key", type="password")

if not api_key:
    st.warning("Please enter your Groq API key to continue.")
    st.stop()

llm=ChatGroq(api_key=api_key, model_name="Llama3-8b-8192",streaming=True)

@st.cache_resource(ttl=2)
def configure_db(mysql_host=None,mysql_user=None,mysql_password=None,mysql_db=None):
    if not (mysql_host and mysql_user and mysql_password and mysql_db):
        st.error("Please provide all MySQL connection details.")
        st.stop()
    password_encoder=quote_plus(mysql_password)    
    return SQLDatabase(create_engine(f"mysql+mysqlconnector://{mysql_user}:{password_encoder}@{mysql_host}/{mysql_db}"))  


## TOOLKIT

toolkit=SQLDatabaseToolkit(llm=llm, db=configure_db(mysql_host,mysql_user,mysql_password,mysql_db))

agent=create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    verbose=True,
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION
)



table_name = st.sidebar.text_input("Enter Table Name (optional)", placeholder="e.g., students")

if "messages" not in st.session_state or st.sidebar.button("Clear message history"):
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

user_query=st.chat_input(placeholder="Ask anything from the database")

if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})
    st.chat_message("user").write(user_query)

    with st.chat_message("assistant"):
        streamlit_callback=StreamlitCallbackHandler(st.container())
        full_query = f"Query from table {table_name}: {user_query}" if table_name else user_query
        response=agent.run(full_query,callbacks=[streamlit_callback])
        st.session_state.messages.append({"role":"assistant","content":response})
        st.write(response)
