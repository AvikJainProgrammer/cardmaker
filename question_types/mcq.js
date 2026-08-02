export function renderMcq(q) {
  const qDiv = document.createElement('div');
  qDiv.style.marginBottom = '1em';

  const label = document.createElement('div');
  // Use marked to render markdown as HTML
  label.innerHTML = window.marked.parse(`Q${q.question_id}: ${q.question_text}`);
  qDiv.appendChild(label);

  const optionsDiv = document.createElement('div');
  const name = `mcq_${q.question_id}_${Math.random()}`;
  let selectedRadio = null;
  const check = document.createElement('span');
  check.style.marginLeft = '0.5em';

  q.options.forEach(option => {
    const optionLabel = document.createElement('label');
    optionLabel.style.display = 'block';
    optionLabel.style.marginLeft = '1em';

    const radio = document.createElement('input');
    radio.type = 'radio';
    radio.name = name;
    radio.value = option;

    radio.addEventListener('change', function() {
      if (radio.checked) {
        selectedRadio = radio;
        if (option === q.correct_answer) {
          check.textContent = '✔️';
        } else {
          check.textContent = '';
        }
      }
    });

    optionLabel.appendChild(radio);
    optionLabel.appendChild(document.createTextNode(option));
    optionsDiv.appendChild(optionLabel);
  });

  qDiv.appendChild(optionsDiv);
  qDiv.appendChild(check);

  const showBtn = document.createElement('button');
  showBtn.textContent = 'Show Answer';
  showBtn.style.marginLeft = '1em';

  showBtn.addEventListener('click', function() {
    const radios = optionsDiv.querySelectorAll('input[type="radio"]');
    radios.forEach(radio => {
      if (radio.value === q.correct_answer) {
        radio.checked = true;
        check.textContent = '✔️';
      } else {
        radio.checked = false;
      }
    });
  });

  qDiv.appendChild(showBtn);
  return qDiv;
}