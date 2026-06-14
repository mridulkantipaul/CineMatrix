// ==========================================
// 🎬 CINEMATIC LOADING SCREEN ENGINE (With Failsafe)
// ==========================================
function hideLoader() {
    const loader = document.getElementById('loader-wrapper');
    if (loader && !loader.classList.contains('fade-out')) {
        loader.classList.add('fade-out');
        setTimeout(() => {
            loader.style.display = 'none';
        }, 800);
    }
}

window.addEventListener('load', function() {
    setTimeout(hideLoader, 500); 
});
setTimeout(hideLoader, 3000); // 3-second failsafe

// ==========================================
// 🧠 MAIN APPLICATION LOGIC
// ==========================================
document.addEventListener("DOMContentLoaded", function() {
    
    // --- 1. Load Movie Rows on Page Load ---
    function loadRow(endpoint, rowId) {
        fetch(endpoint)
            .then(response => response.json())
            .then(data => {
                const row = document.getElementById(rowId);
                if (!row) return; // Failsafe if row doesn't exist on this page
                row.innerHTML = "";
                data.forEach(movie => {
                    const poster = movie.poster_url || "https://placehold.co/200x300/1e1e1e/00a8e1?text=No+Poster";
                    row.innerHTML += `
                        <div class="movie-card">
                            <img src="${poster}" class="movie-poster" alt="${movie.title}">
                            <p class="movie-title">${movie.title}</p>
                        </div>
                    `;
                });
            });
    }

    loadRow('/api/row/trending', 'trending-row');
    loadRow('/api/row/action', 'action-row');
    loadRow('/api/row/scifi', 'scifi-row');

    // --- 2. Live API Search Functionality ---
    const searchBtn = document.getElementById("search-btn");
    const searchInput = document.getElementById("movie-search");
    const searchResultsSection = document.getElementById("search-results-section");
    
    if (searchBtn && searchInput) {
        searchInput.addEventListener("keypress", function(event) {
            if (event.key === "Enter") {
                event.preventDefault();
                searchBtn.click();
            }
        });

        searchBtn.addEventListener("click", function() {
            const query = searchInput.value.trim();
            if(!query) return;
            
            if (!searchResultsSection) {
                alert("Taking you back to the Home page to see your results!");
                window.location.href = "/";
                return;
            }

            searchResultsSection.classList.remove("d-none");
            const row = document.getElementById("search-results-row");
            row.innerHTML = `<p class="text-info p-3 fw-bold">Fetching live results from TVmaze...</p>`;
            
            fetch('/recommend', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: new URLSearchParams({ 'movie': query })
            })
            .then(res => res.json())
            .then(data => {
                row.innerHTML = ""; 
                if(data.error) {
                    row.innerHTML = `<p class="text-danger p-3">${data.error}</p>`;
                    return;
                }
                data.forEach(movie => {
                    const poster = movie.poster_url || "https://placehold.co/200x300/1e1e1e/00a8e1?text=No+Poster";
                    row.innerHTML += `
                        <div class="movie-card">
                            <img src="${poster}" class="movie-poster" alt="${movie.title}">
                            <p class="movie-title">${movie.title.replace('⭐ YOU SEARCHED: ', '')}</p>
                        </div>`;
                });
            })
            .catch(err => {
                row.innerHTML = `<p class="text-danger p-3">Connection error. Please try again.</p>`;
            });
        });
    }

    // --- 3. Chatbot Logic ---
    const chatContainer = document.getElementById("chatbot-container");
    const openChatBtn = document.getElementById("open-chat-btn");
    const closeChatBtn = document.getElementById("close-chat");
    const sendChatBtn = document.getElementById("send-chat");
    const chatInput = document.getElementById("chat-input");
    const chatMessages = document.getElementById("chatbot-messages");

    if (openChatBtn) {
        openChatBtn.addEventListener("click", () => { chatContainer.style.display = "flex"; openChatBtn.style.display = "none"; });
        closeChatBtn.addEventListener("click", () => { chatContainer.style.display = "none"; openChatBtn.style.display = "block"; });

        sendChatBtn.addEventListener("click", function() {
            const text = chatInput.value.trim();
            if(!text) return;
            
            chatMessages.innerHTML += `<div class="user-msg">${text}</div>`;
            chatInput.value = "";
            chatMessages.scrollTop = chatMessages.scrollHeight;

            fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: new URLSearchParams({ 'message': text })
            })
            .then(res => res.json())
            .then(data => {
                let botReply = `<div class="bot-msg">${data.response}</div>`;
                if(data.poster) {
                    botReply += `<img src="${data.poster}" style="width: 100px; border-radius: 8px; margin-left: 15px; margin-top: 5px;">`;
                }
                chatMessages.innerHTML += botReply;
                chatMessages.scrollTop = chatMessages.scrollHeight;
            });
        });
    }

    // --- 4. YOUTUBE IFRAME VIDEO LOGIC ---
    const detailOverlay = document.getElementById('movie-detail-overlay');
    const closeOverlayBtn = document.getElementById('close-overlay-btn');
    const bgVideo = document.getElementById('bg-trailer-video');
    const trailerModal = document.getElementById('trailer-modal');
    const playTrailerBtn = document.getElementById('play-trailer-btn');
    const closeTrailerBtn = document.getElementById('close-trailer-btn');
    const focusedVideo = document.getElementById('focused-trailer-video');

    document.addEventListener('click', function(event) {
        const card = event.target.closest('.movie-card');
        if (card) {
            let title = card.querySelector('.movie-title').innerText;
            title = title.replace('⭐ YOU SEARCHED: ', '');

            fetch(`/api/movie/${encodeURIComponent(title)}`)
                .then(res => res.json())
                .then(data => {
                    if (data.error) return;

                    document.getElementById('detail-title').innerText = data.title;
                    document.getElementById('detail-match').innerText = `${data.age_match}% Match`;
                    document.getElementById('detail-year').innerText = `${data.runtime}m`;
                    document.getElementById('detail-genre').innerText = data.genre;
                    document.getElementById('detail-rating').innerText = data.rating;
                    document.getElementById('detail-description').innerText = data.description;
                    document.getElementById('detail-cast').innerText = data.cast;
                    document.getElementById('detail-views').innerText = data.views;
                    document.getElementById('detail-review').innerText = data.review;

                    const videoId = data.trailer_url.split('/').pop();
                    bgVideo.src = `${data.trailer_url}?autoplay=1&mute=1&controls=0&loop=1&playlist=${videoId}`;
                    focusedVideo.dataset.url = data.trailer_url;

                    detailOverlay.classList.remove('d-none');
                });
        }
    });

    if (closeOverlayBtn) {
        closeOverlayBtn.addEventListener('click', () => {
            detailOverlay.classList.add('d-none');
            bgVideo.src = ""; 
        });
    }

    if (playTrailerBtn) {
        playTrailerBtn.addEventListener('click', () => {
            trailerModal.classList.remove('d-none');
            bgVideo.src = ""; 
            focusedVideo.src = `${focusedVideo.dataset.url}?autoplay=1`; 
        });
    }

    if (closeTrailerBtn) {
        closeTrailerBtn.addEventListener('click', () => {
            trailerModal.classList.add('d-none');
            focusedVideo.src = ""; 
            const videoId = focusedVideo.dataset.url.split('/').pop();
            bgVideo.src = `${focusedVideo.dataset.url}?autoplay=1&mute=1&controls=0&loop=1&playlist=${videoId}`; 
        });
    }

    // --- 5. "MY LIST" WATCHLIST ENGINE ---
    const addWatchlistBtn = document.getElementById('add-watchlist-btn');
    const watchlistRow = document.getElementById('watchlist-row');
    const watchlistTitle = document.getElementById('watchlist-title');
    
    function renderWatchlist() {
        let savedMovies = JSON.parse(localStorage.getItem('myWatchlist')) || [];
        if (watchlistRow && watchlistTitle) {
            if (savedMovies.length > 0) {
                watchlistTitle.style.display = "block";
                watchlistRow.style.display = "flex";
                watchlistRow.innerHTML = ""; 
                savedMovies.forEach(movie => {
                    watchlistRow.innerHTML += `
                        <div class="movie-card">
                            <img src="${movie.poster}" class="movie-poster" alt="${movie.title}">
                            <p class="movie-title">${movie.title}</p>
                        </div>
                    `;
                });
            } else {
                watchlistTitle.style.display = "none";
                watchlistRow.style.display = "none";
            }
        }
    }

    renderWatchlist();

    if (addWatchlistBtn) {
        addWatchlistBtn.addEventListener('click', () => {
            const currentTitle = document.getElementById('detail-title').innerText;
            let savedMovies = JSON.parse(localStorage.getItem('myWatchlist')) || [];
            const movieIndex = savedMovies.findIndex(movie => movie.title === currentTitle);
            
            if (movieIndex === -1) {
                let posterUrl = "https://placehold.co/200x300/1e1e1e/00a8e1?text=No+Poster";
                document.querySelectorAll('.movie-card').forEach(card => {
                    if (card.querySelector('.movie-title').innerText.replace('⭐ YOU SEARCHED: ', '') === currentTitle) {
                        posterUrl = card.querySelector('.movie-poster').src;
                    }
                });
                savedMovies.push({ title: currentTitle, poster: posterUrl });
                localStorage.setItem('myWatchlist', JSON.stringify(savedMovies));
                addWatchlistBtn.innerText = "❌ Remove from List";
                addWatchlistBtn.classList.replace('btn-info', 'btn-danger'); 
            } else {
                savedMovies.splice(movieIndex, 1); 
                localStorage.setItem('myWatchlist', JSON.stringify(savedMovies)); 
                addWatchlistBtn.innerText = "➕ Add to My List";
                addWatchlistBtn.classList.replace('btn-danger', 'btn-info');
            }
            renderWatchlist();
        });
    }

    document.addEventListener('click', function(event) {
        const card = event.target.closest('.movie-card');
        if (card && addWatchlistBtn) {
            let title = card.querySelector('.movie-title').innerText.replace('⭐ YOU SEARCHED: ', '');
            let savedMovies = JSON.parse(localStorage.getItem('myWatchlist')) || [];
            const alreadySaved = savedMovies.some(movie => movie.title === title);
            
            if (alreadySaved) {
                addWatchlistBtn.innerText = "❌ Remove from List";
                addWatchlistBtn.className = "btn-danger text-white fw-bold ms-3";
                addWatchlistBtn.style.border = "none"; addWatchlistBtn.style.padding = "10px 24px"; addWatchlistBtn.style.borderRadius = "4px";
            } else {
                addWatchlistBtn.innerText = "➕ Add to My List";
                addWatchlistBtn.className = "btn-info text-white fw-bold ms-3";
                addWatchlistBtn.style.border = "none"; addWatchlistBtn.style.padding = "10px 24px"; addWatchlistBtn.style.borderRadius = "4px";
            }
        }
    });

    // --- 6. ⭐ PERSONAL REVIEW ENGINE ---
    const stars = document.querySelectorAll('#user-stars .star');
    const reviewInput = document.getElementById('user-review-input');
    const saveReviewBtn = document.getElementById('save-review-btn');
    const savedDisplay = document.getElementById('saved-review-display');
    const savedText = document.getElementById('saved-review-text');
    let currentRating = 0;

    stars.forEach(star => {
        star.addEventListener('click', function() {
            currentRating = this.getAttribute('data-val');
            stars.forEach(s => s.classList.remove('active'));
            for(let i = 0; i < currentRating; i++) { stars[i].classList.add('active'); }
        });
    });

    if (saveReviewBtn) {
        saveReviewBtn.addEventListener('click', () => {
            const currentTitle = document.getElementById('detail-title').innerText;
            const reviewText = reviewInput.value.trim();
            let allReviews = JSON.parse(localStorage.getItem('myMovieReviews')) || {};
            allReviews[currentTitle] = { rating: currentRating, text: reviewText };
            localStorage.setItem('myMovieReviews', JSON.stringify(allReviews));
            savedDisplay.classList.remove('d-none');
            savedText.innerText = `"${reviewText}" (${currentRating}/5 Stars)`;
            saveReviewBtn.innerText = "Update Review";
        });
    }

    document.addEventListener('click', function(event) {
        const card = event.target.closest('.movie-card');
        if (card && saveReviewBtn) {
            let title = card.querySelector('.movie-title').innerText.replace('⭐ YOU SEARCHED: ', '');
            let allReviews = JSON.parse(localStorage.getItem('myMovieReviews')) || {};
            
            currentRating = 0;
            stars.forEach(s => s.classList.remove('active'));
            if(reviewInput) reviewInput.value = "";
            if(savedDisplay) savedDisplay.classList.add('d-none');
            saveReviewBtn.innerText = "Save Review";

            if (allReviews[title]) {
                const savedData = allReviews[title];
                currentRating = savedData.rating;
                if(reviewInput) reviewInput.value = savedData.text;
                for(let i = 0; i < currentRating; i++) { stars[i].classList.add('active'); }
                if(savedDisplay) savedDisplay.classList.remove('d-none');
                if (savedData.text) {
                    if(savedText) savedText.innerText = `"${savedData.text}" (${currentRating}/5 Stars)`;
                } else {
                    if(savedText) savedText.innerText = `Rated ${currentRating}/5 Stars`;
                }
                saveReviewBtn.innerText = "Update Review";
            }
        }
    });

