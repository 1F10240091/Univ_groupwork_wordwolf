export function connectGameSocket(roomId, onMessageCallback) {
    const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
    const socket = new WebSocket(`${wsScheme}://${window.location.host}/ws/game/${roomId}/`);

    socket.onopen = () => {
        console.log("WebSocket接続成功: ルームID", roomId);
    };

    socket.onmessage = (e) => {
        const data = JSON.parse(e.data);
        console.log("受信メッセージ:", data);
        onMessageCallback(data);
    };

    return {
        send: (type, payload) => {
            if (socket.readyState === WebSocket.OPEN) {
                socket.send(JSON.stringify({ type, ...payload }));
            }
        }
    };
}