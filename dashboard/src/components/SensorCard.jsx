export default function SensorCard({
    title,
    value,
    unit = ""
}) {

    return (

        <div className="sensor-card">

            <span className="card-label">
                {title}
            </span>

            <div>

                <span className="sensor-value">
                    {value ?? "--"}
                </span>

                {

                    unit && (

                        <span className="sensor-unit">
                            {unit}
                        </span>

                    )

                }

            </div>

        </div>

    );

}