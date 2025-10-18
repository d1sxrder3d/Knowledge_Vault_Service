function toggleTaskStatus(taskId, checkbox) {
    const isCompleted = checkbox.hasClass('checked');
    const newStatus = isCompleted ? 'pending' : 'completed';
    
    $.ajax({
        url: `/tasks/${taskId}/`,
        method: 'PATCH',
        headers: {
            'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val(),
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        data: JSON.stringify({
            status: newStatus
        }),
        success: function() {
            checkbox.toggleClass('checked');
            const taskItem = checkbox.closest('.task-item');
            taskItem.toggleClass('completed');
            
            if (checkbox.hasClass('checked')) {
                checkbox.html('<i class="bi bi-check-lg"></i>');
            } else {
                checkbox.html('');
            }
        },
        error: function() {
            showNotification('error', 'Ошибка при обновлении статуса');
        }
    });
}// Tasks Management
let selectedTags = [];
let taskModal;

$(document).ready(function() {
    taskModal = new bootstrap.Modal(document.getElementById('taskModal'));
    
    // New Task Button
    $('#newTaskBtn').click(function() {
        openTaskModal();
    });

    // Quick Add Task
    $('#newTaskBtn').dblclick(function() {
        $('#inlineAddTask').slideDown();
        $('#quickTaskName').focus();
    });

    $('#quickAddConfirm').click(function() {
        quickAddTask();
    });

    $('#quickAddCancel').click(function() {
        $('#inlineAddTask').slideUp();
        $('#quickTaskName').val('');
    });

    $('#quickTaskName').keypress(function(e) {
        if (e.which === 13) {
            quickAddTask();
        } else if (e.which === 27) {
            $('#quickAddCancel').click();
        }
    });

    // Save Task
    $('#saveTaskBtn').click(function() {
        saveTask();
    });

    // Quick Date Buttons
    $('.quick-date-btn').click(function() {
        const days = parseInt($(this).data('days'));
        const date = new Date();
        date.setDate(date.getDate() + days);
        const dateStr = date.toISOString().split('T')[0];
        $('#taskDate').val(dateStr);
        
        $('.quick-date-btn').removeClass('active');
        $(this).addClass('active');
    });

    // Quick Time Buttons
    $('.quick-time-btn').click(function() {
        const timeType = $(this).data('time');
        const now = new Date();
        
        if (timeType === 'now') {
            // Round to nearest 5 minutes
            const minutes = Math.round(now.getMinutes() / 5) * 5;
            now.setMinutes(minutes);
        } else if (timeType === 'hour') {
            now.setHours(now.getHours() + 1);
            now.setMinutes(0);
        }
        
        const timeStr = now.toTimeString().slice(0, 5);
        $('#taskTime').val(timeStr);
        
        $('.quick-time-btn').removeClass('active');
        $(this).addClass('active');
    });

    // Tag Input
    $('#tagInput').on('input', function() {
        const query = $(this).val().toLowerCase();
        if (query.length > 0) {
            showTagSuggestions(query);
        } else {
            $('#tagSuggestions').hide();
        }
    });

    $('#tagInput').keypress(function(e) {
        if (e.which === 13 || e.which === 188) { // Enter or comma
            e.preventDefault();
            const tagName = $(this).val().trim();
            if (tagName) {
                addNewTag(tagName);
                $(this).val('');
                $('#tagSuggestions').hide();
            }
        }
    });

    // Existing Tags Selection
    $('.existing-tag').click(function() {
        const tagId = $(this).data('tag-id');
        const tagName = $(this).data('tag-name');
        const tagColor = $(this).data('tag-color');
        
        if ($(this).hasClass('selected')) {
            $(this).removeClass('selected');
            removeTagFromSelection(tagId);
        } else {
            $(this).addClass('selected');
            addTagToSelection(tagId, tagName, tagColor, true);
        }
    });

    // Task Checkboxes
    $(document).on('click', '.task-checkbox', function() {
        const taskId = $(this).data('task-id');
        toggleTaskStatus(taskId, $(this));
    });

    // Subtask Toggle
    $(document).on('click', '.subtask-toggle', function() {
        const taskId = $(this).data('task-id');
        const container = $('#subtasks-' + taskId);
        const icon = $(this).find('i');
        
        container.slideToggle();
        $(this).toggleClass('collapsed');
    });

    // Character Counter
    $('#taskDescription').on('input', function() {
        const length = $(this).val().length;
        const counter = $('#descCharCount');
        counter.text(length);
        
        if (length > 450) {
            counter.parent().addClass('warning');
        } else {
            counter.parent().removeClass('warning');
        }
        
        if (length >= 500) {
            counter.parent().addClass('danger');
        } else {
            counter.parent().removeClass('danger');
        }
    });

    // Close suggestions when clicking outside
    $(document).click(function(e) {
        if (!$(e.target).closest('.tag-input-container').length) {
            $('#tagSuggestions').hide();
        }
    });
});

function openTaskModal(taskId = null, parentId = null) {
    // Reset form
    $('#taskForm')[0].reset();
    $('#taskId').val('');
    $('#parentId').val('');
    selectedTags = [];
    $('.existing-tag').removeClass('selected');
    $('.quick-date-btn, .quick-time-btn').removeClass('active');
    $('#tagInputWrapper .selected-tag').remove();
    
    if (taskId) {
        // Edit mode
        $('#taskModalTitle').text('Редактировать задачу');
        loadTask(taskId);
    } else if (parentId) {
        // Subtask mode
        $('#taskModalTitle').text('Новая подзадача');
        $('#parentId').val(parentId);
        loadParentTaskData(parentId);
    } else {
        // New task mode
        $('#taskModalTitle').text('Новая задача');
    }
    
    taskModal.show();
}

function quickAddTask() {
    const name = $('#quickTaskName').val().trim();
    if (!name) return;
    
    const formData = new FormData();
    formData.append('name', name);
    formData.append('description', '');
    formData.append('csrfmiddlewaretoken', $('[name=csrfmiddlewaretoken]').val());
    
    $.ajax({
        url: '/tasks/add/',
        method: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        headers: {'X-Requested-With': 'XMLHttpRequest'},
        success: function(response) {
            if (response.success) {
                addTaskToList(response.task);
                $('#quickTaskName').val('');
                $('#inlineAddTask').slideUp();
                showNotification('success', response.message);
            } else {
                showNotification('error', response.message);
            }
        },
        error: function() {
            showNotification('error', 'Ошибка при создании задачи');
        }
    });
}

function saveTask() {
    const taskId = $('#taskId').val();
    const formData = new FormData($('#taskForm')[0]);
    
    // Add selected tags
    const existingTagIds = selectedTags.filter(t => t.existing).map(t => t.id).join(',');
    const newTagNames = selectedTags.filter(t => !t.existing).map(t => t.name).join(',');
    
    formData.set('existing_tags', existingTagIds);
    formData.set('new_tags', newTagNames);
    
    // Combine date and time
    const date = $('#taskDate').val();
    const time = $('#taskTime').val();
    if (date && time) {
        formData.set('end_time', date + ' ' + time);
    } else if (date) {
        formData.set('end_time', date + ' 23:59');
    }
    
    // Если редактируем существующую задачу
    if (taskId) {
        updateTask(taskId, formData);
    } else {
        createTask(formData);
    }
}

function createTask(formData) {
    $.ajax({
        url: '/tasks/add/',
        method: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        headers: {'X-Requested-With': 'XMLHttpRequest'},
        success: function(response) {
            if (response.success) {
                taskModal.hide();
                addTaskToList(response.task);
                showNotification('success', response.message);
            } else {
                displayFormErrors(response.errors);
                showNotification('error', response.message);
            }
        },
        error: function() {
            showNotification('error', 'Ошибка при сохранении задачи');
        }
    });
}

function updateTask(taskId, formData) {
    // Convert FormData to JSON for PATCH request
    const data = {
        name: formData.get('name'),
        description: formData.get('description'),
        end_time: formData.get('end_time'),
    };
    
    // Parse tags
    const existingTags = formData.get('existing_tags');
    const newTags = formData.get('new_tags');
    
    if (existingTags) {
        data.existing_tags = existingTags;
    }
    if (newTags) {
        data.new_tags = newTags;
    }
    
    $.ajax({
        url: `/tasks/${taskId}/`,
        method: 'PATCH',
        headers: {
            'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val(),
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        data: JSON.stringify(data),
        success: function(response) {
            if (response.success) {
                taskModal.hide();
                // Update task in DOM
                updateTaskInList(taskId, data);
                showNotification('success', 'Задача обновлена');
            } else {
                showNotification('error', 'Ошибка при обновлении задачи');
            }
        },
        error: function() {
            showNotification('error', 'Ошибка при обновлении задачи');
        }
    });
}

function updateTaskInList(taskId, data) {
    const taskElement = $(`.task-item[data-task-id="${taskId}"]`).first();
    
    taskElement.find('.task-name').first().text(data.name);
    
    if (data.description) {
        let descElement = taskElement.find('.task-description').first();
        if (descElement.length) {
            descElement.text(data.description);
        } else {
            taskElement.find('.task-name').after(`<div class="task-description">${escapeHtml(data.description)}</div>`);
        }
    }
    
    if (data.end_time) {
        taskElement.attr('data-end-time', data.end_time);
        const timeElement = taskElement.find('.task-time span');
        if (timeElement.length) {
            timeElement.text(formatDateTime(data.end_time));
        }
    }
}

function addTaskToList(task) {
    // Remove empty state if exists
    $('.empty-state').remove();
    
    const taskHtml = createTaskHtml(task);
    $('#tasksList').prepend(taskHtml);
    
    // Animate
    $(`[data-task-id="${task.id}"]`).hide().slideDown();
}

function createTaskHtml(task) {
    let tagsHtml = '';
    if (task.tags && task.tags.length > 0) {
        tagsHtml = '<div class="task-tags">';
        task.tags.forEach(tag => {
            tagsHtml += `<span class="task-tag" style="background-color: ${tag.color || '#5865f2'};">${tag.name}</span>`;
        });
        tagsHtml += '</div>';
    }
    
    let timeHtml = '';
    if (task.end_time) {
        timeHtml = `
            <div class="task-time">
                <i class="bi bi-clock"></i>
                <span>${formatDateTime(task.end_time)}</span>
            </div>
        `;
    }
    
    return `
        <div class="task-item" data-task-id="${task.id}" data-end-time="${task.end_time || ''}">
            <div class="task-header">
                <div class="task-checkbox" data-task-id="${task.id}"></div>
                <div class="task-content">
                    <div class="task-name">${escapeHtml(task.name)}</div>
                    ${task.description ? `<div class="task-description">${escapeHtml(task.description)}</div>` : ''}
                    <div class="task-meta">
                        ${timeHtml}
                        ${tagsHtml}
                    </div>
                </div>
                <div class="task-actions">
                    <button class="task-action-btn" onclick="addSubtask(${task.id})">
                        <i class="bi bi-plus-square"></i>
                    </button>
                    <button class="task-action-btn" onclick="editTask(${task.id})">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="task-action-btn delete" onclick="deleteTask(${task.id})">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </div>
        </div>
    `;
}

function addSubtask(parentId) {
    openTaskModal(null, parentId);
}

function editTask(taskId) {
    openTaskModal(taskId);
}

function loadTask(taskId) {
    // Fetch task data via AJAX
    $.ajax({
        url: `/tasks/${taskId}/get/`,
        method: 'GET',
        headers: {'X-Requested-With': 'XMLHttpRequest'},
        success: function(response) {
            if (response.success) {
                const task = response.task;
                $('#taskId').val(task.id);
                $('#taskName').val(task.name);
                $('#taskDescription').val(task.description || '');
                
                // Set date and time
                if (task.end_time) {
                    const [date, time] = task.end_time.split(' ');
                    $('#taskDate').val(date);
                    $('#taskTime').val(time);
                }
                
                // Set tags
                if (task.tags && task.tags.length > 0) {
                    task.tags.forEach(tag => {
                        $(`.existing-tag[data-tag-id="${tag.id}"]`).addClass('selected');
                        addTagToSelection(tag.id, tag.name, tag.color, true);
                    });
                }
            }
        },
        error: function() {
            showNotification('error', 'Ошибка при загрузке данных задачи');
        }
    });
}

function loadParentTaskData(parentId) {
    const parentElement = $(`.task-item[data-task-id="${parentId}"]`);
    const endTime = parentElement.data('end-time');
    
    if (endTime) {
        const date = endTime.split(' ')[0];
        const time = endTime.split(' ')[1];
        $('#taskDate').val(date);
        $('#taskTime').val(time);
    }
    
    // Copy tags
    parentElement.find('.task-tag').each(function() {
        const tagName = $(this).text();
        const tagColor = $(this).css('background-color');
        // Find matching tag and select it
        $(`.existing-tag[data-tag-name="${tagName}"]`).click();
    });
}

function deleteTask(taskId) {
    if (!confirm('Удалить эту задачу?')) return;
    
    $.ajax({
        url: `/tasks/${taskId}/`,
        method: 'DELETE',
        headers: {
            'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val(),
            'X-Requested-With': 'XMLHttpRequest'
        },
        success: function() {
            $(`.task-item[data-task-id="${taskId}"]`).slideUp(function() {
                $(this).remove();
                checkEmptyState();
            });
            showNotification('success', 'Задача удалена');
        },
        error: function() {
            showNotification('error', 'Ошибка при удалении задачи');
        }
    });
}

function toggleTaskStatus(taskId, checkbox) {
    const isCompleted = checkbox.hasClass('checked');
    const newStatus = isCompleted ? 'pending' : 'completed';
    
    $.ajax({
        url: `/api/tasks/${taskId}/`,
        method: 'PATCH',
        headers: {
            'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val(),
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        data: JSON.stringify({
            status: newStatus
        }),
        success: function() {
            checkbox.toggleClass('checked');
            const taskItem = checkbox.closest('.task-item');
            taskItem.toggleClass('completed');
            
            if (checkbox.hasClass('checked')) {
                checkbox.html('<i class="bi bi-check-lg"></i>');
            } else {
                checkbox.html('');
            }
        },
        error: function() {
            showNotification('error', 'Ошибка при обновлении статуса');
        }
    });
}

// Tag Management
function showTagSuggestions(query) {
    const suggestions = [];
    
    // Search existing tags
    $('.existing-tag').each(function() {
        const tagName = $(this).data('tag-name').toLowerCase();
        if (tagName.includes(query) && !isTagSelected($(this).data('tag-id'))) {
            suggestions.push({
                id: $(this).data('tag-id'),
                name: $(this).data('tag-name'),
                color: $(this).data('tag-color'),
                existing: true
            });
        }
    });
    
    // Add "Create new" option
    suggestions.push({
        name: query,
        existing: false
    });
    
    renderTagSuggestions(suggestions);
}

function renderTagSuggestions(suggestions) {
    const container = $('#tagSuggestions');
    container.empty();
    
    suggestions.forEach(tag => {
        let html;
        if (tag.existing) {
            html = `
                <div class="tag-suggestion-item" data-tag='${JSON.stringify(tag)}'>
                    <span class="tag-suggestion-tag" style="background-color: ${tag.color};">${tag.name}</span>
                </div>
            `;
        } else {
            html = `
                <div class="tag-suggestion-item" data-tag='${JSON.stringify(tag)}'>
                    <span class="tag-suggestion-create">
                        <i class="bi bi-plus-circle"></i> Создать "${tag.name}"
                    </span>
                </div>
            `;
        }
        container.append(html);
    });
    
    container.show();
    
    // Click handler
    $('.tag-suggestion-item').click(function() {
        const tag = JSON.parse($(this).attr('data-tag'));
        if (tag.existing) {
            addTagToSelection(tag.id, tag.name, tag.color, true);
            $(`.existing-tag[data-tag-id="${tag.id}"]`).addClass('selected');
        } else {
            addNewTag(tag.name);
        }
        $('#tagInput').val('');
        container.hide();
    });
}

function addTagToSelection(id, name, color, existing = true) {
    if (isTagSelected(id)) return;
    
    selectedTags.push({ id, name, color, existing });
    
    const tagHtml = `
        <span class="selected-tag" data-tag-id="${id}" style="background-color: ${color};">
            ${name}
            <i class="bi bi-x remove-tag" onclick="removeTag(${id})"></i>
        </span>
    `;
    
    $('#tagInput').before(tagHtml);
}

function addNewTag(name) {
    const randomColor = getRandomColor();
    const tempId = 'new_' + Date.now();
    
    selectedTags.push({ 
        id: tempId, 
        name: name, 
        color: randomColor, 
        existing: false 
    });
    
    const tagHtml = `
        <span class="selected-tag" data-tag-id="${tempId}" style="background-color: ${randomColor};">
            ${name}
            <i class="bi bi-x remove-tag" onclick="removeTag('${tempId}')"></i>
        </span>
    `;
    
    $('#tagInput').before(tagHtml);
}

function removeTag(id) {
    selectedTags = selectedTags.filter(t => t.id != id);
    $(`.selected-tag[data-tag-id="${id}"]`).remove();
    $(`.existing-tag[data-tag-id="${id}"]`).removeClass('selected');
}

function removeTagFromSelection(id) {
    selectedTags = selectedTags.filter(t => t.id != id);
    $(`.selected-tag[data-tag-id="${id}"]`).remove();
}

function isTagSelected(id) {
    return selectedTags.some(t => t.id == id);
}

function getRandomColor() {
    const colors = [
        '#5865f2', '#3ba55d', '#ed4245', '#faa61a', 
        '#3498db', '#9b59b6', '#e91e63', '#00bcd4'
    ];
    return colors[Math.floor(Math.random() * colors.length)];
}

// Utility Functions
function formatDateTime(datetime) {
    if (!datetime) return '';
    const date = new Date(datetime.replace(' ', 'T'));
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${day}.${month}.${year} ${hours}:${minutes}`;
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

function displayFormErrors(errors) {
    // Clear previous errors
    $('.is-invalid').removeClass('is-invalid');
    $('.invalid-feedback').empty();
    
    // Display new errors
    for (let field in errors) {
        const input = $(`[name="${field}"]`);
        input.addClass('is-invalid');
        input.siblings('.invalid-feedback').text(errors[field][0]);
    }
}

function checkEmptyState() {
    if ($('.task-item').length === 0) {
        $('#tasksList').html(`
            <div class="empty-state">
                <i class="bi bi-inbox"></i>
                <p>Задач пока нет</p>
                <small>Создайте свою первую задачу</small>
            </div>
        `);
    }
}

function showNotification(type, message) {
    const alertClass = type === 'success' ? 'alert-success-custom' : 'alert-danger-custom';
    const alert = $(`
        <div class="alert-custom ${alertClass} fade-in">
            ${message}
        </div>
    `);
    
    $('.main-container').prepend(alert);
    
    setTimeout(() => {
        alert.fadeOut(() => alert.remove());
    }, 3000);
}