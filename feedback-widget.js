// Feedback Widget Component
// Include this script in any page that needs the feedback widget
// DISABLED - Comment out the return statement below to re-enable

(function() {
    return; // Widget disabled
    // Firebase config (same as other pages)
    const firebaseConfig = {
        apiKey: "AIzaSyClsZXLxKOXjUtB5loTfz0__GpJ8AQYEas",
        authDomain: "aom-paper-understanding.firebaseapp.com",
        projectId: "aom-paper-understanding",
        storageBucket: "aom-paper-understanding.firebasestorage.app",
        messagingSenderId: "668607386746",
        appId: "1:668607386746:web:dc6711c596542fe1b217c3"
    };

    // Get current page name (dynamically for index.html with phases)
    function getCurrentPage() {
        const basePage = window.location.pathname.split('/').pop() || 'index.html';
        // If on index.html and there's a phase, include it
        if (basePage === 'index.html' && window.currentPhase) {
            return `index.html (${window.currentPhase})`;
        }
        return basePage;
    }
    let currentPage = getCurrentPage();

    // Variables to hold Firebase references
    let db = null;
    let firebaseReady = false;

    // Function to initialize Firebase
    function initFirebase() {
        return new Promise((resolve, reject) => {
            // Check if firebase compat is already loaded
            if (typeof firebase !== 'undefined' && firebase.apps) {
                if (!firebase.apps.length) {
                    firebase.initializeApp(firebaseConfig);
                }
                db = firebase.firestore();
                firebaseReady = true;
                resolve();
                return;
            }

            // Load Firebase compat scripts dynamically
            const appScript = document.createElement('script');
            appScript.src = 'https://www.gstatic.com/firebasejs/9.22.0/firebase-app-compat.js';
            appScript.onload = () => {
                const firestoreScript = document.createElement('script');
                firestoreScript.src = 'https://www.gstatic.com/firebasejs/9.22.0/firebase-firestore-compat.js';
                firestoreScript.onload = () => {
                    if (!firebase.apps.length) {
                        firebase.initializeApp(firebaseConfig);
                    }
                    db = firebase.firestore();
                    firebaseReady = true;
                    resolve();
                };
                firestoreScript.onerror = reject;
                document.head.appendChild(firestoreScript);
            };
            appScript.onerror = reject;
            document.head.appendChild(appScript);
        });
    }

    // Create widget container
    const widgetContainer = document.createElement('div');
    widgetContainer.id = 'feedback-widget-container';
    widgetContainer.innerHTML = `
        <style>
            #feedback-widget-container * {
                box-sizing: border-box;
            }
            #feedback-toggle-btn {
                position: fixed;
                left: 0;
                top: 50%;
                transform: translateY(-50%);
                background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
                color: white;
                border: none;
                padding: 12px 8px;
                cursor: pointer;
                z-index: 9999;
                border-radius: 0 8px 8px 0;
                box-shadow: 2px 2px 10px rgba(0,0,0,0.2);
                writing-mode: vertical-rl;
                text-orientation: mixed;
                font-size: 14px;
                font-weight: 600;
                transition: all 0.3s ease;
            }
            #feedback-toggle-btn:hover {
                padding-left: 12px;
                background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
            }
            #feedback-panel {
                position: fixed;
                left: 0;
                top: 0;
                width: 320px;
                height: 100vh;
                background: white;
                box-shadow: 4px 0 20px rgba(0,0,0,0.15);
                z-index: 10000;
                transform: translateX(-100%);
                transition: transform 0.3s ease;
                display: flex;
                flex-direction: column;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }
            #feedback-panel.open {
                transform: translateX(0);
            }
            #feedback-header {
                background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
                color: white;
                padding: 16px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            #feedback-header h3 {
                margin: 0;
                font-size: 16px;
                font-weight: 600;
            }
            #feedback-close-btn {
                background: rgba(255,255,255,0.2);
                border: none;
                color: white;
                width: 28px;
                height: 28px;
                border-radius: 50%;
                cursor: pointer;
                font-size: 18px;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: background 0.2s;
            }
            #feedback-close-btn:hover {
                background: rgba(255,255,255,0.3);
            }
            #feedback-page-info {
                background: #f3f4f6;
                padding: 8px 16px;
                font-size: 12px;
                color: #6b7280;
                border-bottom: 1px solid #e5e7eb;
            }
            #feedback-form {
                padding: 16px;
                border-bottom: 1px solid #e5e7eb;
            }
            #feedback-author-select {
                width: 100%;
                padding: 10px 12px;
                border: 1px solid #d1d5db;
                border-radius: 8px;
                font-size: 14px;
                margin-bottom: 12px;
                background: white;
                cursor: pointer;
            }
            #feedback-author-select:focus {
                outline: none;
                border-color: #6366f1;
                box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
            }
            #feedback-textarea {
                width: 100%;
                padding: 12px;
                border: 1px solid #d1d5db;
                border-radius: 8px;
                font-size: 14px;
                resize: none;
                height: 80px;
                margin-bottom: 12px;
                font-family: inherit;
            }
            #feedback-textarea:focus {
                outline: none;
                border-color: #6366f1;
                box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
            }
            #feedback-submit-btn {
                width: 100%;
                background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
                color: white;
                border: none;
                padding: 10px 16px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                cursor: pointer;
                transition: opacity 0.2s;
            }
            #feedback-submit-btn:hover {
                opacity: 0.9;
            }
            #feedback-submit-btn:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }
            #feedback-list-container {
                flex: 1;
                overflow-y: auto;
                padding: 16px;
            }
            #feedback-list-title {
                font-size: 13px;
                font-weight: 600;
                color: #374151;
                margin-bottom: 12px;
                display: flex;
                align-items: center;
                gap: 6px;
            }
            #feedback-list {
                display: flex;
                flex-direction: column;
                gap: 12px;
            }
            .feedback-item {
                background: #f9fafb;
                border-radius: 8px;
                padding: 12px;
                position: relative;
            }
            .feedback-item-header {
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                margin-bottom: 8px;
                padding-right: 24px;
            }
            .feedback-item-author {
                font-weight: 600;
                font-size: 13px;
            }
            .feedback-item-author.author-lee {
                color: #059669;
            }
            .feedback-item-author.author-park {
                color: #7c3aed;
            }
            .feedback-item-author.author-seunghyun {
                color: #0284c7;
            }
            .feedback-item-date {
                font-size: 11px;
                color: #9ca3af;
                flex-shrink: 0;
            }
            .feedback-item-content {
                font-size: 13px;
                color: #374151;
                line-height: 1.5;
                white-space: pre-wrap;
            }
            .feedback-item-page {
                font-size: 11px;
                color: #9ca3af;
                margin-top: 8px;
                padding-top: 8px;
                border-top: 1px solid #e5e7eb;
            }
            .feedback-delete-btn {
                position: absolute;
                top: 8px;
                right: 8px;
                background: none;
                border: none;
                color: #9ca3af;
                cursor: pointer;
                padding: 4px;
                border-radius: 4px;
                font-size: 14px;
                line-height: 1;
                transition: all 0.2s;
            }
            .feedback-delete-btn:hover {
                background: #fee2e2;
                color: #ef4444;
            }
            .feedback-done-btn {
                display: flex;
                align-items: center;
                gap: 4px;
                background: none;
                border: 1px solid #d1d5db;
                color: #9ca3af;
                cursor: pointer;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 11px;
                line-height: 1;
                transition: all 0.2s;
                margin-top: 8px;
                margin-left: auto;
            }
            .feedback-done-btn:hover {
                background: #dcfce7;
                border-color: #22c55e;
                color: #22c55e;
            }
            .feedback-done-btn.checked {
                background: #dcfce7;
                border-color: #22c55e;
                color: #22c55e;
            }
            .feedback-item.resolved {
                background: #f9fafb;
                border-left: 3px solid #d1d5db;
                opacity: 0.6;
            }
            .feedback-item.resolved .feedback-content,
            .feedback-item.resolved .feedback-meta {
                color: #9ca3af;
            }
            .feedback-empty {
                text-align: center;
                color: #9ca3af;
                font-size: 13px;
                padding: 24px;
            }
            #feedback-filter {
                padding: 12px 16px;
                background: #f9fafb;
                border-bottom: 1px solid #e5e7eb;
            }
            #feedback-filter select {
                width: 100%;
                padding: 8px 10px;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                font-size: 12px;
                background: white;
            }
        </style>

        <button id="feedback-toggle-btn">Feedback</button>

        <div id="feedback-panel">
            <div id="feedback-header">
                <h3>Feedback</h3>
                <button id="feedback-close-btn">&times;</button>
            </div>

            <div id="feedback-page-info">
                Current page: <strong>${currentPage}</strong>
            </div>

            <div id="feedback-form">
                <select id="feedback-author-select">
                    <option value="">Select your name</option>
                    <option value="Prof. Lee">Prof. Lee</option>
                    <option value="Prof. Park">Prof. Park</option>
                    <option value="Seunghyun">Seunghyun</option>
                </select>
                <textarea id="feedback-textarea" placeholder="Write your feedback here..."></textarea>
                <button id="feedback-submit-btn">Submit Feedback</button>
            </div>

            <div id="feedback-filter">
                <select id="feedback-page-filter">
                    <option value="current">This page only</option>
                    <option value="all">Show all pages</option>
                </select>
            </div>

            <div id="feedback-list-container">
                <div id="feedback-list-title">Recent Feedback</div>
                <div id="feedback-list">
                    <div class="feedback-empty">Loading...</div>
                </div>
            </div>
        </div>
    `;

    // Add widget to page
    document.body.appendChild(widgetContainer);

    // Get elements
    const toggleBtn = document.getElementById('feedback-toggle-btn');
    const panel = document.getElementById('feedback-panel');
    const closeBtn = document.getElementById('feedback-close-btn');
    const authorSelect = document.getElementById('feedback-author-select');
    const textarea = document.getElementById('feedback-textarea');
    const submitBtn = document.getElementById('feedback-submit-btn');
    const feedbackList = document.getElementById('feedback-list');
    const pageFilter = document.getElementById('feedback-page-filter');

    // Load saved author preference
    const savedAuthor = localStorage.getItem('feedbackAuthor');
    if (savedAuthor) {
        authorSelect.value = savedAuthor;
    }

    // Update page info display
    function updatePageInfo() {
        currentPage = getCurrentPage();
        const pageInfoEl = document.getElementById('feedback-page-info');
        if (pageInfoEl) {
            pageInfoEl.innerHTML = `Current page: <strong>${currentPage}</strong>`;
        }
    }

    // Toggle panel
    toggleBtn.addEventListener('click', async () => {
        updatePageInfo(); // Update current page/phase when opening
        panel.classList.add('open');
        if (!firebaseReady) {
            feedbackList.innerHTML = '<div class="feedback-empty">Initializing...</div>';
            await initFirebase();
        }
        loadFeedbacks();
    });

    closeBtn.addEventListener('click', () => {
        panel.classList.remove('open');
    });

    // Save author preference
    authorSelect.addEventListener('change', () => {
        localStorage.setItem('feedbackAuthor', authorSelect.value);
    });

    // Submit feedback
    submitBtn.addEventListener('click', async () => {
        if (!firebaseReady) {
            await initFirebase();
        }

        // Update current page before submitting
        updatePageInfo();

        const author = authorSelect.value;
        const content = textarea.value.trim();

        if (!author) {
            alert('Please select your name.');
            return;
        }
        if (!content) {
            alert('Please write your feedback.');
            return;
        }

        submitBtn.disabled = true;
        submitBtn.textContent = 'Submitting...';

        try {
            await db.collection('feedbacks').add({
                author: author,
                content: content,
                page: currentPage,
                createdAt: firebase.firestore.FieldValue.serverTimestamp(),
                timestamp: new Date().toISOString()
            });

            textarea.value = '';
            loadFeedbacks();
            alert('Feedback submitted!');
        } catch (error) {
            console.error('Error submitting feedback:', error);
            alert('Failed to submit feedback. Please try again.');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Submit Feedback';
        }
    });

    // Filter change
    pageFilter.addEventListener('change', loadFeedbacks);

    // Load feedbacks
    async function loadFeedbacks() {
        if (!firebaseReady) {
            feedbackList.innerHTML = '<div class="feedback-empty">Initializing...</div>';
            return;
        }

        const filter = pageFilter.value;

        try {
            // Always fetch all feedbacks and filter client-side to avoid index requirement
            const query = db.collection('feedbacks').orderBy('createdAt', 'desc').limit(100);
            const snapshot = await query.get();

            // Filter client-side if needed
            let docs = [];
            snapshot.forEach(doc => {
                const data = doc.data();
                if (filter === 'all' || data.page === currentPage) {
                    docs.push({ id: doc.id, data: data });
                }
            });

            if (docs.length === 0) {
                feedbackList.innerHTML = '<div class="feedback-empty">No feedback yet.</div>';
                return;
            }

            // Helper to get author color class
            const getAuthorClass = (author) => {
                if (author.includes('Lee')) return 'author-lee';
                if (author.includes('Park')) return 'author-park';
                if (author.includes('Seunghyun')) return 'author-seunghyun';
                return '';
            };

            let html = '';
            docs.forEach(({ id, data }) => {
                const date = data.createdAt ? data.createdAt.toDate() : new Date(data.timestamp);
                const dateStr = date.toLocaleDateString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                });

                const isResolved = data.resolved === true;
                html += `
                    <div class="feedback-item ${isResolved ? 'resolved' : ''}" data-id="${id}">
                        <button class="feedback-delete-btn" onclick="deleteFeedback('${id}')">&times;</button>
                        <div class="feedback-item-header">
                            <span class="feedback-item-author ${getAuthorClass(data.author)}">${escapeHtml(data.author)}</span>
                            <span class="feedback-item-date">${dateStr}</span>
                        </div>
                        <div class="feedback-item-content">${escapeHtml(data.content)}</div>
                        <div class="feedback-item-page">${escapeHtml(data.page)}</div>
                        <button class="feedback-done-btn ${isResolved ? 'checked' : ''}" onclick="toggleFeedbackResolved('${id}', ${!isResolved})" title="${isResolved ? 'Mark as unresolved' : 'Mark as resolved'}">
                            <span>✓</span>
                            <span>Done</span>
                        </button>
                    </div>
                `;
            });

            feedbackList.innerHTML = html;
        } catch (error) {
            console.error('Error loading feedbacks:', error);
            feedbackList.innerHTML = '<div class="feedback-empty">Failed to load feedback.</div>';
        }
    }

    // Delete feedback
    window.deleteFeedback = async function(docId) {
        if (!confirm('Delete this feedback?')) return;

        try {
            await db.collection('feedbacks').doc(docId).delete();
            loadFeedbacks();
        } catch (error) {
            console.error('Error deleting feedback:', error);
            alert('Failed to delete feedback.');
        }
    };

    // Toggle feedback resolved status
    window.toggleFeedbackResolved = async function(docId, resolved) {
        try {
            await db.collection('feedbacks').doc(docId).update({
                resolved: resolved,
                resolvedAt: resolved ? new Date() : null
            });
            loadFeedbacks();
        } catch (error) {
            console.error('Error updating feedback:', error);
            alert('Failed to update feedback.');
        }
    };

    // Escape HTML helper
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Initialize Firebase in background (don't block UI)
    initFirebase().catch(err => console.error('Failed to init Firebase for feedback widget:', err));
})();
