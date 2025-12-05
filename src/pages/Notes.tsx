import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Note, notesAPI } from '../services/api';
import { NoteForm } from '../components/NoteForm';
import './Notes.css';

export const Notes: React.FC = () => {
  const [notes, setNotes] = useState<Note[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [selectedNote, setSelectedNote] = useState<Note | null>(null);
  const [summarizing, setSummarizing] = useState<number | null>(null);
  const { logout, user } = useAuth();

  useEffect(() => {
    loadNotes();
  }, []);

  const loadNotes = async () => {
    try {
      setLoading(true);
      const data = await notesAPI.getAll();
      setNotes(data);
    } catch (error: any) {
      console.error('Failed to load notes:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to load notes';
      console.error('Error details:', errorMessage);
      // Don't show alert if it's an auth error (will be handled by interceptor)
      if (error.response?.status !== 401) {
        alert(`Failed to load notes: ${errorMessage}`);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCreateNote = async (noteData: { title: string; content: string; image_url?: string }) => {
    try {
      await notesAPI.create(noteData);
      setShowForm(false);
      loadNotes();
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to create note');
    }
  };

  const handleDeleteNote = async (id: number) => {
    if (!confirm('Are you sure you want to delete this note?')) {
      return;
    }

    try {
      await notesAPI.delete(id);
      loadNotes();
      if (selectedNote?.id === id) {
        setSelectedNote(null);
      }
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to delete note');
    }
  };

  const handleSummarize = async (noteId: number) => {
    try {
      setSummarizing(noteId);
      const updatedNote = await notesAPI.summarize(noteId);
      setNotes(notes.map(n => n.id === noteId ? updatedNote : n));
      if (selectedNote?.id === noteId) {
        setSelectedNote(updatedNote);
      }
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to generate summary');
    } finally {
      setSummarizing(null);
    }
  };

  if (loading) {
    return (
      <div className="notes-container">
        <div className="loading">Loading notes...</div>
      </div>
    );
  }

  return (
    <div className="notes-container">
      <header className="notes-header">
        <h1>My Notes</h1>
        <div className="header-actions">
          <span className="user-email">{user?.email}</span>
          <button onClick={() => setShowForm(!showForm)} className="new-note-button">
            {showForm ? 'Cancel' : '+ New Note'}
          </button>
          <button onClick={logout} className="logout-button">
            Logout
          </button>
        </div>
      </header>

      {showForm && (
        <div className="form-section">
          <NoteForm
            onSubmit={handleCreateNote}
            onCancel={() => setShowForm(false)}
          />
        </div>
      )}

      <div className="notes-layout">
        <div className="notes-list">
          {notes.length === 0 ? (
            <div className="empty-state">
              <p>No notes yet. Create your first note!</p>
            </div>
          ) : (
            notes.map((note) => (
              <div
                key={note.id}
                className={`note-card ${selectedNote?.id === note.id ? 'selected' : ''}`}
                onClick={() => setSelectedNote(note)}
              >
                <h3>{note.title}</h3>
                <p className="note-preview">
                  {note.content.substring(0, 100)}
                  {note.content.length > 100 ? '...' : ''}
                </p>
                {note.image_url && (
                  <div className="note-image-indicator">📷 Image attached</div>
                )}
                {note.summary && (
                  <div className="note-summary-indicator">✨ Has summary</div>
                )}
                <div className="note-date">
                  {new Date(note.created_at).toLocaleDateString()}
                </div>
              </div>
            ))
          )}
        </div>

        {selectedNote && (
          <div className="note-detail">
            <div className="note-detail-header">
              <h2>{selectedNote.title}</h2>
              <button
                onClick={() => handleDeleteNote(selectedNote.id)}
                className="delete-button"
              >
                Delete
              </button>
            </div>

            {selectedNote.image_url && (
              <div className="note-image">
                <img src={selectedNote.image_url} alt="Note attachment" />
              </div>
            )}

            <div className="note-content">
              <p>{selectedNote.content}</p>
            </div>

            <div className="note-actions">
              <button
                onClick={() => handleSummarize(selectedNote.id)}
                disabled={summarizing === selectedNote.id}
                className="summarize-button"
              >
                {summarizing === selectedNote.id
                  ? 'Generating...'
                  : selectedNote.summary
                  ? 'Regenerate Summary'
                  : 'Generate Summary'}
              </button>
            </div>

            {selectedNote.summary && (
              <div className="note-summary">
                <h3>Summary</h3>
                <p>{selectedNote.summary}</p>
              </div>
            )}

            <div className="note-meta">
              <p>Created: {new Date(selectedNote.created_at).toLocaleString()}</p>
              <p>Updated: {new Date(selectedNote.updated_at).toLocaleString()}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

