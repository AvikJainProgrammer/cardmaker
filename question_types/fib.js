export function renderFib(q) {
  const qDiv = document.createElement('div');
  qDiv.style.marginBottom = '1em';

  const idSpan = document.createElement('span');
  idSpan.textContent = `Q${q.question_id}: `;
  qDiv.appendChild(idSpan);

  const regex = /<<([^<>]+)>>/g;
  let lastIndex = 0;
  let match;
  let blankIndex = 0;
  const answers = [];
  const elements = [];

  while ((match = regex.exec(q.question_text)) !== null) {
    if (match.index > lastIndex) {
      qDiv.appendChild(document.createTextNode(q.question_text.slice(lastIndex, match.index)));
    }
    const correctAns = match[1];
    answers.push(correctAns);

    const input = document.createElement('input');
    input.type = 'text';
    input.style.width = '8em';
    input.style.margin = '0 0.3em';
    input.dataset.index = blankIndex;

    const check = document.createElement('span');
    check.style.marginLeft = '0.3em';

    input.addEventListener('input', function() {
      let userAns = input.value;
      let isCorrect = false;
      if (q.case_sensitive) {
        isCorrect = userAns === correctAns;
      } else {
        isCorrect = userAns.trim().toLowerCase() === correctAns.trim().toLowerCase();
      }
      check.textContent = isCorrect ? '✔️' : '';
    });

    qDiv.appendChild(input);
    qDiv.appendChild(check);

    elements.push({input, check, correctAns});
    lastIndex = regex.lastIndex;
    blankIndex++;
  }

  if (lastIndex < q.question_text.length) {
    qDiv.appendChild(document.createTextNode(q.question_text.slice(lastIndex)));
  }

  const showBtn = document.createElement('button');
  showBtn.textContent = 'Show Answer';
  showBtn.style.marginLeft = '1em';

  showBtn.addEventListener('click', function() {
    elements.forEach(({input, check, correctAns}) => {
      input.value = correctAns;
      check.textContent = '✔️';
    });
  });

  qDiv.appendChild(showBtn);
  return qDiv;
}