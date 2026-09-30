web-site to the chatbot: https://fda-drug-chatbot.streamlit.app/
example:
<img width="1894" height="976" alt="Screenshot 2026-09-30 133329" src="https://github.com/user-attachments/assets/9d798fb3-fe37-4625-8c20-e196f2bdda31" />
<img width="1897" height="620" alt="Screenshot 2026-09-30 133149" src="https://github.com/user-attachments/assets/2e4666f7-36dc-4cba-804b-9c35f9e46cac" />
<img width="1862" height="843" alt="Screenshot 2026-09-30 133254" src="https://github.com/user-attachments/assets/efdd5d42-8c72-4fce-92de-26cc6da030a2" />

So this chatbot is built on the Kaggle dataset: FDA Drug Label Data, but only a small set of the data.

First, we extract the data from the PDFs using a PDF library. Then using LangChain, we create chunks with metadata and Document objects. Then we calculate the embeddings and store them into the Pinecone vectorial database.

After this, we move to the retriever process. In this step, we focus on choosing the right function for calculating the best similarity, create the best rules for the prompts, create the chains, and we add 2 functions: the memory function and the rewriting prompt function, so when there is a follow-up question, we can rewrite the prompt so the retriever will know what to look for.

After this, we use FastAPI to build the app correctly and make the limit of the requests to respect the limit of the free model we use, and separate every logic in their folder.

Then we use Railway to deploy the backend and Streamlit Cloud to deploy the frontend of the chatbot.
