'use client';

import { useCallback, useEffect, useState } from 'react';
import { api, Form, Question } from '../../../lib/api';

export default function PublicForm({ params }: { params: Promise<{ slug: string }> }) {
  const [form, setForm] = useState<Form | null>(null);
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [error, setError] = useState('');
  const [done, setDone] = useState(false);

  useEffect(() => {
    params.then(({ slug }) => api.public(slug).then(setForm).catch(() => setError('This form is not available.')));
  }, [params]);

  const advance = useCallback(async (override?: string) => {
    if (!form) return;
    const question = form.questions[step];
    const value = override ?? answers[question.id] ?? '';
    const nextAnswers = { ...answers, [question.id]: value };

    if (question.required && !value.trim()) return setError('Please answer this question to continue.');
    if (question.type === 'email' && value && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(value)) return setError('Please enter a valid email address.');
    if (question.type === 'number' && value && Number.isNaN(Number(value))) return setError('Please enter a number.');

    setAnswers(nextAnswers);
    setError('');

    let nextStep = step + 1;
    const rule = form.settings.logic;
    if (rule?.sourceQuestionId === question.id && value === rule.expectedValue) {
      const target = form.questions.findIndex((item) => item.id === rule.targetQuestionId);
      if (target > step) nextStep = target;
    }

    if (nextStep < form.questions.length) {
      setStep(nextStep);
    } else {
      try {
        await api.submit(form.slug, nextAnswers);
        setDone(true);
      } catch (submissionError) {
        setError(submissionError instanceof Error ? submissionError.message : 'We could not save your response.');
      }
    }
  }, [answers, form, step]);

  const back = useCallback(() => setStep((current) => Math.max(0, current - 1)), []);

  useEffect(() => {
    const key = (event: KeyboardEvent) => {
      if (!form || done) return;
      if (event.key === 'ArrowRight') {
        event.preventDefault();
        void advance();
      } else if (event.key === 'ArrowLeft') {
        event.preventDefault();
        back();
      } else if (event.key === 'Enter' && form.questions[step]?.type !== 'long_text') {
        event.preventDefault();
        void advance();
      }
    };
    window.addEventListener('keydown', key);
    return () => window.removeEventListener('keydown', key);
  }, [advance, back, done, form, step]);

  if (!form) return <div className="public error-page">{error || 'Loading your form...'}</div>;

  const question = form.questions[step];
  if (done) {
    return <div className="public thank" style={{ background: form.settings.theme || '#191919' }}><div className="thank-card"><span>*</span><h1>{form.settings.thankYou || 'Thank you for your response!'}</h1><p>Your response was recorded successfully.</p></div><footer>Made with <b>typeflow</b></footer></div>;
  }

  return <div className="public" style={{ background: form.settings.theme || '#191919' }}>
    <div className="progress"><i style={{ width: `${((step + 1) / form.questions.length) * 100}%` }} /></div>
    <div className="public-top"><span className="public-brand">type<span>flow</span></span><span>{step + 1} / {form.questions.length}</span></div>
    <main className="public-question" key={question.id}>
      <div className="step">QUESTION {String(step + 1).padStart(2, '0')}</div>
      <h1>{question.title}{question.required && <em> *</em>}</h1>
      {question.description && <p>{question.description}</p>}
      <Input question={question} value={answers[question.id] || ''} change={(value) => { setAnswers({ ...answers, [question.id]: value }); setError(''); }} choose={advance} />
      {error && <div className="field-error">! {error}</div>}
      <div className="respond-actions"><button className="ok-btn" onClick={() => void advance()}>{step === form.questions.length - 1 ? 'Submit' : 'OK'} <b>-&gt;</b></button>{step > 0 && <button className="back-btn" onClick={back}>&lt;- Back</button>}</div>
      <small className="hint">Use <kbd>Enter</kbd> to continue · <kbd>&lt;-</kbd><kbd>-&gt;</kbd> to navigate</small>
    </main>
    <footer><span>Press Enter to continue</span><span>Made with <b>typeflow</b></span></footer>
  </div>;
}

function Input({ question, value, change, choose }: { question: Question; value: string; change: (value: string) => void; choose: (value: string) => Promise<void> }) {
  if (question.type === 'multiple_choice' || question.type === 'yes_no') return <div className="public-choices">{(question.type === 'yes_no' ? ['Yes', 'No'] : question.options).map((option, index) => <button className={value === option ? 'chosen' : ''} key={option} onClick={() => void choose(option)}><b>{String.fromCharCode(65 + index)}</b>{option}</button>)}</div>;
  if (question.type === 'dropdown') return <select autoFocus className="public-input" value={value} onChange={(event) => change(event.target.value)}><option value="">Choose an option</option>{question.options.map((option) => <option key={option}>{option}</option>)}</select>;
  if (question.type === 'rating') return <div className="public-rating">{question.options.map((option) => <button key={option} onClick={() => void choose(option)} className={value === option ? 'chosen' : ''}>{option}</button>)}</div>;
  return question.type === 'long_text' ? <textarea autoFocus className="public-input textarea" value={value} onChange={(event) => change(event.target.value)} placeholder="Type your answer here..." /> : <input autoFocus className="public-input" type={question.type === 'email' ? 'email' : question.type === 'number' ? 'number' : 'text'} value={value} onChange={(event) => change(event.target.value)} placeholder={question.type === 'email' ? 'name@example.com' : question.type === 'number' ? 'Type a number...' : 'Type your answer here...'} />;
}

