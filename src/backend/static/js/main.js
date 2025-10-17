document.addEventListener('DOMContentLoaded', function() {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    // --- Логика модального окна для задач ---
    const addTaskModal = document.getElementById('add-task-modal');
    const addTaskBtn = document.getElementById('add-task-btn');
    const closeBtn = addTaskModal.querySelector('.modal-close-btn');
    const addTaskForm = document.getElementById('add-task-form');

    if (addTaskBtn) {
        addTaskBtn.addEventListener('click', () => {
            addTaskModal.style.display = 'flex';
        });

        closeBtn.addEventListener('click', () => {
            addTaskModal.style.display = 'none';
        });

        addTaskModal.addEventListener('click', (e) => {
            if (e.target === addTaskModal) {
                addTaskModal.style.display = 'none';
            }
        });

        addTaskForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(addTaskForm);
            const submitBtn = addTaskForm.querySelector('button[type="submit"]');

            clearFormErrors(addTaskForm);
            
            try {
                const response = await fetch(addTaskForm.action, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': csrfToken,
                        'X-Requested-With': 'XMLHttpRequest' // Важно для Django
                    },
                });

                // Блокируем кнопку на время запроса
                submitBtn.disabled = true;
                submitBtn.textContent = 'Добавляем...';

                const result = await response.json();

                if (result.success) {
                    addTaskToDOM(result.task);
                    addTaskModal.style.display = 'none';
                    addTaskForm.reset();
                } else if (result.errors) {
                    displayFormErrors(addTaskForm, result.errors);
                } else {
                    // Общая ошибка, если поле errors не пришло
                    alert('Произошла неизвестная ошибка.');
                }
            } catch (error) {
                console.error('Ошибка при отправке формы:', error);
                alert('Произошла сетевая ошибка.');
            } finally {
                // Возвращаем кнопку в исходное состояние
                submitBtn.disabled = false;
                submitBtn.textContent = 'Добавить задачу';
            }
        });
    }

    // --- Логика загрузки документов ---
    const docUploadInput = document.getElementById('document-upload-input');
    if (docUploadInput) {
        docUploadInput.addEventListener('change', async (e) => {
            const files = e.target.files;
            if (files.length === 0) return;

            const formData = new FormData();
            for (const file of files) {
                formData.append('files', file);
            }

            try {
                const response = await fetch('/documents/upload/', { // URL для загрузки
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': csrfToken,
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                });

                const result = await response.json();

                if (result.success) {
                    result.documents.forEach(addDocumentToDOM);
                } else {
                    alert('Ошибка загрузки: ' + result.error);
                }
            } catch (error) {
                console.error('Ошибка при загрузке файла:', error);
                alert('Произошла сетевая ошибка при загрузке файла.');
            }
            
            // Сбрасываем input, чтобы можно было загрузить тот же файл снова
            e.target.value = '';
        });
    }
});

// Функция для добавления задачи в список на странице
function addTaskToDOM(task) {
    const container = document.getElementById('task-list-container');
    const emptyState = container.querySelector('.empty-state');
    if (emptyState) emptyState.remove();

    let tagsHTML = '';
    if (task.tags && task.tags.length > 0) {
        tagsHTML = `<div class="task-tags">${task.tags.map(tag => `<span class="tag">${tag.name}</span>`).join('')}</div>`;
    }

    const taskHTML = `
        <li class="task-item">
            <div class="task-info">
                <div class="task-name">${task.name}</div>
                <div class="task-meta">
                    ${task.end_time ? `⏰ до ${new Date(task.end_time).toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })}` : ''}
                </div>
                ${tagsHTML}
            </div>
        </li>
    `;
    container.insertAdjacentHTML('afterbegin', taskHTML);
}

// Функция для добавления документа в список на странице
function addDocumentToDOM(doc) {
    const container = document.getElementById('doc-list-container');
    const emptyState = container.querySelector('.empty-state');
    if (emptyState) emptyState.remove();

    const docHTML = `
        <li class="doc-item">
            <div class="doc-info">
                <div class="doc-name">📄 ${doc.name}</div>
                <div class="doc-meta">
                    .${doc.extension} • ${doc.uploaded_at_formatted}
                </div>
            </div>
        </li>
    `;
    container.insertAdjacentHTML('afterbegin', docHTML);
}

// --- Функции для работы с ошибками форм ---

function displayFormErrors(form, errors) {
    // Отображаем ошибки для конкретных полей
    for (const fieldName in errors) {
        const field = form.querySelector(`[name=${fieldName}]`);
        if (field) {
            const errorContainer = field.parentElement.querySelector('.field-error');
            if (errorContainer) {
                errorContainer.textContent = errors[fieldName].join(' ');
            }
        }
    }
}

function clearFormErrors(form) {
    form.querySelectorAll('.field-error').forEach(el => {
        el.textContent = '';
    });
}