// --- 7. LIVE API HERO BANNER (MASSIVE CATALOG UPDATE) ---
    const heroBanner = document.getElementById('hero-banner');
    const heroTitle = document.getElementById('hero-title');
    const heroMeta = document.getElementById('hero-meta');
    const heroDesc = document.getElementById('hero-description');
    const heroContent = document.getElementById('hero-content');

    if (heroBanner && heroTitle) {
        // TVmaze has hundreds of pages of shows. Let's pick a random page (0 to 10) every time you refresh!
        const randomPage = Math.floor(Math.random() * 10);
        
        fetch(`https://api.tvmaze.com/shows?page=${randomPage}`)
            .then(res => res.json())
            .then(data => {
                // Filter out shows with missing or bad images
                const validShows = data.filter(show => show.image && show.image.original && show.summary);
                
                // Shuffle the massive list
                const shuffled = validShows.sort(() => 0.5 - Math.random());
                
                // 🔥 THE FIX: We are now grabbing 50 shows instead of 5!
                const selectedShows = shuffled.slice(0, 50);
                
                const heroMovies = selectedShows.map(show => {
                    const year = show.premiered ? show.premiered.split('-')[0] : "2023";
                    const genres = show.genres.length > 0 ? show.genres.slice(0, 2).join(' & ') : "Drama";
                    const rating = show.rating ? show.rating.average || "8.5" : "8.0";
                    
                    const cleanDesc = show.summary.replace(/<[^>]+>/g, ''); 
                    const shortDesc = cleanDesc.length > 180 ? cleanDesc.substring(0, 180) + "..." : cleanDesc;
                    const match = Math.floor(Math.random() * 15) + 85; 

                    return {
                        title: show.name,
                        meta: `<span class='match-score'>${match}% Match</span> | ${year} | ${genres} | ⭐ ${rating}`,
                        desc: shortDesc,
                        bg: `url('${show.image.original}')` 
                    };
                });

                let currentHeroIndex = 0;
                
                const loadHero = (movie) => {
                    // Pre-load the image in the background so it doesn't flicker!
                    const img = new Image();
                    img.src = movie.bg.replace("url('", "").replace("')", "");
                    img.onload = () => {
                        heroBanner.style.backgroundImage = movie.bg;
                        heroTitle.innerText = movie.title;
                        heroMeta.innerHTML = movie.meta;
                        heroDesc.innerText = movie.desc;
                    };
                };
                
                loadHero(heroMovies[0]); 

                setInterval(() => {
                    heroContent.style.opacity = 0;
                    setTimeout(() => {
                        currentHeroIndex = (currentHeroIndex + 1) % heroMovies.length;
                        loadHero(heroMovies[currentHeroIndex]);
                        heroContent.style.opacity = 1;
                    }, 500); 
                }, 5000); 
            })
            .catch(err => console.log("Hero Banner API Error:", err));
    }

    // --- 8. 🧊 3D MOUSE TRACKING ENGINE ---
    document.addEventListener('mousemove', function(e) {
        const card = e.target.closest('.movie-card');
        if (card) {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            const rotateX = ((y - centerY) / centerY) * -15; 
            const rotateY = ((x - centerX) / centerX) * 15;
            card.style.transform = `perspective(1000px) scale3d(1.1, 1.1, 1.1) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
            card.style.zIndex = "50";
            card.style.boxShadow = `${-rotateY}px ${rotateX + 10}px 25px rgba(0,0,0,0.8)`;
        }
    });

    document.addEventListener('mouseout', function(e) {
        const card = e.target.closest('.movie-card');
        if (card) {
            card.style.transform = 'perspective(1000px) scale3d(1, 1, 1) rotateX(0deg) rotateY(0deg)';
            card.style.zIndex = "1";
            card.style.boxShadow = 'none';
        }
    });

}); // <-- FINAL CLOSING BRACKET