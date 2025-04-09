// Wait for the DOM to load
document.addEventListener("DOMContentLoaded", () => {
    const repoInput = document.getElementById("repoInput");
    const repoInputButton = document.getElementById("repoInputButton");
    const userInput = document.getElementById("userInput");
    const sendButton = document.getElementById("sendButton");
    const messagesContainer = document.getElementById("messages");

    // Function to add messages to the chat area
    const addMessage = (sender, message) => {
        const messageElement = document.createElement("div");
        messageElement.className = sender === "user" ? "user-message" : "bot-message";
        messageElement.innerText = message;
        messagesContainer.appendChild(messageElement);
        messagesContainer.scrollTop = messagesContainer.scrollHeight; // Scroll to the bottom
    };

    // Fetch repository data from Flask
    const fetchRepoData = async () => {
        const repoUrl = repoInput.value.trim();
        if (!repoUrl) {
            addMessage('bot', 'Please enter a valid GitHub repository URL.');
            return;
        }

        try {
            const response = await fetch('http://127.0.0.1:5002/fetch_repo', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ repo_url: repoUrl }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                addMessage('bot', `Error: ${errorData.error}`);
                return;
            }

            const data = await response.json();
            addMessage('bot', 'Repository data fetched successfully!');
            addMessage('bot', `README:\n${data.readme}\n\nStructure:\n${data.structure}\n\nFile Contents:\n${data.file_contents}`);
        } catch (error) {
            console.error("Error fetching repo data:", error);
            addMessage('bot', 'An error occurred while fetching the repository data.');
        }
    };

    // Ask a question to the chatbot
    const askQuestion = async () => {
        const userMessage = userInput.value.trim();
        if (!userMessage) {
            addMessage('bot', 'Please enter a question.');
            return;
        }

        addMessage('user', userMessage);
        userInput.value = ""; // Clear input field

        try {
            const response = await fetch('http://127.0.0.1:5002/ask_question', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question: userMessage }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                addMessage('bot', `Error: ${errorData.error}`);
                return;
            }

            const data = await response.json();
            addMessage('bot', data.answer);
        } catch (error) {
            console.error("Error asking question:", error);
            addMessage('bot', 'An error occurred while asking the question.');
        }
    };

    // Event listeners
    repoInputButton.addEventListener("click", fetchRepoData);
    sendButton.addEventListener("click", askQuestion);

    // Optional: Allow pressing Enter to send a question
    userInput.addEventListener("keypress", (event) => {
        if (event.key === "Enter") {
            askQuestion();
        }
    });
});
