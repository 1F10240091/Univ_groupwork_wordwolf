import { connectGameSocket } from './socket.js';

const gameData = JSON.parse(document.getElementById('game-data').textContent);


const gameSocket = connectGameSocket(gameData.roomId, (data) => {
    switch (data.type) {
        case 'chat_log':
            data.messages.forEach(msg => {
                displayChatMessage(msg.sender_name, msg.message);
            });
            break;

        case 'chat_message':
            displayChatMessage(data.sender_name, data.message);
            break;
        
        case 'system_message':
            displayChatMessage(null, data.message);
            break;
        
        case 'member_list':
            displayMembers(data.members);
            break;
        
        default:
            console.log("未定義のメッセージを受信:", data);
    }
});

document.querySelector('#send-chat-btn').onclick = () => {
    const input = document.querySelector('#chat-input');
    if (input.value.trim() !== "") {
        gameSocket.send('chat', { 'message': input.value });
        input.value = '';
    }
};

function displayChatMessage(name, message) {
    const chatLog = document.querySelector('#chat-window');
    if (!chatLog) return;

    const messageElement = document.createElement('div');

    messageElement.innerHTML = `
        <span class="fw-bold text-primary">${name ?? "システム"}</span>: 
        <span>${message}</span>
    `;

    chatLog.appendChild(messageElement);
}

function displayMembers(members) {
    const memberListContainer = document.querySelector('#member-list');
    if (!memberListContainer) return;

    memberListContainer.innerHTML = '';
    members.forEach(username => {
        const li = document.createElement('li');
        li.className = 'list-group-item';
        li.textContent = username;
        memberListContainer.appendChild(li);
    });
}