import {
    useEffect,
    useRef,
    useState
} from "react";

import StatusCard
    from "./components/StatusCard.jsx";

import SensorCard
    from "./components/SensorCard.jsx";

import SensorChart
    from "./components/SensorChart.jsx";

import AiTable
    from "./components/AiTable.jsx";


const REFRESH_INTERVAL = 1000;

const SENSOR_TIMEOUT = 5000;

const MAX_GRAPH_POINTS = 30;


const EMPTY_TELEMETRY = {

    temperature: 0,

    humidity: 0,

    gas: 0,

    gas_baseline: 0,

    pir: false,

    camera: false,

    level: 0

};


function parseApiDate(value) {

    if (!value) {
        return null;
    }


    const hasTimezone =
        value.endsWith("Z") ||
        /[+-]\d{2}:\d{2}$/.test(value);


    return new Date(

        hasTimezone
            ? value
            : `${value}Z`

    );

}


function formatTime(value) {

    const date =
        parseApiDate(
            value
        );


    if (!date) {
        return "--";
    }


    return date.toLocaleTimeString(

        "fr-FR",

        {

            hour:
                "2-digit",

            minute:
                "2-digit",

            second:
                "2-digit"

        }

    );

}


function formatNumber(
    value,
    decimals = 1
) {

    if (
        value === null ||
        value === undefined
    ) {

        return "0";

    }


    return Number(
        value
    ).toFixed(
        decimals
    );

}


