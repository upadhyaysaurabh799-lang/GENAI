# =======================================================
''''import requirmant libary'''
# ===============================================
import pickle
import pandas as pd
from pathlib import Path
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever
import sqlite3
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnablePassthrough
from langchain_core.messages import ToolMessage

# load chanks
LOAD_PATH = Path("../data/processed/chunks.pkl")

with open(LOAD_PATH, "rb") as f:
    chunks = pickle.load(f)

# print(f"✅ Loaded {len(chunks)} chunks")

embedding_model = HuggingFaceEmbeddings(
    model_name="BAAI/bge-small-en-v1.5"
)

# print("✅ Embedding Model Loaded")

vectorstore = FAISS.load_local(
    "../data/processed/vectorstore",
    embedding_model,
    allow_dangerous_deserialization=True
)

print("✅ FAISS Loaded")

# vector retrival(summantic ret)
vector_retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 4}
)

# print("✅ Vector Retriever Ready")

# create BM25 retrival
bm25_retriever = BM25Retriever.from_documents(chunks)
bm25_retriever.k = 4

# print("✅ BM25 Ready")

# hybread retrival
hybrid_retriever = EnsembleRetriever(
    retrievers=[
        bm25_retriever,
        vector_retriever
    ],
    weights=[
        0.4,
        0.6
    ]
)

# print("✅ Hybrid Retriever Ready")

from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
print(api_key)   # Test ke liye

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0
)

prompt = ChatPromptTemplate.from_template("""
You are a professional customer support assistant build by saurabh upadhyay.

Answer ONLY from the provided context.

Rules:
1. Never make up information.
2. If the answer is not available in the context, say:
   "I couldn't find the correct information. I'll connect you with a human support agent."
3. Be polite.
4. Keep answers concise.
5. Guide the customer step by step whenever appropriate.

Context:
{context}

Question:
{question}

Answer:
""")

# context formet
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

rag_chain = (
    {
        "context": hybrid_retriever | format_docs,
        "question": RunnablePassthrough()
    }
    | prompt
    | llm
    | StrOutputParser()
)

# print("✅ RAG Chain Ready")

DATABASE_PATH = r"C:\Users\R&D\Desktop\AI System\GENAI\DataLoading\orders.db"

conn = sqlite3.connect(DATABASE_PATH)

df = pd.read_sql("PRAGMA table_info(orders);", conn)

conn.close()

conn = sqlite3.connect(DATABASE_PATH)

# print("===== ORDERS TABLE =====")
# print(pd.read_sql("SELECT * FROM orders LIMIT 5;", conn))

# print("\n===== CUSTOMERS TABLE =====")
# print(pd.read_sql("SELECT * FROM customers LIMIT 5;", conn))

# print("\n===== PRODUCTS TABLE =====")
# print(pd.read_sql("SELECT * FROM products LIMIT 5;", conn))

conn.close()

@tool
def get_order_status(order_id: str):
    """
    Get complete order details using Order ID.
    """

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            c.name,
            p.name,
            o.quantity,
            o.order_date,
            o.delivery_date,
            o.status,
            o.payment_method,
            o.tracking_id

        FROM orders o

        JOIN customers c
            ON o.customer_id = c.customer_id

        JOIN products p
            ON o.product_id = p.product_id

        WHERE o.order_id = ?
    """, (order_id,))

    row = cursor.fetchone()

    conn.close()

    if row is None:
        return "❌ Order not found."

    return f"""
Order ID: {order_id}

Customer: {row[0]}

Product: {row[1]}

Quantity: {row[2]}

Order Date: {row[3]}

Delivery Date: {row[4]}

Status: {row[5]}

Payment Method: {row[6]}

Tracking ID: {row[7]}
"""

@tool
def check_return(order_id:str):
    """
    Check whether order is eligible for return.
    """

    conn=sqlite3.connect(DATABASE_PATH)

    cursor=conn.cursor()

    cursor.execute("""
    SELECT
    return_window,
    return_status

    FROM orders

    WHERE order_id=?
    """,(order_id,))

    row=cursor.fetchone()

    conn.close()

    if row is None:

        return "Order not found."

    return f"""

Return Window : {row[0]}

Return Status : {row[1]}


"""

conn = sqlite3.connect(DATABASE_PATH)
cursor = conn.cursor()

# Existing columns
cursor.execute("PRAGMA table_info(orders)")
existing_columns = [col[1] for col in cursor.fetchall()]

if "return_window" not in existing_columns:
    cursor.execute("""
        ALTER TABLE orders
        ADD COLUMN return_window INTEGER
    """)

if "return_status" not in existing_columns:
    cursor.execute("""
        ALTER TABLE orders
        ADD COLUMN return_status TEXT
    """)

if "refund_status" not in existing_columns:
    cursor.execute("""
        ALTER TABLE orders
        ADD COLUMN refund_status TEXT
    """)

conn.commit()
conn.close()

# print("✅ Orders table schema verified.")
@tool
def track_delivery(order_id: str):
    """
    Get delivery status using order id.
    """

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            status,
            delivery_date,
            tracking_id

        FROM orders

        WHERE order_id=?
    """, (order_id,))

    row = cursor.fetchone()

    conn.close()

    if row is None:
        return "Order not found."

    return f"""
Order ID : {order_id}

Status : {row[0]}

Expected Delivery : {row[1]}

Tracking ID : {row[2]}
"""

@tool
def get_product_details(order_id: str):
    """
    Get ordered product details using order id.
    """

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            p.name,
            p.category,
            p.price,
            o.quantity

        FROM orders o

        JOIN products p
        ON o.product_id=p.product_id

        WHERE o.order_id=?
    """, (order_id,))

    row = cursor.fetchone()

    conn.close()

    if row is None:
        return "Order not found."

    total = row[2] * row[3]

    return f"""
Product : {row[0]}

Category : {row[1]}

Price : ₹{row[2]}

Quantity : {row[3]}

Total Price : ₹{total}
"""
@tool
def get_customer_details(order_id: str):
    """
    Get customer information using order id.
    """

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            c.name,
            c.email,
            c.phone,
            c.address

        FROM orders o

        JOIN customers c
        ON o.customer_id=c.customer_id

        WHERE o.order_id=?
    """, (order_id,))

    row = cursor.fetchone()

    conn.close()

    if row is None:
        return "Order not found."

    return f"""
Customer : {row[0]}

Email : {row[1]}

Phone : {row[2]}

Address :

{row[3]}
"""
tools = [
    get_order_status,
    track_delivery,
    get_product_details,
    get_customer_details,
    check_return
    
]

llm_with_tools = llm.bind_tools(tools)

tool_dict = {
tool.name: tool
for tool in tools}

# print("Tools Connected")

from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage
)
chat_history = [
    SystemMessage(
        content="""
You are an Amazon Customer Support Assistant.

Remember previous conversation.

Answer politely.

Use tools whenever needed.
"""
    )
]

from langchain_core.messages import ToolMessage
def customer_support_agent(question):

    global chat_history

    chat_history.append(
        HumanMessage(content=question)
    )

    response = llm_with_tools.invoke(chat_history)


    if response.tool_calls:

        chat_history.append(response)

        for tool_call in response.tool_calls:

            tool = tool_dict[tool_call["name"]]

            result = tool.invoke(tool_call["args"])

            chat_history.append(
                ToolMessage(
                    content=str(result),
                    tool_call_id=tool_call["id"]
                )
            )


        final = llm.invoke(chat_history)

        chat_history.append(
            AIMessage(content=final.content)
        )

        return final.content


    chat_history.append(
        AIMessage(content=response.content)
    )

    return response.content
