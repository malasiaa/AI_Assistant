import { useState, useRef, useEffect } from 'react'
import './App.css'

function App() {
  // Chat states
  const [input, setInput] = useState('')
  const [chat, setChat] = useState([])
  const [loading, setLoading] = useState(false)

  // Recording states
  const [isRecording, setIsRecording] = useState(false)
  const [status, setStatus] = useState('Idle')
  const mediaRecorderRef = useRef(null)
  const audioChunksRef = useRef([])

  // Device-selection states
  const [devices, setDevices] = useState([])
  const [selectedDeviceId, setSelectedDeviceId] = useState(null)
  const [showDeviceSelector, setShowDeviceSelector] = useState(false)

  // On mount: enumerate mics
  useEffect(() => {
    navigator.mediaDevices.enumerateDevices()
      .then(list => {
        const mics = list.filter(d => d.kind === 'audioinput')
        setDevices(mics)
        if (mics.length) setSelectedDeviceId(mics[0].deviceId)
      })
      .catch(err => console.error('Could not list devices:', err))
  }, [])

  // Send text to /chat
  const sendText = async (text) => {
    if (!text.trim()) return
    setChat(c => [...c, { from: 'user', message: text }])
    setLoading(true)
    setInput('')

    try {
      const res = await fetch('http://127.0.0.1:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      })
      const data = await res.json()
      setChat(c => [...c, { from: 'jarvis', message: data.response }])
      if (data.result?.content) {
        setChat(c => [...c, { from: 'jarvis', message: `🗒️ Note found: ${data.result.content} ` }])
      }
    } catch {
      setChat(c => [...c, { from: 'jarvis', message: '⚠️ Backend error.' }])
    } finally {
      setLoading(false)
    }
  }

  // Start recording with chosen device
  const startRecording = async () => {
    setStatus('Requesting mic…')
    try {
      const constraints = {
        audio: selectedDeviceId
          ? { deviceId: { exact: selectedDeviceId } }
          : true
      }
      const stream = await navigator.mediaDevices.getUserMedia(constraints)
      const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' })

      audioChunksRef.current = []
      recorder.ondataavailable = e => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data)
      }
      recorder.onstop = async () => {
        setStatus('Transcribing…')
        const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' })
        const form = new FormData()
        form.append('file', blob, 'recording.webm')

        // 1) send to /transcribe
        const tRes = await fetch('http://127.0.0.1:8000/transcribe', { method: 'POST', body: form })
        const tJson = await tRes.json()
        const transcript = tJson.text || ''
        setChat(c => [...c, { from: 'user', message: transcript }])

        // 2) send transcript to /chat
        await sendText(transcript)
        setStatus('Idle')
      }

      recorder.start()
      mediaRecorderRef.current = recorder
      setIsRecording(true)
      setStatus('Recording…')
    } catch (err) {
      console.error('Mic error:', err)
      setStatus('Mic error')
    }
  }

  const stopRecording = () => {
    mediaRecorderRef.current?.stop()
    setIsRecording(false)
  }

  return (
    <div className="App">
      <h1>Jarvis Assistant</h1>

      <div className="chat-box">
        {chat.map((e,i) => (
          <div key={i} className={e.from}>
            <strong>{e.from==='user'?'You':'Jarvis'}:</strong> {e.message}
          </div>
        ))}
        {loading && <div className="jarvis"><strong>Jarvis:</strong> Typing.....</div>}
      </div>

      {/* === Text controls === */}
      <div className="text-controls">
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key==='Enter' && sendText(input)}
          placeholder="Type a message…"
          disabled={loading || isRecording}
        />
        <button onClick={() => sendText(input)} disabled={loading || isRecording}>
          Send
        </button>
      </div>

      {/* === Audio controls underneath === */}
      <div className="audio-controls">
        <button
          className="toggle-mic"
          onClick={() => setShowDeviceSelector(v => !v)}
          title="Select mic"
        >🎛️</button>

        {showDeviceSelector && devices.length > 0 && (
          <select
            className="device-select"
            value={selectedDeviceId}
            onChange={e => setSelectedDeviceId(e.target.value)}
          >
            {devices.map(d => (
              <option key={d.deviceId} value={d.deviceId}>
                {d.label || d.deviceId}
              </option>
            ))}
          </select>
        )}

        <button
          className="record-btn"
          onClick={isRecording ? stopRecording : startRecording}
          disabled={loading}
        >
          {isRecording ? '⏹️ Stop Recording' : '🎤 Record Audio'}
        </button>
      </div>

      <p className="status">Status: {status}</p>
    </div>
  )
}

export default App