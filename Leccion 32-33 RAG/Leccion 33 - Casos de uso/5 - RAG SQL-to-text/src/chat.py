# librerias   
import warnings
warnings.filterwarnings('ignore')

from sqlalchemy import create_engine, text

from langchain import SQLDatabase
from langchain_core.prompts import PromptTemplate
from langchain.chains import create_sql_query_chain
from langchain_openai import OpenAI
from langchain_openai.chat_models import ChatOpenAI   


import os                          
from dotenv import load_dotenv  

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')


URI = 'mysql+pymysql://root:password@localhost:3306/sakila'



def get_sql_response(prompt: str) -> str:

    """
    Funcion para automatizar queries de SQL.

    Params: prompt , string, nuestra pregunta

    Return: string, respuesta del chat
    """
    

    global OPENAI_API_KEY, URI
    
    # prompt inicial
    input_model = OpenAI(model='gpt-3.5-turbo-instruct', temperature=0)
    
    prompt = input_model.invoke(f'Traduce al ingles: {prompt}')
    
    
    # conexion a base de datos
    cursor = create_engine(URI).connect()

    tablas = cursor.execute(text('show tables;')).all()
    tablas = [e[0] for e in tablas]

    db = SQLDatabase.from_uri(URI, sample_rows_in_table_info=1, include_tables=tablas)



    # definion del prompt para generar query SQL
    sql_prompt = '''You are a MySQL expert. Given an input question, 
              first create a syntactically correct MySQL query to run, 
              then look at the results of the query and return the answer to the input question.
              Unless the user specifies in the question a specific number of examples to obtain, 
              query for at most {top_k}0 results using the LIMIT clause as per MySQL. 
              You can order the results to return the most informative data in the database.
              Never query for all columns from a table. You must query only the columns that 
              are needed to answer the question. 
              Wrap each column name in backticks (`) to denote them as delimited identifiers.
              Pay attention to use only the column names you can see in the tables below. 
              Be careful to not query for columns that do not exist. 
              Also, pay attention to which column is in which table.
              Pay attention to use CURDATE() function to get the current date, 
              if the question involves "today".
              
              Use the following format:
              
              Question: Question here
              
              SQLQuery: SQL Query to run
              
              SQLResult: Result of the SQLQuery
              
              Answer: Final answer here
              
              Only use the following tables:
              
              {table_info}
              
              Question: {input}'''

    
    sql_prompt = PromptTemplate(input_variables=['input', 'table_info', 'top_k', 'dialect'],
                                template=sql_prompt)
    
    
    # creacion de query SQL
    database_chain = create_sql_query_chain(input_model, db, prompt=sql_prompt)

    sql_query = database_chain.invoke({'question': prompt})
        
    
    # ejecucion de la query SQL
    contexto = cursor.execute(text(sql_query)).all()
    
    
    
    # respuesta final 
    output_model = ChatOpenAI(model='gpt-4-turbo')

    final_prompt = f'''Given the next query and context, answer the cuestion:
    
                   query: {sql_query},
                    
                   context: {contexto}, 
                    
                   question: {prompt}.
                   
                   If the context is a number, answer the question with it.
                   
                   Give the answer in Spanish.
                   '''
    
    return output_model.invoke(final_prompt).content


