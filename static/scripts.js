// JavaScript to handle single star toggle for marking revision status
document.querySelectorAll('.star-rating .fa-star').forEach(star => {
    star.addEventListener('click', function () {
        const questionId = this.closest('.star-rating').getAttribute('data-question-id');
        const isChecked = this.classList.contains('checked');
        const newStatus = isChecked ? 0 : 1; // Toggle between 0 and 1

        // Disable further clicks until the request is complete (simple debounce)
        this.style.pointerEvents = 'none'; // Disable click temporarily

        // Make an AJAX request to update the revision status in your database
        fetch(`/update_revision?question_id=${questionId}&status=${newStatus}`)
            .then(response => {
                if (!response.ok) {
                    // Handle non-OK response (e.g., 404 or 500)
                    throw new Error(`Failed to update revision status. Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                // Update the UI based on the response
                if (data.status === 'success') {
                    if (data.revision === 1) {
                        this.classList.add('checked');
                    } else {
                        this.classList.remove('checked');
                    }
                } else {
                    throw new Error('Failed to update revision status: ' + data.message);
                }
            })
            .catch(error => {
                // Handle any errors that occur during the fetch operation
                console.error('Error updating revision status:', error);
                alert('An error occurred while updating the revision status. Please try again.');
            })
            .finally(() => {
                // Re-enable the click event after the request is done
                this.style.pointerEvents = 'auto'; // Re-enable click
            });
    });
});

// JavaScript to handle tag filtering
document.getElementById('tags-filter')?.addEventListener('change', function () {
    const selectedTag = this.value;
    const url = new URL(window.location.href);

    // Update the URL search params with the selected tag filter
    if (selectedTag !== 'All') {
        url.searchParams.set('tag', selectedTag);
    } else {
        url.searchParams.delete('tag');
    }

    // Redirect the page to apply the filter
    window.location.href = url.toString();
});
