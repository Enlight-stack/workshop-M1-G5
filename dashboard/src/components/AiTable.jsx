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
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit"
        }
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

        <div
            className="table-container"
        >

            <table>

                <thead>

                    <tr>

                        <th>
                            Heure
                        </th>

                        <th>
                            Température
                        </th>

                        <th>
                            Humidité
                        </th>

                        <th>
                            Gaz
                        </th>

                        <th>
                            PIR
                        </th>

                        <th>
                            Caméra
                        </th>

                        <th>
                            Niveau
                        </th>

                        <th>
                            Analyse IA
                        </th>

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
                                        key={
                                            result._id
                                        }
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
                                                    result.temperature,
                                                    1
                                                )
                                            }

                                            {" °C"}

                                        </td>


                                        <td>

                                            {
                                                formatNumber(
                                                    result.humidity,
                                                    1
                                                )
                                            }

                                            {" %"}

                                        </td>


                                        <td>

                                            {
                                                result.gas ??
                                                "--"
                                            }

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

                                                {
                                                    result.rule_level
                                                }

                                            </span>

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
                                                        ? "ACTIVITÉ SUSPECTE"
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