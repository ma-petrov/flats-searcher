const metroData = {
    lines: [
        {
            id: 1,
            name: "Сокольническая",
            color: "#EF1E25",
            stations: [
                { id: "1_1", name: "Бульвар Рокоссовского", x: 800, y: 200 },
                { id: "1_2", name: "Черкизовская", x: 750, y: 250 },
                { id: "1_3", name: "Преображенская площадь", x: 700, y: 300 },
                // Add more stations with coordinates
            ]
        },
        // Add more lines
    ],
    transfers: [
        {
            stations: ["1_7", "7_7"],
            type: "transfer"
        },
        // Add more transfers
    ]
};
