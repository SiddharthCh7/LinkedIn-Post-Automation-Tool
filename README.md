# 🚀 LinkedIn Post Automation Tool

## 📌 Overview
Tired of manually creating LinkedIn posts? This tool **automates** the entire process—from finding relevant content to publishing a well-structured post. Simply provide a **topic name** or a **GitHub README link**, and let AI do the magic! ✨

[![LinkedOut](./templates/img.png)](https://linkedout-a6rv.onrender.com/)

🌐 **Live**: [https://linkedout-a6rv.onrender.com/](https://linkedout-a6rv.onrender.com/)  

## 🔥 How It Works
1. **User Input 📝**: Enter a **topic name** or a **GitHub README link**.
2. **Custom Search Engine 🔍**: The tool queries **Google Custom Search API** to fetch relevant web links.
3. **Scraping with Failure Handling 🕷️**: Extracts content using **BeautifulSoup**, with mechanisms to handle non-scrapable websites.
4. **Embedding & Storage 📚**: The extracted content is embedded and stored in **ChromaDB** for efficient retrieval.
5. **Similarity Search 🔎**: Retrieves the most relevant content using similarity search techniques.
6. **AI-Generated Post 🤖**: **LLM** from **OpenRouter** processes the retrieved content with a precise brief prompt and crafts an engaging LinkedIn post.
7. **Auto-Publish 🚀**: The post is **instantly** published on LinkedIn using the **LinkedIn API**.

## 🎯 Key Features
✅ **AI-Powered Post Generation** – Creates high-quality, engaging posts 📢  
✅ **Automated Content Search** – Finds **relevant** articles using Google Custom Search API 🔍  
✅ **Smart Content Extraction** – Web scraping with failure handling 🕷️  
✅ **Efficient Context Storage** – Uses **ChromaDB** for optimized retrieval 🧠  
✅ **Seamless LinkedIn Integration** – Directly posts to LinkedIn in one click 🎯  
✅ **Custom Input Methods** – Supports **both topics & README files** 📝  

## 🌟 Tech Stack
- **Python** 🐍 – Core backend scripting  
- **Google Custom Search API** 🔍 – To fetch relevant web links  
- **BeautifulSoup** 🕷️ – For robust web scraping  
- **ChromaDB** 📚 – Vector database for efficient retrieval  
- **LangChain** 🔗 – For similarity search & content retrieval  
- **LinkedIn API** 🔗 – For automated post publishing  

## 🏆 Impact
🚀 **Boost Productivity** – No more manual post writing, **save hours**!  
📈 **Enhance Engagement** – Posts are well-structured & AI-optimized for maximum reach.  
🎯 **Consistent Posting** – Stay active on LinkedIn **without extra effort**!  

## ⚠️ Challenges Faced & Tackled
1. **Extracting Relevant Content** 🧐 – Some websites block scraping. Solution? **Google Custom Search API** + **failure handling in BeautifulSoup**.
2. **Maintaining Context** 🧠 – Many sources had redundant info. Solution? **ChromaDB for efficient retrieval using embeddings**.
3. **LinkedIn API Limitations** 🚫 – Posting limitations required **rate-limiting & API token management**.

## 🔧 Installation & Usage
```sh
git clone https://github.com/SiddharthCh7/LinkedIn-Post-Automation.git
cd LinkedIn-Post-Automation
pip install -r requirements.txt
```

To generate a post:
```sh
python main.py --topic "AI in Healthcare"
# OR
python main.py --github_link "https://github.com/someproject/README.md"
```

### 🔑 Environment Variables
Create a `.env` file and add:
```
GOOGLE_API_KEY
GOOGLE_SEARCH_API_KEY
SEARCH_ENGINE_ID
CLIENT_ID
CLIENT_SECRET
OPENROUTER_API_KEY
GITHUB_API_KEY
```

## 🚀 Future Enhancements
✨ Support for multiple social media platforms  
✨ Advanced AI-powered post structuring  
✨ Post scheduling & analytics dashboard  

## 🤝 Contributing
Contributions welcome! Fork the repo & submit a PR. Let's build this together! 💡

---
💡 Developed by [Siddharth](https://linkedin.com/in/siddharth-ch05)