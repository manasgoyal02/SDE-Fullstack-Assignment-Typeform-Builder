import json
import re
import csv
import io
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

DB_PATH = Path(os.getenv("TYPEFLOW_DB_PATH", str(Path(__file__).with_name("typeflow.db"))))
app = FastAPI(title="Typeflow API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@contextmanager
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def now(): return datetime.now(timezone.utc).isoformat()
def slugify(value: str):
    base = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "form"
    return f"{base}-{uuid.uuid4().hex[:6]}"
def qid(): return uuid.uuid4().hex[:12]

def init_db():
    with db() as con:
        con.executescript('''
        CREATE TABLE IF NOT EXISTS forms (
          id TEXT PRIMARY KEY, title TEXT NOT NULL, slug TEXT UNIQUE NOT NULL,
          status TEXT NOT NULL DEFAULT 'draft', settings TEXT NOT NULL DEFAULT '{}',
          created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS questions (
          id TEXT PRIMARY KEY, form_id TEXT NOT NULL REFERENCES forms(id) ON DELETE CASCADE,
          position INTEGER NOT NULL, type TEXT NOT NULL, title TEXT NOT NULL,
          description TEXT NOT NULL DEFAULT '', required INTEGER NOT NULL DEFAULT 0,
          options TEXT NOT NULL DEFAULT '[]'
        );
        CREATE TABLE IF NOT EXISTS responses (
          id TEXT PRIMARY KEY, form_id TEXT NOT NULL REFERENCES forms(id) ON DELETE CASCADE,
          submitted_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS answers (
          id INTEGER PRIMARY KEY AUTOINCREMENT, response_id TEXT NOT NULL REFERENCES responses(id) ON DELETE CASCADE,
          question_id TEXT NOT NULL, value TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_forms_slug ON forms(slug);
        CREATE INDEX IF NOT EXISTS idx_questions_form_position ON questions(form_id, position);
        CREATE INDEX IF NOT EXISTS idx_responses_form_submitted ON responses(form_id, submitted_at);
        CREATE INDEX IF NOT EXISTS idx_answers_response ON answers(response_id);
        CREATE INDEX IF NOT EXISTS idx_answers_question ON answers(question_id);
        ''')
        if not con.execute("SELECT 1 FROM forms LIMIT 1").fetchone(): seed(con)

def seed(con):
    form_id = qid(); stamp = now()
    con.execute("INSERT INTO forms VALUES (?, ?, ?, 'published', ?, ?, ?)", (form_id, "Product feedback", "product-feedback", json.dumps({"theme":"#191919","thankYou":"Thank you — your feedback makes us better."}), stamp, stamp))
    questions = [
      (qid(), 0, "short_text", "What should we call you?", "", 1, []),
      (qid(), 1, "rating", "How would you rate your experience?", "1 is not great. 5 is amazing.", 1, ["1","2","3","4","5"]),
      (qid(), 2, "multiple_choice", "What was the highlight?", "Choose the one that stands out.", 1, ["The product", "The support", "The experience"]),
      (qid(), 3, "long_text", "Is there anything else you'd like to share?", "", 0, []),
    ]
    for ident,pos,typ,title,desc,required,opts in questions:
        con.execute("INSERT INTO questions VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (ident,form_id,pos,typ,title,desc,required,json.dumps(opts)))
    r = qid(); con.execute("INSERT INTO responses VALUES (?, ?, ?)", (r,form_id,stamp))
    for question, answer in zip(questions, ["Avery", "5", "The experience", "Beautiful and effortless."]):
        con.execute("INSERT INTO answers (response_id,question_id,value) VALUES (?,?,?)", (r,question[0],answer))
    survey_id = qid()
    con.execute("INSERT INTO forms VALUES (?, ?, ?, 'published', ?, ?, ?)", (survey_id, "Team check-in", "team-check-in", json.dumps({"theme":"#2f6fed","thankYou":"Thanks for checking in!"}), stamp, stamp))
    survey_questions = [
      (qid(), 0, "yes_no", "Did you have a productive week?", "", 1, ["Yes", "No"]),
      (qid(), 1, "dropdown", "What could help most next week?", "", 0, ["More focus time", "More support", "Clearer priorities"]),
      (qid(), 2, "email", "Where can we follow up?", "", 0, []),
    ]
    for ident,pos,typ,title,desc,required,opts in survey_questions:
        con.execute("INSERT INTO questions VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (ident,survey_id,pos,typ,title,desc,required,json.dumps(opts)))

def form_data(con, row, include_questions=True):
    data = dict(row); data["settings"] = json.loads(data["settings"])
    data["response_count"] = con.execute("SELECT count(*) FROM responses WHERE form_id=?", (data["id"],)).fetchone()[0]
    if include_questions:
        rows = con.execute("SELECT * FROM questions WHERE form_id=? ORDER BY position", (data["id"],)).fetchall()
        data["questions"] = [{**dict(q), "required": bool(q["required"]), "options": json.loads(q["options"])} for q in rows]
    return data

class FormInput(BaseModel):
    title: str = "Untitled form"
    questions: list[dict[str, Any]] = Field(default_factory=list)
    settings: dict[str, Any] = Field(default_factory=dict)

class ResponseInput(BaseModel):
    answers: dict[str, Any]

def get_form(con, form_id):
    row = con.execute("SELECT * FROM forms WHERE id=?", (form_id,)).fetchone()
    if not row: raise HTTPException(404, "Form not found")
    return row

def save_questions(con, form_id, questions):
    con.execute("DELETE FROM questions WHERE form_id=?", (form_id,))
    for pos, question in enumerate(questions):
        con.execute("INSERT INTO questions VALUES (?,?,?,?,?,?,?,?)", (question.get("id") or qid(), form_id, pos, question.get("type", "short_text"), question.get("title", "Untitled question"), question.get("description", ""), int(bool(question.get("required"))), json.dumps(question.get("options", []))))

@app.on_event("startup")
def startup(): init_db()

@app.get("/health")
def health(): return {"ok": True}

@app.get("/forms")
def list_forms():
    with db() as con:
        return [form_data(con, row, False) for row in con.execute("SELECT * FROM forms ORDER BY updated_at DESC")]

@app.post("/forms")
def create_form(payload: FormInput):
    with db() as con:
        ident = qid(); stamp = now()
        con.execute("INSERT INTO forms VALUES (?,?,?,?,?,?,?)", (ident, payload.title, slugify(payload.title), "draft", json.dumps(payload.settings), stamp, stamp))
        save_questions(con, ident, payload.questions)
        return form_data(con, get_form(con, ident))

@app.get("/forms/{form_id}")
def read_form(form_id: str):
    with db() as con: return form_data(con, get_form(con, form_id))

@app.put("/forms/{form_id}")
def update_form(form_id: str, payload: FormInput):
    with db() as con:
        get_form(con, form_id)
        con.execute("UPDATE forms SET title=?,settings=?,updated_at=? WHERE id=?", (payload.title, json.dumps(payload.settings), now(), form_id))
        save_questions(con, form_id, payload.questions)
        return form_data(con, get_form(con, form_id))

@app.delete("/forms/{form_id}")
def delete_form(form_id: str):
    with db() as con: get_form(con, form_id); con.execute("DELETE FROM forms WHERE id=?", (form_id,)); return {"ok": True}

@app.post("/forms/{form_id}/duplicate")
def duplicate_form(form_id: str):
    with db() as con:
        original = form_data(con, get_form(con, form_id)); ident = qid(); stamp = now(); title = original["title"] + " (copy)"
        con.execute("INSERT INTO forms VALUES (?,?,?,?,?,?,?)", (ident,title,slugify(title),"draft",json.dumps(original["settings"]),stamp,stamp))
        # Question identifiers are global primary keys; a duplicate needs fresh IDs.
        save_questions(con, ident, [{**question, "id": qid()} for question in original["questions"]])
        return form_data(con, get_form(con, ident))

@app.post("/forms/{form_id}/publish")
def set_published(form_id: str, published: bool = True):
    with db() as con:
        get_form(con, form_id); con.execute("UPDATE forms SET status=?,updated_at=? WHERE id=?", ("published" if published else "draft",now(),form_id)); return form_data(con,get_form(con,form_id))

@app.get("/forms/{form_id}/responses")
def responses(form_id: str):
    with db() as con:
        form = form_data(con,get_form(con,form_id)); rows = con.execute("SELECT * FROM responses WHERE form_id=? ORDER BY submitted_at DESC",(form_id,)).fetchall()
        items=[]
        for response in rows:
            answers = {a["question_id"]: a["value"] for a in con.execute("SELECT * FROM answers WHERE response_id=?",(response["id"],))}
            items.append({**dict(response),"answers":answers})
        summaries={}
        for q in form["questions"]:
            if q["type"] in ("multiple_choice","dropdown","yes_no","rating"):
                counts={}
                for i in items:
                    v=i["answers"].get(q["id"])
                    if v: counts[v]=counts.get(v,0)+1
                summaries[q["id"]]=counts
        return {"responses":items,"summaries":summaries}

@app.get("/forms/{form_id}/responses/{response_id}")
def response_detail(form_id: str, response_id: str):
    with db() as con:
        form_data(con, get_form(con, form_id))
        row = con.execute("SELECT * FROM responses WHERE id=? AND form_id=?", (response_id, form_id)).fetchone()
        if not row: raise HTTPException(404, "Response not found")
        answers = {a["question_id"]: a["value"] for a in con.execute("SELECT * FROM answers WHERE response_id=?", (response_id,))}
        return {**dict(row), "answers": answers}

@app.get("/forms/{form_id}/export.csv")
def export_csv(form_id: str):
    with db() as con:
        form = form_data(con, get_form(con, form_id))
        stream = io.StringIO(); writer = csv.writer(stream)
        writer.writerow(["Response ID", "Submitted at", *[q["title"] for q in form["questions"]]])
        for response in con.execute("SELECT * FROM responses WHERE form_id=? ORDER BY submitted_at DESC", (form_id,)):
            values = {a["question_id"]: a["value"] for a in con.execute("SELECT * FROM answers WHERE response_id=?", (response["id"],))}
            writer.writerow([response["id"], response["submitted_at"], *[values.get(q["id"], "") for q in form["questions"]]])
        return StreamingResponse(iter([stream.getvalue()]), media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="{form["slug"]}-responses.csv"'})

@app.get("/public/forms/{slug}")
def public_form(slug: str):
    with db() as con:
        row=con.execute("SELECT * FROM forms WHERE slug=? AND status='published'",(slug,)).fetchone()
        if not row: raise HTTPException(404,"This form is not available")
        return form_data(con,row)

@app.post("/public/forms/{slug}/responses")
def submit_response(slug: str,payload: ResponseInput):
    with db() as con:
        row=con.execute("SELECT * FROM forms WHERE slug=? AND status='published'",(slug,)).fetchone()
        if not row: raise HTTPException(404,"This form is not available")
        form=form_data(con,row); errors={}
        for q in form["questions"]:
            value=payload.answers.get(q["id"])
            if q["required"] and (value is None or value==""): errors[q["id"]]="This question is required"
            if value and q["type"]=="email" and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$",str(value)): errors[q["id"]]="Enter a valid email"
            if value and q["type"]=="number":
                try: float(value)
                except ValueError: errors[q["id"]]="Enter a number"
        if errors: raise HTTPException(422,detail=errors)
        response_id=qid(); con.execute("INSERT INTO responses VALUES (?,?,?)",(response_id,row["id"],now()))
        for question_id,value in payload.answers.items(): con.execute("INSERT INTO answers (response_id,question_id,value) VALUES (?,?,?)",(response_id,question_id,str(value)))
        return {"ok":True,"response_id":response_id,"thankYou":form["settings"].get("thankYou","Thank you for your response!")}
