from langchain_chroma import Chroma
from langchain.text_splitter import CharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import sys
sys.path.append(r"F:\LPU\Code\Python\AI\database")
from scrape import Scrape
import os
import getpass
import sqlite3



if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = getpass.getpass("Provide your Google API key here")

class Agent:
    def __init__(self, query):
        self.query = query
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.persistent_dir = os.path.join(self.current_dir, "chroma_db")
        self.current_files_in_database = os.listdir(os.path.join(self.current_dir,"chroma_db"))
        self.llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        self.scraper = Scrape(query)

    def call_model_with_rag(self,query, docs):
        prompt_template_rag = ChatPromptTemplate.from_messages(
            [
                ("system",
                """You are an rag system. Answer based on your knowledge along with the information in provided documents, without referencing them.
                Strictly not generate something like 'Based on the provided information', 'According to given documents' etc that indicates that you are given external knowledge.
                If the information isn't in the documents or the documents are not provided then answer with your own knowledge, and even if you don't know the answer then reply with 'Hmm. I don't know. That's odd. Let me inform Sid'.
                Keep it clear and direct, as if explaining to someone unfamiliar with the topic.
                But make sure to answer with your own knowledge even when documents are not provided. 
                Answer in 3-4 lines atleast if not asked for more."""),

                ("human", "Here are relevant documents that can help: {docs}. Here's the query : {query}")
            ]
        )
        seq = prompt_template_rag | self.llm | StrOutputParser()
        output = seq.invoke({"query":query, "docs":"\n\n".join([doc.page_content for doc in docs])})
        return output
    
    def call_model_without_rag(self, query):
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", """You are an AI agent derived from an llm developed by Sid, an undergraduate student from India.
                            Sid created you out of his passion for AI and AI-related projects. If anyone asks about how you were trained then respond with: 'I am not supposed to answer that.
                            'If someone asks about the specific organization or individuals involved in your training, deny providing that information and respond with: Sid told me not to answer these type of questions."""),
                ("human", "Here's the query: {query}")
            ]
        )
        seq = prompt_template | self.llm | StrOutputParser()
        output = seq.invoke({"query": query})
        return output

    def scrape_and_embed(self):
        docs_after_scraping = self.scraper.scrape_results()

        if docs_after_scraping is None:
            result = self.call_model_without_rag(query=self.query)
            return f"Output w/o RAG: {result}"
        else:
            text_splitter = CharacterTextSplitter(chunk_size=30, chunk_overlap=5)
            docs = text_splitter.split_documents(docs_after_scraping)

            if not os.path.exists(self.persistent_dir):
                db = Chroma.from_documents(docs,
                self.embeddings, 
                persist_directory=self.persistent_dir
            )
            else:
                db = Chroma(persist_directory=self.persistent_dir, embedding_function=self.embeddings)
                db.add_documents(docs)

            retriever = db.as_retriever(
                search_type="similarity_score_threshold", 
                search_kwargs = {"k":3, "score_threshold" : 0.2}
            )
            relevant_docs = retriever.invoke(self.query)

            result = self.call_model_with_rag(query=self.query, docs=relevant_docs)
            return f"RAG Output : {result}"

    def vaccum_database(self,path):
        try:
            conn = sqlite3.connect(path)
            conn.execute('VACUUM')
            conn.close()
        except Exception as e:
            print(f"Exception while vaccuming : {e}")
            raise

    def execute(self):
        output = self.scrape_and_embed()
        self.vaccum_database(os.path.join(self.current_dir, "chroma_db", "chroma.sqlite3"))
        return output








