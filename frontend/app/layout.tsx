import './globals.css';
import ThemeToggle from './theme-toggle';
export const metadata = { title: 'Typeflow', description: 'Beautiful forms, made simple' };
export default function Layout({children}:{children:React.ReactNode}) { return <html lang="en"><body>{children}<ThemeToggle/></body></html>; }
