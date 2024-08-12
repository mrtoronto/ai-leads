let socket;

function initializeSocket() {
	const options = {
		debug: true,
		path: '/socket.io',
		transports: ['websocket'],
		upgrade: true,
	};

	socket = io(options);

	socket.on('connect', () => {
		socket.emit('connect_user', { 'user_id': window.user_id });
	});

	socket.on('disconnect', (reason) => {
		console.log('Socket disconnected:', reason);
	});
}

initializeSocket();

export { socket };
