import streamlit as st
from rag_implement import rag_implement
# Streamlit front-end
st.title("基于RAG的QA问答系统")

# Text input for user query
user_query = st.text_input("在此输入你的问题：")

# Button to submit the query
if st.button("生成答案"):
    if user_query:
        answer = rag_implement(user_query)
        st.write("答案:")
        st.write(answer)
    else:
        st.write("请输入你的问题")