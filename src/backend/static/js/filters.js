// Filters Management
let activeTimeFilter = 'all';
let activeTagFilters = [];

$(document).ready(function() {
    // Time Filters
    $('.filter-btn').click(function() {
        $('.filter-btn').removeClass('active');
        $(this).addClass('active');
        
        activeTimeFilter = $(this).data('filter');
        applyFilters();
    });

    // Tag Filters
    $('.tag-filter').click(function() {
        const tagId = $(this).data('tag-id');
        
        $(this).toggleClass('active');
        
        if ($(this).hasClass('active')) {
            if (!activeTagFilters.includes(tagId)) {
                activeTagFilters.push(tagId);
            }
        } else {
            activeTagFilters = activeTagFilters.filter(id => id !== tagId);
        }
        
        applyFilters();
    });
});

function applyFilters() {
    $('.task-item').each(function() {
        const taskElement = $(this);
        
        // Skip subtasks - they'll be handled by parent visibility
        if (taskElement.hasClass('subtask-item')) {
            return;
        }
        
        let showTask = true;
        
        // Apply time filter
        if (activeTimeFilter !== 'all') {
            showTask = checkTimeFilter(taskElement, activeTimeFilter);
        }
        
        // Apply tag filter (if any tags selected)
        if (showTask && activeTagFilters.length > 0) {
            showTask = checkTagFilter(taskElement, activeTagFilters);
        }
        
        if (showTask) {
            taskElement.slideDown();
        } else {
            taskElement.slideUp();
        }
    });
}

function checkTimeFilter(taskElement, filter) {
    const endTimeStr = taskElement.data('end-time');
    if (!endTimeStr) return filter === 'all';
    
    const endTime = new Date(endTimeStr);
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    const weekEnd = new Date(today);
    weekEnd.setDate(weekEnd.getDate() + 7);
    const monthEnd = new Date(today);
    monthEnd.setMonth(monthEnd.getMonth() + 1);
    
    switch(filter) {
        case 'today':
            return endTime >= today && endTime < tomorrow;
        case 'tomorrow':
            const dayAfterTomorrow = new Date(tomorrow);
            dayAfterTomorrow.setDate(dayAfterTomorrow.getDate() + 1);
            return endTime >= tomorrow && endTime < dayAfterTomorrow;
        case 'week':
            return endTime >= today && endTime < weekEnd;
        case 'month':
            return endTime >= today && endTime < monthEnd;
        default:
            return true;
    }
}

function checkTagFilter(taskElement, tagIds) {
    const taskTags = [];
    
    taskElement.find('.task-tag').each(function() {
        // Try to find tag ID from data or matching existing tags
        const tagText = $(this).text().trim();
        $('.tag-filter').each(function() {
            if ($(this).text().trim() === tagText) {
                taskTags.push($(this).data('tag-id'));
            }
        });
    });
    
    // Check if task has any of the selected tags
    return tagIds.some(tagId => taskTags.includes(tagId));
}

// Update overdue status
function updateOverdueTasks() {
    const now = new Date();
    
    $('.task-item').each(function() {
        const endTimeStr = $(this).data('end-time');
        if (!endTimeStr) return;
        
        const endTime = new Date(endTimeStr);
        const timeElement = $(this).find('.task-time');
        
        if (endTime < now && !$(this).hasClass('completed')) {
            timeElement.addClass('overdue');
        } else {
            timeElement.removeClass('overdue');
        }
    });
}

// Run on load and periodically
$(document).ready(function() {
    updateOverdueTasks();
    
    // Update every minute
    setInterval(updateOverdueTasks, 60000);
});