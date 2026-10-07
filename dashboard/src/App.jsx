import {
    useEffect,
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


const REFRESH_INTERVAL = 2000;


function formatNumber(
    value,
    decimals = 1
) {

    if (
        value === null ||
        value === undefined
    ) {

        return "--";

    }

    return Number(
        value
    ).toFixed(
        decimals
    );

}


function formatTime(
    value
) {

    if (!value) {
        return "--";
    }

    return new Date(
        value
    ).toLocaleTimeString(
        "fr-FR"
    );

}


export default function App() {

    const [
        status,
        setStatus
    ] = useState(null);


    const [
        telemetryHistory,
        setTelemetryHistory
    ] = useState([]);


    const [
        aiHistory,
        setAiHistory
    ] = useState([]);


    const [
        online,
        setOnline
    ] = useState(false);


    const [
        lastUpdate,
        setLastUpdate
    ] = useState("--");


    async function refresh() {

        try {

            const [
                statusResponse,
                telemetryResponse,
                aiResponse
            ] = await Promise.all([

                fetch(
                    "/api/status"
                ),

                fetch(
                    "/api/telemetry?limit=30"
                ),

                fetch(
                    "/api/ai-results?limit=30"
                )

            ]);


            if (
                !statusResponse.ok ||
                !telemetryResponse.ok ||
                !aiResponse.ok
            ) {

                throw new Error(
                    "API indisponible"
                );

            }


            const statusData =
                await statusResponse.json();


            const telemetryData =
                await telemetryResponse.json();


            const aiData =
                await aiResponse.json();


            setStatus(
                statusData
            );

            setTelemetryHistory(
                telemetryData
            );

            setAiHistory(
                aiData
            );

            setOnline(
                true
            );

            setLastUpdate(
                new Date()
                    .toLocaleTimeString(
                        "fr-FR"
                    )
            );

        }

        catch (error) {

            console.error(
                error
            );

            setOnline(
                false
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


            return () =>
                clearInterval(
                    interval
                );

        },
        []
    );


    const telemetry =
        status?.telemetry;


    const ai =
        status?.ai;


    const ruleLevel =
        telemetry?.level;


    let ruleText = "--";

    let ruleType = "normal";


    if (ruleLevel === 0) {

        ruleText =
            "NORMAL";

        ruleType =
            "normal";

    }

    else if (ruleLevel === 1) {

        ruleText =
            "WARNING";

        ruleType =
            "warning";

    }

    else if (ruleLevel === 2) {

        ruleText =
            "CRITIQUE";

        ruleType =
            "critical";

    }


    const aiType =
        ai?.is_anomaly
            ? "critical"
            : "normal";


    const chronologicalTelemetry =
        [...telemetryHistory]
            .reverse();


    const chronologicalAI =
        [...aiHistory]
            .reverse();


    return (

        <>

            <header className="header">

                <div>

                    <h1>
                        SENTINEL-X
                    </h1>

                    <p>
                        Intelligent Security Monitoring
                    </p>

                </div>


                <div
                    className={
                        online
                            ? "connection online"
                            : "connection offline"
                    }
                >

                    {
                        online
                            ? "SYSTEM ONLINE"
                            : "SYSTEM OFFLINE"
                    }

                </div>

            </header>


            <main className="container">


                <section
                    className="status-grid"
                >

                    <StatusCard
                        title="Niveau ESP32"
                        value={ruleText}
                        type={ruleType}
                    />


                    <StatusCard
                        title="Analyse IA"
                        value={
                            ai
                                ? ai.is_anomaly
                                    ? "ANOMALIE"
                                    : "NORMAL"
                                : "--"
                        }
                        type={aiType}
                    />


                    <StatusCard
                        title="Score IA"
                        value={
                            formatNumber(
                                ai?.anomaly_score,
                                4
                            )
                        }
                        type={aiType}
                    />


                    <StatusCard
                        title="Device"
                        value={
                            telemetry?.device_id ??
                            "--"
                        }
                    />

                </section>


                <section>

                    <h2>
                        Capteurs
                    </h2>


                    <div className="sensor-grid">

                        <SensorCard
                            title="Température"
                            value={
                                formatNumber(
                                    telemetry?.temperature
                                )
                            }
                            unit="°C"
                        />


                        <SensorCard
                            title="Humidité"
                            value={
                                formatNumber(
                                    telemetry?.humidity
                                )
                            }
                            unit="%"
                        />


                        <SensorCard
                            title="Gaz"
                            value={
                                telemetry?.gas
                            }
                        />


                        <SensorCard
                            title="Baseline gaz"
                            value={
                                telemetry?.gas_baseline
                            }
                        />


                        <SensorCard
                            title="Delta gaz"
                            value={
                                formatNumber(
                                    ai?.gas_delta,
                                    0
                                )
                            }
                        />


                        <SensorCard
                            title="Ratio gaz"
                            value={
                                formatNumber(
                                    ai?.gas_ratio,
                                    3
                                )
                            }
                        />


                        <SensorCard
                            title="PIR"
                            value={
                                telemetry?.pir
                                    ? "MOUVEMENT"
                                    : "RAS"
                            }
                        />


                        <SensorCard
                            title="Caméra"
                            value={
                                telemetry?.camera
                                    ? "DÉTECTION"
                                    : "RAS"
                            }
                        />

                    </div>

                </section>


                <section>

                    <h2>
                        Historique temps réel
                    </h2>


                    <div className="charts">


                        <SensorChart

                            title="Température °C"

                            labels={
                                chronologicalTelemetry.map(
                                    item =>
                                        formatTime(
                                            item.received_at
                                        )
                                )
                            }

                            values={
                                chronologicalTelemetry.map(
                                    item =>
                                        item.temperature
                                )
                            }

                        />


                        <SensorChart

                            title="Humidité %"

                            labels={
                                chronologicalTelemetry.map(
                                    item =>
                                        formatTime(
                                            item.received_at
                                        )
                                )
                            }

                            values={
                                chronologicalTelemetry.map(
                                    item =>
                                        item.humidity
                                )
                            }

                        />


                        <SensorChart

                            title="Gaz"

                            labels={
                                chronologicalTelemetry.map(
                                    item =>
                                        formatTime(
                                            item.received_at
                                        )
                                )
                            }

                            values={
                                chronologicalTelemetry.map(
                                    item =>
                                        item.gas
                                )
                            }

                        />


                        <SensorChart

                            title="Score IA"

                            labels={
                                chronologicalAI.map(
                                    item =>
                                        formatTime(
                                            item.received_at
                                        )
                                )
                            }

                            values={
                                chronologicalAI.map(
                                    item =>
                                        item.anomaly_score
                                )
                            }

                        />

                    </div>

                </section>


                <section>

                    <h2>
                        Dernières analyses IA
                    </h2>

                    <AiTable
                        results={
                            aiHistory
                        }
                    />

                </section>


                <footer>

                    Dernière mise à jour :

                    {" "}

                    {lastUpdate}

                </footer>


            </main>

        </>

    );

}