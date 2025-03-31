from langchain_chroma import Chroma
from langchain.text_splitter import CharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import sys, requests, json, os, getpass, sqlite3
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database")))
from scrape import Scrape
from github import Github
from dotenv import load_dotenv
load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = getpass.getpass("Provide your Google API key here")

class Agent:
    def __init__(self, data):
        self.data = data
        self.query = self.data.value
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.persistent_dir = os.path.join(self.current_dir, "chroma_db")
        self.current_files_in_database = os.listdir(os.path.join(self.current_dir,"chroma_db"))
        self.llm="deepseek/deepseek-r1:free"
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        self.scraper = Scrape()
        self.github = Github()


    def call_model_with_rag(self, docs):
        try:
            system_message = {
                "role" : "system",
                "content" : """You are a professional LinkedIn content creator specializing in creating engaging posts. Create a post on the given topic. If provided, use the provided relevant docs for the latest info but do not completely rely on them. Format your output exactly like a LinkedIn post, following these guidelines:
                    1. Start with a compelling hook (1-2 lines)
                    2. Break content into 2-4, scannable long, informative paragraphs
                    3. Include 3-5 relevant hashtags at the end
                    4. Keep total length between 1500-2500 characters
                    5. Use appropriate emojis (2-3 maximum) for visual engagement
                    6. Include 1-2 rhetorical questions or calls-to-action
                    7. Write in a professional yet conversational tone
                    8. End with a thought-provoking statement or actionable insight

                    Writing style:
                    - Use active voice
                    - Keep sentences concise
                    - Include specific examples and data points
                    - Maintain a positive, solution-oriented tone
                    - Address the reader directly using "you" where appropriate
                    - Include relevant industry insights and trends
                    - Focus on providing value through actionable insights
                    - Write with authority and expertise

                    Formatting requirements:
                    - Use line breaks between paragraphs
                    - Avoid bullet points
                    - No external links
                    - No @mentions
                    - No formatting markers or placeholders
                    - Ensure the post is completely ready for direct publication

                    Example structure:
                    [Hook]
                    [Line break]
                    [Main content paragraph 1]
                    [Line break]
                    [Main content paragraph 2]
                    [Line break]
                    [Concluding thought/Call-to-action]
                    [Line break]
                    [Hashtags]
                    """
            }
            documents_content = "\n\n".join([doc.page_content for doc in docs]) if docs else None
            user_message = {
                "role": "user",
                "content": "Topic: {}, Here are the relevant docs that could help: {}.".format(self.query, documents_content)
            }
            messages = [system_message, user_message]

            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
                    "Content-Type": "application/json",
                },
                
                data=json.dumps({
                    "model": "deepseek/deepseek-r1:free",
                    "messages": messages,
                })
            )
            result = response.json()
            if "choices" not in result or not result["choices"]:
                raise ValueError("Error, invalid API response format.")
            output = result['choices'][0]['message']['content']
            return output
        except Exception as e:
            print(f"Exception in call_model_with_rag: {e}")
            return None
    

    def call_model_for_github(self, docs):
        if not docs:
            return "Error: No content retrieved from your repo!!"
        try:
            system_message = {
                "role" : "system",
                "content" : """You are a professional LinkedIn content creator specializing in creating engaging posts. You are provided description of a project from a github readme file. Generate a linkedin post completely describing the post. Format your output exactly like a LinkedIn post, following these guidelines:
                    1. Start with a compelling hook (1-2 lines)
                    2. Break content into 2-4, scannable long, informative paragraphs
                    3. Include 3-5 relevant hashtags at the end
                    4. Keep total length between 1500-2500 characters
                    5. Use appropriate emojis (2-3 maximum) for visual engagement
                    6. Include 1-2 rhetorical questions or calls-to-action
                    7. Write in a professional tone
                    8. End with a thought-provoking statement or actionable insight

                    Writing style:
                    - Use active voice
                    - Keep sentences concise
                    - Include specific examples and data points
                    - Maintain a positive, solution-oriented tone
                    - Address the reader directly using "you" where appropriate
                    - Include relevant industry insights and trends
                    - Focus on providing value through actionable insights
                    - Write with authority and expertise

                    Formatting requirements:
                    - Use line breaks between paragraphs
                    - Avoid bullet points
                    - No external links
                    - No @mentions
                    - No formatting markers or placeholders
                    - Ensure the post is completely ready for direct publication

                    Example structure:
                    [Hook]
                    [Line break]
                    [Main content paragraph 1]
                    [Line break]
                    [Main content paragraph 2]
                    [Line break]
                    [Concluding thought/Call-to-action]
                    [Line break]
                    [Hashtags]
                    """
            }
            user_message = {
                "role": "user",
                "content": "Here's the content: {}".format(docs)
            }
            messages = [system_message, user_message]
            response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
                "Content-Type": "application/json",
            },
            
            data=json.dumps({
                "model": "deepseek/deepseek-r1:free",
                "messages": messages,
                
            })
            )
            output = response.json()['choices'][0]['message']['content']
            return output
        except Exception as e:
            print(f"Exception in call_model_for_github: {e}")
            return None
        

    def scrape_and_embed_github(self, link):
        content = self.github.read_readme(link)
        result_w_rag = self.call_model_for_github(docs=content)
        return result_w_rag
        


    def scrape_and_embed(self):
        docs_after_scraping = self.scraper.scrape_results(self.query)
        if docs_after_scraping is None:
            result_wo_rag = self.call_model_with_rag(docs=None)
            return result_wo_rag
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

            result_w_rag = self.call_model_with_rag(docs=relevant_docs)
            return result_w_rag

    def vaccum_database(self,path):
        try:
            conn = sqlite3.connect(path)
            conn.execute('VACUUM')
            conn.close()
        except Exception as e:
            print(f"Exception while vaccuming : {e}")
            raise

    def execute(self):
        if self.data.domain == 'topic':
            output = self.scrape_and_embed()
            if output is None:
                return None
            self.vaccum_database(os.path.join(self.current_dir, "chroma_db", "chroma.sqlite3"))
            return output
        elif self.data.domain == 'github':
            output = self.scrape_and_embed_github(self.data.value)
            return output
        else:
            return 'Cannot fetch domain'