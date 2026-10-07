export default function StatusCard({
    title,
    value,
    type = "normal"
}) {

    return (

        <div className="status-card">

            <span className="card-label">
                {title}
            </span>

            <div
                className={`status-value status-${type}`}
            >

                {value}

            </div>

        </div>

    );

}