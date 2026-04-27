import { useEffect, useState } from 'react'
import './App.css'

interface Note {
  id: number;
  title: string;
  content: string;
  icon_path: string | null;
}

function App() {
  const [notes, setNotes] = useState<Note[]>([]);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const API_URL = '/api';

  const fetchNotes = async () => {
    try {
      const res = await fetch(`${API_URL}/notes`);
      if (res.ok) setNotes(await res.json());
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    queueMicrotask(() => {
      void fetchNotes();
    });
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title || isSubmitting) return;
    
    const formData = new FormData();
    formData.append('title', title);
    formData.append('content', content);
    if (file) formData.append('icon', file);

    try {
      setIsSubmitting(true);
      await fetch(`${API_URL}/notes`, { method: 'POST', body: formData });
      setTitle(''); setContent(''); setFile(null); fetchNotes();
    } catch (err) {
       console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  };
  
  const handleDelete = async (id: number) => {
    try {
        await fetch(`${API_URL}/notes/${id}`, { method: 'DELETE' });
        fetchNotes();
    } catch (err) { console.error(err); }
  };

  const cardAccents = [
    'from-[#ff5f6d] to-[#ffc371]',
    'from-[#36d1dc] to-[#5b86e5]',
    'from-[#f7971e] to-[#ffd200]',
    'from-[#00c9a7] to-[#92fe9d]',
  ];

  return (
    <div className="relative min-h-screen overflow-hidden bg-[#fff9f2] px-4 py-8 text-slate-900 sm:px-6 lg:px-10 lg:py-12">
      <div className="pointer-events-none absolute -left-24 -top-20 h-72 w-72 rounded-full bg-[#ff8fab]/35 blur-3xl blob-float" />
      <div className="pointer-events-none absolute right-0 top-36 h-80 w-80 rounded-full bg-[#7bdff2]/35 blur-3xl blob-float [animation-delay:0.8s]" />
      <div className="pointer-events-none absolute bottom-0 left-1/3 h-72 w-72 rounded-full bg-[#ffe66d]/30 blur-3xl blob-float [animation-delay:1.6s]" />

      <div className="relative mx-auto flex w-full max-w-7xl flex-col gap-8 lg:gap-10">
        <header className="rounded-[2rem] border border-white/70 bg-white/70 px-6 py-8 shadow-[0_20px_70px_-30px_rgba(0,0,0,0.35)] backdrop-blur-xl sm:px-10 sm:py-10">
          <p className="inline-flex rounded-full bg-[#1a1a1a] px-4 py-1 text-xs font-bold uppercase tracking-[0.22em] text-white">
            Kolorowy Notatnik
          </p>
          <h1 className="display-font mt-4 text-4xl font-extrabold leading-tight sm:text-5xl lg:text-6xl">
            Zapisuj pomysly
            <span className="ml-3 inline-block rotate-[-5deg] rounded-2xl bg-[#ff6b6b] px-3 py-1 text-white shadow-lg">w stylu</span>
            <span className="ml-3 bg-gradient-to-r from-[#ff5f6d] via-[#36d1dc] to-[#f7971e] bg-clip-text text-transparent">
              wow
            </span>
          </h1>
          <p className="mt-4 max-w-3xl text-base text-slate-700 sm:text-lg">
            Twoje notatki, ale bez nudy. Dodawaj, kolekcjonuj i usuwaj wpisy w lekkim, kolorowym interfejsie.
          </p>
        </header>

        <main className="grid gap-8 lg:grid-cols-[minmax(320px,380px)_1fr] lg:items-start">
          <section className="note-form-panel rounded-[2rem] border border-white/70 bg-white/80 p-6 shadow-[0_20px_70px_-35px_rgba(0,0,0,0.35)] backdrop-blur-xl sm:p-7">
            <h2 className="display-font mb-1 text-2xl font-bold">Nowa notatka</h2>
            <p className="mb-6 text-sm text-slate-600">Wpisz tytul, dodaj tresc i opcjonalnie obrazek okladki.</p>

            <form onSubmit={handleSubmit} className="space-y-5" aria-label="Formularz dodawania notatki">
              <div className="space-y-2">
                <label htmlFor="title" className="block text-sm font-semibold text-slate-700">Tytul</label>
                <input
                  id="title"
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  required
                  placeholder="np. Plan na weekend"
                  className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none transition focus:border-[#36d1dc] focus:ring-4 focus:ring-[#36d1dc]/25"
                />
              </div>

              <div className="space-y-2">
                <label htmlFor="content" className="block text-sm font-semibold text-slate-700">Tresc</label>
                <textarea
                  id="content"
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  placeholder="Napisz, co Ci chodzi po glowie..."
                  className="min-h-36 w-full resize-y rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none transition focus:border-[#ff6b6b] focus:ring-4 focus:ring-[#ff6b6b]/20"
                />
              </div>

              <div className="space-y-2">
                <label htmlFor="image" className="block text-sm font-semibold text-slate-700">Okladka (opcjonalnie)</label>
                <input
                  id="image"
                  type="file"
                  onChange={(e) => e.target.files && setFile(e.target.files[0])}
                  accept="image/*"
                  className="block w-full cursor-pointer rounded-xl border border-dashed border-slate-300 bg-[#fffef8] px-3 py-2 text-sm text-slate-600 file:mr-3 file:cursor-pointer file:rounded-lg file:border-0 file:bg-[#1a1a1a] file:px-3 file:py-2 file:text-xs file:font-semibold file:text-white hover:border-[#f7971e]"
                />
                <p className="text-xs text-slate-500" aria-live="polite">
                  {file ? `Wybrano plik: ${file.name}` : 'Nie wybrano pliku'}
                </p>
              </div>

              <button
                type="submit"
                className="flex w-full items-center justify-center rounded-xl bg-gradient-to-r from-[#ff5f6d] to-[#ffc371] px-4 py-3 text-sm font-bold text-white shadow-[0_14px_30px_-12px_rgba(255,95,109,0.8)] transition hover:scale-[1.02] hover:shadow-[0_18px_36px_-12px_rgba(255,95,109,0.85)] focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[#ff5f6d]/35 disabled:cursor-not-allowed disabled:opacity-60"
                disabled={!title || isSubmitting}
                aria-label="Dodaj nowa notatke"
              >
                {isSubmitting ? 'Zapisywanie...' : 'Dodaj notatke'}
              </button>
            </form>
          </section>

          <section className="space-y-5">
            <div className="flex items-center justify-between rounded-2xl border border-white/70 bg-white/75 px-5 py-4 shadow-[0_16px_40px_-28px_rgba(0,0,0,0.35)] backdrop-blur-xl">
              <h2 className="display-font text-2xl font-bold">Twoje notatki</h2>
              <span className="rounded-full bg-slate-900 px-3 py-1 text-xs font-semibold text-white">
                {notes.length} szt.
              </span>
            </div>

            {notes.length === 0 ? (
              <div className="grid min-h-72 place-content-center rounded-[2rem] border-2 border-dashed border-slate-300 bg-white/70 p-8 text-center shadow-[0_16px_40px_-30px_rgba(0,0,0,0.35)] backdrop-blur-xl">
                <span className="mb-4 text-5xl" aria-hidden="true">🌈</span>
                <h3 className="display-font text-2xl font-bold">Jeszcze pusto</h3>
                <p className="mt-2 max-w-md text-sm text-slate-600 sm:text-base">
                  Dodaj pierwsza notatke i zacznij budowac swoja kolorowa tablice pomyslow.
                </p>
              </div>
            ) : (
              <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
                {notes.map((note, index) => (
                  <article
                    key={note.id}
                    className="note-card-enter group relative overflow-hidden rounded-3xl border border-white/80 bg-white shadow-[0_22px_45px_-30px_rgba(0,0,0,0.45)] transition duration-300 hover:-translate-y-1.5"
                    style={{ animationDelay: `${index * 90}ms` }}
                  >
                    <div className={`h-2 w-full bg-gradient-to-r ${cardAccents[index % cardAccents.length]}`} />

                    {note.icon_path ? (
                      <div className="relative h-44 overflow-hidden">
                        <img
                          src={note.icon_path}
                          className="h-full w-full object-cover transition duration-500 group-hover:scale-105"
                          alt={`Okladka notatki ${note.title}`}
                        />
                      </div>
                    ) : (
                      <div className={`grid h-28 place-content-center bg-gradient-to-r ${cardAccents[index % cardAccents.length]} text-2xl font-black text-white`}>
                        {note.title.slice(0, 1).toUpperCase() || 'N'}
                      </div>
                    )}

                    <div className="space-y-4 p-5 text-left">
                      <h3 className="display-font line-clamp-2 text-xl font-bold leading-tight text-slate-900">
                        {note.title}
                      </h3>
                      <p className="min-h-20 whitespace-pre-wrap text-sm leading-6 text-slate-700">{note.content || 'Brak tresci.'}</p>
                      <button
                        className="w-full rounded-xl border border-rose-200 bg-rose-50 px-4 py-2 text-sm font-semibold text-rose-700 transition hover:bg-rose-100 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-rose-300/60"
                        onClick={() => handleDelete(note.id)}
                        aria-label={`Usun notatke ${note.title}`}
                      >
                        Usun notatke
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>
        </main>
      </div>
    </div>
  );
}

export default App;
