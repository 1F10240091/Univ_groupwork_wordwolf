import { startTimer, stopTimer } from './timer.js';

const roomId = JSON.parse(document.getElementById('room-id').textContent);
const userName = JSON.parse(document.getElementById('user-name').textContent);

const socket = new WebSocket(
    'ws://' + window.location.host + '/ws/room/' + roomId + '/'
);

const chatWindow = document.getElementById('chat-window');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-chat-btn');
const topicText = document.getElementById('topic-text');
const wordDisplay = document.getElementById('word-display');
const playerList = document.getElementById('player-list');

let startModal = null; // モーダルインスタンスを保持

// 投票UI作成関数
function createVoteUI(members) {
    const controls = document.querySelector('.game-controls');
    controls.innerHTML = '';
    
    const voteContainer = document.createElement('div');
    voteContainer.className = 'vote-container p-3 bg-light border-top';
    voteContainer.innerHTML = '<h4>投票の時間です。人狼だと思う人を選んでください。</h4>';
    
    const select = document.createElement('select');
    select.className = 'form-select mb-3';
    
    members.forEach(name => {
        if (name !== userName) {
            const option = document.createElement('option');
            option.value = name;
            option.textContent = name;
            select.appendChild(option);
        }
    });
    
    const voteBtn = document.createElement('button');
    voteBtn.className = 'btn btn-danger w-100';
    voteBtn.textContent = '投票する';
    
    voteBtn.onclick = () => {
        const target = select.value;
        if (target) {
            socket.send(JSON.stringify({
                'type': 'vote',
                'target': target
            }));
            voteContainer.innerHTML = '<h4>投票しました。結果を待っています...</h4>';
        }
    };
    
    voteContainer.appendChild(select);
    voteContainer.appendChild(voteBtn);
    controls.appendChild(voteContainer);
}

socket.onopen = function(e) {
    console.log('Connected to game socket');
    socket.send(JSON.stringify({ 'type': 'request_game_info' }));
};

socket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    
    if (data.type === 'game_info') {
        const info = data.data;
        
        // メイン画面への反映
        topicText.textContent = "待機中...";
        wordDisplay.textContent = info.my_word;
        
        playerList.innerHTML = '';
        info.members.forEach(member => {
            const li = document.createElement('li');
            li.textContent = member;
            li.className = 'list-group-item'; // 基本スタイル
            if (member === userName) {
                li.classList.add('fw-bold', 'text-accent');
                li.innerHTML += ' <span class="badge bg-secondary ms-2">YOU</span>';
            }
            playerList.appendChild(li);
        });
        
        // --- 変更: モーダル表示と待機処理 ---
        const modalWord = document.getElementById('modal-word-display');
        const modalRole = document.getElementById('modal-role-display');
        if (modalWord) modalWord.textContent = info.my_word;
        if (modalRole) modalRole.textContent = (info.role === 'wolf') ? '人狼' : '市民';

        // 確認エリアを表示、待機エリアを隠す（リセット）
        const confirmArea = document.getElementById('confirmation-area');
        const waitingArea = document.getElementById('waiting-area');
        if (confirmArea) confirmArea.classList.remove('d-none');
        if (waitingArea) waitingArea.classList.add('d-none');

        const startModalEl = document.getElementById('startModal');
        if (startModalEl) {
            startModal = new bootstrap.Modal(startModalEl);
            startModal.show();
        }

        // 議論時間は後で使うために保持しておく
        window.discussionDuration = info.discussion_time * 60; 
        // メンバー情報も保持しておく（投票用）
        window.gameMembers = info.members;

    } else if (data.type === 'confirmation_update') {
        // 誰かが「確認しました」を押した時の進捗更新
        const current = data.confirmed_count;
        const total = data.total_count;
        const percent = (current / total) * 100;
        
        const progressBar = document.getElementById('confirmation-progress');
        const statusText = document.getElementById('confirmation-status-text');
        
        if (progressBar) progressBar.style.width = percent + '%';
        if (statusText) statusText.textContent = `${current} / ${total} 人 完了`;

    } else if (data.type === 'start_discussion') {
        // 全員揃ったのでモーダルを閉じて開始！
        if (startModal) startModal.hide();
        
        topicText.textContent = "議論中";
        
        // タイマー開始
        if (window.discussionDuration) {
            startTimer(window.discussionDuration, () => {
                alert('議論終了！投票に移ります。');
                createVoteUI(window.gameMembers || []); 
            });
        }

    } else if (data.type === 'chat_message') {
        const p = document.createElement('p');
        p.innerHTML = `<strong>${data.username}:</strong> ${data.message}`;
        chatWindow.appendChild(p);
        chatWindow.scrollTop = chatWindow.scrollHeight;
        
    } else if (data.type === 'vote_update') {
        console.log(`${data.username} voted.`);
        
    } else if (data.type === 'game_result') {
        const result = data.results;
        const msg = `勝者: ${result.winner}\n\n人狼: ${result.wolves.join(', ')}\n\nロビーに戻ります。`;
        alert(msg);
        window.location.href = '/wordwolf/lobby/';
        
    } else if (data.type === 'room_dissolved') {
        alert('ルームが解散されました。');
        window.location.href = '/wordwolf/lobby/';
    }
};

// 「確認しました」ボタンの処理
const confirmBtn = document.getElementById('confirm-btn');
if (confirmBtn) {
    confirmBtn.addEventListener('click', () => {
        // UIを待機状態に切り替え
        const confirmArea = document.getElementById('confirmation-area');
        const waitingArea = document.getElementById('waiting-area');
        if (confirmArea) confirmArea.classList.add('d-none');
        if (waitingArea) waitingArea.classList.remove('d-none');
        
        // サーバーに通知
        socket.send(JSON.stringify({
            'type': 'confirm_start'
        }));
    });
}

// チャット送信処理
function sendChat() {
    const msg = chatInput.value;
    if (msg) {
        socket.send(JSON.stringify({
            'type': 'chat_message',
            'message': msg
        }));
        chatInput.value = '';
    }
}

if (sendBtn) {
    sendBtn.addEventListener('click', sendChat);
}
if (chatInput) {
    chatInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') sendChat();
    });
}

const exitBtn = document.getElementById('exit-room-btn');
if (exitBtn) {
    exitBtn.addEventListener('click', () => {
        if(confirm('本当に退出しますか？')) {
             window.location.href = '/wordwolf/lobby/';
        }
    });
}
