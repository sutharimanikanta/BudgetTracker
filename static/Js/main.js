$(document).ready(function () {
    // Add smooth transitions to alerts
    $('.alert').addClass('show');

    // Form validation feedback
    $('input, select').on('input change', function () {
        if ($(this).hasClass('is-invalid')) {
            $(this).removeClass('is-invalid');
            $(this).siblings('.invalid-feedback').hide();
        }
    });

    // Prevent multiple form submissions
    $('form').submit(function () {
        $(this).find('button[type="submit"]').prop('disabled', true).text('Processing...');
    });

    // Confirmation for delete actions
    $('a[href*="delete_entry"]').on('click', function (e) {
        if (!confirm('Are you sure you want to delete this entry? This action cannot be undone.')) {
            e.preventDefault();
        }
    });
});