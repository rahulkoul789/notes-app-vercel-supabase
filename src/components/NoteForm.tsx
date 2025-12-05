import { useState, useRef } from 'react';
import { NoteCreate, uploadAPI } from '../services/api';
import './NoteForm.css';

interface NoteFormProps {
  onSubmit: (note: NoteCreate) => Promise<void>;
  onCancel?: () => void;
  initialData?: Partial<NoteCreate>;
  loading?: boolean;
}

export const NoteForm: React.FC<NoteFormProps> = ({
  onSubmit,
  onCancel,
  initialData,
  loading = false,
}) => {
  const [title, setTitle] = useState(initialData?.title || '');
  const [content, setContent] = useState(initialData?.content || '');
  const [imageUrl, setImageUrl] = useState(initialData?.image_url || '');
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    try {
      const response = await uploadAPI.uploadImage(file);
      setImageUrl(response.url);
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to upload image');
    } finally {
      setUploading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !content.trim()) {
      alert('Please fill in both title and content');
      return;
    }

    await onSubmit({
      title: title.trim(),
      content: content.trim(),
      image_url: imageUrl || undefined,
    });

    // Reset form if no initial data (new note)
    if (!initialData) {
      setTitle('');
      setContent('');
      setImageUrl('');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="note-form">
      <div className="form-group">
        <input
          type="text"
          placeholder="Note title..."
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="title-input"
        />
      </div>

      <div className="form-group">
        <textarea
          placeholder="Write your note here..."
          value={content}
          onChange={(e) => setContent(e.target.value)}
          className="content-textarea"
          rows={10}
        />
      </div>

      <div className="form-group">
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleImageUpload}
          style={{ display: 'none' }}
        />
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
          className="upload-button"
        >
          {uploading ? 'Uploading...' : imageUrl ? 'Change Image' : 'Upload Image'}
        </button>
        {imageUrl && (
          <div className="image-preview">
            <img src={imageUrl} alt="Preview" />
            <button
              type="button"
              onClick={() => setImageUrl('')}
              className="remove-image"
            >
              ×
            </button>
          </div>
        )}
      </div>

      <div className="form-actions">
        {onCancel && (
          <button type="button" onClick={onCancel} className="cancel-button">
            Cancel
          </button>
        )}
        <button type="submit" disabled={loading || uploading} className="submit-button">
          {loading ? 'Saving...' : 'Save Note'}
        </button>
      </div>
    </form>
  );
};

