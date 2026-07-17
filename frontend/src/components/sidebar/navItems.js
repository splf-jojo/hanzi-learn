import { BarChart3, BookOpen, Home, Images, Leaf, NotebookTabs, Pencil } from 'lucide-react';

export const navItems = [
  { label: 'Home', icon: Home, href: '#/', page: 'home' },
  { label: 'Groups', icon: BookOpen, href: '#/groups', page: 'groups' },
  { label: 'Photo', icon: Images, href: '#/photos', page: 'photos' },
  { label: 'Radicals', icon: Leaf },
  { label: 'Notes', icon: Pencil, href: '#/notes', page: 'notes' },
  { label: 'Flashcards', icon: NotebookTabs, href: '#/flashcards', page: 'flashcards' },
  { label: 'Progress', icon: BarChart3 },
];
