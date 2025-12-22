import { connectGameSocket } from './socket.js';

const gameData = JSON.parse(document.getElementById('game-data').textContent);


const gameSocket = connectGameSocket(gameData.roomId, (data) => {
    switch (data.type) {
        case 'chat_message': // チャットメッセージ
            displayChatMessage(data.sender_name, data.message);
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
        <span class="fw-bold text-primary">${name}</span>: 
        <span>${message}</span>
    `;

    chatLog.appendChild(messageElement);
}