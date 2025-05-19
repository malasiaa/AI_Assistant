import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'

function App() {
  const [input, setInput] = useState('');
  const [chat, setChat] = useState([]);
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim()) return;

    setChat([...chat, { from: 'user', message: input }]);
    setInput('');
    setLoading(true);

    const res = await fetch('http://localhost:8000/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: input }),
    });
    const data = await res.json();

    setChat(c => [...c, { from: 'jarvis', message: data.response }]);

    if (data.result) {
      setChat(c => [...c, { from: 'jarvis', message: `🗒️ Note: ${data.result.content}` }]);
    }

    setLoading(false);
  };

  return (
    <div className="App">
      <h1>Jarvis Assistant</h1>
      <div className="chat-box">
        {chat.map((entry, i) => (
          <div key={i} className={entry.from}>
            <strong>{entry.from === 'user' ? 'You' : 'Jarvis'}:</strong> {entry.message}
          </div>
        ))}
        {loading && <div className="jarvis">Jarvis: Typing...</div>}
      </div>
      <div className="input-box">
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && sendMessage()}
          placeholder="Say something..."
        />
        <button onClick={sendMessage}>Send</button>
      </div>
    </div>
  );
}

export default App;
