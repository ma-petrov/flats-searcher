// app.js
document.addEventListener('DOMContentLoaded', function() {
    const tg = window.Telegram.WebApp;
    tg.expand();

    const svg = document.getElementById('metro-svg');
    let scale = 1;
    let translateX = 0;
    let translateY = 0;
    let isDragging = false;
    let startX, startY;
    let selectedStations = new Set();

    // Initialize map
    function initMap() {
        // Draw lines
        metroData.lines.forEach(line => {
            const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
            const stations = line.stations;
            let pathData = `M ${stations[0].x} ${stations[0].y}`;
            
            for (let i = 1; i < stations.length; i++) {
                pathData += ` L ${stations[i].x} ${stations[i].y}`;
            }

            path.setAttribute("d", pathData);
            path.setAttribute("class", "metro-line");
            path.setAttribute("stroke", line.color);
            svg.appendChild(path);

            // Draw stations
            stations.forEach(station => {
                // Station circle
                const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
                circle.setAttribute("cx", station.x);
                circle.setAttribute("cy", station.y);
                circle.setAttribute("r", "5");
                circle.setAttribute("class", "station-circle");
                circle.setAttribute("stroke", line.color);
                circle.setAttribute("data-station-id", station.id);
                
                // Station label
                const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
                text.setAttribute("x", station.x + 8);
                text.setAttribute("y", station.y + 4);
                text.setAttribute("class", "station-label");
                text.textContent = station.name;

                circle.addEventListener('click', () => toggleStation(station, circle));
                text.addEventListener('click', () => toggleStation(station, circle));

                svg.appendChild(circle);
                svg.appendChild(text);
            });
        });

        // Draw transfers
        metroData.transfers.forEach(transfer => {
            // Draw transfer connections
            const station1 = findStationById(transfer.stations[0]);
            const station2 = findStationById(transfer.stations[1]);
            
            if (station1 && station2) {
                const transferLine = document.createElementNS("http://www.w3.org/2000/svg", "line");
                transferLine.setAttribute("x1", station1.x);
                transferLine.setAttribute("y1", station1.y);
                transferLine.setAttribute("x2", station2.x);
                transferLine.setAttribute("y2", station2.y);
                transferLine.setAttribute("stroke", "#000");
                transferLine.setAttribute("stroke-width", "1");
                transferLine.setAttribute("stroke-dasharray", "2,2");
                svg.appendChild(transferLine);
            }
        });
    }

    // Pan and zoom functionality
    svg.addEventListener('mousedown', startDrag);
    svg.addEventListener('mousemove', drag);
    svg.addEventListener('mouseup', endDrag);
    svg.addEventListener('mouseleave', endDrag);
    document.addEventListener('wheel', zoom);

    // Touch events
    svg.addEventListener('touchstart', startDrag);
    svg.addEventListener('touchmove', drag);
    svg.addEventListener('touchend', endDrag);

    // document.getElementById('zoomIn').addEventListener('click', () => {
    //     scale *= 1.2;
    //     updateTransform();
    // });

    // document.getElementById('zoomOut').addEventListener('click', () => {
    //     scale *= 0.8;
    //     updateTransform();
    // });

    function startDrag(e) {
        isDragging = true;
        const point = getEventPoint(e);
        startX = point.x - translateX;
        startY = point.y - translateY;
    }

    function drag(e) {
        if (!isDragging) return;
        e.preventDefault();
        const point = getEventPoint(e);
        translateX = point.x - startX;
        translateY = point.y - startY;
        updateTransform();
    }

    function endDrag() {
        isDragging = false;
    }

    function zoom(e) {
        e.preventDefault();
        const delta = e.deltaY;
        scale *= delta > 0 ? 0.9 : 1.1;
        updateTransform();
    }

    let initialDistance = 0;
    let initialScale = 1;

    // Add these event listeners for touch gestures
    svg.addEventListener('touchstart', handleTouchStart);
    svg.addEventListener('touchmove', handleTouchMove);
    svg.addEventListener('touchend', handleTouchEnd);

    function handleTouchStart(e) {
        if (e.touches.length === 2) {
            // Prevent default to avoid page zooming
            e.preventDefault();
            // Calculate initial distance between two fingers
            initialDistance = getTouchDistance(e.touches);
            initialScale = scale;
        } else {
            startDrag(e);
        }
    }

    function handleTouchMove(e) {
        if (e.touches.length === 2) {
            e.preventDefault();
            // Calculate new distance between touches
            const currentDistance = getTouchDistance(e.touches);
            
            // Calculate new scale
            scale = initialScale * (currentDistance / initialDistance);
            
            // You might want to add min/max limits
            scale = Math.min(Math.max(scale, 0.5), 3);
            
            updateTransform();
        } else {
            drag(e);
        }
    }

    function handleTouchEnd(e) {
        if (e.touches.length < 2) {
            initialDistance = 0;
        }
        endDrag();
    }

    function getTouchDistance(touches) {
        return Math.hypot(
            touches[1].clientX - touches[0].clientX,
            touches[1].clientY - touches[0].clientY
        );
    }


    function updateTransform() {
        svg.style.transform = `translate(${translateX}px, ${translateY}px) scale(${scale})`;
    }

    function getEventPoint(e) {
        const event = e.touches ? e.touches[0] : e;
        return {
            x: event.clientX,
            y: event.clientY
        };
    }

    // Station selection
    function toggleStation(station, circle) {
        if (selectedStations.has(station.id)) {
            selectedStations.delete(station.id);
            circle.classList.remove('selected-station');
        } else {
            selectedStations.add(station.id);
            circle.classList.add('selected-station');
        }
    }

    // Helper function to find station by ID
    function findStationById(stationId) {
        for (const line of metroData.lines) {
            const station = line.stations.find(s => s.id === stationId);
            if (station) return station;
        }
        return null;
    }

    // Initialize the map
    initMap();

    // Send selected stations to Telegram when done
    const submitButton = document.getElementById("submitButton");
    const cancelButton = document.getElementById("cancelButton");
    
    submitButton.addEventListener("click", (e) => {
        const selectedStationsList = Array.from(selectedStations).map(id => {
            const station = findStationById(id);
            return station ? station.name : null;
        }).filter(Boolean);

        tg.sendData(JSON.stringify({
            action: "selected_stations",
            selected_stations: selectedStationsList,
        }));
    });

    cancelButton.addEventListener("click", (e) => {
        tg.close();
    });

    tg.ready();

    if (!window.Telegram || !window.Telegram.WebApp) {
        console.error('Telegram WebApp is not properly initialized');
    }
});
