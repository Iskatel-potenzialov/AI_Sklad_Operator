import { useState, useEffect, useRef } from 'react';
import { RunInput } from './components/RunInput';
import { AnswerPanel } from './components/AnswerPanel';
import { ExecutionLog } from './components/ExecutionLog';
import { ActionApproval } from './components/ActionApproval';
import Admin from './pages/Admin';
import type { SSEEvent } from './types';

export default function App() {
  // Простой роутинг: /admin → отдельная страница
  if (window.location.pathname === '/admin') {
    return <Admin />;
  }

  const [request, setRequest] = useState('');
  const [events, setEvents] = useState<SSEEvent[]>([]);
  const [answer, setAnswer] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [pendingAction, setPendingAction] = useState<any>(null);
  const [currentRunId, setCurrentRunId] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  const handleRun = async () => {
    if (!request.trim() || isRunning) return;

    setIsRunning(true);
    setEvents([]);
    setAnswer('');
    setPendingAction(null);

    try {
      const response = await fetch('http://localhost:8000/api/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ request: request.trim() }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const { run_id } = await response.json();
      setCurrentRunId(run_id);

      const eventSource = new EventSource(`http://localhost:8000/api/run/${run_id}/events`);
      eventSourceRef.current = eventSource;

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setEvents((prev) => [...prev, data]);

          if (data.type === 'assistant_message' && data.content) {
            setAnswer(data.content);
          }

          if (data.type === 'action_pending' && data.action) {
            setPendingAction(data.action);
          }

          if (data.type === 'run_finished') {
            setIsRunning(false);
            eventSource.close();
          }

          if (data.type === 'error') {
            setIsRunning(false);
            setAnswer(`Ошибка: ${data.message}`);
            eventSource.close();
          }
        } catch (error) {
          console.error('Error parsing SSE event:', error);
        }
      };

      eventSource.onerror = (error) => {
        console.error('SSE error:', error);
        setIsRunning(false);
        eventSource.close();
      };
    } catch (error) {
      console.error('Error starting run:', error);
      setIsRunning(false);
      setAnswer(`Ошибка запуска: ${error}`);
    }
  };

  const handleStop = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }
    setIsRunning(false);
  };

  const handleApprove = async (approved: boolean) => {
    if (!currentRunId) return;

    try {
      const response = await fetch(`http://localhost:8000/api/run/${currentRunId}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ approved }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      setPendingAction(null);
    } catch (error) {
      console.error('Error approving action:', error);
    }
  };

  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  return (
    <div className="min-h-screen bg-slate-900 text-white">
      <div className="container mx-auto px-4 py-8">
        <header className="mb-8 flex items-start justify-between">
          <div className="flex-1">
            <h1 className="text-4xl font-bold text-center mb-2">
              🏪 AI-оператор склада канцелярии
            </h1>
            <p className="text-center text-slate-400">
              Интеллектуальное управление складом с AI-анализом
            </p>
          </div>
          <a
            href="/admin"
            className="px-3 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-sm whitespace-nowrap"
          >
            Admin
          </a>
        </header>

        <main className="max-w-6xl mx-auto space-y-6">
          <RunInput
            value={request}
            onChange={setRequest}
            onRun={handleRun}
            onStop={handleStop}
            isRunning={isRunning}
          />

          {pendingAction && (
            <ActionApproval
              action={pendingAction}
              onApprove={() => handleApprove(true)}
              onReject={() => handleApprove(false)}
            />
          )}

          <AnswerPanel answer={answer} isRunning={isRunning} />

          <ExecutionLog events={events} />
        </main>

        <footer className="mt-12 text-center text-slate-500 text-sm">
          <p>AI-оператор склада канцелярии v0.8.0</p>
        </footer>
      </div>
    </div>
  );
}