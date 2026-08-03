#!/usr/bin/env python3
"""
generatecards.py — Convert YAML files to Anki .apkg

Usage:
    python generatecards.py <path/to/notes.yaml> [output.apkg]

Requirements:
    pip install genanki pyyaml

Card templates are loaded from question_types/*.js (single source of truth
shared with simple_learner index.html). write_code uses a simple textarea instead of Monaco.
"""

import genanki
import yaml
import sys
import re
import json
import hashlib
import html as html_mod
from pathlib import Path

try:
    import markdown as md_lib
    HAS_MARKDOWN = True
except ImportError:
    HAS_MARKDOWN = False

# ---------------------------------------------------------------------------
# Stable model IDs — NEVER change these or Anki will treat them as new
# note types and duplicate all cards on re-import.
# ---------------------------------------------------------------------------
_MODEL_IDS = {
    'qna':              1_707_001_001,
    'fib':              1_707_001_002,
    'mcq':              1_707_001_003,
    'list_completion':  1_707_001_004,
    'descriptive_text': 1_707_001_005,
    'code_fib':         1_707_001_006,
    'write_code':       1_707_001_007,
}

_SCRIPT_DIR = Path(__file__).parent
_QT_DIR = _SCRIPT_DIR / 'question_types'

_MARKED_CDN = '<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>'

