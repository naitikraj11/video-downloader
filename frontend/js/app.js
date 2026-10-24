let currentUrl = "";

async function fetchVideoDetails() {
    const input = document.getElementById("videoUrl");
    const loader = document.getElementById("loader");
    const statusText = document.getElementById("loaderStatus");
    const videoCard = document.getElementById("videoCard");
    const searchBtn = document.getElementById("searchBtn");

    currentUrl = input.value.trim();
    if (!currentUrl) {
        alert("Please paste a valid video URL.");
        return;
    }

    videoCard.style.display = "none";
    loader.style.display = "block";
    statusText.innerText = "Analyzing video link...";
    searchBtn.disabled = true;

    try {
        const res = await fetch('/api/info', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: currentUrl })
        });

        const data = await res.json();
        loader.style.display = "none";
        searchBtn.disabled = false;

        if (data.success) {
            displayDetails(data);
        } else {
            alert("Error: " + (data.error || "Could not fetch formats."));
        }
    } catch (e) {
        loader.style.display = "none";
        searchBtn.disabled = false;
        alert("Failed to connect to backend server.");
    }
}

function displayDetails(info) {
    document.getElementById("thumbImg").src = info.thumbnail;
    document.getElementById("videoTitle").innerText = info.title;

    const list = document.getElementById("qualityList");
    list.innerHTML = "";

    info.options.forEach(opt => {
        const btn = document.createElement("button");
        btn.className = `dl-action-btn ${opt.type === 'audio' ? 'audio-btn' : ''}`;
        btn.innerText = opt.label;
        btn.onclick = () => startProcessAndDownload(opt.format_id, opt.type, btn);
        list.appendChild(btn);
    });

    document.getElementById("videoCard").style.display = "block";
}

async function startProcessAndDownload(formatId, type, btnElement) {
    const originalText = btnElement.innerText;
    btnElement.innerText = "Processing (Merging)...";
    btnElement.disabled = true;

    try {
        const res = await fetch('/api/process', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                url: currentUrl,
                format_id: formatId,
                type: type
            })
        });

        const data = await res.json();
        btnElement.innerText = originalText;
        btnElement.disabled = false;

        if (data.success) {
            // Trigger automatic force-download in browser
            window.location.href = `/api/download/${data.file_name}`;
        } else {
            alert("Download failed: " + (data.error || "Unknown error"));
        }
    } catch (e) {
        btnElement.innerText = originalText;
        btnElement.disabled = false;
        alert("Error while processing video.");
    }
}