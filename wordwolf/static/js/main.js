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
// IDではなくクラスで取得するように変更（複数箇所のリストを更新するため）
const playerLists = document.querySelectorAll('.player-list-container');


let startModal = null; // モーダルインスタンスを保持
let voteProposalModal = null; // 投票提案モーダル

const voteProposalModalEl = document.getElementById('voteProposalModal');
if (voteProposalModalEl) {
    voteProposalModal = new bootstrap.Modal(voteProposalModalEl);
    
    // 同意ボタン
    document.getElementById('proposal-agree-btn').addEventListener('click', () => {
        socket.send(JSON.stringify({
            'type': 'respond_vote_proposal',
            'agree': true
        }));
        // 待機表示に切り替え
        document.querySelector('#voteProposalModal .d-flex').classList.add('d-none');
        document.getElementById('proposal-waiting-msg').classList.remove('d-none');
    });

    // 拒否ボタン
    document.getElementById('proposal-reject-btn').addEventListener('click', () => {
        socket.send(JSON.stringify({
            'type': 'respond_vote_proposal',
            'agree': false
        }));
        voteProposalModal.hide();
    });
}


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
        
        // すべてのプレイヤーリスト（PC用・スマホ用）を更新
        playerLists.forEach(list => {
            list.innerHTML = '';
            info.members.forEach(member => {
                const li = document.createElement('li');
                li.textContent = member;
                li.className = 'list-group-item bg-transparent text-white'; // スタイル調整
                if (member === userName) {
                    li.classList.add('fw-bold', 'text-accent');
                    li.innerHTML += ' <span class="badge bg-secondary ms-2">YOU</span>';
                }
                list.appendChild(li);
            });
        });
        
        // --- 変更: モーダル表示と待機処理 ---
        const modalWord = document.getElementById('modal-word-display');
        const modalRole = document.getElementById('modal-role-display');
        if (modalWord) modalWord.textContent = info.my_word;
        if (modalRole) modalRole.textContent = (info.role === 'wolf') ? '人狼' : '市民';

        // 確認エリアを表示、待機エリアを隠す（リセット）
        // ※ 既に議論が始まっている場合はモーダルを出さない制御が必要だが、
        // 下記の「ステータスに基づく復元処理」で制御するため、ここではDOM要素の取得のみ行う
        const confirmArea = document.getElementById('confirmation-area');
        const waitingArea = document.getElementById('waiting-area');
        if (confirmArea) confirmArea.classList.remove('d-none');
        if (waitingArea) waitingArea.classList.add('d-none');

        /* 
        const startModalEl = document.getElementById('startModal');
        if (startModalEl) {
            startModal = new bootstrap.Modal(startModalEl);
            startModal.show();
        } 
        */

        // 議論時間は後で使うために保持しておく
        window.discussionDuration = info.discussion_time * 60; 
        // メンバー情報も保持しておく（投票用）
        window.gameMembers = info.members;

        // --- チャット履歴の復元 ---
        if (info.chat_history && info.chat_history.length > 0) {
            info.chat_history.forEach(chatData => {
                const div = document.createElement('div');
                div.className = 'chat-message';
                
                if (chatData.username === userName) {
                    div.classList.add('my-message');
                    div.textContent = chatData.message;
                } else {
                    div.classList.add('other-message');
                    const userSpan = document.createElement('span');
                    userSpan.className = 'chat-username';
                    userSpan.textContent = chatData.username;
                    div.appendChild(userSpan);
                    div.appendChild(document.createTextNode(chatData.message));
                }
                chatWindow.appendChild(div);
            });
            chatWindow.scrollTop = chatWindow.scrollHeight;
        }

        // --- ステータスに基づく復元処理 ---
        const startModalEl = document.getElementById('startModal');
        if (startModalEl) {
             startModal = new bootstrap.Modal(startModalEl);
        }

        if (info.phase === 'confirming') {
            // お題確認・待機中（デフォルト）
            topicText.textContent = "待機中...";
            if (startModal) startModal.show();

        } else if (info.phase === 'discussing') {
            // 議論中
            topicText.textContent = "議論中";
            if (startModal) startModal.hide(); // モーダルを隠す

            // 強制投票ボタンを表示
            const forceBtn = document.getElementById('force-vote-btn');
            if (forceBtn) forceBtn.classList.remove('d-none');

            // タイマー開始 (残り時間で)
            if (info.remaining_seconds > 0) {
                startTimer(info.remaining_seconds, () => {
                    alert('議論終了！投票に移ります。');
                    createVoteUI(window.gameMembers || []); 
                    if (forceBtn) forceBtn.classList.add('d-none');
                });
            }

        } else if (info.phase === 'discussing_finished') {
             // 議論時間終了後（投票待ち状態）
             if (startModal) startModal.hide();
             topicText.textContent = "議論終了";
             createVoteUI(window.gameMembers || []);
             const forceBtn = document.getElementById('force-vote-btn');
             if (forceBtn) forceBtn.classList.add('d-none');
        
        } else if (info.phase === 'voting') {
            // 投票中
            if (startModal) startModal.hide();
            topicText.textContent = "投票中";
            createVoteUI(window.gameMembers || []);
            const forceBtn = document.getElementById('force-vote-btn');
            if (forceBtn) forceBtn.classList.add('d-none');
        }

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
                // 自動終了時の処理（もしボタンより先に終わった場合）
                alert('議論終了！投票に移ります。');
                createVoteUI(window.gameMembers || []); 
                
                // 強制投票ボタンを隠す
                const forceBtn = document.getElementById('force-vote-btn');
                if (forceBtn) forceBtn.classList.add('d-none');
            });
        }
        
        // 議論中になったら強制投票ボタンを表示
        const forceBtn = document.getElementById('force-vote-btn');
        if (forceBtn) forceBtn.classList.remove('d-none');

    } else if (data.type === 'vote_proposal') {
        const requester = data.requester;
        const textEl = document.getElementById('proposal-text');
        const btnsDiv = document.querySelector('#voteProposalModal .d-flex');
        const waitDiv = document.getElementById('proposal-waiting-msg');
        
        if (requester === userName) {
            textEl.textContent = '投票への移行を提案しました';
            btnsDiv.classList.add('d-none');
            waitDiv.classList.remove('d-none');
        } else {
            textEl.textContent = `${requester} さんから投票への移行提案がありました`;
            btnsDiv.classList.remove('d-none');
            waitDiv.classList.add('d-none');
        }
        if (voteProposalModal) voteProposalModal.show();

    } else if (data.type === 'vote_proposal_rejected') {
        if (voteProposalModal) voteProposalModal.hide();
        alert(`誰かが提案を拒否したため、議論を続行します。`);

    } else if (data.type === 'start_vote_phase') {
        // 強制的に投票フェーズへ以降
        if (voteProposalModal) voteProposalModal.hide();
        stopTimer(); // タイマー停止
        alert('投票フェーズへ移行します。');
        createVoteUI(window.gameMembers || []);
        
        // ボタンはもういらない
        const forceBtn = document.getElementById('force-vote-btn');
        if (forceBtn) forceBtn.classList.add('d-none');

    } else if (data.type === 'chat_message') {
        const div = document.createElement('div');
        div.className = 'chat-message';
        
        if (data.username === userName) {
            div.classList.add('my-message');
            div.textContent = data.message;
        } else {
            div.classList.add('other-message');
            const userSpan = document.createElement('span');
            userSpan.className = 'chat-username';
            userSpan.textContent = data.username;
            div.appendChild(userSpan);
            div.appendChild(document.createTextNode(data.message));
        }
        
        chatWindow.appendChild(div);
        chatWindow.scrollTop = chatWindow.scrollHeight;
        
    } else if (data.type === 'vote_update') {
        console.log(`${data.username} voted.`);
        
    } else if (data.type === 'game_result') {
        const result = data.results;
        
        // モーダルの要素を取得
        const resultModalEl = document.getElementById('resultModal');
        const winnerEl = document.getElementById('result-winner');
        const wolfListEl = document.getElementById('result-wolf-list');
        const voteListEl = document.getElementById('result-votes-list');
        const backBtn = document.getElementById('back-to-lobby-btn');

        if (resultModalEl) {
            // 勝者表示
            if (winnerEl) winnerEl.textContent = result.winner;
            
            // 人狼表示
            if (wolfListEl) {
                wolfListEl.innerHTML = ''; // クリア
                result.wolves.forEach(name => {
                    const h3 = document.createElement('h3');
                    h3.className = 'fw-bold text-danger';
                    h3.textContent = name;
                    wolfListEl.appendChild(h3);
                });
            }

            // 得票状況表示
            if (voteListEl) {
                voteListEl.innerHTML = '';
                // 投票結果を見やすく整形 (例: "UserA (3票)")
                const sortedVotes = Object.entries(result.votes).sort((a, b) => b[1] - a[1]);
                const ul = document.createElement('ul');
                ul.className = 'list-unstyled text-start d-inline-block';
                
                if (sortedVotes.length === 0) {
                     ul.innerHTML = '<li>投票なし</li>';
                } else {
                    sortedVotes.forEach(([name, count]) => {
                        const li = document.createElement('li');
                        li.className = 'mb-1';
                        // 最多得票かどうかでスタイルを変える？
                        // 今回はシンプルにリスト表示
                        li.textContent = `${name}: ${count}票`;
                        ul.appendChild(li);
                    });
                }
                voteListEl.appendChild(ul);
            }

            // ロビーへ戻るボタン
            if (backBtn) {
                backBtn.onclick = () => {
                    window.location.href = '/wordwolf/lobby/';
                };
            }

            // モーダル表示
            const resultModal = new bootstrap.Modal(resultModalEl);
            resultModal.show();
        } else {
            // 万が一モーダルがない場合のフォールバック
            const msg = `勝者: ${result.winner}\n\n人狼: ${result.wolves.join(', ')}\n\nロビーに戻ります。`;
            alert(msg);
            window.location.href = '/wordwolf/lobby/';
        }
        
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

// 強制投票ボタンの処理
const forceVoteBtn = document.getElementById('force-vote-btn');
if (forceVoteBtn) {
    forceVoteBtn.addEventListener('click', () => {
        if(confirm('議論を終了して投票に移ることを提案しますか？\n（全員の同意が必要です）')) {
            socket.send(JSON.stringify({
                'type': 'request_vote_phase'
            }));
        }
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
