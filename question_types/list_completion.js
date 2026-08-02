export function renderListCompletion(q) {
  const qDiv = document.createElement('div');
  qDiv.style.marginBottom = '1em';

  const label = document.createElement('div');
  // Use marked to render markdown as HTML
  label.innerHTML = window.marked.parse(`Q${q.question_id}: ${q.question_text}`);
  qDiv.appendChild(label);

  const answers = Array.isArray(q.answer) ? q.answer : [];
  const elements = [];

  answers.forEach((ans, idx) => {
    const input = document.createElement('input');
    input.type = 'text';
    input.style.margin = '0.3em';
    input.style.width = '12em';

    const check = document.createElement('span');
    check.style.marginLeft = '0.3em';

    qDiv.appendChild(input);
    qDiv.appendChild(check);
    elements.push({input, check});
  });

  function validateListCompletion() {
    const matched = new Array(answers.length).fill(false);

    elements.forEach((el, idx) => {
      let userAns = el.input.value;
      let isCorrect = false;

      if (q.order_sensitive) {
        let correctAns = answers[idx];
        if (q.case_sensitive) {
          isCorrect = userAns === correctAns;
        } else {
          isCorrect = userAns.trim().toLowerCase() === correctAns.trim().toLowerCase();
        }
        matched[idx] = isCorrect;
      } else {
        for (let i = 0; i < answers.length; i++) {
          if (matched[i]) continue;
          let correctAns = answers[i];
          if (q.case_sensitive) {
            if (userAns === correctAns) {
              isCorrect = true;
              matched[i] = true;
              break;
            }
          } else {
            if (userAns.trim().toLowerCase() === correctAns.trim().toLowerCase()) {
              isCorrect = true;
              matched[i] = true;
              break;
            }
          }
        }
      }
      el.check.textContent = isCorrect ? '✔️' : '';
    });
  }

  elements.forEach(el => {
    el.input.addEventListener('input', validateListCompletion);
  });

  const showBtn = document.createElement('button');
  showBtn.textContent = 'Show Answer';
  showBtn.style.marginLeft = '1em';

  showBtn.addEventListener('click', function() {
    elements.forEach((el, idx) => {
      el.input.value = answers[idx];
      el.check.textContent = '✔️';
    });
  });

  qDiv.appendChild(showBtn);
  return qDiv;
}