import streamlit as st

st.title("Start Streamlit learning")
st.subheader("Yayyyy A small subheader")
st.text("Look same but this is a text")
st.write("IDK why they make this one")

lang = st.selectbox("Select One language from this :", ["Java", "Python", "C#", "GO"])

st.subheader(f"You're Favourite Language is : {lang}")