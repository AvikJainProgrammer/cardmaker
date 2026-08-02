// File: question_types/code_fib.js

export function renderCodeFib(q) {
  const qDiv = document.createElement('div');
  qDiv.style.marginBottom = '2em';

  // Question label
  const label = document.createElement('div');
  // Use marked to render markdown as HTML
  label.innerHTML = window.marked.parse(`Q${q.question_id}: ${q.question_text}`);
  qDiv.appendChild(label);

  // Code block container
  const codeBlock = document.createElement('pre');
  codeBlock.style.background = '#1e1e1e';
  codeBlock.style.color = '#ccc';
  codeBlock.style.borderRadius = '8px';
  codeBlock.style.padding = '1em';
  codeBlock.style.whiteSpace = 'pre-wrap';
  codeBlock.style.lineHeight = '1.5em';
  codeBlock.style.fontFamily = 'monospace';

  const blanks = [];

  // Replace <<answer>> with <input>
  const rendered = (q.question_code || '')
    // .replace(/\//g, '//')
    .replace(/<<([\s\S]*?)>>/g, (_, answer) => {

      const length = answer.length;
      const id = blanks.length;
      blanks.push({ answer, id });
      return `<input type="text" class="blank-input" data-id="${id}" data-answer="${answer}" style="width:${length}ch">`;
    });

  codeBlock.innerHTML = rendered;
  qDiv.appendChild(codeBlock);

  // Tick mark container
  const resultDiv = document.createElement('div');
  resultDiv.style.marginTop = '0.5em';
  qDiv.appendChild(resultDiv);

  // Show answer button
  const showBtn = document.createElement('button');
  showBtn.textContent = 'Show Answer';
  showBtn.style.marginTop = '0.5em';
  showBtn.addEventListener('click', () => {
    blanks.forEach((blank, i) => {
      const input = inputElements[i];
      input.value = blank.answer;
    });
    validate();
  });
  qDiv.appendChild(showBtn);

  // Style for inputs
  const style = document.createElement('style');
  style.textContent = `
    .blank-input {
      background: transparent;
      color: #ffd700;
      border: none;
      border-bottom: 2px solid #888;
      font-family: monospace;
      font-size: 1em;
    }
    .blank-input:focus {
      outline: none;
      border-color: #fff;
    }
    .correct-mark {
      color: lightgreen;
      margin-right: 0.5em;
    }
    .all-correct {
      color: #0f0;
      font-weight: bold;
      margin-top: 0.5em;
    }
  `;
  document.head.appendChild(style);

  const inputElements = codeBlock.querySelectorAll('input');

  function validate() {
    let allCorrect = true;
    resultDiv.innerHTML = '';

    blanks.forEach((blank, i) => {
      const input = inputElements[i];
      const userAns = input.value;
      const correctAns = blank.answer;
      const match = q.case_sensitive
        ? userAns === correctAns
        : userAns.trim().toLowerCase() === correctAns.trim().toLowerCase();

      const tick = document.createElement('span');
      tick.className = 'correct-mark';
      tick.textContent = match ? '✔️' : '❌';
      resultDiv.appendChild(tick);

      if (!match) allCorrect = false;
    });

    if (allCorrect) {
      const allTick = document.createElement('div');
      allTick.className = 'all-correct';
      allTick.textContent = '✅ All answers are correct!';
      resultDiv.appendChild(allTick);
    }
  }

  inputElements.forEach(input => {
    input.addEventListener('input', validate);
  });

  return qDiv;
}