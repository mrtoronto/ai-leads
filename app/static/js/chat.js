import { socket } from "./socket.js";

document.addEventListener('DOMContentLoaded', function() {
    if (window.is_auth && !window.is_admin) {
        initializeUserChat();
    }
});

function initializeUserChat() {
    const chatButton = document.createElement('div');
    chatButton.innerHTML = '<i class="fas fa-comments"></i>';
    chatButton.className = 'chat-button';
    document.body.appendChild(chatButton);

    const chatWindow = document.createElement('div');
    chatWindow.className = 'chat-window';
    chatWindow.style.display = 'none';
    chatWindow.innerHTML = `
        <div class="chat-header">
            <h3>Support</h3>
            <button class="close-chat">×</button>
        </div>
        <div class="chat-messages"></div>
        <div class="chat-input">
            <input type="text" placeholder="Type a message...">
            <button class="btn btn-primary"><i class="fas fa-arrow-right"></i></button>
        </div>
    `;
    document.body.appendChild(chatWindow);

    let currentChatId = null;

    chatButton.addEventListener('click', function() {
        if (chatWindow.style.display === 'none') {
            chatWindow.style.display = 'block';
            if (!currentChatId) {
                socket.emit('start_chat');
            } else {
                socket.emit('get_chat_messages', { chat_id: currentChatId });
            }
        } else {
            chatWindow.style.display = 'none';
        }
    });

    const closeButton = chatWindow.querySelector('.close-chat');
    closeButton.addEventListener('click', function() {
        chatWindow.style.display = 'none';
    });

    const sendButton = chatWindow.querySelector('.chat-input button');
    const messageInput = chatWindow.querySelector('.chat-input input');
    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    function sendMessage() {
        const message = messageInput.value.trim();
        if (message && currentChatId) {
            socket.emit('send_message', { chat_id: currentChatId, message: message });
            messageInput.value = '';
        }
    }

    socket.on('chat_started', function(data) {
        currentChatId = parseInt(data.chat_id);
        const initialMessage = "Welcome to our support chat! How can we assist you today? Please describe what you need help with, and our team will be happy to assist you.";
        socket.emit('send_message', { chat_id: currentChatId, message: initialMessage, is_admin: true });
    });

    socket.on('chat_messages', function(data) {
        const chatMessages = chatWindow.querySelector('.chat-messages');
        if (data.messages && data.messages.length > 0) {
            chatMessages.innerHTML = '';
            data.messages.forEach(function(msg) {
                displayMessage(msg);
            });
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    });

    socket.on('message_received', function(data) {
        console.log('message_received', data);
        if (parseInt(data.chat_id) === currentChatId) {
            displayMessage(data.message);
        }
    });

    function displayMessage(msg) {
        const chatMessages = chatWindow.querySelector('.chat-messages');
        const messageElement = document.createElement('div');
        messageElement.className = `message ${msg.is_admin ? 'admin' : 'user'}`;
        messageElement.textContent = msg.content;
        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    socket.emit('check_unresolved_chat');

    socket.on('unresolved_chat', function(data) {
        currentChatId = parseInt(data.chat_id);
        chatButton.classList.add('unresolved');
    });
}