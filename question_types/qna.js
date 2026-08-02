export function renderQna(q) {
  const qDiv = document.createElement('div');
  qDiv.style.marginBottom = '1em';

  const label = document.createElement('label');
  // Use marked to render markdown as HTML
  label.innerHTML = window.marked.parse(`Q${q.question_id}: ${q.question_text}`);
  qDiv.appendChild(label);

  const input = document.createElement('input');
  input.type = 'text';
  input.style.marginLeft = '1em';

  const check = document.createElement('span');
  check.style.marginLeft = '0.5em';

  input.addEventListener('input', function() {
    let userAns = input.value;
    let correctAns = q.answer;
    let isCorrect = false;
    if (q.case_sensitive) {
      isCorrect = userAns === correctAns;
    } else {
      isCorrect = userAns.trim().toLowerCase() === (correctAns || '').trim().toLowerCase();
    }
    check.textContent = isCorrect ? '✔️' : '';
  });

  qDiv.appendChild(input);
  qDiv.appendChild(check);

  const showBtn = document.createElement('button');
  showBtn.textContent = 'Show Answer';
  showBtn.style.marginLeft = '1em';

  const answerSpan = document.createElement('span');
  answerSpan.style.marginLeft = '0.5em';

  showBtn.addEventListener('click', function() {
    answerSpan.textContent = q.answer;
  });

  qDiv.appendChild(showBtn);
  qDiv.appendChild(answerSpan);

  return qDiv;
}