'use client';
import {useEffect,useState} from 'react';
export default function ThemeToggle(){const[dark,setDark]=useState(false);useEffect(()=>{const enabled=localStorage.getItem('typeflow-theme')==='dark';setDark(enabled);document.body.classList.toggle('dark',enabled)},[]);const toggle=()=>{const next=!dark;setDark(next);document.body.classList.toggle('dark',next);localStorage.setItem('typeflow-theme',next?'dark':'light')};return <button className="theme-toggle global-theme-toggle" onClick={toggle}>{dark?'☀ Light':'◐ Dark'}</button>}
