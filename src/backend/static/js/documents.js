// Documents Management
let documentModal;
let currentDocumentId = null;

$(document).ready(function() {
    documentModal = new bootstrap.Modal(document.getElementById('documentModal'));
    
    // File Input
    $('#fileInput').change(function(e) {
        const files = e.target.files;
        if (files.length > 0) {
            uploadDocuments(files);
        }
    });

    // Save Document
    $('#saveDocBtn').click(function() {
        saveDocument();
    });

    // Drag and drop (optional enhancement)
    setupDragAndDrop();
});

function uploadDocuments(files) {
    const formData = new FormData();
    
    for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
    }
    
    formData.append('csrfmiddlewaretoken', $('[name=csrfmiddlewaretoken]').val());
    
    // Show loading
    showUploadProgress();
    
    $.ajax({
        url: '/documents/upload/',
        method: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        headers: {'X-Requested-With': 'XMLHttpRequest'},
        success: function(response) {
            hideUploadProgress();
            if (response.success) {
                response.documents.forEach(doc => {
                    addDocumentToList(doc);
                });
                showNotification('success', `Загружено файлов: ${response.documents.length}`);
            } else {
                showNotification('error', response.error || 'Ошибка при загрузке');
            }
        },
        error: function() {
            hideUploadProgress();
            showNotification('error', 'Ошибка при загрузке документов');
        }
    });
    
    // Reset file input
    $('#fileInput').val('');
}

function addDocumentToList(doc) {
    // Remove empty state if exists
    $('.documents-grid .empty-state').remove();
    
    const docHtml = createDocumentHtml(doc);
    $('.documents-grid').prepend(docHtml);
    
    // Animate
    $(`.document-card[data-doc-id="${doc.id}"]`).hide().fadeIn();
}

function createDocumentHtml(doc) {
    const extension = doc.extension ? doc.extension.toLowerCase() : '';
    let iconClass = 'bi-file-earmark';
    let iconColor = '';
    
    if (extension === 'pdf') {
        iconClass = 'bi-file-pdf';
        iconColor = 'color: #ed4245;';
    } else if (['doc', 'docx'].includes(extension)) {
        iconClass = 'bi-file-word';
        iconColor = 'color: #4752c4;';
    } else if (['xls', 'xlsx'].includes(extension)) {
        iconClass = 'bi-file-excel';
        iconColor = 'color: #3ba55d;';
    } else if (['jpg', 'jpeg', 'png', 'gif'].includes(extension)) {
        iconClass = 'bi-file-image';
        iconColor = 'color: #faa61a;';
    }
    
    const uploadDate = doc.uploaded_at_formatted || new Date().toLocaleDateString('ru-RU');
    
    return `
        <div class="document-card" data-doc-id="${doc.id}">
            <div class="document-icon">
                <i class="bi ${iconClass}" style="${iconColor}"></i>
            </div>
            <div class="document-name" title="${escapeHtml(doc.name)}">${escapeHtml(doc.name)}</div>
            <div class="document-meta">
                <span>${extension.toUpperCase()}</span>
                <span>${uploadDate}</span>
            </div>
            <div class="document-actions">
                <button class="doc-action-btn" onclick="editDocument(${doc.id})">
                    <i class="bi bi-pencil"></i> Изменить
                </button>
                <button class="doc-action-btn delete" onclick="deleteDocument(${doc.id})">
                    <i class="bi bi-trash"></i>
                </button>
            </div>
        </div>
    `;
}

function editDocument(docId) {
    currentDocumentId = docId;
    
    // Load document data via AJAX
    $.ajax({
        url: `/documents/${docId}/get/`,
        method: 'GET',
        headers: {'X-Requested-With': 'XMLHttpRequest'},
        success: function(response) {
            if (response.success) {
                $('#documentId').val(response.id);
                $('#docName').val(response.name);
                $('#docDescription').val(response.description || '');
                
                // Select tags
                $('#docTagsContainer .existing-tag').removeClass('selected');
                if (response.tags && response.tags.length > 0) {
                    response.tags.forEach(tagId => {
                        $(`#docTagsContainer .existing-tag[data-tag-id="${tagId}"]`).addClass('selected');
                    });
                }
                
                documentModal.show();
            }
        },
        error: function() {
            showNotification('error', 'Ошибка при загрузке данных документа');
        }
    });
}

function saveDocument() {
    const docId = $('#documentId').val();
    const name = $('#docName').val().trim();
    const description = $('#docDescription').val().trim();
    
    // Get selected tags
    const selectedTagIds = [];
    $('#docTagsContainer .existing-tag.selected').each(function() {
        selectedTagIds.push($(this).data('tag-id'));
    });
    
    if (!name) {
        showNotification('error', 'Название обязательно');
        return;
    }
    
    const data = {
        name: name,
        description: description,
        tags: selectedTagIds
    };
    
    $.ajax({
        url: `/documents/${docId}/`,
        method: 'PATCH',
        headers: {
            'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val(),
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        data: JSON.stringify(data),
        success: function(response) {
            documentModal.hide();
            
            // Update document card
            const card = $(`.document-card[data-doc-id="${docId}"]`);
            card.find('.document-name').text(name).attr('title', name);
            
            showNotification('success', 'Документ обновлен');
        },
        error: function() {
            showNotification('error', 'Ошибка при сохранении документа');
        }
    });
}

function deleteDocument(docId) {
    if (!confirm('Удалить этот документ?')) return;
    
    $.ajax({
        url: `/documents/${docId}/`,
        method: 'DELETE',
        headers: {
            'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val(),
            'X-Requested-With': 'XMLHttpRequest'
        },
        success: function() {
            $(`.document-card[data-doc-id="${docId}"]`).fadeOut(function() {
                $(this).remove();
                checkDocumentsEmptyState();
            });
            showNotification('success', 'Документ удален');
        },
        error: function() {
            showNotification('error', 'Ошибка при удалении документа');
        }
    });
}

function checkDocumentsEmptyState() {
    if ($('.document-card').length === 0) {
        $('.documents-grid').html(`
            <div class="empty-state" style="grid-column: 1/-1;">
                <i class="bi bi-cloud-upload"></i>
                <p>Документов пока нет</p>
                <small>Загрузите свой первый документ</small>
            </div>
        `);
    }
}

function showUploadProgress() {
    const progressHtml = `
        <div class="upload-progress">
            <div class="spinner"></div>
            <p>Загрузка файлов...</p>
        </div>
    `;
    $('.documents-grid').prepend(progressHtml);
}

function hideUploadProgress() {
    $('.upload-progress').remove();
}

function setupDragAndDrop() {
    const dropZone = $('.documents-grid');
    
    dropZone.on('dragover', function(e) {
        e.preventDefault();
        e.stopPropagation();
        $(this).addClass('dragover');
    });
    
    dropZone.on('dragleave', function(e) {
        e.preventDefault();
        e.stopPropagation();
        $(this).removeClass('dragover');
    });
    
    dropZone.on('drop', function(e) {
        e.preventDefault();
        e.stopPropagation();
        $(this).removeClass('dragover');
        
        const files = e.originalEvent.dataTransfer.files;
        if (files.length > 0) {
            uploadDocuments(files);
        }
    });
}

// Tag selection for documents
$(document).on('click', '#docTagsContainer .existing-tag', function() {
    $(this).toggleClass('selected');
});