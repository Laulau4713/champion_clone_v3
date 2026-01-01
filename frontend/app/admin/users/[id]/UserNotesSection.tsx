"use client";

import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  StickyNote,
  Plus,
  Pin,
  PinOff,
  Trash2,
  Edit3,
  Save,
  X,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { adminAPI } from '@/lib/admin-api';
import { cn } from '@/lib/utils';

interface Note {
  id: number;
  content: string;
  is_pinned: boolean;
  admin_id: number;
  created_at: string;
  updated_at?: string;
}

interface UserNotesSectionProps {
  userId: number;
  initialNotes: Note[];
}

export default function UserNotesSection({ userId, initialNotes }: UserNotesSectionProps) {
  const [notes, setNotes] = useState<Note[]>(initialNotes);
  const [newNote, setNewNote] = useState('');
  const [isAdding, setIsAdding] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editContent, setEditContent] = useState('');
  const [loading, setLoading] = useState(false);

  const fetchNotes = useCallback(async () => {
    try {
      const res = await adminAPI.getUserNotes(userId);
      setNotes(res.data.items);
    } catch (error) {
      console.error('Error fetching notes:', error);
    }
  }, [userId]);

  const addNote = async () => {
    if (!newNote.trim()) return;
    setLoading(true);
    try {
      await adminAPI.createUserNote(userId, { content: newNote.trim() });
      await fetchNotes();
      setNewNote('');
      setIsAdding(false);
    } catch (error) {
      console.error('Error adding note:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateNote = async (noteId: number, content: string, is_pinned?: boolean) => {
    setLoading(true);
    try {
      await adminAPI.updateNote(noteId, { content, is_pinned });
      await fetchNotes();
      setEditingId(null);
    } catch (error) {
      console.error('Error updating note:', error);
    } finally {
      setLoading(false);
    }
  };

  const togglePin = async (note: Note) => {
    await updateNote(note.id, note.content, !note.is_pinned);
  };

  const deleteNote = async (noteId: number) => {
    if (!confirm('Supprimer cette note ?')) return;
    setLoading(true);
    try {
      await adminAPI.deleteNote(noteId);
      await fetchNotes();
    } catch (error) {
      console.error('Error deleting note:', error);
    } finally {
      setLoading(false);
    }
  };

  const startEdit = (note: Note) => {
    setEditingId(note.id);
    setEditContent(note.content);
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditContent('');
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // Sort notes: pinned first, then by date
  const sortedNotes = [...notes].sort((a, b) => {
    if (a.is_pinned && !b.is_pinned) return -1;
    if (!a.is_pinned && b.is_pinned) return 1;
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
  });

  return (
    <Card className="glass border-white/10">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <StickyNote className="h-5 w-5 text-yellow-400" />
            Notes Admin ({notes.length})
          </CardTitle>
          {!isAdding && (
            <Button
              size="sm"
              onClick={() => setIsAdding(true)}
              className="bg-primary/20 hover:bg-primary/30"
            >
              <Plus className="h-4 w-4 mr-1" />
              Ajouter
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Add Note Form */}
        <AnimatePresence>
          {isAdding && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="overflow-hidden"
            >
              <div className="p-4 rounded-lg bg-white/5 border border-white/10 space-y-3">
                <textarea
                  value={newNote}
                  onChange={(e) => setNewNote(e.target.value)}
                  placeholder="Ajouter une note..."
                  className="w-full h-24 px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary/50 resize-none"
                  autoFocus
                />
                <div className="flex gap-2 justify-end">
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => {
                      setIsAdding(false);
                      setNewNote('');
                    }}
                    disabled={loading}
                  >
                    <X className="h-4 w-4 mr-1" />
                    Annuler
                  </Button>
                  <Button
                    size="sm"
                    onClick={addNote}
                    disabled={loading || !newNote.trim()}
                  >
                    <Save className="h-4 w-4 mr-1" />
                    Enregistrer
                  </Button>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Notes List */}
        {notes.length === 0 ? (
          <p className="text-muted-foreground text-center py-4">
            Aucune note pour cet utilisateur
          </p>
        ) : (
          <div className="space-y-3">
            {sortedNotes.map((note, index) => (
              <motion.div
                key={note.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                className={cn(
                  "p-4 rounded-lg border transition-colors",
                  note.is_pinned
                    ? "bg-yellow-500/10 border-yellow-500/30"
                    : "bg-white/5 border-white/10"
                )}
              >
                {editingId === note.id ? (
                  <div className="space-y-3">
                    <textarea
                      value={editContent}
                      onChange={(e) => setEditContent(e.target.value)}
                      className="w-full h-24 px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary/50 resize-none"
                      autoFocus
                    />
                    <div className="flex gap-2 justify-end">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={cancelEdit}
                        disabled={loading}
                      >
                        <X className="h-4 w-4 mr-1" />
                        Annuler
                      </Button>
                      <Button
                        size="sm"
                        onClick={() => updateNote(note.id, editContent)}
                        disabled={loading || !editContent.trim()}
                      >
                        <Save className="h-4 w-4 mr-1" />
                        Sauvegarder
                      </Button>
                    </div>
                  </div>
                ) : (
                  <>
                    <div className="flex items-start justify-between gap-4">
                      <p className="text-white whitespace-pre-wrap flex-1">
                        {note.content}
                      </p>
                      <div className="flex items-center gap-1 flex-shrink-0">
                        <Button
                          size="icon"
                          variant="ghost"
                          className="h-8 w-8"
                          onClick={() => togglePin(note)}
                          title={note.is_pinned ? 'Desepingler' : 'Epingler'}
                        >
                          {note.is_pinned ? (
                            <PinOff className="h-4 w-4 text-yellow-400" />
                          ) : (
                            <Pin className="h-4 w-4" />
                          )}
                        </Button>
                        <Button
                          size="icon"
                          variant="ghost"
                          className="h-8 w-8"
                          onClick={() => startEdit(note)}
                          title="Modifier"
                        >
                          <Edit3 className="h-4 w-4" />
                        </Button>
                        <Button
                          size="icon"
                          variant="ghost"
                          className="h-8 w-8 text-red-400 hover:text-red-300"
                          onClick={() => deleteNote(note.id)}
                          title="Supprimer"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 mt-2 text-xs text-slate-400">
                      {note.is_pinned && (
                        <Badge className="bg-yellow-500/20 text-yellow-400 text-xs">
                          <Pin className="h-3 w-3 mr-1" />
                          Epingle
                        </Badge>
                      )}
                      <span>Admin #{note.admin_id}</span>
                      <span>•</span>
                      <span>{formatDate(note.created_at)}</span>
                    </div>
                  </>
                )}
              </motion.div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
