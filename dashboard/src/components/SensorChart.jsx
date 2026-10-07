import {
    Line
} from "react-chartjs-2";

import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Tooltip,
    Legend
} from "chart.js";


ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Tooltip,
    Legend
);


export default function SensorChart({
    title,
    labels,
    values
}) {

    const data = {

        labels,

        datasets: [

            {

                label: title,

                data: values,

                tension: 0.3,

                pointRadius: 2

            }

        ]

    };


    const options = {

        responsive: true,

        maintainAspectRatio: false,

        animation: false,

        plugins: {

            legend: {

                labels: {

                    color: "#aeb9d4"

                }

            }

        },

        scales: {

            x: {

                ticks: {

                    color: "#7886a3"

                },

                grid: {

                    color: "#202942"

                }

            },

            y: {

                ticks: {

                    color: "#7886a3"

                },

                grid: {

                    color: "#202942"

                }

            }

        }

    };


    return (

        <div className="chart-card">

            <h3>
                {title}
            </h3>

            <div className="chart-wrapper">

                <Line
                    data={data}
                    options={options}
                />

            </div>

        </div>

    );

}