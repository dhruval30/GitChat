import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from langchain.chains import LLMChain
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain_core.messages import SystemMessage
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain_groq import ChatGroq
from langchain_text_splitters import RecursiveCharacterTextSplitter
from flask_cors import CORS
from repo2text import get_readme_content, traverse_repo_iteratively, get_file_contents_iteratively

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

load_dotenv()

# Global variables to store repository data and conversation memory
repo_data = {}
memory = ConversationBufferWindowMemory(k=5, memory_key="chat_history", return_messages=True)

def fetch_repo_data(repo_url):
    """Fetch repository data from GitHub."""
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    
    if not GITHUB_TOKEN:
        raise ValueError("GitHub token not set. Please set the GITHUB_TOKEN environment variable.")
    
    try:
        from github import Github
        g = Github(GITHUB_TOKEN)
        
        # Extract repo owner and name from URL
        repo_path = repo_url.replace('https://github.com/', '')
        repo = g.get_repo(repo_path)
        
        print(f"Fetching README for: {repo_path}")
        readme = get_readme_content(repo)
        
        print(f"Fetching repository structure")
        structure = traverse_repo_iteratively(repo)
        
        print(f"Fetching file contents")
        file_contents = get_file_contents_iteratively(repo)
        
        return {
            "readme": readme if readme else "No README found.",
            "structure": structure if structure else "No structure information found.",
            "file_contents": file_contents if file_contents else "No file contents found."
        }
    except Exception as e:
        raise ValueError(f"Failed to fetch repository: {str(e)}")

def create_compressed_repo_info(repo_data, max_tokens=4000):
    """Create a compressed version of repo info that fits within token limits."""
    # text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=max_tokens,
        chunk_overlap=0,
        length_function=len,
    )
    
    # Format the repo data with section headers
    readme_section = f"README:\n{repo_data['readme']}"
    structure_section = f"REPOSITORY STRUCTURE:\n{repo_data['structure']}"
    file_contents_section = f"FILE CONTENTS:\n{repo_data['file_contents']}"
    
    # If the combined data is likely to exceed token limits, prioritize and trim
    # This is a rough approximation (1 token ≈ 4 chars)
    estimated_tokens = (len(readme_section) + len(structure_section) + len(file_contents_section)) / 4
    
    if estimated_tokens > max_tokens:
        # Prioritize README and structure, trim file contents
        combined_text = f"{readme_section}\n\n{structure_section}\n\n"
        remaining_tokens = max_tokens - (len(combined_text) / 4)
        
        if remaining_tokens > 0:
            # Add as much of the file contents as possible
            file_content_chunks = text_splitter.create_documents([file_contents_section])
            if file_content_chunks:
                # Take just the beginning part of file contents
                combined_text += file_content_chunks[0].page_content
                combined_text += "\n\n[Note: File contents were truncated due to token limits]"
        
        return combined_text
    else:
        # If everything fits, return the full text
        return f"{readme_section}\n\n{structure_section}\n\n{file_contents_section}"

@app.route('/fetch_repo', methods=['POST'])
def fetch_repository():
    global repo_data, memory
    data = request.json
    repo_url = data.get('repo_url')
    
    if not repo_url:
        return jsonify({"error": "Repository URL is required"}), 400

    try:
        repo_data = fetch_repo_data(repo_url)
        # Reset conversation memory when switching repositories
        memory = ConversationBufferWindowMemory(k=5, memory_key="chat_history", return_messages=True)
        return jsonify({"message": "Repository data fetched successfully"}), 200
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

@app.route('/ask_question', methods=['POST'])
def ask_question():
    global repo_data, memory
    data = request.json
    user_question = data.get('question')

    if not user_question:
        return jsonify({"error": "Question is required"}), 400

    if not repo_data:
        return jsonify({"error": "Repository data not loaded. Please fetch a repository first."}), 400

    # Create a compressed version of the repo data that will fit within token limits
    compressed_repo_info = create_compressed_repo_info(repo_data)
    
    system_prompt = """
    You are a friendly and knowledgeable AI assistant specialized in analyzing GitHub repositories.
    Use the repository information provided to answer questions about the codebase.
    Be specific and precise in your explanations, referencing actual files and code when relevant.
    If you don't have enough information to answer a question completely, explain what you know
    and what additional information would be needed.
    """
    
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        return jsonify({"error": "GROQ_API_KEY not set in environment variables"}), 500
    
    model = os.getenv("GROQ_MODEL", "llama3-8b-8192")  
    
    try:
        groq_chat = ChatGroq(groq_api_key=groq_api_key, model_name=model)

        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=f"{system_prompt}\n\nRepository Information:\n{compressed_repo_info}"),
                MessagesPlaceholder(variable_name="chat_history"),
                HumanMessagePromptTemplate.from_template("{human_input}")
            ]
        )

        # Conversation chain
        conversation = LLMChain(llm=groq_chat, prompt=prompt, verbose=False, memory=memory)

        response = conversation.predict(human_input=user_question)
        return jsonify({"response": response}), 200
    
    except Exception as e:
        # If we hit token limits, try with more aggressive compression
        if "413" in str(e) or "Request too large" in str(e):
            try:
                # create an even more compressed version with only README and structure
                readme_section = f"README:\n{repo_data['readme']}"
                structure_section = f"REPOSITORY STRUCTURE:\n{repo_data['structure']}"
                minimal_repo_info = f"{readme_section}\n\n{structure_section}"
                
                prompt = ChatPromptTemplate.from_messages(
                    [
                        SystemMessage(content=f"{system_prompt}\n\nRepository Information (limited):\n{minimal_repo_info}"),
                        MessagesPlaceholder(variable_name="chat_history"),
                        HumanMessagePromptTemplate.from_template("{human_input}")
                    ]
                )
                
                conversation = LLMChain(llm=groq_chat, prompt=prompt, verbose=False, memory=memory)
                response = conversation.predict(human_input=user_question)
                return jsonify({"response": response}), 200
            
            except Exception as inner_e:
                # as a last resort, try with just the README
                try:
                    readme_only = f"README:\n{repo_data['readme']}"
                    
                    prompt = ChatPromptTemplate.from_messages(
                        [
                            SystemMessage(content=f"{system_prompt}\n\nRepository Information (readme only):\n{readme_only}"),
                            MessagesPlaceholder(variable_name="chat_history"),
                            HumanMessagePromptTemplate.from_template("{human_input}")
                        ]
                    )
                    
                    conversation = LLMChain(llm=groq_chat, prompt=prompt, verbose=False, memory=memory)
                    response = conversation.predict(human_input=user_question)
                    return jsonify({"response": response}), 200
                except Exception as final_e:
                    return jsonify({"error": f"Unable to process with available repository data: {str(final_e)}"}), 500
        
        return jsonify({"error": f"Error processing your question: {str(e)}"}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "message": "Service is running"}), 200

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5002))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", debug=debug, port=port)