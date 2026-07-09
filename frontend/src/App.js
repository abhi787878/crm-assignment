import React, { useState } from 'react';

export default function App() {
  const [chatInput, setChatInput] = useState('');
  const [loading, setLoading] = useState(false);

  
  const [chatHistory, setChatHistory] = useState([
    { role: 'ai', text: 'Log interaction details, or ask me questions about your past meetings!' }
  ]);

  const [formData, setFormData] = useState({
    hcp_name: '', interaction_type: 'Meeting', interaction_date: '',
    interaction_time: '', attendees: '', topics_discussed: '',
    materials_shared: '', samples_distributed: '', sentiment: 'Neutral',
    outcomes: '', next_steps: ''
  });

  const handleInputChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleAILog = async () => {
    if (!chatInput.trim()) return;

    // Add user message to UI immediately
    const userMsg = { role: 'user', text: chatInput };
    setChatHistory(prev => [...prev, userMsg]);
    setChatInput('');
    setLoading(true);

    try {
      const response = await fetch("http://127.0.0.1:8000/api/interaction/process", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: userMsg.text })
      });

      if (response.ok) {
        const data = await response.json();

        // Add AI response to chat
        setChatHistory(prev => [...prev, { role: 'ai', text: data.message }]);

        // Only fill form if the AI was logging a meeting
        if (data.action_type === 'log') {
          setFormData({
            hcp_name: data.interaction_data.hcp_name || '',
            interaction_type: data.interaction_data.interaction_type || 'Meeting',
            interaction_date: data.interaction_data.interaction_date || '',
            interaction_time: data.interaction_data.interaction_time || '',
            attendees: data.interaction_data.attendees || '',
            topics_discussed: data.interaction_data.topics_discussed || '',
            materials_shared: data.interaction_data.materials_shared || '',
            samples_distributed: data.interaction_data.samples_distributed || '',
            sentiment: data.interaction_data.sentiment || 'Neutral',
            outcomes: data.interaction_data.outcomes || '',
            next_steps: data.interaction_data.next_steps || ''
          });
        }
      } else {
        alert("Server Error");
      }
    } catch (error) {
      alert("Failed to connect to backend.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-4 md:p-8 font-sans">
      <div className="max-w-7xl mx-auto flex flex-col lg:flex-row gap-6">

        {/* LEFT PANEL: The Form */}
        <div className="flex-1 bg-white shadow-md rounded-lg p-6">
          <h2 className="text-2xl font-bold text-gray-800 border-b pb-4 mb-6">Log HCP Interaction</h2>
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div><label className="block text-sm text-gray-600 mb-1">HCP Name</label><input name="hcp_name" value={formData.hcp_name} onChange={handleInputChange} className="w-full border rounded p-2 text-sm" /></div>
              <div><label className="block text-sm text-gray-600 mb-1">Interaction Type</label><select name="interaction_type" value={formData.interaction_type} onChange={handleInputChange} className="w-full border rounded p-2 text-sm"><option>Meeting</option><option>Video Call</option><option>Phone</option><option>Email</option></select></div>
              <div><label className="block text-sm text-gray-600 mb-1">Date</label><input name="interaction_date" type="date" value={formData.interaction_date} onChange={handleInputChange} className="w-full border rounded p-2 text-sm" /></div>
              <div><label className="block text-sm text-gray-600 mb-1">Time</label><input name="interaction_time" type="time" value={formData.interaction_time} onChange={handleInputChange} className="w-full border rounded p-2 text-sm" /></div>
            </div>
            <div><label className="block text-sm text-gray-600 mb-1">Attendees</label><input name="attendees" value={formData.attendees} onChange={handleInputChange} className="w-full border rounded p-2 text-sm" /></div>
            <div><label className="block text-sm text-gray-600 mb-1">Topics Discussed</label><textarea name="topics_discussed" value={formData.topics_discussed} onChange={handleInputChange} rows={3} className="w-full border rounded p-2 text-sm" /></div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div><label className="block text-sm text-gray-600 mb-1">Materials Shared</label><input name="materials_shared" value={formData.materials_shared} onChange={handleInputChange} className="w-full border rounded p-2 text-sm" /></div>
              <div><label className="block text-sm text-gray-600 mb-1">Samples Distributed</label><input name="samples_distributed" value={formData.samples_distributed} onChange={handleInputChange} className="w-full border rounded p-2 text-sm" /></div>
            </div>
            <div><label className="block text-sm text-gray-600 mb-1">Observed/Inferred Sentiment</label><div className="flex gap-4">{['Positive', 'Neutral', 'Negative'].map(mood => (<label key={mood} className="flex items-center gap-1 text-sm"><input type="radio" name="sentiment" value={mood} checked={formData.sentiment === mood} onChange={handleInputChange} /> {mood}</label>))}</div></div>
            <div><label className="block text-sm text-gray-600 mb-1">Outcomes</label><textarea name="outcomes" value={formData.outcomes} onChange={handleInputChange} rows={2} className="w-full border rounded p-2 text-sm" /></div>
            <div><label className="block text-sm text-gray-600 mb-1">Follow-up Actions</label><textarea name="next_steps" value={formData.next_steps} onChange={handleInputChange} rows={2} className="w-full border rounded p-2 text-sm" /></div>
          </div>
        </div>

        {/* RIGHT PANEL: Chat Messaging UI */}
        <div className="w-full lg:w-96 bg-white shadow-md rounded-lg flex flex-col h-[700px] lg:h-auto">
          <div className="bg-blue-50 p-4 border-b rounded-t-lg flex items-center gap-2 text-blue-800 font-semibold">
            <span>🤖 Multi-Agent AI</span>
          </div>

          <div className="flex-1 p-4 overflow-y-auto bg-gray-50 flex flex-col gap-3">
            {chatHistory.map((msg, idx) => (
              <div key={idx} className={`p-3 rounded-lg text-sm max-w-[85%] ${msg.role === 'ai' ? 'bg-white border shadow-sm text-gray-700 self-start' : 'bg-blue-600 text-white self-end'}`}>
                {msg.text}
              </div>
            ))}
            {loading && (
              <div className="text-blue-600 text-sm animate-pulse self-start ml-1">
                Routing request...
              </div>
            )}
          </div>

          <div className="p-4 border-t bg-white flex gap-2">
            <input
              className="flex-1 border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
              placeholder="Ask a question or log a meeting..."
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAILog()}
            />
            <button
              onClick={handleAILog}
              disabled={loading}
              className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg text-sm font-medium"
            >
              Send
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}