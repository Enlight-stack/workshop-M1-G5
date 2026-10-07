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
    Legend,
    Filler
} from "chart.js";


ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Tooltip,
    Legend,
    Filler
);


export default function SensorChart({
    title,
    labels,
    values,
    color = "#38bdf8"
}) {

    const data = {

        labels,

        datasets: [

            {

                label:
                    title,

                data:
                    values,

                borderColor:
                    color,

                backgroundColor:
                    `${color}22`,

                pointBackgroundColor:
                    color,

                pointBorderColor:
                    color,

                pointRadius:
                    3,

                pointHoverRadius:
                    6,

                borderWidth:
                    3,

                tension:
                    0.25,

                fill:
                    true

            }

        ]

    };


    const options = {

        responsive:
            true,

        maintainAspectRatio:
            false,

        animation:
            false,

        interaction: {

            intersect:
                false,

            mode:
                "index"

        },

        plugins: {

            legend: {

                labels: {

                    color:
                        "#dbeafe",

                    font: {

                        size:
                            13

                    }

                }

            },


            tooltip: {

                enabled:
                    true

            }

        },


        scales: {

            x: {

                ticks: {

                    color:
                        "#94a3b8",

                    maxRotation:
                        45,

                    minRotation:
                        45,

                    autoSkip:
                        true,

                    maxTicksLimit:
                        8

                },

                grid: {

                    color:
                        "rgba(148, 163, 184, 0.15)"

                },

                border: {

                    color:
                        "rgba(148, 163, 184, 0.35)"

                }

            },


            y: {

                beginAtZero:
                    false,

                ticks: {

                    color:
                        "#94a3b8"

                },

                grid: {

                    color:
                        "rgba(148, 163, 184, 0.16)"

                },

                border: {

                    color:
                        "rgba(148, 163, 184, 0.35)"

                }

            }

        }

    };


    return (

        <div
            className="chart-card"
        >

            <h3>
                {title}
            </h3>


            <div
                className="chart-wrapper"
            >

                <Line
                    data={data}
                    options={options}
                />

            </div>

        </div>

    );

}