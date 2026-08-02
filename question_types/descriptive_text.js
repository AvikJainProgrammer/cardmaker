export function renderDescriptiveText(q) {
  const qDiv = document.createElement('div');
  qDiv.style.marginBottom = '1em';

  const label = document.createElement('div');
  // Use marked to render markdown as HTML
  label.innerHTML = window.marked.parse(`Q${q.question_id}: ${q.question_text}`);
  qDiv.appendChild(label);

  const textarea = document.createElement('textarea');
  textarea.rows = 4;
  textarea.cols = 60;
  textarea.style.display = 'block';
  textarea.style.marginTop = '0.5em';

  const check = document.createElement('span');
  check.style.marginLeft = '0.5em';

  const thumbs = document.createElement('span');
  thumbs.style.marginLeft = '0.5em';

  textarea.addEventListener('input', function() {
    let userAns = textarea.value;
    let correctAns = q.answer || '';
    let isCorrect = false;
    let isPrefix = false;

    if (q.case_sensitive) {
      isCorrect = userAns.trim() === correctAns.trim();
      isPrefix = correctAns.trim().startsWith(userAns.trim());
    } else {
      isCorrect = userAns.trim().toLowerCase() === correctAns.trim().toLowerCase();
      isPrefix = correctAns.trim().toLowerCase().startsWith(userAns.trim().toLowerCase());
    }
    check.textContent = isCorrect ? '✔️' : '';
    thumbs.textContent = (q.guided && !isCorrect && userAns.trim() && isPrefix) ? '👍' : '';
  });

  qDiv.appendChild(textarea);
  qDiv.appendChild(check);
  qDiv.appendChild(thumbs);

  const showBtn = document.createElement('button');
  showBtn.textContent = 'Show Answer';
  showBtn.style.marginLeft = '1em';

  const answerSpan = document.createElement('div');
  answerSpan.style.marginTop = '0.5em';
  answerSpan.style.fontStyle = 'italic';
  answerSpan.style.color = '#555';

  showBtn.addEventListener('click', function() {
    answerSpan.textContent = `Answer: ${q.answer}`;
  });

  qDiv.appendChild(showBtn);
  qDiv.appendChild(answerSpan);

  return qDiv;
}