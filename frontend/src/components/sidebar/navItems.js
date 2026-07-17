import { BarChart3, BookOpen, Home, Leaf, NotebookTabs, Pencil } from 'lucide-react';

export const navItems = [
  { label: 'Home', icon: Home, href: '#/', page: 'home' },
  { label: 'Groups', icon: BookOpen, href: '#/groups', page: 'groups' },
  { label: 'Radicals', icon: Leaf },
  { label: 'Notes', icon: Pencil, href: '#/notes', page: 'notes' },
  { label: 'Flashcards', icon: NotebookTabs, href: '#/flaschcards', page: 'flaschcards' },
  { label: 'Progress', icon: BarChart3 },
];
