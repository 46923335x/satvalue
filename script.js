async function fetchBTCPrices() {
  const response = await fetch(
    "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=60"
  );
  const data = await response.json();
  return data.prices; // each item: [timestamp, price]
}

function transformPrices(prices) {
  const labels = [];
  const inverted = [];

  for (let [timestamp, price] of prices) {
    const date = new Date(timestamp);
    labels.push(date.toLocaleDateString());
    inverted.push((1 / price) * 100000000); // BTC (Sats) per USD
  }

  return { labels, inverted };
}

function drawChart(labels, data) {
  const ctx = document.getElementById("btcChart").getContext("2d");

  new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "BTC (Sats) per USD",
          data: data,
          borderColor: "blue",
          fill: false,
          tension: 0.3,
        },
      ],
    },
    options: {
      responsive: true,
      scales: {
        y: {
            title: {
                display: true,
                text: "Sats per USD"
            },
            ticks: {
                callback: function(value) {
                return Math.round(value) + ' sats';
                }
            }
        },
        x: {
          title: {
            display: true,
            text: "Date",
          },
        },
      },
    },
  });
}

async function main() {
  const prices = await fetchBTCPrices();
  const { labels, inverted } = transformPrices(prices);
  drawChart(labels, inverted);
}

main(); // run the whole thing
