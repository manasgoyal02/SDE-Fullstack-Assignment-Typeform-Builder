'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api, API, Form } from '../../../lib/api';

type Data = { responses: any[]; summaries: Record<string, Record<string, number>> };

export default function Results({ params }: { params: Promise<{ id: string }> }) {
  const [form, setForm] = useState<Form | null>(null);
  const [data, setData] = useState<Data | null>(null);
  const [selected, setSelected] = useState<any>(null);

  useEffect(() => {
    params.then(({ id }) => {
      api.form(id).then(setForm);
      api.responses(id).then(setData);
    });
  }, [params]);

  if (!form || !data) return <div className="center">Loading results…</div>;

  const open = async (response: any) => setSelected(await api.response(form.id, response.id));
  const exportUrl = `${API}/forms/${form.id}/export.csv`;

  return (
    <main className="results">
      <header>
        <Link href={`/builder/${form.id}`}>← Back to builder</Link>
        <h1>{form.title}</h1>
        <nav>
          <Link href={`/builder/${form.id}`}>Create</Link>
          <b>Results <span>{data.responses.length}</span></b>
          <a className="export-link" href={exportUrl}>Export CSV</a>
        </nav>
      </header>
      <section className="results-content">
        <h2>Overview</h2>
        <div className="stat-grid">
          <div><b>{data.responses.length}</b><span>Responses</span></div>
          <div><b>{data.responses.length ? '100%' : '—'}</b><span>Completion rate</span></div>
          <div><b>{data.responses[0] ? new Date(data.responses[0].submitted_at).toLocaleDateString() : '—'}</b><span>Latest response</span></div>
        </div>
        {form.questions.map((question) => (
          <article className="summary" key={question.id}>
            <h3>{question.title}</h3>
            {data.summaries[question.id]
              ? Object.entries(data.summaries[question.id]).map(([value, count]) => (
                  <p key={value}><span>{value}</span><i style={{ width: `${data.responses.length ? (Number(count) / data.responses.length) * 100 : 0}%` }} /><b>{String(count)}</b></p>
                ))
              : <p className="muted">{data.responses.length} response{data.responses.length === 1 ? '' : 's'} collected</p>}
          </article>
        ))}
        <h2>Individual responses</h2>
        {data.responses.map((response, index) => (
          <button className="response-card response-row" onClick={() => void open(response)} key={response.id}>
            <b>Response {data.responses.length - index}</b>
            <time>{new Date(response.submitted_at).toLocaleString()}</time>
            <span>View response →</span>
          </button>
        ))}
      </section>
      {selected && (
        <div className="modal-backdrop" onMouseDown={() => setSelected(null)}>
          <article className="response-detail" onMouseDown={(event) => event.stopPropagation()}>
            <button className="close-detail" onClick={() => setSelected(null)}>×</button>
            <span className="eyebrow">INDIVIDUAL RESPONSE</span>
            <h2>Submitted {new Date(selected.submitted_at).toLocaleString()}</h2>
            {form.questions.map((question, index) => (
              <div className="answer-detail" key={question.id}>
                <small>{index + 1}. {question.title}</small>
                <p>{selected.answers[question.id] || 'No answer'}</p>
              </div>
            ))}
          </article>
        </div>
      )}
    </main>
  );
}
