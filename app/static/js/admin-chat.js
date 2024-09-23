import { socket } from "./socket.js";

let currentAdminChatId = null;

document.addEventListener('DOMContentLoaded', function() {
    const unresolvedChatsList = document.getElementById('unresolved-chats-list');
    const adminChatWindow = document.getElementById('admin-chat-window');
    const chatMessages = adminChatWindow.querySelector('.chat-messages');
    const chatInput = adminChatWindow.querySelector('.chat-input input');
    const sendButton = adminChatWindow.querySelector('.chat-input button');
    const resolveChatBtn = document.getElementById('resolve-chat-btn');

    // Join the admin room
    socket.emit('join_admin_room');

    // Request unresolved chats
    console.log('get_unresolved_chats');
    socket.emit('get_unresolved_chats');

    // Listen for unresolved chats
    socket.on('unresolved_chats', function(data) {
        console.log('unresolved_chats', data);
        unresolvedChatsList.innerHTML = '';
        data.chats.forEach(function(chat) {
            const chatElement = document.createElement('div');
            chatElement.className = 'unresolved-chat';
            chatElement.innerHTML = `
                <h4>Chat #${chat.id}</h4>
                <p>User ID: ${chat.user_id}</p>
                <button class="btn btn-primary view-chat" data-chat-id="${chat.id}">View Chat</button>
            `;
            unresolvedChatsList.appendChild(chatElement);
        });
    });

    // Handle viewing a specific chat
    unresolvedChatsList.addEventListener('click', function(e) {
        if (e.target.classList.contains('view-chat')) {
            const chatId = e.target.getAttribute('data-chat-id');
            currentAdminChatId = parseInt(chatId);
            socket.emit('get_chat_messages', { chat_id: chatId });
            adminChatWindow.style.display = 'block';
        }
    });

    // Send admin message
    sendButton.addEventListener('click', sendAdminMessage);
    chatInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendAdminMessage();
        }
    });

    function sendAdminMessage() {
        const message = chatInput.value.trim();
        if (message && currentAdminChatId) {
            socket.emit('send_admin_message', { chat_id: currentAdminChatId, message: message });
            chatInput.value = '';
        }
    }

    // Listen for chat messages
    socket.on('chat_messages', function(data) {
        chatMessages.innerHTML = '';
        data.messages.forEach(function(msg) {
            const messageElement = document.createElement('div');
            messageElement.className = `message ${msg.is_admin ? 'admin' : 'user'}`;
            messageElement.textContent = msg.content;
            chatMessages.appendChild(messageElement);
        });
        chatMessages.scrollTop = chatMessages.scrollHeight;
    });

    // Listen for new messages
    socket.on('message_received', function(data) {
        console.log('message_received', data);
        if (currentAdminChatId === parseInt(data.chat_id)) {
            const messageElement = document.createElement('div');
            messageElement.className = `message ${data.message.is_admin ? 'admin' : 'user'}`;
            messageElement.textContent = data.message.content;
            chatMessages.appendChild(messageElement);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    });

    // Resolve chat
    resolveChatBtn.addEventListener('click', function() {
        if (currentAdminChatId) {
            socket.emit('resolve_chat', { chat_id: currentAdminChatId });
        }
    });

    // Listen for chat resolution
    socket.on('chat_resolved', function(data) {
        if (data.chat_id === currentAdminChatId) {
            adminChatWindow.style.display = 'none';
            currentAdminChatId = null;
            socket.emit('get_unresolved_chats');
        }
    });

    // Listen for new unresolved chats
    socket.on('new_unresolved_chat', function() {
        socket.emit('get_unresolved_chats');
    });
});