_CSS = """
.card {
  font-family: Arial, sans-serif;
  max-width: 840px;
  margin: 0 auto;
  padding: 18px;
  font-size: 15px;
  line-height: 1.55;
  color: #222;
}
.question { margin-bottom: 14px; }
.question p { margin: 4px 0; }
.question code { background: #f0f0f0; padding: 1px 5px; border-radius: 3px; font-family: monospace; }
.question pre { background: #f0f0f0; padding: 8px 12px; border-radius: 5px; overflow-x: auto; white-space: pre-wrap; }
hr { border: none; border-top: 1px solid #ddd; margin: 14px 0; }
.answer-box { color: #1a7f37; margin-top: 6px; }
.answer-box code { background: #e6f9ed; padding: 1px 5px; border-radius: 3px; font-family: monospace; }
.answer-box pre { background: #e6f9ed; padding: 8px 12px; border-radius: 5px; white-space: pre-wrap; }

/* blank inputs (fib) */
.blank-input {
  background: transparent;
  border: none;
  border-bottom: 2px solid #aaa;
  margin: 0 3px;
  font-size: 1em;
  outline: none;
  min-width: 5ch;
}
.blank-input.ok  { border-bottom-color: #2d8a4e; }
.blank-input.bad { border-bottom-color: #c0392b; }
.blank-answer { color: #e67e22; font-weight: bold;
                background: #fff8e1; padding: 1px 4px; border-radius: 3px; }

/* code block */
.code-block {
  background: #1e1e1e;
  color: #d4d4d4;
  border-radius: 8px;
  padding: 12px 16px;
  white-space: pre-wrap;
  font-family: monospace;
  font-size: 0.93em;
  line-height: 1.65;
  margin: 8px 0;
}
.code-blank {
  background: transparent;
  color: #ffd700;
  border: none;
  border-bottom: 2px solid #666;
  font-family: monospace;
  font-size: 1em;
  outline: none;
  min-width: 4ch;
}
.code-blank.ok  { border-bottom-color: #4ec94e; }
.code-blank.bad { border-bottom-color: #f55; }
.code-answer { color: #4ec94e; font-weight: bold; }

/* MCQ */
.option-label { display: block; margin: 5px 0 5px 10px; cursor: pointer; }
.option-correct { color: #1a7f37; font-weight: bold; }

/* List completion */
.list-input {
  border: 1px solid #ccc;
  border-radius: 3px;
  padding: 3px 7px;
  margin: 3px 0;
  display: block;
  width: 18em;
  font-size: 0.95em;
}
.list-input.ok  { border-color: #2d8a4e; background: #f0fff4; }
.list-input.bad { border-color: #c0392b; }
.answer-list { list-style: disc; padding-left: 20px; color: #1a7f37; margin-top: 6px; }

/* check button */
.chk-btn {
  margin-top: 10px;
  padding: 5px 14px;
  background: #4a90d9;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.93em;
}
.chk-btn:hover { background: #357abd; }
.result { margin-top: 8px; font-size: 1.05em; min-height: 1.3em; }
"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_qt_js(name: str) -> str:
    """Read a question_types JS file and strip the `export` keyword."""
    content = (_QT_DIR / f'{name}.js').read_text(encoding='utf-8')
    return re.sub(r'^export\s+', '', content, flags=re.MULTILINE)


def _md(text: str) -> str:
    """Render markdown to HTML (used only for write_code where HTML is injected directly)."""
    if not text:
        return ''
    text = str(text).strip()
    if HAS_MARKDOWN:
        return md_lib.markdown(text, extensions=['fenced_code'])
    t = html_mod.escape(text)
    t = re.sub(r'`([^`\n]+)`', r'<code>\1</code>', t)
    return '<p>' + t.replace('\n\n', '</p><p>').replace('\n', '<br>') + '</p>'


def _esc(text) -> str:
    """HTML-escape for safe storage in a hidden div; JS reads via .textContent."""
    return html_mod.escape(str(text).strip()) if text is not None else ''


def _json_field(value) -> str:
    """JSON-encode and HTML-escape for hidden div storage."""
    return html_mod.escape(json.dumps(value, ensure_ascii=False))


def _guid(question_type: str, question_id, question_text: str) -> str:
    return genanki.guid_for(
        'simple_learner_v1', question_type,
        str(question_id) if question_id is not None else '',
        str(question_text)[:120],
    )


def _card(data_divs: str, container_id: str, js: str, bridge: str, use_marked: bool = True) -> str:
    """Wrap inlined JS and a bridge script into a complete Anki card template."""
    cdn = _MARKED_CDN + '\n' if use_marked else ''
    return (
        '<div class="card">\n'
        + data_divs
        + '  <div id="' + container_id + '"></div>\n'
        + '</div>\n'
        + cdn
        + '<script>\n' + js + '\n' + bridge + '\n</script>'
    )

# ---------------------------------------------------------------------------
# Models — each reads its JS from question_types/
# ---------------------------------------------------------------------------

def _qna_model():
    js = _read_qt_js('qna')

    qfmt = _card(
        '  <div id="qna-qt" style="display:none">{{Question}}</div>\n'
        '  <div id="qna-ans" style="display:none">{{Answer}}</div>\n'
        '  <div id="qna-cs" style="display:none">{{CaseSensitive}}</div>\n',
        'qna-container', js,
        "(function() {\n"
        "  var q = {\n"
        "    question_id: '',\n"
        "    question_text: document.getElementById('qna-qt').textContent,\n"
        "    answer: document.getElementById('qna-ans').textContent,\n"
        "    case_sensitive: document.getElementById('qna-cs').textContent.trim() === 'true'\n"
        "  };\n"
        "  document.getElementById('qna-container').appendChild(renderQna(q));\n"
        "})();"
    )

    afmt = _card(
        '  <div id="qna-qt-b" style="display:none">{{Question}}</div>\n'
        '  <div id="qna-ans-b" style="display:none">{{Answer}}</div>\n'
        '  <div id="qna-cs-b" style="display:none">{{CaseSensitive}}</div>\n',
        'qna-container-b', js,
        "(function() {\n"
        "  var q = {\n"
        "    question_id: '',\n"
        "    question_text: document.getElementById('qna-qt-b').textContent,\n"
        "    answer: document.getElementById('qna-ans-b').textContent,\n"
        "    case_sensitive: document.getElementById('qna-cs-b').textContent.trim() === 'true'\n"
        "  };\n"
        "  var node = renderQna(q);\n"
        "  document.getElementById('qna-container-b').appendChild(node);\n"
        "  var btn = node.querySelector('button');\n"
        "  if (btn) setTimeout(function() { btn.click(); }, 0);\n"
        "})();"
    )

    return genanki.Model(
        _MODEL_IDS['qna'], 'SimpleLearner — Q&A',
        fields=[{'name': 'Question'}, {'name': 'Answer'}, {'name': 'CaseSensitive'}],
        templates=[{'name': 'Card', 'qfmt': qfmt, 'afmt': afmt}],
        css=_CSS,
    )


def _fib_model():
    js = _read_qt_js('fib')

    qfmt = _card(
        '  <div id="fib-qt" style="display:none">{{QuestionText}}</div>\n'
        '  <div id="fib-cs" style="display:none">{{CaseSensitive}}</div>\n',
        'fib-container', js,
        "(function() {\n"
        "  var q = {\n"
        "    question_id: '',\n"
        "    question_text: document.getElementById('fib-qt').textContent,\n"
        "    case_sensitive: document.getElementById('fib-cs').textContent.trim() === 'true'\n"
        "  };\n"
        "  document.getElementById('fib-container').appendChild(renderFib(q));\n"
        "})();",
        use_marked=False,
    )

    afmt = _card(
        '  <div id="fib-qt-b" style="display:none">{{QuestionText}}</div>\n'
        '  <div id="fib-cs-b" style="display:none">{{CaseSensitive}}</div>\n',
        'fib-container-b', js,
        "(function() {\n"
        "  var q = {\n"
        "    question_id: '',\n"
        "    question_text: document.getElementById('fib-qt-b').textContent,\n"
        "    case_sensitive: document.getElementById('fib-cs-b').textContent.trim() === 'true'\n"
        "  };\n"
        "  var node = renderFib(q);\n"
        "  document.getElementById('fib-container-b').appendChild(node);\n"
        "  var btn = node.querySelector('button');\n"
        "  if (btn) setTimeout(function() { btn.click(); }, 0);\n"
        "})();",
        use_marked=False,
    )

    return genanki.Model(
        _MODEL_IDS['fib'], 'SimpleLearner — Fill in the Blank',
        fields=[{'name': 'QuestionText'}, {'name': 'CaseSensitive'}],
        templates=[{'name': 'Card', 'qfmt': qfmt, 'afmt': afmt}],
        css=_CSS,
    )


def _mcq_model():
    js = _read_qt_js('mcq')

    qfmt = _card(
        '  <div id="mcq-qt" style="display:none">{{QuestionText}}</div>\n'
        '  <div id="mcq-opts" style="display:none">{{Options}}</div>\n'
        '  <div id="mcq-corr" style="display:none">{{CorrectAnswer}}</div>\n',
        'mcq-container', js,
        "(function() {\n"
        "  var q = {\n"
        "    question_id: '',\n"
        "    question_text: document.getElementById('mcq-qt').textContent,\n"
        "    options: JSON.parse(document.getElementById('mcq-opts').textContent),\n"
        "    correct_answer: document.getElementById('mcq-corr').textContent.trim()\n"
        "  };\n"
        "  document.getElementById('mcq-container').appendChild(renderMcq(q));\n"
        "})();"
    )

    afmt = _card(
        '  <div id="mcq-qt-b" style="display:none">{{QuestionText}}</div>\n'
        '  <div id="mcq-opts-b" style="display:none">{{Options}}</div>\n'
        '  <div id="mcq-corr-b" style="display:none">{{CorrectAnswer}}</div>\n',
        'mcq-container-b', js,
        "(function() {\n"
        "  var q = {\n"
        "    question_id: '',\n"
        "    question_text: document.getElementById('mcq-qt-b').textContent,\n"
        "    options: JSON.parse(document.getElementById('mcq-opts-b').textContent),\n"
        "    correct_answer: document.getElementById('mcq-corr-b').textContent.trim()\n"
        "  };\n"
        "  var node = renderMcq(q);\n"
        "  document.getElementById('mcq-container-b').appendChild(node);\n"
        "  var btn = node.querySelector('button');\n"
        "  if (btn) setTimeout(function() { btn.click(); }, 0);\n"
        "})();"
    )

    return genanki.Model(
        _MODEL_IDS['mcq'], 'SimpleLearner — Multiple Choice',
        fields=[{'name': 'QuestionText'}, {'name': 'Options'}, {'name': 'CorrectAnswer'}],
        templates=[{'name': 'Card', 'qfmt': qfmt, 'afmt': afmt}],
        css=_CSS,
    )


def _list_completion_model():
    js = _read_qt_js('list_completion')

    qfmt = _card(
        '  <div id="lc-qt" style="display:none">{{QuestionText}}</div>\n'
        '  <div id="lc-ans" style="display:none">{{Answer}}</div>\n'
        '  <div id="lc-cs" style="display:none">{{CaseSensitive}}</div>\n'
        '  <div id="lc-os" style="display:none">{{OrderSensitive}}</div>\n',
        'lc-container', js,
        "(function() {\n"
        "  var q = {\n"
        "    question_id: '',\n"
        "    question_text: document.getElementById('lc-qt').textContent,\n"
        "    answer: JSON.parse(document.getElementById('lc-ans').textContent),\n"
        "    case_sensitive: document.getElementById('lc-cs').textContent.trim() === 'true',\n"
        "    order_sensitive: document.getElementById('lc-os').textContent.trim() === 'true'\n"
        "  };\n"
        "  document.getElementById('lc-container').appendChild(renderListCompletion(q));\n"
        "})();"
    )

    afmt = _card(
        '  <div id="lc-qt-b" style="display:none">{{QuestionText}}</div>\n'
        '  <div id="lc-ans-b" style="display:none">{{Answer}}</div>\n'
        '  <div id="lc-cs-b" style="display:none">{{CaseSensitive}}</div>\n'
        '  <div id="lc-os-b" style="display:none">{{OrderSensitive}}</div>\n',
        'lc-container-b', js,
        "(function() {\n"
        "  var q = {\n"
        "    question_id: '',\n"
        "    question_text: document.getElementById('lc-qt-b').textContent,\n"
        "    answer: JSON.parse(document.getElementById('lc-ans-b').textContent),\n"
        "    case_sensitive: document.getElementById('lc-cs-b').textContent.trim() === 'true',\n"
        "    order_sensitive: document.getElementById('lc-os-b').textContent.trim() === 'true'\n"
        "  };\n"
        "  var node = renderListCompletion(q);\n"
        "  document.getElementById('lc-container-b').appendChild(node);\n"
        "  var btn = node.querySelector('button');\n"
        "  if (btn) setTimeout(function() { btn.click(); }, 0);\n"
        "})();"
    )

    return genanki.Model(
        _MODEL_IDS['list_completion'], 'SimpleLearner — List Completion',
        fields=[
            {'name': 'QuestionText'}, {'name': 'Answer'},
            {'name': 'CaseSensitive'}, {'name': 'OrderSensitive'},
        ],
        templates=[{'name': 'Card', 'qfmt': qfmt, 'afmt': afmt}],
        css=_CSS,
    )


def _descriptive_model():
    js = _read_qt_js('descriptive_text')

    qfmt = _card(
        '  <div id="dt-qt" style="display:none">{{Question}}</div>\n'
        '  <div id="dt-ans" style="display:none">{{Answer}}</div>\n'
        '  <div id="dt-cs" style="display:none">{{CaseSensitive}}</div>\n'
        '  <div id="dt-guided" style="display:none">{{Guided}}</div>\n',
        'dt-container', js,
        "(function() {\n"
        "  var q = {\n"
        "    question_id: '',\n"
        "    question_text: document.getElementById('dt-qt').textContent,\n"
        "    answer: document.getElementById('dt-ans').textContent,\n"
        "    case_sensitive: document.getElementById('dt-cs').textContent.trim() === 'true',\n"
        "    guided: document.getElementById('dt-guided').textContent.trim() === 'true'\n"
        "  };\n"
        "  document.getElementById('dt-container').appendChild(renderDescriptiveText(q));\n"
        "})();"
    )

    afmt = _card(
        '  <div id="dt-qt-b" style="display:none">{{Question}}</div>\n'
        '  <div id="dt-ans-b" style="display:none">{{Answer}}</div>\n'
        '  <div id="dt-cs-b" style="display:none">{{CaseSensitive}}</div>\n'
        '  <div id="dt-guided-b" style="display:none">{{Guided}}</div>\n',
        'dt-container-b', js,
        "(function() {\n"
        "  var q = {\n"
        "    question_id: '',\n"
        "    question_text: document.getElementById('dt-qt-b').textContent,\n"
        "    answer: document.getElementById('dt-ans-b').textContent,\n"
        "    case_sensitive: document.getElementById('dt-cs-b').textContent.trim() === 'true',\n"
        "    guided: document.getElementById('dt-guided-b').textContent.trim() === 'true'\n"
        "  };\n"
        "  var node = renderDescriptiveText(q);\n"
        "  document.getElementById('dt-container-b').appendChild(node);\n"
        "  var btn = node.querySelector('button');\n"
        "  if (btn) setTimeout(function() { btn.click(); }, 0);\n"
        "})();"
    )

    return genanki.Model(
        _MODEL_IDS['descriptive_text'], 'SimpleLearner — Descriptive',
        fields=[
            {'name': 'Question'}, {'name': 'Answer'},
            {'name': 'CaseSensitive'}, {'name': 'Guided'},
        ],
        templates=[{'name': 'Card', 'qfmt': qfmt, 'afmt': afmt}],
        css=_CSS,
    )


def _code_fib_model():
    js = _read_qt_js('code_fib')

    qfmt = _card(
        '  <div id="cf-qt" style="display:none">{{QuestionText}}</div>\n'
        '  <div id="cf-code" style="display:none">{{QuestionCode}}</div>\n'
        '  <div id="cf-lang" style="display:none">{{Language}}</div>\n'
        '  <div id="cf-cs" style="display:none">{{CaseSensitive}}</div>\n',
        'cf-container', js,
        "(function() {\n"
        "  var q = {\n"
        "    question_id: '',\n"
        "    question_text: document.getElementById('cf-qt').textContent,\n"
        "    question_code: document.getElementById('cf-code').textContent,\n"
        "    language: document.getElementById('cf-lang').textContent.trim(),\n"
        "    case_sensitive: document.getElementById('cf-cs').textContent.trim() === 'true'\n"
        "  };\n"
        "  document.getElementById('cf-container').appendChild(renderCodeFib(q));\n"
        "})();"
    )

    afmt = _card(
        '  <div id="cf-qt-b" style="display:none">{{QuestionText}}</div>\n'
        '  <div id="cf-code-b" style="display:none">{{QuestionCode}}</div>\n'
        '  <div id="cf-lang-b" style="display:none">{{Language}}</div>\n'
        '  <div id="cf-cs-b" style="display:none">{{CaseSensitive}}</div>\n',
        'cf-container-b', js,
        "(function() {\n"
        "  var q = {\n"
        "    question_id: '',\n"
        "    question_text: document.getElementById('cf-qt-b').textContent,\n"
        "    question_code: document.getElementById('cf-code-b').textContent,\n"
        "    language: document.getElementById('cf-lang-b').textContent.trim(),\n"
        "    case_sensitive: document.getElementById('cf-cs-b').textContent.trim() === 'true'\n"
        "  };\n"
        "  var node = renderCodeFib(q);\n"
        "  document.getElementById('cf-container-b').appendChild(node);\n"
        "  var btn = node.querySelector('button');\n"
        "  if (btn) setTimeout(function() { btn.click(); }, 0);\n"
        "})();"
    )

    return genanki.Model(
        _MODEL_IDS['code_fib'], 'SimpleLearner — Code Fill in the Blank',
        fields=[
            {'name': 'QuestionText'}, {'name': 'QuestionCode'},
            {'name': 'Language'}, {'name': 'CaseSensitive'},
        ],
        templates=[{'name': 'Card', 'qfmt': qfmt, 'afmt': afmt}],
        css=_CSS,
    )


def _write_code_model():
    js = _read_qt_js('write_code')

    qfmt = _card(
        '  <div id="wc-qt" style="display:none">{{QuestionText}}</div>\n'
        '  <div id="wc-code" style="display:none">{{QuestionCode}}</div>\n'
        '  <div id="wc-lang" style="display:none">{{Language}}</div>\n'
        '  <div id="wc-cs" style="display:none">{{CaseSensitive}}</div>\n'
        '  <div id="wc-guided" style="display:none">{{Guided}}</div>\n',
        'wc-container', js,
        "(function() {\n"
        "  var q = {\n"
        "    question_id: '',\n"
        "    question_text: document.getElementById('wc-qt').textContent,\n"
        "    question_code: document.getElementById('wc-code').textContent,\n"
        "    language: document.getElementById('wc-lang').textContent.trim(),\n"
        "    case_sensitive: document.getElementById('wc-cs').textContent.trim() === 'true',\n"
        "    guided: document.getElementById('wc-guided').textContent.trim() === 'true'\n"
        "  };\n"
        "  document.getElementById('wc-container').appendChild(renderWriteCode(q));\n"
        "})();"
    )

    afmt = _card(
        '  <div id="wc-qt-b" style="display:none">{{QuestionText}}</div>\n'
        '  <div id="wc-code-b" style="display:none">{{QuestionCode}}</div>\n'
        '  <div id="wc-lang-b" style="display:none">{{Language}}</div>\n'
        '  <div id="wc-cs-b" style="display:none">{{CaseSensitive}}</div>\n'
        '  <div id="wc-guided-b" style="display:none">{{Guided}}</div>\n',
        'wc-container-b', js,
        "(function() {\n"
        "  var q = {\n"
        "    question_id: '',\n"
        "    question_text: document.getElementById('wc-qt-b').textContent,\n"
        "    question_code: document.getElementById('wc-code-b').textContent,\n"
        "    language: document.getElementById('wc-lang-b').textContent.trim(),\n"
        "    case_sensitive: document.getElementById('wc-cs-b').textContent.trim() === 'true',\n"
        "    guided: document.getElementById('wc-guided-b').textContent.trim() === 'true'\n"
        "  };\n"
        "  var node = renderWriteCode(q);\n"
        "  document.getElementById('wc-container-b').appendChild(node);\n"
        "  var btn = node.querySelector('button');\n"
        "  if (btn) setTimeout(function() { btn.click(); }, 0);\n"
        "})();"
    )

    return genanki.Model(
        _MODEL_IDS['write_code'], 'SimpleLearner — Write Code',
        fields=[
            {'name': 'QuestionText'}, {'name': 'QuestionCode'},
            {'name': 'Language'}, {'name': 'CaseSensitive'}, {'name': 'Guided'},
        ],
        templates=[{'name': 'Card', 'qfmt': qfmt, 'afmt': afmt}],
        css=_CSS,
    )

# ---------------------------------------------------------------------------
# Build all models (lazily cached)
# ---------------------------------------------------------------------------
_MODELS: dict = {}


def _get_models() -> dict:
    if not _MODELS:
        _MODELS.update({
            'qna':              _qna_model(),
            'fib':              _fib_model(),
            'mcq':              _mcq_model(),
            'list_completion':  _list_completion_model(),
            'descriptive_text': _descriptive_model(),
            'code_fib':         _code_fib_model(),
            'write_code':       _write_code_model(),
        })
    return _MODELS

# ---------------------------------------------------------------------------
# Note builders — one per question type
# ---------------------------------------------------------------------------

def _note_qna(q, m):
    return genanki.Note(
        model=m,
        guid=_guid('qna', q.get('question_id'), q.get('question_text', '')),
        fields=[
            _esc(q.get('question_text', '')),
            _esc(str(q.get('answer', ''))),
            'true' if q.get('case_sensitive') else 'false',
        ],
    )


def _note_fib(q, m):
    return genanki.Note(
        model=m,
        guid=_guid('fib', q.get('question_id'), q.get('question_text', '')),
        fields=[
            _esc(q.get('question_text', '')),
            'true' if q.get('case_sensitive') else 'false',
        ],
    )


def _note_mcq(q, m):
    return genanki.Note(
        model=m,
        guid=_guid('mcq', q.get('question_id'), q.get('question_text', '')),
        fields=[
            _esc(q.get('question_text', '')),
            _json_field(q.get('options') or []),
            _esc(str(q.get('correct_answer', ''))),
        ],
    )


def _note_list_completion(q, m):
    return genanki.Note(
        model=m,
        guid=_guid('list_completion', q.get('question_id'), q.get('question_text', '')),
        fields=[
            _esc(q.get('question_text', '')),
            _json_field(q.get('answer') or []),
            'true' if q.get('case_sensitive') else 'false',
            'true' if q.get('order_sensitive') else 'false',
        ],
    )


def _note_descriptive(q, m):
    return genanki.Note(
        model=m,
        guid=_guid('descriptive_text', q.get('question_id'), q.get('question_text', '')),
        fields=[
            _esc(q.get('question_text', '')),
            _esc(str(q.get('answer', ''))),
            'true' if q.get('case_sensitive') else 'false',
            'true' if q.get('guided') else 'false',
        ],
    )


def _note_code_fib(q, m):
    return genanki.Note(
        model=m,
        guid=_guid('code_fib', q.get('question_id'), q.get('question_text', '')),
        fields=[
            _esc(q.get('question_text', '')),
            _esc(q.get('question_code', '')),
            _esc(str(q.get('language', 'python'))),
            'true' if q.get('case_sensitive') else 'false',
        ],
    )


def _note_write_code(q, m):
    return genanki.Note(
        model=m,
        guid=_guid('write_code', q.get('question_id'), q.get('question_text', '')),
        fields=[
            _md(q.get('question_text', '')),
            _esc(q.get('question_code', '')),
            _esc(str(q.get('language', 'python'))),
            'true' if q.get('case_sensitive') else 'false',
            'true' if q.get('guided') else 'false',
        ],
    )


_BUILDERS = {
    'qna':              _note_qna,
    'fib':              _note_fib,
    'mcq':              _note_mcq,
    'list_completion':  _note_list_completion,
    'descriptive_text': _note_descriptive,
    'code_fib':         _note_code_fib,
    'write_code':       _note_write_code,
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print('Usage: python generatecards.py <notes.yaml> [output.apkg]')
        sys.exit(1)

    yaml_path = Path(sys.argv[1])
    if not yaml_path.exists():
        print(f'Error: file not found: {yaml_path}')
        sys.exit(1)

    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    questions = data.get('questions') or []
    if not questions:
        print('No questions found in YAML.')
        sys.exit(1)

    deck_name = yaml_path.stem.replace('_', ' ').title()
    deck_id = int(hashlib.sha1(yaml_path.name.encode()).hexdigest()[:8], 16)
    deck = genanki.Deck(deck_id, deck_name)

    models = _get_models()
    skipped = 0

    for q in questions:
        qt = q.get('question_type', '')
        builder = _BUILDERS.get(qt)
        if not builder:
            print(f'  Warning: skipping question_id={q.get("question_id")} — unknown type "{qt}"')
            skipped += 1
            continue
        try:
            note = builder(q, models[qt])
            deck.add_note(note)
        except Exception as e:
            print(f'  Warning: skipping question_id={q.get("question_id")} ({qt}) — {e}')
            skipped += 1

    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else yaml_path.with_suffix('.apkg')
    genanki.Package(deck).write_to_file(str(out_path))

    total = len(questions) - skipped
    print(f'Created  : {out_path}')
    print(f'Cards    : {total}  |  Skipped: {skipped}')


if __name__ == '__main__':
    main()
