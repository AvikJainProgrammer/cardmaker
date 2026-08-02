// File: question_types/write_code.js

export function renderWriteCode(q) {
  const qDiv = document.createElement('div');
  qDiv.style.marginBottom = '2em';

  const label = document.createElement('div');
  // Use marked to render markdown as HTML
  label.innerHTML = window.marked.parse(`Q${q.question_id}: ${q.question_text}`);
  label.style.marginBottom = '0.5em';
  qDiv.appendChild(label);

  const editorContainer = document.createElement('div');
  editorContainer.id = `monaco-editor-${q.question_id}`;
  editorContainer.style.height = '200px';
  editorContainer.style.border = '1px solid #555';
  editorContainer.style.borderRadius = '4px';
  qDiv.appendChild(editorContainer);

  const resultDiv = document.createElement('div');
  resultDiv.style.marginTop = '0.5em';
  resultDiv.style.fontSize = '1.2em';
  qDiv.appendChild(resultDiv);

  const showBtn = document.createElement('button');
  showBtn.textContent = 'Show Answer';
  showBtn.style.marginTop = '0.5em';
  showBtn.style.display = 'block';
  qDiv.appendChild(showBtn);

  // Load Monaco loader script if not already loaded
  if (!window.require) {
    const loaderScript = document.createElement('script');
    loaderScript.src = 'https://unpkg.com/monaco-editor@0.45.0/min/vs/loader.js';
    loaderScript.onload = () => initMonaco();
    document.body.appendChild(loaderScript);
  } else {
    initMonaco();
  }

  function initMonaco() {
    window.require.config({ paths: { vs: 'https://unpkg.com/monaco-editor@0.45.0/min/vs' } });
    window.require(['vs/editor/editor.main'], () => {
      const editor = monaco.editor.create(editorContainer, {
        value: '',
        language: q.language || 'python',
        theme: 'vs-dark',
        automaticLayout: true
      });

      const expectedCode = (q.question_code || '').trim();
      const isCaseSensitive = !!q.case_sensitive;
      const guided = !!q.guided;

      function validate() {
        const userCode = editor.getValue().trim();
        const userCodeForCompare = isCaseSensitive ? userCode : userCode.toLowerCase();
        const expectedForCompare = isCaseSensitive ? expectedCode : expectedCode.toLowerCase();

        resultDiv.innerHTML = '';

        if (guided && expectedForCompare.startsWith(userCodeForCompare)) {
          const hint = document.createElement('span');
          hint.textContent = '👍 Keep going...';
          hint.style.color = '#ff0';
          resultDiv.appendChild(hint);
        }

        if (userCodeForCompare === expectedForCompare) {
          const tick = document.createElement('span');
          tick.textContent = '✔️ Correct!';
          tick.style.color = 'lightgreen';
          resultDiv.appendChild(tick);
        }
      }

      editor.onDidChangeModelContent(validate);

      showBtn.addEventListener('click', () => {
        editor.setValue(expectedCode);
        validate();
      });
    });
  }

  return qDiv;
}