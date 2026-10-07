function formatTime(value) {

    if (!value) {
        return "--";
    }

    return new Date(
        value
    ).toLocaleTimeString(
        "fr-FR"
    );

}


function formatNumber(
    value,
    decimals = 1
) {

    if (
        value === undefined ||
        value === null
    ) {

        return "--";

    }

    return Number(
        value
    ).toFixed(
        decimals
    );

}


export default function AiTable({
    results
}) {

    return (

        <div className="table-container">

            <table>

                <thead>

                    <tr>

                        <th>Heure</th>

                        <th>Temp</th>

                        <th>Humidité</th>

                        <th>Gaz</th>

                        <th>PIR</th>

                        <th>Cam</th>

                        <th>Niveau</th>

                        <th>Score IA</th>

                        <th>IA</th>

                    </tr>

                </thead>


                <tbody>

                    {

                        results
                            .slice(
                                0,
                                10
                            )
                            .map(
                                result => (

                                    <tr
                                        key={result._id}
                                    >

                                        <td>

                                            {
                                                formatTime(
                                                    result.received_at
                                                )
                                            }

                                        </td>


                                        <td>

                                            {
                                                formatNumber(
                                                    result.temperature
                                                )
                                            } °C

                                        </td>


                                        <td>

                                            {
                                                formatNumber(
                                                    result.humidity
                                                )
                                            } %

                                        </td>


                                        <td>
                                            {result.gas}
                                        </td>


                                        <td>

                                            {
                                                result.pir
                                                    ? "Oui"
                                                    : "Non"
                                            }

                                        </td>


                                        <td>

                                            {
                                                result.camera
                                                    ? "Oui"
                                                    : "Non"
                                            }

                                        </td>


                                        <td>

                                            <span
                                                className={
                                                    `badge ${result.rule_level === 0
                                                        ? "badge-normal"
                                                        : result.rule_level === 1
                                                            ? "badge-warning"
                                                            : "badge-critical"
                                                    }`
                                                }
                                            >

                                                {result.rule_level}

                                            </span>

                                        </td>


                                        <td>

                                            {
                                                formatNumber(
                                                    result.anomaly_score,
                                                    4
                                                )
                                            }

                                        </td>


                                        <td>

                                            <span
                                                className={
                                                    `badge ${result.is_anomaly
                                                        ? "badge-critical"
                                                        : "badge-normal"
                                                    }`
                                                }
                                            >

                                                {
                                                    result.is_anomaly
                                                        ? "ANOMALIE"
                                                        : "NORMAL"
                                                }

                                            </span>

                                        </td>

                                    </tr>

                                )
                            )

                    }

                </tbody>

            </table>

        </div>

    );

}