export default function App() {

    const [
        currentTelemetry,
        setCurrentTelemetry
    ] = useState(
        EMPTY_TELEMETRY
    );


    const [
        currentAI,
        setCurrentAI
    ] = useState(
        null
    );


    const [
        telemetryHistory,
        setTelemetryHistory
    ] = useState([]);


    const [
        aiHistory,
        setAiHistory
    ] = useState([]);


    const [
        lastUpdate,
        setLastUpdate
    ] = useState("--");


    const initialized =
        useRef(false);


    const seenTelemetryIds =
        useRef(
            new Set()
        );


    const seenAiIds =
        useRef(
            new Set()
        );


    const lastTelemetryTime =
        useRef(null);


    const currentTelemetryId =
        useRef(null);


    async function refresh() {

        try {

            const timestamp =
                Date.now();


            const [
                telemetryResponse,
                aiResponse
            ] = await Promise.all([

                fetch(
                    `/api/telemetry?limit=30&t=${timestamp}`,
                    {
                        cache: "no-store"
                    }
                ),

                fetch(
                    `/api/ai-results?limit=30&t=${timestamp}`,
                    {
                        cache: "no-store"
                    }
                )

            ]);


            if (
                !telemetryResponse.ok ||
                !aiResponse.ok
            ) {

                throw new Error(
                    "Impossible de récupérer les données"
                );

            }


            const telemetryData =
                await telemetryResponse.json();


            const aiData =
                await aiResponse.json();


            const telemetryList =
                Array.isArray(
                    telemetryData
                )
                    ? telemetryData
                    : [];


            const aiList =
                Array.isArray(
                    aiData
                )
                    ? aiData
                    : [];


            // ===============================================
            // INITIALISATION
            // ===============================================

            if (
                !initialized.current
            ) {

                telemetryList.forEach(
                    item => {

                        if (
                            item._id
                        ) {

                            seenTelemetryIds
                                .current
                                .add(
                                    item._id
                                );

                        }

                    }
                );


                aiList.forEach(
                    item => {

                        if (
                            item._id
                        ) {

                            seenAiIds
                                .current
                                .add(
                                    item._id
                                );

                        }

                    }
                );


                initialized.current =
                    true;


                setLastUpdate(
                    new Date()
                        .toLocaleTimeString(
                            "fr-FR"
                        )
                );


                return;

            }


            // ===============================================
            // TELEMETRIES
            // ===============================================

            const newTelemetry =
                telemetryList
                    .filter(
                        item =>
                            item._id &&
                            !seenTelemetryIds
                                .current
                                .has(
                                    item._id
                                )
                    );


            newTelemetry.forEach(
                item => {

                    seenTelemetryIds
                        .current
                        .add(
                            item._id
                        );

                }
            );


            newTelemetry.sort(
                (a, b) => {

                    const dateA =
                        parseApiDate(
                            a.received_at
                        );


                    const dateB =
                        parseApiDate(
                            b.received_at
                        );


                    return (
                        dateA?.getTime() ?? 0
                    ) - (
                            dateB?.getTime() ?? 0
                        );

                }
            );


            if (
                newTelemetry.length > 0
            ) {

                const latest =
                    newTelemetry[
                    newTelemetry.length - 1
                    ];


                setCurrentTelemetry(
                    latest
                );


                currentTelemetryId.current =
                    latest._id;


                lastTelemetryTime.current =
                    Date.now();


                setTelemetryHistory(
                    previous => {

                        const updated = [

                            ...previous,

                            ...newTelemetry

                        ];


                        return updated.slice(
                            -MAX_GRAPH_POINTS
                        );

                    }
                );

            }


            // ===============================================
            // IA
            // ===============================================

            const newAiResults =
                aiList
                    .filter(
                        item =>
                            item._id &&
                            !seenAiIds
                                .current
                                .has(
                                    item._id
                                )
                    );


            newAiResults.forEach(
                item => {

                    seenAiIds
                        .current
                        .add(
                            item._id
                        );

                }
            );


            newAiResults.sort(
                (a, b) => {

                    const dateA =
                        parseApiDate(
                            a.received_at
                        );


                    const dateB =
                        parseApiDate(
                            b.received_at
                        );


                    return (
                        dateA?.getTime() ?? 0
                    ) - (
                            dateB?.getTime() ?? 0
                        );

                }
            );


            if (
                newAiResults.length > 0
            ) {

                setAiHistory(
                    previous => {

                        const updated = [

                            ...previous,

                            ...newAiResults

                        ];


                        return updated.slice(
                            -30
                        );

                    }
                );


                // Toujours utiliser l'analyse IA
                // la plus récente.

                const latestAI =
                    newAiResults[
                    newAiResults.length - 1
                    ];


                setCurrentAI(
                    latestAI
                );

            }


            // ===============================================
            // TIMEOUT
            // ===============================================

            if (
                lastTelemetryTime.current !== null
            ) {

                const elapsed =
                    Date.now() -
                    lastTelemetryTime.current;


                if (
                    elapsed >
                    SENSOR_TIMEOUT
                ) {

                    setCurrentTelemetry(
                        EMPTY_TELEMETRY
                    );


                    setCurrentAI(
                        null
                    );


                    currentTelemetryId.current =
                        null;


                    lastTelemetryTime.current =
                        null;

                }

            }


            setLastUpdate(
                new Date()
                    .toLocaleTimeString(
                        "fr-FR"
                    )
            );

        }

        catch (error) {

            console.error(
                "Erreur VIGIL-X :",
                error
            );

        }

    }


    useEffect(
        () => {

            refresh();


            const interval =
                setInterval(
                    refresh,
                    REFRESH_INTERVAL
                );


            return () => {

                clearInterval(
                    interval
                );

            };

        },
        []
    );


    // ===================================================
    // ETAT SYSTEME
    // ===================================================

    const hasCurrentData =
        currentTelemetryId.current !== null;


    let ruleText =
        "EN ATTENTE";


    let ruleType =
        "neutral";


    if (
        hasCurrentData
    ) {

        if (
            currentTelemetry.level === 0
        ) {

            ruleText =
                "NORMAL";

            ruleType =
                "normal";

        }

        else if (
            currentTelemetry.level === 1
        ) {

            ruleText =
                "WARNING";

            ruleType =
                "warning";

        }

        else if (
            currentTelemetry.level === 2
        ) {

            ruleText =
                "CRITIQUE";

            ruleType =
                "critical";

        }

    }


    // ===================================================
    // ETAT IA
    // ===================================================

    let aiText =
        "--";


    let aiType =
        "neutral";


    if (
        currentAI
    ) {

        if (
            currentAI.is_anomaly
        ) {

            aiText =
                "ACTIVITÉ SUSPECTE";

            aiType =
                "critical";

        }

        else {

            aiText =
                "NORMAL";

            aiType =
                "normal";

        }

    }


    return (

        <>

            <header
                className="header"
            >

                <div>

                    <h1>
                        VIGIL-X
                    </h1>


                    <p>
                        Versatile Intelligent Guard for IoT
                        & Local eXecution
                    </p>

                </div>

            </header>


            <main
                className="container"
            >


                <section
                    className="status-grid"
                >

                    <StatusCard
                        title="Niveau système"
                        value={ruleText}
                        type={ruleType}
                    />


                    <StatusCard
                        title="Analyse IA"
                        value={aiText}
                        type={aiType}
                    />


                    <StatusCard
                        title="Device cible"
                        value="ESP8266"
                        type="normal"
                    />

                </section>


                <section>

                    <h2>
                        Données capteurs
                    </h2>


                    <div
                        className="sensor-grid"
                    >

                        <SensorCard
                            title="Température"
                            value={
                                formatNumber(
                                    currentTelemetry.temperature,
                                    1
                                )
                            }
                            unit="°C"
                        />


                        <SensorCard
                            title="Humidité"
                            value={
                                formatNumber(
                                    currentTelemetry.humidity,
                                    1
                                )
                            }
                            unit="%"
                        />


                        <SensorCard
                            title="Gaz"
                            value={
                                currentTelemetry.gas
                            }
                        />


                        <SensorCard
                            title="Baseline gaz"
                            value={
                                currentTelemetry.gas_baseline
                            }
                        />


                        <SensorCard
                            title="Variation gaz"
                            value={
                                currentAI?.gas_delta ??
                                0
                            }
                        />


                        <SensorCard
                            title="Présence PIR"
                            value={
                                currentTelemetry.pir
                                    ? "DÉTECTION"
                                    : "RAS"
                            }
                        />


                        <SensorCard
                            title="Caméra"
                            value={
                                currentTelemetry.camera
                                    ? "DÉTECTION"
                                    : "RAS"
                            }
                        />


                        <SensorCard
                            title="Niveau d'alerte"
                            value={
                                currentTelemetry.level
                            }
                        />

                    </div>

                </section>


                <section>

                    <h2>
                        Évolution de la session
                    </h2>


                    <div
                        className="charts"
                    >


                        <SensorChart

                            title="Température °C"

                            color="#fb7185"

                            labels={
                                telemetryHistory.map(
                                    item =>
                                        formatTime(
                                            item.received_at
                                        )
                                )
                            }

                            values={
                                telemetryHistory.map(
                                    item =>
                                        item.temperature
                                )
                            }

                        />


                        <SensorChart

                            title="Humidité %"

                            color="#38bdf8"

                            labels={
                                telemetryHistory.map(
                                    item =>
                                        formatTime(
                                            item.received_at
                                        )
                                )
                            }

                            values={
                                telemetryHistory.map(
                                    item =>
                                        item.humidity
                                )
                            }

                        />


                        <SensorChart

                            title="Gaz"

                            color="#fbbf24"

                            labels={
                                telemetryHistory.map(
                                    item =>
                                        formatTime(
                                            item.received_at
                                        )
                                )
                            }

                            values={
                                telemetryHistory.map(
                                    item =>
                                        item.gas
                                )
                            }

                        />

                    </div>

                </section>


                <section>

                    <h2>
                        Détections de la session
                    </h2>


                    <AiTable
                        results={
                            [...aiHistory]
                                .reverse()
                        }
                    />

                </section>


                <footer>

                    Dashboard actualisé à :

                    {" "}

                    {lastUpdate}

                </footer>


            </main>

        </>

    );

}